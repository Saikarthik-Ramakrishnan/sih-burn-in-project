"""Separate outcome-file support, against the real MLCC bundle.

The central property under test: an outcome file is presentation only. Adding
one, removing one, or changing every value inside one must leave forecasts,
anomaly scores, peer statistics and recommendations bit-identical.
"""

from __future__ import annotations

import io

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from sih26170.api.config import PROJECT_ROOT, ServiceMode, Settings
from sih26170.api.main import create_app
from sih26170.api.sample_data import build_sample_csv

DEMO_DIR = PROJECT_ROOT / "outputs" / "mlcc_v1"
BUNDLE = DEMO_DIR / "model_bundle"

pytestmark = pytest.mark.skipif(
    not (BUNDLE / "manifest.json").is_file(), reason="MLCC bundle not present"
)


@pytest.fixture(scope="module")
def client() -> TestClient:
    app = create_app(Settings(mode=ServiceMode.DEMO, mlcc_bundle_dir=BUNDLE))
    with TestClient(app) as started:
        yield started


@pytest.fixture(scope="module")
def early_frame() -> pd.DataFrame:
    frame = pd.read_csv(io.BytesIO(build_sample_csv()), dtype=str)
    return frame[frame["hours"].astype(float) <= 24.0].reset_index(drop=True)


@pytest.fixture(scope="module")
def outcome_frame(early_frame: pd.DataFrame) -> pd.DataFrame:
    frame = pd.read_csv(DEMO_DIR / "demo_outcomes.csv", dtype=str)
    keep = set(early_frame["component_id"])
    frame = frame[frame["component_id"].isin(keep)]
    return frame[frame["hours"].astype(float) == 168.0].reset_index(drop=True)


def to_csv(frame: pd.DataFrame) -> bytes:
    return frame.to_csv(index=False).encode()


def screen(
    client: TestClient, early: pd.DataFrame, outcome: pd.DataFrame | None = None, **data
):
    files = {"file": ("early.csv", to_csv(early), "text/csv")}
    if outcome is not None:
        files["outcome_file"] = ("outcomes.csv", to_csv(outcome), "text/csv")
    return client.post("/api/v1/screen", files=files, data=data or None)


def inference_fingerprint(body: dict) -> list[tuple]:
    """Everything an outcome file must never be able to move."""
    return [
        (
            r["component_id"],
            r["recommendation"],
            r["anomaly"]["score"],
            r["anomaly"]["is_anomaly"],
            r["forecast"]["predicted_final_value"],
            r["forecast"]["prediction_lower"],
            r["forecast"]["prediction_upper"],
            r["peers"]["current_batch_robust_z"],
            r["limits"]["applicable_limit"],
        )
        for r in sorted(body["records"], key=lambda r: r["component_id"])
    ]


# --------------------------------------------------------------------------
# Backwards compatibility
# --------------------------------------------------------------------------


def test_existing_single_file_requests_still_work(client, early_frame):
    response = screen(client, early_frame)
    assert response.status_code == 200
    body = response.json()
    assert body["scored_record_count"] > 0
    assert body["evaluation"] is None


def test_empty_outcome_part_is_treated_as_absent(client, early_frame):
    """A browser sending an empty file input must not break the request."""
    response = client.post(
        "/api/v1/screen",
        files={
            "file": ("early.csv", to_csv(early_frame), "text/csv"),
            "outcome_file": ("", b"", "application/octet-stream"),
        },
    )
    assert response.status_code == 200
    assert response.json()["evaluation"] is None


# --------------------------------------------------------------------------
# The invariance that matters
# --------------------------------------------------------------------------


def test_adding_an_outcome_file_changes_no_inference(client, early_frame, outcome_frame):
    without = screen(client, early_frame).json()
    with_outcomes = screen(client, early_frame, outcome_frame).json()

    assert inference_fingerprint(without) == inference_fingerprint(with_outcomes)
    assert without["decision_counts"] == with_outcomes["decision_counts"]
    assert without["evaluation"] is None
    assert with_outcomes["evaluation"]["kind"] == "observed_readings"


def test_changing_every_outcome_value_changes_no_inference(
    client, early_frame, outcome_frame
):
    baseline = screen(client, early_frame, outcome_frame).json()

    altered = outcome_frame.copy()
    altered["measurement_value"] = "999.0"
    altered_body = screen(client, early_frame, altered).json()

    assert inference_fingerprint(baseline) == inference_fingerprint(altered_body)
    assert baseline["decision_counts"] == altered_body["decision_counts"]

    # Only the evaluation section may move.
    assert altered_body["evaluation"]["outcomes"][0]["observed_value"] == 999.0
    assert all(
        o["crossed_applicable_limit"] for o in altered_body["evaluation"]["outcomes"]
    )


