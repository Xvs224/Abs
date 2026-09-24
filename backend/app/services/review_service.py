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
    ReviewCreate, ReviewSubmit, ReviewResponse, ReviewApply,
    DefenseCreate, DefenseScore, DefenseResponse,
)
from app.core.exceptions import NotFoundException, BusinessException, ConflictException
from app.schemas.common import PaginationParams


# ==================== 评阅管理 ====================

_REVIEW_RESULT_TEXT = {
    "pass": "通过",
    "revision": "修改后答辩",
    "reject": "不通过",
}

def review_result_text(result: str) -> str:
    return _REVIEW_RESULT_TEXT.get(result, result or "未知")

_DEFENSE_RESULT_TEXT = {
    "pass": "通过",
    "fail": "未通过",
    "reargue": "需重新答辩",
}

def defense_result_text(result: str) -> str:
    return _DEFENSE_RESULT_TEXT.get(result, result or "未知")

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


def apply_review(db: Session, data: ReviewApply, student_id: int) -> ReviewResponse:
    """学生申请评阅（首次申请或再次评阅）

    规则：
    - 必须上传过论文版本
    - 若存在进行中（pending/reviewing）的评阅，不允许重复申请
    - 若最新评阅结果为 pass，不允许再次申请（需教师重新分配）
    - 若最新评阅结果为 reject/revision，允许使用新版本再次申请
    - 评阅教师默认为该选题的指导教师
    """
    # 获取学生选题
    topic = db.query(Topic).filter(Topic.student_id == student_id).first()
    if not topic:
        raise BusinessException(400, "您还没有选题，无法申请评阅")

    # 校验论文版本
    from app.models.thesis import ThesisVersion
    version = db.query(ThesisVersion).filter(
        ThesisVersion.id == data.version_id,
        ThesisVersion.student_id == student_id,
    ).first()
    if not version:
        raise NotFoundException("论文版本不存在或无权访问")

    # 检查是否有进行中的评阅
    ongoing = db.query(Review).filter(
        Review.topic_id == topic.id,
        Review.student_id == student_id,
        Review.status.in_(["pending", "reviewing"]),
    ).first()
    if ongoing:
        raise BusinessException(400, "您已有进行中的评阅，请等待评阅完成后再申请")

    # 检查最新评阅结果，决定是否允许再次申请
    latest = db.query(Review).filter(
        Review.topic_id == topic.id,
        Review.student_id == student_id,
        Review.status == "completed",
    ).order_by(Review.id.desc()).first()

    if latest:
        if latest.result == "pass":
            raise BusinessException(400, "您的论文评阅已通过，无需再次申请")
        # reject / revision 允许再次申请，版本由学生自行选择（前端会提醒确认）

    # 评阅教师默认为指导教师
    reviewer_id = topic.teacher_id
    if not reviewer_id:
        raise BusinessException(400, "该选题暂无指导教师，无法申请评阅，请联系管理员")

    reviewer = db.query(User).filter(User.id == reviewer_id).first()
    if not reviewer or reviewer.role not in ["teacher", "admin"]:
        raise BusinessException(400, "指导教师信息异常，无法申请评阅")

    review = Review(
        topic_id=topic.id,
        student_id=student_id,
        reviewer_id=reviewer_id,
        review_type=data.review_type,
        version_id=data.version_id,
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
    # 评阅意见书文件
    if data.review_file_id:
        review.review_file_id = data.review_file_id
    if data.review_file_path:
        review.review_file_path = data.review_file_path
    if data.review_file_name:
        review.review_file_name = data.review_file_name

    db.commit()
    db.refresh(review)
    return ReviewResponse(**_enrich_review(review))


def update_review(db: Session, review_id: int, data: ReviewSubmit, operator_id: int, operator_role: str) -> ReviewResponse:
    """修改评阅结果（教师或管理员，可修改已完成的评阅）"""
    review = get_review_by_id(db, review_id)
    if not review:
        raise NotFoundException("评阅不存在")

    # 权限：管理员可改所有；教师只能改自己作为评阅人的评阅
    if operator_role != "admin" and review.reviewer_id != operator_id:
        raise BusinessException(403, "无权修改他人的评阅")

    review.topic_score = data.topic_score
    review.content_score = data.content_score
    review.method_score = data.method_score
    review.innovation_score = data.innovation_score
    review.format_score = data.format_score

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
    # 评阅意见书文件
    if data.review_file_id:
        review.review_file_id = data.review_file_id
    if data.review_file_path:
        review.review_file_path = data.review_file_path
    if data.review_file_name:
        review.review_file_name = data.review_file_name

    db.commit()
    db.refresh(review)
    return ReviewResponse(**_enrich_review(review))


def delete_review(db: Session, review_id: int, operator_role: str = None) -> None:
    """删除评阅分配（管理员可删除所有；教师不可删除已完成的评阅）"""
    review = get_review_by_id(db, review_id)
    if not review:
        raise NotFoundException("评阅不存在")

    # 教师不可删除已完成的评阅，管理员无限制
    if operator_role != "admin" and review.status == "completed":
        raise BusinessException(400, "已完成的评阅不可删除")

    db.delete(review)
    db.commit()


# ==================== 答辩管理 ====================

def _enrich_defense(defense: Defense, db: Session) -> dict:
    """补充答辩关联信息"""
    data = {c.name: getattr(defense, c.name) for c in defense.__table__.columns}
    data["topic_title"] = defense.topic.title if defense.topic else ""
    data["student_name"] = defense.student.real_name if defense.student else ""
    data["chair_name"] = defense.chair.real_name if defense.chair else ""
    data["secretary_name"] = defense.secretary.real_name if defense.secretary else ""
    # 将委员会成员ID转为姓名
    if defense.committee_members:
        ids = [int(x) for x in defense.committee_members.split(",") if x.strip().isdigit()]
        if ids:
            members = db.query(User).filter(User.id.in_(ids)).all()
            name_map = {u.id: u.real_name for u in members}
            names = [name_map.get(i, str(i)) for i in ids]
            data["committee_member_names"] = "、".join(names)
        else:
            data["committee_member_names"] = defense.committee_members
    else:
        data["committee_member_names"] = ""
    # 补充该选题最新评阅结果，用于前端判断是否可安排答辩
    review = db.query(Review).filter(
        Review.topic_id == defense.topic_id,
        Review.status == "completed"
    ).order_by(Review.id.desc()).first()
    data["review_result"] = review.result if review else ""
    data["review_result_text"] = review_result_text(review.result) if review else "未评阅"
    data["review_passed"] = bool(review and review.result == "pass")
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
    return DefenseResponse(**_enrich_defense(defense, db))


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

    items = [DefenseResponse(**_enrich_defense(d, db)) for d in defenses]
    return items, total


def create_defense(db: Session, data: DefenseCreate) -> DefenseResponse:
    """安排答辩"""
    # 检查选题是否存在
    topic = db.query(Topic).filter(Topic.id == data.topic_id).first()
    if not topic:
        raise NotFoundException("选题不存在")

    # 检查评阅结果：仅评阅通过(pass)的选题才可安排答辩
    review = db.query(Review).filter(
        Review.topic_id == data.topic_id,
        Review.status == "completed"
    ).order_by(Review.id.desc()).first()
    if not review:
        raise BusinessException(400, "该选题尚未完成论文评阅，无法安排答辩")
    if review.result != "pass":
        raise BusinessException(400, f"该选题评阅结果为「{review_result_text(review.result)}」，需评阅通过后才可安排答辩")

    # 检查是否已有答辩安排
    existing = get_defense_by_topic_id(db, data.topic_id)
    if existing:
        raise ConflictException("该选题已有答辩安排")

    # 校验答辩时间：结束时间必须晚于开始时间
    if data.defense_time_start and data.defense_time_end and data.defense_time_end <= data.defense_time_start:
        raise BusinessException(400, "答辩结束时间必须晚于开始时间")

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
    return DefenseResponse(**_enrich_defense(defense, db))


def apply_redefense(db: Session, student_id: int) -> DefenseResponse:
    """学生申请再次答辩（答辩结果为 reargue 时）"""
    # 查询学生的选题
    topic = db.query(Topic).filter(Topic.student_id == student_id, Topic.status == "approved").first()
    if not topic:
        raise BusinessException(400, "您还没有选题，无法申请再次答辩")

    # 查询该选题的答辩记录
    defense = get_defense_by_topic_id(db, topic.id)
    if not defense:
        raise BusinessException(400, "您还没有答辩安排，无需申请再次答辩")

    # 仅答辩结果为 reargue/fail 时可申请再次答辩
    if defense.result in ("pass", ""):
        result_txt = defense_result_text(defense.result) if defense.result else "无"
        raise BusinessException(400, f"当前答辩结果为「{result_txt}」，无需申请再次答辩")

    # 检查是否已有待安排的答辩（防止重复申请）
    if defense.status == "pending":
        raise BusinessException(400, "您已提交再次答辩申请，请等待教师安排答辩")

    # 重置答辩状态为待安排，清空成绩与结果
    defense.status = "pending"
    defense.total_score = 0.0
    defense.presentation_score = 0.0
    defense.qa_score = 0.0
    defense.thesis_quality_score = 0.0
    defense.grade = ""
    defense.result = ""
    defense.opinion = ""
    defense.suggestions = ""
    defense.defense_date = None
    defense.defense_time_start = None
    defense.defense_time_end = None
    defense.location = ""
    db.commit()
    db.refresh(defense)
    return DefenseResponse(**_enrich_defense(defense, db))


def update_defense(db: Session, defense_id: int, data: dict) -> DefenseResponse:
    """更新答辩安排（允许修改已完成的答辩）"""
    defense = get_defense_by_id(db, defense_id)
    if not defense:
        raise NotFoundException("答辩安排不存在")

    for key, value in data.items():
        if value is not None:
            setattr(defense, key, value)

    # 校验答辩时间：结束时间必须晚于开始时间
    if defense.defense_time_start and defense.defense_time_end and defense.defense_time_end <= defense.defense_time_start:
        raise BusinessException(400, "答辩结束时间必须晚于开始时间")

    db.commit()
    db.refresh(defense)
    return DefenseResponse(**_enrich_defense(defense, db))


def delete_defense(db: Session, defense_id: int, operator_role: str = None) -> None:
    """删除答辩安排（管理员可删除所有；教师不可删除已完成的答辩）"""
    defense = get_defense_by_id(db, defense_id)
    if not defense:
        raise NotFoundException("答辩安排不存在")

    # 教师不可删除已完成的答辩，管理员无限制
    if operator_role != "admin" and defense.status == "completed":
        raise BusinessException(400, "已完成的答辩不可删除")

    db.delete(defense)
    db.commit()


def score_defense(db: Session, defense_id: int, data: DefenseScore, operator_id: int = None, operator_role: str = None) -> DefenseResponse:
    """答辩评分（允许修改已完成的答辩评分）"""
    defense = get_defense_by_id(db, defense_id)
    if not defense:
        raise NotFoundException("答辩安排不存在")

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
    # 答辩记录文件
    if data.defense_file_id:
        defense.defense_file_id = data.defense_file_id
    if data.defense_file_path:
        defense.defense_file_path = data.defense_file_path
    if data.defense_file_name:
        defense.defense_file_name = data.defense_file_name

    db.commit()
    db.refresh(defense)
    return DefenseResponse(**_enrich_defense(defense, db))
