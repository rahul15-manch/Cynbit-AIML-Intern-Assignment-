
from .code_analyzer import analyze_python_code
from .test_runner import run_test_cases, summarize_results
from .ml_detector import detect_structural_anomaly
from .ai_feedback import generate_ai_feedback

def evaluate_submission(source_code, solution_function, test_cases,
                        anomaly_model=None, model_feature_columns=None,
                        request_ai_feedback=False, qwen_model=None):
    """
    Evaluate a trusted callable.

    Source text is parsed, not executed. The supplied function is executed
    against test cases and must be code you wrote and trust.
    """
    code_analysis = analyze_python_code(source_code)
    if not code_analysis["syntax_valid"]:
        return {
            "syntax": code_analysis,
            "tests": None,
            "structural_analysis": None,
            "ai_feedback": None,
        }

    test_rows = run_test_cases(solution_function, test_cases)
    test_summary = summarize_results(test_rows)

    anomaly_result = None
    if anomaly_model is not None:
        if model_feature_columns is None:
            raise ValueError("model_feature_columns is required with anomaly_model.")
        anomaly_result = detect_structural_anomaly(
            anomaly_model, model_feature_columns, code_analysis
        )

    feedback = None
    if request_ai_feedback:
        kwargs = {"model": qwen_model} if qwen_model else {}
        feedback = generate_ai_feedback(
            source_code, test_summary, anomaly_result, **kwargs
        )

    return {
        "syntax": code_analysis,
        "tests": test_summary,
        "structural_analysis": anomaly_result,
        "ai_feedback": feedback,
    }