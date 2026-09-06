from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from sih26170.mlcc_prototype import (
    FORECAST_COLUMNS, RESIDUAL_XGB_FEATURES, RESIDUAL_XGB_NAME, STRATIFIED_INTERVAL_METHOD,
    ResidualOverPersistenceXGB, conformal_radius, load_bundle, prepare_early_features,
    screen_readings, signed_conformal_bounds, stratified_interval_margins, train_bundle,
)


def make_split(prefix: str, batches: int = 8) -> tuple[pd.DataFrame, pd.DataFrame]:
    readings, labels = [], []
    for batch in range(batches):
        for index in range(12):
            identity = {"component_id": f"{prefix}_{batch}_{index}", "batch_id": f"{prefix}_{batch}", "component_family": "MLCC_X7R", "measurement_name": "leakage_ua"}
            initial = 0.1 + index * 0.02 + batch * 0.005
            current = initial + (index % 4) * 0.025
            final = current + (current - initial) * 4 + 0.01 * (index % 3)
            for hours, value in [(0, initial), (24, current)]:
                readings.append({**identity, "hours": hours, "measurement_value": value, "upper_limit": 0.7, "temperature_c": 125.0, "measurement_temperature_c": 25.0, "applied_voltage_v": 50.0, "rated_voltage_v": 50.0, "measurement_voltage_v": 50.0})
            labels.append({**identity, "final_value": final, "true_final_value": final, "is_future_failure": final >= 0.7, "is_observed_final_exceedance": final >= 0.7, "is_tester_fault": False, "scenario": "synthetic_fixture", "profile_id": "TEST"})
    return pd.DataFrame(readings), pd.DataFrame(labels)


@pytest.fixture(scope="module")
def trained_bundle(tmp_path_factory: pytest.TempPathFactory):
    pytest.importorskip("xgboost")
    pytest.importorskip("skops")
    directory = tmp_path_factory.mktemp("mlcc")
    for split in ("train", "calibration", "test"):
        readings, labels = make_split(split)
        readings.to_csv(directory / f"{split}_early.csv", index=False)
        labels.to_csv(directory / f"{split}_labels.csv", index=False)
    result = train_bundle(directory, directory / "bundle")
    return directory, load_bundle(directory / "bundle"), result


def test_future_and_truth_columns_cannot_affect_features() -> None:
    early, _ = make_split("safe", 2)
    expected, _, _ = prepare_early_features(early)
    future = early.loc[early.hours == 24].copy()
    future["hours"] = 168
    future["measurement_value"] = np.inf
    future["upper_limit"] = -1
    extended = pd.concat([early, future], ignore_index=True)
    extended["scenario"] = "secret"
    extended["is_future_failure"] = True
    actual, _, _ = prepare_early_features(extended)
    pd.testing.assert_frame_equal(actual[FORECAST_COLUMNS], expected[FORECAST_COLUMNS])
    assert "scenario" not in FORECAST_COLUMNS
    assert not set(FORECAST_COLUMNS) & {"component_id", "batch_id", "profile_id", "is_future_failure", "final_value"}


def test_exact_checkpoints_and_nonfinite_have_explicit_unscored_state() -> None:
    early, _ = make_split("bad", 1)
    early = early.loc[~((early.component_id == "bad_0_0") & (early.hours == 24))].copy()
    early.loc[(early.component_id == "bad_0_1") & (early.hours == 24), "measurement_value"] = np.inf
    features, _, unscored = prepare_early_features(early)
    assert len(features) == 10
    assert len(unscored) == 2
    assert all(record["predicted_final_value"] is None and record["status"] == "unscored" for record in unscored)


