"""
认证服务
"""
from datetime import timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.core.security import verify_password, create_access_token
from app.core.exceptions import UnauthorizedException
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse, UserInfo


class AuthService:
    """认证服务类"""

    def __init__(self, db: Session):
        self.db = db

    def login(self, login_data: LoginRequest) -> LoginResponse:
        """
        用户登录：验证用户名密码，返回 token

        :param login_data: 登录请求数据
        :return: 登录响应（包含 token 和用户信息）
        :raises UnauthorizedException: 用户名或密码错误
        """
        # 查询用户
        user: Optional[User] = (
            self.db.query(User)
            .filter(User.username == login_data.username)
            .first()
        )

        if not user:
            raise UnauthorizedException("用户名或密码错误")

        # 验证密码
        if not verify_password(login_data.password, user.password_hash):
            raise UnauthorizedException("用户名或密码错误")

        # 检查账号状态
        if user.status != 1:
            raise UnauthorizedException("账号已被禁用")

        # 创建访问令牌
        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "username": user.username,
                "role": user.role,
            },
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )

        # 构造用户信息
        user_info = UserInfo(
            id=user.id,
            username=user.username,
            real_name=user.real_name,
            role=user.role,
            email=user.email or "",
            department=user.department or "",
            avatar=user.avatar or "",
        )

        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_info,
        )

    def get_user_info(self, user: User) -> UserInfo:
        """
        获取当前用户信息

        :param user: 当前用户对象
        :return: 用户信息
        """
        return UserInfo(
            id=user.id,
            username=user.username,
            real_name=user.real_name,
            role=user.role,
            email=user.email or "",
            department=user.department or "",
            avatar=user.avatar or "",
        )
