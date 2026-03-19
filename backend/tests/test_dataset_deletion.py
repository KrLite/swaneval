import tempfile
import unittest
import uuid
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import patch

from app.models.dataset import SourceType
from app.services.dataset_deletion import cleanup_uploaded_file, delete_dataset_versions
from app.services.storage.local import LocalFileStorage


class _FakeExecResult:
    def __init__(self, items):
        self._items = items

    def all(self):
        return list(self._items)


class _FakeSession:
    def __init__(self, versions):
        self.versions = versions
        self.deleted = []

    async def exec(self, stmt):
        _ = stmt
        return _FakeExecResult(self.versions)

    async def delete(self, item):
        self.deleted.append(item)


class TestDatasetDeletion(unittest.IsolatedAsyncioTestCase):
    async def test_cleanup_uploaded_file_non_upload_or_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalFileStorage(root=tmpdir)

            ds_not_upload = cast(
                Any,
                SimpleNamespace(source_type=SourceType.server_path, source_uri="/tmp/x"),
            )
            self.assertFalse(await cleanup_uploaded_file(storage, ds_not_upload))

            ds_empty_path = cast(
                Any,
                SimpleNamespace(source_type=SourceType.upload, source_uri=""),
            )
            self.assertFalse(await cleanup_uploaded_file(storage, ds_empty_path))

    async def test_cleanup_uploaded_file_success(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalFileStorage(root=tmpdir)

            key = "uploads/sample.jsonl"
            await storage.write_file(key, b"{}\n")
            uri = storage.resolve_uri(key)

            with patch("app.services.storage.utils.settings") as mock_settings:
                mock_settings.STORAGE_ROOT = tmpdir
                mock_settings.S3_BUCKET = ""
                mock_settings.S3_PREFIX = ""

                ds_ok = cast(
                    Any,
                    SimpleNamespace(source_type=SourceType.upload, source_uri=uri),
                )
                self.assertTrue(await cleanup_uploaded_file(storage, ds_ok))
                self.assertFalse(await storage.exists(key))

    async def test_cleanup_uploaded_file_not_exists(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalFileStorage(root=tmpdir)
            uri = storage.resolve_uri("uploads/nonexistent.jsonl")

            with patch("app.services.storage.utils.settings") as mock_settings:
                mock_settings.STORAGE_ROOT = tmpdir
                mock_settings.S3_BUCKET = ""
                mock_settings.S3_PREFIX = ""

                ds = cast(
                    Any,
                    SimpleNamespace(source_type=SourceType.upload, source_uri=uri),
                )
                self.assertFalse(await cleanup_uploaded_file(storage, ds))

    async def test_delete_dataset_versions(self):
        versions = [
            cast(Any, SimpleNamespace(id=uuid.uuid4())),
            cast(Any, SimpleNamespace(id=uuid.uuid4())),
            cast(Any, SimpleNamespace(id=uuid.uuid4())),
        ]
        session = _FakeSession(versions)

        deleted_count = await delete_dataset_versions(cast(Any, session), uuid.uuid4())

        self.assertEqual(deleted_count, 3)
        self.assertEqual(session.deleted, versions)


if __name__ == "__main__":
    unittest.main()
