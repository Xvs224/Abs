"""
成果归档模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Archive(Base):
    """成果归档表"""
    __tablename__ = "archives"

    id = Column(Integer, primary_key=True, index=True, comment="归档ID")
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False, unique=True, index=True, comment="选题ID")
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="学生ID")
    teacher_id = Column(Integer, ForeignKey("users.id"), index=True, comment="指导教师ID")

    final_version_id = Column(Integer, ForeignKey("thesis_versions.id"), comment="最终论文版本ID")

    # 归档材料清单
    thesis_file = Column(String(255), default="", comment="最终论文")
    proposal_file = Column(String(255), default="", comment="开题报告")
    midterm_file = Column(String(255), default="", comment="中期报告")
    review_file = Column(String(255), default="", comment="评阅意见")
    defense_file = Column(String(255), default="", comment="答辩记录")
    other_materials = Column(Text, default="", comment="其他材料（JSON格式）")

    final_score = Column(Integer, default=0, comment="最终成绩（总分）")
    final_grade = Column(String(10), default="", comment="最终等级")

    archive_no = Column(String(50), default="", comment="档案编号")
    archive_location = Column(String(200), default="", comment="归档位置")
    archivist_id = Column(Integer, ForeignKey("users.id"), comment="归档人ID")

    status = Column(String(20), default="pending", comment="状态: pending待归档/archived已归档/returned已退回")
    return_reason = Column(String(500), default="", comment="退回原因")

    archive_time = Column(DateTime, comment="归档时间")
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关联关系
    topic = relationship("Topic", backref="archive")
    student = relationship("User", foreign_keys=[student_id])
    teacher = relationship("User", foreign_keys=[teacher_id])
    final_version = relationship("ThesisVersion", foreign_keys=[final_version_id])
    archivist = relationship("User", foreign_keys=[archivist_id])

    def __repr__(self):
        return f"<Archive(id={self.id}, topic_id={self.topic_id}, status='{self.status}')>"
