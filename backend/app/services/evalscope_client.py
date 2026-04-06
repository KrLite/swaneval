"""HTTP client for the EvalScope evaluation service."""

import asyncio
import logging
from collections.abc import Callable, Coroutine
from typing import Any

import httpx

from app.config import settings
from app.errors import EvalScopeServiceError, EvalScopeTimeoutError

logger = logging.getLogger(__name__)


class EvalScopeClient:
    """Async wrapper around the EvalScope HTTP service."""

    async def __aenter__(self) -> "EvalScopeClient":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    def __init__(
        self,
        base_url: str | None = None,
        timeout: int | None = None,
        poll_interval: int | None = None,
    ):
        self.base_url = (base_url or settings.EVALSCOPE_SERVICE_URL).rstrip("/")
        self.timeout = timeout or settings.EVALSCOPE_TIMEOUT_SECONDS
        self.poll_interval = poll_interval or settings.EVALSCOPE_POLL_INTERVAL
        self._async_client = httpx.AsyncClient(timeout=self.timeout)

    async def close(self) -> None:
        await self._async_client.aclose()

    # ── Health ────────────────────────────────────────────────────

    async def health_check(self, retries: int = 3) -> bool:
        """Return True if the EvalScope service is healthy."""
        for attempt in range(retries):
            try:
                resp = await self._async_client.get(
                    f"{self.base_url}/health",
                    timeout=5,
                )
                if resp.status_code == 200:
                    return True
            except Exception:
                if attempt < retries - 1:
                    await asyncio.sleep(1)
        return False

    # ── Evaluation ────────────────────────────────────────────────

    async def invoke_eval(
        self,
        config: dict[str, Any],
        on_progress: Callable[[dict], Coroutine] | None = None,
    ) -> dict[str, Any]:
        """Run an evaluation via the EvalScope service.

        The ``POST /api/v1/eval/invoke`` endpoint does not return until the
        evaluation completes. Use the shared ``AsyncClient`` so the event loop
        remains non-blocking while progress polling runs concurrently.
        """
        done = asyncio.Event()
        result_holder: dict[str, Any] = {}
        error_holder: list[Exception] = []

        async def _do_invoke():
            try:
                resp = await self._async_client.post(
                    f"{self.base_url}/api/v1/eval/invoke",
                    json=config,
                )
                if resp.status_code >= 400:
                    error_holder.append(
                        EvalScopeServiceError(
                            f"EvalScope returned {resp.status_code}: {resp.text[:500]}"
                        )
                    )
                    return
                result_holder["data"] = resp.json()
            except httpx.TimeoutException as e:
                error_holder.append(
                    EvalScopeTimeoutError(
                        f"EvalScope evaluation timed out after {self.timeout}s: {e}"
                    )
                )
            except Exception as e:
                err = EvalScopeServiceError(f"EvalScope invocation failed: {e}")
                err.__cause__ = e
                error_holder.append(err)
            finally:
                done.set()

        async def _do_poll():
            while not done.is_set():
                if on_progress:
                    try:
                        resp = await self._async_client.get(
                            f"{self.base_url}/api/v1/eval/progress",
                        )
                        if resp.status_code == 200:
                            await on_progress(resp.json())
                    except Exception:
                        pass  # Progress polling failure is non-fatal
                try:
                    await asyncio.wait_for(
                        done.wait(),
                        timeout=self.poll_interval,
                    )
                except asyncio.TimeoutError:
                    pass  # Expected — poll again

        await asyncio.gather(_do_invoke(), _do_poll())

        if error_holder:
            raise error_holder[0]

        return result_holder.get("data", {})

    # ── Performance Testing ───────────────────────────────────────

    async def invoke_perf(self, config: dict[str, Any]) -> dict[str, Any]:
        """Run a performance/stress test via the EvalScope service."""
        try:
            resp = await self._async_client.post(
                f"{self.base_url}/api/v1/perf/invoke",
                json=config,
            )
            if resp.status_code >= 400:
                raise EvalScopeServiceError(
                    f"EvalScope perf returned {resp.status_code}: {resp.text[:500]}"
                )
            return resp.json()
        except httpx.TimeoutException as e:
            raise EvalScopeTimeoutError(f"EvalScope perf test timed out: {e}") from e
        except Exception as e:
            raise EvalScopeServiceError(f"EvalScope perf invocation failed: {e}") from e

    # ── Discovery ─────────────────────────────────────────────────

    async def list_benchmarks(self) -> list[str]:
        """List available benchmark datasets from the EvalScope service."""
        try:
            resp = await self._async_client.get(
                f"{self.base_url}/api/v1/eval/benchmarks",
            )
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list):
                    return data
                logger.warning(
                    "EvalScope benchmarks response is not a list: %s",
                    type(data).__name__,
                )
                return []
        except Exception as e:
            logger.warning("Failed to list EvalScope benchmarks: %s", e)
        return []
