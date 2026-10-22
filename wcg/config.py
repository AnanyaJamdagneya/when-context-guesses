"""Fixed experiment settings. Change values here (or via CLI flags / env vars), never per item."""

import os
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATASET_PATH = ROOT / "data" / "sentence_pairs.csv"
FREEZE_PATH = ROOT / "data" / "dataset_freeze.json"
RESULTS_DIR = ROOT / "results"

# One seed for the whole project. Masking positions are derived from (SEED, pair_id),
# so both sentences in a pair always get the same positions.
SEED = 20261022

# The pilot uses the first three pairs in the file. This was fixed before any
# results existed, so the pilot pairs are not hand-picked.
PILOT_PAIRS = ("P01", "P02", "P03")

DEFAULT_MODEL = "claude-opus-5-5"
DEFAULT_EFFORT = "medium"
MAX_TOKENS = 16000

MOCK_MODEL_NAME = "MOCK-no-api-call"


@dataclass(frozen=True)
class ModelSettings:
    model: str
    effort: str
    max_tokens: int

    def as_dict(self) -> dict:
        return asdict(self)


def load_settings(model: str | None = None, effort: str | None = None, mock: bool = False) -> ModelSettings:
    if mock:
        return ModelSettings(model=MOCK_MODEL_NAME, effort="n/a", max_tokens=0)
    return ModelSettings(
        model=model or os.environ.get("WCG_MODEL", DEFAULT_MODEL),
        effort=effort or os.environ.get("WCG_EFFORT", DEFAULT_EFFORT),
        max_tokens=MAX_TOKENS,
    )


def mode_dir(mock: bool) -> Path:
    """Real and mock results live in separate folders so they can never mix."""
    return RESULTS_DIR / ("mock" if mock else "real")