def test_invalid_units_profiles_and_duplicate_checkpoints_rejected() -> None:
    early, _ = make_split("bad", 1)
    early.loc[early.component_id == "bad_0_0", "component_family"] = "TANTALUM"
    early["unit"] = "uA"
    early.loc[early.component_id == "bad_0_1", "unit"] = "mA"
    early = pd.concat([early, early.loc[(early.component_id == "bad_0_2") & (early.hours == 24)]])
    features, _, unscored = prepare_early_features(early)
    assert len(features) == 9
    assert len(unscored) == 3


def test_conformal_uses_finite_sample_order_statistic() -> None:
    assert conformal_radius(np.arange(10.0), np.zeros(10), alpha=0.2) == 8.0
    with pytest.raises(ValueError, match="Too few"):
        conformal_radius(np.array([1.0]), np.array([0.0]))


def test_training_selection_is_batch_disjoint_and_native_xgb_persisted(trained_bundle) -> None:
    directory, bundle, result = trained_bundle
    selection = bundle.manifest["selection"]
    assert not set(selection["fit_batch_ids"]) & set(selection["validation_batch_ids"])
    assert all(batch.startswith("train_") for batch in selection["validation_batch_ids"])
    assert (directory / "bundle/xgboost.json").is_file()
    assert (directory / "bundle/xgboost_v2.ubj").is_file()
    assert set(result["test"]["models"]) == {"persistence", "linear_extrapolation", "ridge", "hist_gradient_boosting", "xgboost", "xgboost_v2"}


def test_reloaded_inference_never_fits_and_future_reveal_does_not_change_results(trained_bundle, monkeypatch) -> None:
    directory, bundle, _ = trained_bundle
    early, labels = make_split("inference", 2)
    def prohibited(*args, **kwargs):
        raise AssertionError("Inference attempted to fit")
    monkeypatch.setattr(bundle.detector, "fit", prohibited)
    monkeypatch.setattr(bundle.imputer, "fit", prohibited)
    for model in bundle.models.values():
        monkeypatch.setattr(model, "fit", prohibited)
    first = screen_readings(early, bundle)
    second = screen_readings(early, load_bundle(directory / "bundle"), future_outcomes=labels)
    assert first["records"] == second["records"]
    assert first["summary"] == second["summary"]
    assert "future_outcomes" not in first
    assert len(second["simulation_truth"]) == 24
    json.dumps(first, allow_nan=False)
    assert first["metadata"]["model_fitted_during_request"] is False
    assert all(record["prediction_lower"] <= record["predicted_final_value"] <= record["prediction_upper"] for record in first["records"])


def test_inference_preserves_valid_subset_and_warns_outside_training_conditions(trained_bundle) -> None:
    _, bundle, _ = trained_bundle
    early, _ = make_split("subset", 1)
    early.loc[early.component_id == "subset_0_0", "measurement_value"] = np.nan
    early["measurement_temperature_c"] = 45
    result = screen_readings(early, bundle)
    assert result["summary"]["unscored_count"] == 1
    abnormal = next(record for record in result["records"] if record["component_id"] == "subset_0_1")
    assert abnormal["prediction_readiness"] == "outside_training_conditions"
    assert "measurement_temperature_c" in abnormal["out_of_training_range_features"]


def test_artifact_corruption_rejected_before_deserialization(trained_bundle, tmp_path: Path) -> None:
    import shutil
    directory, _, _ = trained_bundle
    target = tmp_path / "corrupt"
    shutil.copytree(directory / "bundle", target)
    (target / "xgboost.json").write_text("{}")
    with pytest.raises(ValueError, match="integrity"):
        load_bundle(target)


def test_only_trained_as_of_hour_is_accepted() -> None:
    early, _ = make_split("asof", 1)
    with pytest.raises(ValueError, match="24 only"):
        prepare_early_features(early, as_of_hour=96)


