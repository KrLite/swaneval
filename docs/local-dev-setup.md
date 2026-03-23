# SwanEVAL 本地开发环境搭建 + K8s 部署测试

## 前置条件安装

### Docker

<details>
<summary><b>macOS</b></summary>

```bash
brew install --cask docker
```

安装后打开 Docker Desktop 应用，等待状态变为 "Running"。

</details>

<details>
<summary><b>Windows</b></summary>

1. 下载 [Docker Desktop for Windows](https://docs.docker.com/desktop/setup/install/windows-install/)
2. 双击安装，安装过程中勾选 **Use WSL 2 instead of Hyper-V**
3. 安装完成后重启电脑，打开 Docker Desktop

> 需要先启用 WSL2：以管理员身份运行 PowerShell，执行 `wsl --install`

</details>

<details>
<summary><b>Linux (Ubuntu/Debian)</b></summary>

```bash
# 安装 Docker Engine
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker

# 安装 Docker Compose 插件
sudo apt-get install docker-compose-plugin
```

</details>

验证：

```bash
docker --version
docker compose version
docker ps    # 应无报错
```

---

### Node.js + pnpm

<details>
<summary><b>macOS</b></summary>

```bash
brew install node
npm install -g pnpm
```

</details>

<details>
<summary><b>Windows</b></summary>

1. 下载 [Node.js LTS](https://nodejs.org/) 安装包，双击安装
2. 打开 PowerShell：

```powershell
npm install -g pnpm
```

</details>

<details>
<summary><b>Linux (Ubuntu/Debian)</b></summary>

```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
npm install -g pnpm
```

</details>

验证：

```bash
node --version    # >= 18
pnpm --version    # >= 8
```

---

### Python 3.10+ + uv

<details>
<summary><b>macOS</b></summary>

```bash
brew install python@3.10
curl -LsSf https://astral.sh/uv/install.sh | sh
```

</details>

<details>
<summary><b>Windows</b></summary>

1. 下载 [Python 3.10+](https://www.python.org/downloads/)，安装时勾选 **Add Python to PATH**
2. 打开 PowerShell：

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

</details>

<details>
<summary><b>Linux (Ubuntu/Debian)</b></summary>

```bash
sudo apt-get install -y python3.10 python3.10-venv python3-pip
curl -LsSf https://astral.sh/uv/install.sh | sh
```

</details>

验证：

```bash
python3 --version    # >= 3.10（Windows 上用 python）
uv --version
```

---

### kubectl

<details>
<summary><b>macOS</b></summary>

```bash
brew install kubectl
```

</details>

<details>
<summary><b>Windows</b></summary>

```powershell
# 方式一：使用 winget
winget install Kubernetes.kubectl

# 方式二：使用 choco
choco install kubernetes-cli
```

</details>

<details>
<summary><b>Linux</b></summary>

```bash
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/
```

</details>

验证：

```bash
kubectl version --client
```

---

### K8s 集群 kubeconfig

你需要一份可访问 GPU 集群的 kubeconfig 文件。获取方式取决于集群类型：

```bash
# k3s（在集群主节点上执行）
sudo cat /etc/rancher/k3s/k3s.yaml
# 注意：需要将 server: https://127.0.0.1:6443 改为集群主节点的实际 IP

# 云厂商 K8s（阿里云 ACK / 腾讯云 TKE / 华为云 CCE）
# 在控制台下载 kubeconfig 文件

# 自建集群
cat ~/.kube/config    # 在集群管理机上执行
```

将 kubeconfig 内容保存好，后续在 SwanEVAL 前端注册集群时粘贴。

**可选验证**（如果你把 kubeconfig 放到本机）：

```bash
# macOS / Linux
mkdir -p ~/.kube
# 将 kubeconfig 内容写入 ~/.kube/config

# Windows (PowerShell)
mkdir -Force $env:USERPROFILE\.kube
# 将 kubeconfig 内容写入 $env:USERPROFILE\.kube\config

# 验证
kubectl get nodes    # 应看到集群节点列表
```

## 1. 启动基础设施

```bash
cd /path/to/swaneval-2

# 启动 Postgres + Redis
docker compose up -d postgres redis

# 验证
docker compose ps
# 应看到 swaneval-postgres (healthy) 和 swaneval-redis (healthy)
```

## 2. 创建后端配置

```bash
cat > backend/.env << 'EOF'
DATABASE_URL=postgresql+asyncpg://swaneval:swaneval@localhost:6001/swaneval
DATABASE_URL_SYNC=postgresql://swaneval:swaneval@localhost:6001/swaneval
REDIS_URL=redis://localhost:6379/0
CORS_ORIGINS=["http://localhost:3000"]
SECRET_KEY=dev-secret-change-in-production
HF_TOKEN=
EOF
```

> 如果有 HuggingFace Token，填入 `HF_TOKEN=hf_xxx`，用于拉取 gated 模型。

## 3. 初始化数据库

```bash
cd backend
uv sync                          # 安装 Python 依赖
uv run alembic upgrade head      # 运行数据库迁移
```

## 4. 启动后端

```bash
cd backend
uv run uvicorn app.main:app --reload --port 8000
```

验证：打开 http://localhost:8000/docs 应看到 Swagger API 文档。

## 5. 启动前端

新开一个终端：

```bash
cd frontend
pnpm install                     # 首次需要
pnpm dev                         # 启动开发服务器，默认 localhost:3000
```

验证：打开 http://localhost:3000 应看到登录页面。

## 6. 注册用户 + 登录

打开 http://localhost:3000，点击注册：

- 用户名：admin
- 邮箱：admin@test.com
- 密码：admin123

或者用 API：

```bash
# 注册
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "email": "admin@test.com", "password": "admin123"}'

# 登录，获取 token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# 返回 {"access_token": "eyJ...", "token_type": "bearer"}
# 后续请求用:
export TOKEN="eyJ..."
```

## 7. 配置 HuggingFace Token（可选）

登录后，在**账户设置**页面填入 HF Token，或通过 API：

```bash
curl -X PUT http://localhost:8000/api/v1/auth/tokens \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"hf_token": "hf_你的token"}'
```

## 8. 注册 K8s 集群

### 通过前端 UI

1. 进入 **计算资源** 页面（侧边栏）
2. 点击 **添加**
3. 填写：
   - 集群名称：`gpu-cluster`
   - 命名空间：`swaneval`（或自定义）
   - Kubeconfig：粘贴你的 kubeconfig YAML 完整内容
   - vLLM 镜像源：国内网络选阿里云/华为云
4. 点击 **添加**，等待探测完成（状态变为"就绪"）

### 通过 API

```bash
# 注意：kubeconfig 需要作为字符串传入，换行用 \n
KUBECONFIG_CONTENT=$(cat ~/.kube/config)

curl -X POST http://localhost:8000/api/v1/clusters \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"gpu-cluster\",
    \"description\": \"GPU 评估集群\",
    \"kubeconfig\": $(jq -Rs . <<< "$KUBECONFIG_CONTENT"),
    \"namespace\": \"swaneval\"
  }"

# 记下返回的 cluster_id
```

### 验证集群

```bash
# 探测集群资源
curl -X POST http://localhost:8000/api/v1/clusters/{cluster_id}/probe \
  -H "Authorization: Bearer $TOKEN"

# 查看节点
curl http://localhost:8000/api/v1/clusters/{cluster_id}/nodes \
  -H "Authorization: Bearer $TOKEN"
```

前端 UI 中应看到 GPU 数量、类型、节点列表。

## 9. 注册模型

### 通过前端 UI

1. 进入 **模型管理** 页面
2. 点击 **添加模型**
3. 填写：
   - 名称：`qwen-0.5b`（自定义）
   - 模型类型：`HuggingFace`
   - 模型名称（HF ID）：`Qwen/Qwen2.5-0.5B-Instruct`（小模型，测试用）
   - Endpoint URL：留空（部署后自动填充）
4. 保存

### 通过 API

```bash
curl -X POST http://localhost:8000/api/v1/models \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "qwen-0.5b",
    "provider": "vllm",
    "endpoint_url": "",
    "model_type": "huggingface",
    "api_format": "openai",
    "model_name": "Qwen/Qwen2.5-0.5B-Instruct",
    "source_model_id": "Qwen/Qwen2.5-0.5B-Instruct"
  }'
```

## 10. 部署模型到 K8s

### 通过前端 UI

1. 在模型列表点击模型名称查看详情
2. 在详情面板底部找到 **部署** 区域
3. 选择集群 → 点击 **部署**
4. 等待状态从"部署中"变为"运行中"

### 通过 API

```bash
curl -X POST "http://localhost:8000/api/v1/models/{model_id}/deploy?cluster_id={cluster_id}&gpu_count=1&memory_gb=20" \
  -H "Authorization: Bearer $TOKEN"

# 返回：{"status": "deployed", "endpoint_url": "http://...", "deployment_name": "vllm-xxxxx"}
```

### K8s 侧验证

```bash
kubectl get pods -n swaneval
kubectl get svc -n swaneval
kubectl logs -n swaneval -l swaneval.io/component=vllm --tail=50
```

### 推理测试

用返回的 endpoint_url 测试：

```bash
curl http://<node_ip>:<node_port>/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-0.5B-Instruct",
    "messages": [{"role": "user", "content": "你好，介绍一下你自己"}],
    "max_tokens": 100
  }'
```

## 11. 创建评估任务（可选）

1. 进入 **评估任务** 页面
2. 点击 **新建任务**
3. 向导步骤：
   - 选择已注册的模型
   - 选择数据集
   - 配置评估标准
   - 执行后端选 **K8s / vLLM**，选择集群，配置 GPU
4. 提交任务

## 12. 清理

```bash
# 停止模型部署
curl -X POST http://localhost:8000/api/v1/models/{model_id}/undeploy \
  -H "Authorization: Bearer $TOKEN"

# K8s 侧确认清理
kubectl get pods -n swaneval   # 应无 vllm pod

# 停止本地服务
# Ctrl+C 停止 uvicorn 和 pnpm dev

# 停止数据库
docker compose down            # 保留数据
docker compose down -v         # 删除数据（完全重置）
```

## 常见问题

### 集群注册失败
- 确认 kubeconfig 中的 server 地址从本机可达（`curl -k https://172.16.6.4:6443`）
- 如果是内网地址，确保本机在同一网络或有 VPN

### 模型部署超时
- 默认 600 秒超时，大模型需要更多时间下载
- 可设置环境变量 `VLLM_READINESS_TIMEOUT=1200`
- 查看 pod 日志：`kubectl logs -n swaneval -l app=vllm-xxxxx -f`

### NodePort 无法访问
- 确认节点 IP 从本机可达
- 检查防火墙规则是否放行 NodePort 范围（30000-32767）
- `kubectl get svc -n swaneval` 查看分配的端口

### 国内拉取 vLLM 镜像慢
- 注册集群时选择阿里云或华为云镜像源
- 或在集群详情中编辑 vLLM 镜像地址

### HF 模型下载失败 (401)
- 确认已在账户设置中填入 HF Token
- 确认 Token 有访问该模型的权限
- Gated 模型需要先在 HuggingFace 页面接受使用协议
