import json
import os
from pathlib import Path

from dotenv import load_dotenv
import pandas as pd
import streamlit as st

# Load environment variables (.env file for GROQ_API_KEY)
load_dotenv()

from pipeline.code_analyzer import analyze_python_code
from pipeline.data_loader import load_anomaly_model
from pipeline.ml_detector import detect_structural_anomaly
from pipeline.ai_feedback import generate_ai_feedback
from pipeline.sandbox_runner import execute_sandboxed_tests, check_sandbox_availability


PROJECT_ROOT = Path(__file__).resolve().parent
MODEL_PATH = PROJECT_ROOT / "reports" / "isolation_forest_model.joblib"


PRESETS = {
    "1. Addition (Correct Implementation)": {
        "function_name": "add_numbers",
        "code": """def add_numbers(a, b):
    \"\"\"Return the arithmetic sum of two numbers.\"\"\"
    return a + b
""",
        "json_tests": json.dumps(
            {
                "function_name": "add_numbers",
                "test_cases": [
                    {"name": "Positive numbers", "args": [2, 3], "expected": 5},
                    {"name": "Negative numbers", "args": [-2, -3], "expected": -5},
                    {"name": "Mixed signs", "args": [10, -4], "expected": 6},
                    {"name": "Zero handling", "args": [0, 0], "expected": 0},
                ],
            },
            indent=2,
        ),
    },
    "2. Addition (Intentionally Incorrect)": {
        "function_name": "add_numbers",
        "code": """def add_numbers(a, b):
    \"\"\"Incorrect implementation: uses subtraction instead of addition.\"\"\"
    return a - b
""",
        "json_tests": json.dumps(
            {
                "function_name": "add_numbers",
                "test_cases": [
                    {"name": "Positive numbers", "args": [2, 3], "expected": 5},
                    {"name": "Negative numbers", "args": [-2, -3], "expected": -5},
                    {"name": "Mixed signs", "args": [10, -4], "expected": 6},
                    {"name": "Zero handling", "args": [0, 0], "expected": 0},
                ],
            },
            indent=2,
        ),
    },
    "3. Factorial Function": {
        "function_name": "factorial",
        "code": """def factorial(n):
    \"\"\"Compute factorial of a non-negative integer.\"\"\"
    if n < 0:
        raise ValueError("Factorial is undefined for negative integers.")
    if n in (0, 1):
        return 1
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result
""",
        "json_tests": json.dumps(
            {
                "function_name": "factorial",
                "test_cases": [
                    {"name": "Base case 0", "args": [0], "expected": 1},
                    {"name": "Base case 1", "args": [1], "expected": 1},
                    {"name": "Factorial of 5", "args": [5], "expected": 120},
                    {"name": "Factorial of 6", "args": [6], "expected": 720},
                ],
            },
            indent=2,
        ),
    },
    "4. Palindrome Checker": {
        "function_name": "is_palindrome",
        "code": """def is_palindrome(text):
    \"\"\"Check if an alphanumeric string is a palindrome, ignoring case.\"\"\"
    cleaned = "".join(ch.lower() for ch in str(text) if ch.isalnum())
    return cleaned == cleaned[::-1]
""",
        "json_tests": json.dumps(
            {
                "function_name": "is_palindrome",
                "test_cases": [
                    {"name": "Simple palindrome", "args": ["racecar"], "expected": True},
                    {"name": "Phrase with spaces and punctuation", "args": ["A man, a plan, a canal: Panama"], "expected": True},
                    {"name": "Non-palindrome word", "args": ["hello"], "expected": False},
                    {"name": "Empty string", "args": [""], "expected": True},
                ],
            },
            indent=2,
        ),
    },
    "5. Function with Invalid Syntax": {
        "function_name": "broken_syntax_function",
        "code": """def broken_syntax_function(x):
    # Syntax error: missing colon
    if x > 10
        return x * 2
    return x
""",
        "json_tests": json.dumps(
            {
                "function_name": "broken_syntax_function",
                "test_cases": [
                    {"name": "Test above 10", "args": [15], "expected": 30},
                    {"name": "Test below 10", "args": [5], "expected": 5},
                ],
            },
            indent=2,
        ),
    },
    "6. Function that Raises an Exception": {
        "function_name": "divide_numbers",
        "code": """def divide_numbers(a, b):
    \"\"\"Divide two numbers; raises ZeroDivisionError when b == 0.\"\"\"
    return a / b
""",
        "json_tests": json.dumps(
            {
                "function_name": "divide_numbers",
                "test_cases": [
                    {"name": "Normal division", "args": [10, 2], "expected": 5.0},
                    {"name": "Division by zero (triggers exception)", "args": [10, 0], "expected": 0.0},
                ],
            },
            indent=2,
        ),
    },
    "Custom / Blank Template": {
        "function_name": "my_function",
        "code": """def my_function(x):
    # Write your Python function here
    return x
""",
        "json_tests": json.dumps(
            {
                "function_name": "my_function",
                "test_cases": [
                    {"name": "Sample test 1", "args": [1], "expected": 1}
                ],
            },
            indent=2,
        ),
    },
}


