"""
异常检测模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class AnomalyRecord(Base):
    """异常记录表"""
    __tablename__ = "anomaly_records"

    id = Column(Integer, primary_key=True, index=True, comment="异常记录ID")

    target_type = Column(String(50), nullable=False, index=True, comment="检测对象类型: topic/proposal/guidance/midterm/thesis/review/student")
    target_id = Column(Integer, nullable=False, index=True, comment="检测对象ID")
    student_id = Column(Integer, ForeignKey("users.id"), index=True, comment="关联学生ID")
    topic_id = Column(Integer, ForeignKey("topics.id"), index=True, comment="关联选题ID")

    # 检测信息
    detection_type = Column(String(50), default="", comment="检测类型: iqr/isolation_forest/combined")
    feature_name = Column(String(100), default="", comment="异常特征名称")
    feature_value = Column(Float, default=0.0, comment="特征值")
    feature_data = Column(JSON, default=dict, comment="完整特征数据(JSON)")

    anomaly_score = Column(Float, default=0.0, comment="异常分数")
    severity_level = Column(String(20), default="L1", comment="严重等级: L1提示/L2警告/L3告警")
    confidence = Column(Float, default=0.0, comment="置信度")

    description = Column(String(500), default="", comment="异常描述")
    suggestion = Column(String(500), default="", comment="处理建议")

    # 复核状态
    review_status = Column(String(20), default="pending", comment="复核状态: pending待复核/confirmed确认异常/false_positive误报/ignored忽略")
    reviewer_id = Column(Integer, ForeignKey("users.id"), comment="复核人ID")
    review_time = Column(DateTime, comment="复核时间")
    review_opinion = Column(Text, default="", comment="复核意见")
    correction_result = Column(String(20), default="", comment="纠正结果")

    detection_time = Column(DateTime, server_default=func.now(), comment="检测时间")
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关联关系
    student = relationship("User", foreign_keys=[student_id])
    topic = relationship("Topic", foreign_keys=[topic_id])
    reviewer = relationship("User", foreign_keys=[reviewer_id])
    reviews = relationship("AnomalyReview", back_populates="anomaly_record", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<AnomalyRecord(id={self.id}, target='{self.target_type}', level='{self.severity_level}')>"


class AnomalyReview(Base):
    """异常复核记录表"""
    __tablename__ = "anomaly_reviews"

    id = Column(Integer, primary_key=True, index=True, comment="复核记录ID")
    anomaly_id = Column(Integer, ForeignKey("anomaly_records.id"), nullable=False, index=True, comment="异常记录ID")
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="复核人ID")

    result = Column(String(20), default="", comment="复核结果: confirmed确认异常/false_positive误报/ignored忽略")
    opinion = Column(Text, default="", comment="复核意见")
    correction = Column(Text, default="", comment="纠正措施")
    correction_result = Column(String(20), default="", comment="纠正结果: resolved已解决/unresolved未解决")

    review_time = Column(DateTime, server_default=func.now(), comment="复核时间")
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")

    # 关联关系
    anomaly_record = relationship("AnomalyRecord", back_populates="reviews")
    reviewer = relationship("User", foreign_keys=[reviewer_id])

    def __repr__(self):
        return f"<AnomalyReview(id={self.id}, anomaly_id={self.anomaly_id}, result='{self.result}')>"
