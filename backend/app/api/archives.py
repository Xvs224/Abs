"""
成果归档 API 路由
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.response import success_response, page_response
from app.core.security import get_current_user, require_admin, require_admin_or_teacher, require_teacher_only, require_student, require_student_or_teacher, require_any_authenticated
from app.schemas.archive import ArchiveCreate, ArchiveUpdate, ArchiveReview, ArchiveResponse
from app.schemas.common import PaginationParams
from app.models.user import User
from app.services import archive_service

router = APIRouter(prefix="/api/archives", tags=["成果归档"])


@router.get("", summary="归档列表")
def list_archives(
    params: PaginationParams = Depends(),
    status: str = Query(None, description="状态过滤"),
    student_id: int = Query(None, description="学生ID过滤"),
    teacher_id: int = Query(None, description="教师ID过滤"),
    final_grade: str = Query(None, description="最终等级过滤"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student_or_teacher),
):
    """获取归档列表，支持关键词搜索和分页"""
    # 数据隔离
    if current_user.role == "student":
        student_id = current_user.id
    elif current_user.role == "teacher":
        teacher_id = current_user.id

    items, total = archive_service.get_archive_list(
        db, params, status, student_id, teacher_id, final_grade
    )
    return page_response(items=items, total=total, page=params.page, page_size=params.page_size)


@router.post("", summary="创建归档申请")
def create_archive(
    data: ArchiveCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student),
):
    """学生创建归档申请"""
    result = archive_service.create_archive(db, data, current_user.id)
    return success_response(data=result, message="归档申请创建成功")


@router.get("/{archive_id}", summary="归档详情")
def get_archive(
    archive_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student_or_teacher),
):
    """获取归档详情"""
    result = archive_service.get_archive_detail(db, archive_id)
    return success_response(data=result)


@router.put("/{archive_id}", summary="更新归档")
def update_archive(
    archive_id: int,
    data: ArchiveUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student_or_teacher),
):
    """更新归档信息"""
    result = archive_service.update_archive(db, archive_id, data, current_user)
    return success_response(data=result, message="归档更新成功")


@router.delete("/{archive_id}", summary="删除归档")
def delete_archive(
    archive_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_authenticated),
):
    """删除归档（管理员可删除任意）"""
    archive_service.delete_archive(db, archive_id, current_user)
    return success_response(message="归档删除成功")


@router.post("/{archive_id}/resubmit", summary="重交归档")
def resubmit_archive(
    archive_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_authenticated),
):
    """重交归档（管理员可强制重置为待审核，学生仅能重交被退回的）"""
    result = archive_service.resubmit_archive(db, archive_id, current_user)
    return success_response(data=result, message="归档已重置，可重新提交")


@router.post("/{archive_id}/review", summary="审核归档")
def review_archive(
    archive_id: int,
    data: ArchiveReview,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_only),
):
    """教师/管理员审核归档"""
    result = archive_service.review_archive(db, archive_id, data, current_user.id)
    return success_response(data=result, message="审核完成")
