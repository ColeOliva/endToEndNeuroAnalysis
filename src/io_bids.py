"""BIDS data loading utilities."""

from pathlib import Path


def validate_bids_root(bids_root: Path) -> bool:
    """Return True when a BIDS root appears valid."""
    required_markers = ["dataset_description.json"]
    return all((bids_root / marker).exists() for marker in required_markers)
