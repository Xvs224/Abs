"""
IQR 四分位距异常检测器

基于统计学中四分位距（Interquartile Range）方法的单变量异常检测。
IQR = Q3 - Q1，异常值判定为：值 < Q1 - k*IQR 或 值 > Q3 + k*IQR，
其中 k 为阈值系数，通常取 1.5（轻度异常）或 3.0（重度异常）。
"""
from typing import Dict, List, Tuple, Optional
import statistics
import logging

logger = logging.getLogger(__name__)


class IQRDetector:
    """IQR 四分位距异常检测器

    对单维度数值数据进行异常检测，通过四分位距识别离群点。
    支持自定义阈值系数，并根据偏离程度划分异常等级。
    """

    def __init__(self, threshold: float = 1.5) -> None:
        """初始化 IQR 检测器

        Args:
            threshold: IQR 倍数阈值，默认 1.5。值越大检测越宽松。
                       1.5 为标准异常阈值，3.0 为极端异常阈值。
        """
        self.threshold = threshold

    # ------------------------------------------------------------------
    # 核心检测方法
    # ------------------------------------------------------------------
    def detect_single(
        self,
        value: float,
        data_list: List[float],
    ) -> Dict[str, any]:
        """单值检测

        判断给定值在数据集分布中是否为异常值。

        Args:
            value: 待检测的数值
            data_list: 参考数据集列表

        Returns:
            检测结果字典，包含:
            - is_anomaly: 是否异常
            - score: 异常分数（0-1，越高越异常）
            - level: 严重等级 L1/L2/L3
            - position: 异常位置 high/low/normal
            - q1: 下四分位数
            - q3: 上四分位数
            - iqr: 四分位距
            - lower_bound: 下界
            - upper_bound: 上界
        """
        data_list = self._clean_data(data_list)
        q1, q3, iqr = self._calculate_iqr(data_list)
        lower_bound, upper_bound = self.get_iqr_bounds(data_list)

        is_anomaly = False
        position = "normal"
        score = 0.0

        if value > upper_bound:
            is_anomaly = True
            position = "high"
            # 计算偏离程度分数
            if iqr > 0:
                deviation = (value - upper_bound) / iqr
                score = min(1.0, deviation / 3.0)
            else:
                score = 1.0
        elif value < lower_bound:
            is_anomaly = True
            position = "low"
            if iqr > 0:
                deviation = (lower_bound - value) / iqr
                score = min(1.0, deviation / 3.0)
            else:
                score = 1.0
        else:
            # 正常值也计算相对位置分数（0-0.5 范围）
            if q3 - q1 > 0:
                relative_pos = (value - q1) / (q3 - q1)
                # 越靠近边界分数越高，但不超过 0.5
                score = min(0.5, abs(relative_pos - 0.5))
            else:
                score = 0.0

        level = self._get_severity_level(score)

        return {
            "is_anomaly": is_anomaly,
            "score": round(score, 4),
            "level": level,
            "position": position,
            "q1": round(q1, 4),
            "q3": round(q3, 4),
            "iqr": round(iqr, 4),
            "lower_bound": round(lower_bound, 4),
            "upper_bound": round(upper_bound, 4),
            "value": value,
        }

    def detect_batch(self, data_list: List[float]) -> List[Dict[str, any]]:
        """批量检测

        对数据集中的每个值进行异常检测。

        Args:
            data_list: 待检测的数值列表

        Returns:
            每个数据点的检测结果列表
        """
        data_list = self._clean_data(data_list)
        results: List[Dict[str, any]] = []

        if len(data_list) < 4:
            # 数据量太少时无法计算可靠的 IQR
            for value in data_list:
                results.append({
                    "is_anomaly": False,
                    "score": 0.0,
                    "level": "normal",
                    "position": "normal",
                    "value": value,
                    "q1": 0.0,
                    "q3": 0.0,
                    "iqr": 0.0,
                    "lower_bound": 0.0,
                    "upper_bound": 0.0,
                })
            return results

        for value in data_list:
            result = self.detect_single(value, data_list)
            results.append(result)

        return results

    # ------------------------------------------------------------------
    # 辅助方法
    # ------------------------------------------------------------------
    def get_iqr_bounds(self, data_list: List[float]) -> Tuple[float, float]:
        """计算 IQR 上下界

        Args:
            data_list: 数值列表

        Returns:
            (下界, 上界) 元组
        """
        data_list = self._clean_data(data_list)
        q1, q3, iqr = self._calculate_iqr(data_list)
        lower_bound = q1 - self.threshold * iqr
        upper_bound = q3 + self.threshold * iqr
        return lower_bound, upper_bound

    def _calculate_iqr(self, data_list: List[float]) -> Tuple[float, float, float]:
        """计算四分位数和 IQR

        Args:
            data_list: 已清洗的数值列表

        Returns:
            (Q1, Q3, IQR) 元组
        """
        if len(data_list) == 0:
            return 0.0, 0.0, 0.0

        if len(data_list) == 1:
            return data_list[0], data_list[0], 0.0

        sorted_data = sorted(data_list)
        n = len(sorted_data)

        # 计算 Q1（第25百分位数）
        q1_index = 0.25 * (n - 1)
        q1_low = int(q1_index)
        q1_high = min(q1_low + 1, n - 1)
        q1_frac = q1_index - q1_low
        q1 = sorted_data[q1_low] * (1 - q1_frac) + sorted_data[q1_high] * q1_frac

        # 计算 Q3（第75百分位数）
        q3_index = 0.75 * (n - 1)
        q3_low = int(q3_index)
        q3_high = min(q3_low + 1, n - 1)
        q3_frac = q3_index - q3_low
        q3 = sorted_data[q3_low] * (1 - q3_frac) + sorted_data[q3_high] * q3_frac

        iqr = q3 - q1

        return q1, q3, iqr

    def _get_severity_level(self, score: float) -> str:
        """根据异常分数返回严重等级

        Args:
            score: 异常分数 (0-1)

        Returns:
            严重等级: L1(轻度) / L2(中度) / L3(重度)
        """
        if score >= 0.7:
            return "L3"
        elif score >= 0.4:
            return "L2"
        elif score > 0.0:
            return "L1"
        else:
            return "normal"

    @staticmethod
    def _clean_data(data_list: List[float]) -> List[float]:
        """清洗数据，过滤掉无效值

        Args:
            data_list: 原始数据列表

        Returns:
            清洗后的数值列表
        """
        cleaned: List[float] = []
        for item in data_list:
            if item is None:
                continue
            try:
                val = float(item)
                if not (val != val):  # 排除 NaN
                    cleaned.append(val)
            except (ValueError, TypeError):
                continue
        return cleaned

    # ------------------------------------------------------------------
    # 多特征检测
    # ------------------------------------------------------------------
    def detect_features(
        self,
        feature_values: Dict[str, float],
        feature_data_map: Dict[str, List[float]],
    ) -> Dict[str, Dict[str, any]]:
        """对多个特征分别进行 IQR 检测

        Args:
            feature_values: 待检测的特征值字典 {特征名: 特征值}
            feature_data_map: 各特征的参考数据集 {特征名: 数据列表}

        Returns:
            各特征的检测结果字典 {特征名: 检测结果}
        """
        results: Dict[str, Dict[str, any]] = {}

        for feature_name, value in feature_values.items():
            data_list = feature_data_map.get(feature_name, [])
            if not data_list:
                results[feature_name] = {
                    "is_anomaly": False,
                    "score": 0.0,
                    "level": "normal",
                    "position": "normal",
                    "value": value,
                    "note": "no_reference_data",
                }
                continue

            result = self.detect_single(value, data_list)
            results[feature_name] = result

        return results
