"""
选题服务模块
"""
from typing import List, Optional, Tuple
from datetime import datetime
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session

from app.models.topic import Topic
from app.models.user import User
from app.schemas.topic import TopicCreate, TopicUpdate, TopicReview, TopicResponse, TopicDuplicateCheck
from app.core.exceptions import NotFoundException, BusinessException, ConflictException
from app.schemas.common import PaginationParams


def _enrich_topic(topic: Topic) -> dict:
    """补充选题关联信息"""
    data = {c.name: getattr(topic, c.name) for c in topic.__table__.columns}
    data["student_name"] = topic.student.real_name if topic.student else ""
    data["student_no"] = topic.student.student_no if topic.student and topic.student.role == "student" else ""
    data["teacher_name"] = topic.teacher.real_name if topic.teacher else ""
    return data


def get_topic_by_id(db: Session, topic_id: int) -> Optional[Topic]:
    """根据ID获取选题"""
    return db.query(Topic).filter(Topic.id == topic_id).first()


def get_topic_detail(db: Session, topic_id: int) -> TopicResponse:
    """获取选题详情（含关联信息）"""
    topic = get_topic_by_id(db, topic_id)
    if not topic:
        raise NotFoundException("选题不存在")
    return TopicResponse(**_enrich_topic(topic))


def get_topic_list(
    db: Session,
    params: PaginationParams,
    status: Optional[str] = None,
    student_id: Optional[int] = None,
    teacher_id: Optional[int] = None,
) -> Tuple[List[TopicResponse], int]:
    """获取选题列表"""
    query = db.query(Topic).join(User, Topic.student_id == User.id, isouter=True)

    # 关键词搜索
    if params.keyword:
        keyword = f"%{params.keyword}%"
        query = query.filter(
            or_(
                Topic.title.like(keyword),
                Topic.direction.like(keyword),
                Topic.keywords.like(keyword),
                User.real_name.like(keyword),
            )
        )

    # 状态过滤
    if status:
        query = query.filter(Topic.status == status)

    # 学生过滤
    if student_id:
        query = query.filter(Topic.student_id == student_id)

    # 教师过滤
    if teacher_id:
        query = query.filter(Topic.teacher_id == teacher_id)

    # 总数
    total = query.count()

    # 排序
    sort_column = getattr(Topic, params.sort_by, Topic.id)
    if params.sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    # 分页
    offset = (params.page - 1) * params.page_size
    topics = query.offset(offset).limit(params.page_size).all()

    items = [TopicResponse(**_enrich_topic(t)) for t in topics]
    return items, total


def create_topic(db: Session, data: TopicCreate, student_id: int) -> TopicResponse:
    """创建选题"""
    # 检查学生是否已有待审核或已通过的选题
    existing = db.query(Topic).filter(
        and_(
            Topic.student_id == student_id,
            Topic.status.in_(["pending", "approved"]),
        )
    ).first()
    if existing:
        raise ConflictException("您已有一个待审核或已通过的选题，无法重复创建")

    topic = Topic(
        student_id=student_id,
        teacher_id=data.teacher_id,
        title=data.title,
        direction=data.direction,
        background=data.background,
        significance=data.significance,
        keywords=data.keywords,
        source=data.source,
        difficulty=data.difficulty,
        workload=data.workload,
        status="pending",
        submit_time=datetime.utcnow(),
    )
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return TopicResponse(**_enrich_topic(topic))


def update_topic(db: Session, topic_id: int, data: TopicUpdate, current_user: User) -> TopicResponse:
    """更新选题"""
    topic = get_topic_by_id(db, topic_id)
    if not topic:
        raise NotFoundException("选题不存在")

    # 权限校验：学生只能修改自己的选题，且只能在待审核状态
    if current_user.role == "student":
        if topic.student_id != current_user.id:
            raise BusinessException(403, "无权修改他人的选题")
        if topic.status not in ["pending", "rejected"]:
            raise BusinessException(400, "当前状态不允许修改选题")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(topic, key, value)

    db.commit()
    db.refresh(topic)
    return TopicResponse(**_enrich_topic(topic))


def delete_topic(db: Session, topic_id: int, current_user: User) -> None:
    """删除选题"""
    topic = get_topic_by_id(db, topic_id)
    if not topic:
        raise NotFoundException("选题不存在")

    # 权限校验
    if current_user.role == "student":
        if topic.student_id != current_user.id:
            raise BusinessException(403, "无权删除他人的选题")
        if topic.status not in ["pending", "rejected"]:
            raise BusinessException(400, "当前状态不允许删除选题")

    db.delete(topic)
    db.commit()


def review_topic(db: Session, topic_id: int, data: TopicReview, reviewer_id: int) -> TopicResponse:
    """审核选题"""
    topic = get_topic_by_id(db, topic_id)
    if not topic:
        raise NotFoundException("选题不存在")

    if topic.status != "pending":
        raise BusinessException(400, "只有待审核状态的选题才能进行审核")

    topic.status = data.status
    topic.reject_reason = data.reject_reason if data.status == "rejected" else ""
    topic.reviewer_id = reviewer_id
    topic.review_time = datetime.utcnow()

    db.commit()
    db.refresh(topic)
    return TopicResponse(**_enrich_topic(topic))


def check_duplicate(db: Session, title: str, topic_id: Optional[int] = None) -> TopicDuplicateCheck:
    """选题重复检测"""
    # 简单相似度检测：基于标题关键词匹配
    query = db.query(Topic).filter(Topic.status.in_(["pending", "approved"]))

    if topic_id:
        query = query.filter(Topic.id != topic_id)

    # 使用关键词匹配
    keywords = [kw.strip() for kw in title.split() if len(kw.strip()) > 1]
    similar_topics = []

    if keywords:
        for kw in keywords[:5]:  # 最多取前5个关键词
            keyword = f"%{kw}%"
            matches = query.filter(Topic.title.like(keyword)).all()
            for t in matches:
                if not any(s["id"] == t.id for s in similar_topics):
                    # 计算简单相似度（相同字符比例）
                    same_chars = len(set(title) & set(t.title))
                    max_len = max(len(title), len(t.title))
                    similarity = same_chars / max_len if max_len > 0 else 0
                    if similarity >= 0.3:
                        similar_topics.append({
                            "id": t.id,
                            "title": t.title,
                            "student_name": t.student.real_name if t.student else "",
                            "similarity": round(similarity, 2),
                        })

    # 按相似度排序
    similar_topics.sort(key=lambda x: x["similarity"], reverse=True)

    threshold = 0.7
    duplicate_count = sum(1 for s in similar_topics if s["similarity"] >= threshold)
    is_duplicate = duplicate_count > 0

    return TopicDuplicateCheck(
        is_duplicate=is_duplicate,
        duplicate_count=duplicate_count,
        similar_topics=similar_topics[:10],
        similarity_threshold=threshold,
    )
