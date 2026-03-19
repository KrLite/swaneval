# 共享存储抽象层 — 验证指南

> 分支：`feature/shared-storage`
> 日期：2026-03-19

本文档帮助审查者在另一台机器上拉取代码、理解改动、运行测试、验证功能。

---

## 1. 改动概览

本次引入 `StorageBackend` 抽象层，替换所有硬编码的本地文件操作，支持 **Local 文件系统** 和 **原生 S3** 双后端。

### 新增文件（6个）

| 文件 | 作用 |
|------|------|
| `app/services/storage/__init__.py` | 工厂 `get_storage()`，按配置创建单例 |
| `app/services/storage/base.py` | `StorageBackend` 抽象基类（11个方法） |
| `app/services/storage/local.py` | `LocalFileStorage` — 本地文件系统实现 |
| `app/services/storage/s3.py` | `S3Storage` — 原生 boto3 实现（支持 MinIO/AWS/OSS） |
| `app/services/storage/utils.py` | `uri_to_key()` — DB source_uri ↔ 存储 key 转换 |
| `tests/test_storage.py` | LocalFileStorage 单元测试（15个用例） |

### 修改文件（14个）

| 文件 | 改动摘要 |
|------|---------|
| `app/config.py` | +8 配置项：`STORAGE_BACKEND`, `STORAGE_ROOT`, `S3_*` |
| `app/main.py` | lifespan 中初始化存储、校验连通性、设置 AWS 环境变量 |
| `app/api/v1/datasets.py` | upload/preview/delete 走 `StorageBackend`，通过 `Depends` 注入 |
| `app/services/dataset_deletion.py` | `cleanup_uploaded_file` → async + storage |
| `app/services/task_runner.py` | `_load_dataset_rows` 走 storage，evalscope work_dir 用 `resolve_uri()` |
| `app/services/evalscope_adapter.py` | `convert_dataset` 和 `extract_primary_score` → async + storage |
| `app/services/evalscope_result_ingestor.py` | 全部 → async，递归扫描和读取走 storage |
| `pyproject.toml` | 新增 `boto3>=1.34.0`, `pytest>=9.0.2` |
| `docker-compose.yml` | +MinIO 服务（`--profile s3`）、backend 卷挂载 |
| `tests/test_dataset_deletion.py` | 适配 async + storage 新签名 |
| `tests/test_evalscope_adapter.py` | 适配 async + storage 新签名 |
| `tests/test_evalscope_result_ingestor.py` | 适配 async + storage 新签名 |
| `tests/test_real_model_api_e2e.py` | `/results` 分页响应解包 + `STORAGE_ROOT` 环境变量 |
| `test_docs/run_e2e_evalscope_api_test.py` | `/results` 分页响应解包 |

### 未修改文件

| 文件 | 原因 |
|------|------|
| `app/services/evaluators.py` | 脚本评估器保持本地文件系统（安全边界：不从 S3 加载执行代码） |
| `app/api/v1/datasets.py:mount_dataset()` | mount 始终操作本地路径（设计初衷就是"文件已在服务器上"） |
| 前端所有文件 | 本次改动仅在后端存储层，前端无变化 |

---

## 2. 环境准备

### 2.1 拉取代码

```bash
git clone <repo-url>
cd evalscope-gui-2
git checkout feature/shared-storage
```

### 2.2 安装后端依赖

```bash
cd backend
uv sync
```

需要 Python >= 3.10，uv 包管理器。

### 2.3 安装前端依赖（可选，仅验证 build）

```bash
cd frontend
npm install
```

---

## 3. 运行单元测试

```bash
cd backend
uv run python -m pytest tests/test_storage.py \
  tests/test_dataset_deletion.py \
  tests/test_evalscope_adapter.py \
  tests/test_evalscope_result_ingestor.py \
  -v
```

预期输出：**39 passed**

### 测试覆盖范围

| 测试文件 | 用例数 | 覆盖 |
|---------|--------|------|
| `test_storage.py` | 15 | LocalFileStorage 全部方法 |
| `test_dataset_deletion.py` | 4 | cleanup_uploaded_file (async) + delete_versions |
| `test_evalscope_adapter.py` | 12 | 格式转换、config 构建、score 提取 |
| `test_evalscope_result_ingestor.py` | 8 | 结果解析、artifact 优先、fallback、过滤 |

---

## 4. 代码 Lint 检查

```bash
cd backend
uv run ruff check \
  app/services/storage/ \
  app/api/v1/datasets.py \
  app/services/task_runner.py \
  app/services/evalscope_adapter.py \
  app/services/evalscope_result_ingestor.py \
  app/services/dataset_deletion.py \
  app/main.py \
  app/config.py \
  tests/test_storage.py \
  tests/test_dataset_deletion.py \
  tests/test_evalscope_adapter.py \
  tests/test_evalscope_result_ingestor.py
```

预期输出：**All checks passed!**

---

## 5. 前端 Build 检查

