# EvalScope GUI

企业级大模型评测平台。管理数据集、定义评测标准、跨模型执行评测任务、通过图表和报告分析结果。

## 功能特性

- **数据集管理** — 上传（JSONL/CSV/JSON）、挂载服务器路径、自动版本管理、数据预览
- **评测标准** — 预置标准（精确匹配、包含匹配、数值匹配）、正则表达式、自定义脚本、大模型裁判
- **模型注册** — 注册任何 OpenAI 兼容的 API 端点
- **任务执行** — 4步配置向导、异步后台执行、稳定性测试（多随机种子）、断点续测
- **结果与可视化** — 排行榜、柱状图/雷达图/折线图、错误分析、汇总统计
- **认证与权限** — JWT 认证、基于角色的访问控制（管理员、数据管理员、评测工程师、访客）

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | FastAPI, SQLModel, Alembic, Pydantic Settings, HTTPX |
| 前端 | Next.js 14 (App Router), React 18, Tailwind CSS, shadcn/ui, React Query, Zustand, Recharts |
| 数据 | PostgreSQL 14, Redis 7 |
| 基础设施 | Docker Compose, uv |

## 快速开始

### 前置要求

- Python 3.10+
- Node.js 18+
- Docker（用于 PostgreSQL 和 Redis）

### 1. 启动基础设施

```bash
docker compose up -d postgres redis
```

### 2. 后端

```bash
cd backend
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8000
```

### 3. 前端

```bash
cd frontend
npm install
npm run dev
```

- 后端 API：http://localhost:8000
- 前端界面：http://localhost:3000

### 环境变量

后端从 `backend/.env` 读取配置：

```
DATABASE_URL=postgresql+asyncpg://evalscope:evalscope@localhost:6001/evalscope
DATABASE_URL_SYNC=postgresql://evalscope:evalscope@localhost:6001/evalscope
REDIS_URL=redis://localhost:6379/0
CORS_ORIGINS=["http://localhost:3000"]
SECRET_KEY=dev-secret-change-in-production
UPLOAD_DIR=data/uploads
```

## API 端点

| 模块 | 端点 |
|------|------|
| 认证 | `POST /api/v1/auth/register`, `POST /api/v1/auth/login`, `GET /api/v1/auth/me` |
| 数据集 | `POST /upload`, `POST /mount`, `GET /`, `GET /{id}`, `GET /{id}/preview`, `DELETE /{id}` |
| 评测标准 | `POST /`, `GET /`, `GET /{id}`, `PUT /{id}`, `DELETE /{id}`, `POST /test` |
| 模型 | `POST /`, `GET /`, `GET /{id}`, `PUT /{id}`, `DELETE /{id}` |
| 任务 | `POST /`, `GET /`, `GET /{id}`, `GET /{id}/subtasks`, `POST /{id}/pause\|resume\|cancel` |
| 结果 | `GET /`, `GET /leaderboard`, `GET /errors`, `GET /summary` |

完整交互式文档：http://localhost:8000/docs（Swagger）或 http://localhost:8000/redoc。

## 使用流程

```bash
# 1. 注册并登录
curl -X POST localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","email":"admin@test.com","password":"pass123","role":"admin"}'

TOKEN=$(curl -s -X POST localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"pass123"}' | jq -r .access_token)

# 2. 注册模型
curl -X POST localhost:8000/api/v1/models \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"gpt-4o","provider":"openai","endpoint_url":"https://api.openai.com/v1/chat/completions","api_key":"sk-...","model_type":"api"}'

# 3. 上传数据集（每行格式为 {"prompt":"...","expected":"..."} 的 JSONL 文件）
curl -X POST localhost:8000/api/v1/datasets/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@my_dataset.jsonl" -F "name=math-test" -F "tags=math"

# 4. 创建评测标准
curl -X POST localhost:8000/api/v1/criteria \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"exact_match","type":"preset","config_json":"{\"metric\":\"exact_match\"}"}'

# 5. 创建并运行评测任务
curl -X POST localhost:8000/api/v1/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"eval-gpt4o","model_id":"<MODEL_UUID>","dataset_ids":["<DS_UUID>"],"criteria_ids":["<CRIT_UUID>"]}'

# 6. 查看结果
curl localhost:8000/api/v1/results/summary?task_id=<TASK_UUID> \
  -H "Authorization: Bearer $TOKEN"
```

## 项目结构

```
backend/
  app/
    main.py              # FastAPI 应用入口
    config.py            # pydantic-settings 配置
    database.py          # 异步 SQLAlchemy 引擎
    models/              # SQLModel 数据表模型
    schemas/             # Pydantic 请求/响应模式
    api/
      deps.py            # 认证与数据库依赖
      v1/                # 路由模块
    services/            # 业务逻辑（认证、评测器、任务执行器）
  alembic/               # 数据库迁移
frontend/
  app/                   # Next.js App Router 页面
  components/            # React 组件
  lib/                   # API 客户端、Hooks、状态管理
```

## 许可证

Apache-2.0
