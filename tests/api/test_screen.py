"""End-to-end tests for the GENERIC (non-MLCC) screening path.

The MLCC prototype bundle owns the pilot profile and is covered by
``test_screen_mlcc.py`` against the real artifact. This module keeps the generic
path under test for families that have no bundle of their own, so it configures
a registry with no MLCC bundle and supplies the core calls as doubles.

Everything else under test is real API code: routing, ingestion, eligibility,
compatibility, identity joins, evidence assembly, summaries and serialisation.
"""

from __future__ import annotations

import copy

import pytest
from fastapi.testclient import TestClient

from sih26170.api import core_bridge, service
from pathlib import Path

from sih26170.api.config import ServiceMode, Settings
from sih26170.api.main import create_app
from sih26170.prediction.registry import ModelRegistry

from .conftest import burn_in_rows, make_csv
from .doubles import (
    RecordingAnomalyAdapter,
    RecordingForecastAdapter,
    fake_build_component_features,
    fake_build_screening_record,
    fake_make_prediction_result,
)


@pytest.fixture
def generic_profiles_enabled(monkeypatch):
    """Mark the generic development families scoreable, for these tests only.

    In production they are 'planned': no trained artifact covers them, and the
    MLCC bundle does not apply to another family. The generic screening path
    still needs coverage, so it is exercised here against profiles that are
    enabled in the test process alone and never in the shipped registry.
    """
    from dataclasses import replace

    from sih26170.api import profiles as profiles_module

    enabled = {
        key: (
            replace(profile, status=profiles_module.ProfileStatus.SUPPORTED)
            if profile.profile_id
            in {"digital_ic_leakage_ua", "power_mosfet_rds_on_mohm"}
            else profile
        )
        for key, profile in profiles_module._BY_KEY.items()
    }
    monkeypatch.setattr(profiles_module, "_BY_KEY", enabled)
    return True


@pytest.fixture
def patched_core(monkeypatch, generic_profiles_enabled):
    monkeypatch.setattr(service.core_bridge, "build_component_features", fake_build_component_features)
    monkeypatch.setattr(service.core_bridge, "make_prediction_result", fake_make_prediction_result)
    monkeypatch.setattr(service.core_bridge, "build_screening_record", fake_build_screening_record)
    monkeypatch.setattr(
        service.core_bridge, "adapt_screening_record", lambda record: record.recommendation
    )
    return True


@pytest.fixture
def adapters() -> tuple[RecordingAnomalyAdapter, RecordingForecastAdapter]:
    return RecordingAnomalyAdapter(), RecordingForecastAdapter()


def build_client(
    adapters: tuple[RecordingAnomalyAdapter, RecordingForecastAdapter] | None,
    *,
    mode: ServiceMode = ServiceMode.DEMO,
    forecast: bool = True,
) -> TestClient:
    settings = Settings(mode=mode, mlcc_bundle_dir=Path("__no_mlcc_bundle__"))
    app = create_app(settings)
    registry = ModelRegistry(settings)
    if adapters is not None:
        anomaly, forecaster = adapters
        registry._install_test_adapters(
            anomaly=anomaly, forecast=forecaster if forecast else None
        )
    app.state.registry = registry
    client = TestClient(app)
    # Keep the injected registry: lifespan would otherwise rebuild it.
    client.app.state.registry = registry
    return client


@pytest.fixture
def client(patched_core, adapters):
    app_client = build_client(adapters)
    with app_client as started:
        started.app.state.registry._install_test_adapters(
            anomaly=adapters[0], forecast=adapters[1]
        )
        yield started


def post_csv(client: TestClient, raw: bytes, filename: str = "burn_in.csv", **data):
    return client.post(
        "/api/v1/screen",
        files={"file": (filename, raw, "text/csv")},
        data=data or None,
    )


# --------------------------------------------------------------------------
# Happy path
# --------------------------------------------------------------------------