def test_mixed_profile_batch_and_supplied_invalid_metadata() -> None:
    early, _ = make_split("mixed", 1)
    early["profile_id"] = "PROFILE_A"
    early.loc[early.component_id == "mixed_0_0", "profile_id"] = "PROFILE_B"
    with pytest.raises(ValueError, match="Mixed profile_id"):
        prepare_early_features(early)
    early["profile_id"] = "PROFILE_A"
    early.loc[early.component_id == "mixed_0_0", "measurement_voltage_v"] = np.inf
    features, _, unscored = prepare_early_features(early)
    assert len(features) == 11 and len(unscored) == 1


def test_future_measured_reveal_preserves_values_and_identity(trained_bundle) -> None:
    _, bundle, _ = trained_bundle
    early, _ = make_split("reveal", 1)
    future = early.loc[early.hours == 24].copy()
    future["hours"] = 168
    future["measurement_value"] *= 2
    first = screen_readings(early, bundle)
    revealed = screen_readings(early.sample(frac=1, random_state=4), bundle, future_outcomes=future)
    assert sorted(first["records"], key=lambda row: row["component_id"]) == sorted(revealed["records"], key=lambda row: row["component_id"])
    assert len(revealed["future_outcomes"]) == 12
    assert all(row["hours"] == 168 for row in revealed["future_outcomes"])
    assert "simulation_truth" not in revealed


def test_lower_limit_profile_is_not_silently_scored() -> None:
    early, _ = make_split("lower", 1)
    early["lower_limit"] = 0.01
    features, _, unscored = prepare_early_features(early)
    assert features.empty and len(unscored) == 12


def test_explicit_xgboost_candidate_preserves_validation_winner_and_explains(trained_bundle) -> None:
    _, bundle, _ = trained_bundle
    early, _ = make_split("xgb", 1)
    response = screen_readings(early, bundle, forecast_model="xgboost")
    assert response["metadata"]["selected_model"] == "xgboost"
    assert response["metadata"]["validation_winner"] == bundle.selected_model
    assert all(record["forecast_model"] == "xgboost" for record in response["records"])
    assert len(response["records"][0]["xgboost_explanation"]["top_contributions"]) == 5


def test_v2_residual_model_uses_persistence_margin_and_persists_natively(trained_bundle, tmp_path: Path) -> None:
    directory, bundle, result = trained_bundle
    model = bundle.models[RESIDUAL_XGB_NAME]
    assert isinstance(model, ResidualOverPersistenceXGB)
    early, _ = make_split("v2", 1)
    features, _, _ = prepare_early_features(early)
    matrix = bundle.imputer.transform(features[FORECAST_COLUMNS])
    predicted = model.predict(matrix)
    # margin + trees: contributions (incl. bias) sum to the raw prediction
    contributions = model.contributions(matrix)
    np.testing.assert_allclose(contributions.sum(axis=1), predicted, rtol=1e-5, atol=1e-6)
    # only the leakage-only columns can matter: perturbing an excluded column changes nothing
    perturbed = matrix.copy()
    for column in ("prior_storage_humidity_pct", "measurement_voltage_v", "capacitance_change_fraction"):
        perturbed[:, FORECAST_COLUMNS.index(column)] += 123.0
    np.testing.assert_allclose(model.predict(perturbed), predicted)
    # native reload gives identical predictions
    model.save_model(tmp_path / "m.ubj")
    np.testing.assert_allclose(ResidualOverPersistenceXGB.load(tmp_path / "m.ubj").predict(matrix), predicted)
    assert bundle.manifest["forecast_v2"]["features"] == RESIDUAL_XGB_FEATURES
    assert bundle.manifest["interval"]["stratified"]["model"] == RESIDUAL_XGB_NAME
    assert set(bundle.manifest["interval"]["stratified"]["margins"]) == {"0", "1", "2"}


