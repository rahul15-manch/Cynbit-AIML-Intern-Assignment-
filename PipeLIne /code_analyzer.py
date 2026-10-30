"""Syntax validation and AST-based Python feature extraction."""
import ast

def analyze_python_code(source_code):
    """Parse Python source and return structural features; never execute it."""
    if not isinstance(source_code, str) or not source_code.strip():
        return {"syntax_valid": 0, "syntax_error": "No Python source code provided."}
    try:
        tree = ast.parse(source_code)
    except SyntaxError as error:
        return {"syntax_valid": 0, "syntax_error": f"Line {error.lineno}: {error.msg}"}

    counts = {
        "num_functions": 0, "num_classes": 0, "num_loops": 0,
        "num_conditionals": 0, "num_function_calls": 0, "num_imports": 0,
    }

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            counts["num_functions"] += 1
        elif isinstance(node, ast.ClassDef):
            counts["num_classes"] += 1
        elif isinstance(node, (ast.For, ast.AsyncFor, ast.While)):
            counts["num_loops"] += 1
        elif isinstance(node, ast.If):
            counts["num_conditionals"] += 1
        elif isinstance(node, ast.Call):
            counts["num_function_calls"] += 1
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            counts["num_imports"] += 1

    lines = source_code.splitlines()
    lengths = [len(line) for line in lines]
    return {
        "syntax_valid": 1,
        "code_length": len(source_code),
        "num_lines": len(lines),
        "max_line_length": max(lengths, default=0),
        "avg_line_length": sum(lengths) / len(lengths) if lengths else 0,
        **counts,
    }
