"""
中期检查服务模块
"""
from typing import List, Optional, Tuple
from datetime import datetime
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.midterm import MidtermCheck, Rectification
from app.models.topic import Topic
from app.models.user import User
from app.schemas.midterm import (
    MidtermCheckCreate, MidtermCheckUpdate, MidtermReview, MidtermCheckResponse,
    MidtermGuidance, MidtermPPTSubmit,
    RectificationCreate, RectificationSubmit, RectificationReview, RectificationResponse,
)
from app.core.exceptions import NotFoundException, BusinessException
from app.schemas.common import PaginationParams


# ==================== 中期检查 ====================

def _enrich_midterm(midterm: MidtermCheck) -> dict:
    """补充中期检查关联信息，处理数据库 NULL 值"""
    data = {}
    for c in midterm.__table__.columns:
        val = getattr(midterm, c.name)
        # 将 None 转为 Pydantic schema 期望的默认值
        if val is None:
            col_type = str(c.type).upper()
            if 'TEXT' in col_type or 'VARCHAR' in col_type or 'CHAR' in col_type:
                val = ""
            elif 'FLOAT' in col_type or 'INT' in col_type or 'DECIMAL' in col_type:
                val = 0
            # DATETIME/DATE 保留 None (Optional)
        data[c.name] = val
    data["topic_title"] = midterm.topic.title if midterm.topic else ""
    data["student_name"] = midterm.student.real_name if midterm.student else ""
    data["teacher_name"] = midterm.teacher.real_name if midterm.teacher else ""
    data["rectification_count"] = len(midterm.rectifications) if midterm.rectifications else 0
    return data


def get_midterm_by_id(db: Session, midterm_id: int) -> Optional[MidtermCheck]:
    """根据ID获取中期检查"""
    return db.query(MidtermCheck).filter(MidtermCheck.id == midterm_id).first()


def get_midterm_by_topic_id(db: Session, topic_id: int) -> Optional[MidtermCheck]:
    """根据选题ID获取中期检查"""
    return db.query(MidtermCheck).filter(MidtermCheck.topic_id == topic_id).first()


def get_midterm_detail(db: Session, midterm_id: int) -> MidtermCheckResponse:
    """获取中期检查详情"""
    midterm = get_midterm_by_id(db, midterm_id)
    if not midterm:
        raise NotFoundException("中期检查不存在")
    return MidtermCheckResponse(**_enrich_midterm(midterm))


def get_midterm_list(
    db: Session,
    params: PaginationParams,
    status: Optional[str] = None,
    student_id: Optional[int] = None,
    teacher_id: Optional[int] = None,
) -> Tuple[List[MidtermCheckResponse], int]:
    """获取中期检查列表"""
    query = db.query(MidtermCheck).join(User, MidtermCheck.student_id == User.id, isouter=True)

    # 关键词搜索
    if params.keyword:
        keyword = f"%{params.keyword}%"
        query = query.join(Topic, MidtermCheck.topic_id == Topic.id, isouter=True)
        query = query.filter(
            or_(
                Topic.title.like(keyword),
                MidtermCheck.progress_description.like(keyword),
                User.real_name.like(keyword),
            )
        )

    # 状态过滤
    if status:
        query = query.filter(MidtermCheck.status == status)

    # 学生过滤
    if student_id:
        query = query.filter(MidtermCheck.student_id == student_id)

    # 教师过滤
    if teacher_id:
        query = query.filter(MidtermCheck.teacher_id == teacher_id)

    # 总数
    total = query.count()

    # 排序
    sort_column = getattr(MidtermCheck, params.sort_by, MidtermCheck.id)
    if params.sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    # 分页
    offset = (params.page - 1) * params.page_size
    midterms = query.offset(offset).limit(params.page_size).all()

    items = [MidtermCheckResponse(**_enrich_midterm(m)) for m in midterms]
    return items, total


