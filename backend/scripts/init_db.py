"""
数据库初始化脚本
用于创建数据库和表结构，以及插入初始数据
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Base, engine, SessionLocal
from app.config import settings
from app.models import *  # noqa: F401, F403  # 导入所有模型以注册到 Base.metadata
from app.core.security import hash_password


def init_database():
    """初始化数据库"""
    print(f"正在初始化数据库: {settings.DB_NAME}")

    # 尝试创建数据库（如果不存在）
    try:
        import pymysql
        conn = pymysql.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            charset="utf8mb4"
        )
        cursor = conn.cursor()
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS {settings.DB_NAME} "
            f"DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        conn.commit()
        cursor.close()
        conn.close()
        print(f"数据库 {settings.DB_NAME} 创建成功（或已存在）")
    except Exception as e:
        print(f"创建数据库时出错: {e}")
        print("请确保 MySQL 服务已启动且配置正确")
        return False

    # 创建所有表
    print("正在创建数据表...")
    Base.metadata.create_all(bind=engine)
    print("数据表创建完成")

    # 初始化基础数据
    db = SessionLocal()
    try:
        _init_default_users(db)
        db.commit()
        print("初始数据插入完成")
    except Exception as e:
        db.rollback()
        print(f"初始化数据失败: {e}")
        return False
    finally:
        db.close()

    print("数据库初始化完成!")
    return True


def _init_default_users(db):
    """初始化默认用户"""
    from app.models.user import User

    # 检查是否已有数据
    if db.query(User).count() > 0:
        print("用户表已有数据，跳过初始化")
        return

    users = [
        {
            "username": "admin",
            "password_hash": hash_password("admin123"),
            "real_name": "系统管理员",
            "role": "admin",
            "email": "admin@example.com",
            "department": "教务处",
            "status": 1,
        },
        {
            "username": "teacher01",
            "password_hash": hash_password("teacher123"),
            "real_name": "张教授",
            "role": "teacher",
            "email": "zhang@example.com",
            "department": "计算机学院",
            "teacher_no": "T2024001",
            "status": 1,
        },
        {
            "username": "teacher02",
            "password_hash": hash_password("teacher123"),
            "real_name": "李教授",
            "role": "teacher",
            "email": "li@example.com",
            "department": "计算机学院",
            "teacher_no": "T2024002",
            "status": 1,
        },
        {
            "username": "teacher03",
            "password_hash": hash_password("teacher123"),
            "real_name": "王教授",
            "role": "teacher",
            "email": "wang@example.com",
            "department": "软件工程学院",
            "teacher_no": "T2024003",
            "status": 1,
        },
        {
            "username": "teacher04",
            "password_hash": hash_password("teacher123"),
            "real_name": "陈教授",
            "role": "teacher",
            "email": "chen@example.com",
            "department": "软件工程学院",
            "teacher_no": "T2024004",
            "status": 1,
        },
        {
            "username": "teacher05",
            "password_hash": hash_password("teacher123"),
            "real_name": "刘教授",
            "role": "teacher",
            "email": "liu@example.com",
            "department": "人工智能学院",
            "teacher_no": "T2024005",
            "status": 1,
        },
        {
            "username": "student01",
            "password_hash": hash_password("student123"),
            "real_name": "小明",
            "role": "student",
            "email": "xm@example.com",
            "department": "计算机学院",
            "student_no": "2021001001",
            "grade": "2021",
            "major": "计算机科学与技术",
            "status": 1,
        },
        {
            "username": "student02",
            "password_hash": hash_password("student123"),
            "real_name": "小红",
            "role": "student",
            "email": "xh@example.com",
            "department": "计算机学院",
            "student_no": "2021001002",
            "grade": "2021",
            "major": "计算机科学与技术",
            "status": 1,
        },
        {
            "username": "student03",
            "password_hash": hash_password("student123"),
            "real_name": "小刚",
            "role": "student",
            "email": "xg@example.com",
            "department": "软件工程学院",
            "student_no": "2021002001",
            "grade": "2021",
            "major": "软件工程",
            "status": 1,
        },
    ]

    for user_data in users:
        user = User(**user_data)
        db.add(user)

    print(f"已创建 {len(users)} 个默认用户")


if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)
