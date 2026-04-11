"""Tests for POST /models/preflight-hub — HF / ModelScope preview lookup."""

import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch


def _user_ns(hf_token=""):
    return SimpleNamespace(hf_token=hf_token)


class TestPreflightHub(unittest.IsolatedAsyncioTestCase):
    async def _patch_get(self, response_mock):
        client_mock = AsyncMock()
        client_mock.__aenter__.return_value = client_mock
        client_mock.__aexit__.return_value = None
        client_mock.get = AsyncMock(return_value=response_mock)
        return patch("httpx.AsyncClient", return_value=client_mock)

    async def test_rejects_unknown_source(self):
        from app.api.v1.models import preflight_hub_model

        result = await preflight_hub_model(
            source="foo", model_id="a/b", current_user=_user_ns()
        )
        self.assertFalse(result["ok"])
        self.assertIn("source", result["error"])

    async def test_rejects_invalid_repo(self):
        from app.api.v1.models import preflight_hub_model

        result = await preflight_hub_model(
            source="huggingface", model_id="not-a-repo", current_user=_user_ns()
        )
        self.assertFalse(result["ok"])
        self.assertIn("格式无效", result["error"])

    async def test_extracts_repo_from_full_url(self):
        from app.api.v1.models import preflight_hub_model

        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_resp.json = lambda: {
            "cardData": {"license": "apache-2.0"},
            "pipeline_tag": "text-generation",
            "tags": ["llama", "chat"],
            "downloads": 1000,
            "likes": 42,
            "siblings": [{"size": 1024}],
        }
        with await self._patch_get(mock_resp):
            result = await preflight_hub_model(
                source="huggingface",
                model_id="https://huggingface.co/meta-llama/Llama-3-8B",
                current_user=_user_ns(),
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["repo"], "meta-llama/Llama-3-8B")
        self.assertEqual(result["license"], "apache-2.0")
        self.assertEqual(result["pipeline_tag"], "text-generation")
        self.assertEqual(result["downloads"], 1000)
        self.assertEqual(result["estimated_size_bytes"], 1024)

    async def test_not_found_returns_error(self):
        from app.api.v1.models import preflight_hub_model

        mock_resp = AsyncMock()
        mock_resp.status_code = 404
        mock_resp.text = "Not Found"
        with await self._patch_get(mock_resp):
            result = await preflight_hub_model(
                source="huggingface",
                model_id="nobody/nothing",
                current_user=_user_ns(),
            )
        self.assertFalse(result["ok"])
        self.assertIn("未找到", result["error"])

    async def test_401_asks_for_token(self):
        from app.api.v1.models import preflight_hub_model

        mock_resp = AsyncMock()
        mock_resp.status_code = 401
        with await self._patch_get(mock_resp):
            result = await preflight_hub_model(
                source="huggingface",
                model_id="private/model",
                current_user=_user_ns(),
            )
        self.assertFalse(result["ok"])
        self.assertIn("Token", result["error"])

    async def test_modelscope_source_accepts(self):
        from app.api.v1.models import preflight_hub_model

        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_resp.json = lambda: {
            "license": "MIT",
            "pipeline_tag": "",
            "tags": [],
            "siblings": [],
        }
        with await self._patch_get(mock_resp):
            result = await preflight_hub_model(
                source="modelscope",
                model_id="qwen/Qwen2-7B",
                current_user=_user_ns(),
            )
        self.assertTrue(result["ok"])
        self.assertEqual(result["source"], "modelscope")
        self.assertEqual(result["license"], "MIT")
        self.assertIn("modelscope.cn", result["url"])


if __name__ == "__main__":
    unittest.main()
