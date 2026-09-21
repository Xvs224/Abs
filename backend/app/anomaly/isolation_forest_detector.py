"""
孤立森林异常检测器

基于 sklearn.ensemble.IsolationForest 的多变量异常检测算法。
通过孤立树（Isolation Tree）集成来识别异常样本，异常样本
更容易被孤立（路径更短）。
"""
from typing import Dict, List, Optional, Any
import logging

import numpy as np
from sklearn.ensemble import IsolationForest

logger = logging.getLogger(__name__)


class IsolationForestDetector:
    """孤立森林异常检测器

    使用孤立森林算法进行多维特征的异常检测。
    异常分数被归一化到 0-1 范围，越接近 1 表示越异常。
    """

    def __init__(
        self,
        contamination: float = 0.1,
        random_state: int = 42,
        n_estimators: int = 100,
        max_samples: str = "auto",
    ) -> None:
        """初始化孤立森林检测器

        Args:
            contamination: 预期异常比例，默认 0.1 (10%)
            random_state: 随机种子，保证可重复性
            n_estimators: 孤立树的数量，默认 100
            max_samples: 每棵树使用的最大样本数
        """
        self.contamination = contamination
        self.random_state = random_state
        self.n_estimators = n_estimators
        self.max_samples = max_samples
        self.model: Optional[IsolationForest] = None
        self._is_fitted = False

    # ------------------------------------------------------------------
    # 模型训练
    # ------------------------------------------------------------------
    def fit(self, X: Any) -> None:
        """训练孤立森林模型

        Args:
            X: 训练数据，可以是二维列表、numpy 数组或类似结构
               形状为 (n_samples, n_features)
        """
        X_array = self._to_numpy_array(X)

        if X_array.shape[0] < 2:
            logger.warning("训练样本数不足，无法训练孤立森林模型")
            return

        # 自动调整 contamination 参数
        n_samples = X_array.shape[0]
        actual_contamination = self.contamination
        # 确保至少有 1 个样本被标记为异常的上界
        max_contamination = max(1.0 / n_samples, 0.5)
        if actual_contamination > max_contamination:
            actual_contamination = max_contamination
            logger.info(
                f"contamination 自动调整为 {actual_contamination:.4f}（样本数不足）"
            )

        self.model = IsolationForest(
            n_estimators=self.n_estimators,
            max_samples=self.max_samples,
            contamination=actual_contamination,
            random_state=self.random_state,
            n_jobs=-1,
        )
        self.model.fit(X_array)
        self._is_fitted = True
        logger.info(
            f"孤立森林模型训练完成，样本数: {X_array.shape[0]}, "
            f"特征数: {X_array.shape[1]}"
        )

    # ------------------------------------------------------------------
    # 预测方法
    # ------------------------------------------------------------------
    def predict(self, X: Any) -> List[Dict[str, Any]]:
        """预测样本是否为异常

        Args:
            X: 待预测数据，形状为 (n_samples, n_features)

        Returns:
            每个样本的预测结果列表，每项包含:
            - is_anomaly: 是否异常
            - score: 归一化的异常分数 (0-1)
            - level: 严重等级 L1/L2/L3
        """
        if not self._is_fitted or self.model is None:
            logger.warning("模型未训练，返回全部正常结果")
            X_array = self._to_numpy_array(X)
            return [
                {"is_anomaly": False, "score": 0.0, "level": "normal"}
                for _ in range(X_array.shape[0])
            ]

        X_array = self._to_numpy_array(X)

        # sklearn 的 decision_function 返回值：
        # - 负值表示异常，正值表示正常
        # - 范围大约在 [-0.5, 0.5] 之间
        raw_scores = self.model.decision_function(X_array)

        # 预测标签：1 表示正常，-1 表示异常
        predictions = self.model.predict(X_array)

        results: List[Dict[str, Any]] = []
        for i in range(len(X_array)):
            raw_score = raw_scores[i]
            is_anomaly = bool(predictions[i] == -1)

            # 将原始分数转换为 0-1 范围的异常分数
            # raw_score 越小越异常（越负越异常）
            # 映射: raw_score -> [0, 1]，值越大越异常
            normalized_score = self._normalize_score(raw_score)

            level = self._get_severity_level(normalized_score)

            results.append({
                "is_anomaly": is_anomaly,
                "score": round(normalized_score, 4),
                "level": level,
                "raw_score": round(raw_score, 4),
            })

        return results

    def detect_single(
        self,
        sample: Any,
        X_all: Any,
    ) -> Dict[str, Any]:
        """单样本检测

        使用全部数据训练模型后检测单个样本。

        Args:
            sample: 待检测的样本特征向量
            X_all: 全部参考数据（用于训练模型）

        Returns:
            检测结果字典
        """
        # 将单样本转为二维数组
        X_all_array = self._to_numpy_array(X_all)

        # 训练模型
        self.fit(X_all_array)

        # 预测单样本
        sample_array = self._to_numpy_array([sample])
        results = self.predict(sample_array)

        return results[0] if results else {
            "is_anomaly": False,
            "score": 0.0,
            "level": "normal",
        }

    # ------------------------------------------------------------------
    # 辅助方法
    # ------------------------------------------------------------------
    def _normalize_score(self, raw_score: float) -> float:
        """将原始 decision_function 分数归一化到 0-1

        sklearn IsolationForest 的 decision_function 返回值：
        - 正常样本的分数 > 0，异常样本的分数 < 0
        - 分数范围大致在 [-0.5, 0.5] 之间

        我们将其映射为 [0, 1]，其中：
        - 0 表示完全正常
        - 1 表示极度异常

        Args:
            raw_score: 原始 decision_function 分数

        Returns:
            归一化后的异常分数 (0-1)
        """
        # 使用 sigmoid 函数进行归一化
        # 当 raw_score < 0 时（异常），分数 > 0.5
        # 当 raw_score > 0 时（正常），分数 < 0.5
        normalized = 1.0 / (1.0 + np.exp(raw_score * 10))
        return float(normalized)

    def _get_severity_level(self, score: float) -> str:
        """根据异常分数返回严重等级

        Args:
            score: 归一化的异常分数 (0-1)

        Returns:
            严重等级: L1(轻度) / L2(中度) / L3(重度) / normal(正常)
        """
        if score >= 0.7:
            return "L3"
        elif score >= 0.55:
            return "L2"
        elif score >= 0.45:
            return "L1"
        else:
            return "normal"

    @staticmethod
    def _to_numpy_array(X: Any) -> np.ndarray:
        """将输入数据转换为 numpy 二维数组

        Args:
            X: 输入数据（列表、列表的列表、numpy 数组等）

        Returns:
            numpy 二维数组
        """
        if isinstance(X, np.ndarray):
            if X.ndim == 1:
                return X.reshape(1, -1)
            return X

        # 处理列表输入
        X_list = list(X)
        if len(X_list) == 0:
            return np.zeros((0, 0))

        # 判断是否为单样本（一维列表）还是多样本（二维列表）
        if isinstance(X_list[0], (list, tuple, np.ndarray)):
            # 二维
            return np.array(X_list, dtype=float)
        else:
            # 一维，视为单样本
            return np.array([X_list], dtype=float)

    @property
    def is_fitted(self) -> bool:
        """模型是否已训练"""
        return self._is_fitted
