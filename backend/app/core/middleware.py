"""
操作日志中间件
"""
import time
import json
from datetime import datetime
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging

from app.database import SessionLocal
from app.models.log import OperationLog

logger = logging.getLogger(__name__)

# 不需要记录日志的路径
EXCLUDE_PATHS = [
    "/docs",
    "/openapi.json",
    "/redoc",
    "/static",
    "/favicon.ico",
    "/api/auth/login",
]

# 需要记录的 HTTP 方法
LOG_METHODS = ["POST", "PUT", "DELETE", "PATCH"]


class OperationLogMiddleware(BaseHTTPMiddleware):
    """操作日志中间件"""

    async def dispatch(self, request: Request, call_next):
        # 跳过不需要记录的请求
        if request.method not in LOG_METHODS:
            return await call_next(request)

        path = request.url.path
        for exclude in EXCLUDE_PATHS:
            if path.startswith(exclude):
                return await call_next(request)

        # 记录请求开始时间
        start_time = time.time()

        # 尝试获取请求体（用于记录）
        request_body = ""
        try:
            body = await request.body()
            if body:
                request_body = body.decode("utf-8")[:1000]  # 限制长度
        except Exception:
            pass

        # 处理请求
        response = await call_next(request)

        # 计算耗时
        duration = round((time.time() - start_time) * 1000, 2)

        # 异步记录日志（使用独立会话）
        try:
            self._save_log(request, response, request_body, duration)
        except Exception as e:
            logger.error(f"保存操作日志失败: {e}")

        return response

    def _save_log(self, request: Request, response: Response,
                  request_body: str, duration: float):
        """保存操作日志"""
        db = SessionLocal()
        try:
            # 尝试从请求头获取用户信息
            user_id = None
            username = None
            auth_header = request.headers.get("Authorization", "")
            # 简化处理：实际应解析 JWT
            # 这里先记录基本信息，后续在依赖中补充用户信息

            client_ip = request.client.host if request.client else ""

            log_entry = OperationLog(
                user_id=user_id,
                username=username,
                operation=request.method,
                target=request.url.path,
                detail=request_body[:500] if request_body else "",
                ip=client_ip,
                status_code=response.status_code,
                duration=duration,
                create_time=datetime.now()
            )
            db.add(log_entry)
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"保存操作日志异常: {e}")
        finally:
            db.close()
