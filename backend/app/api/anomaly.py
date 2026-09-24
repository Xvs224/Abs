"""
异常检测 API 路由

提供异常检测、记录查询、复核管理、统计分析等 RESTful 接口。
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.response import success_response, page_response
from app.core.security import get_current_user, require_admin, require_teacher_or_admin, require_student_or_teacher
from app.models.user import User
from app.models.topic import Topic
from app.schemas.anomaly import (
    DetectionRequest,
    AnomalyReviewRequest,
    AnomalyEvaluationRequest,
)
from app.services.anomaly_service import AnomalyService

router = APIRouter(prefix="/api/anomaly", tags=["异常检测"])


def _get_teacher_student_ids(db: Session, teacher_id: int):
    """获取教师负责的所有学生ID"""
    rows = db.query(Topic.student_id).filter(Topic.teacher_id == teacher_id).distinct().all()
    return [r[0] for r in rows]


# ==================================================================
# 检测接口
# ==================================================================

@router.post("/detect", summary="手动触发异常检测")
def detect_anomaly(
    request: DetectionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin),
):
    """
    手动触发单个目标的异常检测

    - **target_type**: 目标类型 (student/topic/proposal/midterm/thesis/review)
    - **target_id**: 目标ID（scope=single 时必填）
    - **detection_method**: 检测方法 (iqr/isolation_forest/combined)
    - **scope**: 检测范围 (single/all)
    """
    service = AnomalyService(db)

    # target_type 为空时，执行全量检测
    if not request.target_type:
        result = service.run_full_detection()
        return success_response(data=result, message="全量检测完成")

    if request.scope == "all":
        # 全量检测某类型
        result = service.detect_batch(
            target_type=request.target_type,
            method=request.detection_method or "combined",
        )
        return success_response(data=result, message="批量检测完成")
    else:
        # 单个目标检测
        if not request.target_id:
            from app.core.exceptions import BusinessException
            raise BusinessException(message="单个检测必须指定 target_id")

        result = service.detect_target(
            target_type=request.target_type,
            target_id=request.target_id,
            method=request.detection_method or "combined",
        )
        return success_response(data=result, message="检测完成")


@router.post("/detect/batch", summary="批量异常检测")
def detect_batch(
    request: DetectionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin),
):
    """
    对指定类型的所有目标进行批量异常检测

    - **target_type**: 目标类型
    - **detection_method**: 检测方法
    """
    service = AnomalyService(db)
    result = service.detect_batch(
        target_type=request.target_type,
        method=request.detection_method or "combined",
    )
    return success_response(data=result, message="批量检测完成")


@router.post("/detect/full", summary="全量异常检测")
def detect_full(
    request: DetectionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin),
):
    """
    运行全量异常检测，检测所有目标类型的所有数据
    """
    service = AnomalyService(db)
    result = service.run_full_detection()
    return success_response(data=result, message="全量检测完成")


@router.post("/detect/rules", summary="全量规则类检测")
def detect_rules(
    request: DetectionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin),
):
    service = AnomalyService(db)
    result = service.run_rule_detection()
    return success_response(data=result, message="规则检测完成")


@router.post("/detect/student/{student_id}", summary="触发单个学生检测（可业务提交后调用）")
def detect_for_student(
    student_id: int,
    clear_old: bool = Query(False, description="是否清空旧待复核记录"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 权限：本人 / 管理员 / 该学生指导教师
    if current_user.role not in ("admin",):
        from app.models.topic import Topic
        topic = db.query(Topic).filter(Topic.student_id == student_id).first()
        if current_user.id != student_id and (not topic or topic.teacher_id != current_user.id):
            from fastapi import HTTPException
            raise HTTPException(403, "无权为该学生触发检测")
    service = AnomalyService(db)
    result = service.trigger_for_student(student_id, clear_old=clear_old)
    return success_response(data=result, message="检测完成")


# ==================================================================
# 异常记录接口
# ==================================================================

@router.get("/records", summary="异常记录列表")
def get_records(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    target_type: Optional[str] = Query(None, description="目标类型"),
    severity_level: Optional[str] = Query(None, description="严重等级"),
    review_status: Optional[str] = Query(None, description="复核状态"),
    student_id: Optional[int] = Query(None, description="学生ID"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取异常记录列表（分页）

    支持按目标类型、严重等级、复核状态、学生ID筛选，以及关键词搜索。
    """
    # 数据隔离：学生只能查看自己的异常记录；教师只能查看自己负责学生的记录
    if current_user.role == "student":
        student_id = current_user.id
    elif current_user.role == "teacher":
        teacher_student_ids = _get_teacher_student_ids(db, current_user.id)
        if not teacher_student_ids:
            return page_response(items=[], total=0, page=page, page_size=page_size)

    service = AnomalyService(db)

    # 教师维度：需要传入多个 student_id 过滤
    if current_user.role == "teacher":
        result = service.get_record_list_teacher(
            page=page,
            page_size=page_size,
            student_ids=teacher_student_ids,
            target_type=target_type,
            severity_level=severity_level,
            review_status=review_status,
            keyword=keyword,
        )
    else:
        result = service.get_record_list(
            page=page,
            page_size=page_size,
            target_type=target_type,
            severity_level=severity_level,
            review_status=review_status,
            student_id=student_id,
            keyword=keyword,
        )
    return page_response(
        items=result["items"],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
    )


