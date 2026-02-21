from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.features import extract_features


def _resolve_registry_selection(config: dict, root: Path) -> None:
    registry_cfg = config.get("registry", {}) if isinstance(config.get("registry", {}), dict) else {}
    datasets_rel = str(registry_cfg.get("datasets_config", "configs/datasets.yaml"))
    datasets_path = root / datasets_rel
    if not datasets_path.exists():
        return

    datasets = yaml.safe_load(datasets_path.read_text(encoding="utf-8")) or {}
    if not isinstance(datasets, dict):
        return

    selection = datasets.get("selection_status", {})
    if not isinstance(selection, dict) or not bool(selection.get("finalized", False)):
        return

    selected_key = selection.get("selected_dataset_key")
    candidates = datasets.get("candidate_datasets", [])
    if not isinstance(selected_key, str) or not isinstance(candidates, list):
        return

    selected = None
    for item in candidates:
        if isinstance(item, dict) and item.get("key") == selected_key:
            selected = item
            break

    if not isinstance(selected, dict):
        return

    analysis_cfg = config.get("analysis", {}) if isinstance(config.get("analysis", {}), dict) else {}
    target_label = selected.get("target_label_column")
    if isinstance(target_label, str) and target_label:
        analysis_cfg["target_label"] = target_label
    task_name = selected.get("task_name")
    if isinstance(task_name, str) and task_name:
        analysis_cfg["task_name"] = task_name
    class_labels = selected.get("class_labels")
    if isinstance(class_labels, list):
        analysis_cfg["class_labels"] = [str(v) for v in class_labels]
    config["analysis"] = analysis_cfg


def main() -> None:
    root = ROOT
    config = yaml.safe_load((root / "configs" / "default.yaml").read_text(encoding="utf-8"))
    _resolve_registry_selection(config, root)
    result = extract_features(
        config=config,
        bids_root=root / "data" / "raw" / "openneuro_candidate_1",
        outputs_dir=root / "outputs",
    )
    print("extract_features_result", result)

    summary_path = root / "outputs" / "metrics" / "baseline_feature_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    print("feature_summary_keys", sorted(summary.keys()))
    print("subject_normalization_enabled", summary.get("subject_normalization_enabled"))
    print("base_feature_group_count", summary.get("base_feature_group_count"))
    print("z_feature_group_count", summary.get("z_feature_group_count"))


if __name__ == "__main__":
    main()
