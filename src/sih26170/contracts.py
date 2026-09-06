"""Shared result contracts used by the model and dashboard modules."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class AnomalyResult:
    component_id: str
    batch_id: str
    component_family: str
    measurement_name: str
    as_of_hour: float
    current_value: float
    safety_limit: float
    anomaly_score: float
    is_anomaly: bool
    robust_deviation_score: float
    model_anomaly_score: float
    reason_codes: list[str] = field(default_factory=list)
    data_quality_warning: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PredictionResult:
    """Contract for the separate future-value prediction module."""

    predicted_final_value: float
    prediction_lower: float
    prediction_upper: float
    target_hour: float = 168.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

