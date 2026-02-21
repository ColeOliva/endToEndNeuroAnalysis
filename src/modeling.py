"""Baseline modeling workflow for EEG decoding."""

from __future__ import annotations

import csv
import json
import statistics
from collections import Counter
from pathlib import Path
from typing import Any


def _load_rows(features_path: Path) -> list[dict[str, str]]:
    with features_path.open("r", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        return list(reader)


def _safe_float(value: str, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: str, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _is_float(value: str | None) -> bool:
    if value is None:
        return False
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


def _infer_feature_columns(rows: list[dict[str, str]]) -> list[str]:
    if not rows:
        return []

    excluded = {
        "subject",
        "task",
        "run",
        "event_code",
        "label",
        "label_binary",
    }
    candidates = [column for column in rows[0].keys() if column not in excluded]

    numeric_columns: list[str] = []
    for column in candidates:
        if all(_is_float(row.get(column)) for row in rows):
            numeric_columns.append(column)
    return numeric_columns


def _balanced_accuracy(y_true: list[int], y_pred: list[int]) -> float:
    positives = sum(1 for value in y_true if value == 1)
    negatives = sum(1 for value in y_true if value == 0)

    tp = sum(1 for truth, pred in zip(y_true, y_pred) if truth == 1 and pred == 1)
    tn = sum(1 for truth, pred in zip(y_true, y_pred) if truth == 0 and pred == 0)

    tpr = tp / positives if positives else 0.0
    tnr = tn / negatives if negatives else 0.0
    return (tpr + tnr) / 2.0


def run_modeling(config: dict[str, Any], outputs_dir: Path) -> dict[str, Any]:
    """Train and evaluate a baseline logistic regression model with subject-wise CV."""
    try:
        from sklearn.linear_model import LogisticRegression
        from sklearn.model_selection import GroupKFold
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import StandardScaler
    except ImportError as exc:
        raise RuntimeError(
            "scikit-learn is required for modeling. Install dependencies from requirements.txt."
        ) from exc

    modeling_cfg = config.get("modeling", {}) if isinstance(config.get("modeling", {}), dict) else {}
    n_splits = int(modeling_cfg.get("n_splits", 5))
    random_seed = int(config.get("project", {}).get("random_seed", 42))

    features_path = outputs_dir / "tables" / "baseline_features.csv"
    if not features_path.exists():
        raise FileNotFoundError(f"Feature table not found: {features_path}")

    rows = _load_rows(features_path)
    if not rows:
        raise ValueError("Feature table is empty; cannot run modeling.")

    feature_names = _infer_feature_columns(rows)
    if not feature_names:
        raise ValueError("No numeric feature columns found in baseline_features.csv.")
    X = [[_safe_float(row.get(name, "0")) for name in feature_names] for row in rows]
    y = [_safe_int(row.get("label_binary", "0")) for row in rows]
    groups = [row.get("subject", "") for row in rows]

    unique_groups = sorted({group for group in groups if group})
    if len(unique_groups) < 2:
        raise ValueError("Need at least 2 subjects for subject-wise cross-validation.")

    n_splits = max(2, min(n_splits, len(unique_groups)))
    splitter = GroupKFold(n_splits=n_splits)

    model = Pipeline(
        steps=[
            ("scale", StandardScaler()),
            (
                "clf",
                LogisticRegression(
                    max_iter=1000,
                    random_state=random_seed,
                    class_weight="balanced",
                ),
            ),
        ]
    )

    fold_rows: list[dict[str, object]] = []
    model_scores: list[float] = []
    baseline_scores: list[float] = []

    for fold_idx, (train_idx, test_idx) in enumerate(splitter.split(X, y, groups), start=1):
        X_train = [X[i] for i in train_idx]
        y_train = [y[i] for i in train_idx]
        X_test = [X[i] for i in test_idx]
        y_test = [y[i] for i in test_idx]

        model.fit(X_train, y_train)
        y_pred = model.predict(X_test).tolist()

        majority_label = Counter(y_train).most_common(1)[0][0]
        y_base = [majority_label for _ in y_test]

        model_bal_acc = _balanced_accuracy(y_test, y_pred)
        base_bal_acc = _balanced_accuracy(y_test, y_base)
        model_scores.append(model_bal_acc)
        baseline_scores.append(base_bal_acc)

        test_subjects = sorted({groups[i] for i in test_idx})
        fold_rows.append(
            {
                "fold": fold_idx,
                "n_train": len(train_idx),
                "n_test": len(test_idx),
                "n_test_subjects": len(test_subjects),
                "test_subjects": ",".join(test_subjects),
                "model_balanced_accuracy": round(model_bal_acc, 6),
                "baseline_balanced_accuracy": round(base_bal_acc, 6),
            }
        )

    metrics_dir = outputs_dir / "metrics"
    tables_dir = outputs_dir / "tables"
    metrics_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)

    folds_path = tables_dir / "modeling_fold_metrics.csv"
    with folds_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(fold_rows[0].keys()))
        writer.writeheader()
        writer.writerows(fold_rows)

    summary = {
        "n_rows": len(rows),
        "n_subjects": len(unique_groups),
        "n_splits": n_splits,
        "feature_columns": feature_names,
        "mean_model_balanced_accuracy": statistics.mean(model_scores),
        "mean_baseline_balanced_accuracy": statistics.mean(baseline_scores),
        "std_model_balanced_accuracy": statistics.pstdev(model_scores) if len(model_scores) > 1 else 0.0,
        "std_baseline_balanced_accuracy": statistics.pstdev(baseline_scores)
        if len(baseline_scores) > 1
        else 0.0,
    }

    summary_path = metrics_dir / "modeling_baseline_metrics.json"
    with summary_path.open("w", encoding="utf-8") as stream:
        json.dump(summary, stream, indent=2)

    return {
        "fold_metrics_output": str(folds_path),
        "summary_output": str(summary_path),
        "mean_model_balanced_accuracy": summary["mean_model_balanced_accuracy"],
    }
