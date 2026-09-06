"""Test doubles for the core modules and the model adapters.

These exist ONLY for tests. The production path loads adapters from verified
artifacts in ``ModelRegistry.load()``; there is no code path in the service that
falls back to anything in this file.

The core stand-ins here are deliberately minimal: they mimic the *shape* of the
pinned core interface so the API path can be exercised, and nothing more. They
are not a reimplementation of the anomaly algorithm and must never be treated
as one.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from sih26170.api.ingestion import HISTORY_KEY
from sih26170.prediction.base import (
    AnomalyOutput,
    FeatureAttribution,
    ForecastOutput,
)

IDENTITY_COLUMNS = list(HISTORY_KEY)


# --------------------------------------------------------------------------
# Core stand-ins
# --------------------------------------------------------------------------


def fake_build_component_features(early_readings: pd.DataFrame, *, as_of_hour: float) -> pd.DataFrame:
    """Shape-compatible stand-in for the shared feature builder.

    Emits one row per history with the identity columns preserved, which is
    what the API needs in order to join results back by full identity.
    """
    rows: list[dict] = []
    for key, block in early_readings.groupby(IDENTITY_COLUMNS, sort=False):
        block = block.sort_values("hours")
        at_zero = block.loc[block["hours"] == 0.0, "measurement_value"]
        at_cut = block.loc[block["hours"] == as_of_hour, "measurement_value"]
        if at_zero.empty or at_cut.empty:
            continue  # the core may omit histories with too few early readings
        v0 = float(at_zero.iloc[0])
        v1 = float(at_cut.iloc[0])
        rows.append(
            {
                **dict(zip(IDENTITY_COLUMNS, (str(k) for k in key))),
                "initial_value": v0,
                "delta": v1 - v0,
                "slope": (v1 - v0) / as_of_hour if as_of_hour else 0.0,
            }
        )
    return pd.DataFrame(rows, columns=IDENTITY_COLUMNS + ["initial_value", "delta", "slope"])


@dataclass
class FakePredictionResult:
    predicted_final_value: float
    prediction_lower: float | None
    prediction_upper: float | None
    target_hour: float


def fake_make_prediction_result(
    *,
    predicted_final_value: float,
    prediction_lower: float | None,
    prediction_upper: float | None,
    target_hour: float,
) -> FakePredictionResult:
    return FakePredictionResult(
        predicted_final_value=predicted_final_value,
        prediction_lower=prediction_lower,
        prediction_upper=prediction_upper,
        target_hour=target_hour,
    )


@dataclass
class FakeScreeningRecord:
    recommendation: str


def fake_build_screening_record(anomaly, prediction) -> FakeScreeningRecord:
    """Stand-in for core decision logic.

    Mirrors the four documented outcomes without claiming to be the real
    thresholds: a flagged part whose prediction crosses the limit escalates.
    """
    is_anomaly = getattr(anomaly, "is_anomaly", False)
    if is_anomaly:
        return FakeScreeningRecord("ENGINEER_REVIEW")
    return FakeScreeningRecord("ACCEPT")


# --------------------------------------------------------------------------
# Adapter doubles
# --------------------------------------------------------------------------


class RecordingAnomalyAdapter:
    """Scores deterministically and refuses to be fitted."""

    model_version = "test-anomaly-0.0.0"
    method = "median_mad+isolation_forest"

    def __init__(self, anomaly_threshold: float = 0.5) -> None:
        self.anomaly_threshold = anomaly_threshold
        self.score_calls = 0
        self.fit_calls = 0

    def fit(self, *args, **kwargs):  # pragma: no cover - must never run
        self.fit_calls += 1
        raise AssertionError("The scoring path must never fit a model.")

    def score(self, features: pd.DataFrame) -> list[AnomalyOutput]:
        self.score_calls += 1
        outputs: list[AnomalyOutput] = []
        for row in features.itertuples():
            slope = float(getattr(row, "slope", 0.0))
            score = slope * 10.0
            outputs.append(
                AnomalyOutput(
                    component_id=str(row.component_id),
                    batch_id=str(row.batch_id),
                    component_family=str(row.component_family),
                    measurement_name=str(row.measurement_name),
                    score=score,
                    is_anomaly=score >= self.anomaly_threshold,
                    method=self.method,
                    attributions=(FeatureAttribution("slope", slope),),
                    raw=_RawAnomaly(score >= self.anomaly_threshold, score),
                )
            )
        return outputs


@dataclass
class _RawAnomaly:
    is_anomaly: bool
    score: float


class RecordingForecastAdapter:
    """Predicts the 168 h value linearly from the early slope."""

    model_version = "test-forecast-0.0.0"
    target_hour = 168.0

    def __init__(
        self,
        *,
        profiles: frozenset[str] = frozenset({"digital_ic_leakage_ua"}),
        with_intervals: bool = True,
    ) -> None:
        self._profiles = profiles
        self.supports_intervals = with_intervals
        self.supports_explanations = True
        self.predict_calls = 0
        self.fit_calls = 0

    def fit(self, *args, **kwargs):  # pragma: no cover - must never run
        self.fit_calls += 1
        raise AssertionError("The scoring path must never fit a model.")

    def supports_profile(self, profile_id: str) -> bool:
        return profile_id in self._profiles

    def predict(self, features: pd.DataFrame) -> list[ForecastOutput]:
        self.predict_calls += 1
        outputs: list[ForecastOutput] = []
        for row in features.itertuples():
            initial = float(getattr(row, "initial_value", 0.0))
            slope = float(getattr(row, "slope", 0.0))
            point = initial + slope * self.target_hour
            half_width = 0.25 if self.supports_intervals else None
            outputs.append(
                ForecastOutput(
                    component_id=str(row.component_id),
                    batch_id=str(row.batch_id),
                    component_family=str(row.component_family),
                    measurement_name=str(row.measurement_name),
                    predicted_final_value=point,
                    target_hour=self.target_hour,
                    lower=(point - half_width) if half_width is not None else None,
                    upper=(point + half_width) if half_width is not None else None,
                    interval_nominal_coverage=0.9 if half_width is not None else None,
                    interval_method="split_conformal" if half_width is not None else None,
                    attributions=(
                        FeatureAttribution("slope", slope),
                        FeatureAttribution("initial_value", initial),
                    ),
                )
            )
        return outputs
