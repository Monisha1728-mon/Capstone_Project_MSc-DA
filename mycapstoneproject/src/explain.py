from pathlib import Path
import joblib
import pandas as pd
import shap

ROOT = Path(__file__).resolve().parents[1]

def explain_row(row: pd.DataFrame):
    model = joblib.load(ROOT/"models"/"best_model.pkl")
    X = row.copy()
    explainer = shap.Explainer(model, X)
    values = explainer(X)
    return values
