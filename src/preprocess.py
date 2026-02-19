"""EEG preprocessing workflow scaffolding and planning utilities."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .io_bids import build_eeg_index


def _get_preprocessing_config(config: dict[str, Any]) -> dict[str, Any]:
    raw = config.get("preprocessing", {})
    if not isinstance(raw, dict):
        raw = {}

    return {
        "l_freq": float(raw.get("l_freq", 1.0)),
        "h_freq": float(raw.get("h_freq", 40.0)),
        "notch_freqs": list(raw.get("notch_freqs", [60.0])),
        "resample_hz": int(raw.get("resample_hz", 250)),
        "tmin": float(raw.get("tmin", -0.2)),
        "tmax": float(raw.get("tmax", 0.8)),
        "baseline": list(raw.get("baseline", [-0.2, 0.0])),
        "event_column": str(raw.get("event_column", "trial_type")),
        "reference": str(raw.get("reference", "average")),
    }


def _write_queue_csv(queue_rows: list[dict[str, str]], output_path: Path) -> None:
    columns = [
        "sub",
        "ses",
        "task",
        "run",
        "eeg_file",
        "events_tsv",
        "derivative_output",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        for row in queue_rows:
            writer.writerow(row)


def run_preprocessing(
    config: dict[str, Any],
    bids_root: Path,
    derivatives_dir: Path,
    outputs_dir: Path,
) -> dict[str, Any]:
    """Create preprocessing plan artifacts from config and discovered BIDS EEG files."""
    settings = _get_preprocessing_config(config)
    index_records = build_eeg_index(bids_root)

    derivatives_dir.mkdir(parents=True, exist_ok=True)
    tables_dir = outputs_dir / "tables"
    tables_dir.mkdir(parents=True, exist_ok=True)

    queue_rows: list[dict[str, str]] = []
    for row in index_records:
        subject = str(row.get("sub") or "unknown")
        session = str(row.get("ses") or "noses")
        run = str(row.get("run") or "norun")
        derivative_output = derivatives_dir / f"sub-{subject}_ses-{session}_run-{run}_epochs.fif"

        queue_rows.append(
            {
                "sub": subject,
                "ses": session,
                "task": str(row.get("task") or ""),
                "run": run,
                "eeg_file": str(row.get("eeg_file") or ""),
                "events_tsv": str(row.get("events_tsv") or ""),
                "derivative_output": str(derivative_output),
            }
        )

    plan = {
        "preprocessing_settings": settings,
        "n_input_files": len(index_records),
        "n_jobs": len(queue_rows),
    }

    plan_output = tables_dir / "preprocessing_plan.json"
    queue_output = tables_dir / "preprocessing_queue.csv"

    with plan_output.open("w", encoding="utf-8") as stream:
        json.dump(plan, stream, indent=2)

    _write_queue_csv(queue_rows, queue_output)

    return {
        "plan_output": str(plan_output),
        "queue_output": str(queue_output),
        "n_jobs": len(queue_rows),
    }