def test_valid_csv_returns_typed_results(client):
    rows = burn_in_rows(n_components=12, drift_per_component=0.02)
    response = post_csv(client, make_csv(rows))
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["schema_version"] == "1.0.0"
    assert body["input_source"] == "upload"
    assert body["filename"] == "burn_in.csv"
    assert body["as_of_hour"] == 24.0
    assert body["target_hour"] == 168.0
    assert body["checkpoint_hours_used"] == [0.0, 24.0]
    assert body["batch_count"] == 1
    assert body["unique_component_count"] == 12
    assert body["measurement_record_count"] == 12
    assert body["scored_record_count"] == 12
    assert body["unscored_record_count"] == 0
    assert body["duration_ms"] > 0
    assert len(body["request_id"]) > 0
    assert body["model_versions"]["anomaly"] == "test-anomaly-0.0.0"
    assert body["model_versions"]["forecast"] == "test-forecast-0.0.0"

    counts = body["decision_counts"]
    assert sum(counts.values()) == body["scored_record_count"]


def test_record_carries_full_identity_and_evidence(client):
    rows = burn_in_rows(n_components=10, drift_per_component=0.02)
    body = post_csv(client, make_csv(rows)).json()
    record = body["records"][0]

    for field in ("component_id", "batch_id", "component_family", "measurement_name"):
        assert record[field]

    assert record["anomaly"]["status"] == "available"
    assert record["anomaly"]["score"] is not None
    assert "not a probability" in record["anomaly"]["note"]

    assert record["forecast"]["status"] == "available"
    assert record["forecast"]["target_hour"] == 168.0
    assert record["forecast"]["interval_nominal_coverage"] == 0.9
    assert record["forecast"]["interval_method"] == "split_conformal"

    assert record["limits"]["direction"] == "upper"
    assert record["limits"]["applicable_limit"] == 10.0
    assert record["early_trajectory"] == [
        {"hour": 0.0, "value": record["initial_value"]},
        {"hour": 24.0, "value": record["latest_value"]},
    ]
    assert record["last_observation_hour"] == 24.0
    assert record["acceleration"] is None


def test_percent_change_is_a_fraction(client):
    rows = burn_in_rows(n_components=8, base_value=1.0, drift_per_component=0.0)
    # component index 0 has no drift; force a known 20 % rise on one history
    for row in rows:
        if row["component_id"] == "C0000" and row["hours"] == 24.0:
            row["measurement_value"] = 1.2
    body = post_csv(client, make_csv(rows)).json()
    record = next(r for r in body["records"] if r["component_id"] == "C0000")
    assert record["percent_change"] == pytest.approx(0.2)
    assert record["percent_change_available"] is True
    assert record["absolute_change"] == pytest.approx(0.2)
    assert record["slope_per_hour"] == pytest.approx(0.2 / 24.0)


def test_zero_initial_value_has_no_displayable_percentage(client):
    rows = burn_in_rows(n_components=9, drift_per_component=0.0)
    for row in rows:
        if row["component_id"] == "C0000":
            row["measurement_value"] = 0.0 if row["hours"] == 0.0 else 0.5
    body = post_csv(client, make_csv(rows)).json()
    record = next(r for r in body["records"] if r["component_id"] == "C0000")
    assert record["percent_change"] is None
    assert record["percent_change_available"] is False
    assert record["absolute_change"] == pytest.approx(0.5)


def test_leading_zero_ids_survive_the_round_trip(client):
    rows = burn_in_rows(n_components=5, id_prefix="", id_width=7)
    body = post_csv(client, make_csv(rows)).json()
    returned = {r["component_id"] for r in body["records"]}
    assert returned == {"0000000", "0000001", "0000002", "0000003", "0000004"}


def test_summaries_are_consistent_with_records(client):
    rows = burn_in_rows(n_components=10, drift_per_component=0.02)
    body = post_csv(client, make_csv(rows)).json()
    summaries = body["component_summaries"]
    assert len(summaries) == 10
    assert all(s["partial_coverage"] is False for s in summaries)
    assert all(s["scored_measurement_count"] == 1 for s in summaries)
    by_id = {r["component_id"]: r["recommendation"] for r in body["records"]}
    for summary in summaries:
        assert summary["summary_recommendation"] == by_id[summary["component_id"]]


