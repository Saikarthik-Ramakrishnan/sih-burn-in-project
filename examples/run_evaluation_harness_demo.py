"""Run the full screening comparison on labelled synthetic burn-in data.

    .venv/bin/python examples/run_evaluation_harness_demo.py
    .venv/bin/python examples/run_evaluation_harness_demo.py --output-dir outputs/evaluation

Everything printed here comes from synthetic data. It is a measurement of
detector behaviour against known ground truth, not evidence about hardware.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from sih26170.evaluation_harness import (
    ENGINEER_REVIEW_DISCLAIMER,
    ScreeningConfig,
    compare_fit_scopes,
    run_early_warning_ladder,
    run_holdout_evaluation,
    run_parameter_sweep,
    summarise_recommendations,
    sweep_summary,
)
from sih26170.splitting import assert_split_is_leakage_safe, split_batches
from sih26170.synthetic import generate_burn_in_dataset

HEADLINE_COLUMNS = [
    "method_label",
    "n_defects",
    "defect_recall",
    "false_negative_rate",
    "false_positive_rate",
    "precision",
    "n_early_warnings",
    "median_lead_time_hours",
    "tester_fault_flag_rate",
]


def _show(title: str, frame: pd.DataFrame) -> None:
    print(f"\n### {title}")
    print(frame.round(3).to_string(index=False))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=26170)
    parser.add_argument("--batches", type=int, default=8)
    parser.add_argument("--components-per-batch", type=int, default=50)
    parser.add_argument("--as-of-hour", type=float, default=24.0)
    parser.add_argument("--output-dir", type=Path, default=None)
    arguments = parser.parse_args()

    pd.set_option("display.width", 220)
    pd.set_option("display.max_columns", 60)

    dataset = generate_burn_in_dataset(
        seed=arguments.seed,
        n_batches=arguments.batches,
        components_per_batch=arguments.components_per_batch,
    )
    split = split_batches(dataset.readings, test_fraction=0.4, random_state=7)
    assert_split_is_leakage_safe(dataset.readings, split, as_of_hour=arguments.as_of_hour)

    print(f"!! {ENGINEER_REVIEW_DISCLAIMER}")
    print(
        f"\nDataset: {len(dataset.labels)} synthetic components, "
        f"{len(dataset.readings)} readings, seed {dataset.seed}"
    )
    print(f"Training batches:   {', '.join(split.train_batches)}")
    print(f"Evaluation batches: {', '.join(split.test_batches)}")
    _show("Scenario counts", dataset.scenario_counts().rename("n").reset_index())

    config = ScreeningConfig(as_of_hour=arguments.as_of_hour)
    report = run_holdout_evaluation(dataset, config=config, split=split)
    _show(
        f"Screening comparison at hour {arguments.as_of_hour:g} (held-out batches)",
        report.metrics[HEADLINE_COLUMNS],
    )
    _show("Flag rate per labelled scenario", report.scenario_flag_rates)
    _show("Recommended actions (decision support only)",
          summarise_recommendations(report, dataset.labels))

    ladder = run_early_warning_ladder(dataset, config=config, split=split)
    _show(
        "Defect recall by screening hour",
        ladder.metrics.pivot(
            index="as_of_hour", columns="method", values="defect_recall"
        ).reset_index(),
    )
    _show(
        "Detection lead time over the full ladder",
        ladder.summary.drop(columns="method_label"),
    )

    scopes = compare_fit_scopes(dataset, config=config, split=split)
    _show(
        "Effect of pooling unlike families in one Isolation Forest",
        scopes[["method", "fit_scope", "defect_recall", "false_positive_rate", "precision"]],
    )

    sweep = run_parameter_sweep(dataset, base_config=config, split=split)
    summary = sweep_summary(sweep)
    _show(
        "Sensitivity of the combined screen",
        summary.loc[summary["method"] == "combined"].drop(
            columns=["method", "method_label", "fit_scope"]
        ),
    )

    if arguments.output_dir is not None:
        destination = Path(arguments.output_dir)
        destination.mkdir(parents=True, exist_ok=True)
        report.metrics.to_csv(destination / "screening_metrics.csv", index=False)
        report.scenario_flag_rates.to_csv(destination / "scenario_flag_rates.csv", index=False)
        ladder.metrics.to_csv(destination / "ladder_metrics.csv", index=False)
        ladder.lead_times.to_csv(destination / "lead_times.csv", index=False)
        ladder.summary.to_csv(destination / "lead_time_summary.csv", index=False)
        sweep.to_csv(destination / "parameter_sweep.csv", index=False)
        summary.to_csv(destination / "parameter_sweep_summary.csv", index=False)
        metadata = {
            "generator_version": dataset.generator_version,
            "seed": dataset.seed,
            "n_components": int(len(dataset.labels)),
            "hours": list(dataset.hours),
            "split": split.to_dict(),
            "config": config.to_dict(),
            "synthetic_data_only": True,
            "disclaimer": ENGINEER_REVIEW_DISCLAIMER,
        }
        (destination / "run_metadata.json").write_text(
            json.dumps(metadata, indent=2), encoding="utf-8"
        )
        print(f"\nWrote CSV results and run metadata to {destination}")


if __name__ == "__main__":
    main()
