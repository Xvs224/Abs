"""
操作日志 API
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, desc, asc
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.core.response import success_response, page_response
from app.core.security import require_admin
from app.models.log import OperationLog
from app.schemas.log import OperationLogResponse, OperationLogListResponse
from app.schemas.common import PaginationParams

router = APIRouter(prefix="/api/logs", tags=["操作日志"])


@router.get("")
async def get_log_list(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=10, ge=1, le=100, description="每页大小"),
    keyword: Optional[str] = Query(default="", description="搜索关键词"),
    module: Optional[str] = Query(default="", description="模块"),
    operation: Optional[str] = Query(default="", description="操作类型"),
    username: Optional[str] = Query(default="", description="用户名"),
    result: Optional[str] = Query(default="", description="操作结果"),
    start_time: Optional[str] = Query(default="", description="开始时间"),
    end_time: Optional[str] = Query(default="", description="结束时间"),
    sort_by: str = Query(default="id", description="排序字段"),
    sort_order: str = Query(default="desc", description="排序方式"),
    current_user=Depends(require_admin),
    db: Session = Depends(get_db)
):
    """获取操作日志列表（分页）"""
    query = db.query(OperationLog)

    # 关键词搜索
    if keyword:
        query = query.filter(
            or_(
                OperationLog.action.like(f"%{keyword}%"),
                OperationLog.target.like(f"%{keyword}%"),
                OperationLog.detail.like(f"%{keyword}%"),
            )
        )

    # 模块过滤
    if module:
        query = query.filter(OperationLog.module == module)

    # 操作类型过滤
    if operation:
        query = query.filter(OperationLog.operation == operation)

    # 用户名过滤
    if username:
        query = query.filter(OperationLog.username.like(f"%{username}%"))

    # 结果过滤
    if result:
        query = query.filter(OperationLog.result == result)

    # 时间范围过滤
    if start_time:
        query = query.filter(OperationLog.create_time >= start_time)
    if end_time:
        query = query.filter(OperationLog.create_time <= end_time)

    # 总数
    total = query.count()

    # 排序
    sort_field = getattr(OperationLog, sort_by, OperationLog.id)
    if sort_order.lower() == "asc":
        query = query.order_by(asc(sort_field))
    else:
        query = query.order_by(desc(sort_field))

    # 分页
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return page_response(
        items=[OperationLogResponse.model_validate(item).model_dump() for item in items],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{log_id}")
async def get_log_detail(
    log_id: int,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db)
):
    """获取操作日志详情"""
    log = db.query(OperationLog).filter(OperationLog.id == log_id).first()
    if not log:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("日志不存在")

    return success_response(OperationLogResponse.model_validate(log).model_dump())


@router.get("/modules/list")
async def get_module_list(
    current_user=Depends(require_admin),
    db: Session = Depends(get_db)
):
    """获取模块列表（用于筛选）"""
    results = db.query(OperationLog.module).distinct().all()
    modules = [r.module for r in results if r.module]
    return success_response(modules)
