"""Run saved models without fitting; produce JSON for a dashboard/backend."""

import argparse
import json
from pathlib import Path
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from sih26170.mlcc_prototype import load_bundle, screen_readings  # noqa: E402
from sih26170.features import GROUP_COLUMNS  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Score MLCC 0/24-hour CSV using a frozen model bundle")
    parser.add_argument("csv", type=Path)
    parser.add_argument("--bundle", type=Path, default=Path("outputs/mlcc_v2/model_bundle"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--future-outcomes", type=Path, help="Optional reveal-only truth, never model input")
    parser.add_argument("--forecast-model", default="xgboost", choices=["xgboost_v2", "xgboost", "persistence", "linear_extrapolation", "ridge", "hist_gradient_boosting"], help="Explicit demo candidate; validation winner stays recorded separately")
    args = parser.parse_args()
    ids = {column: str for column in GROUP_COLUMNS}
    result = screen_readings(pd.read_csv(args.csv, dtype=ids), load_bundle(args.bundle),
                             future_outcomes=pd.read_csv(args.future_outcomes, dtype=ids) if args.future_outcomes else None,
                             forecast_model=args.forecast_model)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"output": str(args.output.resolve()), **result["summary"]}, indent=2))


if __name__ == "__main__":
    main()
