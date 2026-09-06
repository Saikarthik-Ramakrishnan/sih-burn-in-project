"""Train the offline pilot: python scripts/train_mlcc_prototype.py --help."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from sih26170.mlcc_prototype import train_bundle  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Train IF + XGBoost candidates on synthetic whole-batch splits")
    parser.add_argument("--dataset-dir", type=Path, default=Path("outputs/mlcc_v1"))
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/mlcc_v1/model_bundle"))
    parser.add_argument("--seed", type=int, default=26170)
    args = parser.parse_args()
    result = train_bundle(args.dataset_dir, args.output_dir, seed=args.seed)
    selected = result["selected_model"]
    print(json.dumps({"bundle_dir": result["bundle_dir"], "selected_model": selected,
                      "selection_mae": result["validation_mae_normalized"],
                      "test": result["test"]["models"][selected],
                      "combined_screening": result["test"]["combined_screening"]}, indent=2))


if __name__ == "__main__":
    main()