# --- Page Configuration ---
st.set_page_config(
    page_title="General-Purpose AI Code Evaluation Dashboard",
    page_icon="⚡",
    layout="wide",
)

st.title("⚡ General-Purpose AI Code Evaluation Dashboard")
st.caption(
    "Isolated OS Sandbox Execution • AST Structural Analysis • Isolation Forest Anomaly Detection • Qwen AI Feedback"
)

# --- Sandbox Security Status Indicator ---
sandbox_available, sandbox_info = check_sandbox_availability()
if sandbox_available:
    st.success(
        f"🛡️ **Secure Execution Sandbox Active**: {sandbox_info}. "
        "User code runs in an isolated ephemeral subprocess with CPU/memory limits, blocked network sockets, and restricted filesystem writes."
    )
else:
    st.error(
        f"⚠️ **Secure OS Sandbox Unavailable**: {sandbox_info}. "
        "Functional execution of untrusted code is automatically disabled per security policy. "
        "AST syntax parsing and ML structural anomaly analysis remain safely available."
    )

# --- Initialize Session State ---
if "selected_preset" not in st.session_state:
    st.session_state.selected_preset = list(PRESETS.keys())[0]

default_item = PRESETS[st.session_state.selected_preset]
if "source_code" not in st.session_state:
    st.session_state.source_code = default_item["code"]
if "function_name" not in st.session_state:
    st.session_state.function_name = default_item["function_name"]
if "json_tests" not in st.session_state:
    st.session_state.json_tests = default_item["json_tests"]


def apply_preset():
    preset_key = st.session_state.preset_selector
    preset_data = PRESETS[preset_key]
    st.session_state.source_code = preset_data["code"]
    st.session_state.function_name = preset_data["function_name"]
    st.session_state.json_tests = preset_data["json_tests"]
    st.session_state.selected_preset = preset_key
    # Clear previous results
    for key in ["eval_results", "test_summary", "anomaly_result", "feedback_result", "anomaly_error", "feedback_error", "test_error"]:
        st.session_state.pop(key, None)


def reset_editor():
    blank = PRESETS["Custom / Blank Template"]
    st.session_state.source_code = blank["code"]
    st.session_state.function_name = blank["function_name"]
    st.session_state.json_tests = blank["json_tests"]
    for key in ["eval_results", "test_summary", "anomaly_result", "feedback_result", "anomaly_error", "feedback_error", "test_error"]:
        st.session_state.pop(key, None)


# --- Template Selector & Reset Bar ---
ctrl_col1, ctrl_col2 = st.columns([3, 1])
with ctrl_col1:
    st.selectbox(
        "Load Example / Test Preset:",
        options=list(PRESETS.keys()),
        index=list(PRESETS.keys()).index(st.session_state.selected_preset),
        key="preset_selector",
        on_change=apply_preset,
    )
with ctrl_col2:
    st.write("")
    st.write("")
    st.button("🔄 Reset Editor", on_click=reset_editor, width="stretch")

st.divider()

# --- Section A & B: Code & Test Case Editors ---
editor_col1, editor_col2 = st.columns(2)

with editor_col1:
    st.subheader("📝 Python Function Editor")
    fn_name = st.text_input(
        "Target Function Name to Evaluate:",
        key="function_name",
        help="Specify the exact function name in your code that will be called by test cases.",
    )
    code_input = st.text_area(
        "Python Source Code:",
        key="source_code",
        height=320,
        help="Paste any Python function or class definition.",
    )

