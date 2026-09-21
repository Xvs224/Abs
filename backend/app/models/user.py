"""
用户模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.sql import func

from app.database import Base


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, comment="用户ID")
    username = Column(String(50), unique=True, nullable=False, index=True, comment="用户名")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    real_name = Column(String(50), nullable=False, comment="真实姓名")
    role = Column(String(20), nullable=False, comment="角色: student/teacher/admin")
    email = Column(String(100), default="", comment="邮箱")
    phone = Column(String(20), default="", comment="手机号")
    department = Column(String(100), default="", comment="所属院系/部门")
    student_no = Column(String(50), default="", comment="学号（学生角色）")
    teacher_no = Column(String(50), default="", comment="工号（教师角色）")
    grade = Column(String(20), default="", comment="年级（学生角色）")
    major = Column(String(100), default="", comment="专业")
    avatar = Column(String(255), default="", comment="头像")
    status = Column(Integer, default=1, comment="状态: 1=正常, 0=禁用")
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"
