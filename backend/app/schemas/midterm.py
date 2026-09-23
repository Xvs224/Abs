"""
中期检查相关 Schema
"""
from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel, Field


class MidtermCheckBase(BaseModel):
    """中期检查基础信息"""
    progress_description: Optional[str] = Field(default="", description="进度描述")
    completed_work: Optional[str] = Field(default="", description="已完成工作")
    remaining_work: Optional[str] = Field(default="", description="剩余工作")
    progress_percentage: Optional[float] = Field(default=0.0, ge=0, le=100, description="进度百分比")
    existing_problems: Optional[str] = Field(default="", description="存在的问题")
    next_plan: Optional[str] = Field(default="", description="下一步计划")


class MidtermCheckCreate(MidtermCheckBase):
    """创建中期检查请求"""
    topic_id: int
    file_id: Optional[int] = None
    file_path: Optional[str] = ""
    file_name: Optional[str] = ""


class MidtermCheckUpdate(BaseModel):
    """更新中期检查请求"""
    progress_description: Optional[str] = None
    completed_work: Optional[str] = None
    remaining_work: Optional[str] = None
    progress_percentage: Optional[float] = None
    existing_problems: Optional[str] = None
    next_plan: Optional[str] = None
    file_id: Optional[int] = None
    file_path: Optional[str] = None
    file_name: Optional[str] = None
    ppt_file_id: Optional[int] = None
    ppt_file_path: Optional[str] = None
    ppt_file_name: Optional[str] = None


class MidtermGuidance(BaseModel):
    """教师指导请求（阶段1）"""
    teacher_guidance: str = Field(..., min_length=1, description="教师指导意见")


class MidtermPPTSubmit(BaseModel):
    """学生提交PPT请求"""
    ppt_file_id: int
    ppt_file_path: str
    ppt_file_name: str


class MidtermReview(BaseModel):
    """中期检查最终评审请求（阶段2）"""
    teacher_score: Optional[float] = None
    teacher_opinion: Optional[str] = ""
    check_group_score: Optional[float] = None
    check_group_opinion: Optional[str] = ""
    final_score: Optional[float] = None
    status: str = Field(..., pattern="^(passed|failed|rectifying)$")


class MidtermSubmit(BaseModel):
    """提交中期检查请求"""
    pass


class MidtermCheckResponse(MidtermCheckBase):
    """中期检查响应"""
    id: int
    topic_id: int
    student_id: int
    teacher_id: Optional[int] = None
    file_id: Optional[int] = None
    file_path: str = ""
    file_name: str = ""
    ppt_file_id: Optional[int] = None
    ppt_file_path: str = ""
    ppt_file_name: str = ""
    stage: str = "form"
    teacher_guidance: str = ""
    guidance_time: Optional[datetime] = None
    teacher_score: float = 0.0
    teacher_opinion: str = ""
    check_group_score: float = 0.0
    check_group_opinion: str = ""
    final_score: float = 0.0
    status: str
    submit_time: Optional[datetime] = None
    check_time: Optional[datetime] = None
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None

    # 关联信息
    topic_title: Optional[str] = ""
    student_name: Optional[str] = ""
    teacher_name: Optional[str] = ""
    rectification_count: Optional[int] = 0

    class Config:
        from_attributes = True


class RectificationBase(BaseModel):
    """整改基础信息"""
    problem_description: str = Field(..., description="问题描述")
    requirement: Optional[str] = Field(default="", description="整改要求")
    deadline: Optional[date] = None


class RectificationCreate(RectificationBase):
    """创建整改请求"""
    midterm_id: int
    topic_id: int


class RectificationSubmit(BaseModel):
    """提交整改请求"""
    rectification_content: str
    rectification_file_path: Optional[str] = ""
    rectification_file_name: Optional[str] = ""


class RectificationReview(BaseModel):
    """复检请求"""
    review_opinion: str = ""
    review_result: str = Field(..., pattern="^(passed|failed)$")


class RectificationResponse(RectificationBase):
    """整改响应"""
    id: int
    midterm_id: int
    topic_id: int
    rectification_content: str = ""
    rectification_file_path: str = ""
    rectification_file_name: str = ""
    submit_time: Optional[datetime] = None
    reviewer_id: Optional[int] = None
    review_opinion: str = ""
    review_result: str = ""
    review_time: Optional[datetime] = None
    status: str
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None

    class Config:
        from_attributes = True


class MidtermCheckListResponse(BaseModel):
    """中期检查列表响应"""
    total: int
    items: List[MidtermCheckResponse]


class RectificationListResponse(BaseModel):
    """整改列表响应"""
    total: int
    items: List[RectificationResponse]
