"""Evaluation of the screening comparison on held-out synthetic batches.

The claims defended here are the ones the project would present: a fixed
upper limit gives no early warning, the batch-relative and combined screens
find known synthetic defect patterns before the limit is crossed, and the
metric tables are internally consistent and free of leakage.
"""

from __future__ import annotations

import math

import pandas as pd
import pytest

from sih26170.splitting import split_batches
from sih26170.synthetic import SyntheticDataset, generate_burn_in_dataset
from sih26170.evaluation_harness import (
    ALL_METHODS,
    ENGINEER_REVIEW_DISCLAIMER,
    PRIMARY_METHODS,
    ScreeningConfig,
    fit_detectors,
    run_early_warning_ladder,
    run_holdout_evaluation,
    run_parameter_sweep,
    screen_components,
    summarise_recommendations,
    sweep_summary,
)
from sih26170.splitting import build_split_features

ALLOWED_ACTIONS = {"ACCEPT", "MONITOR", "RETEST", "ENGINEER_REVIEW"}


@pytest.fixture(scope="module")
def dataset():
    return generate_burn_in_dataset(seed=101, n_batches=4, components_per_batch=24)


@pytest.fixture(scope="module")
def report(dataset):
    return run_holdout_evaluation(dataset)


@pytest.fixture(scope="module")
def ladder(dataset):
    return run_early_warning_ladder(dataset, as_of_hours=(24.0, 48.0, 96.0, 144.0))


def _row(metrics: pd.DataFrame, method: str) -> pd.Series:
    return metrics.loc[metrics["method"] == method].iloc[0]


def test_every_compared_method_is_reported(report) -> None:
    assert list(report.metrics["method"]) == list(ALL_METHODS)
    assert set(PRIMARY_METHODS).issubset(set(report.metrics["method"]))


def test_ordinary_accuracy_is_never_reported(report) -> None:
    assert not [name for name in report.metrics.columns if "accuracy" in name.lower()]


def test_metrics_are_internally_consistent(report) -> None:
    for _, row in report.metrics.iterrows():
        assert row["n_defects"] + row["n_healthy"] + row["n_tester_faults"] == row["n_components"]
        assert row["true_positives"] + row["false_negatives"] == row["n_defects"]
        assert row["false_positives"] + row["true_negatives"] == row["n_healthy"]
        assert row["defect_recall"] == pytest.approx(1.0 - row["false_negative_rate"])
        if row["true_positives"] + row["false_positives"] > 0:
            assert row["precision"] == pytest.approx(
                row["true_positives"] / (row["true_positives"] + row["false_positives"])
            )
        else:
            assert math.isnan(row["precision"])


def test_tester_faults_are_scored_apart_from_component_defects(report) -> None:
    row = _row(report.metrics, "combined")
    assert row["n_tester_faults"] > 0
    # They are excluded from recall and precision, and reported on their own.
    assert 0.0 <= row["tester_fault_flag_rate"] <= 1.0
    assert row["false_positive_rate_incl_tester_faults"] >= row["false_positive_rate"]


def test_a_fixed_upper_limit_gives_no_early_warning(report) -> None:
    """By construction it can only fire once the limit has already been crossed."""

    fixed = _row(report.metrics, "fixed_limit")
    combined = _row(report.metrics, "combined")

    assert fixed["n_early_warnings"] == 0
    assert combined["n_early_warnings"] > 0
    assert combined["defect_recall"] > fixed["defect_recall"]
    assert combined["median_lead_time_hours"] > 0


def test_known_synthetic_drift_is_found_on_held_out_batches(report) -> None:
    rates = report.scenario_flag_rates.set_index("scenario")["combined"]
    assert rates["gradual_drift"] >= 0.75
    assert rates["sudden_step"] >= 0.5
    assert rates["healthy_stable"] <= 0.10
    assert rates["gradual_drift"] > rates["healthy_stable"]


def test_accelerating_drift_is_the_documented_failure_case(report) -> None:
    """At 24 hours the signal is still inside the noise; this must stay visible."""

    rates = report.scenario_flag_rates.set_index("scenario")
    assert rates.loc["accelerating_drift", "fixed_limit"] == 0.0
    assert rates.loc["accelerating_drift", "combined"] < rates.loc["gradual_drift", "combined"]


def test_evaluation_is_deterministic(dataset, report) -> None:
    repeat = run_holdout_evaluation(dataset)
    pd.testing.assert_frame_equal(report.metrics, repeat.metrics)
    assert report.split == repeat.split


def test_scores_do_not_depend_on_the_other_held_out_batches(dataset, report) -> None:
    """Removing one evaluation batch must not move another batch's scores."""

    dropped = report.split.test_batches[0]
    kept = report.split.test_batches[-1]
    assert dropped != kept

    reduced = SyntheticDataset(
        readings=dataset.readings.loc[dataset.readings["batch_id"] != dropped].copy(),
        labels=dataset.labels.loc[dataset.labels["batch_id"] != dropped].copy(),
        seed=dataset.seed,
        hours=dataset.hours,
    )
    partial = run_holdout_evaluation(reduced, split=report.split)

    columns = ["component_id", "combined_score", "robust_mad_score", "isolation_forest_score"]
    before = report.screened.loc[report.screened["batch_id"] == kept, columns]
    after = partial.screened.loc[partial.screened["batch_id"] == kept, columns]
    pd.testing.assert_frame_equal(
        before.sort_values("component_id").reset_index(drop=True),
        after.sort_values("component_id").reset_index(drop=True),
    )