@router.get("/records/{record_id}", summary="异常记录详情")
def get_record_detail(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student_or_teacher),
):
    """
    获取异常记录详情

    - **record_id**: 异常记录ID
    - 学生只能查看自己的异常记录
    """
    service = AnomalyService(db)
    result = service.get_record_detail(record_id)
    if current_user.role == "student" and result.get("student_id") != current_user.id:
        from app.core.exceptions import ForbiddenException
        raise ForbiddenException("无权查看他人的异常记录")
    return success_response(data=result)


@router.post("/records/{record_id}/review", summary="人工复核异常记录")
def review_record(
    record_id: int,
    request: AnomalyReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin),
):
    """
    人工复核异常记录

    - **record_id**: 异常记录ID
    - **result**: 复核结果 (confirmed/false_positive/ignored)
    - **opinion**: 复核意见
    - **correction**: 纠正措施
    - **correction_result**: 纠正结果
    """
    service = AnomalyService(db)
    result = service.review_record(
        record_id=record_id,
        reviewer_id=current_user.id,
        result=request.result,
        opinion=request.opinion or "",
        correction=request.correction or "",
        correction_result=request.correction_result or "",
    )
    return success_response(data=result, message="复核完成")


@router.get("/records/{record_id}/reviews", summary="复核历史记录")
def get_review_history(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin),
):
    """
    获取异常记录的复核历史

    - **record_id**: 异常记录ID
    """
    service = AnomalyService(db)
    result = service.get_review_history(record_id)
    return success_response(data=result)


@router.delete("/records/{record_id}", summary="删除异常记录")
def delete_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin),
):
    """
    删除异常记录（教师、管理员可操作）。
    教师只能删除自己负责学生的异常记录。
    """
    from app.models.anomaly import AnomalyRecord, AnomalyReview

    record = db.query(AnomalyRecord).filter(AnomalyRecord.id == record_id).first()
    if not record:
        return success_response(message="记录不存在或已删除")

    # 教师数据隔离
    if current_user.role == "teacher":
        student_ids = _get_teacher_student_ids(db, current_user.id)
        if record.student_id not in student_ids:
            from app.core.exceptions import BusinessException
            raise BusinessException(403, "无权删除非本人负责学生的异常记录")

    # 级联删除复核记录
    db.query(AnomalyReview).filter(AnomalyReview.anomaly_id == record_id).delete(synchronize_session=False)
    db.delete(record)
    db.commit()
    return success_response(message="删除成功")


# ==================================================================
# 统计接口
# ==================================================================

@router.get("/stats", summary="异常统计数据")
def get_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin),
):
    """
    获取异常检测统计数据

    包括总数、各等级数量、各类型分布、近7天趋势、复核精确率等。
    教师仅看到自己负责学生的数据。
    """
    service = AnomalyService(db)

    if current_user.role == "teacher":
        student_ids = _get_teacher_student_ids(db, current_user.id)
        result = service.get_stats(student_ids=student_ids)
    else:
        result = service.get_stats()

    return success_response(data=result)


# ==================================================================
# 评估接口
# ==================================================================

@router.post("/evaluate", summary="检测准确性评估（基于真实已复核数据）")
def evaluate_detection(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin),
):
    """
    评估异常检测方法的准确性。

    仅基于已人工复核的真实业务数据计算精确率、召回率等指标，不使用模拟数据。
    """
    service = AnomalyService(db)
    result = service.evaluate_detection(dataset_type="real", method="combined")
    return success_response(data=result, message="评估完成")


# ==================================================================
# 定时检测调度管理（仅管理员）
# ==================================================================

@router.get("/schedule", summary="查询定时检测调度状态")
def get_schedule_status(current_user: User = Depends(require_admin)):
    """
    查询异常检测定时任务的运行状态。

    返回调度器启用状态、cron 表达式、下次执行时间、最近执行结果等。
    """
    from app.core.anomaly_scheduler import get_scheduler_state
    return success_response(data=get_scheduler_state())


@router.put("/schedule", summary="更新定时检测 cron 表达式")
def update_schedule(
    cron: str = Query(..., description="cron 表达式，5 字段：分 时 日 月 周，如 '0 2 * * *'"),
    current_user: User = Depends(require_admin),
):
    """
    更新全量检测的定时执行周期。

    - **cron**: 5 字段 cron 表达式
      - `0 2 * * *` = 每天凌晨 2 点
      - `0 */6 * * *` = 每 6 小时
      - `0 8,18 * * 1-5` = 工作日 8 点和 18 点
    """
    from app.core.anomaly_scheduler import update_cron
    state = update_cron(cron)
    return success_response(data=state, message="调度周期已更新")


@router.post("/schedule/pause", summary="暂停定时检测")
def pause_schedule(current_user: User = Depends(require_admin)):
    """暂停自动定时检测（不影响手动触发）"""
    from app.core.anomaly_scheduler import pause_scheduler
    state = pause_scheduler()
    return success_response(data=state, message="定时检测已暂停")


@router.post("/schedule/resume", summary="恢复定时检测")
def resume_schedule(current_user: User = Depends(require_admin)):
    """恢复自动定时检测"""
    from app.core.anomaly_scheduler import resume_scheduler
    state = resume_scheduler()
    return success_response(data=state, message="定时检测已恢复")


@router.post("/schedule/trigger", summary="立即触发一次全量检测")
def trigger_now(current_user: User = Depends(require_admin)):
    """
    立即在后台异步执行一次全量异常检测。
    接口立即返回，检测结果可稍后在记录列表中查看。
    """
    from app.core.anomaly_scheduler import trigger_now
    result = trigger_now()
    return success_response(data=result, message="已触发全量检测")
