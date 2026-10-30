def run_test_cases(solution_function, test_cases):
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

def summarize_results(results):
    total = len(results)
    passed = sum(row["status"] == "Passed" for row in results)
    failed = sum(row["status"] == "Failed" for row in results)
    errors = sum(row["status"] == "Error" for row in results)
    return {
        "total_test_cases": total,
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "pass_rate": round(passed / total * 100, 2) if total else 0.0,
        "results": results,
    }

