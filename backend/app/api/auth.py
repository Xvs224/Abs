"""
认证路由
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.core.response import success_response, ResponseModel
from app.core.security import get_current_user
from app.core.limiter import limiter
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse, UserInfo, RefreshTokenRequest, LogoutRequest
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["认证"])


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """获取认证服务实例"""
    return AuthService(db)


@router.post("/login", response_model=ResponseModel[LoginResponse])
@limiter.limit(settings.RATE_LIMIT_LOGIN)
def login(
    request: Request,
    login_data: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    用户登录（限流：5次/分钟）

    - **username**: 用户名
    - **password**: 密码
    """
    result = auth_service.login(login_data)
    return success_response(data=result, message="登录成功")


@router.post("/refresh", response_model=ResponseModel)
def refresh_token(
    data: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    刷新访问令牌

    - **refresh_token**: 登录时获取的刷新令牌
    """
    result = auth_service.refresh_access_token(data.refresh_token)
    return success_response(data=result, message="令牌刷新成功")


@router.post("/logout", response_model=ResponseModel)
def logout(
    data: LogoutRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    用户登出 — 撤销 access_token 和 refresh_token
    """
    auth_service.logout(data.access_token, data.refresh_token)
    return success_response(data=None, message="登出成功")


@router.get("/me", response_model=ResponseModel[UserInfo])
def get_me(
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """获取当前登录用户信息"""
    user_info = auth_service.get_user_info(current_user)
    return success_response(data=user_info, message="获取成功")
