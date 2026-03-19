"""Dataset deletion helpers to keep API layer thin and testable."""

from __future__ import annotations

import uuid

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.dataset import Dataset, DatasetVersion, SourceType
from app.services.storage.base import StorageBackend
from app.services.storage.utils import uri_to_key


async def cleanup_uploaded_file(storage: StorageBackend, dataset: Dataset) -> bool:
    """Delete uploaded dataset file from storage if it exists.

    Returns True only when a file is actually removed.
    """
    if dataset.source_type != SourceType.upload:
        return False
    if not dataset.source_uri:
        return False

    key = uri_to_key(dataset.source_uri)
    if key is None:
        return False

    if not await storage.exists(key):
        return False

    return await storage.delete_file(key)


async def delete_dataset_versions(session: AsyncSession, dataset_id: uuid.UUID) -> int:
    """Delete all version rows for a dataset and return deleted row count."""
    stmt = select(DatasetVersion).where(DatasetVersion.dataset_id == dataset_id)
    result = await session.exec(stmt)
    versions = result.all()
    for version in versions:
        await session.delete(version)
    return len(versions)
