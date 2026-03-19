"""Unified storage abstraction for local filesystem and S3."""

from __future__ import annotations

import logging

from app.config import settings
from app.services.storage.base import StorageBackend

logger = logging.getLogger(__name__)

_instance: StorageBackend | None = None


def get_storage() -> StorageBackend:
    """Return the singleton storage backend based on settings."""
    global _instance
    if _instance is not None:
        return _instance

    backend = settings.STORAGE_BACKEND.lower()
    if backend == "s3":
        from app.services.storage.s3 import S3Storage

        _instance = S3Storage(
            bucket=settings.S3_BUCKET,
            endpoint_url=settings.S3_ENDPOINT_URL,
            access_key=settings.S3_ACCESS_KEY,
            secret_key=settings.S3_SECRET_KEY,
            region=settings.S3_REGION,
            prefix=settings.S3_PREFIX,
        )
        logger.info("Storage backend: S3 (bucket=%s)", settings.S3_BUCKET)
    else:
        from app.services.storage.local import LocalFileStorage

        _instance = LocalFileStorage(root=settings.STORAGE_ROOT)
        logger.info("Storage backend: local (%s)", settings.STORAGE_ROOT)

    return _instance


__all__ = ["StorageBackend", "get_storage"]
