"""Risk-sensitive decision rules shared by model and UI modules."""

from __future__ import annotations

from typing import Any

from .contracts import AnomalyResult, PredictionResult


def recommend_action(
    anomaly: AnomalyResult,
    prediction: PredictionResult | None = None,
) -> tuple[str, list[str]]:
    """Return a recommendation and supporting reasons.

    The output is decision support, not an automatic certification decision.
    """

    reasons = list(anomaly.reason_codes)
    if anomaly.data_quality_warning:
        reasons.append(anomaly.data_quality_warning)
        return "RETEST", reasons

    if anomaly.current_value >= anomaly.safety_limit:
        reasons.append("The current measurement has crossed the approved limit")
        return "ENGINEER_REVIEW", reasons

    predicted_crossing = False
    confidently_crossing = False
    if prediction is not None:
        predicted_crossing = prediction.predicted_final_value >= anomaly.safety_limit
        confidently_crossing = prediction.prediction_lower >= anomaly.safety_limit
        if predicted_crossing:
            reasons.append("The predicted final value crosses the approved limit")
        if prediction.prediction_upper >= anomaly.safety_limit:
            reasons.append("The prediction range includes a possible limit crossing")

    if anomaly.is_anomaly and (predicted_crossing or confidently_crossing):
        return "ENGINEER_REVIEW", reasons
    if anomaly.anomaly_score >= 0.8 or predicted_crossing:
        return "RETEST", reasons
    if anomaly.is_anomaly or (
        prediction is not None and prediction.prediction_upper >= anomaly.safety_limit
    ):
        return "MONITOR", reasons
    return "ACCEPT", reasons


def build_screening_record(
    anomaly: AnomalyResult,
    prediction: PredictionResult | None = None,
) -> dict[str, Any]:
    """Build the single dictionary consumed by the dashboard/API layer."""

    action, reasons = recommend_action(anomaly, prediction)
    record = anomaly.to_dict()
    record.update(
        {
            "recommendation": action,
            "recommendation_reasons": reasons,
            "predicted_final_value": None,
            "prediction_lower": None,
            "prediction_upper": None,
            "target_hour": None,
        }
    )
    if prediction is not None:
        record.update(prediction.to_dict())
    return record
