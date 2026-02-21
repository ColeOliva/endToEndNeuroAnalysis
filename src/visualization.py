"""Visualization workflow for QC and baseline model results."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as stream:
        payload = json.load(stream)
    return payload if isinstance(payload, dict) else {}


def _load_fold_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def _load_roc_rows(path: Path) -> list[dict[str, float]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    parsed: list[dict[str, float]] = []
    for row in rows:
        parsed.append(
            {
                "fpr": float(row["fpr"]),
                "tpr": float(row["tpr"]),
                "threshold": float(row["threshold"]),
            }
        )
    return parsed


def make_figures(config: dict[str, Any], outputs_dir: Path) -> dict[str, Any]:
    """Generate key QC/model figures for reporting."""
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError("matplotlib is required for visualization.") from exc

    figures_dir = outputs_dir / "figures"
    metrics_dir = outputs_dir / "metrics"
    tables_dir = outputs_dir / "tables"
    figures_dir.mkdir(parents=True, exist_ok=True)
    metrics_dir.mkdir(parents=True, exist_ok=True)

    created_figures: list[str] = []

    feature_summary = _load_json(metrics_dir / "baseline_feature_summary.json")
    class_counts_raw = feature_summary.get("class_counts", {})
    class_counts = class_counts_raw if isinstance(class_counts_raw, dict) else {}
    if class_counts:
        labels = list(class_counts.keys())
        values = [int(class_counts[label]) for label in labels]

        fig, ax = plt.subplots(figsize=(6, 4))
        ax.bar(labels, values)
        ax.set_title("Class Balance")
        ax.set_ylabel("Trial Count")
        ax.set_xlabel("Class")
        fig.tight_layout()

        out_path = figures_dir / "class_balance.png"
        fig.savefig(out_path, dpi=150)
        plt.close(fig)
        created_figures.append(str(out_path))

    fold_rows = _load_fold_rows(tables_dir / "modeling_fold_metrics.csv")
    if fold_rows:
        folds = [int(row["fold"]) for row in fold_rows]
        model_scores = [float(row["model_balanced_accuracy"]) for row in fold_rows]
        baseline_scores = [float(row["baseline_balanced_accuracy"]) for row in fold_rows]

        fig, ax = plt.subplots(figsize=(7, 4))
        ax.plot(folds, model_scores, marker="o", label="Model")
        ax.plot(folds, baseline_scores, marker="o", label="Baseline")
        ax.set_title("Fold-wise Balanced Accuracy")
        ax.set_xlabel("Fold")
        ax.set_ylabel("Balanced Accuracy")
        ax.set_xticks(folds)
        ax.set_ylim(0.0, 1.0)
        ax.legend()
        fig.tight_layout()

        out_path = figures_dir / "fold_balanced_accuracy.png"
        fig.savefig(out_path, dpi=150)
        plt.close(fig)
        created_figures.append(str(out_path))

    model_summary = _load_json(metrics_dir / "modeling_baseline_metrics.json")
    model_mean = float(model_summary.get("mean_model_balanced_accuracy", 0.0))
    baseline_mean = float(model_summary.get("mean_baseline_balanced_accuracy", 0.0))
    if model_summary:
        fig, ax = plt.subplots(figsize=(5, 4))
        labels = ["Baseline", "Model"]
        values = [baseline_mean, model_mean]
        ax.bar(labels, values)
        ax.set_title("Mean Balanced Accuracy")
        ax.set_ylabel("Score")
        ax.set_ylim(0.0, 1.0)
        fig.tight_layout()

        out_path = figures_dir / "mean_balanced_accuracy.png"
        fig.savefig(out_path, dpi=150)
        plt.close(fig)
        created_figures.append(str(out_path))

    confusion = model_summary.get("confusion_matrix", {}) if isinstance(model_summary, dict) else {}
    if isinstance(confusion, dict) and {"tn", "fp", "fn", "tp"}.issubset(confusion.keys()):
        tn = int(confusion["tn"])
        fp = int(confusion["fp"])
        fn = int(confusion["fn"])
        tp = int(confusion["tp"])

        matrix = [[tn, fp], [fn, tp]]
        fig, ax = plt.subplots(figsize=(5, 4))
        image = ax.imshow(matrix)
        ax.set_title("Confusion Matrix")
        ax.set_xlabel("Predicted")
        ax.set_ylabel("True")
        ax.set_xticks([0, 1])
        ax.set_yticks([0, 1])
        ax.set_xticklabels(["NonTarget", "Target"])
        ax.set_yticklabels(["NonTarget", "Target"])
        for i in range(2):
            for j in range(2):
                ax.text(j, i, str(matrix[i][j]), ha="center", va="center")
        fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
        fig.tight_layout()

        out_path = figures_dir / "confusion_matrix.png"
        fig.savefig(out_path, dpi=150)
        plt.close(fig)
        created_figures.append(str(out_path))

    roc_rows = _load_roc_rows(metrics_dir / "roc_curve_points.csv")
    roc_auc = float(model_summary.get("roc_auc", 0.0)) if isinstance(model_summary, dict) else 0.0
    if roc_rows:
        fpr = [row["fpr"] for row in roc_rows]
        tpr = [row["tpr"] for row in roc_rows]

        fig, ax = plt.subplots(figsize=(5, 4))
        ax.plot(fpr, tpr, label=f"Model (AUC={roc_auc:.3f})")
        ax.plot([0, 1], [0, 1], linestyle="--", label="Chance")
        ax.set_title("ROC Curve")
        ax.set_xlabel("False Positive Rate")
        ax.set_ylabel("True Positive Rate")
        ax.set_xlim(0.0, 1.0)
        ax.set_ylim(0.0, 1.0)
        ax.legend()
        fig.tight_layout()

        out_path = figures_dir / "roc_curve.png"
        fig.savefig(out_path, dpi=150)
        plt.close(fig)
        created_figures.append(str(out_path))

    summary = {
        "n_figures": len(created_figures),
        "figure_paths": created_figures,
        "model_minus_baseline": model_mean - baseline_mean,
    }

    summary_path = metrics_dir / "visualization_summary.json"
    with summary_path.open("w", encoding="utf-8") as stream:
        json.dump(summary, stream, indent=2)

    return {
        "visualization_summary": str(summary_path),
        "n_figures": len(created_figures),
    }
