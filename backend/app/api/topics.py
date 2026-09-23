"""
选题 API 路由
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.response import success_response, page_response
from app.core.security import get_current_user, require_admin, require_admin_or_teacher, require_teacher_only, require_student, require_student_or_teacher, require_any_authenticated
from app.schemas.topic import (
    TopicCreate, TopicUpdate, TopicReview, TopicResponse, TopicDuplicateCheck,
    TeacherTopicCreate, StudentTopicCreate, TopicSelect
)
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
    source_type: str = Query(None, description="选题类型过滤: teacher/student"),
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

    items, total = topic_service.get_topic_list(db, params, status, student_id, teacher_id, source_type)
    return page_response(items=items, total=total, page=params.page, page_size=params.page_size)


@router.get("/available", summary="可选选题列表（学生）")
def list_available_topics(
    params: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student),
):
    """学生查看所有教师发布的可选选题"""
    items, total = topic_service.get_available_topics(db, params)
    return page_response(items=items, total=total, page=params.page, page_size=params.page_size)


@router.post("/teacher/publish", summary="教师发布选题")
def teacher_publish_topic(
    data: TeacherTopicCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_only),
):
    """教师发布选题供学生选择"""
    result = topic_service.teacher_publish_topic(db, data, current_user.id)
    return success_response(data=result, message="选题发布成功")


@router.post("/student/select", summary="学生选择教师发布选题")
def student_select_topic(
    data: TopicSelect,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student),
):
    """学生从教师发布的选题中选择一个"""
    result = topic_service.student_select_topic(db, data.topic_id, current_user.id)
    return success_response(data=result, message="选题成功，等待教师审核")


@router.post("/student/self-propose", summary="学生自拟选题")
def student_self_propose(
    data: StudentTopicCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student),
):
    """学生自拟选题提交审核"""
    result = topic_service.student_create_topic(db, data, current_user.id)
    return success_response(data=result, message="选题已提交，等待审核")


@router.post("/{topic_id}/cancel", summary="学生取消选题")
def student_cancel_topic(
    topic_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student),
):
    """学生取消选择的选题（仅待审核状态）"""
    result = topic_service.student_cancel_select(db, topic_id, current_user.id)
    return success_response(data=result, message="已取消选题")


@router.post("", summary="创建选题（兼容旧接口）")
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


@router.post("/{topic_id}/resubmit", summary="重新提交选题")
def resubmit_topic(
    topic_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_authenticated),
):
    """重新提交被驳回的选题（管理员可强制重置）"""
    result = topic_service.resubmit_topic(db, topic_id, current_user)
    return success_response(data=result, message="选题已重置，可重新提交")


@router.post("/{topic_id}/review", summary="审核选题")
def review_topic(
    topic_id: int,
    data: TopicReview,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_only),
):
    """教师审核选题"""
    result = topic_service.review_topic(db, topic_id, data, current_user.id)
    return success_response(data=result, message="审核完成")


@router.post("/check-duplicate", summary="选题重复检测")
def check_duplicate(
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student_or_teacher),
):
    """检测选题是否与现有选题"""
    title = data.get("title", "")
    topic_id = data.get("topic_id")
    result = topic_service.check_duplicate(db, title, topic_id)
    return success_response(data=result)
