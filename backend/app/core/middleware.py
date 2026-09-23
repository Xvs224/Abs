"""
操作日志中间件 — 从 Authorization 头解码 JWT 获取用户信息
"""
import time
from datetime import datetime
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging

from app.database import SessionLocal
from app.models.log import OperationLog
from app.core.security import decode_token

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

# 模块路径映射
MODULE_MAP = {
    "/api/auth": "认证管理",
    "/api/users": "用户管理",
    "/api/topics": "选题管理",
    "/api/proposals": "开题管理",
    "/api/midterm": "中期检查",
    "/api/thesis": "论文版本",
    "/api/reviews": "评阅答辩",
    "/api/defenses": "评阅答辩",
    "/api/archives": "成果归档",
    "/api/anomaly": "异常检测",
    "/api/stats": "统计分析",
    "/api/logs": "操作日志",
    "/api/files": "文件管理",
}


def _extract_user_info(request: Request):
    """从 Authorization 请求头解析 JWT 获取用户信息"""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None, None, None

    token = auth_header[7:]
    payload = decode_token(token)
    if not payload:
        return None, None, None

    return (
        int(payload.get("sub", 0)) or None,
        payload.get("username"),
        payload.get("role"),
    )


def _infer_module(path: str) -> str:
    """根据请求路径推断业务模块"""
    for prefix, module_name in MODULE_MAP.items():
        if path.startswith(prefix):
            return module_name
    return "其他"


def _infer_operation(method: str, path: str) -> str:
    """根据 HTTP 方法和路径推断操作类型"""
    if "/login" in path:
        return "login"
    if "/logout" in path:
        return "logout"
    op_map = {"POST": "create", "PUT": "update", "PATCH": "update", "DELETE": "delete"}
    return op_map.get(method, method.lower())


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

        # 提取用户信息（P0-6 修复：从 JWT 解码）
        user_id, username, role = _extract_user_info(request)

        # 尝试获取请求体（用于记录）
        request_body = ""
        try:
            body = await request.body()
            if body:
                request_body = body.decode("utf-8")[:1000]
        except Exception:
            pass

        # 处理请求
        response = await call_next(request)

        # 计算耗时
        duration = round((time.time() - start_time) * 1000, 2)

        # 异步记录日志（使用独立会话）
        try:
            self._save_log(request, response, request_body, duration, user_id, username, role)
        except Exception as e:
            logger.error(f"保存操作日志失败: {e}")

        return response

    def _save_log(self, request: Request, response: Response,
                  request_body: str, duration: float,
                  user_id, username, role):
        """保存操作日志"""
        db = SessionLocal()
        try:
            client_ip = request.client.host if request.client else ""
            user_agent = request.headers.get("user-agent", "")[:500]
            path = request.url.path

            log_entry = OperationLog(
                user_id=user_id,
                username=username or "",
                role=role or "",
                module=_infer_module(path),
                operation=_infer_operation(request.method, path),
                action=f"{request.method} {path}",
                target=path,
                method=request.method,
                url=str(request.url),
                ip=client_ip,
                user_agent=user_agent,
                params=request_body[:500] if request_body else "",
                result="success" if response.status_code < 400 else "fail",
                status_code=response.status_code,
                duration=duration,
                detail=request_body[:500] if request_body else "",
                create_time=datetime.now()
            )
            db.add(log_entry)
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"保存操作日志异常: {e}")
        finally:
            db.close()
