"""
评阅与答辩服务模块
"""
from typing import List, Optional, Tuple
from datetime import datetime
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.review import Review, Defense
from app.models.topic import Topic
from app.models.user import User
from app.schemas.review import (
    ReviewCreate, ReviewSubmit, ReviewResponse,
    DefenseCreate, DefenseScore, DefenseResponse,
)
from app.core.exceptions import NotFoundException, BusinessException, ConflictException
from app.schemas.common import PaginationParams


# ==================== 评阅管理 ====================

def _enrich_review(review: Review) -> dict:
    """补充评阅关联信息"""
    data = {c.name: getattr(review, c.name) for c in review.__table__.columns}
    data["topic_title"] = review.topic.title if review.topic else ""
    data["student_name"] = review.student.real_name if review.student else ""
    data["reviewer_name"] = review.reviewer.real_name if review.reviewer else ""
    return data


def get_review_by_id(db: Session, review_id: int) -> Optional[Review]:
    """根据ID获取评阅"""
    return db.query(Review).filter(Review.id == review_id).first()


def get_review_detail(db: Session, review_id: int) -> ReviewResponse:
    """获取评阅详情"""
    review = get_review_by_id(db, review_id)
    if not review:
        raise NotFoundException("评阅不存在")
    return ReviewResponse(**_enrich_review(review))


def get_review_list(
    db: Session,
    params: PaginationParams,
    status: Optional[str] = None,
    topic_id: Optional[int] = None,
    student_id: Optional[int] = None,
    reviewer_id: Optional[int] = None,
    review_type: Optional[str] = None,
) -> Tuple[List[ReviewResponse], int]:
    """获取评阅列表"""
    query = db.query(Review).join(User, Review.reviewer_id == User.id, isouter=True)

    # 关键词搜索
    if params.keyword:
        keyword = f"%{params.keyword}%"
        query = query.join(Topic, Review.topic_id == Topic.id, isouter=True)
        query = query.filter(
            or_(
                Topic.title.like(keyword),
                Review.opinion.like(keyword),
                User.real_name.like(keyword),
            )
        )

    # 状态过滤
    if status:
        query = query.filter(Review.status == status)

    # 选题过滤
    if topic_id:
        query = query.filter(Review.topic_id == topic_id)

    # 学生过滤
    if student_id:
        query = query.filter(Review.student_id == student_id)

    # 评阅教师过滤
    if reviewer_id:
        query = query.filter(Review.reviewer_id == reviewer_id)

    # 类型过滤
    if review_type:
        query = query.filter(Review.review_type == review_type)

    # 总数
    total = query.count()

    # 排序
    sort_column = getattr(Review, params.sort_by, Review.id)
    if params.sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    # 分页
    offset = (params.page - 1) * params.page_size
    reviews = query.offset(offset).limit(params.page_size).all()

    items = [ReviewResponse(**_enrich_review(r)) for r in reviews]
    return items, total


