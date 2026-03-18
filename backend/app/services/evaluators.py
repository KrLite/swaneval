"""Built-in evaluation functions for criteria types."""

import json
import re


def evaluate_exact_match(expected: str, actual: str) -> float:
    return 1.0 if expected.strip() == actual.strip() else 0.0


def evaluate_contains(expected: str, actual: str) -> float:
    return 1.0 if expected.strip() in actual.strip() else 0.0


def evaluate_regex(pattern: str, actual: str, extract_group: int = 0) -> float:
    match = re.search(pattern, actual)
    if not match:
        return 0.0
    return 1.0


def evaluate_numeric_closeness(expected: str, actual: str, tolerance: float = 0.01) -> float:
    try:
        exp_val = float(expected.strip())
        # Try to extract a number from model output
        numbers = re.findall(r"-?\d+\.?\d*", actual)
        if not numbers:
            return 0.0
        act_val = float(numbers[-1])
        return 1.0 if abs(exp_val - act_val) <= tolerance else 0.0
    except (ValueError, IndexError):
        return 0.0


def run_criterion(criterion_type: str, config_json: str, expected: str, actual: str) -> float:
    """Dispatch to the right evaluator based on criterion type and config."""
    config = json.loads(config_json) if config_json else {}

    if criterion_type == "preset":
        metric = config.get("metric", "exact_match")
        if metric == "exact_match":
            return evaluate_exact_match(expected, actual)
        elif metric == "contains":
            return evaluate_contains(expected, actual)
        elif metric == "numeric":
            return evaluate_numeric_closeness(expected, actual, config.get("tolerance", 0.01))
        else:
            return evaluate_exact_match(expected, actual)

    elif criterion_type == "regex":
        pattern = config.get("pattern", "")
        if not pattern:
            return 0.0
        return evaluate_regex(pattern, actual, config.get("extract_group", 0))

    # For script and llm_judge, return 0 in MVP (not implemented)
    return 0.0
