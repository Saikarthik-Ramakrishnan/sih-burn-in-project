"""Tests for the Claude v2 forecasting candidate (small synthetic fixture, fast)."""

from __future__ import annotations

import dataclasses
import hashlib
import importlib.metadata
import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("xgboost")

from sih26170 import forecast_v2 as fv2  # noqa: E402


PROFILES = {
    "P_A": {"upper_limit": 0.25, "nominal_capacitance_nf": 100.0, "rated_voltage_v": 50.0},
    "P_B": {"upper_limit": 1.3, "nominal_capacitance_nf": 4700.0, "rated_voltage_v": 16.0},
}


def make_fixture(n_batches: int = 10, parts_per_batch: int = 16, seed: int = 3, with_future: bool = False) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Deterministic long-format 0/24 h readings plus labels for whole-batch tests."""
    rng = np.random.default_rng(seed)
    readings, labels = [], []
    for b in range(n_batches):
        profile = list(PROFILES)[b % len(PROFILES)]
        spec = PROFILES[profile]
        limit = spec["upper_limit"]
        for i in range(parts_per_batch):
            identity = {"component_id": f"C{b:02d}_{i:03d}", "batch_id": f"B{b:02d}", "component_family": "MLCC_X7R", "measurement_name": "leakage_ua"}
            initial = limit * rng.uniform(0.08, 0.15)
            drifting = i % 5 == 0
            current = initial * (1.6 if drifting else rng.uniform(0.95, 1.02))
            final = current + (current - initial) * 5.0 if drifting else current * rng.uniform(0.97, 1.0)
            meta = {"upper_limit": limit, "profile_id": profile, "nominal_capacitance_nf": spec["nominal_capacitance_nf"], "rated_voltage_v": spec["rated_voltage_v"], "applied_voltage_v": spec["rated_voltage_v"] * 0.9, "measurement_voltage_v": spec["rated_voltage_v"], "temperature_c": 125.0, "measurement_temperature_c": 25.0, "prior_storage_humidity_pct": rng.uniform(30, 60), "tester_id": "T1", "tester_channel": 1 + (i % 2)}
            for hours, value in ((0, initial), (24, current)):
                readings.append({**identity, **meta, "hours": hours, "measurement_value": value, "capacitance_nf": spec["nominal_capacitance_nf"] * rng.uniform(0.97, 1.0), "dissipation_factor_pct": rng.uniform(0.5, 0.9)})
            if with_future:
                for hours, value in ((96, final * 0.9), (168, final)):
                    readings.append({**identity, **meta, "hours": hours, "measurement_value": value, "capacitance_nf": spec["nominal_capacitance_nf"], "dissipation_factor_pct": 0.7})
            labels.append({**identity, "profile_id": profile, "final_value": final, "true_final_value": final, "is_future_failure": final >= limit, "is_observed_final_exceedance": final >= limit, "is_tester_fault": False, "is_defect": drifting, "is_healthy": not drifting, "scenario": "fixture_drift" if drifting else "fixture_healthy", "upper_limit": limit, "anomaly_onset_hour": (12.0 if i % 2 else 48.0) if drifting else np.nan, "tester_fault_onset_hour": np.nan})
    return pd.DataFrame(readings), pd.DataFrame(labels)


@pytest.fixture(scope="module")
def pack(tmp_path_factory: pytest.TempPathFactory) -> Path:
    directory = tmp_path_factory.mktemp("pack")
    early, labels = make_fixture()
    early.to_csv(directory / "train_early.csv", index=False)
    labels.to_csv(directory / "train_labels.csv", index=False)
    return directory


@pytest.fixture(scope="module")
def training(pack: Path) -> fv2.TrainingData:
    return fv2.load_training_data(pack)


@pytest.fixture(scope="module")
def configs() -> list[fv2.CandidateConfig]:
    return [
        fv2.CandidateConfig("persistence", "persistence"),
        fv2.CandidateConfig("linear_extrapolation", "linear_extrapolation"),
        fv2.CandidateConfig("xgb_abs_resid", "xgboost", target="residual_over_persistence", feature_set="leakage_plus_channel_peer", objective="reg:absoluteerror", params={"n_estimators": 40}),
        fv2.CandidateConfig("xgb_log1p", "xgboost", target="log1p_normalized", feature_set="leakage_only", objective="reg:squarederror", params={"n_estimators": 40}),
    ]


@pytest.fixture(scope="module")
def aux_config() -> fv2.CandidateConfig:
    return fv2.CandidateConfig("xgb_abs_resid_aux_small", "xgboost", target="residual_over_persistence", feature_set="leakage_plus_aux", objective="reg:absoluteerror", params={"n_estimators": 30})


@pytest.fixture(scope="module")
def aux_candidate(training: fv2.TrainingData, aux_config: fv2.CandidateConfig) -> fv2.ForecastCandidate:
    return fv2.fit_final_candidate(training, aux_config, seed=17, n_jobs=1)


@pytest.fixture(scope="module")
def saved_candidate(training: fv2.TrainingData, configs: list[fv2.CandidateConfig], tmp_path_factory: pytest.TempPathFactory) -> Path:
    candidate = fv2.fit_final_candidate(training, configs[2], seed=1, n_jobs=1)
    return fv2.save_forecast_candidate(candidate, tmp_path_factory.mktemp("candidate") / "xgb_abs_resid")


# --------------------------------------------------------------------------- #
# Data loading and target definition
# --------------------------------------------------------------------------- #
def test_training_data_joins_on_identity_not_row_order(pack: Path, training: fv2.TrainingData) -> None:
    labels = pd.read_csv(pack / "train_labels.csv", dtype={c: str for c in fv2.IDENTITY})
    shuffled = labels.sample(frac=1.0, random_state=9)
    shuffled.to_csv(pack / "train_labels.csv", index=False)
    reloaded = fv2.load_training_data(pack)
    pd.testing.assert_frame_equal(reloaded.labels, training.labels)
    assert (reloaded.features[fv2.IDENTITY].to_numpy() == reloaded.labels[fv2.IDENTITY].to_numpy()).all()


def test_target_is_final_value_over_upper_limit(training: fv2.TrainingData) -> None:
    expected = training.labels["final_value"].to_numpy() / training.features["upper_limit"].to_numpy()
    np.testing.assert_allclose(training.y, expected)
    assert training.validation["components"] == 160
    assert training.validation["batches"] == 10
    assert set(training.validation["profiles"]) == set(PROFILES)


def test_predictions_convert_back_to_microamps(training: fv2.TrainingData, configs: list[fv2.CandidateConfig], saved_candidate: Path) -> None:
    fitted = fv2.fit_model(configs[0], training.features, training.y, seed=1)
    normalized = fitted.predict_normalized(training.features)
    np.testing.assert_allclose(normalized * training.limits, training.features["current_value"].to_numpy())
    # the two fixture profiles have different limits (0.25 vs 1.3 uA): the same normalized
    # forecast must map to different microamp values, and the candidate output must use
    # the per-component limit rather than a global one
    candidate = fv2.load_forecast_candidate(saved_candidate)
    early, _ = make_fixture(n_batches=2, seed=5)
    out = candidate.predict(early)
    limits = early.drop_duplicates("component_id").set_index("component_id")["upper_limit"]
    np.testing.assert_allclose(out["upper_limit"], out["component_id"].map(limits))
    np.testing.assert_allclose(out["predicted_final_value"], out["predicted_normalized"] * out["component_id"].map(limits))
    np.testing.assert_allclose(out["persistence_final_value"], out["value_at_24h"])
    manual = candidate._fitted().predict_normalized(fv2.augment_features(*fv2.prepare_early_features(early)[:2]).sort_values(fv2.SORT_KEYS))
    np.testing.assert_allclose(out["predicted_normalized"], manual)
    assert set(out["upper_limit"].round(6)) == {0.25, 1.3}


def test_feature_sets_contain_no_identifiers_or_labels() -> None:
    forbidden = {"component_id", "batch_id", "profile_id", "part_number", "scenario", "final_value", "true_final_value", "is_future_failure", "is_observed_final_exceedance", "anomaly_onset_hour", "tester_fault_onset_hour", "tester_id", "tester_channel", "board_position", "insulation_resistance_gohm"}
    for name, columns in fv2.FEATURE_SETS.items():
        assert not forbidden & set(columns), name
    for config in fv2.PREDECLARED_CONFIGS:
        assert config.feature_set in fv2.FEATURE_SETS
    # documented design decision: batch-constant condition columns and raw humidity (a partial lot
    # identifier) stay out of every v2 feature set; only the v1 replica keeps the condition columns
    for name, columns in fv2.FEATURE_SETS.items():
        if name != "v1_all":
            assert "prior_storage_humidity_pct" not in columns, name
            assert not set(fv2.CONDITION_FEATURES) & set(columns), name
    assert set(fv2.CONDITION_FEATURES) <= set(fv2.FEATURE_SETS["v1_all"])  # the replica really is v1
    assert len(fv2.PREDECLARED_CONFIGS) <= 12
    assert len({c.name for c in fv2.PREDECLARED_CONFIGS}) == len(fv2.PREDECLARED_CONFIGS)


# --------------------------------------------------------------------------- #
# Folds and leakage
# --------------------------------------------------------------------------- #
def test_folds_hold_out_whole_batches_and_cover_every_profile(training: fv2.TrainingData) -> None:
    folds = fv2.assign_batch_folds(training.features, n_splits=5)
    assert folds["batch_id"].is_unique and set(folds["fold"]) == set(range(5))
    fv2.assert_folds_disjoint(training.features, folds)
    for k, train_mask, valid_mask in fv2.fold_masks(training.features, folds):
        assert not set(training.features.loc[train_mask, "batch_id"]) & set(training.features.loc[valid_mask, "batch_id"])
        assert not set(training.features.loc[train_mask, "component_id"]) & set(training.features.loc[valid_mask, "component_id"])
        assert set(training.features.loc[valid_mask, "profile_id"]) == set(PROFILES)
    # deterministic
    pd.testing.assert_frame_equal(folds, fv2.assign_batch_folds(training.features, n_splits=5))
    # every training batch appears exactly once, and no fold is empty, for several split counts
    for n_splits in (2, 4, 5):
        assignment = fv2.assign_batch_folds(training.features, n_splits=n_splits)
        assert set(assignment["batch_id"]) == set(training.features["batch_id"])
        assert (assignment["batch_id"].value_counts() == 1).all()
        assert set(assignment["fold"]) == set(range(n_splits))
        per_fold = assignment.groupby("fold")["profile_id"].agg(lambda s: set(s))
        assert all(profiles == set(PROFILES) for profiles in per_fold), per_fold.to_dict()
        assert assignment.groupby("fold").size().max() - assignment.groupby("fold").size().min() <= 1
    # without profile_id the assignment still covers every batch exactly once
    plain = fv2.assign_batch_folds(training.features.drop(columns=["profile_id"]), n_splits=4)
    assert set(plain["batch_id"]) == set(training.features["batch_id"]) and plain["batch_id"].is_unique
    with pytest.raises(ValueError):
        fv2.assign_batch_folds(training.features, n_splits=11)  # more folds than batches


def test_component_shared_across_folds_is_rejected(training: fv2.TrainingData) -> None:
    folds = fv2.assign_batch_folds(training.features, n_splits=5)
    mapping = folds.set_index("batch_id")["fold"]
    first = training.features.iloc[[0]].copy()
    other_fold_batch = folds.loc[folds["fold"] != mapping[first["batch_id"].iloc[0]], "batch_id"].iloc[0]
    duplicate = first.copy()
    duplicate["batch_id"] = other_fold_batch  # same component now appears in a batch of another fold
    with pytest.raises(ValueError, match="shares"):
        fv2.assert_folds_disjoint(pd.concat([training.features, duplicate], ignore_index=True), folds)
    # an unassigned batch is rejected too
    stray = first.copy(); stray["batch_id"] = "B_UNASSIGNED"; stray["component_id"] = "STRAY"
    with pytest.raises(ValueError, match="fold assignment"):
        fv2.assert_folds_disjoint(pd.concat([training.features, stray], ignore_index=True), folds)


def test_future_observations_and_label_columns_cannot_change_predictions(saved_candidate: Path, aux_candidate: fv2.ForecastCandidate, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Both the channel-peer candidate and the aux candidate (which reads capacitance,
    dissipation factor and humidity) must ignore 96/168 h rows entirely, whatever they carry."""
    early, _ = make_fixture(n_batches=2, with_future=False, seed=11)
    with_future, _ = make_fixture(n_batches=2, with_future=True, seed=11)
    with_future = with_future.copy()
    late = with_future["hours"] >= 96
    assert late.sum() == 2 * early["component_id"].nunique()
    with_future.loc[late, "measurement_value"] *= 50          # wildly different late readings
    with_future.loc[late, "capacitance_nf"] *= 0.1            # aux columns differ on the late rows too
    with_future.loc[late, "dissipation_factor_pct"] = 99.0
    with_future.loc[late, "prior_storage_humidity_pct"] = 1000.0
    with_future["scenario"] = "secret"
    with_future["final_value"] = 999.0
    with_future["is_future_failure"] = True
    nan_future = with_future.copy()
    nan_future.loc[late, ["measurement_value", "capacitance_nf", "dissipation_factor_pct"]] = np.nan
    for candidate in (fv2.load_forecast_candidate(saved_candidate), aux_candidate):
        base = candidate.predict(early)
        assert (base["status"] == fv2.FORECAST_STATUS).all()
        pd.testing.assert_frame_equal(base, candidate.predict(with_future))
        pd.testing.assert_frame_equal(base, candidate.predict(nan_future))
        # a change to the 24 h reading itself DOES move the forecast, so the comparison has power
        moved = early.copy()
        moved.loc[moved["hours"] == 24, "measurement_value"] *= 1.5
        assert not np.allclose(base["predicted_normalized"], candidate.predict(moved)["predicted_normalized"])
    # stronger than comparing forecasts (a tree may never split on a leaked column): the design
    # matrix the aux booster receives must be identical with and without the late rows
    spied = fv2.load_forecast_candidate(fv2.save_forecast_candidate(aux_candidate, tmp_path / "aux_spy"))
    captured: list[np.ndarray] = []
    original_predict = spied.booster.predict
    monkeypatch.setattr(spied.booster, "predict", lambda X, *a, **k: (captured.append(np.array(X, dtype=float, copy=True)), original_predict(X, *a, **k))[1])
    spied.predict(early); spied.predict(with_future); spied.predict(nan_future)
    assert len(captured) == 3 and captured[0].shape[1] == len(fv2.FEATURE_SETS["leakage_plus_aux"])
    np.testing.assert_array_equal(captured[0], captured[1])
    np.testing.assert_array_equal(captured[0], captured[2])


