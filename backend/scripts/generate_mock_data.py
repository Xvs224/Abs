"""
生成模拟/脱敏测试数据
按照最小必要原则，不收集与业务无关的个人信息
"""
import sys
import os
import random
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.core.security import hash_password
from app.models.user import User
from app.models.topic import Topic
from app.models.proposal import Proposal
from app.models.midterm import MidtermCheck, Rectification
from app.models.thesis import ThesisVersion, FormatCheck
from app.models.review import Review, Defense
from app.models.archive import Archive
from app.models.anomaly import AnomalyRecord

# 院系列表
DEPARTMENTS = ["计算机学院", "软件工程学院", "人工智能学院", "信息工程学院"]
MAJORS = {
    "计算机学院": ["计算机科学与技术", "网络工程"],
    "软件工程学院": ["软件工程", "软件测试"],
    "人工智能学院": ["人工智能", "数据科学与大数据"],
    "信息工程学院": ["电子信息工程", "通信工程"],
}

# 题目关键词
TOPIC_KEYWORDS = [
    "基于深度学习的图像识别研究",
    "基于区块链的供应链溯源系统设计",
    "基于微服务架构的在线教育平台",
    "基于自然语言处理的文本分类研究",
    "基于大数据的用户行为分析系统",
    "基于物联网的智能家居控制系统",
    "基于云计算的企业资源管理系统",
    "基于机器学习的推荐算法研究",
    "基于计算机视觉的人脸识别系统",
    "基于知识图谱的智能问答系统",
    "基于WebGL的三维可视化引擎开发",
    "基于移动端的健康管理APP设计",
    "基于5G的远程医疗系统研究",
    "基于数据挖掘的金融风险预警",
    "基于VR的虚拟实验室开发",
    "基于边缘计算的智慧城市应用",
    "基于隐私计算的数据共享平台",
    "基于低代码平台的企业应用开发",
    "基于数字孪生的工业监控系统",
    "基于AIGC的内容创作辅助工具",
]

TOPIC_DIRECTIONS = ["人工智能", "大数据", "软件工程", "网络安全", "云计算", "物联网", "区块链"]
TOPIC_SOURCES = ["教师科研项目", "企业实际项目", "学生自选", "实验室课题"]
DIFFICULTIES = ["easy", "medium", "hard"]
WORKLOADS = ["light", "medium", "heavy"]


