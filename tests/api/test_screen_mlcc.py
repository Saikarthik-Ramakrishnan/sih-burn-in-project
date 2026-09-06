"""Integration tests for the MLCC pilot path, against the ACTUAL loaded bundle.

No doubles here. These exercise the shipped mlcc-pilot-1.1 (v2) artifact through the
real HTTP surface, which is the only way to know the demo will behave.

The bundle is loaded once for the module because deserialising it costs a couple
of seconds; every test then screens a small slice of the shipped demonstration
dataset.
"""

from __future__ import annotations

import io

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from sih26170.api.config import PROJECT_ROOT, ServiceMode, Settings
from sih26170.api.schemas import OutcomeRecord
from sih26170.api.main import create_app

DEMO_DIR = PROJECT_ROOT / "outputs" / "mlcc_v1"  # synthetic demo data
BUNDLE_DIR = PROJECT_ROOT / "outputs" / "mlcc_v2" / "model_bundle"  # v2 bundle (mlcc-pilot-1.1)

pytestmark = pytest.mark.skipif(
    not (BUNDLE_DIR / "manifest.json").is_file(),
    reason="MLCC model bundle is not present in this working copy",
)

#: Small enough to keep the suite quick, large enough that every batch still has
#: more than the eight peers the core needs for a meaningful comparison.
SLICE_COMPONENTS = 60


@pytest.fixture(scope="module")
def client() -> TestClient:
    settings = Settings(mode=ServiceMode.DEMO, mlcc_bundle_dir=BUNDLE_DIR)
    with TestClient(create_app(settings)) as started:
        yield started


@pytest.fixture(scope="module")
def early_frame() -> pd.DataFrame:
    frame = pd.read_csv(DEMO_DIR / "demo_early.csv", dtype=str)
    keep = sorted(frame["component_id"].unique())[:SLICE_COMPONENTS]
    return frame[frame["component_id"].isin(keep)].reset_index(drop=True)


@pytest.fixture(scope="module")
def outcome_frame(early_frame: pd.DataFrame) -> pd.DataFrame:
    frame = pd.read_csv(DEMO_DIR / "demo_outcomes.csv", dtype=str)
    keep = set(early_frame["component_id"])
    later = frame[frame["component_id"].isin(keep) & (frame["hours"] == "168")]
    return later[early_frame.columns].reset_index(drop=True)


def to_csv(frame: pd.DataFrame) -> bytes:
    buffer = io.StringIO(newline="")
    frame.to_csv(buffer, index=False, lineterminator="\n")
    return buffer.getvalue().encode("utf-8")


def screen(client: TestClient, frame: pd.DataFrame, **data) -> dict:
    response = client.post(
        "/api/v1/screen",
        files={"file": ("mlcc.csv", to_csv(frame), "text/csv")},
        data=data or None,
    )
    assert response.status_code == 200, response.text
    return response.json()


# --------------------------------------------------------------------------
# Happy path against the real artifact
# --------------------------------------------------------------------------


def test_real_bundle_scores_every_component(client, early_frame):
    body = screen(client, early_frame)

    assert body["scored_record_count"] == SLICE_COMPONENTS
    assert body["unscored_record_count"] == 0
    assert sum(body["decision_counts"].values()) == SLICE_COMPONENTS
    assert body["as_of_hour"] == 24.0
    assert body["target_hour"] == 168.0
    assert body["checkpoint_hours_used"] == [0.0, 24.0]
    assert body["duration_ms"] > 0
    assert body["provenance"] == "synthetic"