def test_cross_validation_predictions_are_out_of_fold(training: fv2.TrainingData, configs: list[fv2.CandidateConfig]) -> None:
    folds = fv2.assign_batch_folds(training.features, n_splits=5)
    results, oof = fv2.run_cross_validation(training, configs, folds, seed=1, n_jobs=1)
    mapping = folds.set_index("batch_id")["fold"]
    assert (oof["batch_id"].map(mapping) == oof["fold"]).all()
    assert len(oof) == len(configs) * len(training.features)
    assert not oof.duplicated(["config"] + fv2.IDENTITY).any()
    # a heldout prediction must equal what a model fitted on the OTHER folds only produces.
    # The masks are built here from the fold table on purpose (not via fold_masks) so a
    # leak inside the module's own mask logic cannot hide by leaking identically.
    k = 1
    valid_mask = training.features["batch_id"].isin(folds.loc[folds["fold"] == k, "batch_id"]).to_numpy()
    train_mask = ~valid_mask
    assert valid_mask.sum() and not set(training.features.loc[train_mask, "batch_id"]) & set(training.features.loc[valid_mask, "batch_id"])
    refit = fv2.fit_model(configs[2], training.features.loc[train_mask].reset_index(drop=True), training.y[train_mask], seed=1, n_jobs=1)
    expected = refit.predict_normalized(training.features.loc[valid_mask].reset_index(drop=True))
    got = oof.loc[(oof["config"] == configs[2].name) & (oof["fold"] == k)].set_index("component_id")["predicted_normalized"]
    np.testing.assert_allclose(got.loc[training.features.loc[valid_mask, "component_id"]].to_numpy(), expected)
    np.testing.assert_allclose(oof["predicted_final_value_ua"], oof["predicted_normalized"] * oof["upper_limit"])
    assert set(oof["config"]) == {c.name for c in configs}
    for config in configs:
        entry = results["configs"][config.name]
        assert entry["fold_summary"]["folds"] == 5
        assert entry["pooled"]["components"] == len(training.features)
        assert set(entry["pooled"]["by_profile"]) == set(PROFILES)
    table = fv2.comparison_table(results)
    assert list(table.columns[:1]) == ["config"] and len(table) == len(configs)
    # persistence must be exact on the fixture's healthy parts by construction? (No: healthy parts settle a few percent.) Just check finite.
    assert np.isfinite(table["mae_norm_pooled"]).all()


