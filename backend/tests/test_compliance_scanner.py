"""Tests for compliance_scanner — license policy and Hub fetch."""

import unittest
from unittest.mock import AsyncMock, patch

from app.services.compliance_scanner import (
    evaluate_license_policy,
    fetch_hub_license,
    scan_image_cves,
)


class TestLicensePolicy(unittest.TestCase):
    def test_apache_is_compliant(self):
        self.assertEqual(evaluate_license_policy("apache-2.0"), "compliant")

    def test_mit_is_compliant(self):
        self.assertEqual(evaluate_license_policy("MIT"), "compliant")

    def test_cc_nc_is_restricted(self):
        self.assertEqual(evaluate_license_policy("cc-by-nc-4.0"), "restricted")

    def test_gpl3_is_restricted(self):
        self.assertEqual(evaluate_license_policy("GPL-3.0"), "restricted")

    def test_other_is_restricted(self):
        self.assertEqual(evaluate_license_policy("other"), "restricted")

    def test_unknown_license_is_unknown(self):
        self.assertEqual(
            evaluate_license_policy("super-custom-license-v1"), "unknown"
        )

    def test_empty_license_is_unknown(self):
        self.assertEqual(evaluate_license_policy(""), "unknown")

    def test_llama3_is_compliant(self):
        self.assertEqual(evaluate_license_policy("llama3"), "compliant")


class TestFetchHubLicense(unittest.IsolatedAsyncioTestCase):
    async def _patch_get(self, response_mock):
        client_mock = AsyncMock()
        client_mock.__aenter__.return_value = client_mock
        client_mock.__aexit__.return_value = None
        client_mock.get = AsyncMock(return_value=response_mock)
        return patch("httpx.AsyncClient", return_value=client_mock)

    async def test_unsupported_source(self):
        result = await fetch_hub_license("foo", "a/b")
        self.assertFalse(result["ok"])

    async def test_hf_success_from_cardData(self):
        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_resp.json = lambda: {"cardData": {"license": "apache-2.0"}}
        with await self._patch_get(mock_resp):
            result = await fetch_hub_license("huggingface", "meta/llama")
        self.assertTrue(result["ok"])
        self.assertEqual(result["license_spdx"], "apache-2.0")

    async def test_hf_fallback_top_level_license(self):
        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_resp.json = lambda: {"license": "mit"}
        with await self._patch_get(mock_resp):
            result = await fetch_hub_license("huggingface", "org/repo")
        self.assertTrue(result["ok"])
        self.assertEqual(result["license_spdx"], "mit")

    async def test_hf_404(self):
        mock_resp = AsyncMock()
        mock_resp.status_code = 404
        mock_resp.text = "Not Found"
        with await self._patch_get(mock_resp):
            result = await fetch_hub_license("huggingface", "nobody/nothing")
        self.assertFalse(result["ok"])
        self.assertIn("404", result["error"])


class TestScanImageCves(unittest.TestCase):
    def test_empty_image_ref(self):
        self.assertEqual(scan_image_cves(""), [])

    def test_trivy_missing_returns_empty(self):
        with patch(
            "app.services.compliance_scanner.subprocess.run",
            side_effect=FileNotFoundError(),
        ):
            self.assertEqual(scan_image_cves("some/image:tag"), [])

    def test_trivy_success_parses_findings(self):
        import json
        from types import SimpleNamespace

        trivy_output = {
            "Results": [
                {
                    "Vulnerabilities": [
                        {
                            "VulnerabilityID": "CVE-2024-1234",
                            "Severity": "HIGH",
                            "Title": "Remote code execution in foo",
                        },
                        {
                            "VulnerabilityID": "CVE-2024-5678",
                            "Severity": "LOW",
                            "Title": "Info leak in bar",
                        },
                    ]
                }
            ]
        }
        mock_result = SimpleNamespace(
            returncode=0,
            stdout=json.dumps(trivy_output).encode(),
            stderr=b"",
        )
        with patch(
            "app.services.compliance_scanner.subprocess.run",
            return_value=mock_result,
        ):
            findings = scan_image_cves("test/image:latest")
        self.assertEqual(len(findings), 2)
        self.assertEqual(findings[0]["id"], "CVE-2024-1234")
        self.assertEqual(findings[0]["severity"], "HIGH")


if __name__ == "__main__":
    unittest.main()
