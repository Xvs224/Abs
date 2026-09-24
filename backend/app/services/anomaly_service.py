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
        """运行全量检测（IQR + Isolation Forest + 规则类检测）"""
        from app.anomaly.rule_detector import detect_rules_batch

        ml_result = self.engine.run_full_detection()

        rule_items = detect_rules_batch(self.db)
        rule_saved = self._save_rule_items(rule_items)

        return {
            "ml_detection": ml_result,
            "rule_detection": {
                "total": len(rule_items),
                "saved": rule_saved,
                "algorithm": "rule",
            },
        }

    def run_rule_detection(self) -> Dict[str, Any]:
        """单独跑规则类检测"""
        from app.anomaly.rule_detector import detect_rules_batch
        items = detect_rules_batch(self.db)
        saved = self._save_rule_items(items)
        return {"total": len(items), "saved": saved, "algorithm": "rule"}

    def trigger_for_student(self, student_id: int, clear_old: bool = False) -> Dict[str, Any]:
        """实时触发单个学生的异常检测（IQR + 规则），供业务提交后钩子调用。"""
        from app.anomaly.rule_detector import detect_rules_for_student
        from app.models.anomaly import AnomalyRecord

        if clear_old:
            self.db.query(AnomalyRecord).filter(
                AnomalyRecord.student_id == student_id,
                AnomalyRecord.review_status == "pending",
            ).delete()
            self.db.commit()

        # 规则类
        rule_items = detect_rules_for_student(self.db, student_id)
        rule_saved = self._save_rule_items(rule_items)

        # IQR/IF 类
        ml_result = {"total": 0, "saved": 0}
        try:
            ml_result = self.engine.detect_target("student", student_id, method="combined")
        except Exception as e:
            logger.warning(f"trigger_for_student ml detect error: {e}")

        return {
            "student_id": student_id,
            "rule_saved": rule_saved,
            "ml_result": ml_result,
        }

    def _save_rule_items(self, items: List[Dict[str, Any]]) -> int:
        """批量保存规则类异常记录。

        去重策略：同一天内相同 (target_type, target_id, feature_name) 的异常
        只保留一条（更新 detection_time），跨天则新建记录。
        同时补全 feature_data 和 topic_id 字段。
        """
        from app.models.anomaly import AnomalyRecord
        count = 0
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        for item in items:
            target_type = item.get("target_type")
            target_id = item.get("target_id")
            feature_name = item.get("feature_name")
            student_id = item.get("student_id")

            # 回填 topic_id：根据 student_id 查询选题
            topic_id = item.get("topic_id")
            if not topic_id and student_id:
                topic = self.db.query(Topic).filter(
                    Topic.student_id == student_id
                ).first()
                if topic:
                    topic_id = topic.id

            # 构建 feature_data：汇总规则检测的上下文信息
            feature_data = {
                "student_id": student_id,
                "topic_id": topic_id,
                "teacher_id": item.get("teacher_id"),
                "feature_name": feature_name,
                "feature_value": item.get("feature_value"),
                "anomaly_score": item.get("anomaly_score"),
                "severity_level": item.get("severity_level"),
                "description": item.get("description"),
                "suggestion": item.get("suggestion"),
                "detection_method": "rule",
            }

            # 按天去重：同一天内同特征只存一条，更新时间；跨天则新建
            existing = self.db.query(AnomalyRecord).filter(
                AnomalyRecord.target_type == target_type,
                AnomalyRecord.target_id == target_id,
                AnomalyRecord.feature_name == feature_name,
                AnomalyRecord.review_status == "pending",
                AnomalyRecord.detection_time >= today_start,
            ).first()

            if existing:
                # 同天已存在，更新特征值与检测时间
                existing.feature_value = item.get("feature_value", existing.feature_value)
                existing.anomaly_score = item.get("anomaly_score", existing.anomaly_score)
                existing.feature_data = feature_data
                existing.detection_time = datetime.now()
                if topic_id and not existing.topic_id:
                    existing.topic_id = topic_id
                continue

            rec = AnomalyRecord(
                target_type=target_type,
                target_id=target_id,
                student_id=student_id,
                topic_id=topic_id,
                detection_type="rule",
                feature_name=feature_name,
                feature_value=item.get("feature_value"),
                feature_data=feature_data,
                anomaly_score=item.get("anomaly_score", 0.5),
                severity_level=item.get("severity_level", "L1"),
                description=item.get("description", ""),
                suggestion=item.get("suggestion", ""),
                review_status="pending",
                detection_time=datetime.now(),
            )
            self.db.add(rec)
            count += 1

        if count:
            self.db.commit()
        else:
            self.db.commit()  # 提交更新
        return count

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

    def get_record_list_teacher(
        self,
        page: int = 1,
        page_size: int = 20,
        student_ids: Optional[List[int]] = None,
        target_type: Optional[str] = None,
        severity_level: Optional[str] = None,
        review_status: Optional[str] = None,
        keyword: Optional[str] = None,
    ) -> Dict[str, Any]:
        """获取异常记录列表（教师维度，按负责学生过滤）

        Args:
            page: 页码
            page_size: 每页大小
            student_ids: 教师负责的学生ID列表
            target_type: 目标类型筛选
            severity_level: 严重等级筛选
            review_status: 复核状态筛选
            keyword: 关键词搜索

        Returns:
            分页结果字典
        """
        query = self.db.query(AnomalyRecord)

        if not student_ids:
            return {"total": 0, "page": page, "page_size": page_size, "items": []}

        query = query.filter(AnomalyRecord.student_id.in_(student_ids))

        if target_type:
            query = query.filter(AnomalyRecord.target_type == target_type)
        if severity_level:
            query = query.filter(AnomalyRecord.severity_level == severity_level)
        if review_status:
            query = query.filter(AnomalyRecord.review_status == review_status)
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

        items = [self._record_to_dict(record) for record in records]

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

    def get_stats(self, student_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        """获取异常统计数据

        Args:
            student_ids: 学生ID列表（教师维度过滤，None 表示全局）

        Returns:
            统计数据字典
        """
        base_query = self.db.query(AnomalyRecord)
        if student_ids is not None:
            if not student_ids:
                return {
                    "total": 0, "L1": 0, "L2": 0, "L3": 0,
                    "pending": 0, "confirmed": 0, "false_positive": 0, "ignored": 0,
                    "by_type": {}, "recent_trend": [], "precision": 0.0, "reviewed_total": 0,
                }
            base_query = base_query.filter(AnomalyRecord.student_id.in_(student_ids))

        # 总数
        total = base_query.count()

        # 按等级统计
        l1_count = base_query.filter(AnomalyRecord.severity_level == "L1").count()
        l2_count = base_query.filter(AnomalyRecord.severity_level == "L2").count()
        l3_count = base_query.filter(AnomalyRecord.severity_level == "L3").count()

        # 按复核状态统计
        pending_count = base_query.filter(AnomalyRecord.review_status == "pending").count()
        confirmed_count = base_query.filter(AnomalyRecord.review_status == "confirmed").count()
        false_positive_count = base_query.filter(AnomalyRecord.review_status == "false_positive").count()

        # 按目标类型统计
        by_type_results = self.db.query(
            AnomalyRecord.target_type,
            func.count(AnomalyRecord.id).label("count"),
        )
        if student_ids is not None:
            by_type_results = by_type_results.filter(AnomalyRecord.student_id.in_(student_ids))
        by_type_results = by_type_results.group_by(AnomalyRecord.target_type).all()

        by_type: Dict[str, int] = {}
        for target_type, count in by_type_results:
            by_type[target_type] = count

        # 近7天趋势
        recent_trend = self._get_recent_trend(days=7, student_ids=student_ids)

        # 精确率（基于已复核记录）
        reviewed_total = confirmed_count + false_positive_count
        precision = (
            confirmed_count / reviewed_total if reviewed_total > 0 else 0.0
        )

        return {
            "total": total,
            "L1": l1_count,
            "L2": l2_count,
            "L3": l3_count,
            "pending": pending_count,
            "confirmed": confirmed_count,
            "false_positive": false_positive_count,
            "ignored": total - pending_count - confirmed_count - false_positive_count,
            "by_type": by_type,
            "recent_trend": recent_trend,
            "precision": round(precision, 4),
            "reviewed_total": reviewed_total,
        }

    def _get_recent_trend(self, days: int = 7, student_ids: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        """获取最近N天的异常趋势

        Args:
            days: 天数
            student_ids: 学生ID列表（教师维度过滤）

        Returns:
            按日期统计的列表
        """
        result: List[Dict[str, Any]] = []

        for i in range(days - 1, -1, -1):
            date = datetime.now().date()
            from datetime import timedelta
            day = date - timedelta(days=i)
            next_day = day + timedelta(days=1)

            base = self.db.query(AnomalyRecord).filter(
                AnomalyRecord.detection_time >= day,
                AnomalyRecord.detection_time < next_day,
            )
            if student_ids is not None:
                base = base.filter(AnomalyRecord.student_id.in_(student_ids))

            count = base.count()
            l1 = base.filter(AnomalyRecord.severity_level == "L1").count()
            l2 = base.filter(AnomalyRecord.severity_level == "L2").count()
            l3 = base.filter(AnomalyRecord.severity_level == "L3").count()

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

        # 获取选题信息及指导教师
        topic_title = ""
        teacher_name = ""
        if record.topic_id:
            topic = self.db.query(Topic).filter(
                Topic.id == record.topic_id
            ).first()
            if topic:
                topic_title = topic.title
                if topic.teacher_id:
                    teacher = self.db.query(User).filter(
                        User.id == topic.teacher_id
                    ).first()
                    if teacher:
                        teacher_name = teacher.real_name

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

        # 构建异常详情：汇总特征数据、建议等
        detail_parts = []
        if record.feature_name:
            detail_parts.append(f"异常特征：{record.feature_name}（值：{record.feature_value}）")
        if record.suggestion:
            detail_parts.append(f"处理建议：{record.suggestion}")
        # 附加特征数据（排除已展示的字段）
        if record.feature_data and isinstance(record.feature_data, dict):
            extra_features = []
            skip_keys = {"student_id", "topic_id", "student_name", "topic_title", record.feature_name}
            for k, v in record.feature_data.items():
                if k not in skip_keys and v is not None:
                    extra_features.append(f"{k}: {v}")
            if extra_features:
                detail_parts.append("相关特征：" + "；".join(extra_features))
        detail_text = "\n".join(detail_parts) if detail_parts else ""

        # 数据来源：检测方法 + 目标类型
        method_map = {"iqr": "IQR统计检测", "isolation_forest": "孤立森林检测", "combined": "综合检测", "rule": "规则检测"}
        type_map = {"topic": "选题", "proposal": "开题", "midterm": "中期", "thesis": "论文", "review": "评阅", "student": "学生", "defense": "答辩", "archive": "归档"}
        method_text = method_map.get(record.detection_type, record.detection_type or "自动检测")
        type_text = type_map.get(record.target_type, record.target_type or "")
        data_source = f"{method_text}-{type_text}" if type_text else method_text

        return {
            "id": record.id,
            "target_type": record.target_type,
            "type": record.target_type,
            "target_id": record.target_id,
            "student_id": record.student_id,
            "student_name": student_name,
            "related_student": student_name,
            "topic_id": record.topic_id,
            "topic_title": topic_title,
            "related_teacher": teacher_name,
            "detection_type": record.detection_type,
            "feature_name": record.feature_name,
            "feature_value": record.feature_value,
            "feature_data": record.feature_data,
            "anomaly_score": record.anomaly_score,
            "severity_level": record.severity_level,
            "confidence": record.confidence,
            "description": record.description,
            "suggestion": record.suggestion,
            "detail": detail_text,
            "data_source": data_source,
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
