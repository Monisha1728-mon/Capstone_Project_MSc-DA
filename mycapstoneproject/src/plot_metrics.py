from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

METRICS_FILE = ROOT / "results" / "metrics_comparison.csv"
OUTPUT_FILE = ROOT / "results" / "model_metrics_comparison.png"


def create_metrics_chart():
    metrics = pd.read_csv(METRICS_FILE)

    metrics["Model"] = (
        metrics["Model"]
        .str.replace("_", " ")
        .str.title()
    )

    metrics = metrics.rename(
        columns={"F1": "F1-score"}
    )

    metric_names = [
        "Accuracy",
        "Precision",
        "Recall",
        "F1-score",
        "ROC-AUC",
    ]

    chart_data = metrics.set_index("Model")[metric_names]

    ax = chart_data.plot(
        kind="bar",
        figsize=(12, 7),
        color=[
            "#2f6fb3",
            "#0d8078",
            "#d48a18",
            "#7c4dcc",
            "#d85855",
        ],
        edgecolor="white",
        width=0.78,
    )

    ax.set_title(
        "Performance Comparison of Machine-Learning Models",
        fontsize=18,
        fontweight="bold",
        color="#17324d",
        pad=16,
    )

    ax.set_xlabel("Classification model")
    ax.set_ylabel("Metric score (0–1)")
    ax.set_ylim(0, 1.08)

    ax.grid(
        axis="y",
        linestyle="--",
        alpha=0.35
    )

    ax.set_axisbelow(True)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.legend(
        ncol=5,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.12),
    )

    for container in ax.containers:
        ax.bar_label(
            container,
            fmt="%.3f",
            fontsize=8,
            rotation=90,
            padding=3,
        )

    plt.tight_layout()

    plt.savefig(
        OUTPUT_FILE,
        dpi=180,
        bbox_inches="tight",
    )

    plt.show()

    print(
        f"Chart saved to: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    create_metrics_chart()