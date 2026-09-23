"""
文件元数据模型
"""
from sqlalchemy import Column, Integer, String, DateTime, BigInteger, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class UploadedFile(Base):
    """上传文件元数据表"""
    __tablename__ = "uploaded_files"

    id = Column(Integer, primary_key=True, index=True, comment="文件ID")
    original_name = Column(String(255), nullable=False, comment="原始文件名")
    stored_name = Column(String(255), nullable=False, comment="存储文件名")
    file_path = Column(String(500), nullable=False, comment="文件存储路径")
    file_size = Column(BigInteger, default=0, comment="文件大小（字节）")
    file_type = Column(String(255), default="", comment="文件MIME类型")
    file_extension = Column(String(20), default="", comment="文件扩展名")

    uploader_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="上传者ID")

    # 关联的业务对象（可选，用于追溯文件归属）
    module = Column(String(50), default="", comment="业务模块: thesis/proposal/midterm/archive等")
    target_id = Column(Integer, default=None, comment="关联目标ID")

    download_count = Column(Integer, default=0, comment="下载次数")

    create_time = Column(DateTime, server_default=func.now(), comment="上传时间")

    uploader = relationship("User", foreign_keys=[uploader_id])

    def __repr__(self):
        return f"<UploadedFile(id={self.id}, name='{self.original_name}')>"
