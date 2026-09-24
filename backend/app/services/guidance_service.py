"""过程指导记录 Service"""
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.user import User
from app.models.topic import Topic
from app.models.guidance import GuidanceRecord
from app.schemas.guidance import GuidanceCreate, GuidanceReply, GuidanceUpdate
from app.core.exceptions import NotFoundException, BusinessException


def _build_response(db: Session, record: GuidanceRecord) -> dict:
    topic = db.query(Topic).filter(Topic.id == record.topic_id).first()
    student = db.query(User).filter(User.id == record.student_id).first()
    teacher = db.query(User).filter(User.id == record.teacher_id).first()
    return {
        "id": record.id,
        "topic_id": record.topic_id,
        "topic_title": topic.title if topic else None,
        "student_id": record.student_id,
        "student_name": student.real_name if student else None,
        "teacher_id": record.teacher_id,
        "teacher_name": teacher.real_name if teacher else None,
        "initiator": record.initiator,
        "guidance_type": record.guidance_type,
        "guidance_time": record.guidance_time,
        "title": record.title or "",
        "content": record.content or "",
        "student_response": record.student_response or "",
        "student_reply_time": record.student_reply_time,
        "teacher_response": record.teacher_response or "",
        "teacher_reply_time": record.teacher_reply_time,
        "status": record.status,
        "create_time": record.create_time,
    }


def create_guidance(db: Session, data: GuidanceCreate, user_id: int, role: str) -> dict:
    """创建指导记录。教师发起或学生提问"""
    topic = db.query(Topic).filter(Topic.id == data.topic_id).first()
    if not topic:
        raise NotFoundException("选题不存在")

    if role == "teacher":
        if topic.teacher_id != user_id:
            raise BusinessException(403, "无权对非本人指导的学生创建指导记录")
        teacher_id = user_id
        student_id = topic.student_id
        initiator = "teacher"
    elif role == "student":
        if topic.student_id != user_id:
            raise BusinessException(403, "无权为他人选题创建指导记录")
        student_id = user_id
        teacher_id = topic.teacher_id
        initiator = "student"
    else:  # admin
        teacher_id = topic.teacher_id
        student_id = topic.student_id
        initiator = "teacher"

    if not teacher_id or not student_id:
        raise BusinessException(400, "该选题缺少师生信息，无法创建指导记录")

    record = GuidanceRecord(
        topic_id=topic.id,
        student_id=student_id,
        teacher_id=teacher_id,
        initiator=initiator,
        guidance_type=data.guidance_type,
        guidance_time=data.guidance_time or datetime.now(),
        title=data.title,
        content=data.content,
        status="pending",
        # 教师发起：等学生回复；学生发起：等教师回复
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return _build_response(db, record)


def reply_guidance(db: Session, record_id: int, data: GuidanceReply, student_id: int) -> dict:
    """学生回复指导"""
    record = db.query(GuidanceRecord).filter(GuidanceRecord.id == record_id).first()
    if not record:
        raise NotFoundException("指导记录不存在")
    if record.student_id != student_id:
        raise BusinessException(403, "无权回复他人的指导记录")
    if record.initiator != "teacher":
        raise BusinessException(400, "该记录非教师发起，无需学生回复")
    record.student_response = data.student_response
    record.student_reply_time = datetime.now()
    record.status = "replied"
    db.commit()
    db.refresh(record)
    return _build_response(db, record)


def teacher_reply_guidance(db: Session, record_id: int, data, teacher_id: int) -> dict:
    """教师回复学生提问"""
    record = db.query(GuidanceRecord).filter(GuidanceRecord.id == record_id).first()
    if not record:
        raise NotFoundException("指导记录不存在")
    if record.teacher_id != teacher_id:
        raise BusinessException(403, "无权回复非本人指导的记录")
    if record.initiator != "student":
        raise BusinessException(400, "该记录非学生提问，无需教师回复")
    record.teacher_response = data.teacher_response
    record.teacher_reply_time = datetime.now()
    record.status = "replied"
    db.commit()
    db.refresh(record)
    return _build_response(db, record)


def update_guidance(db: Session, record_id: int, data: GuidanceUpdate, user_id: int, role: str) -> dict:
    """更新指导记录（仅发起人或教师可改）"""
    record = db.query(GuidanceRecord).filter(GuidanceRecord.id == record_id).first()
    if not record:
        raise NotFoundException("指导记录不存在")
    if role != "admin" and record.teacher_id != user_id:
        raise BusinessException(403, "无权修改该指导记录")
    for field in ("title", "content", "guidance_type", "guidance_time"):
        val = getattr(data, field)
        if val is not None:
            setattr(record, field, val)
    db.commit()
    db.refresh(record)
    return _build_response(db, record)


def delete_guidance(db: Session, record_id: int, user_id: int, role: str) -> None:
    record = db.query(GuidanceRecord).filter(GuidanceRecord.id == record_id).first()
    if not record:
        raise NotFoundException("指导记录不存在")
    if role not in ("admin",) and record.teacher_id != user_id:
        raise BusinessException(403, "无权删除该指导记录")
    db.delete(record)
    db.commit()


def get_guidance_list(
    db: Session,
    user_id: int,
    role: str,
    topic_id: Optional[int] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
):
    """查询指导记录列表"""
    q = db.query(GuidanceRecord)
    if role == "student":
        q = q.filter(GuidanceRecord.student_id == user_id)
    elif role == "teacher":
        q = q.filter(GuidanceRecord.teacher_id == user_id)
    # admin 不限制
    if topic_id:
        q = q.filter(GuidanceRecord.topic_id == topic_id)
    if status:
        q = q.filter(GuidanceRecord.status == status)
    q = q.order_by(GuidanceRecord.guidance_time.desc(), GuidanceRecord.create_time.desc())
    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return [_build_response(db, r) for r in items], total


def get_guidance_detail(db: Session, record_id: int) -> dict:
    record = db.query(GuidanceRecord).filter(GuidanceRecord.id == record_id).first()
    if not record:
        raise NotFoundException("指导记录不存在")
    return _build_response(db, record)
