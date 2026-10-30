import os

DEFAULT_MODEL = "qwen/qwen3.8-27b"

def generate_ai_feedback(source_code, test_summary, anomaly_result=None,
                         model=DEFAULT_MODEL):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError("GROQ_API_KEY is not set in your environment.")

    try:
        from groq import Groq
    except ImportError as error:
        raise ImportError("Install the Groq package with: pip install groq") from error

    client = Groq(api_key=api_key)
    prompt = f"""
Review this Python solution using only the supplied evidence.

Python source:
```python
{source_code}
```

Test-case summary:
{test_summary}

Structural anomaly result:
{anomaly_result if anomaly_result is not None else "Not available"}

Explain the code, summarize the supplied test results, identify possible
failure causes, and suggest practical improvements in beginner-friendly
language. Do not invent test outcomes. An anomaly flag is not proof of bad
code. Passing a limited test suite does not prove complete correctness.
"""
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are an accurate, concise Python tutor."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content
