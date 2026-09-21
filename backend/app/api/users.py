"""
用户路由
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.response import success_response, page_response, ResponseModel, PageResult
from app.core.security import get_current_user, require_admin
from app.models.user import User
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserUpdatePassword,
    UserResponse,
)
from app.schemas.common import PaginationParams, IdResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/api/users", tags=["用户管理"])


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    """获取用户服务实例"""
    return UserService(db)


@router.get("", response_model=ResponseModel[PageResult[UserResponse]])
def list_users(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页大小"),
    keyword: Optional[str] = Query("", description="搜索关键词"),
    sort_by: Optional[str] = Query("id", description="排序字段"),
    sort_order: Optional[str] = Query("desc", description="排序方式: asc/desc"),
    role: Optional[str] = Query(None, description="按角色过滤"),
    current_user: User = Depends(require_admin),
    user_service: UserService = Depends(get_user_service),
):
    """
    获取用户列表（分页）

    - 需要管理员权限
    - 支持关键词搜索（用户名、真实姓名、邮箱、学号、工号）
    - 支持按角色过滤
    - 支持排序
    """
    pagination = PaginationParams(
        page=page,
        page_size=page_size,
        keyword=keyword,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    items, total = user_service.list_users(pagination, role=role)
    return page_response(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        message="查询成功",
    )


@router.get("/{user_id}", response_model=ResponseModel[UserResponse])
def get_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    user_service: UserService = Depends(get_user_service),
):
    """
    获取用户详情

    - 需要管理员权限
    """
    user = user_service.get_user(user_id)
    return success_response(data=user, message="查询成功")


@router.post("", response_model=ResponseModel[IdResponse])
def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_admin),
    user_service: UserService = Depends(get_user_service),
):
    """
    创建用户

    - 需要管理员权限
    """
    user = user_service.create_user(user_data)
    return success_response(data=IdResponse(id=user.id), message="创建成功")


@router.put("/{user_id}", response_model=ResponseModel[UserResponse])
def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(require_admin),
    user_service: UserService = Depends(get_user_service),
):
    """
    更新用户信息

    - 需要管理员权限
    """
    user = user_service.update_user(user_id, user_data)
    return success_response(data=user, message="更新成功")


@router.delete("/{user_id}", response_model=ResponseModel)
def delete_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    user_service: UserService = Depends(get_user_service),
):
    """
    删除用户

    - 需要管理员权限
    """
    user_service.delete_user(user_id)
    return success_response(data=None, message="删除成功")


@router.put("/{user_id}/password", response_model=ResponseModel)
def change_password(
    user_id: int,
    password_data: UserUpdatePassword,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    修改用户密码

    - 用户可以修改自己的密码
    - 管理员可以修改任意用户的密码
    """
    # 非管理员只能修改自己的密码
    if current_user.role != "admin" and current_user.id != user_id:
        from app.core.exceptions import ForbiddenException
        raise ForbiddenException("无权修改他人密码")

    user_service.change_password(user_id, password_data)
    return success_response(data=None, message="密码修改成功")
