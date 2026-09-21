"""
论文版本与格式检测模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class ThesisVersion(Base):
    """论文版本表"""
    __tablename__ = "thesis_versions"

    id = Column(Integer, primary_key=True, index=True, comment="版本ID")
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False, index=True, comment="选题ID")
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="学生ID")

    version_num = Column(Integer, default=1, comment="版本号")
    version_name = Column(String(200), default="", comment="版本名称")
    change_log = Column(Text, default="", comment="修改说明")

    file_path = Column(String(255), nullable=False, comment="文件路径")
    file_name = Column(String(255), nullable=False, comment="文件名")
    file_size = Column(Integer, default=0, comment="文件大小（字节）")
    file_type = Column(String(50), default="", comment="文件类型")

    word_count = Column(Integer, default=0, comment="字数")
    page_count = Column(Integer, default=0, comment="页数")
    chapter_count = Column(Integer, default=0, comment="章节数")
    reference_count = Column(Integer, default=0, comment="参考文献数")

    format_check_status = Column(String(20), default="pending", comment="格式检测状态: pending待检测/done已完成/failed检测失败")
    format_score = Column(Float, default=0.0, comment="格式规范得分")

    submit_time = Column(DateTime, server_default=func.now(), comment="提交时间")
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关联关系
    topic = relationship("Topic", backref="thesis_versions")
    student = relationship("User", foreign_keys=[student_id])
    format_checks = relationship("FormatCheck", back_populates="version", cascade="all, delete-orphan")

    __table_args__ = {"comment": "论文版本表"}

    def __repr__(self):
        return f"<ThesisVersion(id={self.id}, topic_id={self.topic_id}, v{self.version_num})>"


class FormatCheck(Base):
    """格式规范检测表"""
    __tablename__ = "format_checks"

    id = Column(Integer, primary_key=True, index=True, comment="检测ID")
    version_id = Column(Integer, ForeignKey("thesis_versions.id"), nullable=False, index=True, comment="版本ID")
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False, index=True, comment="选题ID")

    check_items = Column(JSON, default=dict, comment="检测项详细结果(JSON)")
    # check_items 结构示例:
    # {
    #   "title_format": {"passed": true, "message": "标题格式正确", "score": 10},
    #   "abstract_format": {"passed": false, "message": "摘要字数不足", "score": 5},
    #   "references_format": {"passed": true, "message": "参考文献格式正确", "score": 10},
    #   ...
    # }

    total_score = Column(Float, default=0.0, comment="总得分")
    max_score = Column(Float, default=100.0, comment="满分")
    passed_count = Column(Integer, default=0, comment="通过项数")
    failed_count = Column(Integer, default=0, comment="未通过项数")
    total_items = Column(Integer, default=0, comment="总检测项数")

    overall_result = Column(String(20), default="", comment="总体结果: pass通过/fail不通过")
    problems_summary = Column(Text, default="", comment="问题汇总")
    suggestions = Column(Text, default="", comment="修改建议")

    check_time = Column(DateTime, server_default=func.now(), comment="检测时间")
    checker = Column(String(50), default="system", comment="检测者: system系统/人工用户名")

    # 关联关系
    version = relationship("ThesisVersion", back_populates="format_checks")
    topic = relationship("Topic", backref="format_checks")

    def __repr__(self):
        return f"<FormatCheck(id={self.id}, version_id={self.version_id}, score={self.total_score})>"