# --------------------------------------------------------------------------
# Multiple measurements per component
# --------------------------------------------------------------------------


def test_partial_coverage_never_reads_as_a_full_pass(client):
    """One measurement scored, one missing its 24 h reading."""
    rows = burn_in_rows(n_components=9, measurement="leakage_ua")
    partial = burn_in_rows(
        n_components=1, measurement="rds_on_mohm", family="Power MOSFET", hours=(0.0,)
    )
    # attach the second measurement to an existing component
    for row in partial:
        row["component_id"] = "C0000"
        row["component_family"] = "Digital IC"
    rows += partial

    body = post_csv(client, make_csv(rows)).json()
    assert body["unscored_record_count"] == 1
    unscored = body["unscored_records"][0]
    assert unscored["reason"] == "unsupported_profile"

    summary = next(s for s in body["component_summaries"] if s["component_id"] == "C0000")
    assert summary["partial_coverage"] is True
    assert summary["unscored_measurement_count"] == 1
    assert summary["scored_measurement_count"] == 1


def test_most_urgent_scored_recommendation_wins_the_summary(client):
    calm = burn_in_rows(n_components=9, drift_per_component=0.0)
    body = post_csv(client, make_csv(calm)).json()
    assert all(r["recommendation"] == "ACCEPT" for r in body["records"])
    assert all(s["summary_recommendation"] == "ACCEPT" for s in body["component_summaries"])


# --------------------------------------------------------------------------
# Eligibility and partial data
# --------------------------------------------------------------------------


def test_history_missing_the_24h_checkpoint_is_reported_unscored(client):
    rows = burn_in_rows(n_components=10)
    rows = [r for r in rows if not (r["component_id"] == "C0003" and r["hours"] == 24.0)]
    body = post_csv(client, make_csv(rows)).json()

    assert body["scored_record_count"] == 9
    assert body["unscored_record_count"] == 1
    unscored = body["unscored_records"][0]
    assert unscored["component_id"] == "C0003"
    assert unscored["reason"] == "missing_checkpoint"
    assert unscored["missing_checkpoint_hours"] == [24.0]
    assert unscored["available_hours"] == [0.0]


def test_no_eligible_histories_returns_422():
    rows = burn_in_rows(n_components=4, hours=(0.0,))
    client = build_client((RecordingAnomalyAdapter(), RecordingForecastAdapter()))
    with client as started:
        response = post_csv(started, make_csv(rows))
    assert response.status_code == 422
    body = response.json()
    assert body["error"] == "NO_ELIGIBLE_HISTORIES"
    assert body["details"]


def test_intermediate_readings_are_excluded_with_a_warning(client):
    rows = burn_in_rows(n_components=10, hours=(0.0, 6.0, 12.0, 24.0))
    body = post_csv(client, make_csv(rows)).json()
    codes = {w["code"] for w in body["warnings"]}
    assert "NON_CHECKPOINT_READINGS_IGNORED" in codes
    warning = next(w for w in body["warnings"] if w["code"] == "NON_CHECKPOINT_READINGS_IGNORED")
    assert warning["count"] == 20  # 10 components x 2 excluded hours
    for record in body["records"]:
        assert [p["hour"] for p in record["early_trajectory"]] == [0.0, 24.0]


def test_unsupported_as_of_hour_rejected(client):
    rows = burn_in_rows(n_components=10)
    response = post_csv(client, make_csv(rows), as_of_hour="48")
    assert response.status_code == 422
    assert response.json()["error"] == "UNSUPPORTED_AS_OF_HOUR"


# --------------------------------------------------------------------------
# Cutoff discipline
# --------------------------------------------------------------------------


