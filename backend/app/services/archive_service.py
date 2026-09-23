"""
成果归档服务模块
"""
from typing import List, Optional, Tuple
from datetime import datetime
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.archive import Archive
from app.models.topic import Topic
from app.models.user import User
from app.models.review import Defense
from app.schemas.archive import ArchiveCreate, ArchiveUpdate, ArchiveReview, ArchiveResponse
from app.core.exceptions import NotFoundException, BusinessException, ConflictException
from app.schemas.common import PaginationParams


def _enrich_archive(archive: Archive, db: Session = None) -> dict:
    """补充归档关联信息（含答辩成绩/等级）"""
    data = {c.name: getattr(archive, c.name) for c in archive.__table__.columns}
    data["topic_title"] = archive.topic.title if archive.topic else ""
    data["student_name"] = archive.student.real_name if archive.student else ""
    data["teacher_name"] = archive.teacher.real_name if archive.teacher else ""

    # 从答辩记录中填充最终成绩与等级（若归档表未显式存储）
    if db is not None and archive.topic_id:
        defense = db.query(Defense).filter(Defense.topic_id == archive.topic_id).first()
        if defense:
            if not data.get("final_score"):
                data["final_score"] = defense.total_score or 0
            if not data.get("final_grade"):
                data["final_grade"] = defense.grade or ""
            data["defense_result"] = defense.result or ""

    return data


def get_archive_by_id(db: Session, archive_id: int) -> Optional[Archive]:
    """根据ID获取归档"""
    return db.query(Archive).filter(Archive.id == archive_id).first()


def get_archive_by_topic_id(db: Session, topic_id: int) -> Optional[Archive]:
    """根据选题ID获取归档"""
    return db.query(Archive).filter(Archive.topic_id == topic_id).first()


def get_archive_detail(db: Session, archive_id: int) -> ArchiveResponse:
    """获取归档详情"""
    archive = get_archive_by_id(db, archive_id)
    if not archive:
        raise NotFoundException("归档不存在")
    return ArchiveResponse(**_enrich_archive(archive, db))


def get_archive_list(
    db: Session,
    params: PaginationParams,
    status: Optional[str] = None,
    student_id: Optional[int] = None,
    teacher_id: Optional[int] = None,
    final_grade: Optional[str] = None,
) -> Tuple[List[ArchiveResponse], int]:
    """获取归档列表"""
    query = db.query(Archive).join(User, Archive.student_id == User.id, isouter=True)

    # 关键词搜索
    if params.keyword:
        keyword = f"%{params.keyword}%"
        query = query.join(Topic, Archive.topic_id == Topic.id, isouter=True)
        query = query.filter(
            or_(
                Topic.title.like(keyword),
                Archive.archive_no.like(keyword),
                Archive.archive_location.like(keyword),
                User.real_name.like(keyword),
            )
        )

    # 状态过滤
    if status:
        query = query.filter(Archive.status == status)

    # 学生过滤
    if student_id:
        query = query.filter(Archive.student_id == student_id)

    # 教师过滤
    if teacher_id:
        query = query.filter(Archive.teacher_id == teacher_id)

    # 等级过滤
    if final_grade:
        query = query.filter(Archive.final_grade == final_grade)

    # 总数
    total = query.count()

    # 排序
    sort_column = getattr(Archive, params.sort_by, Archive.id)
    if params.sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    # 分页
    offset = (params.page - 1) * params.page_size
    archives = query.offset(offset).limit(params.page_size).all()

    items = [ArchiveResponse(**_enrich_archive(a, db)) for a in archives]
    return items, total


def create_archive(db: Session, data: ArchiveCreate, student_id: int) -> ArchiveResponse:
    """创建归档申请"""
    # 检查选题是否存在
    topic = db.query(Topic).filter(Topic.id == data.topic_id).first()
    if not topic:
        raise NotFoundException("选题不存在")
    if topic.student_id != student_id:
        raise BusinessException(403, "无权为他人选题创建归档")

    # 检查是否已有归档
    existing = get_archive_by_topic_id(db, data.topic_id)
    if existing:
        raise ConflictException("该选题已有归档记录")

    archive = Archive(
        topic_id=data.topic_id,
        student_id=student_id,
        teacher_id=topic.teacher_id,
        final_version_id=data.final_version_id,
        status="pending",
    )
    db.add(archive)
    db.commit()
    db.refresh(archive)
    return ArchiveResponse(**_enrich_archive(archive, db))


def update_archive(db: Session, archive_id: int, data: ArchiveUpdate, current_user: User) -> ArchiveResponse:
    """更新归档信息"""
    archive = get_archive_by_id(db, archive_id)
    if not archive:
        raise NotFoundException("归档不存在")

    # 权限校验
    if current_user.role == "student":
        if archive.student_id != current_user.id:
            raise BusinessException(403, "无权修改他人的归档")
        if archive.status not in ["pending", "returned"]:
            raise BusinessException(400, "当前状态不允许修改归档")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(archive, key, value)

    db.commit()
    db.refresh(archive)
    return ArchiveResponse(**_enrich_archive(archive, db))


def review_archive(db: Session, archive_id: int, data: ArchiveReview, archivist_id: int) -> ArchiveResponse:
    """审核归档"""
    archive = get_archive_by_id(db, archive_id)
    if not archive:
        raise NotFoundException("归档不存在")

    if archive.status not in ["pending", "returned"]:
        raise BusinessException(400, "当前状态不允许审核归档")

    archive.status = data.status
    if data.status == "returned":
        archive.return_reason = data.return_reason
    else:
        archive.return_reason = ""
        archive.archive_time = datetime.utcnow()
        archive.archivist_id = archivist_id

        # 如果没有档案编号，自动生成
        if not archive.archive_no:
            archive.archive_no = f"ARC{datetime.utcnow().strftime('%Y%m%d')}{archive.id:06d}"

    db.commit()
    db.refresh(archive)
    return ArchiveResponse(**_enrich_archive(archive, db))


def delete_archive(db: Session, archive_id: int, current_user: User) -> None:
    """删除归档"""
    archive = get_archive_by_id(db, archive_id)
    if not archive:
        raise NotFoundException("归档不存在")

    # 权限校验
    if current_user.role == "student":
        if archive.student_id != current_user.id:
            raise BusinessException(403, "无权删除他人的归档")
        if archive.status not in ["pending", "returned"]:
            raise BusinessException(400, "当前状态不允许删除归档")

    db.delete(archive)
    db.commit()


def resubmit_archive(db: Session, archive_id: int, current_user: User) -> ArchiveResponse:
    """重交归档（管理员可强制重置为待审核，学生仅能重交被退回的）"""
    archive = get_archive_by_id(db, archive_id)
    if not archive:
        raise NotFoundException("归档不存在")

    if current_user.role == "student":
        if archive.student_id != current_user.id:
            raise BusinessException(403, "无权操作他人的归档")
        if archive.status != "returned":
            raise BusinessException(400, "只有被退回的归档才能重交")

    # 重置为待审核状态
    archive.status = "pending"
    archive.return_reason = ""
    archive.archive_time = None
    db.commit()
    db.refresh(archive)
    return ArchiveResponse(**_enrich_archive(archive, db))
