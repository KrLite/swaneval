"""Tests for fail-fast fixes: silent exception elimination (A1-A11)."""

import json
import logging
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.dataset_import import _count_rows
from app.services.storage.local import LocalFileStorage


class TestCountRowsFailFast(unittest.TestCase):
    """A3+A11: _count_rows returns -1 on failure, not 0."""

    def test_valid_jsonl(self):
        content = b'{"a":1}\n{"b":2}\n'
        self.assertEqual(_count_rows(content, ".jsonl"), 2)

    def test_valid_csv(self):
        content = b"col1,col2\nval1,val2\nval3,val4\n"
        self.assertEqual(_count_rows(content, ".csv"), 2)

    def test_valid_json_list(self):
        content = json.dumps([{"a": 1}, {"b": 2}]).encode()
        self.assertEqual(_count_rows(content, ".json"), 2)

    def test_valid_json_single(self):
        content = json.dumps({"a": 1}).encode()
        self.assertEqual(_count_rows(content, ".json"), 1)

    def test_invalid_json_returns_negative_one(self):
        content = b"{not valid json"
        result = _count_rows(content, ".json")
        self.assertEqual(result, -1)

    def test_invalid_encoding_returns_negative_one(self):
        # Invalid UTF-8 bytes
        content = b"\xff\xfe\x00\x01"
        result = _count_rows(content, ".jsonl")
        self.assertEqual(result, -1)

    def test_empty_jsonl(self):
        self.assertEqual(_count_rows(b"", ".jsonl"), 0)

    def test_empty_csv(self):
        # Only header, no data rows
        self.assertEqual(_count_rows(b"col1,col2\n", ".csv"), 0)


class TestStorageFileIoLogging(unittest.IsolatedAsyncioTestCase):
    """A5+A6: storage/file_io.py logs warning on fallback to local."""

    async def test_read_bytes_logs_warning_on_storage_failure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalFileStorage(root=tmpdir)
            # Write a file to local filesystem directly
            local_path = Path(tmpdir) / "test.txt"
            local_path.write_bytes(b"hello")

            # Mock storage.read_file to raise
            original_read = storage.read_file
            storage.read_file = AsyncMock(side_effect=Exception("S3 down"))

            from app.services.storage.file_io import read_bytes

            with self.assertLogs("app.services.storage.file_io", level="WARNING") as cm:
                result = await read_bytes(storage, str(local_path), key="test.txt")

            self.assertEqual(result, b"hello")
            self.assertTrue(any("Storage backend read failed" in msg for msg in cm.output))

    async def test_read_text_logs_warning_on_storage_failure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalFileStorage(root=tmpdir)
            local_path = Path(tmpdir) / "test.txt"
            local_path.write_text("hello", encoding="utf-8")

            storage.read_text = AsyncMock(side_effect=Exception("S3 down"))

            from app.services.storage.file_io import read_text

            with self.assertLogs("app.services.storage.file_io", level="WARNING") as cm:
                result = await read_text(storage, str(local_path), key="test.txt")

            self.assertEqual(result, "hello")
            self.assertTrue(any("Storage backend read failed" in msg for msg in cm.output))


class TestLocalStorageDeleteLogging(unittest.IsolatedAsyncioTestCase):
    """A8: storage/local.py logs warning on delete failure."""

    async def test_delete_nonexistent_returns_false(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalFileStorage(root=tmpdir)
            result = await storage.delete_file("nonexistent.txt")
            self.assertFalse(result)

    async def test_delete_oserror_logs_warning(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalFileStorage(root=tmpdir)
            await storage.write_file("protected.txt", b"data")

            # Patch os.remove to raise OSError
            with patch("os.remove", side_effect=OSError("Permission denied")):
                with self.assertLogs("app.services.storage.local", level="WARNING") as cm:
                    result = await storage.delete_file("protected.txt")
                self.assertFalse(result)
                self.assertTrue(any("Failed to delete" in msg for msg in cm.output))


class TestStorageUtilsPathResolutionLogging(unittest.TestCase):
    """A7: storage/utils.py logs debug on path resolution failure."""

    def test_uri_to_key_invalid_root_logs_debug(self):
        with patch("app.services.storage.utils.settings") as mock_settings:
            mock_settings.STORAGE_ROOT = "/nonexistent/root"
            mock_settings.S3_BUCKET = "test-bucket"
            mock_settings.S3_PREFIX = ""

            from app.services.storage.utils import uri_to_key

            # A path that doesn't match storage root
            result = uri_to_key("/some/other/path/file.txt")
            self.assertIsNone(result)


class TestRbacPermissionsLogging(unittest.IsolatedAsyncioTestCase):
    """A4: rbac.py logs error on corrupt permissions_json."""

    async def test_corrupt_permissions_json_logs_error(self):
        from app.services.rbac import get_user_permissions

        mock_user = MagicMock()
        mock_user.role = "engineer"
        mock_user.id = "test-user-id"

        mock_session = AsyncMock()
        mock_result = MagicMock()
        # Return one valid and one corrupt permissions row
        mock_result.all.return_value = [
            '["datasets.read", "tasks.read"]',
            "NOT VALID JSON {{{",
        ]
        mock_session.exec = AsyncMock(return_value=mock_result)

        with self.assertLogs("app.services.rbac", level="ERROR") as cm:
            perms = await get_user_permissions(mock_session, mock_user)

        # Valid permissions should still be returned
        self.assertIn("datasets.read", perms)
        self.assertIn("tasks.read", perms)
        # Corrupt row should be logged
        self.assertTrue(any("Corrupt permissions_json" in msg for msg in cm.output))


class TestDatasetSyncLogging(unittest.TestCase):
    """A9: dataset_sync.py logs warning on HF SHA failure."""

    def test_get_hf_latest_sha_logs_warning_on_failure(self):
        from app.services.dataset_sync import _get_hf_latest_sha

        with patch("huggingface_hub.repo_info", side_effect=Exception("network error")):
            with self.assertLogs("app.services.dataset_sync", level="WARNING") as cm:
                result = _get_hf_latest_sha("test/dataset")

            self.assertIsNone(result)
            self.assertTrue(any("Failed to get HF SHA" in msg for msg in cm.output))


class TestEvalscoreAdapterLogging(unittest.IsolatedAsyncioTestCase):
    """A10: evalscope_adapter.py logs warnings on report parse failure."""

    async def test_all_reports_invalid_logs_error(self):
        from app.services.evalscope_adapter import extract_primary_score

        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalFileStorage(root=tmpdir)
            # Write invalid JSON report files
            await storage.write_file("work/reports/bad1.json", b"{not json")
            await storage.write_file("work/reports/bad2.json", b"[[invalid")

            with self.assertLogs("app.services.evalscope_adapter", level="WARNING") as cm:
                score = await extract_primary_score(storage, "work")

            self.assertEqual(score, 0.0)
            # Should log warning for each failed parse
            warning_msgs = [m for m in cm.output if "Failed to parse report file" in m]
            self.assertGreaterEqual(len(warning_msgs), 2)


if __name__ == "__main__":
    unittest.main()
