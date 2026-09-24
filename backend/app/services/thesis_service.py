"""
论文版本服务模块
"""
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime
from sqlalchemy import or_, desc
from sqlalchemy.orm import Session

from app.models.thesis import ThesisVersion, FormatCheck
from app.models.topic import Topic
from app.models.user import User
from app.schemas.thesis import (
    ThesisVersionCreate, ThesisVersionUpdate, ThesisVersionResponse,
    FormatCheckResult, VersionCompareResponse,
)
from app.core.exceptions import NotFoundException, BusinessException
from app.schemas.common import PaginationParams

# 检测项英文 key → 中文显示名映射
CHECK_ITEM_NAMES = {
    "title_format": "标题格式",
    "abstract_format": "摘要格式",
    "keywords_format": "关键词格式",
    "chapter_structure": "章节结构",
    "references_format": "参考文献格式",
    "citation_format": "引文标注格式",
    "figure_table_format": "图表格式",
    "font_format": "字体格式",
    "page_layout": "页面布局",
    "appendix_format": "附录格式",
}


def _check_items_to_list(check_items: dict) -> list:
    """将检测结果 dict 转为列表，并补充 name 字段（中文显示名）"""
    result = []
    for key, item in (check_items or {}).items():
        row = dict(item)
        row["name"] = CHECK_ITEM_NAMES.get(key, key)
        result.append(row)
    return result


def _enrich_version(version: ThesisVersion) -> dict:
    """补充论文版本关联信息"""
    data = {c.name: getattr(version, c.name) for c in version.__table__.columns}
    data["topic_title"] = version.topic.title if version.topic else ""
    data["student_name"] = version.student.real_name if version.student else ""
    return data


def get_version_by_id(db: Session, version_id: int) -> Optional[ThesisVersion]:
    """根据ID获取论文版本"""
    return db.query(ThesisVersion).filter(ThesisVersion.id == version_id).first()


def get_version_detail(db: Session, version_id: int) -> ThesisVersionResponse:
    """获取论文版本详情"""
    version = get_version_by_id(db, version_id)
    if not version:
        raise NotFoundException("论文版本不存在")
    return ThesisVersionResponse(**_enrich_version(version))


def get_version_list(
    db: Session,
    params: PaginationParams,
    topic_id: Optional[int] = None,
    student_id: Optional[int] = None,
    format_check_status: Optional[str] = None,
) -> Tuple[List[ThesisVersionResponse], int]:
    """获取论文版本列表"""
    query = db.query(ThesisVersion).join(User, ThesisVersion.student_id == User.id, isouter=True)

    # 关键词搜索
    if params.keyword:
        keyword = f"%{params.keyword}%"
        query = query.join(Topic, ThesisVersion.topic_id == Topic.id, isouter=True)
        query = query.filter(
            or_(
                Topic.title.like(keyword),
                ThesisVersion.version_name.like(keyword),
                ThesisVersion.change_log.like(keyword),
                User.real_name.like(keyword),
            )
        )

    # 选题过滤
    if topic_id:
        query = query.filter(ThesisVersion.topic_id == topic_id)

    # 学生过滤
    if student_id:
        query = query.filter(ThesisVersion.student_id == student_id)

    # 格式检测状态过滤
    if format_check_status:
        query = query.filter(ThesisVersion.format_check_status == format_check_status)

    # 总数
    total = query.count()

    # 排序
    sort_column = getattr(ThesisVersion, params.sort_by, ThesisVersion.version_num)
    if params.sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    # 分页
    offset = (params.page - 1) * params.page_size
    versions = query.offset(offset).limit(params.page_size).all()

    items = [ThesisVersionResponse(**_enrich_version(v)) for v in versions]
    return items, total


def get_latest_version(db: Session, topic_id: int) -> Optional[ThesisVersion]:
    """获取选题的最新版本"""
    return db.query(ThesisVersion).filter(
        ThesisVersion.topic_id == topic_id
    ).order_by(desc(ThesisVersion.version_num)).first()


