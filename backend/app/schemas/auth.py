"""
认证相关 Schema
"""
from typing import Optional
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., min_length=2, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=50, description="密码")


class LoginResponse(BaseModel):
    """登录响应"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserInfo"


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求"""
    refresh_token: str = Field(..., description="刷新令牌")


class LogoutRequest(BaseModel):
    """登出请求"""
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None


class TokenPayload(BaseModel):
    """令牌载荷"""
    sub: int  # 用户ID
    username: str
    role: str
    exp: Optional[int] = None


class UserInfo(BaseModel):
    """用户信息（登录返回）"""
    id: int
    username: str
    real_name: str
    role: str
    email: str = ""
    phone: str = ""
    department: str = ""
    student_no: str = ""
    teacher_no: str = ""
    grade: str = ""
    major: str = ""
    avatar: str = ""

    class Config:
        from_attributes = True
