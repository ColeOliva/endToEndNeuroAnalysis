"""Main pipeline runner for the EEG analysis scaffold."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Any

import yaml

from .features import extract_features
from .io_bids import validate_bids_root
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


def _step_enabled(config: dict[str, Any], key: str, default: bool = True) -> bool:
    execution = config.get("execution", {})
    if not isinstance(execution, dict):
        return default
    value = execution.get(key, default)
    return bool(value)


def _resolve_path(raw_path: str | Path, project_root: Path) -> Path:
    path = Path(raw_path)
    return path if path.is_absolute() else project_root / path


def run_pipeline(config: dict[str, Any], project_root: Path, run_steps: bool) -> int:
    data_cfg = config.get("data", {}) if isinstance(config.get("data", {}), dict) else {}
    bids_root = _resolve_path(data_cfg.get("bids_root", "data/raw"), project_root)

    LOGGER.info("Pipeline mode: %s", "execute" if run_steps else "plan")
    LOGGER.info("BIDS root: %s", bids_root)

    if _step_enabled(config, "run_data_loading", True):
        if validate_bids_root(bids_root):
            LOGGER.info("Data loading check: BIDS root looks valid.")
        else:
            LOGGER.warning(
                "Data loading check: BIDS markers not found yet at %s (expected during planning before data download).",
                bids_root,
            )

    if not run_steps:
        LOGGER.info("Dry run complete. Use --run-steps to execute implemented steps.")
        return 0

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

    cfg_dry_run = _step_enabled(config, "dry_run", True)
    run_steps = args.run_steps and not cfg_dry_run
    if args.run_steps and cfg_dry_run:
        LOGGER.warning(
            "--run-steps was provided, but execution.dry_run=true in config. Running in dry-run mode."
        )

    return run_pipeline(config=config, project_root=project_root, run_steps=run_steps)


if __name__ == "__main__":
    raise SystemExit(main())