def test_residual_target_uses_base_margin_consistently(training: fv2.TrainingData, configs: list[fv2.CandidateConfig]) -> None:
    fitted = fv2.fit_model(configs[2], training.features, training.y, seed=1, n_jobs=1)
    matrix = fv2.impute(fv2.feature_matrix(training.features, configs[2].feature_columns), fitted.medians)
    margin = fv2.persistence_forecast(training.features)
    expected = np.maximum(fitted.booster.predict(matrix, base_margin=margin), 0.0)
    np.testing.assert_allclose(fitted.predict_normalized(training.features), expected)
    without_margin = np.maximum(fitted.booster.predict(matrix), 0.0)
    assert not np.allclose(without_margin, expected)  # the margin matters; predict() must always supply it


def test_log1p_target_round_trips() -> None:
    y = np.array([0.0, 0.1, 1.5, 6.0])
    label, margin = fv2.target_encoding(y, np.full(4, 0.2), "log1p_normalized")
    assert margin is None
    np.testing.assert_allclose(fv2.decode_prediction(label, "log1p_normalized"), y)
    label, margin = fv2.target_encoding(y, np.full(4, 0.2), "log1p_residual_over_persistence")
    np.testing.assert_allclose(margin, np.log1p(0.2))
    assert (fv2.decode_prediction(np.array([-3.0, 0.5]), "normalized") >= 0).all()


# --------------------------------------------------------------------------- #
# Candidate save / load / predict
# --------------------------------------------------------------------------- #
def test_saved_candidate_reloads_and_matches(training: fv2.TrainingData, configs: list[fv2.CandidateConfig], saved_candidate: Path) -> None:
    manifest = json.loads((saved_candidate / "manifest.json").read_text())
    assert manifest["candidate_version"] == fv2.VERSION
    assert manifest["config"]["name"] == "xgb_abs_resid"
    assert manifest["feature_columns"] == configs[2].feature_columns
    assert set(manifest["imputation_medians"]) == set(configs[2].feature_columns)
    assert manifest["target"]["base_margin_required_at_predict"] is True
    assert set(manifest["artifact_sha256"]) == {"model.ubj", "model.json"}
    assert manifest["supported_profiles"] == sorted(PROFILES)
    candidate = fv2.load_forecast_candidate(saved_candidate)
    early, _ = make_fixture(n_batches=2, seed=5)
    fresh = fv2.fit_final_candidate(training, configs[2], seed=1, n_jobs=1)
    pd.testing.assert_frame_equal(candidate.predict(early), fresh.predict(early))


def test_tampered_artifact_is_rejected(saved_candidate: Path, tmp_path: Path) -> None:
    import shutil

    copy = tmp_path / "tampered"
    shutil.copytree(saved_candidate, copy)
    (copy / "model.ubj").write_bytes(b"\x00" + (copy / "model.ubj").read_bytes()[1:])
    with pytest.raises(ValueError, match="integrity"):
        fv2.load_forecast_candidate(copy)


def test_predict_is_invariant_to_input_order_and_keeps_identity(saved_candidate: Path) -> None:
    candidate = fv2.load_forecast_candidate(saved_candidate)
    early, _ = make_fixture(n_batches=3, seed=7)
    a = candidate.predict(early)
    b = candidate.predict(early.sample(frac=1.0, random_state=2).reset_index(drop=True))
    pd.testing.assert_frame_equal(a, b)
    assert list(a.columns) == fv2.OUTPUT_COLUMNS
    assert len(a) == early["component_id"].nunique()
    assert (a["target_hour"] == 168.0).all() and (a["as_of_hour"] == 24.0).all() and (a["unit"] == "uA").all()
    assert a["component_id"].is_unique
    np.testing.assert_allclose(a["predicted_final_value"], a["predicted_normalized"] * a["upper_limit"])
    assert (a["predicted_final_value"] >= 0).all()


def test_predict_returns_unavailable_status_for_invalid_components(saved_candidate: Path) -> None:
    candidate = fv2.load_forecast_candidate(saved_candidate)
    early, _ = make_fixture(n_batches=1, seed=8)
    ids = sorted(early["component_id"].unique())
    early = early.loc[~((early["component_id"] == ids[0]) & (early["hours"] == 24))]           # missing 24 h checkpoint
    early.loc[(early["component_id"] == ids[1]) & (early["hours"] == 0), "measurement_value"] = np.nan  # nonfinite reading
    early.loc[early["component_id"] == ids[2], "component_family"] = "TANTALUM"                  # unsupported family
    out = candidate.predict(early)
    assert len(out) == len(ids)
    unavailable = out.loc[out["status"] == fv2.UNAVAILABLE_STATUS]
    assert set(unavailable["component_id"]) == set(ids[:3])
    assert unavailable["predicted_final_value"].isna().all()
    assert unavailable["unavailable_reason"].str.len().gt(0).all()
    assert (out.loc[out["status"] == fv2.FORECAST_STATUS, "predicted_final_value"] > 0).all()


def test_unsupported_profile_is_unavailable(saved_candidate: Path) -> None:
    candidate = fv2.load_forecast_candidate(saved_candidate)
    early, _ = make_fixture(n_batches=1, seed=8)
    early["profile_id"] = "UNKNOWN_PROFILE"
    out = candidate.predict(early)
    assert (out["status"] == fv2.UNAVAILABLE_STATUS).all()
    assert out["unavailable_reason"].str.contains("profile").all()


