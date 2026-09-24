"""过程指导记录 API"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.response import success_response, page_response
from app.core.security import get_current_user, require_any_authenticated
from app.models.user import User
from app.schemas.guidance import GuidanceCreate, GuidanceReply, GuidanceTeacherReply, GuidanceUpdate
import app.services.guidance_service as guidance_service

router = APIRouter(prefix="/api/guidance", tags=["过程指导"])


@router.post("", summary="创建指导记录")
def create_guidance(
    data: GuidanceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_authenticated),
):
    result = guidance_service.create_guidance(db, data, current_user.id, current_user.role)
    return success_response(data=result, message="指导记录创建成功")


@router.get("", summary="指导记录列表")
def list_guidance(
    topic_id: Optional[int] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_authenticated),
):
    items, total = guidance_service.get_guidance_list(
        db, current_user.id, current_user.role, topic_id, status, page, page_size
    )
    return page_response(items=items, total=total, page=page, page_size=page_size)


@router.get("/{record_id}", summary="指导记录详情")
def get_guidance(
    record_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_any_authenticated),
):
    result = guidance_service.get_guidance_detail(db, record_id)
    return success_response(data=result)


@router.put("/{record_id}", summary="更新指导记录")
def update_guidance(
    record_id: int,
    data: GuidanceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_authenticated),
):
    result = guidance_service.update_guidance(db, record_id, data, current_user.id, current_user.role)
    return success_response(data=result, message="更新成功")


@router.post("/{record_id}/reply", summary="学生回复指导")
def reply_guidance(
    record_id: int,
    data: GuidanceReply,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_authenticated),
):
    result = guidance_service.reply_guidance(db, record_id, data, current_user.id)
    return success_response(data=result, message="回复成功")


@router.post("/{record_id}/teacher-reply", summary="教师回复学生提问")
def teacher_reply_guidance(
    record_id: int,
    data: GuidanceTeacherReply,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_authenticated),
):
    result = guidance_service.teacher_reply_guidance(db, record_id, data, current_user.id)
    return success_response(data=result, message="回复成功")


@router.delete("/{record_id}", summary="删除指导记录")
def delete_guidance(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_authenticated),
):
    guidance_service.delete_guidance(db, record_id, current_user.id, current_user.role)
    return success_response(message="删除成功")
