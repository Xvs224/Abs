"""
中期检查模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class MidtermCheck(Base):
    """中期检查表"""
    __tablename__ = "midterm_checks"

    id = Column(Integer, primary_key=True, index=True, comment="检查ID")
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False, unique=True, index=True, comment="选题ID")
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="学生ID")
    teacher_id = Column(Integer, ForeignKey("users.id"), index=True, comment="指导教师ID")

    # 中期报告内容
    progress_description = Column(Text, default="", comment="进度描述")
    completed_work = Column(Text, default="", comment="已完成工作")
    remaining_work = Column(Text, default="", comment="剩余工作")
    progress_percentage = Column(Float, default=0.0, comment="进度百分比")
    existing_problems = Column(Text, default="", comment="存在的问题")
    next_plan = Column(Text, default="", comment="下一步计划")

    file_path = Column(String(255), default="", comment="中期检查表文件路径")
    file_name = Column(String(255), default="", comment="中期检查表文件名")
    file_id = Column(Integer, ForeignKey("uploaded_files.id"), comment="中期检查表文件ID")

    # 演示文稿（PPT）
    ppt_file_id = Column(Integer, ForeignKey("uploaded_files.id"), comment="PPT文件ID")
    ppt_file_path = Column(String(255), default="", comment="PPT文件路径")
    ppt_file_name = Column(String(255), default="", comment="PPT文件名")

    # 检查结果
    stage = Column(String(20), default="form", comment="当前阶段: form中期检查表/ppt演示文稿")
    teacher_guidance = Column(Text, default="", comment="教师指导意见（阶段1）")
    guidance_time = Column(DateTime, comment="指导时间")
    teacher_score = Column(Float, default=0.0, comment="指导教师评分")
    teacher_opinion = Column(Text, default="", comment="指导教师评审意见（最终）")
    check_group_score = Column(Float, default=0.0, comment="检查小组评分")
    check_group_opinion = Column(Text, default="", comment="检查小组意见")
    final_score = Column(Float, default=0.0, comment="最终成绩")

    status = Column(String(20), default="draft", comment="状态: draft草稿/form_submitted待指导/guided已指导/ppt_submitted待评审/passed通过/failed未通过/rectifying整改中/rectified已整改")
    submit_time = Column(DateTime, comment="提交时间")
    check_time = Column(DateTime, comment="检查时间")
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关联关系
    topic = relationship("Topic", backref="midterm_check")
    student = relationship("User", foreign_keys=[student_id])
    teacher = relationship("User", foreign_keys=[teacher_id])
    rectifications = relationship("Rectification", back_populates="midterm_check", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<MidtermCheck(id={self.id}, topic_id={self.topic_id}, status='{self.status}')>"


class Rectification(Base):
    """问题整改表"""
    __tablename__ = "rectifications"

    id = Column(Integer, primary_key=True, index=True, comment="整改ID")
    midterm_id = Column(Integer, ForeignKey("midterm_checks.id"), nullable=False, index=True, comment="中期检查ID")
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False, index=True, comment="选题ID")

    problem_description = Column(Text, default="", comment="问题描述")
    requirement = Column(Text, default="", comment="整改要求")
    deadline = Column(Date, comment="整改期限")

    rectification_content = Column(Text, default="", comment="整改内容")
    rectification_file_path = Column(String(255), default="", comment="整改材料文件路径")
    rectification_file_name = Column(String(255), default="", comment="整改材料文件名")
    submit_time = Column(DateTime, comment="整改提交时间")

    reviewer_id = Column(Integer, ForeignKey("users.id"), comment="复检人ID")
    review_opinion = Column(Text, default="", comment="复检意见")
    review_result = Column(String(20), default="", comment="复检结果: passed通过/failed不通过")
    review_time = Column(DateTime, comment="复检时间")

    status = Column(String(20), default="pending", comment="状态: pending待整改/submitted待复检/passed通过/failed不通过")
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关联关系
    midterm_check = relationship("MidtermCheck", back_populates="rectifications")
    topic = relationship("Topic", backref="rectifications")
    reviewer = relationship("User", foreign_keys=[reviewer_id])

    def __repr__(self):
        return f"<Rectification(id={self.id}, midterm_id={self.midterm_id}, status='{self.status}')>"
