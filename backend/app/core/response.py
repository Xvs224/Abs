"""
统一响应格式
"""
from typing import Generic, TypeVar, Optional, List
from pydantic import BaseModel, Field

T = TypeVar("T")


class ResponseModel(BaseModel, Generic[T]):
    """统一响应模型"""
    code: int = Field(default=200, description="状态码，200表示成功")
    message: str = Field(default="success", description="响应消息")
    data: Optional[T] = Field(default=None, description="响应数据")


class PageResult(BaseModel, Generic[T]):
    """分页结果模型"""
    total: int = Field(description="总记录数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页大小")
    items: List[T] = Field(description="数据列表")


def success_response(data: T = None, message: str = "操作成功") -> ResponseModel[T]:
    """成功响应"""
    return ResponseModel(code=200, message=message, data=data)


def error_response(code: int = 400, message: str = "操作失败") -> ResponseModel:
    """错误响应"""
    return ResponseModel(code=code, message=message, data=None)


def page_response(items: List[T], total: int, page: int, page_size: int,
                  message: str = "查询成功") -> ResponseModel[PageResult[T]]:
    """分页响应"""
    result = PageResult(
        total=total,
        page=page,
        page_size=page_size,
        items=items
    )
    return ResponseModel(code=200, message=message, data=result)


# 常用错误码
ERROR_CODES = {
    400: "请求参数错误",
    401: "未授权，请先登录",
    403: "权限不足，禁止访问",
    404: "资源不存在",
    409: "资源冲突",
    500: "服务器内部错误",
}
