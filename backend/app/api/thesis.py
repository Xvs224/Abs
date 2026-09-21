"""
论文版本 API 路由
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.response import success_response, page_response
from app.core.security import get_current_user, require_teacher, require_student, require_student_or_teacher
from app.schemas.thesis import (
    ThesisVersionCreate, ThesisVersionUpdate, ThesisVersionResponse,
    FormatCheckResult, VersionCompareResponse,
)
from app.schemas.common import PaginationParams
from app.models.user import User
from app.services import thesis_service

router = APIRouter(prefix="/api/thesis", tags=["论文版本"])


# ==================== 版本管理 ====================

@router.get("/versions", summary="论文版本列表")
def list_versions(
    params: PaginationParams = Depends(),
    topic_id: int = Query(None, description="选题ID过滤"),
    student_id: int = Query(None, description="学生ID过滤"),
    format_check_status: str = Query(None, description="格式检测状态过滤"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student_or_teacher),
):
    """获取论文版本列表，支持关键词搜索和分页"""
    # 数据隔离
    if current_user.role == "student":
        student_id = current_user.id

    items, total = thesis_service.get_version_list(
        db, params, topic_id, student_id, format_check_status
    )
    return page_response(items=items, total=total, page=params.page, page_size=params.page_size)


@router.post("/versions", summary="上传论文版本")
def create_version(
    data: ThesisVersionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student),
):
    """学生上传新的论文版本"""
    result = thesis_service.create_version(db, data, current_user.id)
    return success_response(data=result, message="论文版本上传成功")


@router.get("/versions/{version_id}", summary="论文版本详情")
def get_version(
    version_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student_or_teacher),
):
    """获取论文版本详情"""
    result = thesis_service.get_version_detail(db, version_id)
    return success_response(data=result)


@router.put("/versions/{version_id}", summary="更新论文版本")
def update_version(
    version_id: int,
    data: ThesisVersionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student_or_teacher),
):
    """更新论文版本信息"""
    result = thesis_service.update_version(db, version_id, data, current_user)
    return success_response(data=result, message="论文版本更新成功")


@router.delete("/versions/{version_id}", summary="删除论文版本")
def delete_version(
    version_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student_or_teacher),
):
    """删除论文版本"""
    thesis_service.delete_version(db, version_id, current_user)
    return success_response(message="论文版本删除成功")


@router.post("/versions/{version_id}/format-check", summary="执行格式检测")
def run_format_check(
    version_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student),
):
    """对论文版本执行格式检测"""
    result = thesis_service.run_format_check(db, version_id)
    return success_response(data=result, message="格式检测完成")


@router.get("/versions/{version_id}/format-check", summary="获取格式检测结果")
def get_format_check(
    version_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student_or_teacher),
):
    """获取论文版本的格式检测结果"""
    result = thesis_service.get_format_check_result(db, version_id)
    return success_response(data=result)


@router.get("/versions/compare", summary="版本对比")
def compare_versions(
    version_a_id: int = Query(..., description="版本A ID"),
    version_b_id: int = Query(..., description="版本B ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student_or_teacher),
):
    """对比两个论文版本的差异"""
    result = thesis_service.compare_versions(db, version_a_id, version_b_id)
    return success_response(data=result)
