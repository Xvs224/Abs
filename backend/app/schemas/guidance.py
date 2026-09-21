"""
指导计划与记录相关 Schema
"""
from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel, Field


class GuidancePlanBase(BaseModel):
    """指导计划基础信息"""
    plan_name: str = Field(..., max_length=200, description="计划名称")
    total_times: int = Field(default=12, ge=1, description="预计指导次数")
    frequency: Optional[str] = Field(default="每周1次", max_length=50, description="指导频率")
    plan_content: Optional[str] = Field(default="", description="计划内容")
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class GuidancePlanCreate(GuidancePlanBase):
    """创建指导计划请求"""
    topic_id: int


class GuidancePlanUpdate(BaseModel):
    """更新指导计划请求"""
    plan_name: Optional[str] = None
    total_times: Optional[int] = None
    frequency: Optional[str] = None
    plan_content: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = None


class GuidancePlanResponse(GuidancePlanBase):
    """指导计划响应"""
    id: int
    topic_id: int
    teacher_id: int
    student_id: int
    status: str
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None

    # 关联信息
    topic_title: Optional[str] = ""
    student_name: Optional[str] = ""
    teacher_name: Optional[str] = ""
    record_count: Optional[int] = 0

    class Config:
        from_attributes = True


class GuidanceRecordBase(BaseModel):
    """指导记录基础信息"""
    record_type: Optional[str] = Field(default="regular", max_length=20)
    method: Optional[str] = Field(default="online", max_length=20)
    location: Optional[str] = Field(default="", max_length=100)
    duration: Optional[int] = Field(default=0, ge=0)
    content: Optional[str] = Field(default="", description="指导内容")
    teacher_opinion: Optional[str] = Field(default="", description="教师意见")
    student_task: Optional[str] = Field(default="", description="学生任务")
    next_guidance_date: Optional[date] = None
    record_time: Optional[datetime] = None


class GuidanceRecordCreate(GuidanceRecordBase):
    """创建指导记录请求"""
    plan_id: int


class GuidanceRecordUpdate(BaseModel):
    """更新指导记录请求"""
    record_type: Optional[str] = None
    method: Optional[str] = None
    location: Optional[str] = None
    duration: Optional[int] = None
    content: Optional[str] = None
    teacher_opinion: Optional[str] = None
    student_task: Optional[str] = None
    next_guidance_date: Optional[date] = None
    record_time: Optional[datetime] = None
    attachment_path: Optional[str] = None
    attachment_name: Optional[str] = None


class GuidanceRecordResponse(GuidanceRecordBase):
    """指导记录响应"""
    id: int
    plan_id: int
    topic_id: int
    teacher_id: int
    student_id: int
    attachment_path: str = ""
    attachment_name: str = ""
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None

    # 关联信息
    teacher_name: Optional[str] = ""
    student_name: Optional[str] = ""

    class Config:
        from_attributes = True


class GuidancePlanListResponse(BaseModel):
    """指导计划列表响应"""
    total: int
    items: List[GuidancePlanResponse]


class GuidanceRecordListResponse(BaseModel):
    """指导记录列表响应"""
    total: int
    items: List[GuidanceRecordResponse]
