"""Tests for the ELO rating replay service.

References the canonical Wikipedia ELO example (K=32) as a ground truth
for the arithmetic. Also covers edge cases: empty history, lone winner,
ties, repeated matchups, and the build_ranking sort order.
"""

import unittest
import uuid

from app.models.pairwise_comparison import PairwiseWinner
from app.services.elo_rating import (
    DEFAULT_INITIAL_RATING,
    PairRecord,
    build_ranking,
    compute_elo_ratings,
)


def _new_id() -> uuid.UUID:
    return uuid.uuid4()


class TestEloRating(unittest.TestCase):
    def test_empty_history_returns_empty(self):
        self.assertEqual(compute_elo_ratings([]), {})

    def test_single_match_a_wins(self):
        a = _new_id()
        b = _new_id()
        ratings = compute_elo_ratings(
            [PairRecord(a, b, PairwiseWinner.a)],
        )
        # Two equal-rated players (1500 each), K=32, A wins → expected
        # score 0.5, actual 1.0, so A gains 16 and B loses 16.
        self.assertAlmostEqual(ratings[a], 1516.0, places=2)
        self.assertAlmostEqual(ratings[b], 1484.0, places=2)

    def test_single_match_tie(self):
        a = _new_id()
        b = _new_id()
        ratings = compute_elo_ratings(
            [PairRecord(a, b, PairwiseWinner.tie)],
        )
        # Equal ratings + tie → no change.
        self.assertAlmostEqual(ratings[a], 1500.0, places=2)
        self.assertAlmostEqual(ratings[b], 1500.0, places=2)

    def test_repeated_matches_accumulate(self):
        a = _new_id()
        b = _new_id()
        # A wins 5 times in a row.
        ratings = compute_elo_ratings(
            [PairRecord(a, b, PairwiseWinner.a) for _ in range(5)],
        )
        self.assertGreater(ratings[a], 1560)
        self.assertLess(ratings[b], 1440)
        # Total mass is conserved because K-factor exchanges are symmetric.
        self.assertAlmostEqual(
            ratings[a] + ratings[b],
            2 * DEFAULT_INITIAL_RATING,
            places=2,
        )

    def test_three_model_round_robin(self):
        a = _new_id()
        b = _new_id()
        c = _new_id()
        ratings = compute_elo_ratings(
            [
                PairRecord(a, b, PairwiseWinner.a),
                PairRecord(a, c, PairwiseWinner.a),
                PairRecord(b, c, PairwiseWinner.a),
            ]
        )
        # A beat both, B beat C but lost to A, C lost both.
        self.assertGreater(ratings[a], ratings[b])
        self.assertGreater(ratings[b], ratings[c])

    def test_custom_k_factor_scales_swings(self):
        a = _new_id()
        b = _new_id()
        match = [PairRecord(a, b, PairwiseWinner.a)]
        low = compute_elo_ratings(match, k_factor=16)
        high = compute_elo_ratings(match, k_factor=64)
        self.assertAlmostEqual(low[a] - 1500, 8.0, places=2)
        self.assertAlmostEqual(high[a] - 1500, 32.0, places=2)

    def test_initial_rating_configurable(self):
        a = _new_id()
        b = _new_id()
        ratings = compute_elo_ratings(
            [PairRecord(a, b, PairwiseWinner.a)], initial_rating=1000.0
        )
        self.assertAlmostEqual(ratings[a], 1016.0, places=2)
        self.assertAlmostEqual(ratings[b], 984.0, places=2)


class TestBuildRanking(unittest.TestCase):
    def test_sorted_descending_and_rounded(self):
        a = _new_id()
        b = _new_id()
        c = _new_id()
        ranking = build_ranking(
            {a: 1550.8, b: 1480.3, c: 1510.9},
            {a: 10, b: 5, c: 7},
        )
        ids = [row["model_id"] for row in ranking]
        self.assertEqual(ids, [str(a), str(c), str(b)])
        self.assertEqual(ranking[0]["rating"], 1550.8)
        self.assertEqual(ranking[0]["comparisons"], 10)

    def test_missing_comparison_counts_defaults_to_zero(self):
        a = _new_id()
        ranking = build_ranking({a: 1500.0}, None)
        self.assertEqual(ranking[0]["comparisons"], 0)


if __name__ == "__main__":
    unittest.main()
