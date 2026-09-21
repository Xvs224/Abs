"""
指导计划与记录 API 路由
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.response import success_response, page_response
from app.core.security import get_current_user, require_teacher, require_student_or_teacher
from app.schemas.guidance import (
    GuidancePlanCreate, GuidancePlanUpdate, GuidancePlanResponse,
    GuidanceRecordCreate, GuidanceRecordUpdate, GuidanceRecordResponse,
)
from app.schemas.common import PaginationParams
from app.models.user import User
from app.services import guidance_service

router = APIRouter(prefix="/api/guidance", tags=["指导管理"])


# ==================== 指导计划 ====================

@router.get("/plans", summary="指导计划列表")
def list_plans(
    params: PaginationParams = Depends(),
    status: str = Query(None, description="状态过滤"),
    student_id: int = Query(None, description="学生ID过滤"),
    teacher_id: int = Query(None, description="教师ID过滤"),
    topic_id: int = Query(None, description="选题ID过滤"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student_or_teacher),
):
    # 数据隔离：学生只能看到自己的指导计划
    if current_user.role == "student":
        student_id = current_user.id
    elif current_user.role == "teacher":
        teacher_id = current_user.id
    """获取指导计划列表，支持关键词搜索和分页"""
    items, total = guidance_service.get_plan_list(
        db, params, status, student_id, teacher_id, topic_id
    )
    return page_response(items=items, total=total, page=params.page, page_size=params.page_size)


@router.post("/plans", summary="创建指导计划")
def create_plan(
    data: GuidancePlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher),
):
    """教师创建指导计划"""
    result = guidance_service.create_plan(db, data, current_user.id)
    return success_response(data=result, message="指导计划创建成功")


@router.get("/plans/{plan_id}", summary="指导计划详情")
def get_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student_or_teacher),
):
    """获取指导计划详情"""
    result = guidance_service.get_plan_detail(db, plan_id)
    return success_response(data=result)


@router.put("/plans/{plan_id}", summary="更新指导计划")
def update_plan(
    plan_id: int,
    data: GuidancePlanUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher),
):
    """更新指导计划信息"""
    result = guidance_service.update_plan(db, plan_id, data, current_user)
    return success_response(data=result, message="指导计划更新成功")


@router.delete("/plans/{plan_id}", summary="删除指导计划")
def delete_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher),
):
    """删除指导计划"""
    guidance_service.delete_plan(db, plan_id, current_user)
    return success_response(message="指导计划删除成功")


# ==================== 指导记录 ====================

@router.get("/records", summary="指导记录列表")
def list_records(
    params: PaginationParams = Depends(),
    plan_id: int = Query(None, description="计划ID过滤"),
    topic_id: int = Query(None, description="选题ID过滤"),
    student_id: int = Query(None, description="学生ID过滤"),
    teacher_id: int = Query(None, description="教师ID过滤"),
    record_type: str = Query(None, description="指导类型过滤"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student_or_teacher),
):
    """获取指导记录列表，支持关键词搜索和分页"""
    # 数据隔离：学生只能看到自己的指导记录
    if current_user.role == "student":
        student_id = current_user.id
    elif current_user.role == "teacher":
        teacher_id = current_user.id

    items, total = guidance_service.get_record_list(
        db, params, plan_id, topic_id, student_id, teacher_id, record_type
    )
    return page_response(items=items, total=total, page=params.page, page_size=params.page_size)


@router.post("/records", summary="创建指导记录")
def create_record(
    data: GuidanceRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher),
):
    """教师创建指导记录"""
    result = guidance_service.create_record(db, data, current_user.id)
    return success_response(data=result, message="指导记录创建成功")


@router.get("/records/{record_id}", summary="指导记录详情")
def get_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student_or_teacher),
):
    """获取指导记录详情"""
    result = guidance_service.get_record_detail(db, record_id)
    return success_response(data=result)


@router.put("/records/{record_id}", summary="更新指导记录")
def update_record(
    record_id: int,
    data: GuidanceRecordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher),
):
    """更新指导记录信息"""
    result = guidance_service.update_record(db, record_id, data, current_user)
    return success_response(data=result, message="指导记录更新成功")


@router.delete("/records/{record_id}", summary="删除指导记录")
def delete_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher),
):
    """删除指导记录"""
    guidance_service.delete_record(db, record_id, current_user)
    return success_response(message="指导记录删除成功")
