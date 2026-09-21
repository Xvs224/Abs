"""
评阅与答辩模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float, Date, Time
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Review(Base):
    """评阅表"""
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True, comment="评阅ID")
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False, index=True, comment="选题ID")
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="学生ID")
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="评阅教师ID")

    review_type = Column(String(20), default="normal", comment="评阅类型: normal常规评阅/external外审")
    version_id = Column(Integer, ForeignKey("thesis_versions.id"), comment="评阅的论文版本ID")

    # 各维度评分
    topic_score = Column(Float, default=0.0, comment="选题价值")
    content_score = Column(Float, default=0.0, comment="内容质量")
    method_score = Column(Float, default=0.0, comment="研究方法")
    innovation_score = Column(Float, default=0.0, comment="创新性")
    format_score = Column(Float, default=0.0, comment="写作规范")
    total_score = Column(Float, default=0.0, comment="总分")

    opinion = Column(Text, default="", comment="评阅意见")
    suggestions = Column(Text, default="", comment="修改建议")
    result = Column(String(20), default="", comment="评阅结果: pass通过/revision需修改/reject不通过")

    review_time = Column(DateTime, comment="评阅时间")
    deadline = Column(DateTime, comment="评阅截止时间")
    status = Column(String(20), default="pending", comment="状态: pending待评阅/completed已完成")

    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关联关系
    topic = relationship("Topic", backref="reviews")
    student = relationship("User", foreign_keys=[student_id])
    reviewer = relationship("User", foreign_keys=[reviewer_id])
    version = relationship("ThesisVersion", foreign_keys=[version_id])

    def __repr__(self):
        return f"<Review(id={self.id}, topic_id={self.topic_id}, score={self.total_score})>"


class Defense(Base):
    """答辩表"""
    __tablename__ = "defenses"

    id = Column(Integer, primary_key=True, index=True, comment="答辩ID")
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False, unique=True, index=True, comment="选题ID")
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="学生ID")

    defense_date = Column(Date, comment="答辩日期")
    defense_time_start = Column(Time, comment="开始时间")
    defense_time_end = Column(Time, comment="结束时间")
    location = Column(String(200), default="", comment="答辩地点")
    defense_form = Column(String(20), default="offline", comment="答辩形式: offline线下/online线上/hybrid混合")

    # 答辩委员会
    chair_id = Column(Integer, ForeignKey("users.id"), comment="主席ID")
    committee_members = Column(String(500), default="", comment="委员会成员（ID逗号分隔）")
    secretary_id = Column(Integer, ForeignKey("users.id"), comment="秘书ID")

    # 答辩成绩
    presentation_score = Column(Float, default=0.0, comment="报告陈述")
    qa_score = Column(Float, default=0.0, comment="答辩表现")
    thesis_quality_score = Column(Float, default=0.0, comment="论文质量")
    total_score = Column(Float, default=0.0, comment="答辩总分")
    grade = Column(String(10), default="", comment="等级: excellent优秀/good良好/medium中等/pass及格/fail不及格")

    opinion = Column(Text, default="", comment="答辩意见")
    suggestions = Column(Text, default="", comment="修改建议")
    result = Column(String(20), default="", comment="答辩结果: pass通过/fail不通过/reargue二次答辩")

    # 二次答辩相关
    re_defense_date = Column(Date, comment="二次答辩日期")
    re_defense_result = Column(String(20), default="", comment="二次答辩结果")

    status = Column(String(20), default="scheduled", comment="状态: scheduled已安排/in_progress进行中/completed已完成")
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关联关系
    topic = relationship("Topic", backref="defense")
    student = relationship("User", foreign_keys=[student_id])
    chair = relationship("User", foreign_keys=[chair_id])
    secretary = relationship("User", foreign_keys=[secretary_id])

    def __repr__(self):
        return f"<Defense(id={self.id}, topic_id={self.topic_id}, result='{self.result}')>"