def test_record_carries_real_evidence(client, early_frame):
    body = screen(client, early_frame)
    record = body["records"][0]

    assert record["component_family"] == "MLCC_X7R"
    assert record["measurement_name"] == "leakage_ua"
    assert record["measurement_unit"] == "uA"
    assert record["profile_id"].startswith("SIM_X7R_")

    anomaly = record["anomaly"]
    assert anomaly["score"] is not None
    assert anomaly["score_kind"] == "ranking score, not failure probability"
    assert isinstance(anomaly["reason_codes"], list)

    forecast = record["forecast"]
    assert forecast["predicted_final_value"] is not None
    assert forecast["prediction_lower"] is not None
    assert forecast["prediction_upper"] is not None
    assert forecast["prediction_lower"] <= forecast["predicted_final_value"] <= forecast["prediction_upper"]
    assert forecast["target_hour"] == 168.0
    # v2 stratified interval: an 80 % pair whose upper bound is the one-sided 90 % bound
    assert forecast["interval_nominal_coverage"] == pytest.approx(0.8)
    assert forecast["upper_bound_nominal_level"] == pytest.approx(0.9)
    assert forecast["interval_warning"]
    assert forecast["prediction_readiness"] in {
        "ready",
        "optional_inputs_imputed",
        "outside_training_conditions",
    }

    assert record["limits"]["direction"] == "upper"
    assert record["limits"]["applicable_limit"] > 0
    assert record["peers"]["sample_size"] > 0
    assert [p["hour"] for p in record["early_trajectory"]] == [0.0, 24.0]


def test_percent_change_is_a_fraction_from_the_real_core(client, early_frame):
    body = screen(client, early_frame)
    for record in body["records"]:
        if not record["percent_change_available"]:
            assert record["percent_change"] is None
            continue
        initial, latest = record["initial_value"], record["latest_value"]
        assert record["percent_change"] == pytest.approx((latest - initial) / initial, rel=1e-6)


def test_nulls_are_never_turned_into_zeros(client, early_frame):
    body = screen(client, early_frame)
    for record in body["records"]:
        if record["percent_change"] is None:
            assert record["percent_change_available"] is False
        if record["forecast"]["status"] == "unavailable":
            assert record["forecast"]["predicted_final_value"] is None
            assert record["forecast"]["prediction_lower"] is None


# --------------------------------------------------------------------------
# Forecast model honesty
# --------------------------------------------------------------------------


def test_default_forecast_uses_the_validation_winner(client, early_frame):
    body = screen(client, early_frame)
    info = body["model_info"]
    assert info["selected_model"] == "xgboost_v2"
    assert info["validation_winner"] == "xgboost_v2"
    assert info["forecast_selection"] == "internal validation winner"
    assert info["selection_warning"] is None
    assert "xgboost_v2" in info["available_models"] and "persistence" in info["available_models"]
    for record in body["records"]:
        forecast = record["forecast"]
        assert forecast["model_version"] == "xgboost_v2"
        assert forecast["interval_method"] == "stratified_asymmetric_split_conformal_signed_residual"
        assert forecast["interval_stratum"].startswith("slope_z_stratum_")
        assert forecast["interval_nominal_coverage"] == pytest.approx(0.8)
        assert forecast["upper_bound_nominal_level"] == pytest.approx(0.9)
        assert forecast["prediction_lower_two_sided"] <= forecast["prediction_lower"] <= forecast["predicted_final_value"]
        assert forecast["predicted_final_value"] <= forecast["prediction_upper"] <= forecast["prediction_upper_two_sided"]
        assert forecast["xgboost_explanation"]["is_active_forecast"] is True
        assert forecast["xgboost_explanation"]["explained_model"] == "xgboost_v2"


def test_persistence_can_still_be_requested_with_the_v1_symmetric_interval(client, early_frame):
    body = screen(client, early_frame, forecast_model="persistence")
    info = body["model_info"]
    assert info["selected_model"] == "persistence"
    assert info["validation_winner"] == "xgboost_v2"
    assert info["selection_warning"]
    for record in body["records"]:
        forecast = record["forecast"]
        assert forecast["model_version"] == "persistence"
        assert forecast["interval_method"] == "split_conformal_absolute_residual"
        assert forecast["interval_stratum"] is None and forecast["prediction_upper_two_sided"] is None
        assert forecast["interval_nominal_coverage"] == pytest.approx(0.9)
        assert forecast["predicted_final_value"] == pytest.approx(record["latest_value"])


