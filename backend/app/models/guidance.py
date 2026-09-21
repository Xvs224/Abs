"""
指导计划与指导记录模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class GuidancePlan(Base):
    """指导计划表"""
    __tablename__ = "guidance_plans"

    id = Column(Integer, primary_key=True, index=True, comment="计划ID")
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False, index=True, comment="选题ID")
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="指导教师ID")
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="学生ID")

    plan_name = Column(String(200), default="", comment="计划名称")
    total_times = Column(Integer, default=12, comment="预计指导总次数")
    frequency = Column(String(50), default="每周1次", comment="指导频率")
    plan_content = Column(Text, default="", comment="计划内容概述")
    start_date = Column(Date, comment="计划开始日期")
    end_date = Column(Date, comment="计划结束日期")

    status = Column(String(20), default="active", comment="状态: active进行中/completed已完成/paused暂停")
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关联关系
    topic = relationship("Topic", backref="guidance_plans")
    teacher = relationship("User", foreign_keys=[teacher_id])
    student = relationship("User", foreign_keys=[student_id])
    records = relationship("GuidanceRecord", back_populates="plan", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<GuidancePlan(id={self.id}, topic_id={self.topic_id})>"


class GuidanceRecord(Base):
    """指导记录表"""
    __tablename__ = "guidance_records"

    id = Column(Integer, primary_key=True, index=True, comment="记录ID")
    plan_id = Column(Integer, ForeignKey("guidance_plans.id"), nullable=False, index=True, comment="计划ID")
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False, index=True, comment="选题ID")
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="指导教师ID")
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="学生ID")

    record_type = Column(String(20), default="regular", comment="指导类型: regular常规/urgent紧急/other其他")
    method = Column(String(20), default="online", comment="指导方式: online线上/offline线下/meeting会议")
    location = Column(String(100), default="", comment="指导地点")
    duration = Column(Integer, default=0, comment="指导时长（分钟）")

    content = Column(Text, default="", comment="指导内容")
    teacher_opinion = Column(Text, default="", comment="教师意见")
    student_task = Column(Text, default="", comment="学生任务")
    next_guidance_date = Column(Date, comment="下次指导时间")

    attachment_path = Column(String(255), default="", comment="附件路径")
    attachment_name = Column(String(255), default="", comment="附件名称")

    record_time = Column(DateTime, comment="指导时间")
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关联关系
    plan = relationship("GuidancePlan", back_populates="records")
    topic = relationship("Topic", backref="guidance_records")
    teacher = relationship("User", foreign_keys=[teacher_id])
    student = relationship("User", foreign_keys=[student_id])

    def __repr__(self):
        return f"<GuidanceRecord(id={self.id}, plan_id={self.plan_id})>"
