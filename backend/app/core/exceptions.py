"""
全局异常处理 — 返回真实 HTTP 状态码，body 保留业务 code 供前端细分
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import logging

logger = logging.getLogger(__name__)


class BusinessException(Exception):
    """业务异常基类"""

    def __init__(self, code: int = 400, message: str = "业务异常"):
        self.code = code
        self.message = message
        super().__init__(message)


class UnauthorizedException(BusinessException):
    """未授权异常 — HTTP 401"""

    def __init__(self, message: str = "未授权，请先登录"):
        super().__init__(code=401, message=message)


class ForbiddenException(BusinessException):
    """权限不足异常 — HTTP 403"""

    def __init__(self, message: str = "权限不足，禁止访问"):
        super().__init__(code=403, message=message)


class NotFoundException(BusinessException):
    """资源不存在异常 — HTTP 404"""

    def __init__(self, message: str = "资源不存在"):
        super().__init__(code=404, message=message)


class ConflictException(BusinessException):
    """资源冲突异常 — HTTP 409"""

    def __init__(self, message: str = "资源冲突"):
        super().__init__(code=409, message=message)


def _http_status_from_code(code: int) -> int:
    """将业务 code 映射为 HTTP 状态码"""
    if code in (401, 403, 404, 409, 422, 429):
        return code
    if code >= 500:
        return 500
    return 400


def register_exception_handlers(app):
    """注册全局异常处理器"""

    @app.exception_handler(BusinessException)
    async def business_exception_handler(request: Request, exc: BusinessException):
        """业务异常处理 — 返回真实 HTTP 状态码"""
        http_status = _http_status_from_code(exc.code)
        return JSONResponse(
            status_code=http_status,
            content={"code": exc.code, "message": exc.message, "data": None}
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """请求参数验证异常处理 — HTTP 422"""
        errors = []
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            errors.append(f"{field}: {error['msg']}")
        message = "参数验证失败: " + "; ".join(errors)
        return JSONResponse(
            status_code=422,
            content={"code": 422, "message": message, "data": None}
        )

    @app.exception_handler(IntegrityError)
    async def integrity_exception_handler(request: Request, exc: IntegrityError):
        """数据库完整性异常（如唯一约束冲突）— HTTP 409"""
        logger.warning(f"数据库完整性异常: {str(exc)}")
        return JSONResponse(
            status_code=409,
            content={"code": 409, "message": "数据冲突，可能存在重复记录", "data": None}
        )

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
        """数据库异常处理 — HTTP 500"""
        logger.error(f"数据库异常: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"code": 500, "message": "数据库操作异常", "data": None}
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """通用异常处理 — HTTP 500"""
        logger.error(f"未处理的异常: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"code": 500, "message": "服务器内部错误", "data": None}
        )
