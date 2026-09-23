"""
限流器实例 — 独立模块避免循环导入
"""
import warnings
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=[settings.RATE_LIMIT_DEFAULT],
        config_filename="",
    )