def test_lead_time_is_measured_before_the_limit_is_crossed(ladder) -> None:
    flagged = ladder.lead_times.query("method == 'combined' and is_defect")
    early = flagged.loc[flagged["lead_hours"].notna() & (flagged["lead_hours"] > 0)]
    assert len(early) > 0
    assert (early["first_flag_hour"] < early["first_exceedance_hour"]).all()

    fixed = ladder.summary.loc[ladder.summary["method"] == "fixed_limit"].iloc[0]
    combined = ladder.summary.loc[ladder.summary["method"] == "combined"].iloc[0]
    assert fixed["n_flagged_before_crossing"] == 0
    assert combined["n_flagged_before_crossing"] > 0
    assert combined["n_ever_flagged"] > fixed["n_ever_flagged"]


def test_recall_improves_as_the_screening_hour_moves_later(ladder) -> None:
    recall = ladder.metrics.pivot(index="as_of_hour", columns="method", values="defect_recall")
    assert recall["combined"].iloc[-1] >= recall["combined"].iloc[0]
    assert recall["combined"].max() >= 0.75


def test_parameter_sweep_covers_every_requested_combination(dataset) -> None:
    sweep = run_parameter_sweep(
        dataset,
        as_of_hours=(24.0, 48.0),
        contaminations=(0.05, 0.15),
        robust_thresholds=(2.5, 4.5),
        fixed_limit_fractions=(0.8, 1.0),
    )
    assert len(sweep) == 2 * 2 * 2 * 2 * len(ALL_METHODS)
    assert sweep["defect_recall"].between(0.0, 1.0).all()

    summary = sweep_summary(sweep)
    fixed = summary.loc[summary["method"] == "fixed_limit"]
    # The fixed limit cannot see contamination, so only hour x fraction remain.
    assert len(fixed) == 2 * 2

    lenient = sweep.query("method == 'robust_mad' and robust_threshold == 2.5")
    strict = sweep.query("method == 'robust_mad' and robust_threshold == 4.5")
    assert lenient["defect_recall"].mean() >= strict["defect_recall"].mean()


def test_reusing_a_fitted_forest_matches_fitting_it_again(dataset) -> None:
    """The sweep caches the forest across parameters it cannot see."""

    split = split_batches(dataset.readings, test_fraction=0.4, random_state=7)
    train_features, test_features = build_split_features(
        dataset.readings, split, as_of_hour=24.0
    )
    config = ScreeningConfig(as_of_hour=24.0, robust_threshold=2.5)

    fresh = screen_components(train_features, test_features, config)
    reused = screen_components(
        train_features,
        test_features,
        config,
        detectors=fit_detectors(train_features, config),
    )
    pd.testing.assert_frame_equal(fresh, reused)


def test_a_guard_band_buys_early_warning_that_the_hard_limit_cannot(dataset) -> None:
    sweep = run_parameter_sweep(
        dataset,
        as_of_hours=(96.0,),
        contaminations=(0.1,),
        robust_thresholds=(3.5,),
        fixed_limit_fractions=(0.6, 1.0),
        methods=("fixed_limit",),
    )
    at_limit = sweep.loc[sweep["fixed_limit_fraction"] == 1.0].iloc[0]
    guard_band = sweep.loc[sweep["fixed_limit_fraction"] == 0.6].iloc[0]
    assert at_limit["n_early_warnings"] == 0
    assert guard_band["n_early_warnings"] > 0
    assert guard_band["defect_recall"] >= at_limit["defect_recall"]


def test_per_family_fitting_refuses_an_unseen_family(dataset) -> None:
    split = split_batches(dataset.readings, test_fraction=0.4, random_state=7)
    train_features, test_features = build_split_features(
        dataset.readings, split, as_of_hour=24.0
    )
    family = test_features["component_family"].iloc[0]
    starved = train_features.loc[train_features["component_family"] != family]

    with pytest.raises(ValueError, match="comparable reference components"):
        screen_components(starved, test_features, ScreeningConfig())


def test_the_harness_recommends_and_never_certifies(report, dataset) -> None:
    summary = summarise_recommendations(report, dataset.labels)

    assert set(summary["recommended_action"]).issubset(ALLOWED_ACTIONS)
    assert summary["n_components"].sum() == report.n_test_components
    assert summary["share_of_components"].sum() == pytest.approx(1.0)

    # No action certifies or condemns a part; each one asks a person to act.
    actions = " ".join(summary["recommended_action"]).upper()
    for forbidden in ("CERTIFY", "CERTIFIED", "REJECT", "PASS", "FAIL", "SCRAP"):
        assert forbidden not in actions

    assert report.disclaimer == ENGINEER_REVIEW_DISCLAIMER
    assert "engineer" in report.disclaimer.lower()


def test_a_flagged_component_always_carries_a_reason(report) -> None:
    flagged = report.screened.loc[report.screened["combined_flag"]]
    assert len(flagged) > 0
    assert flagged["reason_codes"].map(len).gt(0).all()
