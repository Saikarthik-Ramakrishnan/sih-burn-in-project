from __future__ import annotations

import hashlib
import json

import numpy as np
import pandas as pd
import pytest

from sih26170.mlcc_synthetic import HOURS, export_mlcc_dataset, generate_mlcc_dataset
from sih26170.validation import validate_readings


@pytest.fixture(scope="module")
def mlcc_data():
    return generate_mlcc_dataset(seed=26170, n_batches=20, components_per_batch=32)


def test_generation_is_repeatable(mlcc_data):
    other = generate_mlcc_dataset(seed=26170, n_batches=20, components_per_batch=32)
    pd.testing.assert_frame_equal(mlcc_data.readings, other.readings)
    pd.testing.assert_frame_equal(mlcc_data.labels, other.labels)
    pd.testing.assert_frame_equal(mlcc_data.batch_splits, other.batch_splits)


def test_input_validity_and_derived_resistance(mlcc_data):
    readings = mlcc_data.readings
    validate_readings(readings)
    assert len(readings) == 20 * 32 * len(HOURS)
    assert readings.is_synthetic.all()
    assert set(readings.data_source) == {"synthetic"}
    assert set(readings.component_family) == {"MLCC_X7R"}
    numeric = readings.select_dtypes(include="number")
    assert np.isfinite(numeric.to_numpy()).all()
    for column in ("measurement_value", "insulation_resistance_gohm", "capacitance_nf", "dissipation_factor_pct"):
        assert (readings[column] > 0).all()
    np.testing.assert_allclose(
        readings.insulation_resistance_gohm,
        readings.measurement_voltage_v / (readings.measurement_value * 1000),
    )
    assert readings.groupby("batch_id").profile_id.nunique().eq(1).all()
    assert readings.groupby("component_id").hours.agg(tuple).map(lambda value: value == HOURS).all()
    assert not {"scenario", "is_defect", "final_value", "true_final_value", "is_future_failure"}.intersection(readings.columns)


def test_whole_batch_splits_are_stratified_and_disjoint(mlcc_data):
    splits = mlcc_data.batch_splits
    assert splits.batch_id.is_unique
    assert splits.split.value_counts().to_dict() == {"train": 12, "test": 4, "calibration": 4}
    counts = splits.groupby(["profile_id", "split"]).size().unstack()
    assert counts["train"].eq(3).all()
    assert counts["calibration"].eq(1).all()
    assert counts["test"].eq(1).all()
    joined = mlcc_data.readings.merge(splits[["batch_id", "split"]], on="batch_id", validate="many_to_one")
    assert joined.groupby("component_id").split.nunique().eq(1).all()


def test_labels_distinguish_observed_outcome_from_latent_component_state(mlcc_data):
    labels = mlcc_data.labels
    final = mlcc_data.readings[mlcc_data.readings.hours == 168].set_index("component_id")
    np.testing.assert_allclose(labels.final_value, final.loc[labels.component_id, "measurement_value"])
    assert labels.is_future_failure.eq(labels.true_final_value > labels.upper_limit).all()
    assert labels.is_observed_final_exceedance.eq(labels.final_value > labels.upper_limit).all()
    faulty = labels[labels.is_tester_fault & ~labels.is_defect]
    assert len(faulty) > 0
    assert (~faulty.is_future_failure).all()
    assert (faulty.final_value > faulty.true_final_value).all()
    assert (labels.is_defect & ~labels.is_future_failure).any()


def test_late_shocks_and_nonmonotonic_behavior_exist(mlcc_data):
    labels = mlcc_data.labels
    assert labels[labels.component_scenario == "late_abrupt_onset"].anomaly_onset_hour.gt(24).all()
    healthy_ids = labels.loc[labels.component_scenario == "healthy_settling", "component_id"]
    healthy = mlcc_data.readings[mlcc_data.readings.component_id.isin(healthy_ids)]
    assert healthy.groupby("component_id").measurement_value.diff().lt(0).any()


def test_export_is_early_only_with_checksums_and_unselected_demo(tmp_path, mlcc_data):
    manifest = export_mlcc_dataset(mlcc_data, tmp_path, include_stress=False)
    for split in ("train", "calibration", "test"):
        early = pd.read_csv(tmp_path / f"{split}_early.csv")
        assert set(early.hours) == {0, 24}
        assert early.groupby("component_id").size().eq(2).all()
        assert "final_value" not in early
    assert manifest["physical_validation"] is False
    for name, item in manifest["files"].items():
        assert hashlib.sha256((tmp_path / name).read_bytes()).hexdigest() == item["sha256"]
    loaded = json.loads((tmp_path / "generation_manifest.json").read_text())
    assert loaded["seed"] == 26170
    demo = pd.read_csv(tmp_path / "demo_early.csv")
    heldout = pd.read_csv(tmp_path / "test_early.csv")
    assert set(demo.component_id).issubset(set(heldout.component_id))
    assert demo.groupby("batch_id").component_id.nunique().eq(32).all()
    outcomes = pd.read_csv(tmp_path / "demo_outcomes.csv")
    assert outcomes.hours.gt(24).all()
    assert set(demo.component_id) == set(outcomes.component_id)


def test_stress_condition_and_identity_separation(mlcc_data):
    shifted = generate_mlcc_dataset(
        seed=42, n_batches=20, components_per_batch=8,
        condition="unseen_condition", identity_prefix="SHIFT",
    )
    assert shifted.readings.measurement_temperature_c.min() > mlcc_data.readings.measurement_temperature_c.max()
    assert not set(shifted.labels.component_id).intersection(mlcc_data.labels.component_id)


@pytest.mark.parametrize("kwargs", [
    {"n_batches": 10}, {"components_per_batch": 1}, {"defect_prevalence": -1},
    {"tester_fault_batch_rate": 2}, {"condition": "unrecognised"},
])
def test_invalid_configuration_rejected(kwargs):
    with pytest.raises(ValueError):
        generate_mlcc_dataset(**kwargs)
