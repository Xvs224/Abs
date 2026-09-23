"""
统计分析 API
- 管理员：全局数据
- 教师：仅看到自己负责的学生相关数据
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, case
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

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

router = APIRouter(prefix="/api/stats", tags=["统计分析"])


def _get_teacher_student_ids(db: Session, teacher_id: int):
    """获取教师负责的所有学生ID（通过选题表 teacher_id 关联）"""
    rows = db.query(Topic.student_id).filter(Topic.teacher_id == teacher_id).distinct().all()
    return [r[0] for r in rows]


def _get_teacher_topic_ids(db: Session, teacher_id: int):
    """获取教师负责的所有选题ID"""
    rows = db.query(Topic.id).filter(Topic.teacher_id == teacher_id).all()
    return [r[0] for r in rows]


@router.get("/overview")
async def get_overview_stats(
    current_user=Depends(require_teacher_or_admin),
    db: Session = Depends(get_db)
):
    """获取概览统计数据 — 教师仅看自己负责的学生"""
    is_admin = current_user.role == "admin"

    if is_admin:
        student_count = db.query(User).filter(User.role == "student", User.status == 1).count()
        teacher_count = db.query(User).filter(User.role == "teacher", User.status == 1).count()

        topic_q = db.query(Topic)
        proposal_q = db.query(Proposal)
        midterm_q = db.query(MidtermCheck)
        version_q = db.query(ThesisVersion)
        review_q = db.query(Review)
        defense_q = db.query(Defense)
        archive_q = db.query(Archive)
        anomaly_q = db.query(AnomalyRecord)
    else:
        student_ids = _get_teacher_student_ids(db, current_user.id)
        topic_ids = _get_teacher_topic_ids(db, current_user.id)

        student_count = len(student_ids)
        teacher_count = 1

        topic_q = db.query(Topic).filter(Topic.teacher_id == current_user.id)
        proposal_q = db.query(Proposal).filter(Proposal.student_id.in_(student_ids)) if student_ids else db.query(Proposal).filter(False)
        midterm_q = db.query(MidtermCheck).filter(MidtermCheck.student_id.in_(student_ids)) if student_ids else db.query(MidtermCheck).filter(False)
        version_q = db.query(ThesisVersion).filter(ThesisVersion.topic_id.in_(topic_ids)) if topic_ids else db.query(ThesisVersion).filter(False)
        review_q = db.query(Review).filter(Review.student_id.in_(student_ids)) if student_ids else db.query(Review).filter(False)
        defense_q = db.query(Defense).filter(Defense.student_id.in_(student_ids)) if student_ids else db.query(Defense).filter(False)
        archive_q = db.query(Archive).filter(Archive.student_id.in_(student_ids)) if student_ids else db.query(Archive).filter(False)
        anomaly_q = db.query(AnomalyRecord).filter(AnomalyRecord.student_id.in_(student_ids)) if student_ids else db.query(AnomalyRecord).filter(False)

    topic_total = topic_q.count()
    topic_approved = topic_q.filter(Topic.status == "approved").count()
    topic_pending = topic_q.filter(Topic.status == "pending").count()

    proposal_total = proposal_q.count()
    proposal_approved = proposal_q.filter(Proposal.status == "approved").count()

    midterm_total = midterm_q.count()
    midterm_passed = midterm_q.filter(MidtermCheck.status == "passed").count()

    version_total = version_q.count()

    review_total = review_q.count()
    review_completed = review_q.filter(Review.status == "completed").count()

    defense_total = defense_q.count()
    defense_completed = defense_q.filter(Defense.status == "completed").count()

    archive_total = archive_q.count()
    archive_archived = archive_q.filter(Archive.status == "archived").count()

    anomaly_total = anomaly_q.count()
    anomaly_L1 = anomaly_q.filter(AnomalyRecord.severity_level == "L1").count()
    anomaly_L2 = anomaly_q.filter(AnomalyRecord.severity_level == "L2").count()
    anomaly_L3 = anomaly_q.filter(AnomalyRecord.severity_level == "L3").count()
    anomaly_pending = anomaly_q.filter(AnomalyRecord.review_status == "pending").count()

    data = {
        "scope": "global" if is_admin else "teacher",
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
    """选题状态分布 — 教师仅看自己的选题"""
    query = db.query(
        Topic.status,
        func.count(Topic.id).label("count")
    )

    if current_user.role != "admin":
        query = query.filter(Topic.teacher_id == current_user.id)

    results = query.group_by(Topic.status).all()

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
    current_user=Depends(require_admin),
    db: Session = Depends(get_db)
):
    """各院系进度统计 — 仅管理员"""
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
    """异常检测趋势 — 教师仅看自己学生的异常"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days - 1)

    query = db.query(
        func.date(AnomalyRecord.detection_time).label("date"),
        AnomalyRecord.severity_level,
        func.count(AnomalyRecord.id).label("count")
    ).filter(AnomalyRecord.detection_time >= start_date)

    if current_user.role != "admin":
        student_ids = _get_teacher_student_ids(db, current_user.id)
        if student_ids:
            query = query.filter(AnomalyRecord.student_id.in_(student_ids))
        else:
            query = query.filter(False)

    results = query.group_by(
        func.date(AnomalyRecord.detection_time),
        AnomalyRecord.severity_level
    ).all()

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


@router.get("/score-distribution")
async def get_score_distribution(
    current_user=Depends(require_teacher_or_admin),
    db: Session = Depends(get_db)
):
    """成绩分布统计 — 教师仅看自己学生"""
    if current_user.role == "admin":
        midterm_scores = db.query(MidtermCheck.final_score).filter(
            MidtermCheck.status == "passed",
            MidtermCheck.final_score > 0
        ).all()
        defense_scores = db.query(Defense.total_score).filter(
            Defense.status == "completed",
            Defense.total_score > 0
        ).all()
    else:
        student_ids = _get_teacher_student_ids(db, current_user.id)
        if student_ids:
            midterm_scores = db.query(MidtermCheck.final_score).filter(
                MidtermCheck.status == "passed",
                MidtermCheck.final_score > 0,
                MidtermCheck.student_id.in_(student_ids)
            ).all()
            defense_scores = db.query(Defense.total_score).filter(
                Defense.status == "completed",
                Defense.total_score > 0,
                Defense.student_id.in_(student_ids)
            ).all()
        else:
            midterm_scores = []
            defense_scores = []

    def calc_distribution(scores):
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
