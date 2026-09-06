"""Rebuild the explicitly synthetic MLCC development and holdout datasets."""

from __future__ import annotations

import argparse
import json

from sih26170.mlcc_synthetic import export_mlcc_dataset, generate_mlcc_dataset


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="outputs/mlcc_v1")
    parser.add_argument("--seed", type=int, default=26170)
    parser.add_argument("--batches", type=int, default=60)
    parser.add_argument("--components-per-batch", type=int, default=200)
    parser.add_argument("--skip-stress", action="store_true")
    args = parser.parse_args()
    dataset = generate_mlcc_dataset(
        seed=args.seed, n_batches=args.batches, components_per_batch=args.components_per_batch,
    )
    manifest = export_mlcc_dataset(dataset, args.output_dir, include_stress=not args.skip_stress)
    print(json.dumps({
        "output_dir": args.output_dir, "components": manifest["components"],
        "readings": manifest["readings"], "split_batches": manifest["split_batches"],
        "scenario_counts": manifest["scenario_counts"], "files": len(manifest["files"]),
        "provenance": manifest["provenance"],
    }, indent=2))


if __name__ == "__main__":
    main()
