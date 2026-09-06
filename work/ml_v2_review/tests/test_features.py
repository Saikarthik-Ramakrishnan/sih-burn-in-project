from __future__ import annotations

import pandas as pd
import pytest

from sih26170 import MODEL_FEATURE_COLUMNS, build_component_features


def test_features_never_use_rows_after_as_of_hour(demo_readings: pd.DataFrame) -> None:
    features = build_component_features(demo_readings, as_of_hour=24)
    suspicious = features.loc[features["component_id"] == "C012"].iloc[0]

    assert len(features) == 12
    assert suspicious["current_value"] == 40.0
    assert suspicious["slope"] == pytest.approx(25.0 / 24.0)
    assert suspicious["n_observations"] == 2
    assert suspicious["current_batch_robust_z"] > 3.5


def test_minimum_observation_rule_is_enforced(demo_readings: pd.DataFrame) -> None:
    with pytest.raises(ValueError, match="minimum number"):
        build_component_features(
            demo_readings.loc[demo_readings["hours"] == 0],
            as_of_hour=24,
            minimum_observations=2,
        )


def test_isolation_forest_features_are_unit_normalized() -> None:
    raw_unit_columns = {
        "current_value",
        "delta",
        "slope",
        "acceleration",
        "variability",
        "distance_to_upper_limit",
    }
    label_columns = {
        "scenario",
        "is_defect",
        "is_tester_fault",
        "anomaly_onset_hour",
        "first_exceedance_hour",
    }

    assert raw_unit_columns.isdisjoint(MODEL_FEATURE_COLUMNS)
    assert label_columns.isdisjoint(MODEL_FEATURE_COLUMNS)
