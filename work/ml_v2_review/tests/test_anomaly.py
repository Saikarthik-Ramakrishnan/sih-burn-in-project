from __future__ import annotations

import pandas as pd

from sih26170 import BatchAwareAnomalyDetector, build_component_features


def test_known_early_drift_is_ranked_first(demo_readings: pd.DataFrame) -> None:
    features = build_component_features(demo_readings, as_of_hour=24)
    detector = BatchAwareAnomalyDetector(contamination=0.05)

    scored = detector.fit_score(features).sort_values(
        "anomaly_score", ascending=False
    )

    assert scored.iloc[0]["component_id"] == "C012"
    assert bool(scored.iloc[0]["is_anomaly"])
    assert scored.iloc[0]["anomaly_score"] >= 0.8
    assert any("batch norm" in reason for reason in scored.iloc[0]["reason_codes"])


def test_dashboard_contract_is_serializable(demo_readings: pd.DataFrame) -> None:
    features = build_component_features(demo_readings, as_of_hour=24)
    detector = BatchAwareAnomalyDetector(contamination=0.05)
    result = detector.to_results(detector.fit_score(features))[0].to_dict()

    assert set(result) >= {
        "component_id",
        "anomaly_score",
        "is_anomaly",
        "reason_codes",
        "data_quality_warning",
    }

