"""
中期检查 API 路由
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.response import success_response, page_response
from app.core.security import get_current_user, require_teacher, require_student, require_student_or_teacher
from app.schemas.midterm import (
    MidtermCheckCreate, MidtermCheckUpdate, MidtermReview, MidtermSubmit, MidtermCheckResponse,
    RectificationCreate, RectificationSubmit, RectificationReview, RectificationResponse,
)
from app.schemas.common import PaginationParams
from app.models.user import User
from app.services import midterm_service

router = APIRouter(prefix="/api/midterm", tags=["中期检查"])


# ==================== 中期检查 ====================

@router.get("", summary="中期检查列表")
def list_midterms(
    params: PaginationParams = Depends(),
    status: str = Query(None, description="状态过滤"),
    student_id: int = Query(None, description="学生ID过滤"),
    teacher_id: int = Query(None, description="教师ID过滤"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student_or_teacher),
):
    """获取中期检查列表，支持关键词搜索和分页"""
    # 数据隔离
    if current_user.role == "student":
        student_id = current_user.id
    elif current_user.role == "teacher":
        teacher_id = current_user.id

    items, total = midterm_service.get_midterm_list(db, params, status, student_id, teacher_id)
    return page_response(items=items, total=total, page=params.page, page_size=params.page_size)


@router.post("", summary="创建/更新中期检查")
def create_or_update_midterm(
    data: MidtermCheckCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student),
):
    """学生创建或更新中期检查（草稿）"""
    result = midterm_service.create_or_update_midterm(db, data, current_user.id)
    return success_response(data=result, message="中期检查保存成功")


@router.get("/{midterm_id}", summary="中期检查详情")
def get_midterm(
    midterm_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student_or_teacher),
):
    """获取中期检查详情"""
    result = midterm_service.get_midterm_detail(db, midterm_id)
    return success_response(data=result)


@router.put("/{midterm_id}", summary="更新中期检查")
def update_midterm(
    midterm_id: int,
    data: MidtermCheckUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student_or_teacher),
):
    """更新中期检查信息"""
    result = midterm_service.update_midterm(db, midterm_id, data, current_user)
    return success_response(data=result, message="中期检查更新成功")


@router.post("/{midterm_id}/submit", summary="提交中期检查")
def submit_midterm(
    midterm_id: int,
    data: MidtermSubmit = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student),
):
    """学生提交中期检查待评审"""
    result = midterm_service.submit_midterm(db, midterm_id, current_user.id)
    return success_response(data=result, message="中期检查提交成功")


@router.post("/{midterm_id}/review", summary="评审中期检查")
def review_midterm(
    midterm_id: int,
    data: MidtermReview,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher),
):
    """教师/管理员评审中期检查"""
    result = midterm_service.review_midterm(db, midterm_id, data, current_user.id)
    return success_response(data=result, message="评审完成")


# ==================== 整改管理 ====================

@router.get("/rectifications", summary="整改列表")
def list_rectifications(
    params: PaginationParams = Depends(),
    midterm_id: int = Query(None, description="中期检查ID过滤"),
    topic_id: int = Query(None, description="选题ID过滤"),
    status: str = Query(None, description="状态过滤"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student_or_teacher),
):
    """获取整改列表，支持关键词搜索和分页"""
    items, total = midterm_service.get_rectification_list(db, params, midterm_id, topic_id, status)
    return page_response(items=items, total=total, page=params.page, page_size=params.page_size)


@router.post("/rectifications", summary="创建整改")
def create_rectification(
    data: RectificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher),
):
    """教师创建整改要求"""
    result = midterm_service.create_rectification(db, data, current_user)
    return success_response(data=result, message="整改创建成功")


@router.get("/rectifications/{rect_id}", summary="整改详情")
def get_rectification(
    rect_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student_or_teacher),
):
    """获取整改详情"""
    result = midterm_service.get_rectification_detail(db, rect_id)
    return success_response(data=result)


@router.put("/rectifications/{rect_id}", summary="更新整改")
def update_rectification(
    rect_id: int,
    data: RectificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher),
):
    """更新整改信息"""
    update_data = data.model_dump(exclude_unset=True)
    result = midterm_service.update_rectification(db, rect_id, update_data, current_user)
    return success_response(data=result, message="整改更新成功")


@router.delete("/rectifications/{rect_id}", summary="删除整改")
def delete_rectification(
    rect_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher),
):
    """删除整改"""
    midterm_service.delete_rectification(db, rect_id, current_user)
    return success_response(message="整改删除成功")


@router.post("/rectifications/{rect_id}/submit", summary="提交整改材料")
def submit_rectification(
    rect_id: int,
    data: RectificationSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student),
):
    """学生提交整改材料待复检"""
    result = midterm_service.submit_rectification(db, rect_id, data, current_user.id)
    return success_response(data=result, message="整改提交成功")


@router.post("/rectifications/{rect_id}/review", summary="复检整改")
def review_rectification(
    rect_id: int,
    data: RectificationReview,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher),
):
    """教师复检整改结果"""
    result = midterm_service.review_rectification(db, rect_id, data, current_user.id)
    return success_response(data=result, message="复检完成")