def create_or_update_midterm(db: Session, data: MidtermCheckCreate, student_id: int) -> MidtermCheckResponse:
    """创建或更新中期检查"""
    # 检查选题是否存在
    topic = db.query(Topic).filter(Topic.id == data.topic_id).first()
    if not topic:
        raise NotFoundException("选题不存在")
    if topic.student_id != student_id:
        raise BusinessException(403, "无权为他人选题创建中期检查")

    # 检查是否已有中期检查
    existing = get_midterm_by_topic_id(db, data.topic_id)
    if existing:
        # 更新已有中期检查
        if existing.status not in ["draft", "failed", "rectified"]:
            raise BusinessException(400, "当前状态不允许修改中期检查")

        update_data = data.model_dump(exclude_unset=True)
        update_data.pop("topic_id", None)
        for key, value in update_data.items():
            setattr(existing, key, value)

        db.commit()
        db.refresh(existing)
        return MidtermCheckResponse(**_enrich_midterm(existing))

    # 创建新的中期检查
    midterm = MidtermCheck(
        topic_id=data.topic_id,
        student_id=student_id,
        teacher_id=topic.teacher_id,
        progress_description=data.progress_description,
        completed_work=data.completed_work,
        remaining_work=data.remaining_work,
        progress_percentage=data.progress_percentage,
        existing_problems=data.existing_problems,
        next_plan=data.next_plan,
        file_id=data.file_id,
        file_path=data.file_path,
        file_name=data.file_name,
        stage="form",
        status="draft",
    )
    db.add(midterm)
    db.commit()
    db.refresh(midterm)
    return MidtermCheckResponse(**_enrich_midterm(midterm))


def update_midterm(db: Session, midterm_id: int, data: MidtermCheckUpdate, current_user: User) -> MidtermCheckResponse:
    """更新中期检查"""
    midterm = get_midterm_by_id(db, midterm_id)
    if not midterm:
        raise NotFoundException("中期检查不存在")

    # 权限校验
    if current_user.role == "student":
        if midterm.student_id != current_user.id:
            raise BusinessException(403, "无权修改他人的中期检查")
        if midterm.status not in ["draft", "failed", "rectified"]:
            raise BusinessException(400, "当前状态不允许修改中期检查")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(midterm, key, value)

    db.commit()
    db.refresh(midterm)
    return MidtermCheckResponse(**_enrich_midterm(midterm))


def submit_midterm(db: Session, midterm_id: int, student_id: int) -> MidtermCheckResponse:
    """学生提交中期检查表（阶段1）"""
    midterm = get_midterm_by_id(db, midterm_id)
    if not midterm:
        raise NotFoundException("中期检查不存在")

    if midterm.student_id != student_id:
        raise BusinessException(403, "无权提交他人的中期检查")

    if midterm.status not in ["draft", "failed", "rectified"]:
        raise BusinessException(400, "当前状态不允许提交中期检查表")

    # 校验必须上传中期检查表
    if not midterm.file_path or not midterm.file_name:
        raise BusinessException(400, "请先上传中期检查表文档后再提交")

    midterm.status = "form_submitted"
    midterm.stage = "form"
    midterm.submit_time = datetime.utcnow()

    db.commit()
    db.refresh(midterm)
    return MidtermCheckResponse(**_enrich_midterm(midterm))


def delete_midterm(db: Session, midterm_id: int, current_user: User) -> None:
    """删除中期检查（管理员可删除任意，学生仅能删除自己的草稿）"""
    midterm = get_midterm_by_id(db, midterm_id)
    if not midterm:
        raise NotFoundException("中期检查不存在")

    if current_user.role == "student":
        if midterm.student_id != current_user.id:
            raise BusinessException(403, "无权删除他人的中期检查")
        if midterm.status not in ["draft", "failed"]:
            raise BusinessException(400, "当前状态不允许删除中期检查")

    db.delete(midterm)
    db.commit()


def resubmit_midterm(db: Session, midterm_id: int, current_user: User) -> MidtermCheckResponse:
    """重交中期检查（管理员可强制重置，学生仅能重交被驳回的）"""
    midterm = get_midterm_by_id(db, midterm_id)
    if not midterm:
        raise NotFoundException("中期检查不存在")

    if current_user.role == "student":
        if midterm.student_id != current_user.id:
            raise BusinessException(403, "无权操作他人的中期检查")

    # 重置为草稿状态
    midterm.status = "draft"
    midterm.stage = "form"
    db.commit()
    db.refresh(midterm)
    return MidtermCheckResponse(**_enrich_midterm(midterm))


def teacher_guidance(db: Session, midterm_id: int, data: MidtermGuidance, current_user: User) -> MidtermCheckResponse:
    """教师对中期检查表给出指导意见（阶段1）"""
    midterm = get_midterm_by_id(db, midterm_id)
    if not midterm:
        raise NotFoundException("中期检查不存在")

    # 权限校验：教师只能指导自己的学生
    if current_user.role == "teacher" and midterm.teacher_id != current_user.id:
        raise BusinessException(403, "无权指导他人学生的中期检查")

    if midterm.status != "form_submitted":
        raise BusinessException(400, "只有待指导状态的中期检查表才能给出指导意见")

    midterm.teacher_guidance = data.teacher_guidance
    midterm.guidance_time = datetime.utcnow()
    midterm.status = "guided"
    midterm.stage = "form"

    db.commit()
    db.refresh(midterm)
    return MidtermCheckResponse(**_enrich_midterm(midterm))