def generate_mock_data(student_count: int = 50):
    """生成模拟数据"""
    db = SessionLocal()
    try:
        print("开始生成模拟数据...")

        # 1. 生成教师
        teachers = _generate_teachers(db, 10)
        print(f"生成教师: {len(teachers)} 人")

        # 2. 生成学生
        students = _generate_students(db, student_count)
        print(f"生成学生: {len(students)} 人")

        # 3. 生成选题
        topics = _generate_topics(db, students, teachers)
        print(f"生成选题: {len(topics)} 个")

        # 4. 生成开题报告
        proposals = _generate_proposals(db, topics)
        print(f"生成开题报告: {len(proposals)} 个")

        # 5. 生成中期检查
        midterms, rectifications = _generate_midterm(db, topics)
        print(f"生成中期检查: {len(midterms)} 个, 整改记录: {len(rectifications)} 条")

        # 6. 生成论文版本和格式检测
        versions, format_checks = _generate_thesis_versions(db, topics)
        print(f"生成论文版本: {len(versions)} 个, 格式检测记录: {len(format_checks)} 条")

        # 8. 生成评阅和答辩
        reviews, defenses = _generate_reviews_and_defense(db, topics, teachers, versions)
        print(f"生成评阅记录: {len(reviews)} 条, 答辩安排: {len(defenses)} 个")

        # 9. 生成归档（部分完成的）
        archives = _generate_archives(db, topics, versions)
        print(f"生成归档记录: {len(archives)} 条")

        # 10. 生成一些异常记录
        anomalies = _generate_anomaly_records(db, topics, students)
        print(f"生成异常记录: {len(anomalies)} 条")

        db.commit()
        print("模拟数据生成完成!")

    except Exception as e:
        db.rollback()
        print(f"生成数据失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def _generate_teachers(db, count: int):
    """生成教师"""
    # 获取已有教师
    existing_teachers = db.query(User).filter(User.role == "teacher").all()
    existing_usernames = {t.username for t in existing_teachers}
    teachers = list(existing_teachers)

    surnames = ["张", "李", "王", "刘", "陈", "杨", "赵", "黄", "周", "吴"]
    names = ["建国", "志明", "秀英", "伟强", "美玲", "俊杰", "丽华", "文博", "思远", "雅婷"]

    i = 0
    while len(teachers) < count:
        i += 1
        username = f"teacher{i:02d}"
        if username in existing_usernames:
            continue

        dept = random.choice(DEPARTMENTS)
        teacher = User(
            username=username,
            password_hash=hash_password("teacher123"),
            real_name=f"{surnames[i % len(surnames)]}{names[i % len(names)]}",
            role="teacher",
            email=f"teacher{i:02d}@example.com",
            department=dept,
            teacher_no=f"T2024{i:03d}",
            status=1,
        )
        db.add(teacher)
        teachers.append(teacher)
        existing_usernames.add(username)

    db.flush()
    return teachers


def _generate_students(db, count: int):
    """生成学生"""
    # 获取已有学生
    existing_students = db.query(User).filter(User.role == "student").all()
    existing_usernames = {s.username for s in existing_students}
    students = list(existing_students)

    if len(students) >= count:
        return students[:count]

    surnames = ["王", "李", "张", "刘", "陈", "杨", "赵", "黄", "周", "吴",
                "徐", "孙", "马", "朱", "胡", "林", "郭", "何", "高", "罗"]
    names = ["伟", "芳", "娜", "敏", "静", "强", "磊", "军", "洋", "勇",
             "艳", "杰", "涛", "明", "超", "秀英", "霞", "平", "刚", "桂英"]

    i = 0
    while len(students) < count:
        i += 1
        username = f"student{i:03d}"
        if username in existing_usernames:
            continue

        dept = random.choice(DEPARTMENTS)
        major = random.choice(MAJORS[dept])
        student = User(
            username=username,
            password_hash=hash_password("student123"),
            real_name=f"{surnames[i % len(surnames)]}{names[i % len(names)]}",
            role="student",
            email=f"student{i:03d}@example.com",
            department=dept,
            student_no=f"2021{i:05d}",
            grade="2021",
            major=major,
            status=1,
        )
        db.add(student)
        students.append(student)
        existing_usernames.add(username)

    db.flush()
    return students


def _generate_topics(db, students, teachers):
    """生成选题"""
    topics = []
    statuses = ["approved", "approved", "approved", "pending", "rejected"]  # 加权

    for i, student in enumerate(students):
        # 为每个学生分配一个指导教师（从同学院的教师中选）
        dept_teachers = [t for t in teachers if t.department == student.department]
        if not dept_teachers:
            dept_teachers = teachers
        teacher = random.choice(dept_teachers)

        topic = Topic(
            student_id=student.id,
            teacher_id=teacher.id,
            title=f"《{random.choice(TOPIC_KEYWORDS)}》",
            direction=random.choice(TOPIC_DIRECTIONS),
            background="本研究旨在探讨相关领域的关键问题，具有重要的理论意义和实践价值。",
            significance="通过本研究，可以推动相关技术的发展，为实际应用提供理论支撑和技术方案。",
            keywords=random.choice(TOPIC_DIRECTIONS) + ", " + random.choice(TOPIC_DIRECTIONS),
            source=random.choice(TOPIC_SOURCES),
            difficulty=random.choice(DIFFICULTIES),
            workload=random.choice(WORKLOADS),
            status=random.choice(statuses),
            submit_time=datetime.now() - timedelta(days=random.randint(60, 120)),
        )
        db.add(topic)
        topics.append(topic)

    db.flush()
    return topics


def _generate_proposals(db, topics):
    """生成开题报告"""
    proposals = []
    # 只为已确认的选题生成开题报告
    approved_topics = [t for t in topics if t.status == "approved"]

    for topic in approved_topics:
        # 随机状态
        rand = random.random()
        if rand < 0.7:
            status = "approved"
        elif rand < 0.9:
            status = "submitted"
        else:
            status = "rejected"

        word_count = random.randint(2000, 8000)

        proposal = Proposal(
            topic_id=topic.id,
            student_id=topic.student_id,
            teacher_id=topic.teacher_id,
            research_content="本文主要研究内容包括以下几个方面：1）理论基础研究；2）关键技术探讨；3）系统设计与实现；4）实验验证与分析。",
            research_method="采用文献研究法、实验法、对比分析法等多种研究方法，确保研究的科学性和可靠性。",
            technical_route="从需求分析出发，经过系统设计、编码实现、测试验证等阶段，最终完成系统开发。",
            expected_results="预期完成一个完整的原型系统，并发表相关学术论文1-2篇。",
            schedule_plan="第1-2周：选题与资料收集；第3-4周：开题报告；第5-8周：系统设计；第9-12周：编码实现；第13-14周：测试与优化；第15-16周：论文撰写与答辩。",
            word_count=word_count,
            status=status,
            submit_time=topic.submit_time + timedelta(days=random.randint(7, 14)),
            review_time=topic.submit_time + timedelta(days=random.randint(14, 21)) if status in ["approved", "rejected"] else None,
        )
        db.add(proposal)
        proposals.append(proposal)

    db.flush()
    return proposals


def _generate_midterm(db, topics):
    """生成中期检查和整改记录"""
    midterms = []
    rectifications = []

    approved_topics = [t for t in topics if t.status == "approved"]
    # 约70%的学生有中期检查
    selected = random.sample(approved_topics, k=int(len(approved_topics) * 0.7))

    for topic in selected:
        progress = random.randint(30, 95)
        score = random.randint(60, 95)

        rand = random.random()
        if rand < 0.6:
            status = "passed"
        elif rand < 0.8:
            status = "rectifying"
        elif rand < 0.9:
            status = "failed"
        else:
            status = "submitted"

        midterm = MidtermCheck(
            topic_id=topic.id,
            student_id=topic.student_id,
            teacher_id=topic.teacher_id,
            progress_description=f"目前已完成约{progress}%的研究工作，主要工作包括...",
            completed_work="已完成需求分析、系统设计和核心模块开发工作。",
            remaining_work="剩余工作包括系统测试、优化和论文撰写。",
            progress_percentage=progress,
            existing_problems="部分功能模块还需要进一步完善，实验数据还需补充。",
            next_plan="接下来将继续完善系统功能，补充实验数据，撰写论文。",
            teacher_score=score + random.randint(-5, 5),
            teacher_opinion="学生态度认真，进展基本符合预期。",
            check_group_score=score,
            check_group_opinion="中期检查通过，建议继续按计划推进。",
            final_score=score,
            status=status,
            submit_time=datetime.now() - timedelta(days=random.randint(20, 40)),
            check_time=datetime.now() - timedelta(days=random.randint(10, 20)),
        )
        db.add(midterm)
        midterms.append(midterm)
        db.flush()

        # 为部分中期检查生成整改记录
        if status in ["rectifying", "failed"] and random.random() > 0.3:
            rect = Rectification(
                midterm_id=midterm.id,
                topic_id=topic.id,
                problem_description="研究进度滞后，部分关键模块尚未完成。",
                requirement="请在两周内完成剩余模块开发，并提交整改报告。",
                deadline=datetime.now().date() + timedelta(days=random.randint(5, 15)),
                rectification_content="已按照要求完成整改，补充了相关模块功能。" if status == "rectifying" else "",
                status=random.choice(["pending", "submitted", "passed"]) if status == "rectifying" else "pending",
            )
            db.add(rect)
            rectifications.append(rect)

    db.flush()
    return midterms, rectifications


def _generate_thesis_versions(db, topics):
    """生成论文版本和格式检测"""
    versions = []
    format_checks = []

    approved_topics = [t for t in topics if t.status == "approved"]
    # 约60%的学生有论文版本
    selected = random.sample(approved_topics, k=int(len(approved_topics) * 0.6))

    for topic in selected:
        version_count = random.randint(1, 5)
        for v in range(1, version_count + 1):
            word_count = random.randint(5000, 20000)
            format_score = random.randint(60, 100)

            version = ThesisVersion(
                topic_id=topic.id,
                student_id=topic.student_id,
                version_num=v,
                version_name=f"第{v}版" if v > 1 else "初稿",
                change_log="根据指导意见修改完善" if v > 1 else "初稿提交",
                file_path=f"/uploads/thesis/{topic.id}/version_{v}.docx",
                file_name=f"毕业论文_第{v}版.docx",
                file_size=random.randint(500000, 3000000),
                file_type="docx",
                word_count=word_count + v * 500,
                page_count=random.randint(20, 60),
                chapter_count=random.randint(5, 8),
                reference_count=random.randint(20, 50),
                format_check_status="done",
                format_score=format_score,
                submit_time=datetime.now() - timedelta(days=random.randint(5, 30) - v * 3),
            )
            db.add(version)
            versions.append(version)
            db.flush()

            # 生成格式检测记录
            total_items = 10
            passed_count = int(format_score / 10)
            failed_count = total_items - passed_count

            check_items = {
                "title_format": {"passed": True, "message": "标题格式正确", "score": 10, "max_score": 10},
                "abstract_format": {"passed": format_score > 70, "message": "摘要格式" + ("正确" if format_score > 70 else "需调整"), "score": 8 if format_score > 70 else 5, "max_score": 10},
                "toc_format": {"passed": True, "message": "目录格式正确", "score": 10, "max_score": 10},
                "chapter_format": {"passed": format_score > 65, "message": "章节格式" + ("规范" if format_score > 65 else "存在问题"), "score": 9 if format_score > 65 else 6, "max_score": 10},
                "references_format": {"passed": format_score > 75, "message": "参考文献格式" + ("规范" if format_score > 75 else "不规范"), "score": 9 if format_score > 75 else 4, "max_score": 10},
                "formula_format": {"passed": True, "message": "公式格式正确", "score": 10, "max_score": 10},
                "table_format": {"passed": format_score > 80, "message": "表格格式" + ("规范" if format_score > 80 else "需调整"), "score": 9 if format_score > 80 else 6, "max_score": 10},
                "figure_format": {"passed": True, "message": "图表格式正确", "score": 10, "max_score": 10},
                "page_number_format": {"passed": True, "message": "页码格式正确", "score": 10, "max_score": 10},
                "appendix_format": {"passed": format_score > 85, "message": "附录格式" + ("正确" if format_score > 85 else "需完善"), "score": 8 if format_score > 85 else 5, "max_score": 10},
            }

            fc = FormatCheck(
                version_id=version.id,
                topic_id=topic.id,
                check_items=check_items,
                total_score=format_score,
                max_score=100.0,
                passed_count=passed_count,
                failed_count=failed_count,
                total_items=total_items,
                overall_result="pass" if format_score >= 70 else "fail",
                problems_summary="" if format_score >= 80 else "存在部分格式问题，建议修改。",
                suggestions="请按照学校毕业论文格式规范进行调整。",
                check_time=version.submit_time + timedelta(hours=random.randint(1, 24)),
            )
            db.add(fc)
            format_checks.append(fc)

    db.flush()
    return versions, format_checks


def _generate_reviews_and_defense(db, topics, teachers, versions):
    """生成评阅和答辩"""
    reviews = []
    defenses = []

    # 为有论文版本的选题生成评阅
    topic_ids_with_versions = set(v.topic_id for v in versions)
    topics_with_versions = [t for t in topics if t.id in topic_ids_with_versions]

    # 约50%有评阅
    selected = random.sample(topics_with_versions, k=min(len(topics_with_versions), int(len(topics_with_versions) * 0.5)))

    for topic in selected:
        # 分配评阅教师（不是指导教师）
        other_teachers = [t for t in teachers if t.id != topic.teacher_id]
        if not other_teachers:
            other_teachers = teachers
        reviewer = random.choice(other_teachers)

        # 获取该选题的最新版本
        topic_versions = [v for v in versions if v.topic_id == topic.id]
        latest_version = max(topic_versions, key=lambda v: v.version_num) if topic_versions else None

        score = random.randint(60, 95)
        rand = random.random()
        if rand < 0.7:
            status = "completed"
            result = random.choice(["pass", "pass", "pass", "revision"])
        else:
            status = "pending"
            result = ""

        review = Review(
            topic_id=topic.id,
            student_id=topic.student_id,
            reviewer_id=reviewer.id,
            review_type=random.choice(["normal", "normal", "external"]),
            version_id=latest_version.id if latest_version else None,
            topic_score=score + random.randint(-5, 5),
            content_score=score,
            method_score=score + random.randint(-3, 3),
            innovation_score=score + random.randint(-8, 5),
            format_score=score + random.randint(-5, 5),
            total_score=score,
            opinion="论文整体质量良好，研究内容充实，结构合理。",
            suggestions="建议进一步完善实验部分，增加对比分析。",
            result=result,
            status=status,
            review_time=datetime.now() - timedelta(days=random.randint(3, 15)) if status == "completed" else None,
            deadline=datetime.now() + timedelta(days=random.randint(5, 10)),
        )
        db.add(review)
        reviews.append(review)

        # 部分生成答辩安排
        if status == "completed" and result == "pass" and random.random() > 0.3:
            defense_score = random.randint(65, 95)
            if defense_score >= 90:
                grade = "excellent"
            elif defense_score >= 80:
                grade = "good"
            elif defense_score >= 70:
                grade = "medium"
            elif defense_score >= 60:
                grade = "pass"
            else:
                grade = "fail"

            chair = random.choice(other_teachers)
            defense = Defense(
                topic_id=topic.id,
                student_id=topic.student_id,
                defense_date=datetime.now().date() + timedelta(days=random.randint(1, 20)),
                defense_time_start=datetime.strptime(f"09:{random.randint(0,3)*15:02d}", "%H:%M").time(),
                defense_time_end=datetime.strptime(f"10:{random.randint(0,3)*15:02d}", "%H:%M").time(),
                location=random.choice(["第一会议室", "第二会议室", "线上腾讯会议", "学术报告厅"]),
                defense_form=random.choice(["offline", "online", "hybrid"]),
                chair_id=chair.id,
                committee_members=",".join(str(random.choice(teachers).id) for _ in range(3)),
                secretary_id=random.choice(teachers).id,
                presentation_score=defense_score + random.randint(-5, 3),
                qa_score=defense_score + random.randint(-3, 5),
                thesis_quality_score=score,
                total_score=defense_score,
                grade=grade,
                opinion="答辩过程顺利，回答问题准确。",
                suggestions="建议继续完善相关研究工作。",
                result="pass",
                status=random.choice(["scheduled", "scheduled", "completed"]),
            )
            db.add(defense)
            defenses.append(defense)

    db.flush()
    return reviews, defenses


def _generate_archives(db, topics, versions):
    """生成归档记录"""
    archives = []

    topic_ids_with_versions = set(v.topic_id for v in versions)
    topics_with_versions = [t for t in topics if t.id in topic_ids_with_versions]

    # 约30%有归档
    selected = random.sample(topics_with_versions, k=min(len(topics_with_versions), int(len(topics_with_versions) * 0.3)))

    for topic in selected:
        topic_versions = [v for v in versions if v.topic_id == topic.id]
        latest_version = max(topic_versions, key=lambda v: v.version_num) if topic_versions else None

        archive = Archive(
            topic_id=topic.id,
            student_id=topic.student_id,
            teacher_id=topic.teacher_id,
            final_version_id=latest_version.id if latest_version else None,
            thesis_file=latest_version.file_path if latest_version else "",
            final_score=random.randint(65, 95),
            final_grade=random.choice(["excellent", "good", "medium", "pass"]),
            archive_no=f"DA2025{random.randint(1000, 9999)}",
            archive_location=random.choice(["档案室A区", "档案室B区", "电子档案库"]),
            status=random.choice(["archived", "archived", "pending"]),
            archive_time=datetime.now() - timedelta(days=random.randint(1, 10)),
        )
        db.add(archive)
        archives.append(archive)

    db.flush()
    return archives


def _generate_anomaly_records(db, topics, students):
    """生成异常记录"""
    anomalies = []

    # 生成各种类型的异常记录
    anomaly_types = [
        ("midterm", "进度严重滞后", "L3"),
        ("midterm", "整改不力", "L2"),
        ("thesis", "格式不达标", "L1"),
        ("thesis", "版本数异常偏多", "L2"),
        ("review", "评阅分数异常偏低", "L3"),
        ("proposal", "参考文献数量不足", "L1"),
        ("proposal", "开题报告字数偏少", "L2"),
        ("student", "综合质量异常", "L3"),
    ]

    # 生成20-40条异常记录
    count = random.randint(20, 40)
    selected_students = random.sample(students, k=min(len(students), count))

    for i, student in enumerate(selected_students):
        anomaly_type, desc, level = random.choice(anomaly_types)

        # 找到该学生的选题
        student_topics = [t for t in topics if t.student_id == student.id]
        topic_id = student_topics[0].id if student_topics else None

        score = 0.0
        if level == "L1":
            score = random.uniform(0.3, 0.5)
        elif level == "L2":
            score = random.uniform(0.5, 0.75)
        else:
            score = random.uniform(0.75, 0.95)

        review_statuses = ["pending", "pending", "confirmed", "false_positive"]
        review_status = random.choice(review_statuses)

        anomaly = AnomalyRecord(
            target_type=anomaly_type,
            target_id=random.randint(1, 100),
            student_id=student.id,
            topic_id=topic_id,
            detection_type=random.choice(["iqr", "isolation_forest", "combined"]),
            feature_name=desc,
            feature_value=random.uniform(0, 100),
            feature_data={"feature": desc, "value": random.uniform(0, 100)},
            anomaly_score=round(score, 3),
            severity_level=level,
            confidence=round(random.uniform(0.6, 0.95), 2),
            description=f"检测到{desc}，请关注。",
            suggestion="建议相关老师关注并核实情况，必要时进行干预。",
            review_status=review_status,
            detection_time=datetime.now() - timedelta(days=random.randint(0, 30)),
        )
        db.add(anomaly)
        anomalies.append(anomaly)

    db.flush()
    return anomalies


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="生成模拟测试数据")
    parser.add_argument("-n", "--number", type=int, default=50, help="学生数量（默认50）")
    args = parser.parse_args()

    generate_mock_data(args.number)
