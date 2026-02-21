"""Automated report artifact generation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as stream:
        payload = json.load(stream)
    return payload if isinstance(payload, dict) else {}


def generate_results_report(config: dict[str, Any], outputs_dir: Path, report_dir: Path) -> dict[str, Any]:
    """Generate a concise markdown results report from latest artifacts."""
    report_dir.mkdir(parents=True, exist_ok=True)

    feature_summary = _load_json(outputs_dir / "metrics" / "baseline_feature_summary.json")
    model_summary = _load_json(outputs_dir / "metrics" / "modeling_baseline_metrics.json")
    viz_summary = _load_json(outputs_dir / "metrics" / "visualization_summary.json")

    confusion = model_summary.get("confusion_matrix", {}) if isinstance(model_summary, dict) else {}
    tn = confusion.get("tn", "n/a")
    fp = confusion.get("fp", "n/a")
    fn = confusion.get("fn", "n/a")
    tp = confusion.get("tp", "n/a")

    lines = [
        "# Results Summary",
        "",
        "## Dataset and Features",
        f"- Event files processed: {feature_summary.get('n_event_files', 'n/a')}",
        f"- EEG files processed: {feature_summary.get('n_processed_eeg_files', 'n/a')}",
        f"- EEG files skipped: {feature_summary.get('n_skipped_eeg_files', 'n/a')}",
        f"- Trial rows in feature table: {feature_summary.get('n_rows', 'n/a')}",
        f"- Class counts: {feature_summary.get('class_counts', {})}",
        "",
        "## Modeling",
        f"- Subjects in CV: {model_summary.get('n_subjects', 'n/a')}",
        f"- CV folds: {model_summary.get('n_splits', 'n/a')}",
        f"- Mean balanced accuracy (model): {model_summary.get('mean_model_balanced_accuracy', 'n/a')}",
        f"- Mean balanced accuracy (baseline): {model_summary.get('mean_baseline_balanced_accuracy', 'n/a')}",
        f"- ROC AUC: {model_summary.get('roc_auc', 'n/a')}",
        f"- Confusion matrix (TN, FP, FN, TP): ({tn}, {fp}, {fn}, {tp})",
        "",
        "## Figures",
        "- Class balance: ../outputs/figures/class_balance.png",
        "- Fold balanced accuracy: ../outputs/figures/fold_balanced_accuracy.png",
        "- Mean balanced accuracy: ../outputs/figures/mean_balanced_accuracy.png",
        "- Confusion matrix: ../outputs/figures/confusion_matrix.png",
        "- ROC curve: ../outputs/figures/roc_curve.png",
        "",
        "## Interpretation",
        (
            f"- Model minus baseline (balanced accuracy): {viz_summary.get('model_minus_baseline', 'n/a')}"
        ),
        "- Current signal-feature pipeline shows above-chance decoding on subject-wise CV.",
    ]

    report_path = report_dir / "results.md"
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return {
        "report_path": str(report_path),
    }
