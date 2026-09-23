"""
Token 黑名单模型 — 支持令牌撤销
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func

from app.database import Base


class RevokedToken(Base):
    """已撤销令牌表"""
    __tablename__ = "revoked_tokens"

    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    jti = Column(String(64), unique=True, index=True, nullable=False, comment="JWT唯一标识")
    user_id = Column(Integer, index=True, nullable=False, comment="用户ID")
    token_type = Column(String(20), default="access", comment="令牌类型: access/refresh")
    revoked_at = Column(DateTime, server_default=func.now(), comment="撤销时间")
    expires_at = Column(DateTime, nullable=False, comment="令牌原始过期时间，用于清理")

    def __repr__(self):
        return f"<RevokedToken(jti='{self.jti}', user_id={self.user_id})>"
