"""Shared fixtures for backend tests.

Test fixtures live here and are built in memory. They are deliberately kept
separate from anything under ``artifacts/`` so a test double can never be
mistaken for a runtime asset.
"""

from __future__ import annotations

import io
import csv
from typing import Any, Iterable, Sequence

import pytest

DEFAULT_COLUMNS: tuple[str, ...] = (
    "component_id",
    "batch_id",
    "component_family",
    "hours",
    "measurement_name",
    "measurement_value",
    "upper_limit",
)


def make_csv(rows: Sequence[dict[str, Any]], columns: Iterable[str] | None = None) -> bytes:
    """Serialise dict rows to CSV bytes, preserving text exactly as given."""
    if columns is None:
        seen: list[str] = []
        for row in rows:
            for key in row:
                if key not in seen:
                    seen.append(key)
        columns = seen or list(DEFAULT_COLUMNS)
    columns = list(columns)

    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({c: row.get(c, "") for c in columns})
    return buffer.getvalue().encode("utf-8")


def burn_in_rows(
    *,
    n_components: int = 12,
    batch_id: str = "B-001",
    family: str = "Digital IC",
    measurement: str = "leakage_ua",
    upper_limit: float = 10.0,
    hours: Sequence[float] = (0.0, 24.0),
    id_prefix: str = "C",
    id_width: int = 4,
    drift_per_component: float = 0.01,
    base_value: float = 1.0,
    extra: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Deterministic long-format rows. No randomness, so tests are stable."""
    rows: list[dict[str, Any]] = []
    for index in range(n_components):
        component_id = f"{id_prefix}{index:0{id_width}d}"
        for hour in hours:
            value = base_value + drift_per_component * index * (hour / 24.0)
            row: dict[str, Any] = {
                "component_id": component_id,
                "batch_id": batch_id,
                "component_family": family,
                "hours": hour,
                "measurement_name": measurement,
                "measurement_value": round(value, 6),
                "upper_limit": upper_limit,
            }
            if extra:
                row.update(extra)
            rows.append(row)
    return rows


@pytest.fixture
def valid_csv_bytes() -> bytes:
    return make_csv(burn_in_rows())


@pytest.fixture
def valid_rows() -> list[dict[str, Any]]:
    return burn_in_rows()
