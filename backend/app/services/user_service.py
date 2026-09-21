"""
用户服务
"""
from typing import List, Optional, Tuple

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.core.exceptions import NotFoundException, ConflictException, BusinessException
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserUpdatePassword, UserResponse
from app.schemas.common import PaginationParams


class UserService:
    """用户服务类"""

    def __init__(self, db: Session):
        self.db = db

    def create_user(self, user_data: UserCreate) -> User:
        """
        创建用户

        :param user_data: 创建用户请求数据
        :return: 创建的用户对象
        :raises ConflictException: 用户名已存在
        """
        # 检查用户名是否已存在
        existing_user = (
            self.db.query(User)
            .filter(User.username == user_data.username)
            .first()
        )
        if existing_user:
            raise ConflictException("用户名已存在")

        # 创建用户
        user = User(
            username=user_data.username,
            password_hash=hash_password(user_data.password),
            real_name=user_data.real_name,
            role=user_data.role,
            email=user_data.email or "",
            phone=user_data.phone or "",
            department=user_data.department or "",
            student_no=user_data.student_no or "",
            teacher_no=user_data.teacher_no or "",
            grade=user_data.grade or "",
            major=user_data.major or "",
            status=1,
        )

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        return user

    def get_user(self, user_id: int) -> User:
        """
        根据 ID 获取用户

        :param user_id: 用户 ID
        :return: 用户对象
        :raises NotFoundException: 用户不存在
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundException("用户不存在")
        return user

    def update_user(self, user_id: int, user_data: UserUpdate) -> User:
        """
        更新用户信息

        :param user_id: 用户 ID
        :param user_data: 更新用户请求数据
        :return: 更新后的用户对象
        :raises NotFoundException: 用户不存在
        """
        user = self.get_user(user_id)

        # 更新字段
        update_data = user_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        self.db.commit()
        self.db.refresh(user)

        return user

    def delete_user(self, user_id: int) -> None:
        """
        删除用户

        :param user_id: 用户 ID
        :raises NotFoundException: 用户不存在
        """
        user = self.get_user(user_id)
        self.db.delete(user)
        self.db.commit()

    def list_users(
        self, pagination: PaginationParams, role: Optional[str] = None
    ) -> Tuple[List[User], int]:
        """
        分页查询用户列表

        :param pagination: 分页参数
        :param role: 按角色过滤
        :return: (用户列表, 总记录数)
        """
        query = self.db.query(User)

        # 关键词搜索
        if pagination.keyword:
            keyword = f"%{pagination.keyword}%"
            query = query.filter(
                or_(
                    User.username.like(keyword),
                    User.real_name.like(keyword),
                    User.email.like(keyword),
                    User.student_no.like(keyword),
                    User.teacher_no.like(keyword),
                )
            )

        # 角色过滤
        if role:
            query = query.filter(User.role == role)

        # 统计总数
        total = query.count()

        # 排序
        sort_field = getattr(User, pagination.sort_by, User.id)
        if pagination.sort_order == "asc":
            query = query.order_by(sort_field.asc())
        else:
            query = query.order_by(sort_field.desc())

        # 分页
        offset = (pagination.page - 1) * pagination.page_size
        items = query.offset(offset).limit(pagination.page_size).all()

        return items, total

    def change_password(
        self, user_id: int, password_data: UserUpdatePassword
    ) -> None:
        """
        修改用户密码

        :param user_id: 用户 ID
        :param password_data: 密码修改请求数据
        :raises NotFoundException: 用户不存在
        :raises BusinessException: 旧密码错误
        """
        user = self.get_user(user_id)

        # 验证旧密码
        if not verify_password(password_data.old_password, user.password_hash):
            raise BusinessException(code=400, message="旧密码错误")

        # 更新密码
        user.password_hash = hash_password(password_data.new_password)
        self.db.commit()

    def reset_password(self, user_id: int, new_password: str) -> None:
        """
        管理员重置用户密码

        :param user_id: 用户 ID
        :param new_password: 新密码
        :raises NotFoundException: 用户不存在
        """
        user = self.get_user(user_id)
        user.password_hash = hash_password(new_password)
        self.db.commit()
