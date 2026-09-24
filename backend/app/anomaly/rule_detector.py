"""
规则类异常检测器

这类异常基于业务规则直接判定（无需 IQR/Isolation Forest），
比如：是否超期、附件是否缺失、分数是否为 0、是否跳过阶段等。
规则检测结果同样写入 anomaly_records，detection_type='rule'。
"""
from typing import List, Dict, Any
from datetime import datetime, date
import logging

from sqlalchemy.orm import Session

from app.models.user import User
from app.models.topic import Topic
from app.models.proposal import Proposal
from app.models.midterm import MidtermCheck, Rectification
from app.models.thesis import ThesisVersion
from app.models.review import Review, Defense
from app.models.archive import Archive
from app.models.stage_config import StageConfig
from app.models.guidance import GuidanceRecord

logger = logging.getLogger(__name__)


def _days_between(a: datetime, b: datetime) -> float:
    return abs((b - a).total_seconds() / 86400)


def detect_rules_for_student(db: Session, student_id: int) -> List[Dict[str, Any]]:
    """对一个学生跑全部规则类检测，返回异常列表。"""
    now = datetime.now()
    anomalies: List[Dict[str, Any]] = []

    # -------- 选题 --------
    topic = db.query(Topic).filter(Topic.student_id == student_id).first()
    if topic:
        topic_cfg = db.query(StageConfig).filter(StageConfig.module_key == "topic").first()
        if topic_cfg and topic.submit_time and topic.submit_time > topic_cfg.end_time:
            anomalies.append({
                "target_type": "topic", "target_id": topic.id,
                "student_id": student_id, "teacher_id": topic.teacher_id,
                "feature_name": "topic_submit_overdue",
                "feature_value": _days_between(topic.submit_time, topic_cfg.end_time),
                "anomaly_score": 0.85, "severity_level": "L2",
                "description": f"选题于 {topic.submit_time:%Y-%m-%d} 提交，已超过选题阶段结束时间 {topic_cfg.end_time:%Y-%m-%d}（超出 {_days_between(topic.submit_time, topic_cfg.end_time):.1f} 天）",
                "suggestion": "联系管理员开放选题阶段后重新提交",
            })

        if topic.reject_reason and (topic.reject_count or 0) >= 2:
            anomalies.append({
                "target_type": "topic", "target_id": topic.id,
                "student_id": student_id, "teacher_id": topic.teacher_id,
                "feature_name": "topic_reject_count",
                "feature_value": topic.reject_count or 0,
                "anomaly_score": 0.7, "severity_level": "L1",
                "description": f"选题已被驳回 {topic.reject_count or 0} 次，反复修改无法通过",
                "suggestion": "学生可考虑更换选题方向",
            })

    # -------- 开题 --------
    proposal = db.query(Proposal).filter(Proposal.student_id == student_id).first()
    if proposal:
        p_cfg = db.query(StageConfig).filter(StageConfig.module_key == "proposal").first()
        if p_cfg and proposal.submit_time and proposal.submit_time > p_cfg.end_time:
            anomalies.append({
                "target_type": "proposal", "target_id": proposal.id,
                "student_id": student_id,
                "feature_name": "proposal_submit_overdue",
                "feature_value": _days_between(proposal.submit_time, p_cfg.end_time),
                "anomaly_score": 0.85, "severity_level": "L2",
                "description": f"开题报告超期提交（超出 {_days_between(proposal.submit_time, p_cfg.end_time):.1f} 天）",
                "suggestion": "提醒学生尽快完成开题报告",
            })

    # -------- 中期检查 --------
    midterm = db.query(MidtermCheck).filter(MidtermCheck.student_id == student_id).first()
    if midterm:
        m_cfg = db.query(StageConfig).filter(StageConfig.module_key == "midterm").first()
        if m_cfg and midterm.submit_time and midterm.submit_time > m_cfg.end_time:
            anomalies.append({
                "target_type": "midterm", "target_id": midterm.id,
                "student_id": student_id, "teacher_id": midterm.teacher_id,
                "feature_name": "midterm_submit_overdue",
                "feature_value": _days_between(midterm.submit_time, m_cfg.end_time),
                "anomaly_score": 0.9, "severity_level": "L2",
                "description": f"中期检查超期提交（超出 {_days_between(midterm.submit_time, m_cfg.end_time):.1f} 天）",
                "suggestion": "按流程中期检查必须在阶段截止前完成",
            })

        if midterm.progress_percentage is not None and midterm.progress_percentage < 30 \
           and (midterm.status not in ("draft", "form_submitted")):
            anomalies.append({
                "target_type": "midterm", "target_id": midterm.id,
                "student_id": student_id, "teacher_id": midterm.teacher_id,
                "feature_name": "midterm_progress_low",
                "feature_value": midterm.progress_percentage,
                "anomaly_score": 0.75, "severity_level": "L1",
                "description": f"中期研究进度仅 {midterm.progress_percentage:.0f}%，严重偏低",
                "suggestion": "教师应督促学生加快研究进度",
            })

        # 整改次数过多
        rect_count = db.query(Rectification).filter(Rectification.midterm_id == midterm.id).count()
        if rect_count >= 2:
            anomalies.append({
                "target_type": "midterm", "target_id": midterm.id,
                "student_id": student_id, "teacher_id": midterm.teacher_id,
                "feature_name": "midterm_rectification_count",
                "feature_value": rect_count,
                "anomaly_score": 0.7, "severity_level": "L1",
                "description": f"中期整改 {rect_count} 次，多次整改依旧不合格",
                "suggestion": "教师应针对性调整指导方向",
            })

    # -------- 论文版本 --------
    if topic:
        versions = db.query(ThesisVersion).filter(ThesisVersion.topic_id == topic.id).order_by(ThesisVersion.version_num.asc()).all()
        if versions:
            version_nums = [v.version_num or i + 1 for i, v in enumerate(versions)]
            expected = list(range(1, max(version_nums) + 1))
            missing = set(expected) - set(version_nums)
            # 缺初稿直接终稿
            if missing and 1 not in version_nums:
                anomalies.append({
                    "target_type": "thesis", "target_id": versions[-1].id,
                    "student_id": student_id, "teacher_id": topic.teacher_id,
                    "feature_name": "thesis_version_skip",
                    "feature_value": len(missing),
                    "anomaly_score": 0.85, "severity_level": "L2",
                    "description": f"跳过必要写作阶段：缺少版本 {sorted(missing)}，疑似无初稿直接终稿",
                    "suggestion": "要求学生补齐初稿版本再提交终稿",
                })

    # -------- 评阅答辩 --------
    if topic:
        defense = db.query(Defense).filter(Defense.topic_id == topic.id).first()
        if defense and defense.status == "completed":
            # 答辩总分为 0
            if (defense.total_score or 0) == 0:
                anomalies.append({
                    "target_type": "defense", "target_id": defense.id,
                    "student_id": student_id, "teacher_id": topic.teacher_id,
                    "feature_name": "defense_score_zero",
                    "feature_value": 0,
                    "anomaly_score": 1.0, "severity_level": "L3",
                    "description": "答辩已完成但总分为 0，疑似评分未录入",
                    "suggestion": "通知答辩委员会核实评分数据并补录",
                })

            # 评阅意见为空
            reviews = db.query(Review).filter(Review.topic_id == topic.id, Review.status == "completed").all()
            empty_opinion = [r for r in reviews if not (r.opinion or "")]
            if empty_opinion:
                anomalies.append({
                    "target_type": "review", "target_id": empty_opinion[0].id,
                    "student_id": student_id, "teacher_id": topic.teacher_id,
                    "feature_name": "review_opinion_empty",
                    "feature_value": len(empty_opinion),
                    "anomaly_score": 0.6, "severity_level": "L1",
                    "description": f"{len(empty_opinion)} 份评阅仅有分数，无评审文字意见",
                    "suggestion": "提醒评阅教师补充文字意见",
                })

    # -------- 归档 --------
    if topic:
        archive = db.query(Archive).filter(Archive.topic_id == topic.id).first()
        if archive:
            a_cfg = db.query(StageConfig).filter(StageConfig.module_key == "archive").first()
            if a_cfg and archive.create_time and archive.create_time > a_cfg.end_time:
                anomalies.append({
                    "target_type": "archive", "target_id": archive.id,
                    "student_id": student_id, "teacher_id": archive.teacher_id,
                    "feature_name": "archive_submit_overdue",
                    "feature_value": _days_between(archive.create_time, a_cfg.end_time),
                    "anomaly_score": 0.85, "severity_level": "L2",
                    "description": f"归档材料超期提交（超出 {_days_between(archive.create_time, a_cfg.end_time):.1f} 天）",
                    "suggestion": "归档流程具有法律效力，务必在阶段结束前完成",
                })

            missing_items = 0
            for field in ("thesis_file", "proposal_file", "midterm_file", "defense_file"):
                if not getattr(archive, field):
                    missing_items += 1
            if missing_items >= 2:
                anomalies.append({
                    "target_type": "archive", "target_id": archive.id,
                    "student_id": student_id, "teacher_id": archive.teacher_id,
                    "feature_name": "archive_missing_materials",
                    "feature_value": missing_items,
                    "anomaly_score": 0.75, "severity_level": "L2",
                    "description": f"归档缺少 {missing_items} 项必要材料",
                    "suggestion": "通知学生补齐归档材料",
                })

    # -------- 过程指导记录 --------
    if topic:
        records = db.query(GuidanceRecord).filter(
            GuidanceRecord.topic_id == topic.id
        ).order_by(GuidanceRecord.guidance_time.asc()).all()
        teacher_id = topic.teacher_id

        # 规则1: 指导次数过少（选题通过至今 > 21 天但指导记录 < 3 次）
        if topic.submit_time and (now - topic.submit_time).days >= 21 and len(records) < 3:
            anomalies.append({
                "target_type": "guidance", "target_id": topic.id,
                "student_id": student_id, "teacher_id": teacher_id,
                "feature_name": "guidance_count_too_few",
                "feature_value": len(records),
                "anomaly_score": 0.8, "severity_level": "L2",
                "description": f"选题已通过 {(now - topic.submit_time).days} 天，但过程指导记录仅 {len(records)} 次（建议不少于 3 次）",
                "suggestion": "提醒指导教师加强对学生论文写作过程的指导",
            })

        # 规则2: 距上次指导间隔过长（> 14 天且未归档）
        if records:
            last = records[-1]
            if last.guidance_time and (now - last.guidance_time).days > 14:
                anomalies.append({
                    "target_type": "guidance", "target_id": last.id,
                    "student_id": student_id, "teacher_id": teacher_id,
                    "feature_name": "guidance_interval_too_long",
                    "feature_value": (now - last.guidance_time).days,
                    "anomaly_score": 0.7, "severity_level": "L1",
                    "description": f"距上次指导已超过 {(now - last.guidance_time).days} 天，指导间隔过长",
                    "suggestion": "建议指导教师本周内与学生进行一次指导交流",
                })

        # 规则3: 指导内容过短（疑似应付）
        for r in records:
            content_len = len((r.content or "").strip())
            if content_len > 0 and content_len < 10:
                anomalies.append({
                    "target_type": "guidance", "target_id": r.id,
                    "student_id": student_id, "teacher_id": teacher_id,
                    "feature_name": "guidance_content_too_short",
                    "feature_value": content_len,
                    "anomaly_score": 0.55, "severity_level": "L1",
                    "description": f"指导记录内容仅 {content_len} 字，疑似应付式记录",
                    "suggestion": "指导记录应包含具体指导内容与反馈，避免只写'简单指导'等敷衍表述",
                })

        # 规则4: 学生未回复指导超过 7 天
        for r in records:
            if r.status == "pending" and r.guidance_time and (now - r.guidance_time).days > 7:
                anomalies.append({
                    "target_type": "guidance", "target_id": r.id,
                    "student_id": student_id, "teacher_id": teacher_id,
                    "feature_name": "guidance_no_reply_overdue",
                    "feature_value": (now - r.guidance_time).days,
                    "anomaly_score": 0.75, "severity_level": "L2",
                    "description": f"指导记录已发布 {(now - r.guidance_time).days} 天，学生仍未回复",
                    "suggestion": "提醒学生及时阅读并回复指导意见",
                })

    return anomalies


def detect_rules_batch(db: Session) -> List[Dict[str, Any]]:
    """对所有学生跑规则类检测。"""
    students = db.query(User).filter(User.role == "student").all()
    all_anomalies: List[Dict[str, Any]] = []
    for s in students:
        try:
            all_anomalies.extend(detect_rules_for_student(db, s.id))
        except Exception as e:
            logger.warning(f"规则检测 student={s.id} 失败: {e}")
    return all_anomalies
