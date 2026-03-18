import logging
import sys
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.session import engine

logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("=== Starting EvalScope GUI Backend ===")
    logger.info("DATABASE_URL = %s", _mask_url(settings.DATABASE_URL))
    logger.info("REDIS_URL    = %s", settings.REDIS_URL)
    logger.info("CORS_ORIGINS = %s", settings.CORS_ORIGINS)

    logger.info("Connecting to database...")
    try:
        async with engine.begin() as conn:
            logger.info("Database connection established successfully")
            await conn.run_sync(SQLModel.metadata.create_all)
            logger.info("Database tables created/verified")
    except Exception as exc:
        logger.error("!!! DATABASE CONNECTION FAILED !!!")
        logger.error("Error type: %s", type(exc).__name__)
        logger.error("Error details: %s", exc)
        logger.error("")
        logger.error("Troubleshooting:")
        logger.error("  1. Is PostgreSQL running? Check: pg_isready -h localhost -p 6001")
        logger.error("  2. Try connecting manually: psql postgresql://evalscope:evalscope@localhost:6001/evalscope")
        logger.error("  3. If using Docker: docker compose up -d")
        logger.error("  4. Or set DATABASE_URL in backend/.env to point to your Postgres instance")
        raise
    yield
    logger.info("=== Shutting down EvalScope GUI Backend ===")


def _mask_url(url: str) -> str:
    """Mask password in database URL for safe logging."""
    try:
        from urllib.parse import urlparse, urlunparse

        parsed = urlparse(url)
        if parsed.password:
            masked = parsed._replace(
                netloc=f"{parsed.username}:****@{parsed.hostname}:{parsed.port}"
            )
            return urlunparse(masked)
    except Exception:
        pass
    return url


app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
