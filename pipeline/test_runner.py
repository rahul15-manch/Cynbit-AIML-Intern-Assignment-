"""Test runner supporting both legacy trusted function calls and isolated sandboxed execution."""

from typing import Any, Dict, List
from .sandbox_runner import (
    execute_sandboxed_tests,
    check_sandbox_availability,
    summarize_results,
)


def run_test_cases(solution_function, test_cases):
    """
    Legacy in-process runner for locally authored, trusted functions only.
    DO NOT use this for untrusted user-submitted code; use execute_sandboxed_tests instead.
    """
    results = []
    for case in test_cases:
        name = case.get("name", "Unnamed test")
        try:
            inputs = case["input"]
            if not isinstance(inputs, tuple):
                raise TypeError("Each test case 'input' must be a tuple.")
            actual = solution_function(*inputs)
            passed = actual == case["expected"]
            results.append({
                "test_case": name,
                "expected": case["expected"],
                "actual": actual,
                "status": "Passed" if passed else "Failed",
                "error": "",
            })
        except Exception as error:
            results.append({
                "test_case": name,
                "expected": case.get("expected"),
                "actual": None,
                "status": "Error",
                "error": f"{type(error).__name__}: {error}",
            })
    return results


__all__ = [
    "run_test_cases",
    "summarize_results",
    "execute_sandboxed_tests",
    "check_sandbox_availability",
]
