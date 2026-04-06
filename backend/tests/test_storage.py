"""Unit tests for the storage abstraction layer."""

import json
import os
import tempfile
import unittest
from pathlib import Path

from app.services.storage.local import LocalFileStorage


class TestLocalFileStorage(unittest.IsolatedAsyncioTestCase):
    """Test LocalFileStorage against a temporary directory."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.root = self._tmpdir.name
        self.storage = LocalFileStorage(root=self.root)

    def tearDown(self):
        self._tmpdir.cleanup()

    # -- write / read ---------------------------------------------------

    async def test_write_and_read_file(self):
        data = b"hello world"
        uri = await self.storage.write_file("uploads/test.txt", data)
        self.assertIn("test.txt", uri)
        self.assertTrue(Path(uri).exists())

        result = await self.storage.read_file("uploads/test.txt")
        self.assertEqual(result, data)

    async def test_write_creates_parent_dirs(self):
        await self.storage.write_file("a/b/c/deep.txt", b"ok")
        self.assertTrue((Path(self.root) / "a" / "b" / "c" / "deep.txt").exists())

    async def test_read_text(self):
        content = "你好世界"
        await self.storage.write_file("text.txt", content.encode("utf-8"))
        result = await self.storage.read_text("text.txt")
        self.assertEqual(result, content)

    async def test_read_lines(self):
        lines_data = "line1\nline2\nline3\nline4\n"
        await self.storage.write_file("lines.txt", lines_data.encode())

        all_lines = await self.storage.read_lines("lines.txt")
        self.assertEqual(len(all_lines), 4)
        self.assertEqual(all_lines[0], "line1")

        limited = await self.storage.read_lines("lines.txt", max_lines=2)
        self.assertEqual(len(limited), 2)

    async def test_read_lines_jsonl(self):
        rows = [
            json.dumps({"query": "q1", "response": "r1"}),
            json.dumps({"query": "q2"}),
            "",
        ]
        await self.storage.write_file("data.jsonl", "\n".join(rows).encode())

        lines = await self.storage.read_lines("data.jsonl")
        non_empty = [ln for ln in lines if ln.strip()]
        self.assertEqual(len(non_empty), 2)

    # -- delete / exists / size -----------------------------------------

    async def test_exists_and_delete(self):
        self.assertFalse(await self.storage.exists("nope.txt"))

        await self.storage.write_file("to_delete.txt", b"bye")
        self.assertTrue(await self.storage.exists("to_delete.txt"))

        deleted = await self.storage.delete_file("to_delete.txt")
        self.assertTrue(deleted)
        self.assertFalse(await self.storage.exists("to_delete.txt"))

        # Delete non-existent returns False
        self.assertFalse(await self.storage.delete_file("to_delete.txt"))

    async def test_file_size(self):
        data = b"12345"
        await self.storage.write_file("sized.bin", data)
        size = await self.storage.file_size("sized.bin")
        self.assertEqual(size, 5)

    # -- listing --------------------------------------------------------

    async def test_list_files_no_pattern(self):
        await self.storage.write_file("dir/a.txt", b"a")
        await self.storage.write_file("dir/b.json", b"b")
        await self.storage.write_file("dir/sub/c.jsonl", b"c")

        files = await self.storage.list_files("dir")
        self.assertEqual(len(files), 3)
        self.assertTrue(any("a.txt" in f for f in files))
        self.assertTrue(any("c.jsonl" in f for f in files))

    async def test_list_files_with_pattern(self):
        await self.storage.write_file("out/report.json", b"{}")
        await self.storage.write_file("out/data.jsonl", b"")
        await self.storage.write_file("out/readme.txt", b"")
        await self.storage.write_file("out/sub/nested.json", b"{}")

        json_files = await self.storage.list_files("out", patterns=["*.json"])
        self.assertEqual(len(json_files), 2)

        jsonl_files = await self.storage.list_files("out", patterns=["*.jsonl"])
        self.assertEqual(len(jsonl_files), 1)

        both = await self.storage.list_files("out", patterns=["*.json", "*.jsonl"])
        self.assertEqual(len(both), 3)

    async def test_list_files_empty_dir(self):
        files = await self.storage.list_files("nonexistent")
        self.assertEqual(files, [])

    async def test_list_files_filters_input_configs(self):
        """Verify that list_files returns raw file list (filtering is caller's job)."""
        await self.storage.write_file("work/input/data.jsonl", b"")
        await self.storage.write_file("work/configs/cfg.json", b"")
        await self.storage.write_file("work/reports/out.json", b"{}")

        files = await self.storage.list_files("work", patterns=["*.json", "*.jsonl"])
        # list_files returns all matches — filtering input/configs is done by callers
        self.assertEqual(len(files), 3)

    # -- resolve / ensure / validate ------------------------------------

    async def test_resolve_uri(self):
        uri = self.storage.resolve_uri("uploads/test.jsonl")
        # OS-native absolute path — on Unix starts with /, on Windows C:\...
        self.assertTrue(os.path.isabs(uri))
        # Should end with the key components (OS-native separator)
        self.assertIn("uploads", uri)
        self.assertIn("test.jsonl", uri)

    async def test_ensure_prefix(self):
        await self.storage.ensure_prefix("new_dir/sub")
        self.assertTrue((Path(self.root) / "new_dir" / "sub").is_dir())

    async def test_validate(self):
        # Should not raise
        await self.storage.validate()

    async def test_validate_creates_root(self):
        new_root = Path(self.root) / "fresh"
        storage = LocalFileStorage(root=str(new_root))
        await storage.validate()
        self.assertTrue(new_root.is_dir())


if __name__ == "__main__":
    unittest.main()