def _inference_fingerprint(body: dict) -> list[dict]:
    """Everything that must not change when post-cutoff data changes."""
    return [
        {
            "id": r["component_id"],
            "recommendation": r["recommendation"],
            "score": r["anomaly"]["score"],
            "prediction": r["forecast"]["predicted_final_value"],
            "lower": r["forecast"]["prediction_lower"],
            "upper": r["forecast"]["prediction_upper"],
            "initial": r["initial_value"],
            "latest": r["latest_value"],
            "slope": r["slope_per_hour"],
            "peer_median": r["peers"]["median"],
            "peer_n": r["peers"]["sample_size"],
        }
        for r in body["records"]
    ]


def test_changing_post_cutoff_observations_cannot_change_inference(client):
    early_only = burn_in_rows(n_components=12, drift_per_component=0.02)

    with_outcome = copy.deepcopy(early_only)
    for row in list(with_outcome):
        if row["hours"] == 24.0:
            with_outcome.append({**row, "hours": 168.0, "measurement_value": 9.5})

    altered_outcome = copy.deepcopy(with_outcome)
    for row in altered_outcome:
        if row["hours"] == 168.0:
            row["measurement_value"] = 0.001

    base = post_csv(client, make_csv(early_only)).json()
    revealed = post_csv(client, make_csv(with_outcome)).json()
    altered = post_csv(client, make_csv(altered_outcome)).json()

    assert _inference_fingerprint(base) == _inference_fingerprint(revealed)
    assert _inference_fingerprint(base) == _inference_fingerprint(altered)

    # Only the evaluation-only section may differ.
    assert base["evaluation"] is None
    assert revealed["evaluation"]["available"] is True
    assert revealed["evaluation"]["outcomes"][0]["observed_value"] == 9.5
    assert altered["evaluation"]["outcomes"][0]["observed_value"] == 0.001
    assert revealed["evaluation"]["outcomes"][0]["crossed_applicable_limit"] is False


def test_evaluation_section_omitted_for_early_only_uploads(client):
    body = post_csv(client, make_csv(burn_in_rows(n_components=10))).json()
    assert body["evaluation"] is None


# --------------------------------------------------------------------------
# Identity joins
# --------------------------------------------------------------------------


def test_row_reordering_does_not_swap_components(client):
    rows = burn_in_rows(n_components=12, drift_per_component=0.03)
    forward = post_csv(client, make_csv(rows)).json()
    backward = post_csv(client, make_csv(list(reversed(rows)))).json()

    def by_id(body):
        return {
            r["component_id"]: (
                r["initial_value"],
                r["latest_value"],
                r["anomaly"]["score"],
                r["forecast"]["predicted_final_value"],
                r["recommendation"],
            )
            for r in body["records"]
        }

    assert by_id(forward) == by_id(backward)


def test_repeated_requests_are_reproducible(client):
    rows = burn_in_rows(n_components=12, drift_per_component=0.03)
    first = post_csv(client, make_csv(rows)).json()
    second = post_csv(client, make_csv(rows)).json()
    assert _inference_fingerprint(first) == _inference_fingerprint(second)


def test_scoring_never_fits_a_model(client, adapters):
    anomaly, forecaster = adapters
    rows = burn_in_rows(n_components=10)
    post_csv(client, make_csv(rows))
    post_csv(client, make_csv(rows))
    assert anomaly.fit_calls == 0
    assert forecaster.fit_calls == 0
    assert anomaly.score_calls == 2
    assert forecaster.predict_calls == 2


# --------------------------------------------------------------------------
# Missing capabilities
# --------------------------------------------------------------------------


def test_missing_anomaly_model_returns_503(patched_core):
    client = build_client(None)
    with client as started:
        response = post_csv(started, make_csv(burn_in_rows(n_components=10)))
    assert response.status_code == 503
    body = response.json()
    assert body["error"] in {"ANOMALY_MODEL_UNAVAILABLE", "CORE_UNAVAILABLE"}
    assert body["message"]


