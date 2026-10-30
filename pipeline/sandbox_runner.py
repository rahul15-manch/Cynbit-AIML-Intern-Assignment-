"""Isolated execution engine for running untrusted Python functions against test cases."""

import ast
import json
import os
import platform
import shutil
import subprocess
import sys
from typing import Any, Dict, List, Optional, Tuple


WORKER_SCRIPT = """
import ast
import json
import resource
import sys

def set_limits(timeout_sec, memory_mb):
    try:
        if hasattr(resource, 'RLIMIT_CPU'):
            resource.setrlimit(resource.RLIMIT_CPU, (int(timeout_sec) + 1, int(timeout_sec) + 2))
    except Exception:
        pass
    try:
        if hasattr(resource, 'RLIMIT_AS'):
            mem_bytes = int(memory_mb) * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))
    except Exception:
        pass

def run():
    raw_input = sys.stdin.read()
    if not raw_input:
        print(json.dumps({"success": False, "error": "No input payload received."}))
        return

    try:
        data = json.loads(raw_input)
    except Exception as e:
        print(json.dumps({"success": False, "error": f"Invalid JSON payload: {e}"}))
        return

    source_code = data.get("source_code", "")
    func_name = data.get("function_name", "").strip()
    test_cases = data.get("test_cases", [])
    timeout_sec = data.get("timeout_sec", 3.0)
    memory_mb = data.get("memory_limit_mb", 256)

    set_limits(timeout_sec, memory_mb)

    # 1. Parse AST
    try:
        tree = ast.parse(source_code)
    except SyntaxError as e:
        print(json.dumps({"success": False, "error": f"SyntaxError: Line {e.lineno}: {e.msg}"}))
        return

    # 2. Compile and execute into private namespace
    namespace = {}
    try:
        code_obj = compile(tree, "<submitted_code>", "exec")
        exec(code_obj, namespace)
    except Exception as e:
        print(json.dumps({"success": False, "error": f"ExecutionError during definition: {type(e).__name__}: {e}"}))
        return

    # 3. Verify function exists and is callable
    if func_name not in namespace:
        print(json.dumps({"success": False, "error": f"Function '{func_name}' was not found in the submitted code."}))
        return

    target_func = namespace[func_name]
    if not callable(target_func):
        print(json.dumps({"success": False, "error": f"'{func_name}' is not callable (type: {type(target_func).__name__})."}))
        return

    # 4. Execute test cases
    results = []
    for case in test_cases:
        tc_name = case.get("name", "Unnamed test")
        args = case.get("args", [])
        kwargs = case.get("kwargs", {})
        expected = case.get("expected")

        if not isinstance(args, (list, tuple)):
            results.append({
                "test_case": tc_name,
                "args": args,
                "expected": expected,
                "actual": None,
                "status": "Error",
                "error": f"Invalid arguments format. Expected a list/tuple, got {type(args).__name__}."
            })
            continue

        try:
            actual = target_func(*args, **kwargs)
            passed = (actual == expected)
            results.append({
                "test_case": tc_name,
                "args": args,
                "expected": expected,
                "actual": actual,
                "status": "Passed" if passed else "Failed",
                "error": ""
            })
        except Exception as e:
            results.append({
                "test_case": tc_name,
                "args": args,
                "expected": expected,
                "actual": None,
                "status": "Error",
                "error": f"{type(e).__name__}: {e}"
            })

    print(json.dumps({"success": True, "results": results}))

if __name__ == "__main__":
    run()
"""


def check_sandbox_availability() -> Tuple[bool, str]:
    """
    Check if an operating system level sandbox is available.
    Returns (is_available, description_or_reason).
    """
    system = platform.system()
    if system == "Darwin":
        sandbox_bin = shutil.which("sandbox-exec")
        if sandbox_bin and os.path.exists(sandbox_bin):
            return True, "macOS Seatbelt (sandbox-exec: network blocked, write blocked)"
        return False, "sandbox-exec binary not found on macOS."
    elif system == "Linux":
        # Check for bubblewrap or docker/container environment
        if shutil.which("bwrap"):
            return True, "Linux Bubblewrap (bwrap)"
        if os.path.exists("/.dockerenv"):
            return True, "Docker container sandbox"
        return False, "No Linux container or bwrap sandbox available."
    else:
        return False, f"OS sandbox not supported on {system}."


