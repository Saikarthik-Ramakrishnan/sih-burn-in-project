"""Validation for long-format burn-in readings."""

from __future__ import annotations

import pandas as pd


REQUIRED_COLUMNS = {
    "component_id",
    "batch_id",
    "component_family",
    "hours",
    "measurement_name",
    "measurement_value",
    "upper_limit",
}

IDENTITY_COLUMNS = [
    "component_id",
    "batch_id",
    "component_family",
    "hours",
    "measurement_name",
]


class DataValidationError(ValueError):
    """Raised when input data cannot safely enter the feature pipeline."""


def validate_readings(df: pd.DataFrame) -> None:
    """Return ``None`` when valid; otherwise list all detected problems."""

    problems: list[str] = []
    missing_columns = sorted(REQUIRED_COLUMNS.difference(df.columns))
    if missing_columns:
        problems.append(f"missing required columns: {', '.join(missing_columns)}")
        raise DataValidationError("; ".join(problems))

    if df.empty:
        problems.append("dataset is empty")

    null_columns = sorted(
        column for column in REQUIRED_COLUMNS if df[column].isna().any()
    )
    if null_columns:
        problems.append(f"null values in required columns: {', '.join(null_columns)}")

    for column in ("hours", "measurement_value", "upper_limit"):
        converted = pd.to_numeric(df[column], errors="coerce")
        if converted.isna().any():
            problems.append(f"{column} must contain only numeric values")

    hours = pd.to_numeric(df["hours"], errors="coerce")
    if (hours.dropna() < 0).any():
        problems.append("hours cannot be negative")

    upper_limits = pd.to_numeric(df["upper_limit"], errors="coerce")
    if (upper_limits.dropna() <= 0).any():
        problems.append("upper_limit must be positive")

    if "lower_limit" in df.columns:
        lower_limits = pd.to_numeric(df["lower_limit"], errors="coerce")
        invalid_limits = lower_limits.notna() & upper_limits.notna() & (
            lower_limits >= upper_limits
        )
        if invalid_limits.any():
            problems.append("lower_limit must be smaller than upper_limit")

    duplicate_count = int(df.duplicated(IDENTITY_COLUMNS, keep=False).sum())
    if duplicate_count:
        problems.append(
            f"{duplicate_count} rows duplicate the same component/time/measurement identity"
        )

    limit_groups = ["component_id", "measurement_name"]
    inconsistent_limits = (
        df.groupby(limit_groups, dropna=False)["upper_limit"].nunique(dropna=False) > 1
    )
    if inconsistent_limits.any():
        problems.append("upper_limit changes within a component measurement history")

    if problems:
        raise DataValidationError("; ".join(problems))