def create_version(db: Session, data: ThesisVersionCreate, student_id: int) -> ThesisVersionResponse:
    """创建论文版本"""
    # 检查选题是否存在
    topic = db.query(Topic).filter(Topic.id == data.topic_id).first()
    if not topic:
        raise NotFoundException("选题不存在")
    if topic.student_id != student_id:
        raise BusinessException(403, "无权为他人选题上传论文版本")

    # 确定版本号：传入则使用指定版本号（一稿=1, 二稿=2, 终稿=3），否则自动递增
    if data.version_num is not None:
        target_version_num = data.version_num
        # 若该版本号已存在，直接更新文件信息（不删除重建，避免被 reviews 等外键引用时触发 IntegrityError）
        existing = db.query(ThesisVersion).filter(
            ThesisVersion.topic_id == data.topic_id,
            ThesisVersion.version_num == target_version_num
        ).first()
        if existing:
            existing.file_path = data.file_path
            existing.file_name = data.file_name
            existing.file_size = data.file_size
            existing.file_type = data.file_type
            existing.change_log = data.change_log
            existing.format_check_status = "pending"
            existing.format_score = 0.0
            db.commit()
            db.refresh(existing)
            return ThesisVersionResponse(**_enrich_version(existing))
    else:
        latest = get_latest_version(db, data.topic_id)
        target_version_num = latest.version_num + 1 if latest else 1

    version = ThesisVersion(
        topic_id=data.topic_id,
        student_id=student_id,
        version_num=target_version_num,
        version_name=data.version_name or f"V{target_version_num}",
        change_log=data.change_log,
        file_path=data.file_path,
        file_name=data.file_name,
        file_size=data.file_size,
        file_type=data.file_type,
        format_check_status="pending",
    )
    db.add(version)
    db.commit()
    db.refresh(version)
    return ThesisVersionResponse(**_enrich_version(version))


def update_version(db: Session, version_id: int, data: ThesisVersionUpdate, current_user: User) -> ThesisVersionResponse:
    """更新论文版本信息"""
    version = get_version_by_id(db, version_id)
    if not version:
        raise NotFoundException("论文版本不存在")

    # 权限校验
    if current_user.role == "student" and version.student_id != current_user.id:
        raise BusinessException(403, "无权修改他人的论文版本")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(version, key, value)

    db.commit()
    db.refresh(version)
    return ThesisVersionResponse(**_enrich_version(version))


def delete_version(db: Session, version_id: int, current_user: User) -> None:
    """删除论文版本"""
    version = get_version_by_id(db, version_id)
    if not version:
        raise NotFoundException("论文版本不存在")

    # 权限校验
    if current_user.role == "student" and version.student_id != current_user.id:
        raise BusinessException(403, "无权删除他人的论文版本")

    # 若该版本已被评阅引用，不允许删除（避免外键冲突）
    from app.models.review import Review
    referenced = db.query(Review).filter(Review.version_id == version_id).first()
    if referenced:
        raise BusinessException(400, "该论文版本已被评阅引用，无法删除")

    db.delete(version)
    db.commit()


