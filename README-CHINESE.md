# EvalScope GUI

企业级 EvalScope 模型评估框架图形界面。

## 功能特性

- **模型管理**：支持 HuggingFace、本地模型和 API 模型
- **数据集管理**：预设数据集、HuggingFace 导入、自定义上传
- **评估任务**：4 步向导、实时进度、任务队列管理
- **结果可视化**：柱状图、雷达图、折线图、排行榜
- **报告生成**：支持导出为 PDF、Word、HTML、CSV

## 快速开始

### 前置要求

- Python 3.10+
- Node.js 18+
- PostgreSQL 14+
- Redis 6+

### 后端配置

```bash
cd backend

# 使用 uv（推荐）
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt

# 或使用 pip
pip install -r requirements.txt

# 设置环境变量
export DATABASE_URL="postgresql://evalscope:evalscope@localhost:5432/evalscope"
export REDIS_URL="redis://localhost:6379/0"

# 运行数据库迁移
alembic upgrade head

# 启动开发服务器
uvicorn app.main:app --reload --port 8000
```

### 前端配置

```bash
cd frontend

# 安装依赖
npm install

# 设置环境变量
export NEXT_PUBLIC_API_URL="http://localhost:8000/api/v1"

# 启动开发服务器
npm run dev
```

### Docker 配置

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

## API 文档

后端运行后，可访问：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 演示账号

```
用户名：admin
密码：admin
```

## 技术栈

### 后端

- FastAPI
- SQLAlchemy 2.0
- PostgreSQL
- Celery + Redis

### 前端

- Next.js 14（App Router）
- shadcn/ui + Tailwind CSS
- Recharts
- TanStack Query

## 许可证

Apache-2.0