```bash
cd frontend
npx next build
```

预期：build 成功，无 TypeScript 错误。

---

## 6. Local 模式功能验证

### 6.1 启动后端（SQLite 模式，无需 Postgres）

```bash
cd backend
DATABASE_URL='sqlite+aiosqlite:///./test_verify.db' \
DATABASE_URL_SYNC='sqlite:///./test_verify.db' \
STORAGE_BACKEND=local \
STORAGE_ROOT=data \
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

日志中应出现：
```
INFO:app.services.storage:Storage backend: local (data)
INFO:app.main:Storage backend validated and ready
```

### 6.2 基础 API 验证

```bash
# 注册 + 登录
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"username":"tester","email":"t@t.com","password":"pass123456","role":"admin"}' \
  > /dev/null && \
  curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"tester","password":"pass123456"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 上传数据集
echo '{"query":"2+2=?","response":"4"}' > /tmp/test.jsonl
curl -s -X POST http://localhost:8000/api/v1/datasets/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/tmp/test.jsonl" \
  -F "name=verify-ds" | python3 -m json.tool

# 验证文件写入存储目录
ls backend/data/uploads/
# 应看到 UUID 命名的 .jsonl 文件

# 获取数据集列表（分页响应）
curl -s http://localhost:8000/api/v1/datasets \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('Format:', 'paginated' if 'items' in d else 'flat list')
print('Total:', d.get('total', 'N/A'))
print('Items:', len(d.get('items', [])))
"
# 应输出: Format: paginated, Total: 1, Items: 1
```

---

## 7. S3 模式功能验证（需要 Docker）

### 7.1 启动 MinIO

```bash
docker compose --profile s3 up -d minio
# 等待 MinIO 就绪
curl -sf http://localhost:9000/minio/health/live && echo "MinIO ready"
```

MinIO 控制台：http://localhost:9001（minioadmin / minioadmin）

### 7.2 启动后端（S3 模式）

```bash
cd backend
DATABASE_URL='sqlite+aiosqlite:///./test_s3.db' \
DATABASE_URL_SYNC='sqlite:///./test_s3.db' \
STORAGE_BACKEND=s3 \
S3_BUCKET=evalscope \
S3_ENDPOINT_URL=http://localhost:9000 \
S3_ACCESS_KEY=minioadmin \
S3_SECRET_KEY=minioadmin \
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

日志中应出现：
```
INFO:app.services.storage:Storage backend: S3 (bucket=evalscope)
INFO:app.main:Storage backend validated and ready
```

### 7.3 验证 S3 写入

重复 6.2 的上传操作，然后在 MinIO 控制台 (http://localhost:9001) 检查：
- Bucket `evalscope` 已自动创建
- `uploads/` 前缀下有上传的文件

---

## 8. 关键设计点审查清单

审查者可重点检查以下设计决策：

- [ ] **StorageBackend 接口** (`base.py`)：11 个方法覆盖了所有文件操作场景
- [ ] **LocalFileStorage** (`local.py`)：用 `asyncio.to_thread` 包装阻塞 I/O
- [ ] **S3Storage** (`s3.py`)：`resolve_uri()` 返回 `s3://` URI，EvalScope 可直接消费
- [ ] **uri_to_key** (`utils.py`)：正确处理 S3 URI / 绝对路径 / 相对路径 / mount 路径
- [ ] **mount 模式** (`datasets.py`)：不走 storage，直接本地操作
- [ ] **evaluators.py**：脚本加载保持本地（安全边界）
- [ ] **main.py lifespan**：S3 模式下自动设置 `AWS_*` 环境变量
- [ ] **E2E 测试** (`test_real_model_api_e2e.py`)：适配分页响应 + STORAGE_ROOT
- [ ] **docker-compose.yml**：MinIO 在 `s3` profile 下，不影响默认启动

---

## 9. 配置参考

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `STORAGE_BACKEND` | `local` | `local` 或 `s3` |
| `STORAGE_ROOT` | `data` | Local 模式根目录 |
| `S3_BUCKET` | _(空)_ | S3 桶名 |
| `S3_ENDPOINT_URL` | _(空)_ | S3 端点（MinIO: `http://minio:9000`） |
| `S3_ACCESS_KEY` | _(空)_ | S3 访问密钥 |
| `S3_SECRET_KEY` | _(空)_ | S3 密钥 |
| `S3_REGION` | `us-east-1` | S3 区域 |
| `S3_PREFIX` | _(空)_ | S3 key 前缀（可选） |

---

## 10. 已知限制

1. **大文件读取**：S3 模式下 `read_file/read_text` 会将整个文件读入内存。对于 GB 级数据集，未来需增加流式读取。
2. **旧数据迁移**：已有数据库中的 `source_uri` 是本地绝对路径。从 local 切换到 S3 需要一次性迁移脚本（上传文件 + 更新 DB）。
3. **脚本评估器**：始终要求本地路径，不支持从 S3 加载。这是有意为之的安全设计。
