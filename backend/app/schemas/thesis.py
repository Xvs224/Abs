"""
论文版本相关 Schema
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ThesisVersionBase(BaseModel):
    """论文版本基础信息"""
    version_name: Optional[str] = Field(default="", max_length=200, description="版本名称")
    change_log: Optional[str] = Field(default="", description="修改说明")


class ThesisVersionCreate(ThesisVersionBase):
    """创建论文版本请求"""
    topic_id: int
    file_path: str
    file_name: str
    file_size: Optional[int] = 0
    file_type: Optional[str] = ""


class ThesisVersionUpdate(BaseModel):
    """更新论文版本请求"""
    version_name: Optional[str] = None
    change_log: Optional[str] = None


class ThesisVersionResponse(ThesisVersionBase):
    """论文版本响应"""
    id: int
    topic_id: int
    student_id: int
    version_num: int
    file_path: str
    file_name: str
    file_size: int = 0
    file_type: str = ""
    word_count: int = 0
    page_count: int = 0
    chapter_count: int = 0
    reference_count: int = 0
    format_check_status: str = "pending"
    format_score: float = 0.0
    submit_time: Optional[datetime] = None
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None

    # 关联信息
    topic_title: Optional[str] = ""
    student_name: Optional[str] = ""

    class Config:
        from_attributes = True


class FormatCheckItem(BaseModel):
    """格式检测项"""
    name: str
    passed: bool
    score: float
    max_score: float
    message: str = ""


class FormatCheckResult(BaseModel):
    """格式检测结果"""
    version_id: int
    total_score: float
    max_score: float
    passed_count: int
    failed_count: int
    total_items: int
    overall_result: str
    problems_summary: str = ""
    suggestions: str = ""
    check_items: List[Dict[str, Any]] = []
    check_time: Optional[datetime] = None


class ThesisVersionListResponse(BaseModel):
    """论文版本列表响应"""
    total: int
    items: List[ThesisVersionResponse]


class VersionCompareResponse(BaseModel):
    """版本对比响应"""
    version_a: ThesisVersionResponse
    version_b: ThesisVersionResponse
    differences: List[Dict[str, Any]]
