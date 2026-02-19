"""Central configuration for dataset paths and analysis defaults."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
DERIVATIVES_DIR = DATA_DIR / "derivatives"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

RANDOM_SEED = 42