def test_requesting_xgboost_is_reported_and_warned(client, early_frame):
    """The demo asks for XGBoost, which did NOT win internal validation."""
    body = screen(client, early_frame, forecast_model="xgboost")
    info = body["model_info"]

    assert info["selected_model"] == "xgboost"
    assert info["validation_winner"] == "xgboost_v2"
    assert info["forecast_selection"] == "explicit caller choice"
    assert info["selection_warning"]

    warning = next(
        w for w in body["warnings"] if w["code"] == "FORECAST_MODEL_NOT_VALIDATION_WINNER"
    )
    assert "xgboost_v2" in warning["message"]
    assert "not evidence that the selected model is better" in warning["message"]

    for record in body["records"]:
        assert record["forecast"]["model_version"] == "xgboost"


def test_xgboost_candidate_is_named_separately_from_the_active_forecast(client, early_frame):
    """A candidate's number must never be presented as the active forecast."""
    body = screen(client, early_frame, forecast_model="persistence")
    record = body["records"][0]
    forecast = record["forecast"]

    assert forecast["model_version"] == "persistence"
    assert forecast["xgboost_candidate_final_value"] is not None
    assert forecast["xgboost_explanation"]["is_active_forecast"] is False
    assert forecast["xgboost_explanation"]["explained_model"] == "xgboost"


def test_xgboost_explanation_marks_itself_active_when_it_is(client, early_frame):
    body = screen(client, early_frame, forecast_model="xgboost")
    record = body["records"][0]
    explanation = record["forecast"]["xgboost_explanation"]
    assert explanation["is_active_forecast"] is True
    assert explanation["top_contributions"]
    assert "not physical causes" in explanation["explains"]


def test_unknown_forecast_model_rejected(client, early_frame):
    response = client.post(
        "/api/v1/screen",
        files={"file": ("mlcc.csv", to_csv(early_frame), "text/csv")},
        data={"forecast_model": "magic_model"},
    )
    assert response.status_code == 422
    assert "magic_model" in response.json()["message"]


def test_model_info_declares_no_fitting_and_synthetic_training(client, early_frame):
    body = screen(client, early_frame)
    info = body["model_info"]
    assert info["model_fitted_during_request"] is False
    assert info["model_training_data"] == "synthetic"
    assert info["prototype_version"] == "mlcc-pilot-1.1"
    assert info["bundle_id"]
    assert info["limitations"]
    assert any(w["code"] == "SYNTHETIC_TRAINING_DATA" for w in body["warnings"])


def test_no_model_is_fitted_during_a_request(client, early_frame):
    """Assert it directly: make fitting explode, then screen."""
    engine = client.app.state.registry.mlcc_engine
    bundle = engine._bundle
    targets = [bundle.detector] + list(bundle.models.values())

    def explode(*args, **kwargs):
        raise AssertionError("A model was fitted during a scoring request.")

    saved = []
    for target in targets:
        if hasattr(target, "fit"):
            saved.append((target, target.fit))
            try:
                target.fit = explode
            except AttributeError:
                saved.pop()
    try:
        body = screen(client, early_frame)
        assert body["scored_record_count"] == SLICE_COMPONENTS
    finally:
        for target, original in saved:
            target.fit = original


# --------------------------------------------------------------------------
# Cutoff discipline and determinism
# --------------------------------------------------------------------------


def _fingerprint(body: dict) -> list[tuple]:
    return [
        (
            r["component_id"],
            r["recommendation"],
            r["anomaly"]["score"],
            r["forecast"]["predicted_final_value"],
            r["forecast"]["prediction_lower"],
            r["forecast"]["prediction_upper"],
            r["initial_value"],
            r["latest_value"],
            r["peers"]["current_batch_robust_z"],
        )
        for r in sorted(body["records"], key=lambda r: r["component_id"])
    ]


