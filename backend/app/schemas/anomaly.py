"""
异常检测相关 Schema
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class AnomalyRecordBase(BaseModel):
    """异常记录基础信息"""
    target_type: str
    target_id: int
    detection_type: Optional[str] = ""
    feature_name: Optional[str] = ""
    feature_value: Optional[float] = 0.0
    anomaly_score: Optional[float] = 0.0
    severity_level: Optional[str] = "L1"
    confidence: Optional[float] = 0.0
    description: Optional[str] = ""
    suggestion: Optional[str] = ""


class AnomalyRecordCreate(AnomalyRecordBase):
    """创建异常记录请求"""
    student_id: Optional[int] = None
    topic_id: Optional[int] = None
    feature_data: Optional[Dict[str, Any]] = None


class AnomalyReviewRequest(BaseModel):
    """异常复核请求"""
    result: str = Field(..., pattern="^(confirmed|false_positive|ignored|resolved)$")
    opinion: Optional[str] = ""
    correction: Optional[str] = ""
    correction_result: Optional[str] = ""


class AnomalyRecordResponse(AnomalyRecordBase):
    """异常记录响应"""
    id: int
    student_id: Optional[int] = None
    topic_id: Optional[int] = None
    feature_data: Optional[Dict[str, Any]] = None
    review_status: str
    reviewer_id: Optional[int] = None
    review_time: Optional[datetime] = None
    review_opinion: str = ""
    correction_result: str = ""
    detection_time: Optional[datetime] = None
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None

    # 关联信息
    student_name: Optional[str] = ""
    topic_title: Optional[str] = ""
    reviewer_name: Optional[str] = ""
    review_count: Optional[int] = 0

    class Config:
        from_attributes = True


class AnomalyReviewResponse(BaseModel):
    """异常复核记录响应"""
    id: int
    anomaly_id: int
    reviewer_id: int
    result: str
    opinion: str = ""
    correction: str = ""
    correction_result: str = ""
    review_time: Optional[datetime] = None
    reviewer_name: Optional[str] = ""

    class Config:
        from_attributes = True


class DetectionRequest(BaseModel):
    """异常检测请求"""
    target_type: Optional[str] = None  # 为空时执行全量检测
    target_id: Optional[int] = None
    detection_method: Optional[str] = "combined"  # iqr / isolation_forest / combined
    scope: Optional[str] = "single"  # single / all


class DetectionResult(BaseModel):
    """检测结果"""
    target_type: str
    target_id: int
    detection_method: str
    anomaly_detected: bool
    anomaly_score: float
    severity_level: str
    feature_name: str
    feature_value: float
    description: str
    suggestion: str
    details: Optional[Dict[str, Any]] = None


class BatchDetectionResult(BaseModel):
    """批量检测结果"""
    total_count: int
    anomaly_count: int
    L1_count: int
    L2_count: int
    L3_count: int
    results: List[DetectionResult]


class AnomalyEvaluationRequest(BaseModel):
    """异常检测评估请求"""
    dataset_type: str = "all"  # normal / critical / abnormal / all / real(真实已复核数据)
    detection_method: str = "combined"


class AnomalyEvaluationResult(BaseModel):
    """异常检测评估结果"""
    method: str
    total_samples: int
    normal_samples: int
    abnormal_samples: int
    true_positives: int
    true_negatives: int
    false_positives: int
    false_negatives: int
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    false_alarm_rate: float
    details: Optional[Dict[str, Any]] = None


class AnomalyRecordListResponse(BaseModel):
    """异常记录列表响应"""
    total: int
    items: List[AnomalyRecordResponse]


class AnomalyStats(BaseModel):
    """异常统计"""
    total: int
    L1_count: int
    L2_count: int
    L3_count: int
    pending_count: int
    confirmed_count: int
    false_positive_count: int
    by_type: Dict[str, int]
