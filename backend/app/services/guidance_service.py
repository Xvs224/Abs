"""
指导计划与记录服务模块
"""
from typing import List, Optional, Tuple
from datetime import datetime
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.guidance import GuidancePlan, GuidanceRecord
from app.models.topic import Topic
from app.models.user import User
from app.schemas.guidance import (
    GuidancePlanCreate, GuidancePlanUpdate, GuidancePlanResponse,
    GuidanceRecordCreate, GuidanceRecordUpdate, GuidanceRecordResponse,
)
from app.core.exceptions import NotFoundException, BusinessException
from app.schemas.common import PaginationParams


# ==================== 指导计划 ====================

def _enrich_plan(plan: GuidancePlan) -> dict:
    """补充指导计划关联信息"""
    data = {c.name: getattr(plan, c.name) for c in plan.__table__.columns}
    data["topic_title"] = plan.topic.title if plan.topic else ""
    data["student_name"] = plan.student.real_name if plan.student else ""
    data["teacher_name"] = plan.teacher.real_name if plan.teacher else ""
    data["record_count"] = len(plan.records) if plan.records else 0
    return data


def get_plan_by_id(db: Session, plan_id: int) -> Optional[GuidancePlan]:
    """根据ID获取指导计划"""
    return db.query(GuidancePlan).filter(GuidancePlan.id == plan_id).first()


def get_plan_detail(db: Session, plan_id: int) -> GuidancePlanResponse:
    """获取指导计划详情"""
    plan = get_plan_by_id(db, plan_id)
    if not plan:
        raise NotFoundException("指导计划不存在")
    return GuidancePlanResponse(**_enrich_plan(plan))


def get_plan_list(
    db: Session,
    params: PaginationParams,
    status: Optional[str] = None,
    student_id: Optional[int] = None,
    teacher_id: Optional[int] = None,
    topic_id: Optional[int] = None,
) -> Tuple[List[GuidancePlanResponse], int]:
    """获取指导计划列表"""
    query = db.query(GuidancePlan).join(User, GuidancePlan.student_id == User.id, isouter=True)

    # 关键词搜索
    if params.keyword:
        keyword = f"%{params.keyword}%"
        query = query.join(Topic, GuidancePlan.topic_id == Topic.id, isouter=True)
        query = query.filter(
            or_(
                Topic.title.like(keyword),
                GuidancePlan.plan_name.like(keyword),
                User.real_name.like(keyword),
            )
        )

    # 状态过滤
    if status:
        query = query.filter(GuidancePlan.status == status)

    # 学生过滤
    if student_id:
        query = query.filter(GuidancePlan.student_id == student_id)

    # 教师过滤
    if teacher_id:
        query = query.filter(GuidancePlan.teacher_id == teacher_id)

    # 选题过滤
    if topic_id:
        query = query.filter(GuidancePlan.topic_id == topic_id)

    # 总数
    total = query.count()

    # 排序
    sort_column = getattr(GuidancePlan, params.sort_by, GuidancePlan.id)
    if params.sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    # 分页
    offset = (params.page - 1) * params.page_size
    plans = query.offset(offset).limit(params.page_size).all()

    items = [GuidancePlanResponse(**_enrich_plan(p)) for p in plans]
    return items, total


