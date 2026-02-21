"""Baseline feature extraction from BIDS event files and metadata."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


def _load_event_levels(bids_root: Path, task_name: str) -> dict[str, str]:
    event_json = bids_root / f"task-{task_name}_events.json"
    if not event_json.exists():
        return {}

    payload = json.load(event_json.open("r", encoding="utf-8"))
    value_block = payload.get("value", {})
    if not isinstance(value_block, dict):
        return {}
    levels = value_block.get("Levels", {})
    if not isinstance(levels, dict):
        return {}
    return {str(key): str(value) for key, value in levels.items()}


def _coerce_float(value: str | None, default: float = 0.0) -> float:
    if value is None:
        return default
    value = value.strip()
    if not value or value.lower() == "n/a":
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _coerce_int(value: str | None, default: int = 0) -> int:
    if value is None:
        return default
    value = value.strip()
    if not value or value.lower() == "n/a":
        return default
    try:
        return int(float(value))
    except ValueError:
        return default


def extract_features(config: dict[str, Any], bids_root: Path, outputs_dir: Path) -> dict[str, Any]:
    """Build a baseline trial-level feature table from events and metadata mapping."""
    analysis_cfg = config.get("analysis", {}) if isinstance(config.get("analysis", {}), dict) else {}
    target_column = str(analysis_cfg.get("target_label", "value"))
    task_name = str(analysis_cfg.get("task_name", "VisualOddball"))
    class_labels_cfg = analysis_cfg.get("class_labels", ["Frequent_NonTarget", "Rare_Target"])
    class_labels = [str(item) for item in class_labels_cfg] if isinstance(class_labels_cfg, list) else []

    levels = _load_event_levels(bids_root, task_name)

    tables_dir = outputs_dir / "tables"
    metrics_dir = outputs_dir / "metrics"
    tables_dir.mkdir(parents=True, exist_ok=True)
    metrics_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, object]] = []
    class_counter: Counter[str] = Counter()

    event_files = sorted(bids_root.glob("sub-*/eeg/*_events.tsv"))
    for event_path in event_files:
        subject = event_path.parts[-3].replace("sub-", "")
        file_stem = event_path.name.replace("_events.tsv", "")
        stem_parts = file_stem.split("_")
        task = next((part.split("-", 1)[1] for part in stem_parts if part.startswith("task-")), "")
        run = next((part.split("-", 1)[1] for part in stem_parts if part.startswith("run-")), "1")

        with event_path.open("r", encoding="utf-8") as stream:
            reader = csv.DictReader(stream, delimiter="\t")
            previous_onset = None
            trial_index = 0
            for event in reader:
                raw_label = str(event.get(target_column, "")).strip()
                mapped_label = levels.get(raw_label, raw_label)

                if class_labels and mapped_label not in class_labels:
                    continue

                onset = _coerce_float(event.get("onset"), default=0.0)
                duration = _coerce_float(event.get("duration"), default=0.0)
                sample = _coerce_int(event.get("sample"), default=0)
                isi = 0.0 if previous_onset is None else max(0.0, onset - previous_onset)
                previous_onset = onset

                trial_index += 1
                class_counter[mapped_label] += 1

                rows.append(
                    {
                        "subject": subject,
                        "task": task,
                        "run": run,
                        "trial_index": trial_index,
                        "onset_sec": onset,
                        "duration_sec": duration,
                        "sample": sample,
                        "isi_sec": isi,
                        "event_code": raw_label,
                        "label": mapped_label,
                        "label_binary": 1 if mapped_label == "Rare_Target" else 0,
                    }
                )

    features_path = tables_dir / "baseline_features.csv"
    if rows:
        fieldnames = list(rows[0].keys())
        with features_path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
    else:
        with features_path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(
                stream,
                fieldnames=[
                    "subject",
                    "task",
                    "run",
                    "trial_index",
                    "onset_sec",
                    "duration_sec",
                    "sample",
                    "isi_sec",
                    "event_code",
                    "label",
                    "label_binary",
                ],
            )
            writer.writeheader()

    summary = {
        "n_event_files": len(event_files),
        "n_rows": len(rows),
        "target_column": target_column,
        "task_name": task_name,
        "class_counts": dict(class_counter),
    }

    summary_path = metrics_dir / "baseline_feature_summary.json"
    with summary_path.open("w", encoding="utf-8") as stream:
        json.dump(summary, stream, indent=2)

    return {
        "features_output": str(features_path),
        "summary_output": str(summary_path),
        "n_rows": len(rows),
    }
