from __future__ import annotations

import pandas as pd

from sih26170 import (
    SyntheticDataset,
    evaluate_repeated_splits,
    evaluate_synthetic_dataset,
    evaluate_time_sweep,
    generate_burn_in_dataset,
    make_batch_split,
    summarize_repeated_splits,
)


def test_batch_split_has_no_overlap() -> None:
    dataset = generate_burn_in_dataset(
        seed=11, n_batches=6, components_per_batch=40
    )
    split = make_batch_split(dataset.readings, random_state=9)

    assert set(split.train_batch_ids).isdisjoint(split.test_batch_ids)
    assert set(split.train_batch_ids) | set(split.test_batch_ids) == set(
        dataset.batch_ids
    )


def test_evaluation_compares_all_required_methods() -> None:
    dataset = generate_burn_in_dataset(
        seed=12, n_batches=6, components_per_batch=40
    )
    report = evaluate_synthetic_dataset(dataset, as_of_hour=24)

    assert set(report.metrics["method"]) == {
        "fixed_limit",
        "robust_mad",
        "isolation_forest",
        "combined",
    }
    assert report.scored_components["batch_id"].isin(
        report.split.test_batch_ids
    ).all()
    assert report.metrics["review_recall"].between(0, 1).all()
    assert report.metrics["false_positive_rate"].between(0, 1).all()
    for _, row in report.metrics.iterrows():
        assert row["review_recall"] + row["false_negative_rate"] == 1.0


def test_future_measurement_changes_cannot_change_early_scores() -> None:
    original = generate_burn_in_dataset(
        seed=13, n_batches=6, components_per_batch=40
    )
    changed_readings = original.readings.copy()
    future = changed_readings["hours"] > 24
    changed_readings.loc[future, "measurement_value"] *= 100.0
    changed = SyntheticDataset(
        readings=changed_readings,
        labels=original.labels.copy(),
        seed=original.seed,
        hours=original.hours,
    )

    first = evaluate_synthetic_dataset(original, as_of_hour=24)
    second = evaluate_synthetic_dataset(changed, as_of_hour=24)
    score_columns = [
        "component_id",
        "anomaly_score",
        "flag_fixed_limit",
        "flag_robust_mad",
        "flag_isolation_forest",
        "flag_combined",
    ]
    first_scores = first.scored_components[score_columns].sort_values(
        "component_id"
    ).reset_index(drop=True)
    second_scores = second.scored_components[score_columns].sort_values(
        "component_id"
    ).reset_index(drop=True)

    pd.testing.assert_frame_equal(first_scores, second_scores)


def test_time_sweep_keeps_method_rows_for_each_hour() -> None:
    dataset = generate_burn_in_dataset(
        seed=14, n_batches=6, components_per_batch=40
    )

    sweep = evaluate_time_sweep(dataset, as_of_hours=(6.0, 24.0, 96.0))

    assert len(sweep) == 3 * 4
    assert set(sweep["as_of_hour"]) == {6.0, 24.0, 96.0}
    assert sweep.groupby("as_of_hour")["method"].nunique().eq(4).all()


def test_repeated_split_summary_has_one_row_per_method() -> None:
    dataset = generate_burn_in_dataset(
        seed=15, n_batches=6, components_per_batch=40
    )
    repeated = evaluate_repeated_splits(
        dataset, split_random_states=(1, 2)
    )
    summary = summarize_repeated_splits(repeated)

    assert len(repeated) == 2 * 4
    assert len(summary) == 4
    assert "review_recall_mean" in summary
    assert "review_recall_std" in summary