def create_plan(db: Session, data: GuidancePlanCreate, teacher_id: int) -> GuidancePlanResponse:
    """创建指导计划"""
    # 检查选题是否存在
    topic = db.query(Topic).filter(Topic.id == data.topic_id).first()
    if not topic:
        raise NotFoundException("选题不存在")

    # 检查是否已有指导计划
    existing = db.query(GuidancePlan).filter(GuidancePlan.topic_id == data.topic_id).first()
    if existing:
        raise BusinessException(400, "该选题已有指导计划")

    plan = GuidancePlan(
        topic_id=data.topic_id,
        teacher_id=teacher_id,
        student_id=topic.student_id,
        plan_name=data.plan_name,
        total_times=data.total_times,
        frequency=data.frequency,
        plan_content=data.plan_content,
        start_date=data.start_date,
        end_date=data.end_date,
        status="active",
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return GuidancePlanResponse(**_enrich_plan(plan))


def update_plan(db: Session, plan_id: int, data: GuidancePlanUpdate, current_user: User) -> GuidancePlanResponse:
    """更新指导计划"""
    plan = get_plan_by_id(db, plan_id)
    if not plan:
        raise NotFoundException("指导计划不存在")

    # 权限校验：只有指导教师或管理员可以修改
    if current_user.role == "teacher" and plan.teacher_id != current_user.id:
        raise BusinessException(403, "无权修改他人的指导计划")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(plan, key, value)

    db.commit()
    db.refresh(plan)
    return GuidancePlanResponse(**_enrich_plan(plan))


def delete_plan(db: Session, plan_id: int, current_user: User) -> None:
    """删除指导计划"""
    plan = get_plan_by_id(db, plan_id)
    if not plan:
        raise NotFoundException("指导计划不存在")

    # 权限校验
    if current_user.role == "teacher" and plan.teacher_id != current_user.id:
        raise BusinessException(403, "无权删除他人的指导计划")

    db.delete(plan)
    db.commit()


# ==================== 指导记录 ====================

def _enrich_record(record: GuidanceRecord) -> dict:
    """补充指导记录关联信息"""
    data = {c.name: getattr(record, c.name) for c in record.__table__.columns}
    data["teacher_name"] = record.teacher.real_name if record.teacher else ""
    data["student_name"] = record.student.real_name if record.student else ""
    return data


def get_record_by_id(db: Session, record_id: int) -> Optional[GuidanceRecord]:
    """根据ID获取指导记录"""
    return db.query(GuidanceRecord).filter(GuidanceRecord.id == record_id).first()


def get_record_detail(db: Session, record_id: int) -> GuidanceRecordResponse:
    """获取指导记录详情"""
    record = get_record_by_id(db, record_id)
    if not record:
        raise NotFoundException("指导记录不存在")
    return GuidanceRecordResponse(**_enrich_record(record))


def get_record_list(
    db: Session,
    params: PaginationParams,
    plan_id: Optional[int] = None,
    topic_id: Optional[int] = None,
    student_id: Optional[int] = None,
    teacher_id: Optional[int] = None,
    record_type: Optional[str] = None,
) -> Tuple[List[GuidanceRecordResponse], int]:
    """获取指导记录列表"""
    query = db.query(GuidanceRecord).join(User, GuidanceRecord.teacher_id == User.id, isouter=True)

    # 关键词搜索
    if params.keyword:
        keyword = f"%{params.keyword}%"
        query = query.filter(
            or_(
                GuidanceRecord.content.like(keyword),
                GuidanceRecord.teacher_opinion.like(keyword),
                User.real_name.like(keyword),
            )
        )

    # 计划过滤
    if plan_id:
        query = query.filter(GuidanceRecord.plan_id == plan_id)

    # 选题过滤
    if topic_id:
        query = query.filter(GuidanceRecord.topic_id == topic_id)

    # 学生过滤
    if student_id:
        query = query.filter(GuidanceRecord.student_id == student_id)

    # 教师过滤
    if teacher_id:
        query = query.filter(GuidanceRecord.teacher_id == teacher_id)

    # 类型过滤
    if record_type:
        query = query.filter(GuidanceRecord.record_type == record_type)

    # 总数
    total = query.count()

    # 排序
    sort_column = getattr(GuidanceRecord, params.sort_by, GuidanceRecord.record_time)
    if params.sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    # 分页
    offset = (params.page - 1) * params.page_size
    records = query.offset(offset).limit(params.page_size).all()

    items = [GuidanceRecordResponse(**_enrich_record(r)) for r in records]
    return items, total


def create_record(db: Session, data: GuidanceRecordCreate, teacher_id: int) -> GuidanceRecordResponse:
    """创建指导记录"""
    # 检查计划是否存在
    plan = get_plan_by_id(db, data.plan_id)
    if not plan:
        raise NotFoundException("指导计划不存在")

    # 权限校验
    if plan.teacher_id != teacher_id:
        raise BusinessException(403, "无权为他人的指导计划添加记录")

    record = GuidanceRecord(
        plan_id=data.plan_id,
        topic_id=plan.topic_id,
        teacher_id=teacher_id,
        student_id=plan.student_id,
        record_type=data.record_type,
        method=data.method,
        location=data.location,
        duration=data.duration,
        content=data.content,
        teacher_opinion=data.teacher_opinion,
        student_task=data.student_task,
        next_guidance_date=data.next_guidance_date,
        record_time=data.record_time or datetime.utcnow(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return GuidanceRecordResponse(**_enrich_record(record))


def update_record(db: Session, record_id: int, data: GuidanceRecordUpdate, current_user: User) -> GuidanceRecordResponse:
    """更新指导记录"""
    record = get_record_by_id(db, record_id)
    if not record:
        raise NotFoundException("指导记录不存在")

    # 权限校验
    if current_user.role == "teacher" and record.teacher_id != current_user.id:
        raise BusinessException(403, "无权修改他人的指导记录")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(record, key, value)

    db.commit()
    db.refresh(record)
    return GuidanceRecordResponse(**_enrich_record(record))


def delete_record(db: Session, record_id: int, current_user: User) -> None:
    """删除指导记录"""
    record = get_record_by_id(db, record_id)
    if not record:
        raise NotFoundException("指导记录不存在")

    # 权限校验
    if current_user.role == "teacher" and record.teacher_id != current_user.id:
        raise BusinessException(403, "无权删除他人的指导记录")

    db.delete(record)
    db.commit()
