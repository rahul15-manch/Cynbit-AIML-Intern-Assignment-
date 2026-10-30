import pandas as pd

def detect_structural_anomaly(model, feature_columns, features):
    if not feature_columns:
        raise ValueError("Model feature column names are missing.")
    row = {column: features.get(column, 0) for column in feature_columns}
    input_frame = pd.DataFrame([row], columns=feature_columns)
    prediction = int(model.predict(input_frame)[0])
    score = float(model.decision_function(input_frame)[0])
    return {
        "anomaly_label": prediction,
        "is_anomaly": prediction == -1,
        "anomaly_score": score,
        "interpretation": (
            "Flagged for structural review" if prediction == -1
            else "Not flagged by the structural anomaly model"
        ),
        "warning": "An anomaly flag is not proof of incorrectness or poor quality.",
    }
