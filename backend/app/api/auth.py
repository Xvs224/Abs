"""
认证路由
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.response import success_response, ResponseModel
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse, UserInfo
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["认证"])


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """获取认证服务实例"""
    return AuthService(db)


@router.post("/login", response_model=ResponseModel[LoginResponse])
def login(
    login_data: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    用户登录

    - **username**: 用户名
    - **password**: 密码
    """
    result = auth_service.login(login_data)
    return success_response(data=result, message="登录成功")


@router.get("/me", response_model=ResponseModel[UserInfo])
def get_me(
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    获取当前登录用户信息
    """
    user_info = auth_service.get_user_info(current_user)
    return success_response(data=user_info, message="获取成功")


@router.post("/logout", response_model=ResponseModel)
def logout():
    """
    用户登出

    说明：由于 JWT 是无状态的，登出操作主要由前端清除本地 token 完成。
    后端此接口仅作为统一登出入口，如需服务端 token 黑名单机制可在此扩展。
    """
    return success_response(data=None, message="登出成功")
