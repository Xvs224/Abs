"""
认证服务
"""
from datetime import timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.core.security import (
    verify_password, create_access_token, create_refresh_token,
    decode_token, revoke_token, is_token_revoked,
)
from app.core.exceptions import UnauthorizedException
from app.models.user import User
from app.models.token_blacklist import RevokedToken
from app.schemas.auth import LoginRequest, LoginResponse, UserInfo


class AuthService:
    """认证服务类"""

    def __init__(self, db: Session):
        self.db = db

    def login(self, login_data: LoginRequest) -> LoginResponse:
        """
        用户登录：验证用户名密码，返回 access_token + refresh_token
        """
        user: Optional[User] = (
            self.db.query(User)
            .filter(User.username == login_data.username)
            .first()
        )

        if not user:
            raise UnauthorizedException("用户名或密码错误")

        if not verify_password(login_data.password, user.password_hash):
            raise UnauthorizedException("用户名或密码错误")

        if user.status != 1:
            raise UnauthorizedException("账号已被禁用")

        token_data = {
            "sub": str(user.id),
            "username": user.username,
            "role": user.role,
        }

        access_token = create_access_token(
            data=token_data,
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        refresh_token = create_refresh_token(
            data=token_data,
            expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )

        user_info = self.get_user_info(user)

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_info,
        )

    def refresh_access_token(self, refresh_token: str) -> dict:
        """使用 refresh_token 获取新的 access_token"""
        payload = decode_token(refresh_token)
        user_id = payload.get("sub")

        if not user_id:
            raise UnauthorizedException("无效的刷新令牌")

        if payload.get("type") != "refresh":
            raise UnauthorizedException("令牌类型错误，需要刷新令牌")

        jti = payload.get("jti")
        if jti and is_token_revoked(self.db, jti):
            raise UnauthorizedException("刷新令牌已被撤销，请重新登录")

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user or user.status != 1:
            raise UnauthorizedException("用户不存在或已被禁用")

        new_access_token = create_access_token(
            data={"sub": str(user.id), "username": user.username, "role": user.role},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )

        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    def logout(self, access_token: Optional[str], refresh_token: Optional[str]) -> None:
        """登出：撤销 access_token 和 refresh_token"""
        if access_token:
            revoke_token(self.db, access_token)
        if refresh_token:
            revoke_token(self.db, refresh_token)

    def get_user_info(self, user: User) -> UserInfo:
        """获取当前用户信息"""
        return UserInfo(
            id=user.id,
            username=user.username,
            real_name=user.real_name,
            role=user.role,
            email=user.email or "",
            phone=user.phone or "",
            department=user.department or "",
            student_no=user.student_no or "",
            teacher_no=user.teacher_no or "",
            grade=user.grade or "",
            major=user.major or "",
            avatar=user.avatar or "",
        )