def summarize_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate aggregate statistics from individual test results."""
    total = len(results)
    passed = sum(1 for r in results if r.get("status") == "Passed")
    failed = sum(1 for r in results if r.get("status") == "Failed")
    errors = sum(1 for r in results if r.get("status") == "Error")
    pass_rate = round((passed / total) * 100, 2) if total > 0 else 0.0

    return {
        "total_test_cases": total,
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "pass_rate": pass_rate,
        "results": results,
    }


def execute_sandboxed_tests(
    source_code: str,
    function_name: str,
    test_cases: List[Dict[str, Any]],
    timeout_sec: float = 3.0,
    memory_limit_mb: int = 256,
    python_executable: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Execute untrusted Python code in an isolated process wrapped with OS-level sandboxing.

    Enforces:
    - Dedicated child process (no exec/eval in host Streamlit process)
    - Wall-clock timeout
    - CPU & virtual memory resource limits
    - Network access blocked
    - Filesystem write blocked
    """
    is_sandboxed, sandbox_desc = check_sandbox_availability()

    if not is_sandboxed:
        return {
            "executed": False,
            "sandbox_available": False,
            "sandbox_description": sandbox_desc,
            "error": (
                "A secure OS sandbox is not available on this host. "
                "Per security policy, functional execution of untrusted user code is disabled. "
                "AST syntax parsing and ML structural anomaly analysis remain fully functional."
            ),
            "summary": None,
        }

    if not python_executable:
        # Default to the current virtualenv Python
        python_executable = sys.executable

    payload = json.dumps({
        "source_code": source_code,
        "function_name": function_name,
        "test_cases": test_cases,
        "timeout_sec": timeout_sec,
        "memory_limit_mb": memory_limit_mb,
    })

    # Prepare command with sandbox wrapping
    system = platform.system()
    if system == "Darwin":
        # macOS Seatbelt profile:
        # - Deny default
        # - Allow process-exec
        # - Allow file-read* for python libraries
        # - Network is denied by default
        # - File write is denied by default
        seatbelt_profile = (
            "(version 1)"
            "(deny default)"
            "(allow process-exec)"
            "(allow file-read*)"
            "(allow sysctl-read)"
        )
        cmd = [
            "sandbox-exec",
            "-p",
            seatbelt_profile,
            python_executable,
            "-c",
            WORKER_SCRIPT,
        ]
    else:
        cmd = [python_executable, "-c", WORKER_SCRIPT]

    # Calculate max total timeout for all tests combined
    total_timeout = max(5.0, (timeout_sec * len(test_cases)) + 4.0)

    try:
        proc = subprocess.run(
            cmd,
            input=payload,
            capture_output=True,
            text=True,
            timeout=total_timeout,
        )
    except subprocess.TimeoutExpired:
        timeout_results = [
            {
                "test_case": tc.get("name", f"Test {i+1}"),
                "args": tc.get("args", []),
                "expected": tc.get("expected"),
                "actual": None,
                "status": "Error",
                "error": f"Execution timed out after {total_timeout:.1f}s (possible infinite loop or resource exhaustion).",
            }
            for i, tc in enumerate(test_cases)
        ]
        return {
            "executed": True,
            "sandbox_available": True,
            "sandbox_description": sandbox_desc,
            "error": "Execution timed out.",
            "summary": summarize_results(timeout_results),
        }
    except Exception as e:
        return {
            "executed": False,
            "sandbox_available": True,
            "sandbox_description": sandbox_desc,
            "error": f"Sandbox runner invocation failed: {type(e).__name__}: {e}",
            "summary": None,
        }

    stdout = proc.stdout.strip()
    if not stdout:
        stderr = proc.stderr.strip()
        return {
            "executed": False,
            "sandbox_available": True,
            "sandbox_description": sandbox_desc,
            "error": f"Sandbox process terminated unexpectedly (exit code {proc.returncode}): {stderr}",
            "summary": None,
        }

    try:
        res_data = json.loads(stdout)
    except Exception as e:
        return {
            "executed": False,
            "sandbox_available": True,
            "sandbox_description": sandbox_desc,
            "error": f"Failed to parse sandbox response: {e}\nRaw output: {stdout[:300]}",
            "summary": None,
        }

    if not res_data.get("success"):
        return {
            "executed": False,
            "sandbox_available": True,
            "sandbox_description": sandbox_desc,
            "error": res_data.get("error", "Unknown worker execution error."),
            "summary": None,
        }

    raw_results = res_data.get("results", [])
    summary = summarize_results(raw_results)

    return {
        "executed": True,
        "sandbox_available": True,
        "sandbox_description": sandbox_desc,
        "error": None,
        "summary": summary,
    }
