import json
from collections.abc import AsyncGenerator
from pathlib import Path

from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)

# ── Load preset data from JSON files ──────────────────────────────
_DATA_DIR = Path(__file__).parent / "data"

with open(_DATA_DIR / "preset_datasets.json", encoding="utf-8") as _f:
    PRESET_DATASETS: list[dict] = json.load(_f)

with open(_DATA_DIR / "preset_criteria.json", encoding="utf-8") as _f:
    PRESET_CRITERIA: list[dict] = json.load(_f)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(engine) as session:
        yield session


async def init_db():
    """
    Initialize database.

    Skips create_all when Alembic manages the schema.
    """
    from sqlalchemy import inspect

    async with engine.begin() as conn:
        has_alembic = await conn.run_sync(
            lambda sync_conn: inspect(sync_conn).has_table("alembic_version")
        )
        if not has_alembic:
            await conn.run_sync(SQLModel.metadata.create_all)