def test_changing_every_post_cutoff_reading_cannot_change_inference(
    client, early_frame, outcome_frame
):
    early_only = screen(client, early_frame)

    with_outcomes = screen(client, pd.concat([early_frame, outcome_frame], ignore_index=True))

    altered = outcome_frame.copy()
    altered["measurement_value"] = "999.0"
    with_altered = screen(client, pd.concat([early_frame, altered], ignore_index=True))

    assert _fingerprint(early_only) == _fingerprint(with_outcomes)
    assert _fingerprint(early_only) == _fingerprint(with_altered)

    # Only the evaluation-only section may differ.
    assert early_only["evaluation"] is None
    assert with_outcomes["evaluation"]["available"] is True
    assert with_outcomes["evaluation"]["kind"] == "observed_readings"
    assert with_altered["evaluation"]["outcomes"][0]["observed_value"] == 999.0


def test_removing_post_cutoff_readings_leaves_inference_unchanged(
    client, early_frame, outcome_frame
):
    combined = screen(client, pd.concat([early_frame, outcome_frame], ignore_index=True))
    early_only = screen(client, early_frame)
    assert _fingerprint(combined) == _fingerprint(early_only)


def test_repeated_inference_is_reproducible(client, early_frame):
    assert _fingerprint(screen(client, early_frame)) == _fingerprint(screen(client, early_frame))


def test_row_reordering_does_not_swap_components(client, early_frame):
    shuffled = early_frame.iloc[::-1].reset_index(drop=True)
    assert _fingerprint(screen(client, early_frame)) == _fingerprint(screen(client, shuffled))


def test_evaluation_section_omitted_for_early_only_uploads(client, early_frame):
    assert screen(client, early_frame)["evaluation"] is None


def test_simulation_labels_are_not_returned_as_observed_readings(client, early_frame):
    """Generator truth must never be dressed up as sensor measurements."""
    labels = pd.read_csv(DEMO_DIR / "demo_labels.csv", dtype=str)
    keep = set(early_frame["component_id"])
    labels = labels[labels["component_id"].isin(keep)]

    combined = pd.concat([early_frame, labels], ignore_index=True)
    response = client.post(
        "/api/v1/screen", files={"file": ("mlcc.csv", to_csv(combined), "text/csv")}
    )
    # Labels carry no `hours`, so they are not valid later observations at all.
    if response.status_code == 200:
        evaluation = response.json()["evaluation"]
        assert evaluation is None or evaluation["kind"] == "simulation_truth"
    else:
        assert response.status_code in (422, 413)


# --------------------------------------------------------------------------
# Eligibility, profiles and gating
# --------------------------------------------------------------------------


def test_missing_24h_checkpoint_is_reported_unscored(client, early_frame):
    victim = sorted(early_frame["component_id"])[0]
    trimmed = early_frame[
        ~((early_frame["component_id"] == victim) & (early_frame["hours"] == "24"))
    ]
    body = screen(client, trimmed)

    assert body["unscored_record_count"] == 1
    unscored = body["unscored_records"][0]
    assert unscored["component_id"] == victim
    assert unscored["reason"] == "missing_checkpoint"
    assert body["scored_record_count"] == SLICE_COMPONENTS - 1
    assert any(w["code"] == "UNSCORED_RECORDS_PRESENT" for w in body["warnings"])


def test_decision_counts_exclude_unscored_records(client, early_frame):
    """The core folds unscored records into RETEST; the API must not."""
    victim = sorted(early_frame["component_id"])[0]
    trimmed = early_frame[
        ~((early_frame["component_id"] == victim) & (early_frame["hours"] == "24"))
    ]
    body = screen(client, trimmed)
    assert sum(body["decision_counts"].values()) == body["scored_record_count"]

    summary = next(s for s in body["component_summaries"] if s["component_id"] == victim)
    assert summary["summary_recommendation"] is None
    assert summary["partial_coverage"] is True


