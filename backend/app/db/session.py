import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings

logger = logging.getLogger(__name__)

_pg_url = settings.DATABASE_URL
if _pg_url.startswith("postgresql://"):
    _pg_url = _pg_url.replace("postgresql://", "postgresql+asyncpg://", 1)

logger.debug("Async DB URL (driver): %s", _pg_url.split("@")[0].rsplit(":", 1)[0] + ":****@...")

engine = create_async_engine(_pg_url, echo=False, pool_pre_ping=True)
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