def assign_review(db: Session, data: ReviewCreate) -> ReviewResponse:
    """分配评阅任务"""
    # 检查选题是否存在
    topic = db.query(Topic).filter(Topic.id == data.topic_id).first()
    if not topic:
        raise NotFoundException("选题不存在")

    # 检查评阅教师是否存在
    reviewer = db.query(User).filter(User.id == data.reviewer_id).first()
    if not reviewer or reviewer.role not in ["teacher", "admin"]:
        raise BusinessException(400, "评阅教师不存在或无评阅权限")

    # 检查是否已分配给同一教师
    existing = db.query(Review).filter(
        Review.topic_id == data.topic_id,
        Review.reviewer_id == data.reviewer_id,
        Review.review_type == data.review_type,
    ).first()
    if existing:
        raise ConflictException("该选题已分配给此评阅教师")

    review = Review(
        topic_id=data.topic_id,
        student_id=topic.student_id,
        reviewer_id=data.reviewer_id,
        review_type=data.review_type,
        version_id=data.version_id,
        deadline=data.deadline,
        status="reviewing",
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return ReviewResponse(**_enrich_review(review))


def submit_review(db: Session, review_id: int, data: ReviewSubmit, reviewer_id: int) -> ReviewResponse:
    """提交评阅结果"""
    review = get_review_by_id(db, review_id)
    if not review:
        raise NotFoundException("评阅不存在")

    if review.reviewer_id != reviewer_id:
        raise BusinessException(403, "无权提交他人的评阅")

    if review.status != "reviewing":
        raise BusinessException(400, "该评阅已完成，不可重复提交")

    review.topic_score = data.topic_score
    review.content_score = data.content_score
    review.method_score = data.method_score
    review.innovation_score = data.innovation_score
    review.format_score = data.format_score

    # 计算总分（取平均值或加权平均）
    if data.total_score is not None:
        review.total_score = data.total_score
    else:
        review.total_score = round(
            (data.topic_score + data.content_score + data.method_score +
             data.innovation_score + data.format_score) / 5, 2
        )

    review.opinion = data.opinion
    review.suggestions = data.suggestions
    review.result = data.result
    review.review_time = datetime.utcnow()
    review.status = "completed"

    db.commit()
    db.refresh(review)
    return ReviewResponse(**_enrich_review(review))


def delete_review(db: Session, review_id: int) -> None:
    """删除评阅分配"""
    review = get_review_by_id(db, review_id)
    if not review:
        raise NotFoundException("评阅不存在")

    if review.status == "completed":
        raise BusinessException(400, "已完成的评阅不可删除")

    db.delete(review)
    db.commit()


# ==================== 答辩管理 ====================

def _enrich_defense(defense: Defense) -> dict:
    """补充答辩关联信息"""
    data = {c.name: getattr(defense, c.name) for c in defense.__table__.columns}
    data["topic_title"] = defense.topic.title if defense.topic else ""
    data["student_name"] = defense.student.real_name if defense.student else ""
    data["chair_name"] = defense.chair.real_name if defense.chair else ""
    return data


def get_defense_by_id(db: Session, defense_id: int) -> Optional[Defense]:
    """根据ID获取答辩"""
    return db.query(Defense).filter(Defense.id == defense_id).first()


def get_defense_by_topic_id(db: Session, topic_id: int) -> Optional[Defense]:
    """根据选题ID获取答辩"""
    return db.query(Defense).filter(Defense.topic_id == topic_id).first()


def get_defense_detail(db: Session, defense_id: int) -> DefenseResponse:
    """获取答辩详情"""
    defense = get_defense_by_id(db, defense_id)
    if not defense:
        raise NotFoundException("答辩安排不存在")
    return DefenseResponse(**_enrich_defense(defense))


def get_defense_list(
    db: Session,
    params: PaginationParams,
    status: Optional[str] = None,
    student_id: Optional[int] = None,
    defense_form: Optional[str] = None,
    result: Optional[str] = None,
) -> Tuple[List[DefenseResponse], int]:
    """获取答辩列表"""
    query = db.query(Defense).join(User, Defense.student_id == User.id, isouter=True)

    # 关键词搜索
    if params.keyword:
        keyword = f"%{params.keyword}%"
        query = query.join(Topic, Defense.topic_id == Topic.id, isouter=True)
        query = query.filter(
            or_(
                Topic.title.like(keyword),
                Defense.location.like(keyword),
                User.real_name.like(keyword),
            )
        )

    # 状态过滤
    if status:
        query = query.filter(Defense.status == status)

    # 学生过滤
    if student_id:
        query = query.filter(Defense.student_id == student_id)

    # 形式过滤
    if defense_form:
        query = query.filter(Defense.defense_form == defense_form)

    # 结果过滤
    if result:
        query = query.filter(Defense.result == result)

    # 总数
    total = query.count()

    # 排序
    sort_column = getattr(Defense, params.sort_by, Defense.defense_date)
    if params.sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    # 分页
    offset = (params.page - 1) * params.page_size
    defenses = query.offset(offset).limit(params.page_size).all()

    items = [DefenseResponse(**_enrich_defense(d)) for d in defenses]
    return items, total


def create_defense(db: Session, data: DefenseCreate) -> DefenseResponse:
    """安排答辩"""
    # 检查选题是否存在
    topic = db.query(Topic).filter(Topic.id == data.topic_id).first()
    if not topic:
        raise NotFoundException("选题不存在")

    # 检查是否已有答辩安排
    existing = get_defense_by_topic_id(db, data.topic_id)
    if existing:
        raise ConflictException("该选题已有答辩安排")

    defense = Defense(
        topic_id=data.topic_id,
        student_id=topic.student_id,
        defense_date=data.defense_date,
        defense_time_start=data.defense_time_start,
        defense_time_end=data.defense_time_end,
        location=data.location,
        defense_form=data.defense_form,
        chair_id=data.chair_id,
        committee_members=data.committee_members,
        secretary_id=data.secretary_id,
        status="scheduled",
    )
    db.add(defense)
    db.commit()
    db.refresh(defense)
    return DefenseResponse(**_enrich_defense(defense))


def update_defense(db: Session, defense_id: int, data: dict) -> DefenseResponse:
    """更新答辩安排"""
    defense = get_defense_by_id(db, defense_id)
    if not defense:
        raise NotFoundException("答辩安排不存在")

    if defense.status == "completed":
        raise BusinessException(400, "已完成的答辩不可修改")

    for key, value in data.items():
        if value is not None:
            setattr(defense, key, value)

    db.commit()
    db.refresh(defense)
    return DefenseResponse(**_enrich_defense(defense))


def delete_defense(db: Session, defense_id: int) -> None:
    """删除答辩安排"""
    defense = get_defense_by_id(db, defense_id)
    if not defense:
        raise NotFoundException("答辩安排不存在")

    if defense.status == "completed":
        raise BusinessException(400, "已完成的答辩不可删除")

    db.delete(defense)
    db.commit()


def score_defense(db: Session, defense_id: int, data: DefenseScore) -> DefenseResponse:
    """答辩评分"""
    defense = get_defense_by_id(db, defense_id)
    if not defense:
        raise NotFoundException("答辩安排不存在")

    if defense.status == "completed":
        raise BusinessException(400, "该答辩已完成评分，不可重复提交")

    defense.presentation_score = data.presentation_score
    defense.qa_score = data.qa_score
    defense.thesis_quality_score = data.thesis_quality_score

    # 计算总分
    if data.total_score is not None:
        defense.total_score = data.total_score
    else:
        defense.total_score = round(
            (data.presentation_score + data.qa_score + data.thesis_quality_score) / 3, 2
        )

    # 计算等级
    if not data.grade:
        if defense.total_score >= 90:
            defense.grade = "excellent"
        elif defense.total_score >= 80:
            defense.grade = "good"
        elif defense.total_score >= 70:
            defense.grade = "medium"
        elif defense.total_score >= 60:
            defense.grade = "pass"
        else:
            defense.grade = "fail"
    else:
        defense.grade = data.grade

    defense.opinion = data.opinion
    defense.suggestions = data.suggestions
    defense.result = data.result
    defense.status = "completed"

    db.commit()
    db.refresh(defense)
    return DefenseResponse(**_enrich_defense(defense))
