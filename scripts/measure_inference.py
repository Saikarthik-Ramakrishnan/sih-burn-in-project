"""Measure end-to-end /screen duration with the REAL MLCC bundle loaded.

These are measurements from this machine, not a performance guarantee. They
include genuine model inference: Isolation Forest scoring, the forecast, the
conformal interval and TreeSHAP contributions for every component.

Usage (from the repository root):

    .venv/Scripts/python.exe scripts/measure_inference.py
"""

from __future__ import annotations

import io
import statistics
import sys
import time
from pathlib import Path

import pandas as pd
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from sih26170.api.config import ServiceMode, Settings  # noqa: E402
from sih26170.api.main import create_app  # noqa: E402

DEMO_DIR = PROJECT_ROOT / "outputs" / "mlcc_v1"
BUNDLE = DEMO_DIR / "model_bundle"
REPEATS = 5
SIZES = (60, 240, 800)


def main() -> None:
    early = pd.read_csv(DEMO_DIR / "demo_early.csv", dtype=str)
    outcomes = pd.read_csv(DEMO_DIR / "demo_outcomes.csv", dtype=str)
    outcomes = outcomes[outcomes["hours"] == "168"][early.columns]
    components = sorted(early["component_id"].unique())

    settings = Settings(mode=ServiceMode.DEMO, mlcc_bundle_dir=BUNDLE)

    started = time.perf_counter()
    app = create_app(settings)
    with TestClient(app) as client:
        load_ms = (time.perf_counter() - started) * 1000
        print(f"startup (bundle load + verify + probe): {load_ms:.0f} ms\n")
        print(f"{'components':>11}  {'rows':>7}  {'KiB':>7}  {'wall ms':>9}  {'server ms':>10}")

        for size in SIZES:
            if size > len(components):
                continue
            keep = set(components[:size])
            frame = pd.concat(
                [
                    early[early["component_id"].isin(keep)],
                    outcomes[outcomes["component_id"].isin(keep)],
                ],
                ignore_index=True,
            )
            buffer = io.StringIO(newline="")
            frame.to_csv(buffer, index=False, lineterminator="\n")
            payload = buffer.getvalue().encode("utf-8")

            wall: list[float] = []
            server: list[float] = []
            for _ in range(REPEATS):
                begin = time.perf_counter()
                response = client.post(
                    "/api/v1/screen",
                    files={"file": ("bench.csv", payload, "text/csv")},
                    data={"forecast_model": "xgboost"},
                )
                wall.append((time.perf_counter() - begin) * 1000)
                response.raise_for_status()
                server.append(response.json()["duration_ms"])

            print(
                f"{size:>11}  {len(frame):>7}  {len(payload) / 1024:>7.0f}"
                f"  {statistics.median(wall):>9.0f}  {statistics.median(server):>10.0f}"
            )


if __name__ == "__main__":
    main()
