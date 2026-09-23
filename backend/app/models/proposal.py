"""
开题报告模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Proposal(Base):
    """开题报告表"""
    __tablename__ = "proposals"

    id = Column(Integer, primary_key=True, index=True, comment="开题ID")
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False, unique=True, index=True, comment="选题ID")
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="学生ID")
    teacher_id = Column(Integer, ForeignKey("users.id"), index=True, comment="指导教师ID")

    # 开题报告内容
    research_content = Column(Text, default="", comment="研究内容")
    research_method = Column(Text, default="", comment="研究方法")
    technical_route = Column(Text, default="", comment="技术路线")
    expected_results = Column(Text, default="", comment="预期成果")
    schedule_plan = Column(Text, default="", comment="进度安排")
    references_count = Column(Integer, default=0, comment="参考文献数量")
    references_list = Column(Text, default="", comment="参考文献列表")
    word_count = Column(Integer, default=0, comment="字数")

    # 附件
    file_id = Column(Integer, ForeignKey("uploaded_files.id"), comment="上传文件ID")
    file_path = Column(String(255), default="", comment="开题报告文件路径")
    file_name = Column(String(255), default="", comment="文件名")

    # 审核状态
    status = Column(String(20), default="draft", comment="状态: draft草稿/submitted待审核/approved通过/rejected驳回")
    review_opinion = Column(Text, default="", comment="审核意见")
    review_time = Column(DateTime, comment="审核时间")
    reviewer_id = Column(Integer, ForeignKey("users.id"), comment="审核人ID")

    submit_time = Column(DateTime, comment="提交时间")
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关联关系
    topic = relationship("Topic", backref="proposal")
    student = relationship("User", foreign_keys=[student_id])
    teacher = relationship("User", foreign_keys=[teacher_id])
    reviewer = relationship("User", foreign_keys=[reviewer_id])

    def __repr__(self):
        return f"<Proposal(id={self.id}, topic_id={self.topic_id}, status='{self.status}')>"
