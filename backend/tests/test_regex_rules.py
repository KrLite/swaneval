"""Tests for extended regex criterion — match_mode and keywords."""

import json
import unittest

from app.services.evaluators import (
    _evaluate_keyword_rules,
    evaluate_regex,
    run_criterion,
)


class TestEvaluateRegexModes(unittest.TestCase):
    def test_contains_default(self):
        self.assertEqual(
            evaluate_regex(r"\d+", "The answer is 42", match_mode="contains"),
            1.0,
        )

    def test_contains_no_match(self):
        self.assertEqual(
            evaluate_regex(r"\d+", "no digits here", match_mode="contains"),
            0.0,
        )

    def test_exact_whole_string(self):
        self.assertEqual(
            evaluate_regex(r"^\d+$", "42", match_mode="exact"), 1.0
        )

    def test_exact_partial_fails(self):
        self.assertEqual(
            evaluate_regex(r"\d+", "42 is the answer", match_mode="exact"),
            0.0,
        )

    def test_extract_group_matches_expected(self):
        self.assertEqual(
            evaluate_regex(
                r"Answer: (\d+)",
                "Answer: 42",
                match_mode="extract",
                expected="42",
            ),
            1.0,
        )

    def test_extract_group_mismatch(self):
        self.assertEqual(
            evaluate_regex(
                r"Answer: (\d+)",
                "Answer: 41",
                match_mode="extract",
                expected="42",
            ),
            0.0,
        )

    def test_empty_pattern_returns_zero(self):
        self.assertEqual(evaluate_regex("", "some text"), 0.0)


class TestKeywordRules(unittest.TestCase):
    def test_any_hit(self):
        self.assertEqual(
            _evaluate_keyword_rules(["yes", "correct"], "the answer is yes"),
            1.0,
        )

    def test_any_no_hit(self):
        self.assertEqual(
            _evaluate_keyword_rules(["yes", "correct"], "not this one"),
            0.0,
        )

    def test_all_partial_hit(self):
        self.assertEqual(
            _evaluate_keyword_rules(
                ["yes", "correct"], "yes but not the other", mode="all"
            ),
            0.0,
        )

    def test_all_full_hit(self):
        self.assertEqual(
            _evaluate_keyword_rules(
                ["yes", "correct"], "yes, that is correct", mode="all"
            ),
            1.0,
        )

    def test_empty_list_is_vacuously_true(self):
        self.assertEqual(_evaluate_keyword_rules([], "anything"), 1.0)


class TestCriterionDispatchRegex(unittest.TestCase):
    def _call(self, config, expected="", actual=""):
        return run_criterion("regex", json.dumps(config), expected, actual)

    def test_pattern_only_contains(self):
        score = self._call(
            {"pattern": r"\d+", "match_mode": "contains"},
            actual="The price is 100",
        )
        self.assertEqual(score, 1.0)

    def test_keywords_only(self):
        score = self._call(
            {"keywords": ["yes", "no"], "keywords_mode": "any"},
            actual="yes it is",
        )
        self.assertEqual(score, 1.0)

    def test_pattern_and_keywords_both_required(self):
        # Pattern matches, but keyword doesn't → fail
        score = self._call(
            {
                "pattern": r"\d+",
                "match_mode": "contains",
                "keywords": ["correct"],
                "keywords_mode": "any",
            },
            actual="The answer is 42",  # has digits but not "correct"
        )
        self.assertEqual(score, 0.0)

    def test_pattern_and_keywords_both_pass(self):
        score = self._call(
            {
                "pattern": r"\d+",
                "match_mode": "contains",
                "keywords": ["correct"],
                "keywords_mode": "any",
            },
            actual="The answer is 42, correct",
        )
        self.assertEqual(score, 1.0)

    def test_neither_pattern_nor_keywords_raises(self):
        with self.assertRaises(ValueError):
            self._call({}, actual="anything")


if __name__ == "__main__":
    unittest.main()
