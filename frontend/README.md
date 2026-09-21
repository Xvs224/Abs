# 毕业论文质量监控系统 - 前端

基于 Vue 3 + Vite + Element Plus 的前端项目。

## 技术栈

- Vue 3 (Composition API)
- Vite 5
- Element Plus
- Vue Router 4
- Pinia (状态管理)
- Axios (HTTP 客户端)
- ECharts 5 (数据可视化)
- vue-echarts

## 快速开始

### 安装依赖

```bash
cd frontend
npm install
```

### 开发模式

```bash
npm run dev
```

访问 http://localhost:5173

### 构建生产版本

```bash
npm run build
```

### 预览生产版本

```bash
npm run preview
```

## 项目结构

```
src/
├── api/              # API 接口模块
├── components/       # 公共组件
├── layout/           # 布局组件
├── router/           # 路由配置
├── store/            # Pinia 状态管理
├── styles/           # 全局样式
├── utils/            # 工具函数
├── views/            # 页面组件
├── App.vue           # 根组件
└── main.js           # 入口文件
```

## 默认账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | admin123 |
| 教师 | teacher01 | teacher123 |
| 学生 | student01 | student123 |
