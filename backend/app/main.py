"""
FastAPI 主应用入口
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
import os

from app.config import settings
from app.core.logger import setup_logging
from app.core.exceptions import register_exception_handlers
from app.core.middleware import OperationLogMiddleware
from app.core.limiter import limiter
from app.database import engine, Base

# 设置日志
setup_logging()

# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="基于异常检测的毕业论文全过程质量监控系统 API",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
)

# 限流器状态注册
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"code": 429, "message": "请求过于频繁，请稍后再试", "data": None}
    )

# 注册 CORS 中间件 — 使用配置白名单而非通配符
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册操作日志中间件
app.add_middleware(OperationLogMiddleware)

# 注册全局异常处理器
register_exception_handlers(app)

# 确保上传目录存在
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    # 创建所有数据表（生产环境应使用 alembic 迁移）
    Base.metadata.create_all(bind=engine)

    # 初始化默认数据
    from app.services.user_service import UserService
    from app.database import SessionLocal
    from app.models.user import User

    db = SessionLocal()
    try:
        # 检查是否已有管理员
        admin_count = db.query(User).filter(User.role == "admin").count()
        if admin_count == 0:
            user_service = UserService(db)
            # 创建默认管理员
            from app.schemas.user import UserCreate
            admin_data = UserCreate(
                username="admin",
                password="admin123",
                real_name="系统管理员",
                role="admin",
                email="admin@example.com",
                department="教务处"
            )
            user_service.create_user(admin_data)
            print("默认管理员账号已创建: admin / admin123")

        # 创建默认教师
        teacher_count = db.query(User).filter(User.role == "teacher").count()
        if teacher_count == 0:
            user_service = UserService(db)
            from app.schemas.user import UserCreate
            teacher_data = UserCreate(
                username="teacher01",
                password="teacher123",
                real_name="张教授",
                role="teacher",
                email="teacher01@example.com",
                department="计算机学院",
                teacher_no="T2024001"
            )
            user_service.create_user(teacher_data)
            print("默认教师账号已创建: teacher01 / teacher123")

        # 创建默认学生
        student_count = db.query(User).filter(User.role == "student").count()
        if student_count == 0:
            user_service = UserService(db)
            from app.schemas.user import UserCreate
            student_data = UserCreate(
                username="student01",
                password="student123",
                real_name="李同学",
                role="student",
                email="student01@example.com",
                department="计算机学院",
                student_no="2021001001",
                grade="2021",
                major="计算机科学与技术"
            )
            user_service.create_user(student_data)
            print("默认学生账号已创建: student01 / student123")

    except Exception as e:
        print(f"初始化默认数据失败: {e}")
    finally:
        db.close()

    # 启动异常检测定时调度器
    try:
        from app.core.anomaly_scheduler import init_scheduler
        init_scheduler()
    except Exception as e:
        print(f"启动异常检测调度器失败: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    try:
        from app.core.anomaly_scheduler import shutdown_scheduler
        shutdown_scheduler()
    except Exception as e:
        print(f"关闭异常检测调度器失败: {e}")


# 注册路由
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.topics import router as topics_router
from app.api.proposals import router as proposals_router
from app.api.midterm import router as midterm_router
from app.api.thesis import router as thesis_router
from app.api.reviews import router as reviews_router
from app.api.archives import router as archives_router
from app.api.anomaly import router as anomaly_router
from app.api.stats import router as stats_router
from app.api.logs import router as logs_router
from app.api.files import router as files_router
from app.api.stages import router as stages_router
from app.api.guidance import router as guidance_router

app.include_router(auth_router, tags=["认证"])
app.include_router(users_router, tags=["用户管理"])
app.include_router(topics_router, tags=["选题管理"])
app.include_router(proposals_router, tags=["开题管理"])
app.include_router(midterm_router, tags=["中期检查"])
app.include_router(thesis_router, tags=["论文版本"])
app.include_router(reviews_router, tags=["评阅答辩"])
app.include_router(archives_router, tags=["成果归档"])
app.include_router(anomaly_router, tags=["异常检测"])
app.include_router(stats_router, tags=["统计分析"])
app.include_router(logs_router, tags=["操作日志"])
app.include_router(files_router, tags=["文件管理"])
app.include_router(stages_router, tags=["阶段时间配置"])
app.include_router(guidance_router, tags=["过程指导"])


@app.get("/", tags=["根路径"])
async def root():
    """根路径 - 健康检查"""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health", tags=["根路径"])
async def health_check():
    """健康检查"""
    return {"status": "healthy"}
