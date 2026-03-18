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

    logger.info("Connecting to database...")
    try:
        async with engine.begin() as conn:
            logger.info("Database connection established successfully")
            await conn.run_sync(SQLModel.metadata.create_all)
            logger.info("Database tables created/verified")
    except Exception as exc:
        logger.error("!!! DATABASE CONNECTION FAILED !!!")
        logger.error("Error: %s: %s", type(exc).__name__, exc)
        logger.error("Is PostgreSQL running? Try: docker compose up -d")
        raise
    yield
    logger.info("=== Shutting down EvalScope GUI Backend ===")


def _mask_url(url: str) -> str:
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
