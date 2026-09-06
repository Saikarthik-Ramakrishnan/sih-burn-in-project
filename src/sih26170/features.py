"""Leakage-safe feature engineering for early burn-in measurements."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .validation import validate_readings


GROUP_COLUMNS = [
    "component_id",
    "batch_id",
    "component_family",
    "measurement_name",
]
BATCH_COLUMNS = ["batch_id", "component_family", "measurement_name"]

MODEL_FEATURE_COLUMNS = [
    "percent_change",
    "delta_fraction_of_limit",
    "slope_fraction_per_hour",
    "acceleration_fraction_per_hour2",
    "variability_fraction_of_limit",
    "limit_fraction",
    "distance_fraction_to_upper_limit",
    "current_batch_robust_z",
    "slope_batch_robust_z",
]


def _safe_percent_change(initial: float, current: float) -> float:
    scale = max(abs(initial), 1e-9)
    return (current - initial) / scale


def _component_features(group: pd.DataFrame, as_of_hour: float) -> dict[str, object]:
    ordered = group.sort_values("hours")
    hours = ordered["hours"].to_numpy(dtype=float)
    values = ordered["measurement_value"].to_numpy(dtype=float)

    unique_time_count = len(np.unique(hours))
    slope = float(np.polyfit(hours, values, 1)[0]) if unique_time_count >= 2 else 0.0
    acceleration = 0.0
    if unique_time_count >= 3:
        early_dt = hours[1] - hours[0]
        late_dt = hours[-1] - hours[-2]
        if early_dt > 0 and late_dt > 0:
            early_slope = (values[1] - values[0]) / early_dt
            late_slope = (values[-1] - values[-2]) / late_dt
            acceleration = float((late_slope - early_slope) / (hours[-1] - hours[0]))

    initial = float(values[0])
    current = float(values[-1])
    upper_limit = float(ordered["upper_limit"].iloc[-1])
    result: dict[str, object] = {
        **{column: ordered[column].iloc[-1] for column in GROUP_COLUMNS},
        "as_of_hour": float(as_of_hour),
        "last_observed_hour": float(hours[-1]),
        "n_observations": int(len(ordered)),
        "initial_value": initial,
        "current_value": current,
        "delta": current - initial,
        "percent_change": _safe_percent_change(initial, current),
        "slope": slope,
        "acceleration": acceleration,
        "variability": float(np.std(values, ddof=0)),
        "upper_limit": upper_limit,
        "delta_fraction_of_limit": (current - initial) / upper_limit,
        "slope_fraction_per_hour": slope / upper_limit,
        "acceleration_fraction_per_hour2": acceleration / upper_limit,
        "variability_fraction_of_limit": float(np.std(values, ddof=0)) / upper_limit,
        "limit_fraction": current / upper_limit,
        "distance_to_upper_limit": upper_limit - current,
        "distance_fraction_to_upper_limit": (upper_limit - current) / upper_limit,
    }
    for optional in ("temperature_c", "humidity_pct", "test_condition", "data_source"):
        result[optional] = ordered[optional].iloc[-1] if optional in ordered else None
    return result


def _add_robust_z(
    df: pd.DataFrame, value_column: str, output_column: str
) -> pd.DataFrame:
    scored = df.copy()
    grouped_values = scored.groupby(BATCH_COLUMNS, dropna=False)[value_column]
    medians = grouped_values.transform("median").astype(float)
    absolute_deviation = (scored[value_column].astype(float) - medians).abs()
    median_deviation = absolute_deviation.groupby(
        [scored[column] for column in BATCH_COLUMNS], dropna=False
    ).transform("median")
    standard_deviation = grouped_values.transform("std").fillna(0.0).astype(float)
    scale = np.maximum.reduce(
        [
            median_deviation.to_numpy(dtype=float),
            medians.abs().to_numpy(dtype=float) * 0.01,
            standard_deviation.to_numpy(dtype=float) * 0.1,
            np.full(len(scored), 1e-9),
        ]
    )
    scored[output_column] = (
        0.6745 * (scored[value_column].astype(float) - medians) / scale
    )
    return scored


def build_component_features(
    readings: pd.DataFrame,
    *,
    as_of_hour: float,
    minimum_observations: int = 2,
) -> pd.DataFrame:
    """Build one early-warning feature row per component and measurement.

    Rows after `as_of_hour` are discarded before any calculation. This is the
    central leakage guard for the early-warning claim.
    """

    validate_readings(readings)
    if as_of_hour < 0:
        raise ValueError("as_of_hour cannot be negative")
    if minimum_observations < 1:
        raise ValueError("minimum_observations must be at least one")

    early = readings.loc[readings["hours"].astype(float) <= as_of_hour].copy()
    if early.empty:
        raise ValueError("no observations exist at or before as_of_hour")

    rows = [
        _component_features(group, as_of_hour)
        for _, group in early.groupby(GROUP_COLUMNS, sort=False, dropna=False)
        if len(group) >= minimum_observations
    ]
    if not rows:
        raise ValueError(
            "no component has the minimum number of early observations"
        )

    features = pd.DataFrame(rows).reset_index(drop=True)
    features = _add_robust_z(
        features, "current_value", "current_batch_robust_z"
    )
    features = _add_robust_z(features, "slope", "slope_batch_robust_z")
    return features