with editor_col2:
    st.subheader("🧪 Dynamic Test Cases (JSON)")
    json_input = st.text_area(
        "Test Cases Specification (JSON format):",
        key="json_tests",
        height=320,
        help="Define function_name and an array of test cases with 'name', 'args' list, and 'expected' value.",
    )

    # Validate JSON syntax on the fly
    parsed_json = None
    json_parse_error = None
    try:
        parsed_json = json.loads(json_input)
        if not isinstance(parsed_json, dict) or "test_cases" not in parsed_json:
            json_parse_error = "JSON root must be an object containing a 'test_cases' array."
    except Exception as e:
        json_parse_error = f"Invalid JSON format: {e}"

    if json_parse_error:
        st.error(f"❌ {json_parse_error}")
    else:
        st.success(f"✅ Valid test case schema ({len(parsed_json.get('test_cases', []))} test cases defined)")

# --- Section C: Action Controls ---
btn_col1, btn_col2, btn_col3 = st.columns(3)

with btn_col1:
    run_all_clicked = st.button("🚀 Evaluate Submission (Tests + Analysis)", type="primary", width="stretch")
with btn_col2:
    static_only_clicked = st.button("🔍 Static & Anomaly Analysis Only", width="stretch")
with btn_col3:
    feedback_clicked = st.button("🤖 Generate Qwen AI Feedback", width="stretch")

# --- Evaluation Logic ---
if run_all_clicked or static_only_clicked or feedback_clicked:
    # Clear previous execution state
    st.session_state.pop("eval_results", None)
    st.session_state.pop("test_summary", None)
    st.session_state.pop("anomaly_result", None)
    st.session_state.pop("anomaly_error", None)
    st.session_state.pop("test_error", None)
    if feedback_clicked or run_all_clicked:
        st.session_state.pop("feedback_result", None)
        st.session_state.pop("feedback_error", None)

    # 1. AST Analysis (Always runs safely)
    analysis = analyze_python_code(code_input)
    st.session_state.analysis_result = analysis

    # 2. Structural Anomaly Detection (Isolation Forest)
    if analysis.get("syntax_valid"):
        if MODEL_PATH.exists():
            try:
                model, feature_columns = load_anomaly_model(MODEL_PATH)
                st.session_state.anomaly_result = detect_structural_anomaly(model, feature_columns, analysis)
            except Exception as e:
                st.session_state.anomaly_error = f"Anomaly model error: {e}"
        else:
            st.session_state.anomaly_error = f"Model artifact not found at: {MODEL_PATH}"

    # 3. Functional Execution (if requested)
    if run_all_clicked:
        if not analysis.get("syntax_valid"):
            st.session_state.test_error = f"Cannot execute tests: syntax error present ({analysis.get('syntax_error')})."
        elif json_parse_error:
            st.session_state.test_error = f"Cannot execute tests: {json_parse_error}"
        elif not fn_name.strip():
            st.session_state.test_error = "Target function name cannot be empty."
        else:
            test_cases = parsed_json.get("test_cases", [])
            with st.spinner("Running tests inside isolated sandbox..."):
                exec_result = execute_sandboxed_tests(
                    source_code=code_input,
                    function_name=fn_name.strip(),
                    test_cases=test_cases,
                    timeout_sec=2.5,
                    memory_limit_mb=256,
                )
                if exec_result.get("executed"):
                    st.session_state.test_summary = exec_result.get("summary")
                else:
                    st.session_state.test_error = exec_result.get("error", "Execution failed.")

    # 4. AI Feedback Generation
    if feedback_clicked or (run_all_clicked and st.session_state.get("test_summary")):
        test_info = st.session_state.get("test_summary")
        if not test_info:
            test_info = "No functional test results are available (tests were not executed or syntax is invalid). Base your response strictly on code analysis; do not invent test outcomes."

        anomaly_info = st.session_state.get("anomaly_result")
        with st.spinner("Requesting educational code feedback from Qwen via Groq..."):
            try:
                feedback_text = generate_ai_feedback(code_input, test_info, anomaly_info)
                st.session_state.feedback_result = feedback_text
            except Exception as e:
                st.session_state.feedback_error = f"Groq / Qwen feedback error: {e}"

st.divider()

# --- Results Presentation ---
tab_tests, tab_ast, tab_anomaly, tab_feedback = st.tabs([
    "🧪 Functional Test Results",
    "📊 AST & Complexity Analysis",
    "🛡️ Structural Anomaly Detection",
    "💡 Qwen AI Feedback",
])

