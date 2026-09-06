"""Scenario-level checks on the synthetic burn-in generator.

These tests defend the properties the evaluation depends on: the data obeys
the public input contract, every row is marked synthetic, the seven scenarios
are present and correctly labelled, and the physical shape of each defect is
what the evaluation claims it is.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from sih26170.synthetic import (
    DEFAULT_FAMILIES,
    DEFECT_SCENARIOS,
    FAULT_SCENARIOS,
    SCENARIOS,
    SYNTHETIC_DATA_SOURCE,
    generate_burn_in_dataset,
)
from sih26170.validation import validate_readings


@pytest.fixture(scope="module")
def dataset():
    return generate_burn_in_dataset(seed=101, n_batches=4, components_per_batch=24)


def _readings_at(dataset, hour: float) -> pd.DataFrame:
    at_hour = dataset.readings.loc[dataset.readings["hours"] == hour]
    return at_hour.merge(
        dataset.labels[["component_id", "scenario"]], on="component_id", how="left"
    )


def test_dataset_passes_the_public_input_contract(dataset) -> None:
    validate_readings(dataset.readings)


def test_every_generated_row_is_marked_synthetic(dataset) -> None:
    assert (dataset.readings["data_source"] == SYNTHETIC_DATA_SOURCE).all()
    assert dataset.readings["is_synthetic"].all()
    assert dataset.labels["is_synthetic"].all()
    # A ground-truth label must never travel with a reading.
    assert "scenario" not in dataset.readings.columns
    assert "is_defect" not in dataset.readings.columns


def test_generator_is_reproducible_and_seeded_per_batch() -> None:
    first = generate_burn_in_dataset(seed=101, n_batches=4, components_per_batch=24)
    repeat = generate_burn_in_dataset(seed=101, n_batches=4, components_per_batch=24)
    pd.testing.assert_frame_equal(first.readings, repeat.readings)
    pd.testing.assert_frame_equal(first.labels, repeat.labels)

    extended = generate_burn_in_dataset(seed=101, n_batches=5, components_per_batch=24)
    original_batches = extended.readings["batch_id"].isin(first.readings["batch_id"].unique())
    pd.testing.assert_frame_equal(
        extended.readings.loc[original_batches].reset_index(drop=True),
        first.readings.reset_index(drop=True),
    )


def test_all_seven_scenarios_are_generated_and_labelled(dataset) -> None:
    assert set(dataset.labels["scenario"]) == set(SCENARIOS)

    flags = dataset.labels[["is_defect", "is_tester_fault", "is_healthy"]].astype(int)
    assert (flags.sum(axis=1) == 1).all(), "each component belongs to exactly one class"

    defects = set(dataset.labels.loc[dataset.labels["is_defect"], "scenario"])
    assert defects == set(DEFECT_SCENARIOS)
    faults = set(dataset.labels.loc[dataset.labels["is_tester_fault"], "scenario"])
    assert faults == set(FAULT_SCENARIOS)


def test_tester_faults_are_not_labelled_as_component_defects(dataset) -> None:
    faults = dataset.labels.loc[dataset.labels["scenario"] == "tester_fault"]
    assert len(faults) > 0
    assert not faults["is_defect"].any()
    assert not faults["is_healthy"].any()
    assert faults["anomaly_onset_hour"].notna().all()


def test_healthy_components_never_cross_the_approved_limit(dataset) -> None:
    healthy = dataset.labels.loc[dataset.labels["is_healthy"]]
    assert len(healthy) > 0
    assert healthy["first_exceedance_hour"].isna().all()


def test_measured_values_stay_physically_positive(dataset) -> None:
    assert (dataset.readings["measurement_value"] > 0).all()
    assert np.isfinite(dataset.readings["measurement_value"]).all()


def test_accelerating_drift_hides_from_a_fixed_limit_early(dataset) -> None:
    """The scenario that justifies the whole early-warning claim."""

    early = _readings_at(dataset, 24.0)
    accelerating = early.loc[early["scenario"] == "accelerating_drift"]
    assert len(accelerating) > 0
    fraction_of_limit = accelerating["measurement_value"] / accelerating["upper_limit"]
    assert fraction_of_limit.max() < 1.0, "a fixed limit would already have caught these"

    labels = dataset.labels.loc[dataset.labels["scenario"] == "accelerating_drift"]
    crossing_share = float(labels["first_exceedance_hour"].notna().mean())
    assert crossing_share >= 0.7, "most accelerating drifts must cross the limit eventually"
    assert (labels["first_exceedance_hour"].dropna() > 24.0).all()


def test_gradual_drift_crosses_later_than_it_becomes_abnormal(dataset) -> None:
    labels = dataset.labels.loc[dataset.labels["scenario"] == "gradual_drift"]
    assert len(labels) > 0
    assert (labels["anomaly_onset_hour"] == 0.0).all()
    crossings = labels["first_exceedance_hour"].dropna()
    assert len(crossings) > 0
    assert (crossings > 0.0).all()


def test_sudden_step_raises_the_level_at_its_onset_hour(dataset) -> None:
    steps = dataset.labels.loc[dataset.labels["scenario"] == "sudden_step"]
    assert len(steps) > 0
    readings = dataset.readings.set_index(["component_id", "hours"])["measurement_value"]
    for component_id, onset in zip(steps["component_id"], steps["anomaly_onset_hour"]):
        series = readings.loc[component_id]
        before = series.loc[series.index < onset]
        after = series.loc[series.index >= onset]
        assert after.min() > before.max(), f"{component_id} has no visible step at {onset}h"


def test_intermittent_components_return_towards_the_batch_level(dataset) -> None:
    intermittent = dataset.labels.loc[dataset.labels["scenario"] == "intermittent"]
    assert len(intermittent) > 0
    readings = dataset.readings.set_index(["component_id", "hours"])["measurement_value"]
    returns_to_normal = 0
    for component_id in intermittent["component_id"]:
        series = readings.loc[component_id]
        if series.iloc[-1] < 0.5 * series.max():
            returns_to_normal += 1
    assert returns_to_normal > 0, "an intermittent fault must be able to recover"


def test_batch_temperature_shifts_the_healthy_population() -> None:
    """A hotter chamber raises the healthy level, so a global limit is not enough."""

    dataset = generate_burn_in_dataset(
        seed=11, n_batches=8, components_per_batch=24, families=(DEFAULT_FAMILIES[0],)
    )
    first_readings = dataset.readings.loc[dataset.readings["hours"] == 0.0]
    merged = first_readings.merge(
        dataset.labels[["component_id", "is_healthy", "batch_temperature_c"]],
        on="component_id",
    )
    healthy = merged.loc[merged["is_healthy"]]
    per_batch = healthy.groupby("batch_id").agg(
        level=("measurement_value", "median"),
        temperature=("batch_temperature_c", "first"),
    )
    correlation = per_batch["level"].corr(per_batch["temperature"], method="spearman")
    assert correlation > 0.6
    assert per_batch["level"].max() / per_batch["level"].min() > 1.05
