# EvalScope GUI

Enterprise LLM evaluation platform. Manage datasets, define evaluation criteria, run evaluation tasks across models, and analyze results with charts and reports.

## Features

- **Dataset Management** — Upload (JSONL/CSV/JSON), mount server paths, auto-versioning, row preview
- **Evaluation Criteria** — Presets (exact match, contains, numeric), regex, custom scripts, LLM-as-a-Judge
- **Model Registry** — Register any OpenAI-compatible API endpoint
- **Task Execution** — 4-step config wizard, async background runner, stability testing (multi-seed), pause/resume with checkpointing
- **Results & Visualization** — Leaderboard, bar/radar/line charts, error drill-down, summary statistics
- **Auth & Permissions** — JWT auth, role-based access (admin, data_admin, engineer, viewer)

## Tech Stack

| Layer | Tech |
|-------|------|
| Backend | FastAPI, SQLModel, Alembic, Pydantic Settings, HTTPX |
| Frontend | Next.js 14 (App Router), React 18, Tailwind CSS, shadcn/ui, React Query, Zustand, Recharts |
| Data | PostgreSQL 14, Redis 7 |
| Infra | Docker Compose, uv |

## Quick Start

### 方式一：全容器化（推荐）

```bash
docker compose up --build -d
```

等待就绪后访问：
- 前端：http://localhost:3000
- 后端 API：http://localhost:8000
- Swagger 文档：http://localhost:8000/docs

### 方式二：混合开发模式

```bash
# 启动基础设施
docker compose up -d postgres redis

# 后端
cd backend
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8000

# 前端（新终端）
cd frontend
npm install
npm run dev
```

### 可选服务

```bash
# 本地模型推理（Ollama）
docker compose --profile ollama up -d

# S3 对象存储（MinIO）
docker compose --profile s3 up -d
```

> **全流程操作指南**：从注册到可视化结果的完整步骤见 [docs/full-pipeline-guide.md](docs/full-pipeline-guide.md)

## API Endpoints

| Module | Endpoints |
|--------|-----------|
| Auth | `POST /api/v1/auth/register`, `POST /api/v1/auth/login`, `GET /api/v1/auth/me` |
| Datasets | `POST /upload`, `POST /mount`, `GET /`, `GET /{id}`, `GET /{id}/preview`, `DELETE /{id}` |
| Criteria | `POST /`, `GET /`, `GET /{id}`, `PUT /{id}`, `DELETE /{id}`, `POST /test` |
| Models | `POST /`, `GET /`, `GET /{id}`, `PUT /{id}`, `DELETE /{id}` |
| Tasks | `POST /`, `GET /`, `GET /{id}`, `GET /{id}/subtasks`, `POST /{id}/pause\|resume\|cancel` |
| Results | `GET /`, `GET /leaderboard`, `GET /errors`, `GET /summary` |

Full interactive docs at http://localhost:8000/docs (Swagger) or http://localhost:8000/redoc.

## Pipeline Usage

```bash
# 1. Register & login
curl -X POST localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","email":"admin@test.com","password":"pass123","role":"admin"}'

TOKEN=$(curl -s -X POST localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"pass123"}' | jq -r .access_token)

# 2. Register a model
curl -X POST localhost:8000/api/v1/models \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"gpt-4o","provider":"openai","endpoint_url":"https://api.openai.com/v1/chat/completions","api_key":"sk-...","model_type":"api"}'

# 3. Upload a dataset (JSONL with {"prompt":"...","expected":"..."} per line)
curl -X POST localhost:8000/api/v1/datasets/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@my_dataset.jsonl" -F "name=math-test" -F "tags=math"

# 4. Create evaluation criterion
curl -X POST localhost:8000/api/v1/criteria \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"exact_match","type":"preset","config_json":"{\"metric\":\"exact_match\"}"}'

# 5. Create and run a task
curl -X POST localhost:8000/api/v1/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"eval-gpt4o","model_id":"<MODEL_UUID>","dataset_ids":["<DS_UUID>"],"criteria_ids":["<CRIT_UUID>"]}'

# 6. Check results
curl localhost:8000/api/v1/results/summary?task_id=<TASK_UUID> \
  -H "Authorization: Bearer $TOKEN"
```

## Project Structure

```
backend/
  app/
    main.py              # FastAPI app entry point
    config.py            # Settings via pydantic-settings
    database.py          # Async SQLAlchemy engine
    models/              # SQLModel table classes
    schemas/             # Pydantic request/response schemas
    api/
      deps.py            # Auth & DB dependencies
      v1/                # Route modules
    services/            # Business logic (auth, evaluators, task runner)
  alembic/               # Database migrations
frontend/
  app/                   # Next.js App Router pages
  components/            # React components
  lib/                   # API client, hooks, stores
```

## License

Apache-2.0
