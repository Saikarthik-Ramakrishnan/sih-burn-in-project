from __future__ import annotations

import pandas as pd
import pytest

from sih26170 import DataValidationError, validate_readings


def test_valid_dataset_passes(demo_readings: pd.DataFrame) -> None:
    validate_readings(demo_readings)


def test_duplicate_identity_is_rejected(demo_readings: pd.DataFrame) -> None:
    duplicated = pd.concat([demo_readings, demo_readings.iloc[[0]]], ignore_index=True)

    with pytest.raises(DataValidationError, match="duplicate"):
        validate_readings(duplicated)


def test_missing_required_column_is_rejected(demo_readings: pd.DataFrame) -> None:
    with pytest.raises(DataValidationError, match="measurement_name"):
        validate_readings(demo_readings.drop(columns="measurement_name"))

