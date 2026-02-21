"""EEG-derived feature extraction from BIDS event files and EEGLAB recordings."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np


def _load_mne_or_raise() -> Any:
    try:
        import mne
    except ImportError as exc:
        raise RuntimeError("mne is required for EEG feature extraction. Install requirements.txt.") from exc
    return mne


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


def _bandpower_features(
    waveform: np.ndarray,
    sfreq: float,
    bands: dict[str, tuple[float, float]],
) -> dict[str, float]:
    if waveform.size == 0:
        return {f"bandpower_{name}": 0.0 for name in bands}

    signal = waveform - waveform.mean()
    spectrum = np.fft.rfft(signal)
    power = np.abs(spectrum) ** 2
    freqs = np.fft.rfftfreq(signal.size, d=1.0 / sfreq)

    total_power = float(power.sum()) if power.size else 0.0
    features: dict[str, float] = {}
    for name, (f_lo, f_hi) in bands.items():
        mask = (freqs >= f_lo) & (freqs <= f_hi)
        band_power = float(power[mask].sum()) if np.any(mask) else 0.0
        features[f"bandpower_{name}"] = band_power
        features[f"bandpower_{name}_rel"] = (band_power / total_power) if total_power > 0 else 0.0

    return features


def _extract_waveform_features(
    raw: Any,
    onset_sec: float,
    tmin: float,
    tmax: float,
    baseline_start: float,
    baseline_end: float,
    windows: list[tuple[str, float, float]],
    bands: dict[str, tuple[float, float]],
) -> dict[str, float] | None:
    sfreq = float(raw.info["sfreq"])
    onset_sample = int(round(onset_sec * sfreq))
    start = onset_sample + int(round(tmin * sfreq))
    stop = onset_sample + int(round(tmax * sfreq))

    if start < 0 or stop <= start or stop >= raw.n_times:
        return None

    data = raw.get_data(picks="eeg", start=start, stop=stop)
    if data.size == 0:
        return None

    baseline_s = onset_sample + int(round(baseline_start * sfreq))
    baseline_e = onset_sample + int(round(baseline_end * sfreq))
    baseline_s = max(0, baseline_s)
    baseline_e = min(raw.n_times, baseline_e)

    if baseline_e <= baseline_s:
        return None

    baseline_data = raw.get_data(picks="eeg", start=baseline_s, stop=baseline_e)
    if baseline_data.size == 0:
        return None

    centered = data - baseline_data.mean(axis=1, keepdims=True)
    global_waveform = centered.mean(axis=0)

    features: dict[str, float] = {}
    for name, win_start, win_end in windows:
        w_start = onset_sample + int(round(win_start * sfreq))
        w_end = onset_sample + int(round(win_end * sfreq))
        rel_start = w_start - start
        rel_end = w_end - start

        rel_start = max(0, rel_start)
        rel_end = min(len(global_waveform), rel_end)
        if rel_end <= rel_start:
            features[name] = 0.0
            continue

        segment = global_waveform[rel_start:rel_end]
        features[name] = float(segment.mean())

    features["erp_peak_pos"] = float(global_waveform.max())
    features["erp_peak_neg"] = float(global_waveform.min())
    features["erp_peak_to_peak"] = float(features["erp_peak_pos"] - features["erp_peak_neg"])
    features["erp_mean_abs"] = float(np.mean(np.abs(global_waveform)))
    features["erp_std"] = float(np.std(global_waveform))
    features["erp_auc_abs"] = float(np.trapezoid(np.abs(global_waveform), dx=1.0 / sfreq))
    features.update(_bandpower_features(global_waveform, sfreq=sfreq, bands=bands))
    return features


def _add_subject_z_features(
    rows: list[dict[str, object]],
    feature_keys: list[str],
) -> int:
    if not rows or not feature_keys:
        return 0

    subject_to_rows: dict[str, list[dict[str, object]]] = {}
    for row in rows:
        subject = str(row.get("subject", ""))
        subject_to_rows.setdefault(subject, []).append(row)

    for subject_rows in subject_to_rows.values():
        for key in feature_keys:
            values = np.array([float(row.get(key, 0.0)) for row in subject_rows], dtype=float)
            if values.size == 0:
                continue
            mean_value = float(values.mean())
            std_value = float(values.std())
            safe_std = std_value if std_value > 1e-12 else 1.0
            for row in subject_rows:
                row[f"z_{key}"] = (float(row.get(key, 0.0)) - mean_value) / safe_std

    return len(feature_keys)


def extract_features(config: dict[str, Any], bids_root: Path, outputs_dir: Path) -> dict[str, Any]:
    """Build trial-level EEG-derived ERP features from event-locked windows."""
    mne = _load_mne_or_raise()

    analysis_cfg = config.get("analysis", {}) if isinstance(config.get("analysis", {}), dict) else {}
    target_column = str(analysis_cfg.get("target_label", "value"))
    task_name = str(analysis_cfg.get("task_name", "VisualOddball"))
    class_labels_cfg = analysis_cfg.get("class_labels", ["Frequent_NonTarget", "Rare_Target"])
    class_labels = [str(item) for item in class_labels_cfg] if isinstance(class_labels_cfg, list) else []
    subject_normalization = bool(analysis_cfg.get("subject_normalization", True))

    preprocessing_cfg = (
        config.get("preprocessing", {}) if isinstance(config.get("preprocessing", {}), dict) else {}
    )
    fallback_target_columns: list[str] = []
    preprocessing_event_column = preprocessing_cfg.get("event_column")
    if isinstance(preprocessing_event_column, str) and preprocessing_event_column.strip():
        fallback_target_columns.append(preprocessing_event_column.strip())
    fallback_target_columns.extend(["value", "trial_type"])
    l_freq = float(preprocessing_cfg.get("l_freq", 1.0))
    h_freq = float(preprocessing_cfg.get("h_freq", 40.0))
    tmin = float(preprocessing_cfg.get("tmin", -0.2))
    tmax = float(preprocessing_cfg.get("tmax", 0.8))
    baseline_cfg = preprocessing_cfg.get("baseline", [-0.2, 0.0])
    baseline_start = float(baseline_cfg[0]) if isinstance(baseline_cfg, list) and baseline_cfg else -0.2
    baseline_end = (
        float(baseline_cfg[1])
        if isinstance(baseline_cfg, list) and len(baseline_cfg) > 1
        else 0.0
    )

    windows_cfg = analysis_cfg.get(
        "erp_windows",
        {
            "erp_n1": [0.08, 0.14],
            "erp_p2": [0.15, 0.25],
            "erp_p3": [0.25, 0.5],
        },
    )
    windows: list[tuple[str, float, float]] = []
    if isinstance(windows_cfg, dict):
        for name, bounds in windows_cfg.items():
            if isinstance(bounds, list) and len(bounds) == 2:
                windows.append((str(name), float(bounds[0]), float(bounds[1])))

    bands_cfg = analysis_cfg.get(
        "bandpower_bands",
        {
            "theta": [4.0, 7.0],
            "alpha": [8.0, 12.0],
            "beta": [13.0, 30.0],
        },
    )
    bands: dict[str, tuple[float, float]] = {}
    if isinstance(bands_cfg, dict):
        for name, bounds in bands_cfg.items():
            if isinstance(bounds, list) and len(bounds) == 2:
                bands[str(name)] = (float(bounds[0]), float(bounds[1]))

    levels = _load_event_levels(bids_root, task_name)

    tables_dir = outputs_dir / "tables"
    metrics_dir = outputs_dir / "metrics"
    tables_dir.mkdir(parents=True, exist_ok=True)
    metrics_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, object]] = []
    class_counter: Counter[str] = Counter()
    processed_files = 0
    skipped_files = 0

    event_files = sorted(bids_root.glob("sub-*/eeg/*_events.tsv"))
    for event_path in event_files:
        eeg_path = event_path.with_name(event_path.name.replace("_events.tsv", "_eeg.set"))
        if not eeg_path.exists():
            skipped_files += 1
            continue

        try:
            raw = mne.io.read_raw_eeglab(str(eeg_path), preload=True, verbose="ERROR")
            raw.pick("eeg")
            raw.filter(l_freq=l_freq, h_freq=h_freq, verbose="ERROR")
            processed_files += 1
        except Exception:
            skipped_files += 1
            continue

        subject = event_path.parts[-3].replace("sub-", "")
        file_stem = event_path.name.replace("_events.tsv", "")
        stem_parts = file_stem.split("_")
        task = next((part.split("-", 1)[1] for part in stem_parts if part.startswith("task-")), "")
        run = next((part.split("-", 1)[1] for part in stem_parts if part.startswith("run-")), "1")

        with event_path.open("r", encoding="utf-8") as stream:
            reader = csv.DictReader(stream, delimiter="\t")
            active_target_column = target_column
            if reader.fieldnames and active_target_column not in reader.fieldnames:
                for candidate in fallback_target_columns:
                    if candidate in reader.fieldnames:
                        active_target_column = candidate
                        break
            previous_onset = None
            trial_index = 0
            for event in reader:
                raw_label = str(event.get(active_target_column, "")).strip()
                mapped_label = levels.get(raw_label, raw_label)

                if class_labels and mapped_label not in class_labels:
                    continue

                onset = _coerce_float(event.get("onset"), default=0.0)
                duration = _coerce_float(event.get("duration"), default=0.0)
                sample = _coerce_int(event.get("sample"), default=0)
                isi = 0.0 if previous_onset is None else max(0.0, onset - previous_onset)
                previous_onset = onset

                waveform_features = _extract_waveform_features(
                    raw=raw,
                    onset_sec=onset,
                    tmin=tmin,
                    tmax=tmax,
                    baseline_start=baseline_start,
                    baseline_end=baseline_end,
                    windows=windows,
                    bands=bands,
                )
                if waveform_features is None:
                    continue

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
                        **waveform_features,
                    }
                )

    features_path = tables_dir / "baseline_features.csv"
    added_z_feature_groups = 0
    base_feature_keys: list[str] = []
    if rows:
        excluded = {
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
        }
        base_feature_keys = [
            key
            for key in rows[0].keys()
            if key not in excluded and isinstance(rows[0].get(key), (float, int))
        ]

        if subject_normalization:
            added_z_feature_groups = _add_subject_z_features(rows, base_feature_keys)

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
        "n_processed_eeg_files": processed_files,
        "n_skipped_eeg_files": skipped_files,
        "n_rows": len(rows),
        "target_column": target_column,
        "task_name": task_name,
        "class_counts": dict(class_counter),
        "erp_windows": {name: [start, end] for name, start, end in windows},
        "bandpower_bands": {name: [lo, hi] for name, (lo, hi) in bands.items()},
        "subject_normalization_enabled": subject_normalization,
        "base_feature_group_count": len(base_feature_keys),
        "z_feature_group_count": added_z_feature_groups,
    }

    summary_path = metrics_dir / "baseline_feature_summary.json"
    with summary_path.open("w", encoding="utf-8") as stream:
        json.dump(summary, stream, indent=2)

    return {
        "features_output": str(features_path),
        "summary_output": str(summary_path),
        "n_rows": len(rows),
    }
