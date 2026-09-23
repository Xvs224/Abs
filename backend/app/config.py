"""
应用配置模块
"""
import os
import secrets
import logging
from pydantic_settings import BaseSettings
from typing import Optional, List

logger = logging.getLogger(__name__)

_DEFAULT_INSECURE_KEY = "your-secret-key-change-in-production-please-change-this-key"
_INSECURE_KEY_MARKERS = {"your-secret-key", "change-in-production", "change-this-key", "please-change"}


def _is_insecure_secret(value: str) -> bool:
    lowered = value.lower()
    if lowered == _DEFAULT_INSECURE_KEY:
        return True
    return any(marker in lowered for marker in _INSECURE_KEY_MARKERS)


class Settings(BaseSettings):
    """应用全局配置"""

    # 应用基本信息
    APP_NAME: str = "毕业论文质量监控系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # 数据库配置
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "thesis_monitor"

    # JWT 配置
    JWT_SECRET_KEY: str = _DEFAULT_INSECURE_KEY
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24小时
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # 刷新令牌有效期

    # CORS 配置（逗号分隔的域名列表，生产环境必须配置具体域名）
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"

    # 上传配置
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 52428800  # 50MB

    # 允许的文件扩展名（逗号分隔）
    ALLOWED_FILE_EXTENSIONS: str = ".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.zip,.rar,.txt"

    # 异常检测配置
    ANOMALY_IQR_THRESHOLD: float = 1.5
    ANOMALY_ISOLATION_FOREST_CONTAMINATION: float = 0.1

    # 定时自动检测配置
    ANOMALY_AUTO_DETECT_ENABLED: bool = True          # 是否启用定时检测
    ANOMALY_DETECTION_CRON: str = "0 2 * * *"          # cron 表达式，默认每天凌晨 2 点
    ANOMALY_DETECTION_TIMEZONE: str = "Asia/Shanghai"  # 调度时区

    # 限流配置
    RATE_LIMIT_LOGIN: str = "5/minute"
    RATE_LIMIT_DEFAULT: str = "100/minute"

    @property
    def DATABASE_URL(self) -> str:
        """构造数据库连接URL"""
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"

    @property
    def cors_origins_list(self) -> List[str]:
        """解析 CORS 域名列表"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def allowed_extensions_list(self) -> List[str]:
        """解析允许的文件扩展名列表"""
        return [ext.strip().lower() for ext in self.ALLOWED_FILE_EXTENSIONS.split(",") if ext.strip()]

    def validate_security(self) -> None:
        """启动时校验安全配置，不达标直接报错阻断启动"""
        if _is_insecure_secret(self.JWT_SECRET_KEY):
            if self.DEBUG:
                # 开发模式下自动生成临时密钥并警告
                self.JWT_SECRET_KEY = secrets.token_urlsafe(32)
                logger.warning(
                    "JWT_SECRET_KEY 使用了不安全的默认值，开发模式下已自动生成临时密钥。"
                    "生产环境务必在 .env 中配置固定的高强度密钥。"
                )
            else:
                raise RuntimeError(
                    "JWT_SECRET_KEY 未配置或使用了不安全的默认值。"
                    "请在 .env 文件中设置 JWT_SECRET_KEY 为一个高强度随机字符串。"
                )

        if not self.DEBUG and "*" in self.cors_origins_list:
            raise RuntimeError(
                "生产环境（DEBUG=False）不允许 CORS 通配符 '*'，"
                "请在 .env 中配置 CORS_ORIGINS 为具体的域名列表。"
            )

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
settings.validate_security()
