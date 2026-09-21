"""
全局异常处理
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
import logging

from app.core.response import error_response

logger = logging.getLogger(__name__)


class BusinessException(Exception):
    """业务异常基类"""

    def __init__(self, code: int = 400, message: str = "业务异常"):
        self.code = code
        self.message = message
        super().__init__(message)


class UnauthorizedException(BusinessException):
    """未授权异常"""

    def __init__(self, message: str = "未授权，请先登录"):
        super().__init__(code=401, message=message)


class ForbiddenException(BusinessException):
    """权限不足异常"""

    def __init__(self, message: str = "权限不足，禁止访问"):
        super().__init__(code=403, message=message)


class NotFoundException(BusinessException):
    """资源不存在异常"""

    def __init__(self, message: str = "资源不存在"):
        super().__init__(code=404, message=message)


class ConflictException(BusinessException):
    """资源冲突异常"""

    def __init__(self, message: str = "资源冲突"):
        super().__init__(code=409, message=message)


def register_exception_handlers(app):
    """注册全局异常处理器"""

    @app.exception_handler(BusinessException)
    async def business_exception_handler(request: Request, exc: BusinessException):
        """业务异常处理"""
        return JSONResponse(
            status_code=200,
            content={"code": exc.code, "message": exc.message, "data": None}
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """请求参数验证异常处理"""
        errors = []
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            errors.append(f"{field}: {error['msg']}")
        message = "参数验证失败: " + "; ".join(errors)
        return JSONResponse(
            status_code=200,
            content={"code": 400, "message": message, "data": None}
        )

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
        """数据库异常处理"""
        logger.error(f"数据库异常: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=200,
            content={"code": 500, "message": "数据库操作异常", "data": None}
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """通用异常处理"""
        logger.error(f"未处理的异常: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=200,
            content={"code": 500, "message": "服务器内部错误", "data": None}
        )
