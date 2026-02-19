"""Main pipeline runner for the EEG analysis scaffold."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any

import yaml

from .features import extract_features
from .io_bids import (build_eeg_index, summarize_eeg_index, validate_bids_root,
                      write_eeg_index_csv)
from .modeling import run_modeling
from .preprocess import run_preprocessing
from .visualization import make_figures

LOGGER = logging.getLogger(__name__)


def _load_config(config_path: Path) -> dict[str, Any]:
    with config_path.open("r", encoding="utf-8") as stream:
        content = yaml.safe_load(stream) or {}

    if not isinstance(content, dict):
        raise ValueError("Config file must contain a top-level mapping/object.")

    return content


def _load_optional_yaml(config_path: Path) -> dict[str, Any]:
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as stream:
        content = yaml.safe_load(stream) or {}

    if not isinstance(content, dict):
        raise ValueError(f"Config file must contain a top-level mapping/object: {config_path}")

    return content


def _step_enabled(config: dict[str, Any], key: str, default: bool = True) -> bool:
    execution = config.get("execution", {})
    if not isinstance(execution, dict):
        return default
    value = execution.get(key, default)
    return bool(value)


def _resolve_path(raw_path: str | Path, project_root: Path) -> Path:
    path = Path(raw_path)
    return path if path.is_absolute() else project_root / path


def _resolve_dataset_from_registry(
    config: dict[str, Any],
    datasets_config: dict[str, Any],
    project_root: Path,
) -> tuple[Path | None, str | None]:
    selection_status = datasets_config.get("selection_status", {})
    if not isinstance(selection_status, dict):
        raise ValueError("datasets.yaml: selection_status must be a mapping.")

    finalized = bool(selection_status.get("finalized", False))
    selected_key = selection_status.get("selected_dataset_key")

    if not finalized:
        LOGGER.info("Dataset registry not finalized yet; using default config paths/labels.")
        return None, None

    if not selected_key or not isinstance(selected_key, str):
        raise ValueError(
            "datasets.yaml: selection_status.finalized=true requires selection_status.selected_dataset_key."
        )

    candidates = datasets_config.get("candidate_datasets", [])
    if not isinstance(candidates, list):
        raise ValueError("datasets.yaml: candidate_datasets must be a list.")

    selected_dataset = None
    for item in candidates:
        if isinstance(item, dict) and item.get("key") == selected_key:
            selected_dataset = item
            break

    if not isinstance(selected_dataset, dict):
        raise ValueError(f"datasets.yaml: selected_dataset_key '{selected_key}' was not found.")

    raw_bids_root = selected_dataset.get("bids_root_relative")
    if not raw_bids_root or not isinstance(raw_bids_root, str):
        raise ValueError(
            f"datasets.yaml: selected dataset '{selected_key}' must define bids_root_relative."
        )

    target_label = selected_dataset.get("target_label_column")
    if not target_label or not isinstance(target_label, str):
        raise ValueError(
            f"datasets.yaml: selected dataset '{selected_key}' must define target_label_column."
        )

    resolved_bids_root = _resolve_path(raw_bids_root, project_root)

    analysis_cfg = config.get("analysis", {})
    if not isinstance(analysis_cfg, dict):
        analysis_cfg = {}
        config["analysis"] = analysis_cfg
    analysis_cfg["target_label"] = target_label

    LOGGER.info("Dataset registry selected key: %s", selected_key)
    LOGGER.info("Resolved target label from registry: %s", target_label)
    return resolved_bids_root, target_label


def run_pipeline(config: dict[str, Any], project_root: Path, run_steps: bool) -> int:
    data_cfg = config.get("data", {}) if isinstance(config.get("data", {}), dict) else {}
    bids_root = _resolve_path(data_cfg.get("bids_root", "data/raw"), project_root)
    outputs_dir = _resolve_path(data_cfg.get("outputs_dir", "outputs"), project_root)

    LOGGER.info("Pipeline mode: %s", "execute" if run_steps else "plan")
    LOGGER.info("BIDS root: %s", bids_root)
    analysis_cfg = config.get("analysis", {}) if isinstance(config.get("analysis", {}), dict) else {}
    LOGGER.info("Target label: %s", analysis_cfg.get("target_label", "(not set)"))

    if _step_enabled(config, "run_data_loading", True):
        if validate_bids_root(bids_root):
            LOGGER.info("Data loading check: BIDS root looks valid.")

            eeg_index_records = build_eeg_index(bids_root)
            eeg_summary = summarize_eeg_index(eeg_index_records)
            LOGGER.info(
                "EEG index summary: files=%s, subjects=%s, tasks=%s",
                eeg_summary["n_files"],
                eeg_summary["n_subjects"],
                eeg_summary["n_tasks"],
            )

            tables_dir = outputs_dir / "tables"
            tables_dir.mkdir(parents=True, exist_ok=True)

            index_output_path = tables_dir / "eeg_index.csv"
            summary_output_path = tables_dir / "eeg_index_summary.json"

            write_eeg_index_csv(eeg_index_records, index_output_path)
            with summary_output_path.open("w", encoding="utf-8") as stream:
                json.dump(eeg_summary, stream, indent=2)

            LOGGER.info("Saved EEG index table to: %s", index_output_path)
            LOGGER.info("Saved EEG index summary to: %s", summary_output_path)
        else:
            LOGGER.warning(
                "Data loading check: BIDS markers not found yet at %s (expected during planning before data download).",
                bids_root,
            )

    if not run_steps:
        LOGGER.info("Dry run complete. Use --run-steps to execute implemented steps.")
        return 0

    derivatives_dir = _resolve_path(data_cfg.get("derivatives_dir", "data/derivatives"), project_root)

    steps: list[tuple[str, Any, str]] = [
        ("run_preprocessing", run_preprocessing, "Preprocessing"),
        ("run_features", extract_features, "Feature extraction"),
        ("run_modeling", run_modeling, "Modeling"),
        ("run_visualization", make_figures, "Visualization"),
    ]

    for config_key, step_fn, display_name in steps:
        if not _step_enabled(config, config_key, True):
            LOGGER.info("%s skipped via config.", display_name)
            continue
        try:
            LOGGER.info("Starting %s...", display_name)
            if config_key == "run_preprocessing":
                step_result = step_fn(
                    config=config,
                    bids_root=bids_root,
                    derivatives_dir=derivatives_dir,
                    outputs_dir=outputs_dir,
                )
                LOGGER.info("Preprocessing artifacts: %s", step_result)
            else:
                step_fn()
            LOGGER.info("Finished %s.", display_name)
        except NotImplementedError as exc:
            LOGGER.error("%s is not implemented yet: %s", display_name, exc)
            return 1

    LOGGER.info("Pipeline finished.")
    return 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="EEG pipeline runner")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/default.yaml"),
        help="Path to YAML configuration file.",
    )
    parser.add_argument(
        "--run-steps",
        action="store_true",
        help="Execute step functions (will fail until stubs are implemented).",
    )
    parser.add_argument(
        "--datasets-config",
        type=Path,
        default=None,
        help="Optional path to dataset registry YAML file (overrides config registry settings).",
    )
    return parser.parse_args()


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    args = _parse_args()

    project_root = Path(__file__).resolve().parents[1]
    config_path = args.config if args.config.is_absolute() else project_root / args.config

    if not config_path.exists():
        LOGGER.error("Config file not found: %s", config_path)
        return 2

    config = _load_config(config_path)

    registry_cfg = config.get("registry", {}) if isinstance(config.get("registry", {}), dict) else {}
    prefer_registry = bool(registry_cfg.get("prefer_registry_selection", True))
    datasets_cfg_raw = registry_cfg.get("datasets_config", "configs/datasets.yaml")

    datasets_cfg_input = args.datasets_config if args.datasets_config is not None else Path(datasets_cfg_raw)
    datasets_cfg_path = (
        datasets_cfg_input if datasets_cfg_input.is_absolute() else project_root / datasets_cfg_input
    )

    try:
        if prefer_registry:
            datasets_cfg = _load_optional_yaml(datasets_cfg_path)
            resolved_bids_root, _ = _resolve_dataset_from_registry(
                config=config,
                datasets_config=datasets_cfg,
                project_root=project_root,
            )
            if resolved_bids_root is not None:
                data_cfg = config.get("data", {})
                if not isinstance(data_cfg, dict):
                    data_cfg = {}
                    config["data"] = data_cfg
                data_cfg["bids_root"] = str(resolved_bids_root)
        else:
            LOGGER.info("Dataset registry resolution disabled via registry.prefer_registry_selection=false.")
    except FileNotFoundError:
        LOGGER.info("Dataset registry file not found at %s; using default config.", datasets_cfg_path)
    except ValueError as exc:
        LOGGER.error("Invalid dataset registry configuration: %s", exc)
        return 2

    cfg_dry_run = _step_enabled(config, "dry_run", True)
    run_steps = args.run_steps and not cfg_dry_run
    if args.run_steps and cfg_dry_run:
        LOGGER.warning(
            "--run-steps was provided, but execution.dry_run=true in config. Running in dry-run mode."
        )

    return run_pipeline(config=config, project_root=project_root, run_steps=run_steps)


if __name__ == "__main__":
    raise SystemExit(main())