def run_format_check(db: Session, version_id: int) -> FormatCheckResult:
    """执行格式检测（调用真实检测引擎）"""
    version = get_version_by_id(db, version_id)
    if not version:
        raise NotFoundException("论文版本不存在")

    if not version.file_path:
        raise BusinessException(400, "论文版本未关联文件，无法执行格式检测")

    # 调用真实格式检测引擎
    from app.services.format_checker import run_format_check as _run_check
    result = _run_check(version.file_path)

    check_items = result["check_items"]
    total_score = result["total_score"]
    max_score = result["max_score"]
    passed_count = result["passed_count"]
    failed_count = result["failed_count"]
    total_items = result["total_items"]
    overall_result = result["overall_result"]
    problems_summary = result["problems_summary"]
    suggestions = result["suggestions"]
    doc_stats = result["document_stats"]

    # 保存检测结果
    format_check = FormatCheck(
        version_id=version_id,
        topic_id=version.topic_id,
        check_items=check_items,
        total_score=total_score,
        max_score=max_score,
        passed_count=passed_count,
        failed_count=failed_count,
        total_items=total_items,
        overall_result=overall_result,
        problems_summary=problems_summary,
        suggestions=suggestions,
        check_time=datetime.utcnow(),
        checker="system",
    )
    db.add(format_check)

    # 更新版本状态
    version.format_check_status = "done"
    version.format_score = total_score

    # 更新版本统计信息（来自真实文档解析）
    version.word_count = doc_stats["word_count"]
    version.page_count = doc_stats["page_count"]
    version.chapter_count = doc_stats["chapter_count"]
    version.reference_count = doc_stats["reference_count"]

    db.commit()
    db.refresh(format_check)

    return FormatCheckResult(
        version_id=version_id,
        total_score=total_score,
        max_score=max_score,
        passed_count=passed_count,
        failed_count=failed_count,
        total_items=total_items,
        overall_result=overall_result,
        problems_summary=problems_summary,
        suggestions=suggestions,
        check_items=_check_items_to_list(check_items),
        check_time=format_check.check_time,
    )


def get_format_check_result(db: Session, version_id: int) -> Optional[FormatCheckResult]:
    """获取格式检测结果"""
    check = db.query(FormatCheck).filter(
        FormatCheck.version_id == version_id
    ).order_by(desc(FormatCheck.check_time)).first()

    if not check:
        return None

    check_items_list = []
    if isinstance(check.check_items, dict):
        check_items_list = _check_items_to_list(check.check_items)

    return FormatCheckResult(
        version_id=check.version_id,
        total_score=check.total_score,
        max_score=check.max_score,
        passed_count=check.passed_count,
        failed_count=check.failed_count,
        total_items=check.total_items,
        overall_result=check.overall_result,
        problems_summary=check.problems_summary,
        suggestions=check.suggestions,
        check_items=check_items_list,
        check_time=check.check_time,
    )


def compare_versions(db: Session, version_a_id: int, version_b_id: int) -> VersionCompareResponse:
    """版本对比"""
    version_a = get_version_by_id(db, version_a_id)
    version_b = get_version_by_id(db, version_b_id)

    if not version_a or not version_b:
        raise NotFoundException("论文版本不存在")

    if version_a.topic_id != version_b.topic_id:
        raise BusinessException(400, "只能对比同一选题的不同版本")

    # 计算差异
    differences: List[Dict[str, Any]] = []

    if version_a.word_count != version_b.word_count:
        differences.append({
            "field": "word_count",
            "field_name": "字数",
            "value_a": version_a.word_count,
            "value_b": version_b.word_count,
            "change": version_b.word_count - version_a.word_count,
        })

    if version_a.page_count != version_b.page_count:
        differences.append({
            "field": "page_count",
            "field_name": "页数",
            "value_a": version_a.page_count,
            "value_b": version_b.page_count,
            "change": version_b.page_count - version_a.page_count,
        })

    if version_a.chapter_count != version_b.chapter_count:
        differences.append({
            "field": "chapter_count",
            "field_name": "章节数",
            "value_a": version_a.chapter_count,
            "value_b": version_b.chapter_count,
            "change": version_b.chapter_count - version_a.chapter_count,
        })

    if version_a.format_score != version_b.format_score:
        differences.append({
            "field": "format_score",
            "field_name": "格式得分",
            "value_a": version_a.format_score,
            "value_b": version_b.format_score,
            "change": round(version_b.format_score - version_a.format_score, 2),
        })

    differences.append({
        "field": "version_num",
        "field_name": "版本号",
        "value_a": version_a.version_num,
        "value_b": version_b.version_num,
        "change": version_b.version_num - version_a.version_num,
    })

    differences.append({
        "field": "change_log",
        "field_name": "修改说明",
        "value_a": version_a.change_log,
        "value_b": version_b.change_log,
        "change": None,
    })

    return VersionCompareResponse(
        version_a=ThesisVersionResponse(**_enrich_version(version_a)),
        version_b=ThesisVersionResponse(**_enrich_version(version_b)),
        differences=differences,
    )
