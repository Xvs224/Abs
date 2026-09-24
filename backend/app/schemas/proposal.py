"""
开题报告相关 Schema
"""
from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel, Field


class ProposalBase(BaseModel):
    """开题报告基础信息"""
    research_content: Optional[str] = Field(default="", description="研究内容")
    research_method: Optional[str] = Field(default="", description="研究方法")
    technical_route: Optional[str] = Field(default="", description="技术路线")
    expected_results: Optional[str] = Field(default="", description="预期成果")
    schedule_plan: Optional[str] = Field(default="", description="进度安排")
    word_count: Optional[int] = Field(default=0, description="字数")


class ProposalCreate(ProposalBase):
    """创建开题报告请求"""
    topic_id: int
    file_id: Optional[int] = Field(default=None, description="上传文件ID")
    file_path: Optional[str] = Field(default="", description="文件路径")
    file_name: Optional[str] = Field(default="", description="文件名")


class ProposalUpdate(BaseModel):
    """更新开题报告请求"""
    research_content: Optional[str] = None
    research_method: Optional[str] = None
    technical_route: Optional[str] = None
    expected_results: Optional[str] = None
    schedule_plan: Optional[str] = None
    word_count: Optional[int] = None
    file_id: Optional[int] = None
    file_path: Optional[str] = None
    file_name: Optional[str] = None


class ProposalReview(BaseModel):
    """开题审核请求"""
    status: str = Field(..., pattern="^(approved|rejected)$")
    review_opinion: Optional[str] = Field(default="", description="审核意见")


class ProposalSubmit(BaseModel):
    """提交开题报告请求"""
    pass


class ProposalResponse(ProposalBase):
    """开题报告响应"""
    id: int
    topic_id: int
    student_id: int
    teacher_id: Optional[int] = None
    file_id: Optional[int] = None
    file_path: str = ""
    file_name: str = ""
    status: str
    review_opinion: str = ""
    review_time: Optional[datetime] = None
    reviewer_id: Optional[int] = None
    submit_time: Optional[datetime] = None
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None

    # 关联信息
    topic_title: Optional[str] = ""
    student_name: Optional[str] = ""
    teacher_name: Optional[str] = ""

    class Config:
        from_attributes = True


class ProposalListResponse(BaseModel):
    """开题报告列表响应"""
    total: int
    items: List[ProposalResponse]
