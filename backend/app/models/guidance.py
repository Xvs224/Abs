"""
过程指导记录模型
教师与学生在论文写作全过程中的指导互动记录
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class GuidanceRecord(Base):
    """过程指导记录表"""
    __tablename__ = "guidance_records"

    id = Column(Integer, primary_key=True, index=True, comment="指导记录ID")
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False, index=True, comment="选题ID")
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="学生ID")
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="指导教师ID")

    # 发起人：teacher 教师发起指导 / student 学生发起提问
    initiator = Column(String(20), default="teacher", comment="发起人: teacher/student")

    guidance_type = Column(
        String(20), default="meeting",
        comment="指导方式: meeting面对面/written书面/online线上/phone电话/other其他"
    )
    guidance_time = Column(DateTime, comment="指导时间")

    title = Column(String(200), default="", comment="指导主题")
    content = Column(Text, default="", comment="指导内容/提问内容")

    # 学生回复（教师发起指导时，学生回复）
    student_response = Column(Text, default="", comment="学生回复内容")
    student_reply_time = Column(DateTime, comment="学生回复时间")

    # 教师回复（学生发起提问时，教师回复）
    teacher_response = Column(Text, default="", comment="教师回复内容")
    teacher_reply_time = Column(DateTime, comment="教师回复时间")

    # 状态
    status = Column(String(20), default="pending", comment="状态: pending待回复/replied已回复/closed已关闭")

    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关联关系
    topic = relationship("Topic", backref="guidance_records")
    student = relationship("User", foreign_keys=[student_id])
    teacher = relationship("User", foreign_keys=[teacher_id])

    def __repr__(self):
        return f"<GuidanceRecord(id={self.id}, topic_id={self.topic_id}, type='{self.guidance_type}')>"