def test_v2_forecast_gets_stratified_asymmetric_interval_and_explanation(trained_bundle) -> None:
    _, bundle, _ = trained_bundle
    early, _ = make_split("v2s", 1)
    response = screen_readings(early, bundle, forecast_model=RESIDUAL_XGB_NAME)
    assert response["metadata"]["selected_model"] == RESIDUAL_XGB_NAME
    margins = bundle.manifest["interval"]["stratified"]["margins"]
    for record in response["records"]:
        assert record["forecast_model"] == RESIDUAL_XGB_NAME
        assert record["interval_method"] == STRATIFIED_INTERVAL_METHOD
        assert record["interval_stratum"].startswith("slope_z_stratum_")
        stratum = margins[record["interval_stratum"].rsplit("_", 1)[1]]
        limit = record["safety_limit"]
        normalized = record["predicted_final_value"] / limit
        assert record["prediction_lower"] == pytest.approx(max(normalized + stratum["lower"], 0.0) * limit)
        assert record["prediction_upper"] == pytest.approx((normalized + stratum["upper"]) * limit)
        assert record["prediction_upper_two_sided"] == pytest.approx((normalized + stratum["upper_two_sided"]) * limit)
        assert record["prediction_lower_two_sided"] <= record["prediction_lower"] <= record["predicted_final_value"] <= record["prediction_upper"] <= record["prediction_upper_two_sided"]
        assert record["interval_nominal_coverage"] == pytest.approx(0.8) and record["upper_bound_nominal_level"] == pytest.approx(0.9)
        assert record["xgboost_explanation"]["is_active_forecast"] is True
        assert record["xgboost_explanation"]["explained_model"] == RESIDUAL_XGB_NAME
        assert {item["feature"] for item in record["xgboost_explanation"]["top_contributions"]} <= set(RESIDUAL_XGB_FEATURES)
    # v1 models keep the symmetric radius and the v1 explanation
    legacy = screen_readings(early, bundle, forecast_model="persistence")
    assert all(r["interval_method"] == "split_conformal_absolute_residual" and r["interval_stratum"] is None for r in legacy["records"])
    assert all(r["xgboost_explanation"]["explained_model"] == "xgboost" and r["xgboost_explanation"]["is_active_forecast"] is False for r in legacy["records"])
    json.dumps(response, allow_nan=False)


def test_signed_conformal_bounds_and_pooled_fallback() -> None:
    residuals = np.arange(1, 40, dtype=float) - 20  # -19..19, n=39
    bounds = signed_conformal_bounds(residuals, 0.2)
    # ranks: two-sided floor(40*0.1)=4 / ceil(40*0.9)=36; one-sided floor(40*0.2)=8 / ceil(40*0.8)=32
    assert bounds == {"lower_two_sided": -16.0, "upper_two_sided": 16.0, "lower": -12.0, "upper": 12.0}
    margins = stratified_interval_margins(residuals, np.full(39, 0.0), 0.2)
    assert margins["0"]["pooled_fallback"] is False and margins["1"]["pooled_fallback"] is True
    assert margins["1"]["lower"] == bounds["lower"] and margins["2"]["upper_two_sided"] == bounds["upper_two_sided"]
    with pytest.raises(ValueError, match="Too few"):
        signed_conformal_bounds(np.array([1.0, 2.0]), 0.05)


def test_v1_bundle_without_v2_model_still_loads(trained_bundle, tmp_path: Path) -> None:
    import shutil
    directory, _, _ = trained_bundle
    target = tmp_path / "legacy"
    shutil.copytree(directory / "bundle", target)
    manifest = json.loads((target / "manifest.json").read_text())
    manifest["prototype_version"] = "mlcc-pilot-1.0"
    manifest["artifact_sha256"].pop("xgboost_v2.ubj")
    manifest["interval"].pop("stratified")
    (target / "xgboost_v2.ubj").unlink()
    (target / "manifest.json").write_text(json.dumps(manifest))
    legacy = load_bundle(target)
    assert RESIDUAL_XGB_NAME not in legacy.models
    early, _ = make_split("legacy", 1)
    assert screen_readings(early, legacy, forecast_model="xgboost")["metadata"]["selected_model"] == "xgboost"
