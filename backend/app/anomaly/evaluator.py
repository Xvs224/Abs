"""
异常检测评估器

用于评估异常检测算法的性能指标，包括准确率、精确率、召回率、F1分数、误报率等。
支持生成模拟测试数据和基于真实数据的评估。
"""
from typing import Dict, List, Tuple, Any
import random
import math
import logging

from sqlalchemy.orm import Session
import numpy as np

from app.anomaly.feature_extractor import FeatureExtractor
from app.anomaly.iqr_detector import IQRDetector
from app.anomaly.isolation_forest_detector import IsolationForestDetector
from app.config import settings

logger = logging.getLogger(__name__)


class AnomalyEvaluator:
    """异常检测评估器

    提供测试数据生成、指标计算、方法评估等功能。
    """

    # 用于评估的特征维度（学生综合特征）
    EVAL_FEATURE_KEYS: List[str] = [
        "progress_percentage",
        "midterm_score",
        "rectification_count",
        "thesis_version_count",
        "format_score",
        "word_count",
        "reference_count",
        "review_avg_score",
        "review_score_deviation",
        "defense_score",
        "proposal_word_count",
    ]

    # 各特征的正常范围（用于生成测试数据）
    FEATURE_NORMAL_RANGES: Dict[str, Tuple[float, float, float]] = {
        # (均值, 标准差, 方向: high/low/both)
        "progress_percentage": (75.0, 15.0, "low"),
        "midterm_score": (78.0, 10.0, "low"),
        "rectification_count": (1.0, 1.0, "high"),
        "thesis_version_count": (4.0, 1.5, "both"),
        "format_score": (85.0, 10.0, "low"),
        "word_count": (15000.0, 3000.0, "both"),
        "reference_count": (25.0, 8.0, "low"),
        "review_avg_score": (80.0, 8.0, "low"),
        "review_score_deviation": (5.0, 3.0, "high"),
        "defense_score": (78.0, 10.0, "low"),
        "proposal_word_count": (3000.0, 800.0, "both"),
    }

    def __init__(self, db: Session) -> None:
        """初始化评估器

        Args:
            db: 数据库会话
        """
        self.db = db
        self.feature_extractor = FeatureExtractor()
        self.iqr_detector = IQRDetector(threshold=settings.ANOMALY_IQR_THRESHOLD)
        self.isolation_forest = IsolationForestDetector(
            contamination=settings.ANOMALY_ISOLATION_FOREST_CONTAMINATION,
        )

    # ------------------------------------------------------------------
    # 测试数据生成
    # ------------------------------------------------------------------
    def generate_test_data(
        self,
        normal_count: int = 80,
        critical_count: int = 10,
        abnormal_count: int = 10,
    ) -> List[Dict[str, Any]]:
        """生成测试数据

        生成包含正常样本、临界样本和异常样本的测试数据集。

        Args:
            normal_count: 正常样本数量
            critical_count: 临界样本数量（接近异常边界）
            abnormal_count: 异常样本数量

        Returns:
            测试数据列表，每个元素包含 features 和 label (True=异常, False=正常)
        """
        test_data: List[Dict[str, Any]] = []

        # 生成正常样本
        for i in range(normal_count):
            features = self._generate_normal_sample()
            test_data.append({
                "id": f"normal_{i}",
                "features": features,
                "label": False,  # 正常
                "category": "normal",
            })

        # 生成临界样本（接近异常边界，容易被误判）
        for i in range(critical_count):
            features = self._generate_critical_sample()
            test_data.append({
                "id": f"critical_{i}",
                "features": features,
                "label": False,  # 视为正常（临界但未异常）
                "category": "critical",
            })

        # 生成异常样本
        for i in range(abnormal_count):
            features = self._generate_abnormal_sample()
            test_data.append({
                "id": f"abnormal_{i}",
                "features": features,
                "label": True,  # 异常
                "category": "abnormal",
            })

        # 打乱顺序
        random.shuffle(test_data)

        logger.info(
            f"生成测试数据: 正常={normal_count}, "
            f"临界={critical_count}, 异常={abnormal_count}"
        )

        return test_data

    def _generate_normal_sample(self) -> Dict[str, float]:
        """生成一个正常样本

        Returns:
            特征字典
        """
        features: Dict[str, float] = {}
        for feature_name, (mean, std, direction) in self.FEATURE_NORMAL_RANGES.items():
            # 正态分布采样
            value = random.gauss(mean, std)
            # 确保非负
            value = max(0.0, value)
            # 进度和百分比类限制在合理范围
            if feature_name in ("progress_percentage", "format_score",
                                "midterm_score", "review_avg_score",
                                "defense_score"):
                value = min(100.0, value)
            features[feature_name] = round(value, 2)
        return features

    def _generate_critical_sample(self) -> Dict[str, float]:
        """生成一个临界样本（接近异常边界）

        Returns:
            特征字典
        """
        features: Dict[str, float] = {}
        for feature_name, (mean, std, direction) in self.FEATURE_NORMAL_RANGES.items():
            # 偏移 1.5-2 个标准差（接近 IQR 边界）
            if direction == "low":
                # 偏低但还在正常范围边缘
                offset = -1.5 * std
            elif direction == "high":
                # 偏高但还在正常范围边缘
                offset = 1.5 * std
            else:  # both
                # 随机选择一个方向
                offset = (1.5 if random.random() > 0.5 else -1.5) * std

            value = mean + offset + random.gauss(0, std * 0.3)
            value = max(0.0, value)

            if feature_name in ("progress_percentage", "format_score",
                                "midterm_score", "review_avg_score",
                                "defense_score"):
                value = min(100.0, value)

            features[feature_name] = round(value, 2)
        return features

    def _generate_abnormal_sample(self) -> Dict[str, float]:
        """生成一个异常样本

        Returns:
            特征字典
        """
        features: Dict[str, float] = {}

        # 随机选择 2-4 个特征设为异常值
        feature_names = list(self.FEATURE_NORMAL_RANGES.keys())
        anomaly_count = random.randint(2, 4)
        anomaly_features = random.sample(feature_names, anomaly_count)

        for feature_name, (mean, std, direction) in self.FEATURE_NORMAL_RANGES.items():
            if feature_name in anomaly_features:
                # 设置为明显的异常值
                if direction == "low":
                    # 显著偏低
                    value = mean - 3.5 * std + random.gauss(0, std * 0.5)
                elif direction == "high":
                    # 显著偏高
                    value = mean + 3.5 * std + random.gauss(0, std * 0.5)
                else:  # both
                    # 随机选择一个方向显著偏离
                    if random.random() > 0.5:
                        value = mean + 3.5 * std + random.gauss(0, std * 0.5)
                    else:
                        value = mean - 3.5 * std + random.gauss(0, std * 0.5)
            else:
                # 正常范围
                value = random.gauss(mean, std)

            value = max(0.0, value)

            if feature_name in ("progress_percentage", "format_score",
                                "midterm_score", "review_avg_score",
                                "defense_score"):
                value = min(100.0, value)

            features[feature_name] = round(value, 2)

        return features

    # ------------------------------------------------------------------
    # 评估指标计算
    # ------------------------------------------------------------------
    def evaluate(
        self,
        y_true: List[bool],
        y_pred: List[bool],
        scores: List[float],
    ) -> Dict[str, Any]:
        """计算评估指标

        Args:
            y_true: 真实标签列表 (True=异常, False=正常)
            y_pred: 预测标签列表 (True=异常, False=正常)
            scores: 异常分数列表

        Returns:
            评估指标字典，包含准确率、精确率、召回率、F1、误报率等
        """
        if len(y_true) != len(y_pred):
            raise ValueError("y_true 和 y_pred 长度必须一致")

        n = len(y_true)
        if n == 0:
            return {
                "total_samples": 0,
                "accuracy": 0.0,
                "precision": 0.0,
                "recall": 0.0,
                "f1_score": 0.0,
                "false_alarm_rate": 0.0,
                "true_positives": 0,
                "true_negatives": 0,
                "false_positives": 0,
                "false_negatives": 0,
            }

        tp = sum(1 for t, p in zip(y_true, y_pred) if t and p)
        tn = sum(1 for t, p in zip(y_true, y_pred) if not t and not p)
        fp = sum(1 for t, p in zip(y_true, y_pred) if not t and p)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t and not p)

        # 准确率
        accuracy = (tp + tn) / n

        # 精确率（查准率）
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0

        # 召回率（查全率）
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0

        # F1 分数
        f1 = (2 * precision * recall / (precision + recall)
              if (precision + recall) > 0 else 0.0)

        # 误报率（假正率）
        false_alarm_rate = fp / (fp + tn) if (fp + tn) > 0 else 0.0

        # 特异度
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0

        # AUC 近似计算（简化版，基于分数排序）
        auc = self._calculate_auc(y_true, scores)

        # 正常和异常样本数
        normal_count = sum(1 for t in y_true if not t)
        abnormal_count = sum(1 for t in y_true if t)

        return {
            "total_samples": n,
            "normal_samples": normal_count,
            "abnormal_samples": abnormal_count,
            "true_positives": tp,
            "true_negatives": tn,
            "false_positives": fp,
            "false_negatives": fn,
            "accuracy": round(accuracy, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
            "specificity": round(specificity, 4),
            "false_alarm_rate": round(false_alarm_rate, 4),
            "auc": round(auc, 4),
        }

    def _calculate_auc(
        self,
        y_true: List[bool],
        scores: List[float],
    ) -> float:
        """近似计算 AUC (Area Under ROC Curve)

        使用 Mann-Whitney U 统计量近似计算 AUC。

        Args:
            y_true: 真实标签
            scores: 预测分数

        Returns:
            AUC 值
        """
        # 按分数降序排列
        sorted_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)

        tp_count = 0
        fp_count = 0
        total_positive = sum(1 for t in y_true if t)
        total_negative = len(y_true) - total_positive

        if total_positive == 0 or total_negative == 0:
            return 0.5

        auc = 0.0
        prev_tpr = 0.0
        prev_fpr = 0.0

        for idx in sorted_indices:
            if y_true[idx]:
                tp_count += 1
            else:
                fp_count += 1

            tpr = tp_count / total_positive
            fpr = fp_count / total_negative

            # 梯形面积累加
            auc += (fpr - prev_fpr) * (tpr + prev_tpr) / 2
            prev_tpr = tpr
            prev_fpr = fpr

        return auc

    # ------------------------------------------------------------------
    # 方法评估
    # ------------------------------------------------------------------
    def evaluate_method(
        self,
        method: str = "combined",
        dataset_type: str = "all",
    ) -> Dict[str, Any]:
        """评估指定检测方法

        Args:
            method: 检测方法 (iqr/isolation_forest/combined)
            dataset_type: 数据集类型 (normal/critical/abnormal/all)

        Returns:
            评估结果
        """
        # 生成测试数据
        test_data = self.generate_test_data(
            normal_count=80,
            critical_count=10,
            abnormal_count=10,
        )

        # 根据数据集类型过滤
        if dataset_type == "normal":
            test_data = [d for d in test_data if d["category"] == "normal"]
        elif dataset_type == "critical":
            test_data = [d for d in test_data if d["category"] == "critical"]
        elif dataset_type == "abnormal":
            test_data = [d for d in test_data if d["category"] == "abnormal"]
        # all: 使用全部数据

        if not test_data:
            return {"error": "测试数据为空", "method": method, "dataset_type": dataset_type}

        # 提取特征矩阵
        all_features = [d["features"] for d in test_data]
        X_all: List[List[float]] = []
        for feat in all_features:
            vector = FeatureExtractor.features_to_vector(
                feat, self.EVAL_FEATURE_KEYS
            )
            X_all.append(vector)

        y_true = [d["label"] for d in test_data]
        y_pred: List[bool] = []
        scores: List[float] = []

        if method == "iqr":
            y_pred, scores = self._evaluate_iqr(test_data, all_features)
        elif method == "isolation_forest":
            y_pred, scores = self._evaluate_isolation_forest(X_all)
        elif method == "combined":
            y_pred, scores = self._evaluate_combined(test_data, all_features, X_all)
        else:
            return {"error": f"不支持的检测方法: {method}"}

        metrics = self.evaluate(y_true, y_pred, scores)
        metrics["method"] = method
        metrics["dataset_type"] = dataset_type

        return metrics

    def _evaluate_iqr(
        self,
        test_data: List[Dict[str, Any]],
        all_features: List[Dict[str, float]],
    ) -> Tuple[List[bool], List[float]]:
        """评估 IQR 方法

        Args:
            test_data: 测试数据
            all_features: 所有特征列表

        Returns:
            (预测标签, 异常分数) 元组
        """
        y_pred: List[bool] = []
        scores: List[float] = []

        # 为每个特征构建数据列表
        feature_data_map: Dict[str, List[float]] = {}
        for key in self.EVAL_FEATURE_KEYS:
            feature_data_map[key] = [feat.get(key, 0.0) for feat in all_features]

        for i, data in enumerate(test_data):
            features = data["features"]
            max_score = 0.0
            is_anomaly = False

            for key in self.EVAL_FEATURE_KEYS:
                value = features.get(key, 0.0)
                data_list = feature_data_map[key]

                if len(data_list) < 4:
                    continue

                result = self.iqr_detector.detect_single(value, data_list)
                if result["is_anomaly"]:
                    is_anomaly = True
                    if result["score"] > max_score:
                        max_score = result["score"]

            y_pred.append(is_anomaly)
            scores.append(max_score)

        return y_pred, scores

    def _evaluate_isolation_forest(
        self,
        X_all: List[List[float]],
    ) -> Tuple[List[bool], List[float]]:
        """评估孤立森林方法

        Args:
            X_all: 特征矩阵

        Returns:
            (预测标签, 异常分数) 元组
        """
        if len(X_all) < 5:
            return [False] * len(X_all), [0.0] * len(X_all)

        self.isolation_forest.fit(X_all)
        results = self.isolation_forest.predict(X_all)

        y_pred = [r["is_anomaly"] for r in results]
        scores = [r["score"] for r in results]

        return y_pred, scores

    def _evaluate_combined(
        self,
        test_data: List[Dict[str, Any]],
        all_features: List[Dict[str, float]],
        X_all: List[List[float]],
    ) -> Tuple[List[bool], List[float]]:
        """评估组合方法

        Args:
            test_data: 测试数据
            all_features: 所有特征字典列表
            X_all: 特征矩阵

        Returns:
            (预测标签, 异常分数) 元组
        """
        iqr_pred, iqr_scores = self._evaluate_iqr(test_data, all_features)
        if_pred, if_scores = self._evaluate_isolation_forest(X_all)

        y_pred: List[bool] = []
        scores: List[float] = []

        for i in range(len(test_data)):
            # 并集策略
            is_anomaly = iqr_pred[i] or if_pred[i]
            # 加权分数
            combined_score = iqr_scores[i] * 0.4 + if_scores[i] * 0.6
            y_pred.append(is_anomaly)
            scores.append(combined_score)

        return y_pred, scores

    # ------------------------------------------------------------------
    # 基于真实数据的评估
    # ------------------------------------------------------------------
    def evaluate_with_real_data(
        self,
        method: str = "combined",
    ) -> Dict[str, Any]:
        """使用真实数据评估检测方法

        通过已人工复核的异常记录来评估检测准确性。
        真实数据评估能反映算法在实际业务中的表现，是系统投产的关键依据。

        指标说明：
        - TP (确认异常)：review_status == "confirmed"
        - FP (误报)：review_status == "false_positive"
        - 忽略/已处理：review_status in ("ignored", "resolved")，不计入精确率分母
        - 精确率 precision = TP / (TP + FP)  ← 已复核样本中真实异常占比（可靠指标）
        - 复核覆盖率 reviewed_rate = 已复核数 / 检测总数
        - 异常检出率 anomaly_rate = 检测总数 / 扫描目标总数

        Args:
            method: 检测方法

        Returns:
            评估结果字典
        """
        from app.models.anomaly import AnomalyRecord
        from datetime import datetime

        # 所有检测记录
        all_records = self.db.query(AnomalyRecord).all()
        total_detected = len(all_records)

        # 已复核的记录（confirmed / false_positive 用于精确率计算）
        reviewed_records = [
            r for r in all_records
            if r.review_status in ("confirmed", "false_positive")
        ]

        confirmed_count = sum(1 for r in reviewed_records if r.review_status == "confirmed")
        false_positive_count = sum(1 for r in reviewed_records if r.review_status == "false_positive")
        ignored_count = sum(1 for r in all_records if r.review_status == "ignored")
        resolved_count = sum(1 for r in all_records if r.review_status == "resolved")
        pending_count = sum(1 for r in all_records if r.review_status == "pending")
        reviewed_total = len(reviewed_records)

        # 精确率（基于已复核的 confirmed + false_positive）
        precision = (
            confirmed_count / reviewed_total if reviewed_total > 0 else 0.0
        )

        # 复核覆盖率
        reviewed_rate = (
            reviewed_total / total_detected if total_detected > 0 else 0.0
        )

        # 严重等级分布（基于 confirmed 真实异常）
        confirmed_records = [r for r in reviewed_records if r.review_status == "confirmed"]
        severity_dist = {"L1": 0, "L2": 0, "L3": 0}
        for r in confirmed_records:
            lvl = r.severity_level if r.severity_level in severity_dist else "L1"
            severity_dist[lvl] += 1

        # 按目标类型统计
        by_type: Dict[str, Dict[str, int]] = {}
        for r in all_records:
            t = r.target_type or "unknown"
            if t not in by_type:
                by_type[t] = {"total": 0, "confirmed": 0, "false_positive": 0, "pending": 0}
            by_type[t]["total"] += 1
            if r.review_status == "confirmed":
                by_type[t]["confirmed"] += 1
            elif r.review_status == "false_positive":
                by_type[t]["false_positive"] += 1
            elif r.review_status == "pending":
                by_type[t]["pending"] += 1

        # 估算扫描目标总数（用于异常检出率）
        # 通过异常记录中的 target_id 去重 + 类型推断
        scanned_targets = len(set(
            (r.target_type, r.target_id) for r in all_records
        ))
        anomaly_rate = (
            total_detected / scanned_targets if scanned_targets > 0 else 0.0
        )

        return {
            "method": method,
            "evaluation_type": "real",
            "total_samples": total_detected,
            "reviewed_total": reviewed_total,
            "true_positives": confirmed_count,
            "false_positives": false_positive_count,
            "ignored_count": ignored_count,
            "resolved_count": resolved_count,
            "pending_count": pending_count,
            "precision": round(precision, 4),
            "reviewed_rate": round(reviewed_rate, 4),
            "anomaly_rate": round(anomaly_rate, 4),
            "severity_distribution": severity_dist,
            "by_type": by_type,
            "evaluation_time": datetime.now().isoformat(),
            "note": (
                "精确率基于已人工复核的记录计算（confirmed=TP, false_positive=FP）。"
                "召回率因缺少正常样本的人工标注无法精确计算，建议结合复核覆盖率综合判断。"
            ),
        }
