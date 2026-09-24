"""
异常检测引擎（主入口）

整合特征提取、IQR 检测、孤立森林检测，提供统一的异常检测接口。
支持单目标检测、批量检测、全量检测等多种检测模式。
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from sqlalchemy.orm import Session

from app.models.anomaly import AnomalyRecord
from app.config import settings

from app.anomaly.feature_extractor import FeatureExtractor
from app.anomaly.iqr_detector import IQRDetector
from app.anomaly.isolation_forest_detector import IsolationForestDetector

logger = logging.getLogger(__name__)

# 各目标类型对应的可检测特征及说明
TARGET_FEATURE_MAP: Dict[str, List[Dict[str, str]]] = {
    "student": [
        {"name": "progress_percentage", "label": "进度百分比", "direction": "low"},
        {"name": "thesis_version_count", "label": "论文版本数", "direction": "both"},
        {"name": "format_score", "label": "格式得分", "direction": "low"},
        {"name": "word_count", "label": "论文字数", "direction": "both"},
        {"name": "review_score_deviation", "label": "评阅分数偏差", "direction": "high"},
        {"name": "rectification_count", "label": "整改数量", "direction": "high"},
    ],
    "topic": [
        {"name": "topic_difficulty", "label": "选题难度", "direction": "both"},
        {"name": "topic_workload", "label": "选题工作量", "direction": "both"},
    ],
    "proposal": [
        {"name": "proposal_word_count", "label": "开题报告字数", "direction": "both"},
    ],
    "midterm": [
        {"name": "progress_percentage", "label": "进度百分比", "direction": "low"},
        {"name": "midterm_score", "label": "中期成绩", "direction": "low"},
        {"name": "midterm_score_deviation", "label": "评分偏差", "direction": "high"},
        {"name": "rectification_count", "label": "整改数量", "direction": "high"},
    ],
    "thesis": [
        {"name": "thesis_version_count", "label": "版本数量", "direction": "both"},
        {"name": "format_score", "label": "格式得分", "direction": "low"},
        {"name": "word_count", "label": "字数", "direction": "both"},
        {"name": "reference_count", "label": "参考文献数", "direction": "low"},
    ],
    "review": [
        {"name": "review_avg_score", "label": "平均评阅分数", "direction": "low"},
        {"name": "review_score_deviation", "label": "评阅分数偏差", "direction": "high"},
        {"name": "defense_score", "label": "答辩成绩", "direction": "low"},
        {"name": "review_defense_deviation", "label": "评阅答辩分差", "direction": "high"},
    ],
}


class AnomalyEngine:
    """异常检测引擎

    整合多种检测方法，提供统一的异常检测接口。
    支持 IQR、孤立森林、组合检测三种检测方法。
    """

    def __init__(self, db: Session) -> None:
        """初始化异常检测引擎

        Args:
            db: 数据库会话
        """
        self.db = db
        self.feature_extractor = FeatureExtractor()
        self.iqr_detector = IQRDetector(threshold=settings.ANOMALY_IQR_THRESHOLD)
        self.isolation_forest = IsolationForestDetector(
            contamination=settings.ANOMALY_ISOLATION_FOREST_CONTAMINATION,
        )
        self.supported_target_types = list(TARGET_FEATURE_MAP.keys())

    # ------------------------------------------------------------------
    # 单目标检测
    # ------------------------------------------------------------------
    def detect_target(
        self,
        target_type: str,
        target_id: int,
        method: str = "combined",
    ) -> Dict[str, Any]:
        """检测单个目标的异常

        Args:
            target_type: 目标类型 (student/topic/proposal/midterm/thesis/review)
            target_id: 目标ID
            method: 检测方法 (iqr/isolation_forest/combined)

        Returns:
            检测结果字典，包含是否异常、异常详情、分数等

        Raises:
            ValueError: 不支持的目标类型或检测方法
        """
        if target_type not in self.supported_target_types:
            raise ValueError(f"不支持的目标类型: {target_type}")

        if method not in ("iqr", "isolation_forest", "combined"):
            raise ValueError(f"不支持的检测方法: {method}")

        # 提取目标特征
        target_features = self.feature_extractor.extract_features_by_target(
            self.db, target_type, target_id
        )

        # 提取所有同类目标的特征作为参考
        all_features = self._get_all_features_by_type(target_type)

        if not all_features:
            return {
                "target_type": target_type,
                "target_id": target_id,
                "method": method,
                "anomaly_detected": False,
                "anomaly_score": 0.0,
                "severity_level": "normal",
                "details": [],
                "feature_data": target_features,
                "message": "参考数据不足，无法检测",
            }

        # 根据检测方法执行检测
        if method == "iqr":
            result = self._detect_by_iqr(target_features, all_features, target_type)
        elif method == "isolation_forest":
            result = self._detect_by_isolation_forest(
                target_features, all_features, target_type
            )
        else:  # combined
            result = self._detect_combined(target_features, all_features, target_type)

        result["target_type"] = target_type
        result["target_id"] = target_id
        result["method"] = method
        result["feature_data"] = target_features

        return result

    # ------------------------------------------------------------------
    # 批量检测
    # ------------------------------------------------------------------
    def detect_batch(
        self,
        target_type: str,
        method: str = "combined",
    ) -> List[Dict[str, Any]]:
        """批量检测某类型的所有目标

        Args:
            target_type: 目标类型
            method: 检测方法

        Returns:
            所有目标的检测结果列表
        """
        if target_type not in self.supported_target_types:
            raise ValueError(f"不支持的目标类型: {target_type}")

        all_features = self._get_all_features_by_type(target_type)

        if not all_features:
            return []

        results: List[Dict[str, Any]] = []

        if method == "iqr":
            # IQR 逐个检测
            for features in all_features:
                tid = self._get_target_id(features, target_type)
                if tid is None:
                    continue
                result = self._detect_by_iqr(features, all_features, target_type)
                result["target_type"] = target_type
                result["target_id"] = tid
                result["method"] = method
                result["feature_data"] = features
                results.append(result)

        elif method == "isolation_forest":
            # 孤立森林批量检测
            results = self._batch_detect_isolation_forest(
                all_features, target_type, method
            )

        else:  # combined
            # 组合检测
            results = self._batch_detect_combined(
                all_features, target_type, method
            )

        return results

    # ------------------------------------------------------------------
    # 全量检测
    # ------------------------------------------------------------------
    def run_full_detection(self) -> Dict[str, Any]:
        """运行全量检测

        对所有目标类型的所有数据执行异常检测。

        Returns:
            全量检测汇总结果
        """
        all_results: Dict[str, List[Dict[str, Any]]] = {}
        summary = {
            "total_targets": 0,
            "total_anomalies": 0,
            "L1_count": 0,
            "L2_count": 0,
            "L3_count": 0,
            "by_type": {},
        }

        for target_type in self.supported_target_types:
            try:
                type_results = self.detect_batch(target_type, method="combined")
                all_results[target_type] = type_results

                anomaly_count = sum(1 for r in type_results if r.get("anomaly_detected"))
                l1 = sum(1 for r in type_results if r.get("severity_level") == "L1")
                l2 = sum(1 for r in type_results if r.get("severity_level") == "L2")
                l3 = sum(1 for r in type_results if r.get("severity_level") == "L3")

                summary["total_targets"] += len(type_results)
                summary["total_anomalies"] += anomaly_count
                summary["L1_count"] += l1
                summary["L2_count"] += l2
                summary["L3_count"] += l3
                summary["by_type"][target_type] = {
                    "total": len(type_results),
                    "anomalies": anomaly_count,
                    "L1": l1,
                    "L2": l2,
                    "L3": l3,
                }

                # 保存异常记录
                for result in type_results:
                    if result.get("anomaly_detected"):
                        try:
                            self.save_anomaly_record(result)
                        except Exception as e:
                            logger.error(f"保存异常记录失败: {str(e)}")

            except Exception as e:
                logger.error(f"检测 {target_type} 类型时出错: {str(e)}")
                all_results[target_type] = []
                summary["by_type"][target_type] = {"error": str(e)}

        summary["detection_time"] = datetime.now().isoformat()

        return {
            "summary": summary,
            "results": all_results,
        }

    # ------------------------------------------------------------------
    # 保存异常记录
    # ------------------------------------------------------------------
    def save_anomaly_record(self, detection_result: Dict[str, Any]) -> AnomalyRecord:
        """保存异常记录到数据库

        Args:
            detection_result: 检测结果字典

        Returns:
            保存后的 AnomalyRecord 对象
        """
        feature_data = detection_result.get("feature_data", {})

        # 确定学生ID和选题ID
        student_id = feature_data.get("student_id")
        topic_id = feature_data.get("topic_id")

        # 获取最异常的特征信息
        details = detection_result.get("details", [])
        top_anomaly = None
        if details:
            # 按分数排序取最高的
            sorted_details = sorted(
                details, key=lambda x: x.get("score", 0), reverse=True
            )
            top_anomaly = sorted_details[0]

        feature_name = top_anomaly.get("feature_name", "") if top_anomaly else ""
        feature_value = float(top_anomaly.get("value", 0)) if top_anomaly else 0.0
        description = self._generate_description(detection_result)
        suggestion = self._generate_suggestion(detection_result)

        record = AnomalyRecord(
            target_type=detection_result.get("target_type", ""),
            target_id=detection_result.get("target_id", 0),
            student_id=student_id,
            topic_id=topic_id,
            detection_type=detection_result.get("method", ""),
            feature_name=feature_name,
            feature_value=feature_value,
            feature_data=feature_data,
            anomaly_score=float(detection_result.get("anomaly_score", 0)),
            severity_level=detection_result.get("severity_level", "L1"),
            confidence=float(detection_result.get("confidence", 0.7)),
            description=description,
            suggestion=suggestion,
            review_status="pending",
            detection_time=datetime.now(),
        )

        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)

        logger.info(
            f"保存异常记录: id={record.id}, "
            f"target={record.target_type}/{record.target_id}, "
            f"level={record.severity_level}"
        )

        return record

    # ------------------------------------------------------------------
    # 评估检测准确性
    # ------------------------------------------------------------------
    def evaluate_detection(
        self,
        dataset_type: str = "all",
        method: str = "combined",
    ) -> Dict[str, Any]:
        """评估检测准确性

        Args:
            dataset_type: 数据集类型 (normal/critical/abnormal/all/real)
                          real = 使用已复核的真实业务数据评估
            method: 检测方法

        Returns:
            评估结果字典
        """
        from app.anomaly.evaluator import AnomalyEvaluator

        evaluator = AnomalyEvaluator(self.db)

        # 真实数据评估：基于已人工复核的异常记录
        if dataset_type == "real":
            return evaluator.evaluate_with_real_data(method)

        return evaluator.evaluate_method(method, dataset_type)

    # ==================================================================
    # 内部方法
    # ==================================================================

    # ------------------------------------------------------------------
    # IQR 检测
    # ------------------------------------------------------------------
    def _detect_by_iqr(
        self,
        target_features: Dict[str, Any],
        all_features: List[Dict[str, Any]],
        target_type: str,
    ) -> Dict[str, Any]:
        """使用 IQR 方法进行检测

        Args:
            target_features: 目标特征
            all_features: 所有参考特征
            target_type: 目标类型

        Returns:
            检测结果
        """
        feature_configs = TARGET_FEATURE_MAP.get(target_type, [])
        details: List[Dict[str, Any]] = []
        max_score = 0.0
        is_anomaly = False
        top_level = "normal"

        for config in feature_configs:
            feature_name = config["name"]
            feature_label = config["label"]
            direction = config["direction"]

            # 获取目标特征值
            value = target_features.get(feature_name)
            if value is None:
                continue

            try:
                value = float(value)
            except (ValueError, TypeError):
                continue

            # 收集所有样本的该特征值
            data_list: List[float] = []
            for feat in all_features:
                v = feat.get(feature_name)
                if v is not None:
                    try:
                        data_list.append(float(v))
                    except (ValueError, TypeError):
                        continue

            if len(data_list) < 4:
                continue

            # IQR 检测
            iqr_result = self.iqr_detector.detect_single(value, data_list)

            # 根据方向过滤（只检测指定方向的异常）
            if direction != "both":
                if direction == "low" and iqr_result["position"] == "high":
                    continue
                if direction == "high" and iqr_result["position"] == "low":
                    continue

            if iqr_result["is_anomaly"]:
                is_anomaly = True
                if iqr_result["score"] > max_score:
                    max_score = iqr_result["score"]
                    top_level = iqr_result["level"]

            details.append({
                "feature_name": feature_name,
                "feature_label": feature_label,
                "value": value,
                "is_anomaly": iqr_result["is_anomaly"],
                "score": iqr_result["score"],
                "level": iqr_result["level"],
                "position": iqr_result["position"],
                "q1": iqr_result["q1"],
                "q3": iqr_result["q3"],
                "lower_bound": iqr_result["lower_bound"],
                "upper_bound": iqr_result["upper_bound"],
            })

        # 按异常分数排序
        details.sort(key=lambda x: x["score"], reverse=True)

        # 置信度计算（基于异常特征的数量和分数）
        anomaly_features = [d for d in details if d["is_anomaly"]]
        confidence = 0.0
        if anomaly_features:
            avg_score = sum(d["score"] for d in anomaly_features) / len(anomaly_features)
            count_factor = min(len(anomaly_features) / 3.0, 1.0)
            confidence = min(0.95, avg_score * 0.6 + count_factor * 0.4)

        return {
            "anomaly_detected": is_anomaly,
            "anomaly_score": round(max_score, 4),
            "severity_level": top_level if is_anomaly else "normal",
            "confidence": round(confidence, 4),
            "details": details,
        }

    # ------------------------------------------------------------------
    # 孤立森林检测
    # ------------------------------------------------------------------
    def _detect_by_isolation_forest(
        self,
        target_features: Dict[str, Any],
        all_features: List[Dict[str, Any]],
        target_type: str,
    ) -> Dict[str, Any]:
        """使用孤立森林方法进行检测

        Args:
            target_features: 目标特征
            all_features: 所有参考特征
            target_type: 目标类型

        Returns:
            检测结果
        """
        feature_configs = TARGET_FEATURE_MAP.get(target_type, [])
        feature_keys = [fc["name"] for fc in feature_configs]

        # 构建特征矩阵
        X_all: List[List[float]] = []
        for feat in all_features:
            vector = FeatureExtractor.features_to_vector(feat, feature_keys)
            X_all.append(vector)

        # 目标样本向量
        target_vector = FeatureExtractor.features_to_vector(
            target_features, feature_keys
        )

        # 训练并预测
        if len(X_all) < 5:
            return {
                "anomaly_detected": False,
                "anomaly_score": 0.0,
                "severity_level": "normal",
                "confidence": 0.0,
                "details": [],
                "message": "样本数不足，无法使用孤立森林检测",
            }

        self.isolation_forest.fit(X_all)
        results = self.isolation_forest.predict([target_vector])
        result = results[0] if results else {
            "is_anomaly": False,
            "score": 0.0,
            "level": "normal",
        }

        # 生成各特征贡献度（简化版，使用 IQR 辅助分析）
        details: List[Dict[str, Any]] = []
        for config in feature_configs:
            feature_name = config["name"]
            feature_label = config["label"]
            value = target_features.get(feature_name, 0)
            try:
                value = float(value) if value is not None else 0.0
            except (ValueError, TypeError):
                value = 0.0

            details.append({
                "feature_name": feature_name,
                "feature_label": feature_label,
                "value": value,
                "is_anomaly": False,
                "score": 0.0,
                "level": "normal",
                "position": "normal",
            })

        # 如果是异常，标记得分最高的特征
        if result["is_anomaly"] and details:
            # 使用 IQR 找出最异常的特征作为说明
            data_map: Dict[str, List[float]] = {}
            for config in feature_configs:
                fname = config["name"]
                data_map[fname] = []
                for feat in all_features:
                    v = feat.get(fname)
                    if v is not None:
                        try:
                            data_map[fname].append(float(v))
                        except (ValueError, TypeError):
                            continue

            for d in details:
                fname = d["feature_name"]
                if data_map.get(fname):
                    iqr_r = self.iqr_detector.detect_single(
                        d["value"], data_map[fname]
                    )
                    d["score"] = iqr_r["score"]
                    d["level"] = iqr_r["level"]
                    d["position"] = iqr_r["position"]
                    d["is_anomaly"] = iqr_r["is_anomaly"]

            details.sort(key=lambda x: x["score"], reverse=True)

        confidence = result["score"] if result["is_anomaly"] else 0.0

        return {
            "anomaly_detected": result["is_anomaly"],
            "anomaly_score": round(result["score"], 4),
            "severity_level": result["level"],
            "confidence": round(confidence, 4),
            "details": details,
        }

    # ------------------------------------------------------------------
    # 组合检测
    # ------------------------------------------------------------------
    def _detect_combined(
        self,
        target_features: Dict[str, Any],
        all_features: List[Dict[str, Any]],
        target_type: str,
    ) -> Dict[str, Any]:
        """组合检测（IQR + 孤立森林）

        取两种方法的并集，异常分数取加权平均。

        Args:
            target_features: 目标特征
            all_features: 所有参考特征
            target_type: 目标类型

        Returns:
            检测结果
        """
        iqr_result = self._detect_by_iqr(target_features, all_features, target_type)
        if_result = self._detect_by_isolation_forest(
            target_features, all_features, target_type
        )

        # 组合判定：任一方法检测为异常则标记为异常
        is_anomaly = iqr_result["anomaly_detected"] or if_result["anomaly_detected"]

        # 加权分数：IQR 权重 0.4，孤立森林权重 0.6
        combined_score = (
            iqr_result["anomaly_score"] * 0.4
            + if_result["anomaly_score"] * 0.6
        )

        # 确定等级
        if is_anomaly:
            if combined_score >= 0.7:
                level = "L3"
            elif combined_score >= 0.4:
                level = "L2"
            else:
                level = "L1"
        else:
            level = "normal"

        # 置信度：两种方法一致时置信度更高
        if iqr_result["anomaly_detected"] and if_result["anomaly_detected"]:
            confidence = min(0.95, max(iqr_result["confidence"], if_result["confidence"]) + 0.1)
        elif is_anomaly:
            confidence = max(iqr_result["confidence"], if_result["confidence"]) * 0.7
        else:
            confidence = 0.0

        # 合并详情，以 IQR 的详细特征为主，补充孤立森林信息
        details = iqr_result.get("details", [])

        return {
            "anomaly_detected": is_anomaly,
            "anomaly_score": round(combined_score, 4),
            "severity_level": level,
            "confidence": round(confidence, 4),
            "details": details,
            "iqr_result": {
                "anomaly_detected": iqr_result["anomaly_detected"],
                "anomaly_score": iqr_result["anomaly_score"],
                "severity_level": iqr_result["severity_level"],
            },
            "isolation_forest_result": {
                "anomaly_detected": if_result["anomaly_detected"],
                "anomaly_score": if_result["anomaly_score"],
                "severity_level": if_result["severity_level"],
            },
        }

    # ------------------------------------------------------------------
    # 批量检测辅助方法
    # ------------------------------------------------------------------
    def _batch_detect_isolation_forest(
        self,
        all_features: List[Dict[str, Any]],
        target_type: str,
        method: str,
    ) -> List[Dict[str, Any]]:
        """孤立森林批量检测

        Args:
            all_features: 所有特征
            target_type: 目标类型
            method: 检测方法

        Returns:
            检测结果列表
        """
        feature_configs = TARGET_FEATURE_MAP.get(target_type, [])
        feature_keys = [fc["name"] for fc in feature_configs]

        # 构建特征矩阵
        X_all: List[List[float]] = []
        for feat in all_features:
            vector = FeatureExtractor.features_to_vector(feat, feature_keys)
            X_all.append(vector)

        if len(X_all) < 5:
            results = []
            for feat in all_features:
                tid = self._get_target_id(feat, target_type)
                results.append({
                    "target_type": target_type,
                    "target_id": tid,
                    "method": method,
                    "anomaly_detected": False,
                    "anomaly_score": 0.0,
                    "severity_level": "normal",
                    "confidence": 0.0,
                    "details": [],
                    "feature_data": feat,
                    "message": "样本数不足",
                })
            return results

        self.isolation_forest.fit(X_all)
        predictions = self.isolation_forest.predict(X_all)

        results: List[Dict[str, Any]] = []
        for i, feat in enumerate(all_features):
            tid = self._get_target_id(feat, target_type)
            pred = predictions[i] if i < len(predictions) else {
                "is_anomaly": False, "score": 0.0, "level": "normal"
            }

            details = []
            for config in feature_configs:
                fname = config["name"]
                flabel = config["label"]
                value = feat.get(fname, 0)
                try:
                    value = float(value) if value is not None else 0.0
                except (ValueError, TypeError):
                    value = 0.0
                details.append({
                    "feature_name": fname,
                    "feature_label": flabel,
                    "value": value,
                    "is_anomaly": False,
                    "score": 0.0,
                    "level": "normal",
                    "position": "normal",
                })

            results.append({
                "target_type": target_type,
                "target_id": tid,
                "method": method,
                "anomaly_detected": pred["is_anomaly"],
                "anomaly_score": pred["score"],
                "severity_level": pred["level"],
                "confidence": pred["score"] if pred["is_anomaly"] else 0.0,
                "details": details,
                "feature_data": feat,
            })

        return results

    def _batch_detect_combined(
        self,
        all_features: List[Dict[str, Any]],
        target_type: str,
        method: str,
    ) -> List[Dict[str, Any]]:
        """组合方法批量检测

        Args:
            all_features: 所有特征
            target_type: 目标类型
            method: 检测方法

        Returns:
            检测结果列表
        """
        results: List[Dict[str, Any]] = []

        for feat in all_features:
            tid = self._get_target_id(feat, target_type)
            if tid is None:
                continue

            result = self._detect_combined(feat, all_features, target_type)
            result["target_type"] = target_type
            result["target_id"] = tid
            result["method"] = method
            result["feature_data"] = feat
            results.append(result)

        return results

    # ------------------------------------------------------------------
    # 获取参考特征
    # ------------------------------------------------------------------
    def _get_all_features_by_type(self, target_type: str) -> List[Dict[str, Any]]:
        """根据目标类型获取所有参考特征

        Args:
            target_type: 目标类型

        Returns:
            特征列表
        """
        if target_type == "student":
            return self.feature_extractor.extract_all_features(self.db)

        elif target_type == "topic":
            from app.models.topic import Topic
            topics = self.db.query(Topic).all()
            return [self.feature_extractor.extract_topic_features(self.db, t.id) for t in topics]

        elif target_type == "proposal":
            from app.models.proposal import Proposal
            proposals = self.db.query(Proposal).all()
            return [self.feature_extractor.extract_proposal_features(self.db, p.id) for p in proposals]

        elif target_type == "midterm":
            from app.models.midterm import MidtermCheck
            midterms = self.db.query(MidtermCheck).all()
            return [self.feature_extractor.extract_midterm_features(self.db, m.id) for m in midterms]

        elif target_type == "thesis":
            from app.models.thesis import ThesisVersion
            # 只取每个选题的最新版本
            versions = self.db.query(ThesisVersion).all()
            # 按选题分组，取最新版本
            latest_map: Dict[int, ThesisVersion] = {}
            for v in versions:
                if v.topic_id not in latest_map or v.version_num > latest_map[v.topic_id].version_num:
                    latest_map[v.topic_id] = v
            return [
                self.feature_extractor.extract_thesis_features(self.db, v.id)
                for v in latest_map.values()
            ]

        elif target_type == "review":
            from app.models.topic import Topic
            topics = self.db.query(Topic).all()
            features_list = []
            for t in topics:
                feat = self.feature_extractor.extract_review_features(self.db, t.id)
                feat["topic_id"] = t.id
                feat["student_id"] = t.student_id
                features_list.append(feat)
            return features_list

        return []

    # ------------------------------------------------------------------
    # 辅助方法
    # ------------------------------------------------------------------
    @staticmethod
    def _get_target_id(features: Dict[str, Any], target_type: str) -> Optional[int]:
        """从特征字典中获取目标ID

        Args:
            features: 特征字典
            target_type: 目标类型

        Returns:
            目标ID
        """
        id_map = {
            "student": "student_id",
            "topic": "topic_id",
            "proposal": "proposal_id",
            "midterm": "midterm_id",
            "thesis": "version_id",
            "review": "topic_id",
        }
        key = id_map.get(target_type)
        if key:
            val = features.get(key)
            return int(val) if val is not None else None
        return None

    @staticmethod
    def _generate_description(result: Dict[str, Any]) -> str:
        """生成异常描述

        Args:
            result: 检测结果

        Returns:
            异常描述文本
        """
        details = result.get("details", [])
        if not details:
            return "检测到异常行为"

        anomaly_details = [d for d in details if d.get("is_anomaly")]
        if not anomaly_details:
            return "未检测到明显异常"

        top = anomaly_details[0]
        label = top.get("feature_label", top.get("feature_name", ""))
        position = top.get("position", "")
        position_text = "偏高" if position == "high" else "偏低" if position == "low" else "异常"

        desc = f"{label}{position_text}"
        if len(anomaly_details) > 1:
            desc += f"，另有{len(anomaly_details) - 1}项指标异常"

        return desc

    @staticmethod
    def _generate_suggestion(result: Dict[str, Any]) -> str:
        """生成处理建议

        Args:
            result: 检测结果

        Returns:
            处理建议文本
        """
        details = result.get("details", [])
        anomaly_details = [d for d in details if d.get("is_anomaly")]
        level = result.get("severity_level", "L1")

        if not anomaly_details:
            return "各项指标正常"

        suggestions = []
        for d in anomaly_details[:3]:
            label = d.get("feature_label", "")
            position = d.get("position", "")

            if label == "指导次数" and position == "low":
                suggestions.append("增加指导频次，关注学生研究进展")
            elif label == "指导间隔天数" and position == "high":
                suggestions.append("指导间隔过长，建议缩短指导周期")
            elif label == "指导完成率" and position == "low":
                suggestions.append("指导计划执行率偏低，需督促按计划开展指导")
            elif label == "进度百分比" and position == "low":
                suggestions.append("研究进度滞后，建议加快进度并调整计划")
            elif label == "中期成绩" and position == "low":
                suggestions.append("中期检查成绩偏低，需重点关注和帮扶")
            elif label == "整改数量" and position == "high":
                suggestions.append("问题整改项较多，需加强质量把控")
            elif label == "格式得分" and position == "low":
                suggestions.append("论文格式不规范，需按照模板认真修改")
            elif label == "字数" and position == "low":
                suggestions.append("论文字数偏少，建议补充内容")
            elif label == "字数" and position == "high":
                suggestions.append("论文字数偏多，建议精简冗余内容")
            elif label == "评阅分数偏差" and position == "high":
                suggestions.append("评阅教师评分差异较大，需关注评分标准一致性")
            elif label == "参考文献数量" and position == "low":
                suggestions.append("参考文献数量不足，建议补充相关文献")
            elif label == "论文版本数" and position == "low":
                suggestions.append("论文修改版本较少，需关注修改质量")
            else:
                suggestions.append(f"关注{label}指标")

        if level == "L3":
            suggestions.insert(0, "【严重警告】")
        elif level == "L2":
            suggestions.insert(0, "【警告】")

        return "；".join(suggestions) if suggestions else "建议进一步核查"
