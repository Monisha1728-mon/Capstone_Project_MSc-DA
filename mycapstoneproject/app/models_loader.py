from pathlib import Path
import json
import joblib

# Project root
ROOT = Path(__file__).resolve().parents[1]

# Model paths
MODEL_PATH = ROOT / "models" / "logistic_regression.pkl"
ENCODER_PATH = ROOT / "models" / "encoder.pkl"
FEATURE_PATH = ROOT / "models" / "feature_list.json"


def load():
    """
    Load the trained Logistic Regression model,
    categorical encoder, and exact feature list.
    """

    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model not found: {MODEL_PATH}")

    if not ENCODER_PATH.exists():
        raise FileNotFoundError(f"Encoder not found: {ENCODER_PATH}")

    if not FEATURE_PATH.exists():
        raise FileNotFoundError(f"Feature list not found: {FEATURE_PATH}")

    model = joblib.load(MODEL_PATH)
    encoder = joblib.load(ENCODER_PATH)

    features = json.loads(FEATURE_PATH.read_text(encoding="utf-8"))

    return model, encoder, features


# Load everything when this module is imported
model, encoder, feature_list = load()


print("Model loaded successfully:", MODEL_PATH.name)
print("Encoder loaded successfully:", ENCODER_PATH.name)
print("Features:", len(feature_list))
