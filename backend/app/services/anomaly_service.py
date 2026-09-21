"""
异常检测服务层

封装异常检测引擎的调用，提供异常记录 CRUD、复核管理、统计聚合等业务逻辑。
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_

from app.models.anomaly import AnomalyRecord, AnomalyReview
from app.models.user import User
from app.models.topic import Topic

from app.anomaly.anomaly_engine import AnomalyEngine
from app.anomaly.evaluator import AnomalyEvaluator

from app.core.exceptions import NotFoundException

logger = logging.getLogger(__name__)


class AnomalyService:
    """异常检测服务

    提供异常检测相关的业务逻辑，包括：
    - 检测触发与结果处理
    - 异常记录的增删改查
    - 复核记录管理
    - 统计数据聚合
    """

    def __init__(self, db: Session) -> None:
        """初始化服务

        Args:
            db: 数据库会话
        """
        self.db = db
        self.engine = AnomalyEngine(db)
        self.evaluator = AnomalyEvaluator(db)

    # ==================================================================
    # 检测相关
    # ==================================================================

    def detect_target(
        self,
        target_type: str,
        target_id: int,
        method: str = "combined",
        save_record: bool = True,
    ) -> Dict[str, Any]:
        """检测单个目标

        Args:
            target_type: 目标类型
            target_id: 目标ID
            method: 检测方法
            save_record: 是否保存异常记录

        Returns:
            检测结果
        """
        result = self.engine.detect_target(target_type, target_id, method)

        if save_record and result.get("anomaly_detected"):
            try:
                record = self.engine.save_anomaly_record(result)
                result["record_id"] = record.id
            except Exception as e:
                logger.error(f"保存异常记录失败: {str(e)}")

        return result

    def detect_batch(
        self,
        target_type: str,
        method: str = "combined",
        save_records: bool = True,
    ) -> Dict[str, Any]:
        """批量检测某类型的所有目标

        Args:
            target_type: 目标类型
            method: 检测方法
            save_records: 是否保存异常记录

        Returns:
            批量检测结果汇总
        """
        results = self.engine.detect_batch(target_type, method)

        anomaly_results = [r for r in results if r.get("anomaly_detected")]

        saved_count = 0
        if save_records:
            for result in anomaly_results:
                try:
                    record = self.engine.save_anomaly_record(result)
                    result["record_id"] = record.id
                    saved_count += 1
                except Exception as e:
                    logger.error(f"保存异常记录失败: {str(e)}")

        l1_count = sum(1 for r in results if r.get("severity_level") == "L1")
        l2_count = sum(1 for r in results if r.get("severity_level") == "L2")
        l3_count = sum(1 for r in results if r.get("severity_level") == "L3")

        return {
            "total_count": len(results),
            "anomaly_count": len(anomaly_results),
            "saved_count": saved_count,
            "L1_count": l1_count,
            "L2_count": l2_count,
            "L3_count": l3_count,
            "results": results,
        }

    def run_full_detection(self) -> Dict[str, Any]:
        """运行全量检测

        Returns:
            全量检测结果
        """
        return self.engine.run_full_detection()

    def evaluate_detection(
        self,
        dataset_type: str = "all",
        method: str = "combined",
    ) -> Dict[str, Any]:
        """评估检测准确性

        Args:
            dataset_type: 数据集类型
            method: 检测方法

        Returns:
            评估结果
        """
        return self.engine.evaluate_detection(dataset_type, method)

    # ==================================================================
    # 异常记录 CRUD
    # ==================================================================

    def get_record_list(
        self,
        page: int = 1,
        page_size: int = 20,
        target_type: Optional[str] = None,
        severity_level: Optional[str] = None,
        review_status: Optional[str] = None,
        student_id: Optional[int] = None,
        keyword: Optional[str] = None,
    ) -> Dict[str, Any]:
        """获取异常记录列表（分页）

        Args:
            page: 页码
            page_size: 每页大小
            target_type: 目标类型筛选
            severity_level: 严重等级筛选
            review_status: 复核状态筛选
            student_id: 学生ID筛选
            keyword: 关键词搜索

        Returns:
            分页结果字典
        """
        query = self.db.query(AnomalyRecord)

        if target_type:
            query = query.filter(AnomalyRecord.target_type == target_type)
        if severity_level:
            query = query.filter(AnomalyRecord.severity_level == severity_level)
        if review_status:
            query = query.filter(AnomalyRecord.review_status == review_status)
        if student_id:
            query = query.filter(AnomalyRecord.student_id == student_id)
        if keyword:
            query = query.filter(
                or_(
                    AnomalyRecord.description.like(f"%{keyword}%"),
                    AnomalyRecord.feature_name.like(f"%{keyword}%"),
                    AnomalyRecord.suggestion.like(f"%{keyword}%"),
                )
            )

        total = query.count()

        records = (
            query.order_by(desc(AnomalyRecord.detection_time))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        # 补充关联信息
        items = []
        for record in records:
            item = self._record_to_dict(record)
            items.append(item)

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": items,
        }

    def get_record_detail(self, record_id: int) -> Dict[str, Any]:
        """获取异常记录详情

        Args:
            record_id: 记录ID

        Returns:
            记录详情字典

        Raises:
            NotFoundException: 记录不存在
        """
        record = self.db.query(AnomalyRecord).filter(
            AnomalyRecord.id == record_id
        ).first()

        if not record:
            raise NotFoundException("异常记录不存在")

        return self._record_to_dict(record)

    def delete_record(self, record_id: int) -> bool:
        """删除异常记录

        Args:
            record_id: 记录ID

        Returns:
            是否删除成功

        Raises:
            NotFoundException: 记录不存在
        """
        record = self.db.query(AnomalyRecord).filter(
            AnomalyRecord.id == record_id
        ).first()

        if not record:
            raise NotFoundException("异常记录不存在")

        self.db.delete(record)
        self.db.commit()

        logger.info(f"删除异常记录: {record_id}")
        return True

    # ==================================================================
    # 复核记录管理
    # ==================================================================

    def review_record(
        self,
        record_id: int,
        reviewer_id: int,
        result: str,
        opinion: str = "",
        correction: str = "",
        correction_result: str = "",
    ) -> Dict[str, Any]:
        """人工复核异常记录

        Args:
            record_id: 异常记录ID
            reviewer_id: 复核人ID
            result: 复核结果 (confirmed/false_positive/ignored)
            opinion: 复核意见
            correction: 纠正措施
            correction_result: 纠正结果

        Returns:
            复核结果字典

        Raises:
            NotFoundException: 记录不存在
        """
        record = self.db.query(AnomalyRecord).filter(
            AnomalyRecord.id == record_id
        ).first()

        if not record:
            raise NotFoundException("异常记录不存在")

        # 更新记录的复核状态
        record.review_status = result
        record.reviewer_id = reviewer_id
        record.review_time = datetime.now()
        record.review_opinion = opinion
        record.correction_result = correction_result

        # 创建复核记录
        review = AnomalyReview(
            anomaly_id=record_id,
            reviewer_id=reviewer_id,
            result=result,
            opinion=opinion,
            correction=correction,
            correction_result=correction_result,
            review_time=datetime.now(),
        )

        self.db.add(review)
        self.db.commit()
        self.db.refresh(record)
        self.db.refresh(review)

        logger.info(
            f"异常记录复核: record_id={record_id}, "
            f"reviewer_id={reviewer_id}, result={result}"
        )

        return self._record_to_dict(record)

    def get_review_history(self, record_id: int) -> List[Dict[str, Any]]:
        """获取异常记录的复核历史

        Args:
            record_id: 异常记录ID

        Returns:
            复核记录列表
        """
        reviews = (
            self.db.query(AnomalyReview)
            .filter(AnomalyReview.anomaly_id == record_id)
            .order_by(desc(AnomalyReview.review_time))
            .all()
        )

        result = []
        for review in reviews:
            reviewer = self.db.query(User).filter(
                User.id == review.reviewer_id
            ).first()

            result.append({
                "id": review.id,
                "anomaly_id": review.anomaly_id,
                "reviewer_id": review.reviewer_id,
                "reviewer_name": reviewer.real_name if reviewer else "",
                "result": review.result,
                "opinion": review.opinion or "",
                "correction": review.correction or "",
                "correction_result": review.correction_result or "",
                "review_time": review.review_time,
                "create_time": review.create_time,
            })

        return result

    # ==================================================================
    # 统计数据聚合
    # ==================================================================

    def get_stats(self) -> Dict[str, Any]:
        """获取异常统计数据

        Returns:
            统计数据字典
        """
        # 总数
        total = self.db.query(func.count(AnomalyRecord.id)).scalar() or 0

        # 按等级统计
        l1_count = self.db.query(func.count(AnomalyRecord.id)).filter(
            AnomalyRecord.severity_level == "L1"
        ).scalar() or 0

        l2_count = self.db.query(func.count(AnomalyRecord.id)).filter(
            AnomalyRecord.severity_level == "L2"
        ).scalar() or 0

        l3_count = self.db.query(func.count(AnomalyRecord.id)).filter(
            AnomalyRecord.severity_level == "L3"
        ).scalar() or 0

        # 按复核状态统计
        pending_count = self.db.query(func.count(AnomalyRecord.id)).filter(
            AnomalyRecord.review_status == "pending"
        ).scalar() or 0

        confirmed_count = self.db.query(func.count(AnomalyRecord.id)).filter(
            AnomalyRecord.review_status == "confirmed"
        ).scalar() or 0

        false_positive_count = self.db.query(func.count(AnomalyRecord.id)).filter(
            AnomalyRecord.review_status == "false_positive"
        ).scalar() or 0

        # 按目标类型统计
        by_type_results = self.db.query(
            AnomalyRecord.target_type,
            func.count(AnomalyRecord.id).label("count"),
        ).group_by(AnomalyRecord.target_type).all()

        by_type: Dict[str, int] = {}
        for target_type, count in by_type_results:
            by_type[target_type] = count

        # 近7天趋势
        recent_trend = self._get_recent_trend(days=7)

        # 精确率（基于已复核记录）
        reviewed_total = confirmed_count + false_positive_count
        precision = (
            confirmed_count / reviewed_total if reviewed_total > 0 else 0.0
        )

        return {
            "total": total,
            "L1_count": l1_count,
            "L2_count": l2_count,
            "L3_count": l3_count,
            "pending_count": pending_count,
            "confirmed_count": confirmed_count,
            "false_positive_count": false_positive_count,
            "ignored_count": total - pending_count - confirmed_count - false_positive_count,
            "by_type": by_type,
            "recent_trend": recent_trend,
            "precision": round(precision, 4),
            "reviewed_total": reviewed_total,
        }

    def _get_recent_trend(self, days: int = 7) -> List[Dict[str, Any]]:
        """获取最近N天的异常趋势

        Args:
            days: 天数

        Returns:
            按日期统计的列表
        """
        result: List[Dict[str, Any]] = []

        for i in range(days - 1, -1, -1):
            date = datetime.now().date()
            from datetime import timedelta
            day = date - timedelta(days=i)
            next_day = day + timedelta(days=1)

            count = self.db.query(func.count(AnomalyRecord.id)).filter(
                AnomalyRecord.detection_time >= day,
                AnomalyRecord.detection_time < next_day,
            ).scalar() or 0

            l1 = self.db.query(func.count(AnomalyRecord.id)).filter(
                AnomalyRecord.detection_time >= day,
                AnomalyRecord.detection_time < next_day,
                AnomalyRecord.severity_level == "L1",
            ).scalar() or 0

            l2 = self.db.query(func.count(AnomalyRecord.id)).filter(
                AnomalyRecord.detection_time >= day,
                AnomalyRecord.detection_time < next_day,
                AnomalyRecord.severity_level == "L2",
            ).scalar() or 0

            l3 = self.db.query(func.count(AnomalyRecord.id)).filter(
                AnomalyRecord.detection_time >= day,
                AnomalyRecord.detection_time < next_day,
                AnomalyRecord.severity_level == "L3",
            ).scalar() or 0

            result.append({
                "date": day.isoformat(),
                "total": count,
                "L1": l1,
                "L2": l2,
                "L3": l3,
            })

        return result

    # ==================================================================
    # 内部辅助方法
    # ==================================================================

    def _record_to_dict(self, record: AnomalyRecord) -> Dict[str, Any]:
        """将记录对象转换为字典

        Args:
            record: 异常记录对象

        Returns:
            记录字典
        """
        # 获取学生信息
        student_name = ""
        if record.student_id:
            student = self.db.query(User).filter(
                User.id == record.student_id
            ).first()
            if student:
                student_name = student.real_name

        # 获取选题信息
        topic_title = ""
        if record.topic_id:
            topic = self.db.query(Topic).filter(
                Topic.id == record.topic_id
            ).first()
            if topic:
                topic_title = topic.title

        # 获取复核人信息
        reviewer_name = ""
        if record.reviewer_id:
            reviewer = self.db.query(User).filter(
                User.id == record.reviewer_id
            ).first()
            if reviewer:
                reviewer_name = reviewer.real_name

        # 复核次数
        review_count = len(record.reviews) if record.reviews else 0

        return {
            "id": record.id,
            "target_type": record.target_type,
            "target_id": record.target_id,
            "student_id": record.student_id,
            "student_name": student_name,
            "topic_id": record.topic_id,
            "topic_title": topic_title,
            "detection_type": record.detection_type,
            "feature_name": record.feature_name,
            "feature_value": record.feature_value,
            "feature_data": record.feature_data,
            "anomaly_score": record.anomaly_score,
            "severity_level": record.severity_level,
            "confidence": record.confidence,
            "description": record.description,
            "suggestion": record.suggestion,
            "review_status": record.review_status,
            "reviewer_id": record.reviewer_id,
            "reviewer_name": reviewer_name,
            "review_time": record.review_time,
            "review_opinion": record.review_opinion or "",
            "correction_result": record.correction_result or "",
            "detection_time": record.detection_time,
            "create_time": record.create_time,
            "update_time": record.update_time,
            "review_count": review_count,
        }
