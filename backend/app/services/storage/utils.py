"""Storage utility functions."""

from __future__ import annotations

import logging
import os

from app.config import settings

logger = logging.getLogger(__name__)


def uri_to_key(source_uri: str) -> str | None:
    """Convert a stored source_uri back to a storage key.

    Returns None if the URI is an external/mounted path that is not managed
    by the storage backend (e.g. an absolute server path from ``mount``).

    Keys always use forward slashes regardless of OS.
    """
    if not source_uri:
        return None

    # S3 URI: s3://bucket/prefix/key → extract key after bucket(+prefix)
    if source_uri.startswith("s3://"):
        parts = source_uri[5:]  # strip "s3://"
        bucket = settings.S3_BUCKET
        if parts.startswith(bucket + "/"):
            after_bucket = parts[len(bucket) + 1 :]
            prefix = (settings.S3_PREFIX or "").strip("/")
            if prefix and after_bucket.startswith(prefix + "/"):
                return after_bucket[len(prefix) + 1 :]
            return after_bucket
        return None

    # Normalize to forward slashes for comparison (Windows compat)
    normalized = source_uri.replace("\\", "/")

    # Local storage: relative path under STORAGE_ROOT
    root = settings.STORAGE_ROOT.replace("\\", "/")
    if normalized.startswith(root + "/"):
        return normalized[len(root) + 1 :]

    # Absolute path that was resolved at write time
    from pathlib import Path

    try:
        resolved_root = str(Path(root).resolve()).replace("\\", "/")
        if normalized.startswith(resolved_root + "/"):
            return normalized[len(resolved_root) + 1 :]
    except Exception as e:
        logger.warning("Failed to resolve STORAGE_ROOT '%s': %s", root, e)

    # Also try os.sep-native comparison for Windows paths like C:\foo\bar
    if os.sep == "\\":
        native_root = str(Path(root).resolve())
        if source_uri.startswith(native_root + os.sep):
            key = source_uri[len(native_root) + 1 :]
            return key.replace("\\", "/")

    # Not a storage-managed path (e.g. mounted server path)
    return None
