import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import router as v1_router
from app.config import settings
from app.database import init_db
from app.services.storage import get_storage

# 配置日志 / Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理 / Application lifespan management

    启动时初始化数据库和存储后端，关闭时清理资源。
    Initialize database and storage on startup, cleanup on shutdown.
    """
    await init_db()

    # 初始化存储后端 / Initialize storage backend
    storage = get_storage()
    await storage.validate()
    await storage.ensure_prefix("uploads")
    await storage.ensure_prefix("evalscope_outputs")
    logger.info("Storage backend validated and ready")

    # S3 模式下设置 AWS 环境变量供 EvalScope/fsspec 使用
    if settings.STORAGE_BACKEND.lower() == "s3":
        if settings.S3_ENDPOINT_URL:
            os.environ.setdefault("AWS_ENDPOINT_URL", settings.S3_ENDPOINT_URL)
        if settings.S3_ACCESS_KEY:
            os.environ.setdefault("AWS_ACCESS_KEY_ID", settings.S3_ACCESS_KEY)
        if settings.S3_SECRET_KEY:
            os.environ.setdefault("AWS_SECRET_ACCESS_KEY", settings.S3_SECRET_KEY)
        if settings.S3_REGION:
            os.environ.setdefault("AWS_DEFAULT_REGION", settings.S3_REGION)

    yield


# 创建FastAPI应用 / Create FastAPI application
app = FastAPI(
    title="EvalScope GUI API",
    version="0.1.0",
    lifespan=lifespan,
)

# 添加CORS中间件 / Add CORS middleware
# 允许前端跨域访问 / Allow frontend cross-origin access
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含API路由 / Include API routes
app.include_router(v1_router)


@app.get("/health")
async def health():
    """
    健康检查端点 / Health check endpoint

    用于检查服务是否正常运行。
    Used to check if the service is running normally.
    """
    return {"status": "ok"}