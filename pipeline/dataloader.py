from pathlib import Path
import joblib
import pandas as pd

def load_anomaly_model(model_path):
    """Load the saved Isolation Forest pipeline and its feature names."""
    model_path = Path(model_path)
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    saved_object = joblib.load(model_path)
    if not isinstance(saved_object, dict) or "model" not in saved_object:
        raise ValueError("Expected a dictionary containing a 'model' entry.")
    return saved_object["model"], saved_object.get("feature_columns", [])

def load_feature_data(csv_path):
    """Load the previously generated feature dataset."""
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"Feature CSV not found: {csv_path}")
    return pd.read_csv(csv_path)
