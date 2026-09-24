"""
评阅与答辩相关 Schema
"""
from typing import Optional, List
from datetime import datetime, date, time
from pydantic import BaseModel, Field


class ReviewBase(BaseModel):
    """评阅基础信息"""
    review_type: Optional[str] = Field(default="normal", max_length=20)
    topic_score: Optional[float] = Field(default=0.0, ge=0, le=100)
    content_score: Optional[float] = Field(default=0.0, ge=0, le=100)
    method_score: Optional[float] = Field(default=0.0, ge=0, le=100)
    innovation_score: Optional[float] = Field(default=0.0, ge=0, le=100)
    format_score: Optional[float] = Field(default=0.0, ge=0, le=100)
    opinion: Optional[str] = Field(default="", description="评阅意见")
    suggestions: Optional[str] = Field(default="", description="修改建议")
    result: Optional[str] = Field(default="", max_length=20)


class ReviewCreate(BaseModel):
    """创建评阅请求"""
    topic_id: int
    reviewer_id: int
    review_type: Optional[str] = "normal"
    version_id: Optional[int] = None
    deadline: Optional[datetime] = None


class ReviewApply(BaseModel):
    """学生申请评阅请求（含首次申请和再次评阅）"""
    version_id: int = Field(..., description="待评阅的论文版本ID")
    review_type: Optional[str] = "normal"


class ReviewSubmit(BaseModel):
    """提交评阅结果请求"""
    topic_score: float = Field(..., ge=0, le=100)
    content_score: float = Field(..., ge=0, le=100)
    method_score: float = Field(..., ge=0, le=100)
    innovation_score: float = Field(..., ge=0, le=100)
    format_score: float = Field(..., ge=0, le=100)
    total_score: Optional[float] = None
    opinion: str = ""
    suggestions: str = ""
    result: str = Field(..., pattern="^(pass|revision|reject)$")
    review_file_id: Optional[int] = None
    review_file_path: Optional[str] = ""
    review_file_name: Optional[str] = ""


class ReviewResponse(ReviewBase):
    """评阅响应"""
    id: int
    topic_id: int
    student_id: int
    reviewer_id: int
    version_id: Optional[int] = None
    total_score: float = 0.0
    deadline: Optional[datetime] = None
    review_time: Optional[datetime] = None
    status: str
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None

    # 关联信息
    topic_title: Optional[str] = ""
    student_name: Optional[str] = ""
    reviewer_name: Optional[str] = ""
    review_file_id: Optional[int] = None
    review_file_path: Optional[str] = ""
    review_file_name: Optional[str] = ""

    class Config:
        from_attributes = True


class DefenseBase(BaseModel):
    """答辩基础信息"""
    defense_date: Optional[date] = None
    defense_time_start: Optional[time] = None
    defense_time_end: Optional[time] = None
    location: Optional[str] = Field(default="", max_length=200)
    defense_form: Optional[str] = Field(default="offline", max_length=20)
    chair_id: Optional[int] = None
    committee_members: Optional[str] = Field(default="", max_length=500)
    secretary_id: Optional[int] = None


class DefenseCreate(DefenseBase):
    """创建答辩安排请求"""
    topic_id: int
    status: Optional[str] = Field(default=None, pattern="^(pending|scheduled|completed|in_progress)$")


class DefenseScore(BaseModel):
    """答辩评分请求"""
    presentation_score: float = Field(..., ge=0, le=100)
    qa_score: float = Field(..., ge=0, le=100)
    thesis_quality_score: float = Field(..., ge=0, le=100)
    total_score: Optional[float] = None
    grade: Optional[str] = ""
    opinion: str = ""
    suggestions: str = ""
    result: str = Field(..., pattern="^(pass|fail|reargue)$")
    defense_file_id: Optional[int] = None
    defense_file_path: Optional[str] = ""
    defense_file_name: Optional[str] = ""


class DefenseResponse(DefenseBase):
    """答辩响应"""
    id: int
    topic_id: int
    student_id: int
    presentation_score: float = 0.0
    qa_score: float = 0.0
    thesis_quality_score: float = 0.0
    total_score: float = 0.0
    grade: str = ""
    opinion: str = ""
    suggestions: str = ""
    result: str = ""
    re_defense_date: Optional[date] = None
    re_defense_result: str = ""
    status: str
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None
    defense_file_id: Optional[int] = None
    defense_file_path: Optional[str] = ""
    defense_file_name: Optional[str] = ""

    # 关联信息
    topic_title: Optional[str] = ""
    student_name: Optional[str] = ""
    chair_name: Optional[str] = ""
    secretary_name: Optional[str] = ""
    committee_member_names: Optional[str] = ""
    review_result: Optional[str] = ""
    review_result_text: Optional[str] = "未评阅"
    review_passed: Optional[bool] = False

    class Config:
        from_attributes = True


class ReviewListResponse(BaseModel):
    """评阅列表响应"""
    total: int
    items: List[ReviewResponse]


class DefenseListResponse(BaseModel):
    """答辩列表响应"""
    total: int
    items: List[DefenseResponse]
