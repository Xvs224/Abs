"""
评阅与答辩 API 路由
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.response import success_response, page_response
from app.core.security import get_current_user, require_admin, require_admin_or_teacher, require_teacher_only, require_student_or_teacher
from app.schemas.review import (
    ReviewCreate, ReviewSubmit, ReviewResponse,
    DefenseCreate, DefenseScore, DefenseResponse,
)
from app.schemas.common import PaginationParams
from app.models.user import User
from app.services import review_service

router = APIRouter(tags=["评阅答辩"])

# 评阅路由前缀
review_router = APIRouter(prefix="/api/reviews", tags=["评阅管理"])
# 答辩路由前缀
defense_router = APIRouter(prefix="/api/defenses", tags=["答辩管理"])


# ==================== 评阅管理 ====================

@review_router.get("", summary="评阅列表")
def list_reviews(
    params: PaginationParams = Depends(),
    status: str = Query(None, description="状态过滤"),
    topic_id: int = Query(None, description="选题ID过滤"),
    student_id: int = Query(None, description="学生ID过滤"),
    reviewer_id: int = Query(None, description="评阅教师ID过滤"),
    review_type: str = Query(None, description="评阅类型过滤"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student_or_teacher),
):
    """获取评阅列表，支持关键词搜索和分页"""
    # 数据隔离
    if current_user.role == "student":
        student_id = current_user.id
    elif current_user.role == "teacher":
        reviewer_id = current_user.id

    items, total = review_service.get_review_list(
        db, params, status, topic_id, student_id, reviewer_id, review_type
    )
    return page_response(items=items, total=total, page=params.page, page_size=params.page_size)


@review_router.post("", summary="分配评阅")
def assign_review(
    data: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_only),
):
    """分配评阅任务给评阅教师"""
    result = review_service.assign_review(db, data)
    return success_response(data=result, message="评阅分配成功")


@review_router.get("/{review_id}", summary="评阅详情")
def get_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student_or_teacher),
):
    """获取评阅详情"""
    result = review_service.get_review_detail(db, review_id)
    return success_response(data=result)


@review_router.post("/{review_id}/submit", summary="提交评阅结果")
def submit_review(
    review_id: int,
    data: ReviewSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_only),
):
    """评阅教师提交评阅结果"""
    result = review_service.submit_review(db, review_id, data, current_user.id)
    return success_response(data=result, message="评阅提交成功")


@review_router.delete("/{review_id}", summary="删除评阅分配")
def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_teacher),
):
    """删除评阅分配（管理员或教师）"""
    review_service.delete_review(db, review_id)
    return success_response(message="评阅删除成功")


# ==================== 答辩管理 ====================

@defense_router.get("", summary="答辩列表")
def list_defenses(
    params: PaginationParams = Depends(),
    status: str = Query(None, description="状态过滤"),
    student_id: int = Query(None, description="学生ID过滤"),
    defense_form: str = Query(None, description="答辩形式过滤"),
    result: str = Query(None, description="答辩结果过滤"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student_or_teacher),
):
    """获取答辩列表，支持关键词搜索和分页"""
    # 数据隔离
    if current_user.role == "student":
        student_id = current_user.id

    items, total = review_service.get_defense_list(
        db, params, status, student_id, defense_form, result
    )
    return page_response(items=items, total=total, page=params.page, page_size=params.page_size)


@defense_router.post("", summary="安排答辩")
def create_defense(
    data: DefenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_only),
):
    """创建答辩安排"""
    result = review_service.create_defense(db, data)
    return success_response(data=result, message="答辩安排成功")


@defense_router.get("/{defense_id}", summary="答辩详情")
def get_defense(
    defense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student_or_teacher),
):
    """获取答辩详情"""
    result = review_service.get_defense_detail(db, defense_id)
    return success_response(data=result)


@defense_router.put("/{defense_id}", summary="更新答辩安排")
def update_defense(
    defense_id: int,
    data: DefenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_only),
):
    """更新答辩安排信息"""
    update_data = data.model_dump(exclude_unset=True)
    result = review_service.update_defense(db, defense_id, update_data)
    return success_response(data=result, message="答辩安排更新成功")


@defense_router.delete("/{defense_id}", summary="删除答辩安排")
def delete_defense(
    defense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_teacher),
):
    """删除答辩安排（管理员或教师）"""
    review_service.delete_defense(db, defense_id)
    return success_response(message="答辩安排删除成功")


@defense_router.post("/{defense_id}/score", summary="答辩评分")
def score_defense(
    defense_id: int,
    data: DefenseScore,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_only),
):
    """提交答辩评分结果"""
    result = review_service.score_defense(db, defense_id, data)
    return success_response(data=result, message="答辩评分完成")


# 合并到主路由
router.include_router(review_router)
router.include_router(defense_router)