def submit_ppt(db: Session, midterm_id: int, data: MidtermPPTSubmit, student_id: int) -> MidtermCheckResponse:
    """学生提交中期检查演示文稿PPT（阶段2）"""
    midterm = get_midterm_by_id(db, midterm_id)
    if not midterm:
        raise NotFoundException("中期检查不存在")

    if midterm.student_id != student_id:
        raise BusinessException(403, "无权提交他人的中期检查")

    if midterm.status != "guided":
        raise BusinessException(400, "只有教师已指导后的中期检查才能提交PPT")

    midterm.ppt_file_id = data.ppt_file_id
    midterm.ppt_file_path = data.ppt_file_path
    midterm.ppt_file_name = data.ppt_file_name
    midterm.status = "ppt_submitted"
    midterm.stage = "ppt"
    midterm.submit_time = datetime.utcnow()

    db.commit()
    db.refresh(midterm)
    return MidtermCheckResponse(**_enrich_midterm(midterm))


def review_midterm(db: Session, midterm_id: int, data: MidtermReview, current_user: User) -> MidtermCheckResponse:
    """评审中期检查（阶段2，PPT提交后最终评审）"""
    midterm = get_midterm_by_id(db, midterm_id)
    if not midterm:
        raise NotFoundException("中期检查不存在")

    # 权限校验：教师只能评审自己的学生
    if current_user.role == "teacher" and midterm.teacher_id != current_user.id:
        raise BusinessException(403, "无权评审他人学生的中期检查")

    if midterm.status not in ["ppt_submitted", "rectified"]:
        raise BusinessException(400, "只有PPT已提交或整改完成的中期检查才能评审")

    if data.teacher_score is not None:
        midterm.teacher_score = data.teacher_score
    if data.teacher_opinion is not None:
        midterm.teacher_opinion = data.teacher_opinion
    if data.check_group_score is not None:
        midterm.check_group_score = data.check_group_score
    if data.check_group_opinion is not None:
        midterm.check_group_opinion = data.check_group_opinion
    if data.final_score is not None:
        midterm.final_score = data.final_score

    midterm.status = data.status
    midterm.check_time = datetime.utcnow()

    db.commit()
    db.refresh(midterm)
    return MidtermCheckResponse(**_enrich_midterm(midterm))


# ==================== 整改管理 ====================

def _enrich_rectification(rect: Rectification) -> dict:
    """补充整改关联信息，处理数据库 NULL 值"""
    data = {}
    for c in rect.__table__.columns:
        val = getattr(rect, c.name)
        if val is None:
            col_type = str(c.type).upper()
            if 'TEXT' in col_type or 'VARCHAR' in col_type or 'CHAR' in col_type:
                val = ""
            elif 'FLOAT' in col_type or 'INT' in col_type or 'DECIMAL' in col_type:
                val = 0
            # DATETIME/DATE 保留 None (Optional)
        data[c.name] = val
    return data


def get_rectification_by_id(db: Session, rect_id: int) -> Optional[Rectification]:
    """根据ID获取整改"""
    return db.query(Rectification).filter(Rectification.id == rect_id).first()


def get_rectification_detail(db: Session, rect_id: int) -> RectificationResponse:
    """获取整改详情"""
    rect = get_rectification_by_id(db, rect_id)
    if not rect:
        raise NotFoundException("整改不存在")
    return RectificationResponse(**_enrich_rectification(rect))


def get_rectification_list(
    db: Session,
    params: PaginationParams,
    midterm_id: Optional[int] = None,
    topic_id: Optional[int] = None,
    status: Optional[str] = None,
) -> Tuple[List[RectificationResponse], int]:
    """获取整改列表"""
    query = db.query(Rectification)

    # 关键词搜索
    if params.keyword:
        keyword = f"%{params.keyword}%"
        query = query.filter(
            or_(
                Rectification.problem_description.like(keyword),
                Rectification.requirement.like(keyword),
                Rectification.rectification_content.like(keyword),
            )
        )

    # 中期检查过滤
    if midterm_id:
        query = query.filter(Rectification.midterm_id == midterm_id)

    # 选题过滤
    if topic_id:
        query = query.filter(Rectification.topic_id == topic_id)

    # 状态过滤
    if status:
        query = query.filter(Rectification.status == status)

    # 总数
    total = query.count()

    # 排序
    sort_column = getattr(Rectification, params.sort_by, Rectification.id)
    if params.sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    # 分页
    offset = (params.page - 1) * params.page_size
    rects = query.offset(offset).limit(params.page_size).all()

    items = [RectificationResponse(**_enrich_rectification(r)) for r in rects]
    return items, total


