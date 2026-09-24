"""
阶段时间门禁工具：用于在业务接口入口校验当前时间是否在允许操作窗口内。

典型用法：
  from app.core.stage_gate import check_stage_access, StageLockedException

  # 在 submit 接口里：
  try:
      check_stage_access(db, "proposal", current_user.role)
  except StageLockedException as e:
      raise HTTPException(403, str(e))
"""
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.stage_config import StageConfig


# 业务模块 → stage_configs.module_key 的映射（方便后续扩展）
MODULE_STAGE_MAP = {
    # proposals submit
    "proposal": "proposal",
    # midterm submit/guidance/ppt
    "midterm": "midterm",
    # topics submit/resubmit
    "topic": "topic",
    # thesis upload
    "thesis_draft": "thesis_draft",
    "thesis_revision": "thesis_revision",
    "thesis_final": "thesis_final",
    # review
    "review": "review",
    # defense
    "defense": "defense",
    # archive submit
    "archive": "archive",
}


class StageLockedException(Exception):
    """阶段锁定异常"""

    def __init__(self, message: str, status: str = "locked", module_key: str = "", module_name: str = ""):
        super().__init__(message)
        self.message = message
        self.status = status            # pending / locked
        self.module_key = module_key
        self.module_name = module_name


def get_stage_status(db: Session, module_key: str) -> Optional[dict]:
    """查询指定模块的时间窗状态"""
    row = db.query(StageConfig).filter(StageConfig.module_key == module_key).first()
    if not row:
        return None
    now = datetime.now()
    if now < row.start_time:
        status = "pending"
    elif now <= row.end_time:
        status = "active"
    else:
        status = "locked"
    return {
        "module_key": row.module_key,
        "module_name": row.module_name,
        "start_time": row.start_time.isoformat(),
        "end_time": row.end_time.isoformat(),
        "status": status,
        "student_lock_after_end": bool(row.student_lock_after_end),
        "teacher_lock_after_end": bool(row.teacher_lock_after_end),
    }


def check_stage_access(db: Session, module_key: str, role: str = "student", skip_admin: bool = True) -> dict:
    """校验某角色是否允许操作指定模块。

    Args:
        db: Session
        module_key: stage_configs.module_key
        role: 当前用户角色
        skip_admin: 管理员跳过锁定

    Returns:
        stage_info dict（active 时返回）

    Raises:
        StageLockedException: 不在时间窗内或已锁定
    """
    if skip_admin and role == "admin":
        return {"status": "active", "module_key": module_key, "admin_bypass": True}

    row = db.query(StageConfig).filter(StageConfig.module_key == module_key).first()
    if not row:
        # 未配置阶段 → 默认放行
        return {"status": "active", "module_key": module_key, "no_config": True}

    now = datetime.now()
    if now < row.start_time:
        raise StageLockedException(
            f"「{row.module_name}」阶段尚未开放，开放时间：{row.start_time.strftime('%Y-%m-%d %H:%M')} ～ {row.end_time.strftime('%Y-%m-%d %H:%M')}",
            status="pending",
            module_key=module_key,
            module_name=row.module_name,
        )

    if now > row.end_time:
        # 检查是否对该角色锁定
        locked = (role == "student" and row.student_lock_after_end == 1) or \
                 (role in ("teacher",) and row.teacher_lock_after_end == 1)
        if locked:
            raise StageLockedException(
                f"「{row.module_name}」阶段已结束（{row.end_time.strftime('%Y-%m-%d %H:%M')}），提交入口已锁定，请联系管理员调整时间。",
                status="locked",
                module_key=module_key,
                module_name=row.module_name,
            )

    return {
        "status": "active",
        "module_key": module_key,
        "module_name": row.module_name,
        "start_time": row.start_time.isoformat(),
        "end_time": row.end_time.isoformat(),
    }


def raise_if_locked(db: Session, module_key: str, role: str = "student", skip_admin: bool = True):
    """便捷封装：阶段锁定时抛出 HTTPException(403)，上层调用无需自己 try/except。

    用法：
        from app.core.stage_gate import raise_if_locked
        raise_if_locked(db, "proposal", current_user.role)
    """
    from fastapi import HTTPException
    try:
        return check_stage_access(db, module_key, role, skip_admin)
    except StageLockedException as e:
        raise HTTPException(status_code=403, detail=e.message)