def test_missing_forecast_yields_nulls_not_zeros(patched_core):
    anomaly = RecordingAnomalyAdapter()
    client = build_client((anomaly, RecordingForecastAdapter()), forecast=False)
    with client as started:
        started.app.state.registry._install_test_adapters(anomaly=anomaly)
        body = post_csv(started, make_csv(burn_in_rows(n_components=10))).json()

    assert body["capabilities"]["forecast"] is False
    assert body["capabilities"]["intervals"] is False
    for record in body["records"]:
        forecast = record["forecast"]
        assert forecast["status"] == "unavailable"
        assert forecast["predicted_final_value"] is None
        assert forecast["prediction_lower"] is None
        assert forecast["prediction_upper"] is None
        assert forecast["note"]
        assert record["provisional"] is True
        assert record["recommendation_basis"] == "anomaly_only"

    assert any(w["code"] == "PROVISIONAL_RECOMMENDATIONS" for w in body["warnings"])


def test_uncalibrated_forecast_reports_null_bounds(patched_core):
    anomaly = RecordingAnomalyAdapter()
    forecaster = RecordingForecastAdapter(with_intervals=False)
    client = build_client((anomaly, forecaster))
    with client as started:
        started.app.state.registry._install_test_adapters(anomaly=anomaly, forecast=forecaster)
        body = post_csv(started, make_csv(burn_in_rows(n_components=10))).json()

    for record in body["records"]:
        forecast = record["forecast"]
        assert forecast["predicted_final_value"] is not None
        assert forecast["prediction_lower"] is None
        assert forecast["prediction_upper"] is None
        assert forecast["interval_nominal_coverage"] is None
        assert "no calibrated prediction interval" in forecast["note"].lower()
    assert body["capabilities"]["intervals"] is False


# --------------------------------------------------------------------------
# Profiles, peers and compatibility
# --------------------------------------------------------------------------


def test_unsupported_family_is_unscored_not_guessed(client):
    good = burn_in_rows(n_components=10)
    exotic = burn_in_rows(
        n_components=2, family="Tantalum Cap", measurement="esr_mohm", id_prefix="T"
    )
    body = post_csv(client, make_csv(good + exotic)).json()
    reasons = {u["reason"] for u in body["unscored_records"]}
    assert reasons == {"unsupported_profile"}
    assert body["unscored_record_count"] == 2


def test_planned_profile_cannot_be_scored(client):
    """A lower-limit profile must not silently take the upper-limit path."""
    rows = burn_in_rows(
        n_components=10,
        family="Film Capacitor",
        measurement="capacitance_nf",
        id_prefix="F",
    )
    response = post_csv(client, make_csv(rows))
    assert response.status_code == 422
    body = response.json()
    assert body["error"] == "NO_ELIGIBLE_HISTORIES"
    assert any("planned" in d["message"].lower() or "not yet available" in d["message"].lower()
               for d in body["details"])


def test_mlcc_profile_is_declared_but_not_scoreable(client):
    rows = burn_in_rows(n_components=10, family="MLCC X7R", id_prefix="M")
    response = post_csv(client, make_csv(rows))
    assert response.status_code == 422
    assert response.json()["error"] == "NO_ELIGIBLE_HISTORIES"


def test_mixed_units_in_a_peer_group_rejected(client):
    rows = burn_in_rows(n_components=10, extra={"measurement_unit": "uA"})
    for row in rows:
        if row["component_id"] == "C0005":
            row["measurement_unit"] = "nA"
    response = post_csv(client, make_csv(rows))
    assert response.status_code == 422
    assert response.json()["error"] == "INCOMPATIBLE_UNITS"


def test_unit_mismatching_the_profile_rejected(client):
    rows = burn_in_rows(n_components=10, extra={"measurement_unit": "nA"})
    response = post_csv(client, make_csv(rows))
    assert response.status_code == 422
    body = response.json()
    assert body["error"] == "INCOMPATIBLE_UNITS"
    assert "does not convert units" in body["details"][0]["message"]