def test_outcome_file_limits_are_ignored_in_favour_of_the_early_file(
    client, early_frame, outcome_frame
):
    """A later file must not be able to move the goalposts."""
    tampered = outcome_frame.copy()
    tampered["upper_limit"] = "99999.0"  # would hide every crossing if trusted

    honest = screen(client, early_frame, outcome_frame).json()
    body = screen(client, early_frame, tampered).json()

    assert inference_fingerprint(honest) == inference_fingerprint(body)

    honest_limits = {
        o["component_id"]: o["applicable_limit"] for o in honest["evaluation"]["outcomes"]
    }
    for outcome in body["evaluation"]["outcomes"]:
        assert outcome["applicable_limit"] == honest_limits[outcome["component_id"]]
        assert outcome["applicable_limit"] != 99999.0

    assert any(w["code"] == "OUTCOME_LIMITS_IGNORED" for w in body["warnings"])


def test_crossings_are_computed_from_the_early_file_limit(
    client, early_frame, outcome_frame
):
    body = screen(client, early_frame, outcome_frame).json()

    limits = {
        str(row.component_id): float(row.upper_limit)
        for row in early_frame.itertuples(index=False)
    }
    expected = {
        str(row.component_id)
        for row in outcome_frame.itertuples(index=False)
        if float(row.measurement_value) > limits[str(row.component_id)]
    }
    assert expected, "fixture must contain a genuine crossing"

    reported = {
        o["component_id"]
        for o in body["evaluation"]["outcomes"]
        if o["crossed_applicable_limit"]
    }
    assert reported == expected


# --------------------------------------------------------------------------
# Validation
# --------------------------------------------------------------------------


def test_outcome_at_or_before_the_cutoff_rejected(client, early_frame, outcome_frame):
    bad = outcome_frame.copy()
    bad.loc[bad.index[0], "hours"] = "24"
    response = screen(client, early_frame, bad)
    assert response.status_code == 422
    assert response.json()["error"] == "INVALID_HOURS"


def test_duplicate_outcome_checkpoint_rejected(client, early_frame, outcome_frame):
    bad = pd.concat([outcome_frame, outcome_frame.head(1)], ignore_index=True)
    response = screen(client, early_frame, bad)
    assert response.status_code == 422
    assert response.json()["error"] == "DUPLICATE_MEASUREMENT_IDENTITY"


def test_unknown_identity_rejected_not_silently_dropped(
    client, early_frame, outcome_frame
):
    """The core inner-joins, so an unpaired file would reveal nothing quietly."""
    bad = outcome_frame.copy()
    bad.loc[bad.index[0], "component_id"] = "MLCC_C999999"
    response = screen(client, early_frame, bad)
    assert response.status_code == 422
    body = response.json()
    assert body["error"] == "AMBIGUOUS_COMPONENT_IDENTITY"
    assert "MLCC_C999999" in str(body["details"])


def test_outcome_unit_mismatch_rejected(client, early_frame, outcome_frame):
    bad = outcome_frame.copy()
    bad["measurement_unit"] = "nA"
    response = screen(client, early_frame, bad)
    assert response.status_code == 422
    assert response.json()["error"] == "INCOMPATIBLE_UNITS"


def test_non_finite_outcome_value_rejected(client, early_frame, outcome_frame):
    bad = outcome_frame.copy()
    bad.loc[bad.index[0], "measurement_value"] = "inf"
    response = screen(client, early_frame, bad)
    assert response.status_code == 422
    assert response.json()["error"] == "NON_FINITE_VALUE"


def test_outcome_missing_required_columns_rejected(client, early_frame, outcome_frame):
    bad = outcome_frame.drop(columns=["measurement_value"])
    response = screen(client, early_frame, bad)
    assert response.status_code == 422
    assert response.json()["error"] == "MISSING_REQUIRED_COLUMNS"


def test_outcome_binary_payload_rejected(client, early_frame):
    response = client.post(
        "/api/v1/screen",
        files={
            "file": ("early.csv", to_csv(early_frame), "text/csv"),
            "outcome_file": ("book.xlsx", b"PK\x03\x04fake", "text/csv"),
        },
    )
    assert response.status_code == 415
    assert response.json()["error"] == "UNSUPPORTED_FILE_TYPE"


def test_partial_outcome_coverage_is_warned_not_hidden(
    client, early_frame, outcome_frame
):
    half = outcome_frame.head(len(outcome_frame) // 2)
    body = screen(client, early_frame, half).json()
    warning = next(
        (w for w in body["warnings"] if w["code"] == "OUTCOME_COVERAGE_PARTIAL"), None
    )
    assert warning is not None
    assert "not the same as having stayed within limit" in warning["message"]
