"""
选题相关 Schema
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class TopicBase(BaseModel):
    """选题基础信息"""
    title: str = Field(..., min_length=5, max_length=200, description="题目名称")
    direction: Optional[str] = Field(default="", max_length=100, description="研究方向")
    background: Optional[str] = Field(default="", description="研究背景")
    significance: Optional[str] = Field(default="", description="研究意义")
    keywords: Optional[str] = Field(default="", max_length=200, description="关键词")
    source: Optional[str] = Field(default="", max_length=50, description="题目来源")
    difficulty: Optional[str] = Field(default="medium", description="难度")
    workload: Optional[str] = Field(default="medium", description="工作量")
    teacher_id: Optional[int] = Field(default=None, description="指导教师ID")


class TopicCreate(TopicBase):
    """创建选题请求"""
    pass


class TopicUpdate(BaseModel):
    """更新选题请求"""
    title: Optional[str] = None
    direction: Optional[str] = None
    background: Optional[str] = None
    significance: Optional[str] = None
    keywords: Optional[str] = None
    source: Optional[str] = None
    difficulty: Optional[str] = None
    workload: Optional[str] = None
    teacher_id: Optional[int] = None


class TopicReview(BaseModel):
    """选题审核请求"""
    status: str = Field(..., pattern="^(approved|rejected)$")
    reject_reason: Optional[str] = Field(default="", max_length=500)


class TopicResponse(TopicBase):
    """选题响应"""
    id: int
    student_id: int
    status: str
    reject_reason: str = ""
    review_time: Optional[datetime] = None
    reviewer_id: Optional[int] = None
    submit_time: Optional[datetime] = None
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None

    # 关联信息
    student_name: Optional[str] = ""
    student_no: Optional[str] = ""
    teacher_name: Optional[str] = ""

    class Config:
        from_attributes = True


class TopicListResponse(BaseModel):
    """选题列表响应"""
    total: int
    items: List[TopicResponse]


class TopicDuplicateCheck(BaseModel):
    """选题重复检测结果"""
    is_duplicate: bool
    duplicate_count: int
    similar_topics: List[dict]
    similarity_threshold: float = 0.7
