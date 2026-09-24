"""过程指导记录 Schema"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class GuidanceCreate(BaseModel):
    topic_id: int = Field(..., description="选题ID")
    guidance_type: str = Field("meeting", description="指导方式: meeting/written/online/phone/other")
    guidance_time: Optional[datetime] = None
    title: str = Field("", max_length=200, description="指导主题")
    content: str = Field(..., min_length=1, description="指导内容")


class GuidanceReply(BaseModel):
    student_response: str = Field(..., min_length=1, description="学生回复内容")


class GuidanceTeacherReply(BaseModel):
    teacher_response: str = Field(..., min_length=1, description="教师回复内容")


class GuidanceUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    guidance_type: Optional[str] = None
    guidance_time: Optional[datetime] = None


class GuidanceResponse(BaseModel):
    id: int
    topic_id: int
    topic_title: Optional[str] = None
    student_id: int
    student_name: Optional[str] = None
    teacher_id: int
    teacher_name: Optional[str] = None
    initiator: str
    guidance_type: str
    guidance_time: Optional[datetime] = None
    title: str
    content: str
    student_response: str = ""
    student_reply_time: Optional[datetime] = None
    teacher_response: str = ""
    teacher_reply_time: Optional[datetime] = None
    status: str
    create_time: datetime

    class Config:
        from_attributes = True
