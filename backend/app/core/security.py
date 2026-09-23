"""
安全认证模块
"""
import uuid
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
from app.models.token_blacklist import RevokedToken
from app.core.exceptions import UnauthorizedException, ForbiddenException

# 密码哈希上下文（使用 pbkdf2_sha256 避免 bcrypt 版本兼容问题）
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# OAuth2 令牌承载 — auto_error=True 确保无 token 时直接返回 401
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=True)


def hash_password(password: str) -> str:
    """哈希密码"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌（包含 jti 用于撤销追踪）"""
    to_encode = data.copy()
    jti = str(uuid.uuid4())
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "jti": jti, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建刷新令牌（有效期更长，仅用于获取新 access token）"""
    to_encode = data.copy()
    jti = str(uuid.uuid4())
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "jti": jti, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict:
    """解码令牌"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return {}


def is_token_revoked(db: Session, jti: str) -> bool:
    """检查令牌是否已被撤销"""
    return db.query(RevokedToken).filter(RevokedToken.jti == jti).first() is not None


def revoke_token(db: Session, token: str) -> bool:
    """撤销令牌（加入黑名单）"""
    payload = decode_token(token)
    jti = payload.get("jti")
    if not jti:
        return False

    existing = db.query(RevokedToken).filter(RevokedToken.jti == jti).first()
    if existing:
        return True

    exp = payload.get("exp")
    expires_at = datetime.utcfromtimestamp(exp) if exp else datetime.utcnow()

    revoked = RevokedToken(
        jti=jti,
        user_id=int(payload.get("sub", 0)),
        token_type=payload.get("type", "access"),
        expires_at=expires_at,
    )
    db.add(revoked)
    db.commit()
    return True


def get_current_user(token: str = Depends(oauth2_scheme),
                     db: Session = Depends(get_db)) -> User:
    """获取当前登录用户（校验黑名单）"""
    payload = decode_token(token)
    user_id: Optional[str] = payload.get("sub")
    if user_id is None:
        raise UnauthorizedException("无效的认证令牌")

    # 检查令牌类型
    token_type = payload.get("type")
    if token_type == "refresh":
        raise UnauthorizedException("刷新令牌不能用于接口访问")

    # 检查是否已被撤销
    jti = payload.get("jti")
    if jti and is_token_revoked(db, jti):
        raise UnauthorizedException("令牌已被撤销，请重新登录")

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
# 语义说明：
#   require_admin          — 仅管理员（用户管理、操作日志、全局配置）
#   require_teacher_only   — 仅教师（发布选题、审核、指导、评审等教师专属业务操作）
#   require_student_only   — 仅学生
#   require_admin_or_teacher — admin 和 teacher 都能进（业务列表/详情接口，进去后按 role 做数据隔离）
#   require_any_authenticated — 任何登录用户（list 接口，进去后按 role 做数据隔离）
require_admin = require_role(["admin"])
require_teacher_only = require_role(["teacher"])
require_student_only = require_role(["student"])
require_admin_or_teacher = require_role(["admin", "teacher"])
require_any_authenticated = require_role(["admin", "teacher", "student"])

# 兼容旧名（谨慎使用，推荐使用上面语义清晰的名称）
require_teacher = require_admin_or_teacher  # 兼容：admin 与 teacher 都能进，进去后按 role 隔离数据
require_student = require_any_authenticated  # 兼容：admin 也能访问学生接口（调试用）
require_student_or_teacher = require_any_authenticated
require_teacher_or_admin = require_admin_or_teacher
