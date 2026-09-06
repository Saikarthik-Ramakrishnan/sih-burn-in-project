from __future__ import annotations

from sih26170 import (
    AnomalyResult,
    PredictionResult,
    build_screening_record,
    recommend_action,
)


def anomaly_result(**overrides: object) -> AnomalyResult:
    values: dict[str, object] = {
        "component_id": "C012",
        "batch_id": "B01",
        "component_family": "Digital IC",
        "measurement_name": "leakage_ua",
        "as_of_hour": 24.0,
        "current_value": 40.0,
        "safety_limit": 50.0,
        "anomaly_score": 0.95,
        "is_anomaly": True,
        "robust_deviation_score": 12.0,
        "model_anomaly_score": 0.9,
        "reason_codes": ["Unusually high drift"],
    }
    values.update(overrides)
    return AnomalyResult(**values)  # type: ignore[arg-type]


def test_anomaly_plus_predicted_crossing_requires_engineer_review() -> None:
    prediction = PredictionResult(
        predicted_final_value=56.0,
        prediction_lower=49.0,
        prediction_upper=63.0,
    )

    action, reasons = recommend_action(anomaly_result(), prediction)

    assert action == "ENGINEER_REVIEW"
    assert any("predicted final value" in reason for reason in reasons)


def test_data_quality_problem_forces_retest() -> None:
    action, _ = recommend_action(
        anomaly_result(data_quality_warning="Duplicate measurement")
    )

    assert action == "RETEST"


def test_prediction_contract_builds_dashboard_record() -> None:
    prediction = PredictionResult(
        predicted_final_value=56.0,
        prediction_lower=49.0,
        prediction_upper=63.0,
    )

    record = build_screening_record(anomaly_result(), prediction)

    assert record["predicted_final_value"] == 56.0
    assert record["target_hour"] == 168.0
    assert record["recommendation"] == "ENGINEER_REVIEW"
    assert record["recommendation_reasons"]
