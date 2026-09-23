"""
成果归档相关 Schema
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class ArchiveBase(BaseModel):
    """归档基础信息"""
    archive_no: Optional[str] = Field(default="", max_length=50)
    archive_location: Optional[str] = Field(default="", max_length=200)


class ArchiveCreate(BaseModel):
    """创建归档请求"""
    topic_id: int
    final_version_id: Optional[int] = None


class ArchiveUpdate(BaseModel):
    """更新归档请求"""
    thesis_file: Optional[str] = None
    proposal_file: Optional[str] = None
    midterm_file: Optional[str] = None
    review_file: Optional[str] = None
    defense_file: Optional[str] = None
    other_materials: Optional[str] = None
    final_score: Optional[int] = None
    final_grade: Optional[str] = None
    archive_no: Optional[str] = None
    archive_location: Optional[str] = None


class ArchiveReview(BaseModel):
    """归档审核请求"""
    status: str = Field(..., pattern="^(archived|returned)$")
    return_reason: Optional[str] = Field(default="", max_length=500)


class ArchiveResponse(ArchiveBase):
    """归档响应"""
    id: int
    topic_id: int
    student_id: int
    teacher_id: Optional[int] = None
    final_version_id: Optional[int] = None
    thesis_file: str = ""
    proposal_file: str = ""
    midterm_file: str = ""
    review_file: str = ""
    defense_file: str = ""
    other_materials: str = ""
    final_score: int = 0
    final_grade: str = ""
    defense_result: Optional[str] = ""
    archivist_id: Optional[int] = None
    status: str
    return_reason: str = ""
    archive_time: Optional[datetime] = None
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None

    # 关联信息
    topic_title: Optional[str] = ""
    student_name: Optional[str] = ""
    teacher_name: Optional[str] = ""

    class Config:
        from_attributes = True


class ArchiveListResponse(BaseModel):
    """归档列表响应"""
    total: int
    items: List[ArchiveResponse]
