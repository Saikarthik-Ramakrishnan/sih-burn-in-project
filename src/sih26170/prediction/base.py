"""Adapter interfaces for the anomaly detector and the 168 h forecaster.

The API depends on these protocols, never on a concrete model class. That lets
the frontend contract and the API tests stabilise before any artifact exists,
and lets a real MLCC-specific artifact be swapped in later without touching a
single response field.

Two rules are enforced by the surrounding code, not by politeness:

  * Adapters are constructed at startup from a trusted local artifact and are
    read-only afterwards. Nothing in a scoring request may call ``fit``.
  * A missing model produces an explicit unavailable capability. Production
    never substitutes a fake prediction. Test doubles exist only in tests.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

import pandas as pd


@dataclass(frozen=True)
class FeatureAttribution:
    """One feature's contribution to a model output.

    This explains model behaviour. It does not establish a physical cause.
    """

    feature: str
    contribution: float

    @property
    def direction(self) -> str:
        return "increases" if self.contribution >= 0 else "decreases"


@dataclass(frozen=True)
class ForecastOutput:
    """One component/measurement forecast, keyed by its full identity.

    ``lower``/``upper`` are null unless the artifact carries a calibrated
    interval. An uncalibrated model returns a point estimate with null bounds
    rather than an invented range.
    """

    component_id: str
    batch_id: str
    component_family: str
    measurement_name: str
    predicted_final_value: float
    target_hour: float
    lower: float | None = None
    upper: float | None = None
    interval_nominal_coverage: float | None = None
    interval_method: str | None = None
    attributions: tuple[FeatureAttribution, ...] = ()

    @property
    def identity(self) -> tuple[str, str, str, str]:
        return (
            self.component_id,
            self.batch_id,
            self.component_family,
            self.measurement_name,
        )


@dataclass(frozen=True)
class AnomalyOutput:
    """One component/measurement anomaly result, keyed by its full identity.

    ``score`` is a relative deviation score produced by the fitted detector.
    It is not a probability of physical failure and must never be presented
    as a confidence level.
    """

    component_id: str
    batch_id: str
    component_family: str
    measurement_name: str
    score: float
    is_anomaly: bool
    method: str
    attributions: tuple[FeatureAttribution, ...] = ()
    raw: Any = field(
        default=None,
        repr=False,
        compare=False,
        metadata={
            "note": (
                "The core AnomalyResult this output was derived from, carried "
                "through unchanged so build_screening_record() receives the "
                "object the core decision logic expects."
            )
        },
    )

    @property
    def identity(self) -> tuple[str, str, str, str]:
        return (
            self.component_id,
            self.batch_id,
            self.component_family,
            self.measurement_name,
        )


@runtime_checkable
class AnomalyAdapter(Protocol):
    """Wraps an ALREADY FITTED detector. Scoring never fits."""

    model_version: str
    method: str

    def score(self, features: pd.DataFrame) -> list[AnomalyOutput]:
        ...


@runtime_checkable
class ForecastAdapter(Protocol):
    """Predicts the measurement at ``target_hour`` from early-window features."""

    model_version: str
    target_hour: float
    supports_intervals: bool
    supports_explanations: bool

    def supports_profile(self, profile_id: str) -> bool:
        ...

    def predict(self, features: pd.DataFrame) -> list[ForecastOutput]:
        ...


@dataclass
class CapabilityState:
    """Whether a capability loaded, and exactly why not when it did not."""

    name: str
    available: bool
    reason: str | None = None
    artifact_id: str | None = None
    model_version: str | None = None
    checks: list[tuple[str, bool, str | None]] = field(default_factory=list)

    def add_check(self, name: str, passed: bool, detail: str | None = None) -> None:
        self.checks.append((name, passed, detail))
