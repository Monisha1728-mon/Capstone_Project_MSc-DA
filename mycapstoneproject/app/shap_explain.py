from pathlib import Path
import joblib
import pandas as pd
import shap

ROOT = Path(__file__).resolve().parents[1]


def explain_prediction(row_dict):
    model = joblib.load(ROOT / "models" / "best_model.pkl")
    X = pd.DataFrame([row_dict])
    try:
        explainer = shap.Explainer(model, X)
        explanation = explainer(X)
        vals = explanation.values[0]
        names = X.columns.tolist()
        pairs = sorted(zip(names, vals), key=lambda x: abs(float(x[1])), reverse=True)[
            :5
        ]
        return [{"feature": n, "impact": float(v)} for n, v in pairs]
    except Exception as exc:
        return [{"feature": "SHAP explanation", "impact": 0.0, "note": str(exc)}]