def test_mixed_test_conditions_in_a_peer_group_rejected(client):
    rows = burn_in_rows(n_components=10, extra={"test_condition": "125C/5V5"})
    for row in rows:
        if row["component_id"] == "C0007":
            row["test_condition"] = "85C/3V3"
    response = post_csv(client, make_csv(rows))
    assert response.status_code == 422
    assert response.json()["error"] == "INCOMPATIBLE_TEST_CONDITIONS"


def test_small_peer_group_reports_insufficient_not_reliable(client):
    rows = burn_in_rows(n_components=3)
    body = post_csv(client, make_csv(rows)).json()
    for record in body["records"]:
        peers = record["peers"]
        assert peers["sample_size"] == 3
        assert peers["sufficient"] is False
        assert peers["status"] == "insufficient_data"
        assert "at least 8" in peers["note"]
    assert body["capabilities"]["peer_statistics"] is False


def test_sufficient_peer_group_reports_statistics(client):
    rows = burn_in_rows(n_components=12)
    body = post_csv(client, make_csv(rows)).json()
    peers = body["records"][0]["peers"]
    assert peers["sample_size"] == 12
    assert peers["sufficient"] is True
    assert peers["median"] is not None
    assert peers["mad"] is not None


# --------------------------------------------------------------------------
# Provenance
# --------------------------------------------------------------------------


def test_synthetic_provenance_stays_visible(client):
    rows = burn_in_rows(n_components=10, extra={"data_source": "synthetic_v9"})
    body = post_csv(client, make_csv(rows)).json()
    assert body["provenance"] == "synthetic"
    assert any(w["code"] == "SYNTHETIC_DATA" for w in body["warnings"])
    assert all(r["provenance"] == "synthetic" for r in body["records"])


def test_absent_provenance_is_unknown_with_a_warning(client):
    body = post_csv(client, make_csv(burn_in_rows(n_components=10))).json()
    assert body["provenance"] == "unknown"
    assert any(w["code"] == "UNKNOWN_PROVENANCE" for w in body["warnings"])


def test_unsupplied_metadata_stays_null(client):
    body = post_csv(client, make_csv(burn_in_rows(n_components=10))).json()
    record = body["records"][0]
    assert record["part_number"] is None
    assert record["temperature_c"] is None
    assert record["humidity_pct"] is None
    assert record["applied_voltage_v"] is None
    assert record["board_position"] is None


# --------------------------------------------------------------------------
# Transport-level errors
# --------------------------------------------------------------------------


def test_oversized_upload_returns_413(client):
    settings = client.app.state.settings
    payload = b"component_id\n" + b"x" * (settings.max_upload_bytes + 1024)
    response = post_csv(client, payload)
    assert response.status_code == 413
    assert response.json()["error"] == "FILE_TOO_LARGE"


def test_spreadsheet_upload_returns_415(client):
    response = post_csv(client, b"PK\x03\x04\x14\x00fake xlsx", filename="data.xlsx")
    assert response.status_code == 415
    assert response.json()["error"] == "UNSUPPORTED_FILE_TYPE"


def test_empty_upload_returns_422(client):
    response = post_csv(client, b"")
    assert response.status_code == 422
    assert response.json()["error"] == "FILE_EMPTY"


def test_error_responses_carry_the_request_id(client):
    response = post_csv(client, b"")
    assert response.json()["request_id"]
    assert response.headers["x-request-id"]


def test_errors_never_leak_a_traceback(client):
    response = post_csv(client, b"component_id,batch_id\n1,2\n")
    body = response.text
    assert "Traceback" not in body
    assert "File \"" not in body


def test_content_type_is_not_trusted_over_content(client):
    """A CSV sent with an Excel MIME type is still accepted."""
    rows = burn_in_rows(n_components=10)
    response = client.post(
        "/api/v1/screen",
        files={"file": ("export.csv", make_csv(rows), "application/vnd.ms-excel")},
    )
    assert response.status_code == 200
