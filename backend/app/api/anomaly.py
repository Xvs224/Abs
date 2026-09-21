"""
异常检测 API 路由

提供异常检测、记录查询、复核管理、统计分析等 RESTful 接口。
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.response import success_response, page_response
from app.core.security import get_current_user, require_admin, require_teacher_or_admin
from app.models.user import User
from app.schemas.anomaly import (
    DetectionRequest,
    AnomalyReviewRequest,
    AnomalyEvaluationRequest,
)
from app.services.anomaly_service import AnomalyService

router = APIRouter(prefix="/api/anomaly", tags=["异常检测"])


# ==================================================================
# 检测接口
# ==================================================================

@router.post("/detect", summary="手动触发异常检测")
def detect_anomaly(
    request: DetectionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin),
):
    """
    手动触发单个目标的异常检测

    - **target_type**: 目标类型 (student/topic/proposal/guidance/midterm/thesis/review)
    - **target_id**: 目标ID（scope=single 时必填）
    - **detection_method**: 检测方法 (iqr/isolation_forest/combined)
    - **scope**: 检测范围 (single/all)
    """
    service = AnomalyService(db)

    if request.scope == "all":
        # 全量检测某类型
        result = service.detect_batch(
            target_type=request.target_type,
            method=request.detection_method or "combined",
        )
        return success_response(data=result, message="批量检测完成")
    else:
        # 单个目标检测
        if not request.target_id:
            from app.core.exceptions import BusinessException
            raise BusinessException(message="单个检测必须指定 target_id")

        result = service.detect_target(
            target_type=request.target_type,
            target_id=request.target_id,
            method=request.detection_method or "combined",
        )
        return success_response(data=result, message="检测完成")


@router.post("/detect/batch", summary="批量异常检测")
def detect_batch(
    request: DetectionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin),
):
    """
    对指定类型的所有目标进行批量异常检测

    - **target_type**: 目标类型
    - **detection_method**: 检测方法
    """
    service = AnomalyService(db)
    result = service.detect_batch(
        target_type=request.target_type,
        method=request.detection_method or "combined",
    )
    return success_response(data=result, message="批量检测完成")


@router.post("/detect/full", summary="全量异常检测")
def detect_full(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    运行全量异常检测，检测所有目标类型的所有数据
    """
    service = AnomalyService(db)
    result = service.run_full_detection()
    return success_response(data=result, message="全量检测完成")


# ==================================================================
# 异常记录接口
# ==================================================================

@router.get("/records", summary="异常记录列表")
def get_records(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    target_type: Optional[str] = Query(None, description="目标类型"),
    severity_level: Optional[str] = Query(None, description="严重等级"),
    review_status: Optional[str] = Query(None, description="复核状态"),
    student_id: Optional[int] = Query(None, description="学生ID"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取异常记录列表（分页）

    支持按目标类型、严重等级、复核状态、学生ID筛选，以及关键词搜索。
    """
    # 数据隔离：学生只能查看自己的异常记录
    if current_user.role == "student":
        student_id = current_user.id

    service = AnomalyService(db)
    result = service.get_record_list(
        page=page,
        page_size=page_size,
        target_type=target_type,
        severity_level=severity_level,
        review_status=review_status,
        student_id=student_id,
        keyword=keyword,
    )
    return page_response(
        items=result["items"],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
    )


@router.get("/records/{record_id}", summary="异常记录详情")
def get_record_detail(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin),
):
    """
    获取异常记录详情

    - **record_id**: 异常记录ID
    """
    service = AnomalyService(db)
    result = service.get_record_detail(record_id)
    return success_response(data=result)


@router.post("/records/{record_id}/review", summary="人工复核异常记录")
def review_record(
    record_id: int,
    request: AnomalyReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin),
):
    """
    人工复核异常记录

    - **record_id**: 异常记录ID
    - **result**: 复核结果 (confirmed/false_positive/ignored)
    - **opinion**: 复核意见
    - **correction**: 纠正措施
    - **correction_result**: 纠正结果
    """
    service = AnomalyService(db)
    result = service.review_record(
        record_id=record_id,
        reviewer_id=current_user.id,
        result=request.result,
        opinion=request.opinion or "",
        correction=request.correction or "",
        correction_result=request.correction_result or "",
    )
    return success_response(data=result, message="复核完成")


@router.get("/records/{record_id}/reviews", summary="复核历史记录")
def get_review_history(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin),
):
    """
    获取异常记录的复核历史

    - **record_id**: 异常记录ID
    """
    service = AnomalyService(db)
    result = service.get_review_history(record_id)
    return success_response(data=result)


# ==================================================================
# 统计接口
# ==================================================================

@router.get("/stats", summary="异常统计数据")
def get_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin),
):
    """
    获取异常检测统计数据

    包括总数、各等级数量、各类型分布、近7天趋势、复核精确率等。
    """
    service = AnomalyService(db)
    result = service.get_stats()
    return success_response(data=result)


# ==================================================================
# 评估接口
# ==================================================================

@router.post("/evaluate", summary="检测准确性评估")
def evaluate_detection(
    request: AnomalyEvaluationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    评估异常检测方法的准确性

    - **dataset_type**: 数据集类型 (normal/critical/abnormal/all)
    - **detection_method**: 检测方法 (iqr/isolation_forest/combined)

    返回准确率、精确率、召回率、F1分数、误报率等指标。
    """
    service = AnomalyService(db)
    result = service.evaluate_detection(
        dataset_type=request.dataset_type,
        method=request.detection_method,
    )
    return success_response(data=result, message="评估完成")
