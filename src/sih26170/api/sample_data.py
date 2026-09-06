"""The synthetic MLCC sample CSV served by GET /api/v1/sample.csv.

This is a slice of Karthik's shipped demonstration dataset
(``outputs/mlcc_v1/demo_early.csv`` plus the 168 h rows of
``demo_outcomes.csv``), not a fixture invented here. Using his exact schema
matters: renaming a generic IC fixture to look like MLCC data would be exactly
the sort of claim this project must not make.

Provenance, stated plainly: every row carries ``data_source=synthetic`` and
``is_synthetic=True`` from the generator. It is a labelled SYNTHETIC dataset. It
is not measured hardware, and results on it are not evidence of screening
accuracy on real capacitors.

The file is assembled deterministically - components are taken in sorted order,
so the same request always returns identical bytes.
"""

from __future__ import annotations

import functools
import io

import pandas as pd

from sih26170.api.config import PROJECT_ROOT

SAMPLE_FILENAME = "sih26170_mlcc_synthetic_sample.csv"

DEMO_DIR = PROJECT_ROOT / "outputs" / "mlcc_v1"
EARLY_CSV = DEMO_DIR / "demo_early.csv"
OUTCOMES_CSV = DEMO_DIR / "demo_outcomes.csv"

#: Number of components in the served sample. The full demo set has 800; a
#: smaller slice keeps the download quick while still giving every batch enough
#: peers for a meaningful batch comparison.
SAMPLE_COMPONENTS = 240

#: Later checkpoint included so a demonstration can reveal the outcome after the
#: prediction has been shown. It is never an inference input.
OUTCOME_HOUR = "168"


class SampleDataUnavailable(RuntimeError):
    """Raised when the shipped demo dataset is not present."""


@functools.lru_cache(maxsize=1)
def build_sample_csv() -> bytes:
    """Return the sample CSV bytes. Deterministic and cached."""
    if not EARLY_CSV.is_file():
        raise SampleDataUnavailable(
            f"The MLCC demonstration dataset is not present at {EARLY_CSV}."
        )

    early = pd.read_csv(EARLY_CSV, dtype=str)
    components = sorted(early["component_id"].unique())[:SAMPLE_COMPONENTS]
    selected = early[early["component_id"].isin(components)].copy()

    frames = [selected]
    if OUTCOMES_CSV.is_file():
        outcomes = pd.read_csv(OUTCOMES_CSV, dtype=str)
        later = outcomes[
            outcomes["component_id"].isin(components) & (outcomes["hours"] == OUTCOME_HOUR)
        ]
        if not later.empty:
            frames.append(later[selected.columns])

    combined = pd.concat(frames, ignore_index=True)
    combined = combined.sort_values(
        ["batch_id", "component_id", "hours"], key=lambda s: s.astype(str), kind="stable"
    )

    buffer = io.StringIO(newline="")
    combined.to_csv(buffer, index=False, lineterminator="\n")
    return buffer.getvalue().encode("utf-8")


def sample_description() -> dict[str, object]:
    """Facts about the sample, for the endpoint's headers and the docs."""
    return {
        "family": "MLCC_X7R",
        "measurement": "leakage_ua",
        "unit": "uA",
        "components": SAMPLE_COMPONENTS,
        "early_hours": [0, 24],
        "outcome_hour": int(OUTCOME_HOUR),
        "provenance": "synthetic",
        "source": "outputs/mlcc_v1/demo_early.csv + demo_outcomes.csv",
    }