def test_unknown_profile_id_is_unscored_not_guessed(client, early_frame):
    """A whole batch on an unknown part profile must not be scored by guesswork."""
    altered = early_frame.copy()
    batch = altered["batch_id"].iloc[0]
    altered.loc[altered["batch_id"] == batch, "profile_id"] = "SIM_NOT_A_REAL_PROFILE"
    body = screen(client, altered)

    affected = set(early_frame.loc[early_frame["batch_id"] == batch, "component_id"])
    unscored_ids = {u["component_id"] for u in body["unscored_records"]}
    assert affected <= unscored_ids
    reasons = {u["reason"] for u in body["unscored_records"] if u["component_id"] in affected}
    assert reasons == {"unsupported_profile"}

    scored_ids = {r["component_id"] for r in body["records"]}
    assert not (affected & scored_ids)


def test_mixed_part_profiles_within_a_batch_are_rejected(client, early_frame):
    """The core refuses to compare incomparable part specifications as peers."""
    altered = early_frame.copy()
    victim = sorted(altered["component_id"])[0]
    altered.loc[altered["component_id"] == victim, "profile_id"] = "SIM_X7R_1U_25V"

    response = client.post(
        "/api/v1/screen", files={"file": ("mlcc.csv", to_csv(altered), "text/csv")}
    )
    assert response.status_code == 422
    body = response.json()
    assert "Mixed profile_id" in body["message"]
    # A dataset-level rejection must not invent a row number.
    assert body["details"][0]["row"] is None


def test_renaming_the_family_does_not_make_the_model_apply(client, early_frame):
    """A CSV with the family renamed is not evidence the model generalises."""
    altered = early_frame.copy()
    altered["component_family"] = "Tantalum_Cap"
    response = client.post(
        "/api/v1/screen", files={"file": ("mlcc.csv", to_csv(altered), "text/csv")}
    )
    if response.status_code == 200:
        body = response.json()
        assert body["scored_record_count"] == 0
        assert body["unscored_record_count"] > 0
    else:
        assert response.status_code == 422


def test_lower_limit_is_rejected_not_screened_as_upper(client, early_frame):
    """A lower limit must never be quietly screened against the upper side."""
    altered = early_frame.copy()
    altered["lower_limit"] = "0.001"
    response = client.post(
        "/api/v1/screen", files={"file": ("mlcc.csv", to_csv(altered), "text/csv")}
    )
    assert response.status_code == 422
    body = response.json()
    assert body["error"] == "UNSUPPORTED_PROFILE"
    assert "two-sided" in body["message"]


def test_wrong_unit_is_rejected_without_conversion(client, early_frame):
    altered = early_frame.copy()
    altered["measurement_unit"] = "nA"
    response = client.post(
        "/api/v1/screen", files={"file": ("mlcc.csv", to_csv(altered), "text/csv")}
    )
    assert response.status_code == 422
    assert response.json()["error"] == "INCOMPATIBLE_UNITS"
    assert "does not convert units" in response.json()["message"]


def test_unsupported_as_of_hour_rejected(client, early_frame):
    response = client.post(
        "/api/v1/screen",
        files={"file": ("mlcc.csv", to_csv(early_frame), "text/csv")},
        data={"as_of_hour": "48"},
    )
    assert response.status_code == 422
    assert response.json()["error"] == "UNSUPPORTED_AS_OF_HOUR"


def test_missing_profile_id_column_warns_and_scores_nothing(client, early_frame):
    altered = early_frame.drop(columns=["profile_id"])
    response = client.post(
        "/api/v1/screen", files={"file": ("mlcc.csv", to_csv(altered), "text/csv")}
    )
    assert response.status_code == 200
    body = response.json()
    assert any(w["code"] == "PROFILE_ID_COLUMN_ABSENT" for w in body["warnings"])
    assert body["scored_record_count"] == 0


# --------------------------------------------------------------------------
# Peer context
# --------------------------------------------------------------------------


def test_peer_counts_are_reported_so_group_size_is_visible(client, early_frame):
    body = screen(client, early_frame)
    for record in body["records"]:
        assert record["peers"]["sample_size"] >= 1
        assert record["peers"]["current_batch_robust_z"] is not None


