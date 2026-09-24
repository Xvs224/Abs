"""
系统阶段时间配置模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func

from app.database import Base


# 允许配置的模块 key 及对应显示名
STAGE_MODULE_CHOICES = [
    ("topic", "选题确认"),
    ("proposal", "开题报告"),
    ("midterm", "中期检查"),
    ("thesis_draft", "论文一稿"),
    ("thesis_revision", "论文二稿"),
    ("thesis_final", "论文终审"),
    ("review", "评阅答辩"),
    ("defense", "答辩"),
    ("archive", "成果归档"),
]


class StageConfig(Base):
    """阶段时间配置表"""
    __tablename__ = "stage_configs"

    id = Column(Integer, primary_key=True, index=True, comment="主键")
    module_key = Column(String(32), unique=True, nullable=False, index=True, comment="模块key: topic/proposal/midterm/thesis_draft/thesis_revision/thesis_final/review/defense/archive")
    module_name = Column(String(50), nullable=False, comment="显示名称")

    start_time = Column(DateTime, nullable=False, comment="阶段开始时间")
    end_time = Column(DateTime, nullable=False, comment="阶段结束时间")

    # 锁定策略
    student_lock_after_end = Column(Integer, default=1, comment="学生在结束时间后是否锁定(1锁定/0不锁定)")
    teacher_lock_after_end = Column(Integer, default=0, comment="教师在结束时间后是否锁定(默认不锁)")

    description = Column(Text, default="", comment="备注说明")

    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<StageConfig(key='{self.module_key}', {self.start_time}~{self.end_time})>"
