from pathlib import Path
import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT/"data"/"processed"
MODELS = ROOT/"models"

def main():
    MODELS.mkdir(exist_ok=True)
    X = pd.read_csv(DATA/"X_train_smote.csv")
    y = pd.read_csv(DATA/"y_train_smote.csv").iloc[:, 0]

    models = {
        "logistic_regression": LogisticRegression(max_iter=2000, class_weight=None, random_state=42),
        "random_forest": RandomForestClassifier(
            n_estimators=400, random_state=42, class_weight=None, n_jobs=-1
        ),
        "gradient_boosting": GradientBoostingClassifier(random_state=42)
    }

    for name, model in models.items():
        model.fit(X, y)
        joblib.dump(model, MODELS/f"{name}.pkl")
        print(f"Saved {name}.pkl")

if __name__ == "__main__":
    main()
