import json
import sys
import tempfile
import types
import unittest
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import patch

from app.services.evalscope_adapter import (
    _find_numeric_score,
    _normalize_qa_row,
    build_evalscope_task_config,
    convert_dataset_to_general_qa_jsonl,
    extract_primary_score,
    run_evalscope_task,
)
from app.services.storage.local import LocalFileStorage


class TestEvalscopeAdapter(unittest.IsolatedAsyncioTestCase):
    def test_normalize_qa_row_supported_fields(self):
        self.assertEqual(
            _normalize_qa_row({"query": "q", "response": "r"}),
            {"query": "q", "response": "r"},
        )
        self.assertEqual(
            _normalize_qa_row({"prompt": "p", "expected": 1}),
            {"query": "p", "response": "1"},
        )
        self.assertEqual(
            _normalize_qa_row({"input": "i", "output": "o"}),
            {"query": "i", "response": "o"},
        )
        self.assertEqual(
            _normalize_qa_row({"question": "who", "answer": "me"}),
            {"query": "who", "response": "me"},
        )
        self.assertEqual(
            _normalize_qa_row({"query": "only query"}), {"query": "only query"}
        )
        self.assertIsNone(_normalize_qa_row({"unknown": 1}))

    async def test_convert_jsonl_to_general_qa(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalFileStorage(root=tmpdir)

            rows = [
                {"prompt": "2+2=?", "expected": "4"},
                {"query": "capital of China", "response": "Beijing"},
                {"input": "no expected"},
                {"bad": "row without query"},
            ]
            src_key = "src/sample.jsonl"
            await storage.write_file(
                src_key,
                "\n".join(json.dumps(r) for r in rows).encode(),
            )
            src_uri = storage.resolve_uri(src_key)

            out_key = "out/sample.jsonl"
            converted = await convert_dataset_to_general_qa_jsonl(
                storage, src_uri, out_key
            )
            self.assertEqual(converted, 3)

            text = await storage.read_text(out_key)
            lines = [json.loads(ln) for ln in text.splitlines() if ln.strip()]
            self.assertEqual(lines[0], {"query": "2+2=?", "response": "4"})
            self.assertEqual(
                lines[1], {"query": "capital of China", "response": "Beijing"}
            )
            self.assertEqual(lines[2], {"query": "no expected"})

    async def test_convert_json_list(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalFileStorage(root=tmpdir)
            src_key = "src/list.json"
            data = [{"prompt": "a", "expected": "b"}, {"query": "c"}]
            await storage.write_file(src_key, json.dumps(data).encode())
            src_uri = storage.resolve_uri(src_key)

            out_key = "out/list.jsonl"
            converted = await convert_dataset_to_general_qa_jsonl(
                storage, src_uri, out_key
            )
            self.assertEqual(converted, 2)

    async def test_convert_json_dict(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalFileStorage(root=tmpdir)
            src_key = "src/single.json"
            await storage.write_file(
                src_key, json.dumps({"query": "q", "response": "r"}).encode()
            )
            src_uri = storage.resolve_uri(src_key)

            out_key = "out/single.jsonl"
            converted = await convert_dataset_to_general_qa_jsonl(
                storage, src_uri, out_key
            )
            self.assertEqual(converted, 1)

    async def test_convert_skips_blank_lines(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalFileStorage(root=tmpdir)
            src_key = "src/blanks.jsonl"
            content = (
                json.dumps({"query": "q1"})
                + "\n\n   \n"
                + json.dumps({"query": "q2"})
            )
            await storage.write_file(src_key, content.encode())
            src_uri = storage.resolve_uri(src_key)

            out_key = "out/blanks.jsonl"
            converted = await convert_dataset_to_general_qa_jsonl(
                storage, src_uri, out_key
            )
            self.assertEqual(converted, 2)

    def test_build_evalscope_task_config_defaults_and_seed(self):
        fake_config_module = types.ModuleType("evalscope.config")

        class FakeTaskConfig:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

        setattr(fake_config_module, "TaskConfig", FakeTaskConfig)

        with patch.dict(sys.modules, {"evalscope.config": fake_config_module}):
            model = cast(
                Any,
                SimpleNamespace(
                    name="mock-model",
                    endpoint_url="http://127.0.0.1:8801/v1/chat/completions",
                    api_key="real-key",
                ),
            )
            dataset = cast(
                Any,
                SimpleNamespace(source_uri="data/e2e_cases/sample.jsonl"),
            )
            cfg = cast(
                Any,
                build_evalscope_task_config(
                    model=model,
                    dataset=dataset,
                    evalscope_input_root="data/evalscope_input",
                    params={"temperature": 0.2, "seed": 7},
                    repeat_count=0,
                    work_dir="data/evalscope_outputs/task-1",
                ),
            )
            self.assertEqual(cfg.kwargs["model"], "mock-model")
            self.assertEqual(cfg.kwargs["generation_config"]["seed"], 7)
            self.assertEqual(cfg.kwargs["repeats"], 1)

    def test_build_evalscope_task_config_requires_api_key(self):
        fake_config_module = types.ModuleType("evalscope.config")

        class FakeTaskConfig:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

        setattr(fake_config_module, "TaskConfig", FakeTaskConfig)

        with patch.dict(sys.modules, {"evalscope.config": fake_config_module}):
            model = cast(
                Any,
                SimpleNamespace(name="m", endpoint_url="http://api", api_key="  "),
            )
            dataset = cast(Any, SimpleNamespace(source_uri="a/b/case.json"))

            with self.assertRaises(ValueError):
                build_evalscope_task_config(
                    model=model,
                    dataset=dataset,
                    evalscope_input_root="root",
                    params={},
                    repeat_count=1,
                    work_dir="work",
                )

    def test_run_evalscope_task_returns_dict_or_wraps_result(self):
        fake_run_module = types.ModuleType("evalscope.run")

        def fake_run_dict(task_cfg):
            return {"ok": True}

        setattr(fake_run_module, "run_task", fake_run_dict)

        with patch.dict(sys.modules, {"evalscope.run": fake_run_module}):
            self.assertEqual(run_evalscope_task(task_cfg={"x": 1}), {"ok": True})

        def fake_run_non_dict(task_cfg):
            return "done"

        fake_run_module_2 = types.ModuleType("evalscope.run")
        setattr(fake_run_module_2, "run_task", fake_run_non_dict)

        with patch.dict(sys.modules, {"evalscope.run": fake_run_module_2}):
            self.assertEqual(
                run_evalscope_task(task_cfg={"x": 2}), {"result": "done"}
            )

    async def test_extract_primary_score_from_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalFileStorage(root=tmpdir)
            report_key = "work/reports/modelA/general_qa.json"
            payload = {
                "summary": {
                    "metrics": [{"name": "AverageAccuracy", "score": 0.875}],
                }
            }
            await storage.write_file(
                report_key, json.dumps(payload).encode()
            )

            score = await extract_primary_score(storage, "work")
            self.assertAlmostEqual(score, 0.875, places=6)

    async def test_extract_primary_score_no_reports(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalFileStorage(root=tmpdir)
            score = await extract_primary_score(storage, "empty_work")
            self.assertEqual(score, 0.0)

    async def test_extract_primary_score_invalid_json(self):
        from app.errors import ResultIngestionError
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalFileStorage(root=tmpdir)
            await storage.write_file(
                "work/reports/broken.json", b"{not-json"
            )
            with self.assertRaises(ResultIngestionError):
                await extract_primary_score(storage, "work")

    def test_find_numeric_score_variants(self):
        self.assertEqual(_find_numeric_score({"score": 0.1}), 0.1)
        self.assertEqual(_find_numeric_score({"Score": 0.2}), 0.2)
        self.assertEqual(_find_numeric_score({"avg_score": 0.3}), 0.3)
        self.assertEqual(_find_numeric_score({"AverageAccuracy": 0.4}), 0.4)
        self.assertEqual(
            _find_numeric_score([{"x": [{"y": 1}, {"score": 0.6}]}]), 0.6
        )
        self.assertIsNone(
            _find_numeric_score({"a": [{"b": "c"}], "d": {"e": "f"}})
        )


if __name__ == "__main__":
    unittest.main()
