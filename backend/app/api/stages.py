"""阶段时间配置 CRUD API"""
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.database import get_db
from app.core.response import success_response
from app.core.security import get_current_user, require_admin
from app.models.stage_config import StageConfig

router = APIRouter(prefix="/api/stages", tags=["阶段时间配置"])


# ---------------- Schema ----------------
class StageConfigUpsert(BaseModel):
    module_key: str = Field(..., description="模块key")
    module_name: Optional[str] = None
    start_time: datetime
    end_time: datetime
    student_lock_after_end: int = 1
    teacher_lock_after_end: int = 0
    description: str = ""

    def validate_time(self):
        if self.end_time <= self.start_time:
            raise HTTPException(400, "结束时间必须晚于开始时间")


# ---------------- 查询 ----------------
@router.get("", summary="获取全部阶段配置")
def list_stages(
    db: Session = Depends(get_db),
    _: any = Depends(get_current_user),
):
    rows = db.query(StageConfig).order_by(StageConfig.start_time.asc()).all()
    data = []
    now = datetime.now()
    for r in rows:
        status = "locked"
        if now < r.start_time:
            status = "pending"
        elif now <= r.end_time:
            status = "active"
        data.append({
            "id": r.id,
            "module_key": r.module_key,
            "module_name": r.module_name,
            "start_time": r.start_time.isoformat() if r.start_time else None,
            "end_time": r.end_time.isoformat() if r.end_time else None,
            "status": status,
            "student_lock_after_end": bool(r.student_lock_after_end),
            "teacher_lock_after_end": bool(r.teacher_lock_after_end),
            "description": r.description or "",
        })
    return success_response(data)


@router.get("/{module_key}", summary="获取单个阶段配置")
def get_stage(module_key: str, db: Session = Depends(get_db), _: any = Depends(get_current_user)):
    row = db.query(StageConfig).filter(StageConfig.module_key == module_key).first()
    if not row:
        raise HTTPException(404, "阶段配置不存在")
    return success_response(data={
        "id": row.id,
        "module_key": row.module_key,
        "module_name": row.module_name,
        "start_time": row.start_time.isoformat(),
        "end_time": row.end_time.isoformat(),
        "student_lock_after_end": bool(row.student_lock_after_end),
        "teacher_lock_after_end": bool(row.teacher_lock_after_end),
        "description": row.description or "",
    })


# ---------------- 管理 ----------------
# 固定路径 /batch 必须在参数路径 /{module_key} 之前注册，否则会被吞掉
@router.put("/batch", summary="批量更新阶段时间（管理员）")
def batch_update(
    payloads: List[StageConfigUpsert],
    db: Session = Depends(get_db),
    _: any = Depends(require_admin),
):
    updated = []
    for p in payloads:
        p.validate_time()
        row = db.query(StageConfig).filter(StageConfig.module_key == p.module_key).first()
        if not row:
            row = StageConfig(module_key=p.module_key, module_name=p.module_name or p.module_key)
            db.add(row)
        row.module_name = p.module_name or row.module_name
        row.start_time = p.start_time
        row.end_time = p.end_time
        row.student_lock_after_end = p.student_lock_after_end
        row.teacher_lock_after_end = p.teacher_lock_after_end
        row.description = p.description
        updated.append(p.module_key)
    db.commit()
    return success_response(message="批量更新成功", data={"updated": updated})


@router.put("/{module_key}", summary="更新阶段时间（管理员）")
def update_stage(
    module_key: str,
    payload: StageConfigUpsert,
    db: Session = Depends(get_db),
    _: any = Depends(require_admin),
):
    payload.validate_time()
    row = db.query(StageConfig).filter(StageConfig.module_key == module_key).first()
    if not row:
        row = StageConfig(module_key=module_key, module_name=payload.module_name or module_key)
        db.add(row)
    row.module_name = payload.module_name or row.module_name
    row.start_time = payload.start_time
    row.end_time = payload.end_time
    row.student_lock_after_end = payload.student_lock_after_end
    row.teacher_lock_after_end = payload.teacher_lock_after_end
    row.description = payload.description
    db.commit()
    db.refresh(row)
    return success_response(message="更新成功", data={"module_key": row.module_key})
