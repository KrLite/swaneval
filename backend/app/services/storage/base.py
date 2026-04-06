"""Abstract storage backend interface."""

from __future__ import annotations

from abc import ABC, abstractmethod


class StorageBackend(ABC):
    """Unified file storage interface for local filesystem and S3."""

    @abstractmethod
    async def write_file(self, key: str, data: bytes) -> str:
        """Write bytes to storage. Returns the storage URI."""

    @abstractmethod
    async def read_file(self, key: str) -> bytes:
        """Read entire file as bytes."""

    @abstractmethod
    async def read_text(self, key: str, encoding: str = "utf-8") -> str:
        """Read entire file as text."""

    @abstractmethod
    async def read_lines(self, key: str, max_lines: int = 0, encoding: str = "utf-8") -> list[str]:
        """Read file lines. If max_lines > 0, return at most that many non-empty lines."""

    @abstractmethod
    async def delete_file(self, key: str) -> bool:
        """Delete a file. Returns True if actually deleted."""

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if a file exists."""

    @abstractmethod
    async def file_size(self, key: str) -> int:
        """Get file size in bytes."""

    @abstractmethod
    async def list_files(self, prefix: str, patterns: list[str] | None = None) -> list[str]:
        """List file keys under prefix, optionally filtered by glob patterns.

        Returns keys relative to the storage root (same format as other methods).
        Excludes directories, returns only files.
        """

    @abstractmethod
    def resolve_uri(self, key: str) -> str:
        """Return the full URI for external consumption.

        - LocalFileStorage: absolute local path
        - S3Storage: s3://bucket/prefix/key
        """

    @abstractmethod
    async def ensure_prefix(self, prefix: str) -> None:
        """Ensure a prefix/directory exists (mkdir for local, no-op for S3)."""

    @abstractmethod
    async def validate(self) -> None:
        """Check that the backend is accessible. Raise on failure."""
