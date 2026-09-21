"""
开题报告服务模块
"""
from typing import List, Optional, Tuple
from datetime import datetime
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.proposal import Proposal
from app.models.topic import Topic
from app.models.user import User
from app.schemas.proposal import ProposalCreate, ProposalUpdate, ProposalReview, ProposalResponse
from app.core.exceptions import NotFoundException, BusinessException, ConflictException
from app.schemas.common import PaginationParams


def _enrich_proposal(proposal: Proposal) -> dict:
    """补充开题报告关联信息"""
    data = {c.name: getattr(proposal, c.name) for c in proposal.__table__.columns}
    data["topic_title"] = proposal.topic.title if proposal.topic else ""
    data["student_name"] = proposal.student.real_name if proposal.student else ""
    data["teacher_name"] = proposal.teacher.real_name if proposal.teacher else ""
    return data


def get_proposal_by_id(db: Session, proposal_id: int) -> Optional[Proposal]:
    """根据ID获取开题报告"""
    return db.query(Proposal).filter(Proposal.id == proposal_id).first()


def get_proposal_by_topic_id(db: Session, topic_id: int) -> Optional[Proposal]:
    """根据选题ID获取开题报告"""
    return db.query(Proposal).filter(Proposal.topic_id == topic_id).first()


def get_proposal_detail(db: Session, proposal_id: int) -> ProposalResponse:
    """获取开题报告详情"""
    proposal = get_proposal_by_id(db, proposal_id)
    if not proposal:
        raise NotFoundException("开题报告不存在")
    return ProposalResponse(**_enrich_proposal(proposal))


def get_proposal_list(
    db: Session,
    params: PaginationParams,
    status: Optional[str] = None,
    student_id: Optional[int] = None,
    teacher_id: Optional[int] = None,
) -> Tuple[List[ProposalResponse], int]:
    """获取开题报告列表"""
    query = db.query(Proposal).join(User, Proposal.student_id == User.id, isouter=True)

    # 关键词搜索
    if params.keyword:
        keyword = f"%{params.keyword}%"
        query = query.join(Topic, Proposal.topic_id == Topic.id, isouter=True)
        query = query.filter(
            or_(
                Topic.title.like(keyword),
                Proposal.research_content.like(keyword),
                User.real_name.like(keyword),
            )
        )

    # 状态过滤
    if status:
        query = query.filter(Proposal.status == status)

    # 学生过滤
    if student_id:
        query = query.filter(Proposal.student_id == student_id)

    # 教师过滤
    if teacher_id:
        query = query.filter(Proposal.teacher_id == teacher_id)

    # 总数
    total = query.count()

    # 排序
    sort_column = getattr(Proposal, params.sort_by, Proposal.id)
    if params.sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    # 分页
    offset = (params.page - 1) * params.page_size
    proposals = query.offset(offset).limit(params.page_size).all()

    items = [ProposalResponse(**_enrich_proposal(p)) for p in proposals]
    return items, total


def create_or_update_proposal(db: Session, data: ProposalCreate, student_id: int) -> ProposalResponse:
    """创建或更新开题报告"""
    # 检查选题是否存在且已通过
    topic = db.query(Topic).filter(Topic.id == data.topic_id).first()
    if not topic:
        raise NotFoundException("选题不存在")
    if topic.status != "approved":
        raise BusinessException(400, "选题未通过审核，无法创建开题报告")
    if topic.student_id != student_id:
        raise BusinessException(403, "无权为他人选题创建开题报告")

    # 检查是否已有开题报告
    existing = get_proposal_by_topic_id(db, data.topic_id)
    if existing:
        # 更新已有开题报告（草稿状态）
        if existing.status not in ["draft", "rejected"]:
            raise BusinessException(400, "当前状态不允许修改开题报告")

        update_data = data.model_dump(exclude_unset=True)
        update_data.pop("topic_id", None)
        for key, value in update_data.items():
            setattr(existing, key, value)

        db.commit()
        db.refresh(existing)
        return ProposalResponse(**_enrich_proposal(existing))

    # 创建新的开题报告
    proposal = Proposal(
        topic_id=data.topic_id,
        student_id=student_id,
        teacher_id=topic.teacher_id,
        research_content=data.research_content,
        research_method=data.research_method,
        technical_route=data.technical_route,
        expected_results=data.expected_results,
        schedule_plan=data.schedule_plan,
        references_count=data.references_count,
        references_list=data.references_list,
        word_count=data.word_count,
        status="draft",
    )
    db.add(proposal)
    db.commit()
    db.refresh(proposal)
    return ProposalResponse(**_enrich_proposal(proposal))


def update_proposal(db: Session, proposal_id: int, data: ProposalUpdate, current_user: User) -> ProposalResponse:
    """更新开题报告"""
    proposal = get_proposal_by_id(db, proposal_id)
    if not proposal:
        raise NotFoundException("开题报告不存在")

    # 权限校验
    if current_user.role == "student":
        if proposal.student_id != current_user.id:
            raise BusinessException(403, "无权修改他人的开题报告")
        if proposal.status not in ["draft", "rejected"]:
            raise BusinessException(400, "当前状态不允许修改开题报告")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(proposal, key, value)

    db.commit()
    db.refresh(proposal)
    return ProposalResponse(**_enrich_proposal(proposal))


def submit_proposal(db: Session, proposal_id: int, student_id: int) -> ProposalResponse:
    """提交开题报告"""
    proposal = get_proposal_by_id(db, proposal_id)
    if not proposal:
        raise NotFoundException("开题报告不存在")

    if proposal.student_id != student_id:
        raise BusinessException(403, "无权提交他人的开题报告")

    if proposal.status not in ["draft", "rejected"]:
        raise BusinessException(400, "当前状态不允许提交开题报告")

    proposal.status = "submitted"
    proposal.submit_time = datetime.utcnow()

    db.commit()
    db.refresh(proposal)
    return ProposalResponse(**_enrich_proposal(proposal))


def review_proposal(db: Session, proposal_id: int, data: ProposalReview, reviewer_id: int) -> ProposalResponse:
    """审核开题报告"""
    proposal = get_proposal_by_id(db, proposal_id)
    if not proposal:
        raise NotFoundException("开题报告不存在")

    if proposal.status != "submitted":
        raise BusinessException(400, "只有待审核状态的开题报告才能进行审核")

    proposal.status = data.status
    proposal.review_opinion = data.review_opinion
    proposal.reviewer_id = reviewer_id
    proposal.review_time = datetime.utcnow()

    db.commit()
    db.refresh(proposal)
    return ProposalResponse(**_enrich_proposal(proposal))
