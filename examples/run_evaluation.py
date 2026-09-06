"""Run the reproducible multi-batch synthetic evaluation."""

from __future__ import annotations

import argparse
from pathlib import Path

from sih26170 import (
    evaluate_repeated_splits,
    evaluate_synthetic_dataset,
    evaluate_time_sweep,
    generate_burn_in_dataset,
    summarize_repeated_splits,
    write_evaluation_report,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-hour", type=float, default=24.0)
    parser.add_argument("--batches", type=int, default=12)
    parser.add_argument("--components-per-batch", type=int, default=60)
    parser.add_argument("--seed", type=int, default=26170)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/evaluation_24h"),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    dataset = generate_burn_in_dataset(
        seed=args.seed,
        n_batches=args.batches,
        components_per_batch=args.components_per_batch,
    )
    report = evaluate_synthetic_dataset(dataset, as_of_hour=args.as_of_hour)
    destination = write_evaluation_report(report, args.output_dir)
    time_sweep = evaluate_time_sweep(dataset)
    repeated = evaluate_repeated_splits(dataset, as_of_hour=args.as_of_hour)
    repeated_summary = summarize_repeated_splits(repeated)
    time_sweep.to_csv(destination / "time_sweep_metrics.csv", index=False)
    repeated.to_csv(destination / "repeated_split_metrics.csv", index=False)
    repeated_summary.to_csv(destination / "repeated_split_summary.csv", index=False)

    columns = [
        "method",
        "review_recall",
        "false_negative_rate",
        "false_positive_rate",
        "precision",
        "future_failure_recall",
        "median_early_warning_lead_hours",
    ]
    print("SYNTHETIC EVALUATION ONLY — not aerospace validation")
    print(f"Train batches: {', '.join(report.split.train_batch_ids)}")
    print(f"Test batches:  {', '.join(report.split.test_batch_ids)}")
    print(report.metrics[columns].to_string(index=False))
    print("\nFive held-out-batch splits (mean ± sample standard deviation):")
    repeated_columns = [
        "method",
        "review_recall_mean",
        "review_recall_std",
        "false_positive_rate_mean",
        "false_positive_rate_std",
        "future_failure_recall_mean",
        "future_failure_recall_std",
    ]
    print(repeated_summary[repeated_columns].to_string(index=False))
    print(f"Detailed output: {destination.resolve()}")


if __name__ == "__main__":
    main()
