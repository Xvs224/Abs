"""
特征提取器

从毕业论文全过程各阶段数据中提取用于异常检测的特征向量。
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, date
import statistics
import logging

from sqlalchemy.orm import Session

from app.models.user import User
from app.models.topic import Topic
from app.models.proposal import Proposal
from app.models.midterm import MidtermCheck, Rectification
from app.models.thesis import ThesisVersion, FormatCheck
from app.models.review import Review, Defense

logger = logging.getLogger(__name__)


class FeatureExtractor:
    """特征提取器

    从毕业论文全过程各阶段（选题、开题、指导、中期、论文、评阅答辩）中
    提取结构化特征，用于异常检测算法分析。
    """

    def __init__(self) -> None:
        """初始化特征提取器"""
        self.feature_names: List[str] = [
            "progress_percentage",
            "midterm_score",
            "rectification_count",
            "thesis_version_count",
            "format_score",
            "word_count",
            "reference_count",
            "review_score",
            "review_score_deviation",
            "defense_score",
            "proposal_word_count",
        ]

    # ------------------------------------------------------------------
    # 学生全过程特征
    # ------------------------------------------------------------------
    def extract_student_features(self, db: Session, student_id: int) -> Dict[str, Any]:
        """提取学生全过程特征

        Args:
            db: 数据库会话
            student_id: 学生ID

        Returns:
            包含学生全过程各阶段特征的字典
        """
        features: Dict[str, Any] = {
            "student_id": student_id,
            "target_type": "student",
            "target_id": student_id,
        }

        # 获取学生的选题
        topic = db.query(Topic).filter(
            Topic.student_id == student_id,
            Topic.status == "approved",
        ).first()

        if topic:
            features["topic_id"] = topic.id
            topic_features = self.extract_topic_features(db, topic.id)
            features.update(topic_features)

            # 中期特征
            midterm = db.query(MidtermCheck).filter(
                MidtermCheck.topic_id == topic.id
            ).first()
            if midterm:
                midterm_features = self.extract_midterm_features(db, midterm.id)
                features.update(midterm_features)

            # 论文特征
            latest_version = db.query(ThesisVersion).filter(
                ThesisVersion.topic_id == topic.id
            ).order_by(ThesisVersion.version_num.desc()).first()
            if latest_version:
                thesis_features = self.extract_thesis_features(db, latest_version.id)
                features.update(thesis_features)

            # 评阅答辩特征
            review_features = self.extract_review_features(db, topic.id)
            features.update(review_features)
        else:
            features["topic_id"] = None
            # 无选题时填充默认值
            features.update({
                "topic_difficulty": 0,
                "topic_workload": 0,
                "progress_percentage": 0.0,
                "midterm_score": 0.0,
                "rectification_count": 0,
                "thesis_version_count": 0,
                "format_score": 0.0,
                "word_count": 0,
                "reference_count": 0,
                "review_count": 0,
                "review_avg_score": 0.0,
                "review_score_deviation": 0.0,
                "defense_score": 0.0,
            })

        # 开题特征
        proposal = db.query(Proposal).filter(
            Proposal.student_id == student_id
        ).first()
        if proposal:
            proposal_features = self.extract_proposal_features(db, proposal.id)
            features.update(proposal_features)
        else:
            features.update({
                "proposal_word_count": 0,
                "proposal_status": "none",
            })

        return features

    # ------------------------------------------------------------------
    # 选题特征
    # ------------------------------------------------------------------
    def extract_topic_features(self, db: Session, topic_id: int) -> Dict[str, Any]:
        """提取选题特征

        Args:
            db: 数据库会话
            topic_id: 选题ID

        Returns:
            选题特征字典
        """
        topic = db.query(Topic).filter(Topic.id == topic_id).first()
        if not topic:
            return {"topic_id": topic_id, "topic_exists": False}

        difficulty_map = {"easy": 1, "medium": 2, "hard": 3}
        workload_map = {"light": 1, "medium": 2, "heavy": 3}

        features: Dict[str, Any] = {
            "topic_id": topic_id,
            "topic_exists": True,
            "topic_difficulty": difficulty_map.get(topic.difficulty, 2),
            "topic_workload": workload_map.get(topic.workload, 2),
            "topic_status": topic.status,
            "student_id": topic.student_id,
            "teacher_id": topic.teacher_id,
        }

        return features

    # ------------------------------------------------------------------
    # 开题特征
    # ------------------------------------------------------------------
    def extract_proposal_features(self, db: Session, proposal_id: int) -> Dict[str, Any]:
        """提取开题特征

        Args:
            db: 数据库会话
            proposal_id: 开题报告ID

        Returns:
            开题特征字典
        """
        proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
        if not proposal:
            return {"proposal_id": proposal_id, "proposal_exists": False}

        features: Dict[str, Any] = {
            "proposal_id": proposal_id,
            "proposal_exists": True,
            "proposal_word_count": proposal.word_count or 0,
            "proposal_status": proposal.status,
            "topic_id": proposal.topic_id,
            "student_id": proposal.student_id,
        }

        return features

    # ------------------------------------------------------------------
    # 中期特征
    # ------------------------------------------------------------------
    def extract_midterm_features(self, db: Session, midterm_id: int) -> Dict[str, Any]:
        """提取中期特征

        包含进度百分比、成绩、整改数量等。

        Args:
            db: 数据库会话
            midterm_id: 中期检查ID

        Returns:
            中期特征字典
        """
        midterm = db.query(MidtermCheck).filter(MidtermCheck.id == midterm_id).first()
        if not midterm:
            return {"midterm_id": midterm_id, "midterm_exists": False}

        # 整改数量
        rectification_count = db.query(Rectification).filter(
            Rectification.midterm_id == midterm_id
        ).count()

        # 未通过整改数
        failed_rectification_count = db.query(Rectification).filter(
            Rectification.midterm_id == midterm_id,
            Rectification.status == "failed",
        ).count()

        # 成绩偏差（指导教师与检查小组评分差异）
        score_deviation = 0.0
        if midterm.teacher_score and midterm.check_group_score:
            score_deviation = abs(midterm.teacher_score - midterm.check_group_score)

        features: Dict[str, Any] = {
            "midterm_id": midterm_id,
            "midterm_exists": True,
            "progress_percentage": midterm.progress_percentage or 0.0,
            "midterm_teacher_score": midterm.teacher_score or 0.0,
            "midterm_group_score": midterm.check_group_score or 0.0,
            "midterm_score": midterm.final_score or 0.0,
            "midterm_score_deviation": round(score_deviation, 2),
            "rectification_count": rectification_count,
            "failed_rectification_count": failed_rectification_count,
            "midterm_status": midterm.status,
            "topic_id": midterm.topic_id,
            "student_id": midterm.student_id,
        }

        return features

    # ------------------------------------------------------------------
    # 论文版本特征
    # ------------------------------------------------------------------
    def extract_thesis_features(self, db: Session, version_id: int) -> Dict[str, Any]:
        """提取论文版本特征

        包含版本数量、格式得分、字数、参考文献数等。

        Args:
            db: 数据库会话
            version_id: 论文版本ID

        Returns:
            论文特征字典
        """
        version = db.query(ThesisVersion).filter(ThesisVersion.id == version_id).first()
        if not version:
            return {"version_id": version_id, "thesis_exists": False}

        # 该选题的总版本数
        version_count = db.query(ThesisVersion).filter(
            ThesisVersion.topic_id == version.topic_id
        ).count()

        # 格式检测结果
        format_check = db.query(FormatCheck).filter(
            FormatCheck.version_id == version_id
        ).order_by(FormatCheck.check_time.desc()).first()

        format_score = version.format_score or 0.0
        format_pass_rate = 0.0
        format_failed_count = 0
        if format_check:
            format_score = format_check.total_score
            if format_check.total_items > 0:
                format_pass_rate = format_check.passed_count / format_check.total_items
            format_failed_count = format_check.failed_count

        features: Dict[str, Any] = {
            "version_id": version_id,
            "thesis_exists": True,
            "thesis_version_count": version_count,
            "current_version_num": version.version_num,
            "format_score": format_score,
            "format_pass_rate": round(format_pass_rate, 4),
            "format_failed_count": format_failed_count,
            "word_count": version.word_count or 0,
            "page_count": version.page_count or 0,
            "chapter_count": version.chapter_count or 0,
            "reference_count": version.reference_count or 0,
            "file_size": version.file_size or 0,
            "topic_id": version.topic_id,
            "student_id": version.student_id,
        }

        return features

    # ------------------------------------------------------------------
    # 评阅答辩特征
    # ------------------------------------------------------------------
    def extract_review_features(self, db: Session, topic_id: int) -> Dict[str, Any]:
        """提取评阅答辩特征

        包含评阅分数、分数偏差、答辩成绩等。

        Args:
            db: 数据库会话
            topic_id: 选题ID

        Returns:
            评阅答辩特征字典
        """
        # 评阅记录
        reviews = db.query(Review).filter(
            Review.topic_id == topic_id,
            Review.status == "completed",
        ).all()

        review_count = len(reviews)
        review_scores = [r.total_score for r in reviews if r.total_score > 0]
        avg_review_score = statistics.mean(review_scores) if review_scores else 0.0

        # 评阅分数偏差（不同评阅教师之间的分数差异）
        score_deviation = 0.0
        if len(review_scores) >= 2:
            score_deviation = max(review_scores) - min(review_scores)

        # 分数标准差
        score_std = 0.0
        if len(review_scores) >= 2:
            score_std = statistics.stdev(review_scores)

        # 答辩成绩
        defense = db.query(Defense).filter(Defense.topic_id == topic_id).first()
        defense_score = 0.0
        defense_grade = ""
        defense_result = ""
        if defense and defense.total_score > 0:
            defense_score = defense.total_score
            defense_grade = defense.grade or ""
            defense_result = defense.result or ""

        # 评阅与答辩分数差异
        review_defense_deviation = 0.0
        if avg_review_score > 0 and defense_score > 0:
            review_defense_deviation = abs(avg_review_score - defense_score)

        features: Dict[str, Any] = {
            "review_count": review_count,
            "review_avg_score": round(avg_review_score, 2),
            "review_score_deviation": round(score_deviation, 2),
            "review_score_std": round(score_std, 2),
            "defense_score": defense_score,
            "defense_grade": defense_grade,
            "defense_result": defense_result,
            "review_defense_deviation": round(review_defense_deviation, 2),
        }

        return features

    # ------------------------------------------------------------------
    # 批量提取所有学生特征
    # ------------------------------------------------------------------
    def extract_all_features(self, db: Session) -> List[Dict[str, Any]]:
        """提取所有学生特征用于批量检测

        Args:
            db: 数据库会话

        Returns:
            所有学生的特征列表
        """
        # 获取所有学生用户
        students = db.query(User).filter(User.role == "student").all()

        all_features: List[Dict[str, Any]] = []
        for student in students:
            try:
                features = self.extract_student_features(db, student.id)
                features["student_name"] = student.real_name
                features["student_no"] = student.student_no
                all_features.append(features)
            except Exception as e:
                logger.warning(f"提取学生 {student.id} 特征失败: {str(e)}")
                continue

        return all_features

    # ------------------------------------------------------------------
    # 按目标类型提取特征
    # ------------------------------------------------------------------
    def extract_features_by_target(
        self,
        db: Session,
        target_type: str,
        target_id: int,
    ) -> Dict[str, Any]:
        """根据目标类型提取对应特征

        Args:
            db: 数据库会话
            target_type: 目标类型
            target_id: 目标ID

        Returns:
            特征字典

        Raises:
            ValueError: 不支持的目标类型
        """
        extractors = {
            "student": self.extract_student_features,
            "topic": self.extract_topic_features,
            "proposal": self.extract_proposal_features,
            "midterm": self.extract_midterm_features,
            "thesis": self.extract_thesis_features,
            "review": self.extract_review_features,
        }

        if target_type not in extractors:
            raise ValueError(f"不支持的目标类型: {target_type}")

        return extractors[target_type](db, target_id)

    # ------------------------------------------------------------------
    # 特征向量化（用于孤立森林等多维算法）
    # ------------------------------------------------------------------
    @staticmethod
    def features_to_vector(
        features: Dict[str, Any],
        feature_keys: Optional[List[str]] = None,
    ) -> List[float]:
        """将特征字典转换为数值向量

        Args:
            features: 特征字典
            feature_keys: 需要提取的特征键列表，为 None 时使用默认键

        Returns:
            数值向量列表
        """
        if feature_keys is None:
            feature_keys = [
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

        vector: List[float] = []
        for key in feature_keys:
            value = features.get(key, 0.0)
            try:
                vector.append(float(value) if value is not None else 0.0)
            except (ValueError, TypeError):
                vector.append(0.0)

        return vector
