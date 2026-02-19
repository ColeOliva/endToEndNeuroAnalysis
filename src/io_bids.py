"""BIDS data loading utilities."""

from __future__ import annotations

import csv
from pathlib import Path

EEG_SUFFIX = "_eeg"
EEG_EXTENSIONS = (".edf", ".bdf", ".vhdr", ".set", ".fif")


def validate_bids_root(bids_root: Path) -> bool:
    """Return True when a BIDS root appears valid."""
    required_markers = ["dataset_description.json"]
    return all((bids_root / marker).exists() for marker in required_markers)


def discover_eeg_files(bids_root: Path) -> list[Path]:
    """Discover BIDS EEG files under the root directory."""
    if not bids_root.exists():
        return []

    discovered: list[Path] = []
    for extension in EEG_EXTENSIONS:
        discovered.extend(bids_root.rglob(f"*{EEG_SUFFIX}{extension}"))

    return sorted(path for path in discovered if path.is_file())


def _parse_bids_entities(file_name: str) -> dict[str, str | None]:
    """Parse BIDS entities from a file name stem."""
    stem_parts = file_name.split("_")
    entities: dict[str, str | None] = {
        "sub": None,
        "ses": None,
        "task": None,
        "run": None,
        "acq": None,
        "recording": None,
        "space": None,
        "split": None,
    }

    for part in stem_parts:
        if "-" not in part:
            continue
        key, value = part.split("-", maxsplit=1)
        if key in entities:
            entities[key] = value

    return entities


def _infer_sidecar_paths(eeg_file: Path) -> tuple[Path, Path]:
    """Infer associated events.tsv and channels.tsv sidecars for an EEG file."""
    stem = eeg_file.stem
    if not stem.endswith(EEG_SUFFIX):
        events_path = eeg_file.with_name(f"{stem}_events.tsv")
        channels_path = eeg_file.with_name(f"{stem}_channels.tsv")
        return events_path, channels_path

    base_stem = stem[: -len(EEG_SUFFIX)]
    events_path = eeg_file.with_name(f"{base_stem}_events.tsv")
    channels_path = eeg_file.with_name(f"{base_stem}_channels.tsv")
    return events_path, channels_path


def build_eeg_index(bids_root: Path) -> list[dict[str, object]]:
    """Build a tabular index of EEG recordings and key BIDS metadata."""
    records: list[dict[str, object]] = []

    for eeg_file in discover_eeg_files(bids_root):
        entities = _parse_bids_entities(eeg_file.stem)
        events_path, channels_path = _infer_sidecar_paths(eeg_file)

        records.append(
            {
                "sub": entities["sub"],
                "ses": entities["ses"],
                "task": entities["task"],
                "run": entities["run"],
                "acq": entities["acq"],
                "recording": entities["recording"],
                "space": entities["space"],
                "split": entities["split"],
                "datatype": eeg_file.parent.name,
                "eeg_file": str(eeg_file),
                "events_tsv": str(events_path),
                "channels_tsv": str(channels_path),
                "events_exists": events_path.exists(),
                "channels_exists": channels_path.exists(),
            }
        )

    return records


def summarize_eeg_index(index_records: list[dict[str, object]]) -> dict[str, int]:
    """Return compact dataset-level counts from the EEG index."""
    if not index_records:
        return {
            "n_files": 0,
            "n_subjects": 0,
            "n_tasks": 0,
        }

    subjects = {
        str(record["sub"])
        for record in index_records
        if record.get("sub") is not None and str(record.get("sub"))
    }
    tasks = {
        str(record["task"])
        for record in index_records
        if record.get("task") is not None and str(record.get("task"))
    }

    return {
        "n_files": int(len(index_records)),
        "n_subjects": int(len(subjects)),
        "n_tasks": int(len(tasks)),
    }


def write_eeg_index_csv(index_records: list[dict[str, object]], output_path: Path) -> None:
    """Write EEG index records to CSV."""
    columns = [
        "sub",
        "ses",
        "task",
        "run",
        "acq",
        "recording",
        "space",
        "split",
        "datatype",
        "eeg_file",
        "events_tsv",
        "channels_tsv",
        "events_exists",
        "channels_exists",
    ]

    with output_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        for row in index_records:
            writer.writerow(row)
