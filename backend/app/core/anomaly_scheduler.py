"""
异常检测定时调度器

基于 APScheduler 的 BackgroundScheduler，在应用启动时注册定时全量检测任务。
支持运行时动态调整 cron 表达式、暂停/恢复、立即触发。
"""
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.memory import MemoryJobStore

from app.config import settings

logger = logging.getLogger(__name__)

# 全局调度器实例（单例）
_scheduler: Optional[BackgroundScheduler] = None

# 调度状态（供 API 查询）
_scheduler_state: Dict[str, Any] = {
    "enabled": settings.ANOMALY_AUTO_DETECT_ENABLED,
    "cron": settings.ANOMALY_DETECTION_CRON,
    "timezone": settings.ANOMALY_DETECTION_TIMEZONE,
    "running": False,
    "last_run_time": None,
    "last_run_result": None,
    "next_run_time": None,
    "run_count": 0,
}

JOB_ID = "anomaly_full_detection"


def _run_full_detection_job() -> None:
    """定时任务执行体：运行全量异常检测

    在独立线程中执行，不阻塞 API 请求。
    每次执行都会打开新的数据库会话。
    """
    from app.database import SessionLocal
    from app.services.anomaly_service import AnomalyService

    logger.info("[定时检测] 开始执行全量异常检测...")
    _scheduler_state["last_run_time"] = datetime.now().isoformat()
    db = SessionLocal()
    try:
        service = AnomalyService(db)
        result = service.run_full_detection()
        _scheduler_state["last_run_result"] = {
            "total_targets": result.get("summary", {}).get("total_targets", 0),
            "total_anomalies": result.get("summary", {}).get("total_anomalies", 0),
            "L1": result.get("summary", {}).get("L1", 0),
            "L2": result.get("summary", {}).get("L2", 0),
            "L3": result.get("summary", {}).get("L3", 0),
        }
        _scheduler_state["run_count"] += 1
        logger.info(
            f"[定时检测] 完成：扫描 {result.get('summary', {}).get('total_targets', 0)} 个目标，"
            f"发现 {result.get('summary', {}).get('total_anomalies', 0)} 条异常"
        )
    except Exception as e:
        logger.exception(f"[定时检测] 执行失败: {e}")
        _scheduler_state["last_run_result"] = {"error": str(e)}
    finally:
        db.close()


def init_scheduler() -> None:
    """初始化调度器并注册全量检测任务（应用启动时调用）"""
    global _scheduler

    if _scheduler is not None:
        logger.warning("[定时检测] 调度器已初始化，跳过")
        return

    _scheduler = BackgroundScheduler(
        jobstores={"default": MemoryJobStore()},
        timezone=settings.ANOMALY_DETECTION_TIMEZONE,
    )

    if settings.ANOMALY_AUTO_DETECT_ENABLED:
        _add_detection_job(settings.ANOMALY_DETECTION_CRON)
        _scheduler.start()
        _scheduler_state["running"] = True
        _update_next_run_time()
        logger.info(
            f"[定时检测] 调度器已启动，cron='{settings.ANOMALY_DETECTION_CRON}'，"
            f"下次执行：{_scheduler_state['next_run_time']}"
        )
    else:
        logger.info("[定时检测] 自动检测已禁用（ANOMALY_AUTO_DETECT_ENABLED=False）")


def _add_detection_job(cron_expr: str) -> None:
    """添加/替换全量检测定时任务"""
    if _scheduler is None:
        return

    # 解析 cron 表达式：5 字段 "分 时 日 月 周"
    parts = cron_expr.strip().split()
    if len(parts) != 5:
        raise ValueError(f"无效的 cron 表达式，需要 5 个字段: {cron_expr}")

    minute, hour, day, month, day_of_week = parts
    trigger = CronTrigger(
        minute=minute,
        hour=hour,
        day=day,
        month=month,
        day_of_week=day_of_week,
        timezone=settings.ANOMALY_DETECTION_TIMEZONE,
    )

    # 若已存在则替换
    if _scheduler.get_job(JOB_ID):
        _scheduler.reschedule_job(JOB_ID, trigger=trigger)
    else:
        _scheduler.add_job(
            _run_full_detection_job,
            trigger=trigger,
            id=JOB_ID,
            name="全量异常检测",
            replace_existing=True,
        )


def _update_next_run_time() -> None:
    """更新下次执行时间"""
    if _scheduler is None:
        return
    job = _scheduler.get_job(JOB_ID)
    if job and job.next_run_time:
        _scheduler_state["next_run_time"] = job.next_run_time.strftime("%Y-%m-%d %H:%M:%S")
    else:
        _scheduler_state["next_run_time"] = None


def get_scheduler_state() -> Dict[str, Any]:
    """获取调度器状态"""
    _update_next_run_time()
    return dict(_scheduler_state)


def update_cron(cron_expr: str) -> Dict[str, Any]:
    """更新定时检测的 cron 表达式"""
    if _scheduler is None:
        raise RuntimeError("调度器未初始化")
    _add_detection_job(cron_expr)
    _scheduler_state["cron"] = cron_expr
    _update_next_run_time()
    return get_scheduler_state()


def pause_scheduler() -> Dict[str, Any]:
    """暂停定时检测"""
    if _scheduler is None:
        raise RuntimeError("调度器未初始化")
    if _scheduler.get_job(JOB_ID):
        _scheduler.pause_job(JOB_ID)
    _scheduler_state["enabled"] = False
    _scheduler_state["running"] = False
    return get_scheduler_state()


def resume_scheduler() -> Dict[str, Any]:
    """恢复定时检测"""
    if _scheduler is None:
        raise RuntimeError("调度器未初始化")
    if _scheduler.get_job(JOB_ID):
        _scheduler.resume_job(JOB_ID)
    _scheduler_state["enabled"] = True
    _scheduler_state["running"] = True
    _update_next_run_time()
    return get_scheduler_state()


def trigger_now() -> Dict[str, Any]:
    """立即触发一次全量检测（异步执行）"""
    if _scheduler is None:
        raise RuntimeError("调度器未初始化")
    # 在调度器线程中立即执行一次
    _scheduler.add_job(
        _run_full_detection_job,
        trigger="date",
        run_date=datetime.now(),
        id=f"{JOB_ID}_manual_{int(datetime.now().timestamp())}",
        name="手动触发全量检测",
    )
    return {"message": "已触发全量检测，将在后台异步执行"}


def shutdown_scheduler() -> None:
    """关闭调度器（应用关闭时调用）"""
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        _scheduler_state["running"] = False
        logger.info("[定时检测] 调度器已关闭")
