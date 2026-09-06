"""Transparent and machine-learning anomaly detectors."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler

from .contracts import AnomalyResult
from .features import MODEL_FEATURE_COLUMNS


IDENTIFIER_COLUMNS = [
    "component_id",
    "batch_id",
    "component_family",
    "measurement_name",
]


def _logistic_risk(raw_score: float, threshold: float) -> float:
    return float(1.0 / (1.0 + math.exp(-(raw_score - threshold))))


def apply_robust_baseline(
    features: pd.DataFrame, *, threshold: float = 3.5
) -> pd.DataFrame:
    """Flag components whose current value or drift is far from batch peers."""

    required = {"current_batch_robust_z", "slope_batch_robust_z"}
    missing = required.difference(features.columns)
    if missing:
        raise ValueError(f"missing robust feature columns: {', '.join(sorted(missing))}")

    result = features.copy()
    result["robust_deviation_score"] = result[
        ["current_batch_robust_z", "slope_batch_robust_z"]
    ].abs().max(axis=1)
    result["robust_anomaly_score"] = result["robust_deviation_score"].map(
        lambda value: _logistic_risk(float(value), threshold)
    )
    result["is_robust_anomaly"] = result["robust_deviation_score"] >= threshold
    return result


def _reason_codes(row: pd.Series) -> list[str]:
    reasons: list[str] = []
    if abs(float(row["current_batch_robust_z"])) >= 3.5:
        direction = "above" if row["current_batch_robust_z"] > 0 else "below"
        reasons.append(f"Current value is unusually {direction} the batch norm")
    if abs(float(row["slope_batch_robust_z"])) >= 3.5:
        direction = "faster" if row["slope_batch_robust_z"] > 0 else "slower"
        reasons.append(f"Drift is unusually {direction} than comparable components")
    if float(row["limit_fraction"]) >= 0.8:
        reasons.append("Current value has used at least 80% of the safety limit")
    if float(row["acceleration"]) > 0:
        reasons.append("The rate of change is accelerating")
    if not reasons and bool(row["is_anomaly"]):
        reasons.append("The combination of early measurements is unusual")
    return reasons


class BatchAwareAnomalyDetector:
    """Isolation Forest combined with a human-auditable robust baseline."""

    def __init__(
        self,
        *,
        contamination: float = 0.1,
        robust_threshold: float = 3.5,
        random_state: int = 42,
    ) -> None:
        if not 0 < contamination < 0.5:
            raise ValueError("contamination must be between 0 and 0.5")
        self.contamination = contamination
        self.robust_threshold = robust_threshold
        self.pipeline = Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", RobustScaler()),
                (
                    "model",
                    IsolationForest(
                        n_estimators=250,
                        contamination=contamination,
                        random_state=random_state,
                    ),
                ),
            ]
        )
        self._training_strengths: np.ndarray | None = None

    def _matrix(self, features: pd.DataFrame) -> pd.DataFrame:
        missing = set(MODEL_FEATURE_COLUMNS).difference(features.columns)
        if missing:
            raise ValueError(f"missing model features: {', '.join(sorted(missing))}")
        return features[MODEL_FEATURE_COLUMNS].replace([np.inf, -np.inf], np.nan)

    def fit(self, reference_features: pd.DataFrame) -> "BatchAwareAnomalyDetector":
        if len(reference_features) < 8:
            raise ValueError("at least eight reference components are required")
        matrix = self._matrix(reference_features)
        self.pipeline.fit(matrix)
        strengths = -self.pipeline.decision_function(matrix)
        self._training_strengths = np.sort(np.asarray(strengths, dtype=float))
        return self

    def _percentile_scores(self, strengths: np.ndarray) -> np.ndarray:
        if self._training_strengths is None:
            raise RuntimeError("fit must be called before score")
        positions = np.searchsorted(
            self._training_strengths, strengths, side="right"
        )
        percentiles = positions / len(self._training_strengths)
        cutoff = 1.0 - self.contamination
        width = max(self.contamination / 3.0, 0.01)
        return 1.0 / (1.0 + np.exp(-(percentiles - cutoff) / width))

    def score(self, features: pd.DataFrame) -> pd.DataFrame:
        if self._training_strengths is None:
            raise RuntimeError("fit must be called before score")

        scored = apply_robust_baseline(
            features, threshold=self.robust_threshold
        )
        matrix = self._matrix(scored)
        model_labels = self.pipeline.predict(matrix)
        model_strengths = -self.pipeline.decision_function(matrix)
        scored["model_anomaly_score"] = self._percentile_scores(model_strengths)
        scored["is_model_anomaly"] = model_labels == -1
        scored["anomaly_score"] = scored[
            ["robust_anomaly_score", "model_anomaly_score"]
        ].max(axis=1)
        scored["is_anomaly"] = (
            scored["is_robust_anomaly"] | scored["is_model_anomaly"]
        )
        scored["reason_codes"] = scored.apply(_reason_codes, axis=1)
        return scored

    def fit_score(self, features: pd.DataFrame) -> pd.DataFrame:
        return self.fit(features).score(features)

    @staticmethod
    def to_results(scored: pd.DataFrame) -> list[AnomalyResult]:
        results: list[AnomalyResult] = []
        for _, row in scored.iterrows():
            results.append(
                AnomalyResult(
                    component_id=str(row["component_id"]),
                    batch_id=str(row["batch_id"]),
                    component_family=str(row["component_family"]),
                    measurement_name=str(row["measurement_name"]),
                    as_of_hour=float(row["as_of_hour"]),
                    current_value=float(row["current_value"]),
                    safety_limit=float(row["upper_limit"]),
                    anomaly_score=float(row["anomaly_score"]),
                    is_anomaly=bool(row["is_anomaly"]),
                    robust_deviation_score=float(row["robust_deviation_score"]),
                    model_anomaly_score=float(row["model_anomaly_score"]),
                    reason_codes=list(row["reason_codes"]),
                )
            )
        return results
