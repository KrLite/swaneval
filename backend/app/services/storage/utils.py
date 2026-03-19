"""Storage utility functions."""

from __future__ import annotations

from app.config import settings


def uri_to_key(source_uri: str) -> str | None:
    """Convert a stored source_uri back to a storage key.

    Returns None if the URI is an external/mounted path that is not managed
    by the storage backend (e.g. an absolute server path from ``mount``).
    """
    if not source_uri:
        return None

    # S3 URI: s3://bucket/prefix/key → extract key after bucket(+prefix)
    if source_uri.startswith("s3://"):
        parts = source_uri[5:]  # strip "s3://"
        # strip bucket name
        bucket = settings.S3_BUCKET
        if parts.startswith(bucket + "/"):
            after_bucket = parts[len(bucket) + 1 :]
            # strip S3_PREFIX if present
            prefix = (settings.S3_PREFIX or "").strip("/")
            if prefix and after_bucket.startswith(prefix + "/"):
                return after_bucket[len(prefix) + 1 :]
            return after_bucket
        return None

    # Local storage: relative path under STORAGE_ROOT
    root = settings.STORAGE_ROOT
    # Handle both "data/uploads/x.jsonl" and "/abs/data/uploads/x.jsonl"
    if source_uri.startswith(root + "/"):
        return source_uri[len(root) + 1 :]

    # Absolute path that was resolved at write time
    from pathlib import Path

    try:
        resolved_root = str(Path(root).resolve())
        if source_uri.startswith(resolved_root + "/"):
            return source_uri[len(resolved_root) + 1 :]
    except Exception:
        pass

    # Not a storage-managed path (e.g. mounted server path)
    return None
