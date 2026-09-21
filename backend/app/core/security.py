"""
安全认证模块
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.core.exceptions import UnauthorizedException, ForbiddenException

# 密码哈希上下文（使用 pbkdf2_sha256 避免 bcrypt 版本兼容问题）
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# OAuth2 令牌承载
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def hash_password(password: str) -> str:
    """哈希密码"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict:
    """解码令牌"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return {}


def get_current_user(token: str = Depends(oauth2_scheme),
                     db: Session = Depends(get_db)) -> User:
    """获取当前登录用户"""
    if not token:
        raise UnauthorizedException("未提供认证令牌")

    payload = decode_token(token)
    user_id: Optional[int] = payload.get("sub")
    if user_id is None:
        raise UnauthorizedException("无效的认证令牌")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise UnauthorizedException("用户不存在")

    if user.status != 1:
        raise UnauthorizedException("账号已被禁用")

    return user


def require_role(allowed_roles: list):
    """角色权限装饰器工厂"""

    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise ForbiddenException(f"需要以下角色之一: {', '.join(allowed_roles)}")
        return current_user

    return role_checker


# 预定义的角色检查依赖
require_admin = require_role(["admin"])
require_teacher = require_role(["teacher", "admin"])
require_student = require_role(["student", "admin"])
require_teacher_or_admin = require_role(["teacher", "admin"])
require_student_or_teacher = require_role(["student", "teacher", "admin"])
