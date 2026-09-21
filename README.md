# 基于异常检测的毕业论文全过程质量监控系统

## 项目简介

面向学生、指导老师和教学管理人员，围绕毕业论文全过程质量监控的核心对象和业务流程开展服务。系统实现选题确认→开题审核→过程指导→中期检查→论文评阅→答辩评价→成果归档的完整业务闭环，核心智能化功能为基于统计阈值、四分位距（IQR）和孤立森林（Isolation Forest）的异常检测。

## 技术栈

### 后端
- **框架**: FastAPI (Python 3.10+)
- **ORM**: SQLAlchemy 2.0
- **数据库**: MySQL 8.0
- **认证**: JWT + RBAC
- **异常检测**: scikit-learn (Isolation Forest + IQR)

### 前端
- **框架**: Vue 3 + Vite
- **UI 组件库**: Element Plus
- **图表**: ECharts 5
- **HTTP 客户端**: Axios

## 项目结构

```
.
├── backend/          # 后端 FastAPI 项目
├── frontend/         # 前端 Vue 3 项目
├── scripts/          # 工具脚本（数据生成等）
└── docs/             # 项目文档
```

## 快速开始

### 后端启动

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API 文档: http://localhost:8000/docs

### 前端启动

```bash
cd frontend
npm install
npm run dev
```

前端地址: http://localhost:5173

## 默认账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | admin123 |
| 教师 | teacher01 | teacher123 |
| 学生 | student01 | student123 |

## 核心功能

1. **身份认证与权限管理** - JWT 认证 + RBAC 三角色权限
2. **选题管理** - 题目申报、选题确认、重复检测
3. **开题管理** - 开题报告、材料审核
4. **过程指导** - 指导计划、指导记录
5. **中期检查** - 中期报告、问题整改与复检
6. **论文版本管理** - 版本提交、格式规范检测
7. **评阅答辩** - 评阅分配、成绩记录
8. **异常检测引擎** - IQR + 孤立森林，三级分级提示
9. **质量统计看板** - 多维度统计可视化
10. **成果归档** - 论文归档管理

## 异常检测

- **检测方法**: 统计阈值 + 四分位距(IQR) + 孤立森林(Isolation Forest)
- **分级提示**: L1(提示/蓝) → L2(警告/橙) → L3(告警/红)
- **人工复核**: 支持人工复核与结果纠正
- **准确性评价**: 使用正常、临界、异常样例评估准确率与误报率
