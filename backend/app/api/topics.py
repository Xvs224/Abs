"""
选题 API 路由
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.response import success_response, page_response
from app.core.security import get_current_user, require_admin, require_teacher, require_student, require_student_or_teacher
from app.schemas.topic import TopicCreate, TopicUpdate, TopicReview, TopicResponse, TopicDuplicateCheck
from app.schemas.common import PaginationParams, SuccessResponse
from app.models.user import User
from app.services import topic_service

router = APIRouter(prefix="/api/topics", tags=["选题管理"])


@router.get("", summary="选题列表")
def list_topics(
    params: PaginationParams = Depends(),
    status: str = Query(None, description="状态过滤"),
    student_id: int = Query(None, description="学生ID过滤"),
    teacher_id: int = Query(None, description="教师ID过滤"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student_or_teacher),
):
    """获取选题列表，支持关键词搜索和分页"""
    # 数据隔离：学生只能看到自己的选题
    if current_user.role == "student":
        student_id = current_user.id
    # 教师只能看到自己指导的选题
    elif current_user.role == "teacher":
        teacher_id = current_user.id

    items, total = topic_service.get_topic_list(db, params, status, student_id, teacher_id)
    return page_response(items=items, total=total, page=params.page, page_size=params.page_size)


@router.post("", summary="创建选题")
def create_topic(
    data: TopicCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student),
):
    """学生创建选题"""
    result = topic_service.create_topic(db, data, current_user.id)
    return success_response(data=result, message="选题创建成功")


@router.get("/{topic_id}", summary="选题详情")
def get_topic(
    topic_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student_or_teacher),
):
    """获取选题详情"""
    result = topic_service.get_topic_detail(db, topic_id)
    # 数据隔离：学生只能查看自己的选题
    if current_user.role == "student" and result.student_id != current_user.id:
        from app.core.exceptions import BusinessException
        raise BusinessException(403, "无权查看他人的选题")
    return success_response(data=result)


@router.put("/{topic_id}", summary="更新选题")
def update_topic(
    topic_id: int,
    data: TopicUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student_or_teacher),
):
    """更新选题信息"""
    result = topic_service.update_topic(db, topic_id, data, current_user)
    return success_response(data=result, message="选题更新成功")


@router.delete("/{topic_id}", summary="删除选题")
def delete_topic(
    topic_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student_or_teacher),
):
    """删除选题"""
    topic_service.delete_topic(db, topic_id, current_user)
    return success_response(message="选题删除成功")


@router.post("/{topic_id}/review", summary="审核选题")
def review_topic(
    topic_id: int,
    data: TopicReview,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher),
):
    """教师/管理员审核选题"""
    result = topic_service.review_topic(db, topic_id, data, current_user.id)
    return success_response(data=result, message="审核完成")


@router.post("/check-duplicate", summary="选题重复检测")
def check_duplicate(
    title: str = Query(..., description="选题标题"),
    topic_id: int = Query(None, description="排除的选题ID（编辑时使用）"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student),
):
    """检测选题是否与现有选题重复"""
    result = topic_service.check_duplicate(db, title, topic_id)
    return success_response(data=result)