def test_predict_does_not_fit_or_touch_labels(saved_candidate: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    candidate = fv2.load_forecast_candidate(saved_candidate)
    from xgboost import XGBRegressor

    def forbidden(*args, **kwargs):  # pragma: no cover - only runs on failure
        raise AssertionError("fit was called during predict")

    monkeypatch.setattr(XGBRegressor, "fit", forbidden)
    monkeypatch.setattr(fv2, "fit_model", forbidden)
    monkeypatch.setattr(fv2, "fit_medians", forbidden)
    early, _ = make_fixture(n_batches=2, seed=4)
    before = json.dumps(candidate.manifest, sort_keys=True)
    out = candidate.predict(early)
    assert len(out) == early["component_id"].nunique()
    assert json.dumps(candidate.manifest, sort_keys=True) == before
    assert "final_value" not in out.columns and "scenario" not in out.columns


def test_interval_experiment_uses_nested_calibration(training: fv2.TrainingData, configs: list[fv2.CandidateConfig]) -> None:
    folds = fv2.assign_batch_folds(training.features, n_splits=4)
    report = fv2.run_interval_experiment(training, configs[0], folds, alpha=0.2, calibration_batches_per_profile=1, seed=1, n_jobs=1, quantile_params={"n_estimators": 30})
    for entry in report["calibration_log"]:
        fold = entry["fold"]
        validation_batches = set(folds.loc[folds["fold"] == fold, "batch_id"])
        assert not set(entry["calibration_batches"]) & validation_batches
        assert entry["fit_batches"] + len(entry["calibration_batches"]) == len(folds) - len(validation_batches)
        train_features = training.features.loc[~training.features["batch_id"].isin(validation_batches)]
        assert entry["calibration_batches"] == fv2.choose_calibration_batches(train_features, per_profile=1, rotation=fold)
    assert len({tuple(e["calibration_batches"]) for e in report["calibration_log"]}) > 1  # not the same batches in every fold
    for method in ("symmetric_absolute", "asymmetric_signed", "stratified_asymmetric_signed", "stratified_one_sided_upper", "cqr_quantile_xgboost"):
        summary = report["methods"][method]
        assert 0.0 <= summary["coverage_mean"] <= 1.0
        assert 0.0 <= summary["per_batch_coverage_min"] <= summary["per_batch_coverage_max"] <= 1.0
        assert len(summary["per_fold"]) == 4
    assert report["methods"]["stratified_one_sided_upper"]["upper_only_coverage_mean"] == report["methods"]["stratified_one_sided_upper"]["coverage_mean"]


def test_conformal_quantiles_use_finite_sample_rank() -> None:
    residuals = np.arange(1, 20, dtype=float)  # 19 values
    assert fv2.conformal_radius(residuals, 0.1) == 18.0  # ceil(20*0.9)=18th order statistic
    lower, upper = fv2.signed_conformal_bounds(residuals - 10, 0.2)
    assert lower == -8.0 and upper == 8.0
    with pytest.raises(ValueError):
        fv2.conformal_radius(np.array([1.0, 2.0]), 0.01)


def test_v2_features_use_only_same_upload_peers_and_no_channel_identity(training: fv2.TrainingData) -> None:
    features = training.features
    assert set(fv2.CHANNEL_PEER_FEATURES) <= set(features.columns)
    assert "tester_channel" not in fv2.FEATURE_SETS["leakage_plus_channel_peer"]
    # humidity rank is a within-batch percentile: max per batch is 1, min ~ 1/n
    rank = features.groupby("batch_id")["prior_storage_humidity_batch_rank_v2"]
    assert np.allclose(rank.max(), 1.0) and (rank.min() > 0).all()
    # channel peers: fixture has 8 parts per channel per batch -> 7 peers >= MIN_CHANNEL_PEERS, so finite
    assert np.isfinite(features["channel_peer_median_current_z_v2"]).all()
    assert features["channel_peer_elevated_fraction_v2"].between(0, 1).all()
    # leave-one-out: recompute one value by hand
    row = features.iloc[0]
    early, _ = make_fixture()
    channel = early.loc[early["component_id"] == row["component_id"], "tester_channel"].iloc[0]
    same = early.loc[(early["batch_id"] == row["batch_id"]) & (early["tester_channel"] == channel), "component_id"].unique()
    peers = features.loc[features["component_id"].isin(same) & (features["component_id"] != row["component_id"]), "current_batch_robust_z"]
    assert np.isclose(row["channel_peer_median_current_z_v2"], peers.median())
    # too few channel peers -> NaN, later median-imputed (no crash)
    small_early, _ = make_fixture(n_batches=1, parts_per_batch=6, seed=2)
    feats, validated, _ = fv2.prepare_early_features(small_early)
    augmented = fv2.augment_features(feats, validated)
    assert augmented["channel_peer_median_current_z_v2"].isna().all()
    without_channel = fv2.augment_features(feats, validated.drop(columns=["tester_channel"]))
    assert without_channel["channel_peer_elevated_fraction_v2"].isna().all()


def test_retrospective_strata_and_paired_batch_stats(training: fv2.TrainingData, configs: list[fv2.CandidateConfig]) -> None:
    strata = fv2.retrospective_strata(training.labels)
    assert set(np.unique(strata)) <= set(fv2.STRATA_ORDER)
    assert (strata == "healthy").sum() == int((~training.labels["is_defect"]).sum())
    assert (strata == "defect_onset_le24").sum() + (strata == "defect_onset_gt24").sum() == int(training.labels["is_defect"].sum())
    folds = fv2.assign_batch_folds(training.features, n_splits=5)
    results, _ = fv2.run_cross_validation(training, configs[:2], folds, seed=1, n_jobs=1)
    persistence = results["configs"]["persistence"]
    assert persistence["batches_beating_persistence"] == 0 and persistence["batches_total"] == 10
    assert persistence["paired_batch_delta_vs_persistence"]["mean"] == 0.0
    linear = results["configs"]["linear_extrapolation"]
    assert set(linear["pooled"]["by_stratum"]) <= set(fv2.STRATA_ORDER)
    assert all("train_mae_normalized" in m for m in linear["per_fold"])
    table = fv2.comparison_table(results)
    assert {"paired_batch_delta_mean", "train_mae_norm_fold_mean", "share_clipped_at_zero"} <= set(table.columns)
    strata_table = fv2.stratum_table(results)
    assert len(strata_table) == 2 * len(linear["pooled"]["by_stratum"])


def test_prevalence_readout_and_seed_check_touch_only_training_rows(training: fv2.TrainingData, configs: list[fv2.CandidateConfig]) -> None:
    folds = fv2.assign_batch_folds(training.features, n_splits=5)
    report = fv2.run_prevalence_readout(training, configs[:1], folds, keep_fraction=0.5, seed=1, n_jobs=1)
    assert report["training_defect_parts_dropped"] == int(round(training.labels["is_defect"].sum() * 0.5))
    # persistence does not depend on training rows, so the read-out equals the plain pooled metric
    results, _ = fv2.run_cross_validation(training, configs[:1], folds, seed=1, n_jobs=1)
    assert np.isclose(report["configs"]["persistence"]["mae_normalized"], results["configs"]["persistence"]["pooled"]["mae_normalized"])
    seeds = fv2.run_seed_check(training, configs[2], folds, seeds=[1, 2], n_jobs=1)
    assert set(seeds["seeds"]) == {"1", "2"} and seeds["pooled_mae_normalized_spread"]["std"] >= 0.0


# --------------------------------------------------------------------------- #
# Added by the test audit: predeclaration, coverage of every configuration,
# calibration/validation disjointness, imputation, provenance, input contract
# --------------------------------------------------------------------------- #
def test_training_data_is_invariant_to_early_row_order(pack: Path, training: fv2.TrainingData, tmp_path: Path) -> None:
    early = pd.read_csv(pack / "train_early.csv", dtype={c: str for c in fv2.IDENTITY})
    labels = pd.read_csv(pack / "train_labels.csv", dtype={c: str for c in fv2.IDENTITY})
    early.sample(frac=1.0, random_state=13).to_csv(tmp_path / "train_early.csv", index=False)
    labels.sample(frac=1.0, random_state=14).to_csv(tmp_path / "train_labels.csv", index=False)
    reloaded = fv2.load_training_data(tmp_path)
    pd.testing.assert_frame_equal(reloaded.features, training.features)
    pd.testing.assert_frame_equal(reloaded.labels, training.labels)
    np.testing.assert_array_equal(reloaded.y, training.y)
    assert reloaded.input_hashes != training.input_hashes  # the files differ, the derived data must not


def test_training_rejects_future_checkpoints_in_train_early(tmp_path: Path) -> None:
    early, labels = make_fixture(n_batches=2, with_future=True, seed=11)
    early.to_csv(tmp_path / "train_early.csv", index=False)
    labels.to_csv(tmp_path / "train_labels.csv", index=False)
    with pytest.raises(ValueError, match="0 h and 24 h"):
        fv2.load_training_data(tmp_path)
    with pytest.raises(FileNotFoundError, match="data-dir"):
        fv2.load_training_data(tmp_path / "nowhere")


def test_validation_fold_labels_cannot_influence_their_own_oof_predictions(training: fv2.TrainingData, configs: list[fv2.CandidateConfig]) -> None:
    """Multiply the labels of fold 0's batches by 7. Fold 0's out-of-fold predictions must not
    move at all (they never see those labels); the other folds' predictions must move (proves
    the test has power and that the models really are trained on the labels)."""
    folds = fv2.assign_batch_folds(training.features, n_splits=5)
    _, before = fv2.run_cross_validation(training, [configs[2]], folds, seed=1, n_jobs=1)
    tampered = training.labels.copy()
    in_fold0 = training.features["batch_id"].map(folds.set_index("batch_id")["fold"]).eq(0).to_numpy()
    tampered.loc[in_fold0, "y_normalized"] *= 7.0
    tampered.loc[in_fold0, "final_value"] *= 7.0
    _, after = fv2.run_cross_validation(fv2.TrainingData(training.features, tampered, training.input_hashes, training.validation), [configs[2]], folds, seed=1, n_jobs=1)
    assert (before[fv2.IDENTITY + ["fold"]].to_numpy() == after[fv2.IDENTITY + ["fold"]].to_numpy()).all()
    fold0 = (before["fold"] == 0).to_numpy()
    np.testing.assert_array_equal(before.loc[fold0, "predicted_normalized"].to_numpy(), after.loc[fold0, "predicted_normalized"].to_numpy())
    assert not np.allclose(before.loc[~fold0, "predicted_normalized"], after.loc[~fold0, "predicted_normalized"])


def test_predictions_for_a_batch_do_not_depend_on_other_uploaded_batches(saved_candidate: Path) -> None:
    candidate = fv2.load_forecast_candidate(saved_candidate)
    two, _ = make_fixture(n_batches=2, seed=21)
    together = candidate.predict(two)
    alone = candidate.predict(two.loc[two["batch_id"] == "B00"])
    pd.testing.assert_frame_equal(together.loc[together["batch_id"] == "B00"].reset_index(drop=True), alone)
    # but peers INSIDE the batch do matter (batch-relative features), so the test has power
    dropped = candidate.predict(two.loc[(two["batch_id"] == "B00") & ~two["component_id"].isin(sorted(two["component_id"].unique())[:6])])
    assert not np.allclose(alone.set_index("component_id").loc[dropped["component_id"], "predicted_normalized"], dropped["predicted_normalized"])


def test_predeclared_digest_changes_when_a_config_changes() -> None:
    base = fv2.config_digest(fv2.PREDECLARED_CONFIGS)
    assert base == fv2.config_digest(list(fv2.PREDECLARED_CONFIGS))  # deterministic
    configs = list(fv2.PREDECLARED_CONFIGS)
    edits = {
        "params": dataclasses.replace(configs[6], params={**configs[6].params, "n_estimators": 351}),
        "objective": dataclasses.replace(configs[6], objective="reg:squarederror"),
        "target": dataclasses.replace(configs[6], target="normalized"),
        "feature_set": dataclasses.replace(configs[6], feature_set="leakage_plus_aux"),
        "description": dataclasses.replace(configs[6], description="edited"),
    }
    for what, edited in edits.items():
        changed = configs.copy(); changed[6] = edited
        assert fv2.config_digest(changed) != base, what
    assert fv2.config_digest(configs[:-1]) != base                 # dropping a config
    assert fv2.config_digest(list(reversed(configs))) != base      # reordering
    # the digest also covers the feature allowlists themselves: editing a set's CONTENTS (not its
    # name) must change the digest, so an allowlist edit after predeclaration is detectable
    assert configs[6].to_dict()["feature_columns"] == fv2.FEATURE_SETS[configs[6].feature_set]
    original = list(fv2.FEATURE_SETS[configs[6].feature_set])
    fv2.FEATURE_SETS[configs[6].feature_set] = original + ["bogus_extra_feature"]
    try:
        assert fv2.config_digest(configs) != base, "digest ignores feature allowlist contents"
    finally:
        fv2.FEATURE_SETS[configs[6].feature_set] = original
    assert fv2.config_digest(configs) == base
    recorded = Path(__file__).resolve().parents[1] / "outputs" / "claude_forecast_v2" / "PREDECLARED_COMPARISON.json"
    if recorded.exists():
        assert json.loads(recorded.read_text())["config_digest"] == base, "PREDECLARED_CONFIGS changed after predeclaration"


def test_every_predeclared_config_fits_saves_and_predicts(training: fv2.TrainingData, tmp_path: Path) -> None:
    early, _ = make_fixture(n_batches=1, seed=9)
    x0 = early.loc[early["hours"] == 0].set_index("component_id")["measurement_value"]
    x24 = early.loc[early["hours"] == 24].set_index("component_id")["measurement_value"]
    input_limit = early.drop_duplicates("component_id").set_index("component_id")["upper_limit"]
    for config in fv2.PREDECLARED_CONFIGS:
        small = dataclasses.replace(config, params={**config.params, "n_estimators": 5}) if config.model == "xgboost" else config
        assert small.params.get("huber_slope") == config.params.get("huber_slope")  # override keeps other params
        fitted = fv2.fit_model(small, training.features, training.y, seed=1, n_jobs=1)
        in_sample = fitted.predict_normalized(training.features)
        assert np.isfinite(in_sample).all() and (in_sample >= 0).all(), config.name
        candidate = fv2.fit_final_candidate(training, small, seed=1, n_jobs=1)
        assert candidate.manifest["target"]["base_margin_required_at_predict"] == (config.model == "xgboost" and config.target.endswith("residual_over_persistence"))
        loaded = fv2.load_forecast_candidate(fv2.save_forecast_candidate(candidate, tmp_path / config.name))
        out = loaded.predict(early)
        assert (out["status"] == fv2.FORECAST_STATUS).all(), config.name
        assert np.isfinite(out["predicted_final_value"]).all() and (out["predicted_final_value"] >= 0).all(), config.name
        assert (out["candidate_name"] == config.name).all()
        pd.testing.assert_frame_equal(out, candidate.predict(early))
        # unit conversion end to end, against the INPUT frame (not the output's own columns)
        np.testing.assert_allclose(out["predicted_final_value"], out["predicted_normalized"] * out["component_id"].map(input_limit), err_msg=config.name)
        if config.model == "persistence":
            np.testing.assert_allclose(out["predicted_final_value"], out["component_id"].map(x24), err_msg=config.name)
        elif config.model == "linear_extrapolation":
            np.testing.assert_allclose(out["predicted_final_value"], out["component_id"].map(x24 + (x24 - x0) / 24.0 * 144.0), err_msg=config.name)
        else:
            assert not np.allclose(out["predicted_final_value"], out["component_id"].map(x24)), config.name  # learned correction is not a no-op
    assert fv2.PREDECLARED_CONFIGS[0].model == "persistence"  # baseline is always first


def test_calibration_batches_lie_inside_training_portion_and_off_validation(training: fv2.TrainingData) -> None:
    folds = fv2.assign_batch_folds(training.features, n_splits=4)
    for k, train_mask, valid_mask in fv2.fold_masks(training.features, folds):
        train_features = training.features.loc[train_mask]
        calibration = fv2.choose_calibration_batches(train_features, per_profile=1)
        validation_batches = set(training.features.loc[valid_mask, "batch_id"])
        assert set(calibration) <= set(train_features["batch_id"])
        assert not set(calibration) & validation_batches
        assert len(calibration) == len(set(calibration)) == len(PROFILES)
        per_profile = train_features.drop_duplicates("batch_id").set_index("batch_id")["profile_id"].loc[calibration]
        assert per_profile.value_counts().eq(1).all()
        # fit = train minus calibration: both disjoint from validation
        fit_batches = set(train_features["batch_id"]) - set(calibration)
        assert fit_batches and not fit_batches & validation_batches and not fit_batches & set(calibration)
        assert calibration == fv2.choose_calibration_batches(train_features.sample(frac=1.0, random_state=1), per_profile=1)  # deterministic
        # the experiment rotates the window by fold index; every rotation must obey the same rules
        rotated = [fv2.choose_calibration_batches(train_features, per_profile=1, rotation=r) for r in range(4)]
        for r, chosen in enumerate(rotated):
            assert set(chosen) <= set(train_features["batch_id"]) and not set(chosen) & validation_batches
            assert train_features.drop_duplicates("batch_id").set_index("batch_id")["profile_id"].loc[chosen].value_counts().eq(1).all()
            assert chosen == fv2.choose_calibration_batches(train_features.sample(frac=1.0, random_state=2), per_profile=1, rotation=r)
        assert len({b for chosen in rotated for b in chosen}) > len(PROFILES)  # rotation really moves the window
        # the window wraps per profile with that profile's own training-batch count, so the product of the counts is a period
        period = int(np.prod(train_features.drop_duplicates("batch_id")["profile_id"].value_counts().to_numpy()))
        assert fv2.choose_calibration_batches(train_features, per_profile=1, rotation=k) == fv2.choose_calibration_batches(train_features, per_profile=1, rotation=k + period)
    with pytest.raises(ValueError, match="calibration"):
        fv2.choose_calibration_batches(training.features.loc[train_mask], per_profile=4)


def test_aux_and_peer_features_have_no_missing_values_on_fixture(training: fv2.TrainingData) -> None:
    columns = fv2.AUX_FEATURES + fv2.CHANNEL_PEER_FEATURES
    assert set(columns) <= set(training.features.columns)
    assert training.features[columns].notna().all().all(), training.features[columns].isna().sum().to_dict()
    assert np.isfinite(training.features[columns].to_numpy(dtype=float)).all()
    assert training.validation.get("nonfinite_feature_values", {}) == {}


def test_imputer_handles_columns_entirely_missing_at_inference(aux_candidate: fv2.ForecastCandidate, aux_config: fv2.CandidateConfig, saved_candidate: Path) -> None:
    early, _ = make_fixture(n_batches=1, seed=9)
    complete = aux_candidate.predict(early)
    stripped = early.drop(columns=["capacitance_nf", "dissipation_factor_pct", "prior_storage_humidity_pct"])
    imputed = aux_candidate.predict(stripped)
    assert (imputed["status"] == fv2.FORECAST_STATUS).all()
    assert np.isfinite(imputed["predicted_final_value"]).all()
    assert (imputed[fv2.IDENTITY].to_numpy() == complete[fv2.IDENTITY].to_numpy()).all()
    # the design matrix really is filled with the TRAINING medians for the absent columns
    features, validated, _ = fv2.prepare_early_features(stripped)
    matrix = fv2.feature_matrix(fv2.augment_features(features, validated), aux_config.feature_columns)
    absent = [c for c in fv2.AUX_FEATURES]
    assert matrix[absent].isna().all().all()
    filled = fv2.impute(matrix, aux_candidate.manifest["imputation_medians"])
    for column in absent:
        np.testing.assert_allclose(filled[:, aux_config.feature_columns.index(column)], aux_candidate.manifest["imputation_medians"][column])
    assert np.isfinite(filled).all()
    # and the aux columns really matter when present (so this path is exercised, not bypassed)
    assert not np.allclose(complete["predicted_normalized"], imputed["predicted_normalized"])
    # the peer candidate copes with tester_channel absent (peer features NaN -> medians)
    peer = fv2.load_forecast_candidate(saved_candidate)
    without_channel = peer.predict(early.drop(columns=["tester_channel"]))
    assert (without_channel["status"] == fv2.FORECAST_STATUS).all() and np.isfinite(without_channel["predicted_final_value"]).all()
    # a required leakage column missing is a structural error, not imputation
    with pytest.raises(ValueError, match="missing feature columns"):
        fv2.impute(fv2.feature_matrix(features.drop(columns=["limit_fraction"]), ["limit_fraction"]), {"limit_fraction": 0.0})


def test_manifest_records_provenance(pack: Path, training: fv2.TrainingData, aux_candidate: fv2.ForecastCandidate, aux_config: fv2.CandidateConfig, saved_candidate: Path, tmp_path: Path) -> None:
    manifest = aux_candidate.manifest
    # input hashes: the candidate carries the hashes of the exact files the training data came from
    assert manifest["training"]["input_sha256"] == training.input_hashes
    assert set(training.input_hashes) == {"train_early.csv", "train_labels.csv"}
    fresh_dir = tmp_path / "fresh"; fresh_dir.mkdir()
    early, labels = make_fixture(n_batches=6, seed=31)
    early.to_csv(fresh_dir / "train_early.csv", index=False); labels.to_csv(fresh_dir / "train_labels.csv", index=False)
    fresh = fv2.fit_final_candidate(fv2.load_training_data(fresh_dir), fv2.CandidateConfig("persistence", "persistence"), seed=3, n_jobs=1)
    for name in ("train_early.csv", "train_labels.csv"):
        assert fresh.manifest["training"]["input_sha256"][name] == hashlib.sha256((fresh_dir / name).read_bytes()).hexdigest(), name
    assert fresh.manifest["training"]["seed"] == 3 and fresh.manifest["training"]["batches"] == 6
    assert manifest["training"]["seed"] == 17
    assert manifest["training"]["batches"] == 10 and manifest["training"]["components"] == 160
    assert manifest["training"]["batch_ids"] == sorted(training.features["batch_id"].unique())
    # library versions recorded from the live environment
    for package in ("numpy", "pandas", "scikit-learn", "xgboost"):
        assert manifest["environment"]["versions"][package] == importlib.metadata.version(package), package
    # feature allowlist and imputation medians (recomputed)
    assert manifest["feature_columns"] == aux_config.feature_columns == fv2.FEATURE_SETS["leakage_plus_aux"]
    assert manifest["config"]["feature_columns"] == aux_config.feature_columns
    expected_medians = fv2.fit_medians(fv2.feature_matrix(training.features, aux_config.feature_columns))
    assert manifest["imputation_medians"] == expected_medians
    assert manifest["supported_profiles"] == sorted(PROFILES)
    assert manifest["as_of_hour"] == 24.0 and manifest["target_hour"] == 168.0 and manifest["unit"] == "uA"
    # saved manifest is JSON with the same content plus artifact hashes, and a version mismatch is caught on load
    saved = json.loads((saved_candidate / "manifest.json").read_text())
    assert {"input_sha256", "seed"} <= set(saved["training"]) and saved["environment"]["versions"]["xgboost"] == importlib.metadata.version("xgboost")
    copy = tmp_path / "old_env"
    shutil.copytree(saved_candidate, copy)
    saved["environment"]["versions"]["xgboost"] = "0.0.1"
    (copy / "manifest.json").write_text(json.dumps(saved))
    with pytest.raises(ValueError, match="version mismatch"):
        fv2.load_forecast_candidate(copy)
    assert fv2.load_forecast_candidate(copy, strict_versions=False).manifest["config"]["name"] == "xgb_abs_resid"
    saved["candidate_version"] = "other"
    (copy / "manifest.json").write_text(json.dumps(saved))
    with pytest.raises(ValueError, match="version"):
        fv2.load_forecast_candidate(copy, strict_versions=False)


def test_predict_raises_for_structural_problems_but_not_per_component_problems(saved_candidate: Path) -> None:
    candidate = fv2.load_forecast_candidate(saved_candidate)
    early, _ = make_fixture(n_batches=1, seed=9)
    ids = sorted(early["component_id"].unique())
    # whole-upload problems -> ValueError
    with pytest.raises(ValueError, match="Missing required columns"):
        candidate.predict(early.drop(columns=["upper_limit"]))
    with pytest.raises(ValueError, match="Missing required columns"):
        candidate.predict(early.drop(columns=["hours", "measurement_value"]))
    with pytest.raises(ValueError, match="cannot be blank"):
        candidate.predict(early.assign(component_id=early["component_id"].where(early.index != 0, "   ")))
    with pytest.raises(ValueError, match="missing values"):
        candidate.predict(early.assign(batch_id=early["batch_id"].where(early.index != 0, np.nan)))
    with pytest.raises(ValueError, match="no readings"):
        candidate.predict(early.iloc[0:0])
    with pytest.raises(ValueError, match="Mixed profile_id"):
        candidate.predict(early.assign(profile_id=np.where(early["component_id"] == ids[0], "P_B", early["profile_id"])))
    twice = pd.concat([early, early.loc[early["component_id"] == ids[0]].assign(batch_id="B99")])  # same device, two batches
    with pytest.raises(ValueError, match="one device"):
        candidate.predict(twice)
    # a single stray row in another batch is an incomplete identity, not a structural error
    stray = candidate.predict(pd.concat([early, early.loc[(early["component_id"] == ids[0]) & (early["hours"] == 0)].assign(batch_id="B99")]))
    assert (stray.loc[stray["batch_id"] == "B99", "status"] == fv2.UNAVAILABLE_STATUS).all() and len(stray) == len(ids) + 1
    # per-component problems -> one unavailable row each, everyone else still forecast
    broken = early.copy()
    broken.loc[(broken["component_id"] == ids[0]) & (broken["hours"] == 24), "hours"] = 48        # no 24 h checkpoint
    broken.loc[(broken["component_id"] == ids[1]) & (broken["hours"] == 0), "measurement_value"] = -1.0  # negative leakage
    broken.loc[broken["component_id"] == ids[2], "upper_limit"] = 0.0                                # nonpositive limit
    broken.loc[broken["component_id"] == ids[3], "measurement_name"] = "capacitance_nf"              # unsupported measurement
    broken = pd.concat([broken, broken.loc[(broken["component_id"] == ids[4]) & (broken["hours"] == 0)]])  # duplicate checkpoint
    out = candidate.predict(broken)
    assert len(out) == len(ids) and out["component_id"].is_unique
    status = out.set_index("component_id")["status"]
    assert (status.loc[ids[:5]] == fv2.UNAVAILABLE_STATUS).all()
    assert (status.loc[ids[5:]] == fv2.FORECAST_STATUS).all()
    assert out.loc[out["status"] == fv2.UNAVAILABLE_STATUS, ["predicted_final_value", "predicted_normalized", "upper_limit"]].isna().all().all()
    assert out.loc[out["status"] == fv2.UNAVAILABLE_STATUS, "unavailable_reason"].str.len().gt(0).all()
    assert list(out.columns) == fv2.OUTPUT_COLUMNS


def test_inference_imputation_uses_training_medians_not_upload_medians(aux_candidate: fv2.ForecastCandidate, aux_config: fv2.CandidateConfig, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The design matrix that reaches the booster must have its gaps filled with the medians
    recorded in the manifest at training time, never with statistics of the uploaded batch."""
    candidate = fv2.load_forecast_candidate(fv2.save_forecast_candidate(aux_candidate, tmp_path / "aux"))
    early, _ = make_fixture(n_batches=1, seed=9)
    ids = sorted(early["component_id"].unique())
    partial = early.copy()
    partial.loc[partial["component_id"].isin(ids[:4]), "capacitance_nf"] = np.nan           # some parts lack capacitance
    partial.loc[partial["component_id"].isin(ids[4:6]) & (partial["hours"] == 24), "dissipation_factor_pct"] = np.nan
    features, validated, _ = fv2.prepare_early_features(partial)
    matrix = fv2.feature_matrix(fv2.augment_features(features, validated), aux_config.feature_columns)
    gaps = matrix.isna()
    assert gaps.to_numpy().any() and not gaps.all().any()  # partial gaps: upload medians exist and differ from training medians
    medians = candidate.manifest["imputation_medians"]
    upload_medians = matrix.median()
    gap_columns = [c for c in matrix.columns if gaps[c].any()]
    assert all(not np.isclose(upload_medians[c], medians[c]) for c in gap_columns), "fixture gives no power"
    captured: list[np.ndarray] = []
    original_predict = candidate.booster.predict

    def spy(X, *args, **kwargs):
        captured.append(np.array(X, dtype=float, copy=True))
        return original_predict(X, *args, **kwargs)

    monkeypatch.setattr(candidate.booster, "predict", spy)
    out = candidate.predict(partial)
    assert len(captured) == 1 and (out["status"] == fv2.FORECAST_STATUS).all()
    fed = captured[0]
    assert fed.shape == matrix.shape and np.isfinite(fed).all()
    expected = fv2.impute(matrix, medians)
    np.testing.assert_allclose(fed, expected)
    for column in gap_columns:
        j = aux_config.feature_columns.index(column)
        np.testing.assert_allclose(fed[gaps[column].to_numpy(), j], medians[column])
    # and the same forecast comes from the manual manifest-median path (no hidden preprocessing)
    persistence = fv2.persistence_forecast(fv2.augment_features(features, validated))
    manual = np.maximum(original_predict(expected, base_margin=persistence), 0.0)
    np.testing.assert_allclose(out["predicted_normalized"], manual)


def test_training_ignores_label_columns_in_train_early_and_never_reads_train_readings(pack: Path, training: fv2.TrainingData, tmp_path: Path) -> None:
    """Label columns smuggled into train_early.csv must not become features, and the loader
    must not depend on train_readings.csv (diagnosis only)."""
    early = pd.read_csv(pack / "train_early.csv", dtype={c: str for c in fv2.IDENTITY})
    labels = pd.read_csv(pack / "train_labels.csv", dtype={c: str for c in fv2.IDENTITY})
    smuggled = early.copy()
    smuggled["final_value"] = smuggled["component_id"].map(labels.set_index("component_id")["final_value"]) * 3.0
    smuggled["true_final_value"] = smuggled["final_value"]
    smuggled["scenario"] = "leaked"
    smuggled["is_future_failure"] = True
    smuggled.to_csv(tmp_path / "train_early.csv", index=False)
    labels.to_csv(tmp_path / "train_labels.csv", index=False)
    (tmp_path / "train_readings.csv").write_text("not,a,valid,file\n\x00\x01")
    reloaded = fv2.load_training_data(tmp_path)
    pd.testing.assert_frame_equal(reloaded.features, training.features)
    pd.testing.assert_frame_equal(reloaded.labels, training.labels)
    forbidden = {"final_value", "true_final_value", "scenario", "is_future_failure"}
    assert not forbidden & set(reloaded.features.columns)
    for columns in fv2.FEATURE_SETS.values():
        assert not forbidden & set(columns)
    folds = fv2.assign_batch_folds(training.features, n_splits=5)
    config = fv2.CandidateConfig("xgb", "xgboost", target="residual_over_persistence", feature_set="leakage_plus_aux", objective="reg:absoluteerror", params={"n_estimators": 20})
    _, before = fv2.run_cross_validation(training, [config], folds, seed=1, n_jobs=1)
    _, after = fv2.run_cross_validation(reloaded, [config], folds, seed=1, n_jobs=1)
    np.testing.assert_array_equal(before["predicted_normalized"].to_numpy(), after["predicted_normalized"].to_numpy())


def test_provenance_digest_tracks_hyperparameters_and_constants(aux_candidate: fv2.ForecastCandidate, monkeypatch: pytest.MonkeyPatch) -> None:
    """The second predeclaration digest must move when anything outside the configuration
    list that changes results moves: shared XGBoost hyperparameters, feature and interval
    constants, feature formulas. Source hashes are recorded but compared separately."""
    record = fv2.provenance_record()
    base = fv2.provenance_digest()
    assert base == fv2.provenance_digest(record) == fv2.provenance_digest()
    assert record["v1_xgb_params"] == fv2.V1_XGB_PARAMS and record["feature_constants"]["MIN_CHANNEL_PEERS"] == fv2.MIN_CHANNEL_PEERS
    here = Path(fv2.__file__).resolve().parent
    assert record["source_sha256"]["forecast_v2.py"] == hashlib.sha256((here / "forecast_v2.py").read_bytes()).hexdigest()
    assert {"features.py", "mlcc_prototype.py"} <= set(record["source_sha256"])
    tampered = dict(record); tampered["source_sha256"] = {k: "0" * 64 for k in record["source_sha256"]}
    assert fv2.provenance_digest(tampered) == base  # source drift is a warning path, not part of this digest
    with monkeypatch.context() as m:
        m.setitem(fv2.V1_XGB_PARAMS, "n_estimators", 351)
        assert fv2.provenance_digest() != base, "hyperparameters"
    with monkeypatch.context() as m:
        m.setattr(fv2, "MIN_CHANNEL_PEERS", fv2.MIN_CHANNEL_PEERS + 1)
        assert fv2.provenance_digest() != base, "feature constant"
    with monkeypatch.context() as m:
        m.setattr(fv2, "CHANNEL_PEER_Z_THRESHOLD", 2.5)
        assert fv2.provenance_digest() != base, "peer threshold"
    with monkeypatch.context() as m:
        m.setattr(fv2, "SLOPE_Z_STRATA_EDGES", (2.0, 6.0))
        assert fv2.provenance_digest() != base, "interval strata"
    with monkeypatch.context() as m:
        m.setitem(fv2.V2_FEATURE_FORMULAS, "channel_peer_elevated_fraction_v2", "edited")
        assert fv2.provenance_digest() != base, "feature formula"
    assert fv2.provenance_digest() == base  # everything restored
    # the candidate manifest carries the same provenance block
    assert aux_candidate.manifest["provenance"]["v1_xgb_params"] == fv2.V1_XGB_PARAMS
    assert fv2.provenance_digest(aux_candidate.manifest["provenance"]) == base
    recorded = Path(__file__).resolve().parents[1] / "outputs" / "claude_forecast_v2" / "PREDECLARED_COMPARISON.json"
    if recorded.exists():
        payload = json.loads(recorded.read_text())
        assert payload["provenance_digest"] == base, "hyperparameters or constants changed after predeclaration"
        assert fv2.provenance_digest(payload["provenance"]) == payload["provenance_digest"]


def test_manifest_is_bound_to_the_model_and_validated_at_load(saved_candidate: Path, tmp_path: Path) -> None:
    import shutil

    def copy_with(mutate):
        target = tmp_path / f"m{len(list(tmp_path.iterdir()))}"
        shutil.copytree(saved_candidate, target)
        manifest = json.loads((target / "manifest.json").read_text())
        mutate(manifest)
        (target / "manifest.json").write_text(json.dumps(manifest))
        return target

    def set_target(m):
        m["config"]["target"] = "normalized"; m["target"]["parameterisation"] = "normalized"; m["target"]["base_margin_required_at_predict"] = False

    with pytest.raises(ValueError, match="Manifest integrity"):
        fv2.load_forecast_candidate(copy_with(set_target))
    with pytest.raises(ValueError, match="artifact_sha256"):
        fv2.load_forecast_candidate(copy_with(lambda m: m.__setitem__("artifact_sha256", {})))
    with pytest.raises(ValueError, match="imputation_medians"):
        fv2.load_forecast_candidate(copy_with(lambda m: m["imputation_medians"].pop("limit_fraction")))
    with pytest.raises(ValueError, match="feature_columns"):
        fv2.load_forecast_candidate(copy_with(lambda m: m["config"].__setitem__("feature_set", "leakage_plus_aux")))
    with pytest.raises(ValueError, match="base_margin"):
        fv2.load_forecast_candidate(copy_with(lambda m: m["target"].__setitem__("base_margin_required_at_predict", False)))
    with pytest.raises(ValueError, match="supported_profiles"):
        fv2.load_forecast_candidate(copy_with(lambda m: m.__setitem__("supported_profiles", "P_A")))
    # the informational environment block is outside the binding: a version edit is caught by the version check only
    edited = copy_with(lambda m: m["environment"]["versions"].__setitem__("numpy", "0.0.1"))
    with pytest.raises(ValueError, match="version mismatch"):
        fv2.load_forecast_candidate(edited)
    with pytest.warns(RuntimeWarning, match="mismatched"):
        assert fv2.load_forecast_candidate(edited, strict_versions=False).config.name == "xgb_abs_resid"
    # untouched copy loads and the bound digest equals the manifest digest
    clean = copy_with(lambda m: None)
    candidate = fv2.load_forecast_candidate(clean)
    assert candidate.booster.get_booster().attr(fv2.MANIFEST_DIGEST_ATTRIBUTE) == fv2.manifest_digest(candidate.manifest)


def test_output_dtypes_are_stable_and_records_are_json_safe(saved_candidate: Path) -> None:
    candidate = fv2.load_forecast_candidate(saved_candidate)
    early, _ = make_fixture(n_batches=1, seed=8)
    ids = sorted(early["component_id"].unique())
    broken = early.loc[~((early["component_id"] == ids[0]) & (early["hours"] == 24))]
    clean_out, mixed_out = candidate.predict(early), candidate.predict(broken)
    assert dict(clean_out.dtypes.astype(str)) == dict(mixed_out.dtypes.astype(str))
    assert str(mixed_out["peer_count"].dtype) == "Int64" and str(mixed_out["weak_peer_warning"].dtype) == "boolean"
    assert mixed_out.loc[mixed_out["status"] == fv2.UNAVAILABLE_STATUS, "unavailable_reason"].str.len().gt(0).all()
    assert (clean_out["weak_peer_warning"] == False).all() and (clean_out["imputed_feature_count"] == 0).all()  # noqa: E712
    small = candidate.predict(early.loc[early["component_id"].isin(ids[:3])])
    assert (small["weak_peer_warning"] == True).all() and (small["peer_count"] == 3).all()  # noqa: E712
    records = candidate.predict_records(broken)
    assert len(records) == len(ids)
    json.dumps(records, allow_nan=False)  # must not raise
    assert any(r["status"] == fv2.UNAVAILABLE_STATUS and r["predicted_final_value"] is None for r in records)


def test_missing_optional_columns_are_counted_as_imputed(aux_candidate: fv2.ForecastCandidate) -> None:
    early, _ = make_fixture(n_batches=1, seed=8)
    full = aux_candidate.predict(early)
    dropped = aux_candidate.predict(early.drop(columns=["capacitance_nf", "dissipation_factor_pct"]))
    assert (full["imputed_feature_count"] == 0).all()
    assert (dropped["imputed_feature_count"] == 6).all()  # six capacitance / dissipation-factor features
