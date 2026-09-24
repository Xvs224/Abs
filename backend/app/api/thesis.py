"""
论文版本 API 路由
"""
import os
import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.core.response import success_response, page_response
from app.core.security import get_current_user, require_admin_or_teacher, require_teacher_only, require_student, require_student_or_teacher
from app.core.stage_gate import raise_if_locked
from app.schemas.thesis import (
    ThesisVersionCreate, ThesisVersionUpdate, ThesisVersionResponse,
    FormatCheckResult, VersionCompareResponse,
)
from app.schemas.common import PaginationParams
from app.models.user import User
from app.models.topic import Topic
from app.services import thesis_service
from app.core.exceptions import NotFoundException, BusinessException

router = APIRouter(prefix="/api/thesis", tags=["论文版本"])


# ==================== 版本管理 ====================

@router.get("/versions", summary="论文版本列表")
def list_versions(
    params: PaginationParams = Depends(),
    topic_id: int = Query(None, description="选题ID过滤"),
    student_id: int = Query(None, description="学生ID过滤"),
    format_check_status: str = Query(None, description="格式检测状态过滤"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student_or_teacher),
):
    """获取论文版本列表，支持关键词搜索和分页"""
    # 数据隔离
    if current_user.role == "student":
        student_id = current_user.id

    items, total = thesis_service.get_version_list(
        db, params, topic_id, student_id, format_check_status
    )
    return page_response(items=items, total=total, page=params.page, page_size=params.page_size)


@router.post("/versions", summary="上传论文版本")
async def create_version(
    file: UploadFile = File(...),
    topic_id: int = Form(None, description="选题ID（教师上传时必填）"),
    student_id: int = Form(None, description="学生ID（教师上传时必填）"),
    version_name: str = Form("", description="版本名称"),
    change_log: str = Form("", description="修改说明"),
    version_num: Optional[int] = Form(None, description="版本号（1=一稿, 2=二稿, 3=终稿），不传则自动递增"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student_or_teacher),
):
    """上传新的论文版本（学生上传自己的，教师可代学生上传）"""
    raise_if_locked(db, "thesis_final", current_user.role)
    # 校验文件大小
    content = await file.read()
    file_size = len(content)
    if file_size == 0:
        raise BusinessException(400, "文件不能为空")
    if file_size > settings.MAX_UPLOAD_SIZE:
        raise BusinessException(400, f"文件大小超过限制（最大 {settings.MAX_UPLOAD_SIZE // 1024 // 1024}MB）")

    # 校验扩展名
    original_name = file.filename or "unnamed"
    _, ext = os.path.splitext(original_name)
    ext = ext.lower()
    if ext not in settings.allowed_extensions_list:
        raise BusinessException(400, f"不支持的文件类型: {ext}")

    # 确定学生ID
    if current_user.role == "student":
        target_student_id = current_user.id
    else:
        # 教师上传需要指定学生
        if not student_id:
            raise BusinessException(400, "教师上传需指定学生ID")
        target_student_id = student_id

    # 确定选题ID
    if current_user.role == "student":
        # 学生取自己的选题
        topic = db.query(Topic).filter(Topic.student_id == current_user.id).first()
        if not topic:
            raise BusinessException(400, "您还没有选题，无法上传论文版本")
        target_topic_id = topic.id
    else:
        if not topic_id:
            raise BusinessException(400, "教师上传需指定选题ID")
        topic = db.query(Topic).filter(Topic.id == topic_id).first()
        if not topic:
            raise NotFoundException("选题不存在")
        if topic.student_id != target_student_id:
            raise BusinessException(400, "选题与学生不匹配")
        target_topic_id = topic_id

    # 保存文件
    date_dir = datetime.now().strftime("%Y-%m")
    save_dir = os.path.join(settings.UPLOAD_DIR, "thesis", date_dir)
    os.makedirs(save_dir, exist_ok=True)
    stored_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(save_dir, stored_name)
    with open(file_path, "wb") as f:
        f.write(content)

    # 构造创建数据
    data = ThesisVersionCreate(
        topic_id=target_topic_id,
        file_path=file_path,
        file_name=original_name,
        file_size=file_size,
        file_type=file.content_type or "",
        version_name=version_name,
        change_log=change_log,
        version_num=version_num,
    )
    result = thesis_service.create_version(db, data, target_student_id)
    return success_response(data=result, message="论文版本上传成功")


@router.get("/versions/{version_id}", summary="论文版本详情")
def get_version(
    version_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student_or_teacher),
):
    """获取论文版本详情"""
    result = thesis_service.get_version_detail(db, version_id)
    return success_response(data=result)


@router.get("/versions/{version_id}/download", summary="下载论文版本文件")
def download_version(
    version_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student_or_teacher),
):
    """下载论文版本对应的文件"""
    version = thesis_service.get_version_by_id(db, version_id)
    if not version:
        raise NotFoundException("论文版本不存在")

    # 权限校验：学生只能下载自己的版本
    if current_user.role == "student" and version.student_id != current_user.id:
        from app.core.exceptions import BusinessException
        raise BusinessException(403, "无权下载他人的论文版本")

    if not version.file_path or not os.path.exists(version.file_path):
        raise NotFoundException("论文文件不存在或已被删除")

    return FileResponse(
        path=version.file_path,
        filename=version.file_name,
        media_type="application/octet-stream",
    )


@router.put("/versions/{version_id}", summary="更新论文版本")
def update_version(
    version_id: int,
    data: ThesisVersionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student_or_teacher),
):
    """更新论文版本信息"""
    result = thesis_service.update_version(db, version_id, data, current_user)
    return success_response(data=result, message="论文版本更新成功")


@router.delete("/versions/{version_id}", summary="删除论文版本")
def delete_version(
    version_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student_or_teacher),
):
    """删除论文版本"""
    thesis_service.delete_version(db, version_id, current_user)
    return success_response(message="论文版本删除成功")


@router.post("/versions/{version_id}/format-check", summary="执行格式检测")
def run_format_check(
    version_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student),
):
    """对论文版本执行格式检测"""
    result = thesis_service.run_format_check(db, version_id)
    return success_response(data=result, message="格式检测完成")


@router.get("/versions/{version_id}/format-check", summary="获取格式检测结果")
def get_format_check(
    version_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student_or_teacher),
):
    """获取论文版本的格式检测结果"""
    result = thesis_service.get_format_check_result(db, version_id)
    return success_response(data=result)


@router.get("/versions/compare", summary="版本对比")
def compare_versions(
    version_a_id: int = Query(..., description="版本A ID"),
    version_b_id: int = Query(..., description="版本B ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student_or_teacher),
):
    """对比两个论文版本的差异"""
    result = thesis_service.compare_versions(db, version_a_id, version_b_id)
    return success_response(data=result)