def test_small_batch_is_flagged_as_a_weak_peer_comparison(client, early_frame):
    """Peer statistics depend on batch composition; that must be visible."""
    smallest_batch = early_frame["batch_id"].iloc[0]
    subset = early_frame[early_frame["batch_id"] == smallest_batch]
    keep = sorted(subset["component_id"].unique())[:4]
    tiny = subset[subset["component_id"].isin(keep)]

    body = screen(client, tiny)
    for record in body["records"]:
        assert record["peers"]["sample_size"] <= 4
        assert record["peers"]["sufficient"] is False
        assert record["peers"]["warning"]


def test_peer_scores_depend_on_batch_composition(client, early_frame):
    """Documented behaviour: robust z is relative to the uploaded batch.

    Screening a component alongside a different set of peers can change its
    batch-relative score. The frontend must show group size for this reason.
    """
    full = screen(client, early_frame)

    # Drop half of one batch, so the survivors are compared against fewer peers.
    batch = early_frame["batch_id"].iloc[0]
    in_batch = sorted(early_frame.loc[early_frame["batch_id"] == batch, "component_id"].unique())
    dropped = set(in_batch[: len(in_batch) // 2])
    thinned = early_frame[~early_frame["component_id"].isin(dropped)]
    partial = screen(client, thinned)

    full_n = {r["component_id"]: r["peers"]["sample_size"] for r in full["records"]}
    partial_n = {r["component_id"]: r["peers"]["sample_size"] for r in partial["records"]}
    survivors = set(in_batch) - dropped
    assert survivors, "expected surviving components in the thinned batch"

    # The peer group really did shrink, and the response exposes both sizes so a
    # reader can see the comparison rests on a different group.
    assert all(partial_n[c] < full_n[c] for c in survivors)

    full_z = {r["component_id"]: r["peers"]["current_batch_robust_z"] for r in full["records"]}
    partial_z = {r["component_id"]: r["peers"]["current_batch_robust_z"] for r in partial["records"]}
    assert any(full_z[c] != partial_z[c] for c in survivors)


# --------------------------------------------------------------------------
# Outcome reveal: crossings must be computed, not assumed
# --------------------------------------------------------------------------


def test_outcome_crossings_are_computed_against_the_real_limit(
    client, early_frame, outcome_frame
):
    """The 168 h reveal must identify the components that actually breached.

    Regression: this field was previously hard-coded False, so every component
    looked like it stayed in spec no matter what it did at 168 h.
    """
    combined = pd.concat([early_frame, outcome_frame], ignore_index=True)
    body = screen(client, combined)

    evaluation = body["evaluation"]
    assert evaluation["kind"] == "observed_readings"
    outcomes = evaluation["outcomes"]
    assert outcomes

    # Independently work out who crossed, straight from the uploaded numbers.
    limits = {
        str(row.component_id): float(row.upper_limit)
        for row in early_frame.itertuples(index=False)
    }
    expected = {
        str(row.component_id)
        for row in outcome_frame.itertuples(index=False)
        if float(row.measurement_value) > limits[str(row.component_id)]
    }
    assert expected, "fixture must contain at least one genuine limit crossing"

    reported = {o["component_id"] for o in outcomes if o["crossed_applicable_limit"]}
    assert reported == expected

    for outcome in outcomes:
        assert outcome["applicable_limit"] == limits[outcome["component_id"]]
        assert outcome["crossed_applicable_limit"] == (
            outcome["observed_value"] > outcome["applicable_limit"]
        )


def test_outcome_crossing_is_null_when_the_limit_is_unknown(
    client, early_frame, outcome_frame
):
    """An unknown limit must not read as 'stayed within limit'."""
    combined = pd.concat([early_frame, outcome_frame], ignore_index=True)
    body = screen(client, combined)
    for outcome in body["evaluation"]["outcomes"]:
        # Every component here has a limit, so none may be null...
        assert outcome["crossed_applicable_limit"] is not None
        # ...and the field is nullable rather than defaulting to False.
    assert (
        OutcomeRecord.model_fields["crossed_applicable_limit"].annotation
        is not bool
    )
