"""
文件管理 API 路由 — 统一文件上传/下载
"""
import os
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, UploadFile, File, Query, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.core.response import success_response, ResponseModel
from app.core.security import get_current_user, require_student_or_teacher
from app.core.exceptions import BusinessException, NotFoundException
from app.models.user import User
from app.models.file import UploadedFile

router = APIRouter(prefix="/api/files", tags=["文件管理"])


@router.post("/upload", summary="上传文件")
async def upload_file(
    file: UploadFile = File(...),
    module: str = Query(default="", description="业务模块: thesis/proposal/midterm/archive等"),
    target_id: int = Query(default=None, description="关联目标ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    上传文件，返回文件元数据。

    - 支持 PDF/DOC/DOCX/XLS/XLSX/PPT/PPTX/ZIP/RAR/TXT
    - 单文件最大 50MB（由 MAX_UPLOAD_SIZE 配置）
    """
    # 校验文件大小
    content = await file.read()
    file_size = len(content)
    if file_size > settings.MAX_UPLOAD_SIZE:
        raise BusinessException(400, f"文件大小超过限制（最大 {settings.MAX_UPLOAD_SIZE // 1024 // 1024}MB）")

    # 校验文件扩展名
    original_name = file.filename or "unnamed"
    _, ext = os.path.splitext(original_name)
    ext = ext.lower()
    if ext not in settings.allowed_extensions_list:
        raise BusinessException(400, f"不支持的文件类型: {ext}，允许的类型: {', '.join(settings.allowed_extensions_list)}")

    # 生成存储路径：uploads/{module}/{yyyy-mm}/{uuid}{ext}
    date_dir = datetime.now().strftime("%Y-%m")
    module_dir = module if module else "general"
    save_dir = os.path.join(settings.UPLOAD_DIR, module_dir, date_dir)
    os.makedirs(save_dir, exist_ok=True)

    stored_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(save_dir, stored_name)

    # 写入文件
    with open(file_path, "wb") as f:
        f.write(content)

    # 保存元数据
    file_record = UploadedFile(
        original_name=original_name,
        stored_name=stored_name,
        file_path=file_path,
        file_size=file_size,
        file_type=file.content_type or "",
        file_extension=ext,
        uploader_id=current_user.id,
        module=module,
        target_id=target_id,
    )
    db.add(file_record)
    db.commit()
    db.refresh(file_record)

    return success_response(
        data={
            "id": file_record.id,
            "original_name": file_record.original_name,
            "file_path": file_record.file_path,
            "file_size": file_record.file_size,
            "file_type": file_record.file_type,
            "file_extension": file_record.file_extension,
            "module": file_record.module,
            "target_id": file_record.target_id,
            "create_time": file_record.create_time.isoformat() if file_record.create_time else None,
        },
        message="文件上传成功",
    )


@router.get("/{file_id}/download", summary="下载文件")
def download_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """根据文件ID下载文件"""
    file_record = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file_record:
        raise NotFoundException("文件不存在")

    if not os.path.exists(file_record.file_path):
        raise NotFoundException("文件在服务器上不存在")

    # 增加下载计数
    file_record.download_count = (file_record.download_count or 0) + 1
    db.commit()

    return FileResponse(
        path=file_record.file_path,
        filename=file_record.original_name,
        media_type=file_record.file_type or "application/octet-stream",
    )


@router.get("/download", summary="按路径下载文件")
def download_by_path(
    path: str = Query(..., description="文件存储路径"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """根据文件存储路径下载文件（归档材料等按路径存储的场景）"""
    file_record = db.query(UploadedFile).filter(UploadedFile.file_path == path).first()
    if not file_record:
        # 元数据不存在但物理文件可能存在，直接尝试返回
        if os.path.exists(path):
            return FileResponse(
                path=path,
                filename=os.path.basename(path),
                media_type="application/octet-stream",
            )
        raise NotFoundException("文件不存在")

    if not os.path.exists(file_record.file_path):
        raise NotFoundException("文件在服务器上不存在")

    file_record.download_count = (file_record.download_count or 0) + 1
    db.commit()

    return FileResponse(
        path=file_record.file_path,
        filename=file_record.original_name,
        media_type=file_record.file_type or "application/octet-stream",
    )


@router.get("/{file_id}", summary="获取文件信息")
def get_file_info(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取文件元数据信息"""
    file_record = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file_record:
        raise NotFoundException("文件不存在")

    return success_response(data={
        "id": file_record.id,
        "original_name": file_record.original_name,
        "file_size": file_record.file_size,
        "file_type": file_record.file_type,
        "file_extension": file_record.file_extension,
        "module": file_record.module,
        "target_id": file_record.target_id,
        "download_count": file_record.download_count,
        "uploader_id": file_record.uploader_id,
        "create_time": file_record.create_time.isoformat() if file_record.create_time else None,
    })


@router.delete("/{file_id}", summary="删除文件")
def delete_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student_or_teacher),
):
    """删除文件（同时删除物理文件和元数据）"""
    file_record = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file_record:
        raise NotFoundException("文件不存在")

    # 权限校验：学生只能删除自己上传的文件
    if current_user.role == "student" and file_record.uploader_id != current_user.id:
        raise BusinessException(403, "无权删除他人上传的文件")

    # 删除物理文件
    if os.path.exists(file_record.file_path):
        try:
            os.remove(file_record.file_path)
        except OSError:
            pass

    db.delete(file_record)
    db.commit()
    return success_response(message="文件删除成功")