# TAB 1: Functional Testing
with tab_tests:
    if "test_error" in st.session_state:
        st.error(st.session_state.test_error)
    elif "test_summary" in st.session_state:
        summary = st.session_state.test_summary
        total = summary.get("total_test_cases", 0)
        passed = summary.get("passed", 0)
        failed = summary.get("failed", 0)
        errors = summary.get("errors", 0)
        pass_rate = summary.get("pass_rate", 0.0)

        # Overview Metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Pass Rate", f"{pass_rate}%")
        m2.metric("Total Tests", total)
        m3.metric("Passed", passed)
        m4.metric("Failed / Errors", f"{failed} failed | {errors} errors")

        # Visual progress bar
        st.progress(float(pass_rate) / 100.0)

        # Results Table
        raw_results = summary.get("results", [])
        if raw_results:
            formatted_rows = []
            for r in raw_results:
                status = r.get("status", "Unknown")
                status_icon = "✅ Passed" if status == "Passed" else ("❌ Failed" if status == "Failed" else "⚠️ Error")
                formatted_rows.append({
                    "Test Case": r.get("test_case"),
                    "Arguments": str(r.get("args")),
                    "Expected": str(r.get("expected")),
                    "Actual Output": str(r.get("actual")),
                    "Status": status_icon,
                    "Error Details": r.get("error", ""),
                })
            df = pd.DataFrame(formatted_rows)
            st.dataframe(df, width="stretch")
    else:
        st.info("Click **Evaluate Submission** to run the submitted code against your custom test cases.")

# TAB 2: AST Analysis
with tab_ast:
    if "analysis_result" in st.session_state:
        analysis = st.session_state.analysis_result
        if not analysis.get("syntax_valid"):
            st.error(f"❌ Syntax Error Detected: {analysis.get('syntax_error', 'Invalid Python syntax')}")
        else:
            st.success("✅ Syntax Valid")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Lines of Code", analysis.get("num_lines", 0))
            c2.metric("Character Count", analysis.get("code_length", 0))
            c3.metric("Avg Line Length", f"{analysis.get('avg_line_length', 0):.1f}")
            c4.metric("Max Line Length", analysis.get("max_line_length", 0))

            st.subheader("Structural Element Counts")
            e1, e2, e3, e4, e5, e6 = st.columns(6)
            e1.metric("Functions", analysis.get("num_functions", 0))
            e2.metric("Classes", analysis.get("num_classes", 0))
            e3.metric("Loops", analysis.get("num_loops", 0))
            e4.metric("Conditionals", analysis.get("num_conditionals", 0))
            e5.metric("Function Calls", analysis.get("num_function_calls", 0))
            e6.metric("Imports", analysis.get("num_imports", 0))
    else:
        st.info("Click **Evaluate Submission** or **Static & Anomaly Analysis Only** to extract AST metrics.")

# TAB 3: Structural Anomaly Detection
with tab_anomaly:
    if "anomaly_error" in st.session_state:
        st.warning(st.session_state.anomaly_error)
    elif "anomaly_result" in st.session_state:
        anomaly = st.session_state.anomaly_result
        is_anomaly = anomaly.get("is_anomaly", False)

        a_col1, a_col2 = st.columns([1, 2])
        with a_col1:
            if is_anomaly:
                st.error("⚠️ Anomaly Flagged")
            else:
                st.success("🟢 Normal Structure")
            st.metric("Anomaly Score", f"{anomaly.get('anomaly_score', 0):.4f}")
            st.caption(f"Raw Label: {anomaly.get('anomaly_label', 0)} (1: Inlier, -1: Outlier)")

        with a_col2:
            st.markdown(f"**Model Interpretation:** {anomaly.get('interpretation', 'N/A')}")
            st.info(
                "ℹ️ **Important ML Disclaimer:** "
                + anomaly.get("warning", "An anomaly flag indicates unusual syntactic complexity, not incorrectness.")
            )
    else:
        st.info("Evaluate valid Python code to compute structural anomaly scores with the Isolation Forest model.")

# TAB 4: Qwen AI Feedback
with tab_feedback:
    if "feedback_error" in st.session_state:
        st.error(st.session_state.feedback_error)
    elif "feedback_result" in st.session_state:
        st.markdown(st.session_state.feedback_result)
    else:
        st.info("Click **Generate Qwen AI Feedback** to receive pedagogical explanations, bug insights, and code recommendations.")