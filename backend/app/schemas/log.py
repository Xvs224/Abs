"""
操作日志相关 Schema
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class OperationLogResponse(BaseModel):
    """操作日志响应"""
    id: int
    user_id: Optional[int] = None
    username: str = ""
    role: str = ""
    module: str = ""
    operation: str = ""
    action: str = ""
    target: str = ""
    target_id: Optional[int] = None
    method: str = ""
    url: str = ""
    ip: str = ""
    result: str = ""
    status_code: int = 200
    duration: float = 0.0
    detail: str = ""
    create_time: Optional[datetime] = None

    class Config:
        from_attributes = True


class OperationLogListResponse(BaseModel):
    """操作日志列表响应"""
    total: int
    items: List[OperationLogResponse]
