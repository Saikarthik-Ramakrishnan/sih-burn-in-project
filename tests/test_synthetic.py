from __future__ import annotations

import pandas as pd

from sih26170 import generate_burn_in_dataset, validate_readings
from sih26170.synthetic import SCENARIOS, arrhenius_acceleration


def test_generator_is_reproducible_and_contract_safe() -> None:
    first = generate_burn_in_dataset(seed=7, n_batches=4, components_per_batch=40)
    second = generate_burn_in_dataset(seed=7, n_batches=4, components_per_batch=40)

    pd.testing.assert_frame_equal(first.readings, second.readings)
    pd.testing.assert_frame_equal(first.labels, second.labels)
    validate_readings(first.readings)
    assert len(first.readings) == 4 * 40 * len(first.hours)
    assert len(first.labels) == 4 * 40
    assert "scenario" not in first.readings
    assert first.readings["is_synthetic"].all()
    assert set(first.labels["scenario"]) == set(SCENARIOS)


def test_temperature_acceleration_is_monotonic() -> None:
    assert arrhenius_acceleration(130.0) > arrhenius_acceleration(125.0)
    assert arrhenius_acceleration(125.0) > arrhenius_acceleration(120.0)

