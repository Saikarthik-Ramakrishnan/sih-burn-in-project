"""Readiness truthfulness, profile advertising and the synthetic sample."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from sih26170.api.config import PROJECT_ROOT, ServiceMode, Settings
from sih26170.api.ingestion import ingest_csv
from sih26170.api.main import create_app
from sih26170.api.profiles import DataProvenance
from sih26170.api.sample_data import build_sample_csv
from sih26170.prediction.registry import ModelRegistry

from .doubles import RecordingAnomalyAdapter, RecordingForecastAdapter

REAL_BUNDLE = PROJECT_ROOT / "outputs" / "mlcc_v2" / "model_bundle"
NO_BUNDLE = Path("__no_mlcc_bundle__")


def make_client(
    mode: ServiceMode, *, anomaly=None, forecast=None, bundle: Path | None = None
) -> TestClient:
    settings = Settings(mode=mode, mlcc_bundle_dir=bundle or NO_BUNDLE)
    app = create_app(settings)
    registry = ModelRegistry(settings)
    if anomaly or forecast:
        registry._install_test_adapters(anomaly=anomaly, forecast=forecast)
    app.state.registry = registry
    client = TestClient(app)
    client.app.state.registry = registry
    return client


def real_client(mode: ServiceMode = ServiceMode.DEMO) -> TestClient:
    """A client backed by the actual shipped MLCC bundle."""
    return TestClient(create_app(Settings(mode=mode, mlcc_bundle_dir=REAL_BUNDLE)))


# --------------------------------------------------------------------------
# Liveness / readiness
# --------------------------------------------------------------------------


def test_liveness_is_independent_of_models():
    with make_client(ServiceMode.DEMO) as client:
        response = client.get("/api/v1/health/live")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "alive"
    assert body["schema_version"] == "1.0.0"


def test_readiness_is_503_when_the_bundle_is_absent():
    """A missing artifact must fail readiness, not degrade quietly."""
    settings = Settings(mode=ServiceMode.DEMO, mlcc_bundle_dir=NO_BUNDLE)
    with TestClient(create_app(settings)) as client:
        response = client.get("/api/v1/health/ready")

    assert response.status_code == 503
    body = response.json()
    assert body["ready"] is False

    capabilities = {c["name"]: c for c in body["capabilities"]}
    assert capabilities["anomaly"]["available"] is False
    assert capabilities["forecast"]["available"] is False
    # The core modules ARE importable now; only the artifact is missing.
    assert capabilities["core_modules"]["available"] is True
    assert "bundle" in capabilities["anomaly"]["reason"].lower()


def test_readiness_is_200_with_the_real_bundle():
    with real_client() as client:
        response = client.get("/api/v1/health/ready")

    assert response.status_code == 200
    body = response.json()
    assert body["ready"] is True
    assert body["limitations"] == []

    capabilities = {c["name"]: c for c in body["capabilities"]}
    assert capabilities["anomaly"]["available"] is True
    assert capabilities["forecast"]["available"] is True
    assert capabilities["anomaly"]["model_version"] == "mlcc-pilot-1.1"
    assert capabilities["anomaly"]["artifact_id"]


def test_readiness_reports_checksum_and_probe_checks():
    """Readiness must reflect real verification, not just file presence."""
    with real_client() as client:
        body = client.get("/api/v1/health/ready").json()

    anomaly = next(c for c in body["capabilities"] if c["name"] == "anomaly")
    names = {check["name"] for check in anomaly["checks"]}
    assert "checksum:state.skops" in names
    assert "checksum:xgboost.json" in names
    assert "inference_probe" in names
    assert all(check["passed"] for check in anomaly["checks"])


def test_a_corrupted_artifact_fails_readiness(tmp_path):
    """Flipping one byte of the model must be caught by the checksum gate."""
    import shutil

    bundle = tmp_path / "model_bundle"
    shutil.copytree(REAL_BUNDLE, bundle)
    target = bundle / "xgboost.json"
    target.write_bytes(target.read_bytes() + b"\n")

    settings = Settings(mode=ServiceMode.DEMO, mlcc_bundle_dir=bundle)
    with TestClient(create_app(settings)) as client:
        response = client.get("/api/v1/health/ready")

    assert response.status_code == 503
    anomaly = next(c for c in response.json()["capabilities"] if c["name"] == "anomaly")
    assert anomaly["available"] is False
    assert "integrity" in anomaly["reason"].lower() or "checksum" in anomaly["reason"].lower()


def test_demo_mode_requires_both_capabilities():
    with make_client(ServiceMode.DEMO, anomaly=RecordingAnomalyAdapter()) as client:
        response = client.get("/api/v1/health/ready")
    assert response.status_code == 503
    assert response.json()["ready"] is False


def test_anomaly_only_mode_states_its_limitations():
    with make_client(ServiceMode.ANOMALY_ONLY, anomaly=RecordingAnomalyAdapter()) as client:
        response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["ready"] is True
    assert body["mode"] == "anomaly_only"
    text = " ".join(body["limitations"]).lower()
    assert "no 168 h forecast" in text
    assert "must not be used for the demonstration" in text


# --------------------------------------------------------------------------
# Profiles
# --------------------------------------------------------------------------


def test_mlcc_is_the_only_usable_profile():
    with real_client() as client:
        body = client.get("/api/v1/profiles").json()

    profiles = {p["profile_id"]: p for p in body["profiles"]}
    usable = {pid for pid, p in profiles.items() if p["usable"]}
    assert usable == {"mlcc_x7r_leakage_ua"}

    mlcc = profiles["mlcc_x7r_leakage_ua"]
    assert mlcc["component_family"] == "MLCC_X7R"
    assert mlcc["measurement_name"] == "leakage_ua"
    assert mlcc["measurement_unit"] == "uA"
    assert mlcc["limit_direction"] == "upper"
    assert mlcc["required_checkpoint_hours"] == [0.0, 24.0]
    assert mlcc["target_hour"] == 168.0
    assert mlcc["anomaly_available"] is True
    assert mlcc["forecast_available"] is True


def test_bundle_part_profiles_are_advertised():
    """The UI must be able to tell a user which profile_id values are accepted."""
    with real_client() as client:
        body = client.get("/api/v1/profiles").json()
    mlcc = next(p for p in body["profiles"] if p["profile_id"] == "mlcc_x7r_leakage_ua")
    assert set(mlcc["supported_part_profiles"]) == {
        "SIM_X7R_100N_50V",
        "SIM_X7R_10N_50V",
        "SIM_X7R_1U_25V",
        "SIM_X7R_4U7_16V",
    }


def test_other_families_are_visibly_unavailable():
    """Renaming a family must not make the MLCC model appear to cover it."""
    with real_client() as client:
        body = client.get("/api/v1/profiles").json()

    profiles = {p["profile_id"]: p for p in body["profiles"]}
    for pid in ("digital_ic_leakage_ua", "power_mosfet_rds_on_mohm", "film_cap_capacitance_nf"):
        other = profiles[pid]
        assert other["status"] == "planned"
        assert other["usable"] is False
        assert other["forecast_available"] is False
        assert other["unavailable_reason"]
        assert other["supported_part_profiles"] == []


def test_mlcc_profile_declares_synthetic_training_data():
    with real_client() as client:
        body = client.get("/api/v1/profiles").json()
    mlcc = next(p for p in body["profiles"] if p["profile_id"] == "mlcc_x7r_leakage_ua")
    note = mlcc["provenance_note"].lower()
    assert "synthetic" in note
    assert "not validated hardware" in note


def test_lower_limit_profile_declares_its_direction():
    with real_client() as client:
        body = client.get("/api/v1/profiles").json()
    film = next(p for p in body["profiles"] if p["profile_id"] == "film_cap_capacitance_nf")
    assert film["limit_direction"] == "lower"
    assert film["usable"] is False


# --------------------------------------------------------------------------
# Sample CSV
# --------------------------------------------------------------------------


def test_sample_csv_is_deterministic():
    assert build_sample_csv() == build_sample_csv()


def test_sample_csv_is_served_and_labelled_synthetic():
    with real_client() as client:
        response = client.get("/api/v1/sample.csv")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert response.headers["x-data-provenance"] == "synthetic"
    assert "attachment" in response.headers["content-disposition"]


def test_sample_csv_uses_the_real_mlcc_schema():
    """The sample is a slice of the shipped MLCC dataset, not a renamed fixture."""
    dataset = ingest_csv(build_sample_csv(), max_data_rows=100_000)
    assert set(dataset.frame["component_family"]) == {"MLCC_X7R"}
    assert set(dataset.frame["measurement_name"]) == {"leakage_ua"}
    assert dataset.provenance is DataProvenance.SYNTHETIC
    assert "profile_id" in dataset.frame.columns
    assert set(dataset.frame["profile_id"]) <= {
        "SIM_X7R_100N_50V",
        "SIM_X7R_10N_50V",
        "SIM_X7R_1U_25V",
        "SIM_X7R_4U7_16V",
    }


def test_sample_csv_carries_early_and_outcome_hours():
    dataset = ingest_csv(build_sample_csv(), max_data_rows=100_000)
    assert sorted(set(dataset.frame["hours"])) == [0.0, 24.0, 168.0]


def test_openapi_document_is_published():
    with real_client() as client:
        response = client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    document = response.json()
    for path in ("/api/v1/screen", "/api/v1/profiles", "/api/v1/health/ready", "/api/v1/sample.csv"):
        assert path in document["paths"]
    assert "ScreenResponse" in document["components"]["schemas"]
    assert "ModelInfo" in document["components"]["schemas"]


def test_api_404_is_json_not_spa_html():
    with make_client(ServiceMode.DEMO) as client:
        response = client.get("/api/v1/does-not-exist")
    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/json")
