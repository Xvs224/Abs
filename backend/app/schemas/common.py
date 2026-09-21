"""
通用 Schema
"""
from typing import Optional, Generic, TypeVar, List
from pydantic import BaseModel, Field, field_validator

T = TypeVar("T")


class PaginationParams(BaseModel):
    """分页查询参数"""
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=10, ge=1, le=100, description="每页大小")
    keyword: Optional[str] = Field(default="", description="搜索关键词")
    sort_by: Optional[str] = Field(default="id", description="排序字段")
    sort_order: Optional[str] = Field(default="desc", description="排序方式: asc/desc")

    @field_validator("sort_order")
    @classmethod
    def validate_sort_order(cls, v):
        if v and v.lower() not in ["asc", "desc"]:
            return "desc"
        return v.lower() if v else "desc"


class IdResponse(BaseModel):
    """ID 响应"""
    id: int


class SuccessResponse(BaseModel):
    """成功响应"""
    success: bool = True
    message: str = "操作成功"


class StatItem(BaseModel):
    """统计项"""
    label: str
    value: int
    percentage: Optional[float] = None


class TrendItem(BaseModel):
    """趋势项"""
    date: str
    count: int
