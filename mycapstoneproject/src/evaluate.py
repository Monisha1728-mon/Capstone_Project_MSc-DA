from pathlib import Path
import joblib
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix, roc_curve

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT/"data"/"processed"
MODELS = ROOT/"models"
RESULTS = ROOT/"results"
RESULTS.mkdir(exist_ok=True)

def main():
    X = pd.read_csv(DATA/"X_test.csv")
    y = pd.read_csv(DATA/"y_test.csv").iloc[:, 0]

    rows = []
    loaded = {}
    for name in ["random_forest", "logistic_regression", "gradient_boosting"]:
        model = joblib.load(MODELS/f"{name}.pkl")
        loaded[name] = model
        pred = model.predict(X)
        proba = model.predict_proba(X)[:, 1]
        rows.append({
            "Model": name,
            "Accuracy": accuracy_score(y, pred),
            "Precision": precision_score(y, pred, zero_division=0),
            "Recall": recall_score(y, pred, zero_division=0),
            "F1": f1_score(y, pred, zero_division=0),
            "ROC-AUC": roc_auc_score(y, proba)
        })

    metrics = pd.DataFrame(rows)
    metrics.to_csv(RESULTS/"metrics_comparison.csv", index=False)

    # Primary selection rule: ROC-AUC, then F1, then Recall.
    best_name = metrics.sort_values(
        ["ROC-AUC", "F1", "Recall"], ascending=False
    ).iloc[0]["Model"]
    joblib.dump(loaded[best_name], MODELS/"best_model.pkl")
    (MODELS/"best_model_name.txt").write_text(best_name)

    # Confusion matrix and ROC curve for selected model.
    best = loaded[best_name]
    pred = best.predict(X)
    proba = best.predict_proba(X)[:, 1]

    cm = confusion_matrix(y, pred)
    plt.figure()
    plt.imshow(cm)
    plt.title(f"Confusion Matrix - {best_name}")
    plt.xlabel("Predicted")
    plt.ylabel("Actual")
    for (i, j), value in __import__("numpy").ndenumerate(cm):
        plt.text(j, i, str(value), ha="center", va="center")
    plt.savefig(RESULTS/"confusion_matrix.png", bbox_inches="tight")
    plt.close()

    fpr, tpr, _ = roc_curve(y, proba)
    plt.figure()
    plt.plot(fpr, tpr, label=f"AUC={roc_auc_score(y, proba):.3f}")
    plt.plot([0,1], [0,1], linestyle="--")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title(f"ROC Curve - {best_name}")
    plt.legend()
    plt.savefig(RESULTS/"roc_curve.png", bbox_inches="tight")
    plt.close()

    print(metrics.to_string(index=False))
    print(f"Selected deployment model: {best_name}")

if __name__ == "__main__":
    main()
