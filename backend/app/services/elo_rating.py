"""Pure-function ELO rating computation from a history of pairwise comparisons.

The ELO score for a (task, criterion) pair is a deterministic function of
the full comparison history, so we recompute it on demand rather than
storing it. Callers load all `PairwiseComparison` rows for the scope,
sort them by `created_at`, and feed them to `compute_elo_ratings`.

The pairwise history itself is populated by `record_pair_decision` — a
thin wrapper around a PairwiseComparison insert that the task runner
calls after a judge-model verdict. Keeping the write path in this
module keeps all ELO concerns in one file.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.pairwise_comparison import PairwiseComparison, PairwiseWinner


@dataclass
class PairRecord:
    """Lightweight view of a pairwise comparison for ELO replay."""

    model_a_id: uuid.UUID
    model_b_id: uuid.UUID
    winner: PairwiseWinner


DEFAULT_K_FACTOR = 32
DEFAULT_INITIAL_RATING = 1500.0


def _expected_score(rating_a: float, rating_b: float) -> float:
    """Probability that player A beats player B under standard ELO."""
    return 1.0 / (1.0 + 10 ** ((rating_b - rating_a) / 400.0))


def _actual_score_for_a(winner: PairwiseWinner) -> float:
    if winner == PairwiseWinner.a:
        return 1.0
    if winner == PairwiseWinner.b:
        return 0.0
    return 0.5  # tie


def compute_elo_ratings(
    comparisons: list[PairRecord],
    k_factor: float = DEFAULT_K_FACTOR,
    initial_rating: float = DEFAULT_INITIAL_RATING,
) -> dict[uuid.UUID, float]:
    """Replay a list of comparisons and return each model's final rating.

    Models default to ``initial_rating`` on first appearance. Comparisons
    are consumed in the order given; callers must pre-sort by time.
    """
    ratings: dict[uuid.UUID, float] = {}

    def _rating(model_id: uuid.UUID) -> float:
        if model_id not in ratings:
            ratings[model_id] = initial_rating
        return ratings[model_id]

    for pair in comparisons:
        a = _rating(pair.model_a_id)
        b = _rating(pair.model_b_id)
        e_a = _expected_score(a, b)
        e_b = 1.0 - e_a
        s_a = _actual_score_for_a(pair.winner)
        s_b = 1.0 - s_a
        ratings[pair.model_a_id] = a + k_factor * (s_a - e_a)
        ratings[pair.model_b_id] = b + k_factor * (s_b - e_b)

    return ratings


async def record_pair_decision(
    session: AsyncSession,
    *,
    task_id: uuid.UUID,
    criterion_id: uuid.UUID,
    prompt_text: str,
    model_a_id: uuid.UUID,
    model_b_id: uuid.UUID,
    result_a_id: uuid.UUID,
    result_b_id: uuid.UUID,
    winner: PairwiseWinner,
    judge_reasoning: str = "",
) -> PairwiseComparison:
    """Persist a single judge verdict and return the inserted row.

    Does not commit the session — the caller decides how to batch
    writes. The row is added via `session.add` and will be flushed
    on the next commit.
    """
    row = PairwiseComparison(
        task_id=task_id,
        criterion_id=criterion_id,
        prompt_text=prompt_text,
        model_a_id=model_a_id,
        model_b_id=model_b_id,
        result_a_id=result_a_id,
        result_b_id=result_b_id,
        winner=winner,
        judge_reasoning=judge_reasoning,
    )
    session.add(row)
    return row


def build_ranking(
    ratings: dict[uuid.UUID, float],
    comparison_counts: dict[uuid.UUID, int] | None = None,
) -> list[dict]:
    """Convert a ratings dict into a sorted list suitable for the API.

    Returns a list of `{model_id, rating, comparisons}` sorted descending
    by rating. `comparison_counts` is optional; if provided it populates
    the `comparisons` field, otherwise it defaults to 0.
    """
    counts = comparison_counts or {}
    rows = [
        {
            "model_id": str(model_id),
            "rating": round(rating, 2),
            "comparisons": counts.get(model_id, 0),
        }
        for model_id, rating in ratings.items()
    ]
    rows.sort(key=lambda row: row["rating"], reverse=True)
    return rows
