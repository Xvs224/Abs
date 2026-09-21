"""
应用配置模块
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用全局配置"""

    # 应用基本信息
    APP_NAME: str = "毕业论文质量监控系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # 数据库配置
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "root"
    DB_NAME: str = "thesis_monitor"

    # JWT 配置
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production-please-change-this-key"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24小时

    # 上传配置
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 52428800  # 50MB

    # 异常检测配置
    ANOMALY_IQR_THRESHOLD: float = 1.5
    ANOMALY_ISOLATION_FOREST_CONTAMINATION: float = 0.1

    @property
    def DATABASE_URL(self) -> str:
        """构造数据库连接URL"""
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
