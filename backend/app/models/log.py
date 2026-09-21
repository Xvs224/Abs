"""
操作日志模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Float
from sqlalchemy.sql import func

from app.database import Base


class OperationLog(Base):
    """操作日志表"""
    __tablename__ = "operation_logs"

    id = Column(Integer, primary_key=True, index=True, comment="日志ID")
    user_id = Column(Integer, index=True, comment="用户ID")
    username = Column(String(50), default="", index=True, comment="用户名")
    role = Column(String(20), default="", comment="用户角色")

    module = Column(String(50), default="", comment="操作模块")
    operation = Column(String(50), default="", comment="操作类型: create/update/delete/login/logout")
    action = Column(String(100), default="", comment="操作动作描述")
    target = Column(String(200), default="", comment="操作目标")
    target_id = Column(Integer, comment="目标ID")

    method = Column(String(10), default="", comment="HTTP方法")
    url = Column(String(500), default="", comment="请求URL")
    ip = Column(String(50), default="", comment="IP地址")
    user_agent = Column(String(500), default="", comment="用户代理")

    params = Column(Text, default="", comment="请求参数")
    result = Column(String(20), default="", comment="操作结果: success/fail")
    error_msg = Column(String(500), default="", comment="错误信息")
    status_code = Column(Integer, default=200, comment="状态码")
    duration = Column(Float, default=0.0, comment="耗时(毫秒)")

    detail = Column(Text, default="", comment="详细信息")
    create_time = Column(DateTime, server_default=func.now(), index=True, comment="创建时间")

    def __repr__(self):
        return f"<OperationLog(id={self.id}, user='{self.username}', action='{self.action}')>"
