"""
选题模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Topic(Base):
    """选题表"""
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, index=True, comment="选题ID")
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="学生ID")
    teacher_id = Column(Integer, ForeignKey("users.id"), index=True, comment="指导教师ID")
    title = Column(String(200), nullable=False, comment="题目名称")
    direction = Column(String(100), default="", comment="研究方向")
    background = Column(Text, default="", comment="研究背景")
    significance = Column(Text, default="", comment="研究意义")
    keywords = Column(String(200), default="", comment="关键词，逗号分隔")
    source = Column(String(50), default="", comment="题目来源")
    difficulty = Column(String(20), default="medium", comment="难度: easy/medium/hard")
    workload = Column(String(20), default="medium", comment="工作量: light/medium/heavy")
    status = Column(String(20), default="pending", comment="状态: pending待审核/approved已确认/rejected已拒绝/withdrawn已撤回")
    reject_reason = Column(String(500), default="", comment="拒绝原因")
    review_time = Column(DateTime, comment="审核时间")
    reviewer_id = Column(Integer, ForeignKey("users.id"), comment="审核人ID")
    submit_time = Column(DateTime, server_default=func.now(), comment="提交时间")
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关联关系
    student = relationship("User", foreign_keys=[student_id], backref="student_topics")
    teacher = relationship("User", foreign_keys=[teacher_id], backref="teacher_topics")
    reviewer = relationship("User", foreign_keys=[reviewer_id])

    def __repr__(self):
        return f"<Topic(id={self.id}, title='{self.title}', status='{self.status}')>"
