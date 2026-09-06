from __future__ import annotations

import pandas as pd
import pytest


@pytest.fixture
def demo_readings() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    starts = [9.8, 10.1, 9.9, 10.2, 10.0, 9.7, 10.3, 9.9, 10.1, 10.0, 9.8, 15.0]
    ends = [10.4, 10.8, 10.3, 10.9, 10.5, 10.2, 10.9, 10.4, 10.7, 10.5, 10.3, 40.0]
    for index, (start, end) in enumerate(zip(starts, ends), start=1):
        final = end + 1.0 if index < 12 else 60.0
        for hour, value in ((0, start), (24, end), (168, final)):
            rows.append(
                {
                    "component_id": f"C{index:03d}",
                    "batch_id": "B01",
                    "component_family": "Digital IC",
                    "hours": hour,
                    "measurement_name": "leakage_ua",
                    "measurement_value": value,
                    "upper_limit": 50.0,
                    "temperature_c": 125.0,
                    "data_source": "synthetic",
                }
            )
    return pd.DataFrame(rows)

