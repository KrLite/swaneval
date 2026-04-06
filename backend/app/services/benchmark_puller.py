"""Pull external benchmark data from public platforms.

Supports:
- Open LLM Leaderboard (HuggingFace)
- Manual JSON import (fallback)
"""

import logging

import httpx

logger = logging.getLogger(__name__)

# Known benchmark sources with their API endpoints
BENCHMARK_SOURCES = {
    "open_llm_leaderboard": {
        "name": "Open LLM Leaderboard",
        "url": "https://huggingface.co/api/spaces/open-llm-leaderboard-old/open_llm_leaderboard/api/leaderboard",
        "platform": "HuggingFace",
    },
}


async def pull_open_llm_leaderboard(
    model_filter: str = "",
    limit: int = 50,
) -> list[dict]:
    """Pull data from HuggingFace Open LLM Leaderboard.

    Returns list of benchmark entries ready for batch import.
    """
    results: list[dict] = []

    # Try the HF datasets API for leaderboard data
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                "https://datasets-server.huggingface.co/rows",
                params={
                    "dataset": "open-llm-leaderboard/contents",
                    "config": "default",
                    "split": "train",
                    "offset": 0,
                    "length": limit,
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                for row in data.get("rows", []):
                    r = row.get("row", {})
                    model_name = r.get("fullname", r.get("model", ""))
                    if model_filter and model_filter.lower() not in model_name.lower():
                        continue

                    # Extract benchmark scores
                    benchmarks = {
                        "MMLU": r.get("MMLU", r.get("mmlu")),
                        "ARC": r.get("ARC", r.get("arc")),
                        "HellaSwag": r.get("HellaSwag", r.get("hellaswag")),
                        "TruthfulQA": r.get("TruthfulQA", r.get("truthfulqa")),
                        "Winogrande": r.get("Winogrande", r.get("winogrande")),
                        "GSM8K": r.get("GSM8K", r.get("gsm8k")),
                    }

                    for bench_name, score in benchmarks.items():
                        if score is not None:
                            try:
                                score_val = float(score)
                                # Normalize to 0-1 if needed
                                if score_val > 1.0:
                                    score_val = score_val / 100.0
                                results.append(
                                    {
                                        "model_name": model_name,
                                        "provider": r.get("organization", ""),
                                        "benchmark_name": bench_name,
                                        "score": round(max(0, min(1, score_val)), 4),
                                        "score_display": str(score),
                                        "source_url": f"https://huggingface.co/{model_name}",
                                        "source_platform": "Open LLM Leaderboard",
                                        "notes": "",
                                    }
                                )
                            except (ValueError, TypeError):
                                continue
    except Exception as e:
        logger.warning("Failed to pull from Open LLM Leaderboard: %s", e)

    return results


async def pull_benchmarks(
    source: str = "open_llm_leaderboard",
    model_filter: str = "",
    limit: int = 50,
) -> list[dict]:
    """Pull benchmarks from a specified source."""
    if source == "open_llm_leaderboard":
        return await pull_open_llm_leaderboard(model_filter, limit)
    raise ValueError(f"Unknown benchmark source: {source}")
