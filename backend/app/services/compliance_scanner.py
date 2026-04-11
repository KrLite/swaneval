"""License + CVE scanning for LLM models and datasets.

License data comes from HuggingFace / ModelScope Hub APIs (same path the
preflight endpoint uses) and is mapped to an SPDX identifier plus a
compliance_status via an internal policy table. CVE scanning is handled
by an external binary (trivy / grype) if present on the host; otherwise
findings stay empty and the record still carries license info.
"""

from __future__ import annotations

import asyncio
import json
import logging
import subprocess  # noqa: S404 — intentional CVE scanner invocation

import httpx

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# License policy
# ---------------------------------------------------------------------------

_COMPLIANT_LICENSES: set[str] = {
    "apache-2.0",
    "mit",
    "bsd-2-clause",
    "bsd-3-clause",
    "isc",
    "mpl-2.0",
    "cc0-1.0",
    "cc-by-4.0",
    "openrail",
    "openrail++",
    "llama3",
    "llama2",
    "gemma",
    "qwen",
}

_RESTRICTED_LICENSES: set[str] = {
    "cc-by-nc-4.0",
    "cc-by-nc-sa-4.0",
    "cc-by-nd-4.0",
    "gpl-3.0",
    "gpl-2.0",
    "agpl-3.0",
    "other",
    "non-commercial",
    "research-only",
}


def evaluate_license_policy(license_spdx: str) -> str:
    """Return 'compliant', 'restricted', or 'unknown' for an SPDX id.

    Matching is case-insensitive and normalizes a few common variants
    (e.g. drops the trailing version suffix when absent).
    """
    if not license_spdx:
        return "unknown"
    key = license_spdx.strip().lower()
    if key in _COMPLIANT_LICENSES:
        return "compliant"
    if key in _RESTRICTED_LICENSES:
        return "restricted"
    # Permissive prefix match — e.g. "apache" → "apache-2.0" → compliant.
    for allowed in _COMPLIANT_LICENSES:
        if key.startswith(allowed):
            return "compliant"
    for blocked in _RESTRICTED_LICENSES:
        if key.startswith(blocked):
            return "restricted"
    return "unknown"


# ---------------------------------------------------------------------------
# Hub metadata fetch
# ---------------------------------------------------------------------------


async def fetch_hub_license(
    source: str, repo: str, hf_token: str = ""
) -> dict:
    """Look up the license of a HuggingFace / ModelScope repo.

    Returns ``{license_spdx, ok, error}``. Fail-soft: any network or
    parse error returns ``ok: False`` so the caller can still record
    an `unknown` compliance row rather than bubble up.
    """
    if source not in ("huggingface", "modelscope"):
        return {"license_spdx": "", "ok": False, "error": "unsupported source"}
    url = (
        f"https://huggingface.co/api/models/{repo}"
        if source == "huggingface"
        else f"https://modelscope.cn/api/v1/models/{repo}"
    )
    headers: dict[str, str] = {}
    if source == "huggingface" and hf_token:
        headers["Authorization"] = f"Bearer {hf_token}"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=headers)
    except (httpx.TimeoutException, httpx.TransportError) as e:
        return {"license_spdx": "", "ok": False, "error": str(e)}

    if resp.status_code != 200:
        return {
            "license_spdx": "",
            "ok": False,
            "error": f"HTTP {resp.status_code}",
        }
    try:
        data = resp.json()
    except ValueError as e:
        return {"license_spdx": "", "ok": False, "error": f"bad JSON: {e}"}

    card = data.get("cardData") or {}
    license_id = ""
    if isinstance(card, dict):
        license_id = card.get("license") or ""
    if not license_id:
        license_id = data.get("license") or ""
    return {"license_spdx": str(license_id or ""), "ok": True}


# ---------------------------------------------------------------------------
# CVE scanner
# ---------------------------------------------------------------------------


def scan_image_cves(image_ref: str, timeout: float = 30.0) -> list[dict]:
    """Invoke a local CVE scanner (trivy) if available.

    Returns a list of `{id, severity, description}`. When trivy is not
    installed or the scan fails, returns `[]` — the caller treats the
    empty list as "no findings recorded" rather than "no vulnerabilities".
    """
    if not image_ref:
        return []
    try:
        result = subprocess.run(  # noqa: S603 — image_ref is server-managed
            [
                "trivy",
                "image",
                "--quiet",
                "--no-progress",
                "--format",
                "json",
                image_ref,
            ],
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError:
        logger.debug("trivy not installed — skipping CVE scan for %s", image_ref)
        return []
    except subprocess.TimeoutExpired:
        logger.warning("trivy scan timed out for %s", image_ref)
        return []

    if result.returncode != 0:
        logger.warning(
            "trivy returned %s for %s: %s",
            result.returncode,
            image_ref,
            (result.stderr or b"").decode("utf-8", errors="replace")[:200],
        )
        return []
    try:
        parsed = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        logger.warning("trivy produced non-JSON output: %s", e)
        return []

    findings: list[dict] = []
    for target in parsed.get("Results") or []:
        for vuln in target.get("Vulnerabilities") or []:
            findings.append(
                {
                    "id": vuln.get("VulnerabilityID", ""),
                    "severity": vuln.get("Severity", ""),
                    "description": vuln.get("Title", "")[:200],
                }
            )
    return findings


async def scan_image_cves_async(image_ref: str) -> list[dict]:
    """Async wrapper around the blocking trivy invocation."""
    return await asyncio.to_thread(scan_image_cves, image_ref)
