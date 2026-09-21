"""
用户相关 Schema
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr


class UserBase(BaseModel):
    """用户基础信息"""
    username: str = Field(..., min_length=2, max_length=50)
    real_name: str = Field(..., min_length=2, max_length=50)
    role: str = Field(..., pattern="^(student|teacher|admin)$")
    email: Optional[str] = Field(default="", max_length=100)
    phone: Optional[str] = Field(default="", max_length=20)
    department: Optional[str] = Field(default="", max_length=100)
    student_no: Optional[str] = Field(default="", max_length=50)
    teacher_no: Optional[str] = Field(default="", max_length=50)
    grade: Optional[str] = Field(default="", max_length=20)
    major: Optional[str] = Field(default="", max_length=100)


class UserCreate(UserBase):
    """创建用户请求"""
    password: str = Field(..., min_length=6, max_length=50, description="密码")


class UserUpdate(BaseModel):
    """更新用户请求"""
    real_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    student_no: Optional[str] = None
    teacher_no: Optional[str] = None
    grade: Optional[str] = None
    major: Optional[str] = None
    status: Optional[int] = None


class UserUpdatePassword(BaseModel):
    """修改密码请求"""
    old_password: str = Field(..., min_length=6, max_length=50)
    new_password: str = Field(..., min_length=6, max_length=50)


class UserResponse(UserBase):
    """用户响应"""
    id: int
    avatar: str = ""
    status: int = 1
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """用户列表响应"""
    total: int
    items: List[UserResponse]
