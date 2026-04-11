"""Prometheus HTTP API client for DCGM GPU metrics queries.

Used by report_generator.py to populate GPU utilization / memory peak / power
draw fields for K8s/vLLM tasks. All methods are fail-soft: network errors,
timeouts, malformed responses and empty result sets are logged as WARNING
and return None, never raised. Callers must handle the None fallback.
"""

import logging
from datetime import datetime
from typing import Literal

import httpx

logger = logging.getLogger(__name__)


class PrometheusClient:
    """Thin wrapper around the Prometheus HTTP API."""

    def __init__(self, base_url: str, timeout: float = 5.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def query_instant(self, query: str, at: datetime) -> float | None:
        """Evaluate an instant query at a specific time. Returns None on any failure."""
        params = {"query": query, "time": at.timestamp()}
        data = await self._get("/api/v1/query", params)
        if data is None:
            return None
        return _extract_single_scalar(data)

    async def query_range(
        self,
        query: str,
        start: datetime,
        end: datetime,
        step: str = "30s",
    ) -> list[tuple[datetime, float]]:
        """Evaluate a range query. Returns [] on any failure."""
        params = {
            "query": query,
            "start": start.timestamp(),
            "end": end.timestamp(),
            "step": step,
        }
        data = await self._get("/api/v1/query_range", params)
        if data is None:
            return []
        return _extract_range_series(data)

    async def aggregate_over_window(
        self,
        query: str,
        start: datetime,
        end: datetime,
        agg: Literal["avg", "max", "sum"],
        step: str = "30s",
    ) -> float | None:
        """Query a range then aggregate the samples with the given function.

        Returns None if the query fails or returns no samples.
        """
        series = await self.query_range(query, start, end, step)
        if not series:
            return None
        values = [v for _, v in series]
        if not values:
            return None
        if agg == "avg":
            return sum(values) / len(values)
        if agg == "max":
            return max(values)
        if agg == "sum":
            return sum(values)
        return None

    async def _get(self, path: str, params: dict) -> dict | None:
        url = f"{self.base_url}{path}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(url, params=params)
        except (httpx.TimeoutException, httpx.TransportError) as e:
            logger.warning("Prometheus request failed: %s %s: %s", url, params, e)
            return None
        if resp.status_code != 200:
            logger.warning(
                "Prometheus returned HTTP %s for %s: %s",
                resp.status_code,
                url,
                resp.text[:200],
            )
            return None
        try:
            body = resp.json()
        except ValueError as e:
            logger.warning("Prometheus returned non-JSON body for %s: %s", url, e)
            return None
        if body.get("status") != "success":
            logger.warning(
                "Prometheus query failed for %s: %s", url, body.get("error", "")
            )
            return None
        return body.get("data")


def _extract_single_scalar(data: dict) -> float | None:
    """Extract a single numeric value from a Prometheus `vector` result."""
    result_type = data.get("resultType")
    result = data.get("result") or []
    if not result:
        return None
    if result_type == "vector":
        first = result[0]
        value = first.get("value")
        if not value or len(value) < 2:
            return None
        try:
            return float(value[1])
        except (ValueError, TypeError):
            return None
    if result_type == "scalar":
        if len(result) < 2:
            return None
        try:
            return float(result[1])
        except (ValueError, TypeError):
            return None
    return None


def _extract_range_series(data: dict) -> list[tuple[datetime, float]]:
    """Extract a flat time series from a Prometheus `matrix` result.

    If multiple series are returned (e.g., per-GPU), they are flattened into
    one list of (timestamp, value) tuples. Callers decide how to aggregate.
    """
    if data.get("resultType") != "matrix":
        return []
    series: list[tuple[datetime, float]] = []
    for entry in data.get("result") or []:
        values = entry.get("values") or []
        for ts, raw in values:
            try:
                series.append((datetime.fromtimestamp(float(ts)), float(raw)))
            except (ValueError, TypeError):
                continue
    return series
