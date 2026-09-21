"""
统计分析 API
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, case
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.core.response import success_response
from app.core.security import require_admin, require_teacher_or_admin
from app.models.topic import Topic
from app.models.proposal import Proposal
from app.models.midterm import MidtermCheck
from app.models.thesis import ThesisVersion
from app.models.review import Review, Defense
from app.models.archive import Archive
from app.models.user import User
from app.models.anomaly import AnomalyRecord
from app.models.guidance import GuidanceRecord

router = APIRouter(prefix="/api/stats", tags=["统计分析"])


@router.get("/overview")
async def get_overview_stats(
    current_user=Depends(require_teacher_or_admin),
    db: Session = Depends(get_db)
):
    """获取概览统计数据"""
    # 学生总数
    student_count = db.query(User).filter(User.role == "student", User.status == 1).count()

    # 教师总数
    teacher_count = db.query(User).filter(User.role == "teacher", User.status == 1).count()

    # 选题统计
    topic_total = db.query(Topic).count()
    topic_approved = db.query(Topic).filter(Topic.status == "approved").count()
    topic_pending = db.query(Topic).filter(Topic.status == "pending").count()

    # 开题统计
    proposal_total = db.query(Proposal).count()
    proposal_approved = db.query(Proposal).filter(Proposal.status == "approved").count()

    # 中期检查统计
    midterm_total = db.query(MidtermCheck).count()
    midterm_passed = db.query(MidtermCheck).filter(MidtermCheck.status == "passed").count()

    # 论文版本统计
    version_total = db.query(ThesisVersion).count()

    # 评阅统计
    review_total = db.query(Review).count()
    review_completed = db.query(Review).filter(Review.status == "completed").count()

    # 答辩统计
    defense_total = db.query(Defense).count()
    defense_completed = db.query(Defense).filter(Defense.status == "completed").count()

    # 归档统计
    archive_total = db.query(Archive).count()
    archive_archived = db.query(Archive).filter(Archive.status == "archived").count()

    # 异常统计
    anomaly_total = db.query(AnomalyRecord).count()
    anomaly_L1 = db.query(AnomalyRecord).filter(AnomalyRecord.severity_level == "L1").count()
    anomaly_L2 = db.query(AnomalyRecord).filter(AnomalyRecord.severity_level == "L2").count()
    anomaly_L3 = db.query(AnomalyRecord).filter(AnomalyRecord.severity_level == "L3").count()
    anomaly_pending = db.query(AnomalyRecord).filter(AnomalyRecord.review_status == "pending").count()

    data = {
        "users": {
            "student_count": student_count,
            "teacher_count": teacher_count,
        },
        "topics": {
            "total": topic_total,
            "approved": topic_approved,
            "pending": topic_pending,
            "approved_rate": round(topic_approved / topic_total * 100, 1) if topic_total > 0 else 0,
        },
        "proposals": {
            "total": proposal_total,
            "approved": proposal_approved,
            "approved_rate": round(proposal_approved / proposal_total * 100, 1) if proposal_total > 0 else 0,
        },
        "midterm": {
            "total": midterm_total,
            "passed": midterm_passed,
            "passed_rate": round(midterm_passed / midterm_total * 100, 1) if midterm_total > 0 else 0,
        },
        "versions": {
            "total": version_total,
        },
        "reviews": {
            "total": review_total,
            "completed": review_completed,
            "completion_rate": round(review_completed / review_total * 100, 1) if review_total > 0 else 0,
        },
        "defenses": {
            "total": defense_total,
            "completed": defense_completed,
            "completion_rate": round(defense_completed / defense_total * 100, 1) if defense_total > 0 else 0,
        },
        "archives": {
            "total": archive_total,
            "archived": archive_archived,
            "archived_rate": round(archive_archived / archive_total * 100, 1) if archive_total > 0 else 0,
        },
        "anomalies": {
            "total": anomaly_total,
            "L1": anomaly_L1,
            "L2": anomaly_L2,
            "L3": anomaly_L3,
            "pending": anomaly_pending,
        }
    }

    return success_response(data)


@router.get("/topic-status-distribution")
async def get_topic_status_distribution(
    current_user=Depends(require_teacher_or_admin),
    db: Session = Depends(get_db)
):
    """选题状态分布"""
    results = db.query(
        Topic.status,
        func.count(Topic.id).label("count")
    ).group_by(Topic.status).all()

    status_map = {
        "pending": "待审核",
        "approved": "已确认",
        "rejected": "已拒绝",
        "withdrawn": "已撤回",
    }

    data = [
        {"status": status_map.get(r.status, r.status), "value": r.count, "key": r.status}
        for r in results
    ]

    return success_response(data)


@router.get("/progress-by-department")
async def get_progress_by_department(
    current_user=Depends(require_teacher_or_admin),
    db: Session = Depends(get_db)
):
    """各院系进度统计"""
    # 按院系统计学生数量和各环节完成情况
    students = db.query(User.department, func.count(User.id).label("student_count")) \
        .filter(User.role == "student", User.status == 1) \
        .group_by(User.department).all()

    result = []
    for dept in students:
        dept_students = db.query(User.id).filter(
            User.role == "student",
            User.department == dept.department,
            User.status == 1
        ).subquery()

        topic_count = db.query(Topic).filter(Topic.student_id.in_(dept_students)).count()
        proposal_count = db.query(Proposal).filter(Proposal.student_id.in_(dept_students)).count()
        midterm_count = db.query(MidtermCheck).filter(MidtermCheck.student_id.in_(dept_students)).count()
        archive_count = db.query(Archive).filter(Archive.student_id.in_(dept_students)).count()

        result.append({
            "department": dept.department or "未分配",
            "student_count": dept.student_count,
            "topic_count": topic_count,
            "proposal_count": proposal_count,
            "midterm_count": midterm_count,
            "archive_count": archive_count,
        })

    return success_response(result)


@router.get("/anomaly-trend")
async def get_anomaly_trend(
    days: int = Query(default=7, ge=1, le=30),
    current_user=Depends(require_teacher_or_admin),
    db: Session = Depends(get_db)
):
    """异常检测趋势（近 N 天）"""
    from datetime import datetime, timedelta

    end_date = datetime.now()
    start_date = end_date - timedelta(days=days - 1)

    # 按天统计
    results = db.query(
        func.date(AnomalyRecord.detection_time).label("date"),
        AnomalyRecord.severity_level,
        func.count(AnomalyRecord.id).label("count")
    ).filter(
        AnomalyRecord.detection_time >= start_date
    ).group_by(
        func.date(AnomalyRecord.detection_time),
        AnomalyRecord.severity_level
    ).all()

    # 构造完整日期范围
    date_list = [(start_date + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)]
    trend_data = {}

    for d in date_list:
        trend_data[d] = {"date": d, "total": 0, "L1": 0, "L2": 0, "L3": 0}

    for r in results:
        date_str = str(r.date)
        if date_str in trend_data:
            trend_data[date_str][r.severity_level] = r.count
            trend_data[date_str]["total"] += r.count

    data = list(trend_data.values())
    return success_response(data)


@router.get("/guidance-stats")
async def get_guidance_stats(
    current_user=Depends(require_teacher_or_admin),
    db: Session = Depends(get_db)
):
    """指导统计"""
    # 总指导次数
    total_records = db.query(GuidanceRecord).count()

    # 按教师统计
    teacher_stats = db.query(
        User.real_name.label("teacher_name"),
        func.count(GuidanceRecord.id).label("record_count")
    ).join(
        GuidanceRecord, GuidanceRecord.teacher_id == User.id
    ).filter(
        User.role == "teacher"
    ).group_by(User.id, User.real_name).order_by(func.count(GuidanceRecord.id).desc()).limit(10).all()

    # 按指导方式统计
    method_stats = db.query(
        GuidanceRecord.method,
        func.count(GuidanceRecord.id).label("count")
    ).group_by(GuidanceRecord.method).all()

    data = {
        "total_records": total_records,
        "teacher_ranking": [
            {"teacher_name": r.teacher_name, "record_count": r.record_count}
            for r in teacher_stats
        ],
        "method_distribution": [
            {"method": r.method or "unknown", "count": r.count}
            for r in method_stats
        ]
    }

    return success_response(data)


@router.get("/score-distribution")
async def get_score_distribution(
    current_user=Depends(require_teacher_or_admin),
    db: Session = Depends(get_db)
):
    """成绩分布统计"""
    # 中期检查成绩分布
    midterm_scores = db.query(MidtermCheck.final_score).filter(
        MidtermCheck.status == "passed",
        MidtermCheck.final_score > 0
    ).all()

    # 答辩成绩分布
    defense_scores = db.query(Defense.total_score).filter(
        Defense.status == "completed",
        Defense.total_score > 0
    ).all()

    def calc_distribution(scores):
        """计算成绩分段分布"""
        ranges = [
            {"label": "优秀(90-100)", "min": 90, "max": 100, "count": 0},
            {"label": "良好(80-89)", "min": 80, "max": 89.99, "count": 0},
            {"label": "中等(70-79)", "min": 70, "max": 79.99, "count": 0},
            {"label": "及格(60-69)", "min": 60, "max": 69.99, "count": 0},
            {"label": "不及格(<60)", "min": 0, "max": 59.99, "count": 0},
        ]
        for (score,) in scores:
            for r in ranges:
                if r["min"] <= score <= r["max"]:
                    r["count"] += 1
                    break
        return ranges

    data = {
        "midterm_distribution": calc_distribution(midterm_scores),
        "defense_distribution": calc_distribution(defense_scores),
    }

    return success_response(data)