def create_rectification(db: Session, data: RectificationCreate, current_user: User) -> RectificationResponse:
    """创建整改"""
    # 检查中期检查是否存在
    midterm = get_midterm_by_id(db, data.midterm_id)
    if not midterm:
        raise NotFoundException("中期检查不存在")

    # 权限校验：教师或管理员可以创建整改
    if current_user.role == "teacher" and midterm.teacher_id != current_user.id:
        raise BusinessException(403, "无权为他人的中期检查创建整改")

    rect = Rectification(
        midterm_id=data.midterm_id,
        topic_id=data.topic_id,
        problem_description=data.problem_description,
        requirement=data.requirement,
        deadline=data.deadline,
        status="pending",
    )
    db.add(rect)

    # 更新中期检查状态为整改中
    midterm.status = "rectifying"

    db.commit()
    db.refresh(rect)
    return RectificationResponse(**_enrich_rectification(rect))


def update_rectification(db: Session, rect_id: int, data: dict, current_user: User) -> RectificationResponse:
    """更新整改"""
    rect = get_rectification_by_id(db, rect_id)
    if not rect:
        raise NotFoundException("整改不存在")

    # 权限校验
    midterm = get_midterm_by_id(db, rect.midterm_id)
    if current_user.role == "teacher" and midterm and midterm.teacher_id != current_user.id:
        raise BusinessException(403, "无权修改他人的整改")

    for key, value in data.items():
        if value is not None:
            setattr(rect, key, value)

    db.commit()
    db.refresh(rect)
    return RectificationResponse(**_enrich_rectification(rect))


def delete_rectification(db: Session, rect_id: int, current_user: User) -> None:
    """删除整改"""
    rect = get_rectification_by_id(db, rect_id)
    if not rect:
        raise NotFoundException("整改不存在")

    # 权限校验
    midterm = get_midterm_by_id(db, rect.midterm_id)
    if current_user.role == "teacher" and midterm and midterm.teacher_id != current_user.id:
        raise BusinessException(403, "无权删除他人的整改")

    if rect.status not in ["pending"]:
        raise BusinessException(400, "当前状态不允许删除整改")

    db.delete(rect)
    db.commit()


def submit_rectification(db: Session, rect_id: int, data: RectificationSubmit, student_id: int) -> RectificationResponse:
    """提交整改材料"""
    rect = get_rectification_by_id(db, rect_id)
    if not rect:
        raise NotFoundException("整改不存在")

    midterm = get_midterm_by_id(db, rect.midterm_id)
    if not midterm or midterm.student_id != student_id:
        raise BusinessException(403, "无权提交他人的整改")

    if rect.status != "pending":
        raise BusinessException(400, "当前状态不允许提交整改")

    rect.rectification_content = data.rectification_content
    rect.rectification_file_path = data.rectification_file_path
    rect.rectification_file_name = data.rectification_file_name
    rect.submit_time = datetime.utcnow()
    rect.status = "submitted"

    db.commit()
    db.refresh(rect)
    return RectificationResponse(**_enrich_rectification(rect))


def review_rectification(db: Session, rect_id: int, data: RectificationReview, current_user: User) -> RectificationResponse:
    """复检整改"""
    rect = get_rectification_by_id(db, rect_id)
    if not rect:
        raise NotFoundException("整改不存在")

    # 权限校验：教师只能复检自己的学生
    midterm = get_midterm_by_id(db, rect.midterm_id)
    if current_user.role == "teacher" and midterm and midterm.teacher_id != current_user.id:
        raise BusinessException(403, "无权复检他人学生的整改")

    if rect.status != "submitted":
        raise BusinessException(400, "当前状态不允许复检")

    rect.reviewer_id = current_user.id
    rect.review_opinion = data.review_opinion
    rect.review_result = data.review_result
    rect.review_time = datetime.utcnow()
    rect.status = data.review_result

    # 如果复检通过，更新中期检查状态
    midterm = get_midterm_by_id(db, rect.midterm_id)
    if midterm:
        if data.review_result == "passed":
            midterm.status = "rectified"
        elif data.review_result == "failed":
            midterm.status = "rectifying"

    db.commit()
    db.refresh(rect)
    return RectificationResponse(**_enrich_rectification(rect))
