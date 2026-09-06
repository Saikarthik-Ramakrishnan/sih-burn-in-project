"""Offline MLCC pilot: frozen Isolation Forest + a validated final-value model.

Only exact 0 h and 24 h observations enter either model. Synthetic performance
is a software benchmark, not evidence of field accuracy or physical causation.
The public inference functions never fit a model. FastAPI can call them directly.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from hashlib import sha256
import importlib.metadata
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from .anomaly import BatchAwareAnomalyDetector
from .contracts import PredictionResult
from .decision import build_screening_record
from .features import GROUP_COLUMNS, MODEL_FEATURE_COLUMNS, build_component_features
from .validation import REQUIRED_COLUMNS


VERSION = "mlcc-pilot-1.1"
COMPATIBLE_VERSIONS = ("mlcc-pilot-1.0", VERSION)  # 1.0 bundles have no xgboost_v2 model
AS_OF_HOUR = 24.0
TARGET_HOUR = 168.0
UNIT = "uA"
FORECAST_COLUMNS = MODEL_FEATURE_COLUMNS + [
    "initial_fraction_of_limit", "temperature_c", "measurement_temperature_c",
    "voltage_stress_ratio", "measurement_voltage_v", "prior_storage_humidity_pct",
    "initial_capacitance_fraction", "current_capacitance_fraction",
    "capacitance_change_fraction", "initial_dissipation_factor_pct",
    "current_dissipation_factor_pct", "dissipation_factor_change_pct",
]
METADATA_COLUMNS = [
    "profile_id", "part_number", "nominal_capacitance_nf", "rated_voltage_v",
    "applied_voltage_v", "measurement_voltage_v", "temperature_c",
    "measurement_temperature_c", "prior_storage_humidity_pct", "dielectric",
    "package_code", "tester_id", "tester_channel", "board_position", "data_source",
    "is_synthetic", "generator_version",
]
CONDITION_COLUMNS = ["temperature_c", "measurement_temperature_c", "voltage_stress_ratio", "measurement_voltage_v"]

# --- Forecast v2 (Claude forecasting workstream, 2026-09-06) ------------------
# Absolute-error XGBoost on the correction over persistence: base_margin is the
# 24 h value divided by the limit, so a zero tree output reproduces persistence.
# Uses only the ten leakage-derived 0/24 h features; the batch-constant condition
# columns and the auxiliary measurements are deliberately excluded (they act as
# batch identifiers / carry no signal on the training folds). Hyperparameters are
# v1's; a bounded tuning check on whole-batch folds found no improvement.
RESIDUAL_XGB_NAME = "xgboost_v2"
RESIDUAL_XGB_FEATURES = MODEL_FEATURE_COLUMNS + ["initial_fraction_of_limit"]
RESIDUAL_XGB_FEATURE_INDEX = [FORECAST_COLUMNS.index(column) for column in RESIDUAL_XGB_FEATURES]
PERSISTENCE_COLUMN_INDEX = FORECAST_COLUMNS.index("limit_fraction")
SLOPE_Z_COLUMN_INDEX = FORECAST_COLUMNS.index("slope_batch_robust_z")
CURRENT_Z_COLUMN_INDEX = FORECAST_COLUMNS.index("current_batch_robust_z")
# Gate: parts whose 24 h level and drift both sit within this many robust standard
# deviations of their batch keep the persistence forecast (no learned correction).
# Chosen on whole-batch training folds (pooled MAE 0.1415 vs 0.1429, healthy-part
# MAE 0.0128 vs 0.0165); a transparent rule with no fitted parameter.
RESIDUAL_XGB_GATE_Z = 2.0
RESIDUAL_XGB_PARAMS = {
    "n_estimators": 350, "max_depth": 3, "learning_rate": 0.04, "min_child_weight": 12,
    "subsample": 0.9, "colsample_bytree": 0.9, "reg_lambda": 10.0,
    "objective": "reg:absoluteerror", "tree_method": "hist", "base_score": 0.0,
}
RESIDUAL_XGB_FILE = "xgboost_v2.ubj"
# Stratified asymmetric split-conformal interval for the v2 model: strata on the
# signed 24 h slope robust z (<2, 2-5, >=5), pooled fallback below 20 parts.
INTERVAL_STRATA_EDGES = (2.0, 5.0)
INTERVAL_MIN_STRATUM = 20
STRATIFIED_INTERVAL_METHOD = "stratified_asymmetric_split_conformal_signed_residual"


class ResidualOverPersistenceXGB:
    """sklearn-like wrapper so the v2 forecaster fits into the v1 model dictionary.

    ``fit``/``predict`` take the full FORECAST_COLUMNS matrix (after the bundle
    imputer) and select the leakage-only columns internally; the persistence
    forecast (limit_fraction) is always supplied as the XGBoost base margin.
    """

    def __init__(self, seed: int = 26170, n_jobs: int = 2) -> None:
        from xgboost import XGBRegressor

        self.model = XGBRegressor(random_state=seed, n_jobs=n_jobs, **RESIDUAL_XGB_PARAMS)

    @staticmethod
    def _split(matrix: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        full = np.asarray(matrix, dtype=float)
        return full[:, RESIDUAL_XGB_FEATURE_INDEX], full[:, PERSISTENCE_COLUMN_INDEX]

    def fit(self, matrix: np.ndarray, y: np.ndarray) -> "ResidualOverPersistenceXGB":
        features, margin = self._split(matrix)
        self.model.fit(features, np.asarray(y, dtype=float), base_margin=margin)
        return self

    def predict(self, matrix: np.ndarray) -> np.ndarray:
        features, margin = self._split(matrix)
        corrected = np.asarray(self.model.predict(features, base_margin=margin), dtype=float)
        return np.where(self.quiet(matrix), margin, corrected)

    @staticmethod
    def quiet(matrix: np.ndarray) -> np.ndarray:
        """True where both batch robust z-scores are inside the gate (persistence is used)."""
        full = np.nan_to_num(np.asarray(matrix, dtype=float), nan=0.0)
        return (np.abs(full[:, SLOPE_Z_COLUMN_INDEX]) < RESIDUAL_XGB_GATE_Z) & (np.abs(full[:, CURRENT_Z_COLUMN_INDEX]) < RESIDUAL_XGB_GATE_Z)

    def contributions(self, matrix: np.ndarray) -> np.ndarray:
        """TreeSHAP contributions (last column = bias, which includes the persistence
        margin). For gated parts the tree contributions are zeroed so the explanation
        sums to the persistence forecast actually reported."""
        from xgboost import DMatrix

        features, margin = self._split(matrix)
        contributions = self.model.get_booster().predict(DMatrix(features, base_margin=margin), pred_contribs=True)
        quiet = self.quiet(matrix)
        contributions[quiet, :-1] = 0.0
        contributions[quiet, -1] = margin[quiet]
        return contributions

    def get_booster(self):
        return self.model.get_booster()

    def save_model(self, path: str | Path) -> None:
        self.model.save_model(str(path))

    @classmethod
    def load(cls, path: str | Path) -> "ResidualOverPersistenceXGB":
        from xgboost import XGBRegressor

        instance = cls.__new__(cls)
        instance.model = XGBRegressor()
        instance.model.load_model(str(path))
        return instance


def interval_stratum(slope_batch_robust_z: np.ndarray) -> np.ndarray:
    values = np.nan_to_num(np.asarray(slope_batch_robust_z, dtype=float), nan=0.0)
    return np.digitize(values, INTERVAL_STRATA_EDGES)


def signed_conformal_bounds(residuals: np.ndarray, alpha: float) -> dict[str, float]:
    """Finite-sample quantiles of the signed residual (observed - forecast).

    Returns the two-sided (1-alpha) bounds ``lower_two_sided``/``upper_two_sided``
    (ranks floor((n+1)alpha/2), ceil((n+1)(1-alpha/2))) and the one-sided
    (1-alpha) bounds ``lower``/``upper`` (ranks floor((n+1)alpha), ceil((n+1)(1-alpha))).
    The reported interval is [lower, upper]: each bound is a one-sided (1-alpha)
    bound, so the pair is a two-sided (1-2*alpha) interval whose upper bound is the
    'may exceed limit' bound used by the decision rule."""
    ordered = np.sort(np.asarray(residuals, dtype=float))
    n = len(ordered)
    if not 0 < alpha < 0.5 or n == 0 or not np.isfinite(ordered).all():
        raise ValueError("Finite calibration residuals and 0 < alpha < 0.5 are required")
    ranks = {"lower_two_sided": math.floor((n + 1) * (alpha / 2)), "upper_two_sided": math.ceil((n + 1) * (1 - alpha / 2)), "lower": math.floor((n + 1) * alpha), "upper": math.ceil((n + 1) * (1 - alpha))}
    if min(ranks.values()) < 1 or max(ranks.values()) > n:
        raise ValueError("Too few calibration components for asymmetric bounds at this alpha")
    return {name: float(ordered[rank - 1]) for name, rank in ranks.items()}


def stratified_interval_margins(residuals: np.ndarray, slope_batch_robust_z: np.ndarray, alpha: float) -> dict[str, dict[str, float]]:
    """Per-stratum signed-residual margins with a pooled fallback for small strata."""
    residuals = np.asarray(residuals, dtype=float)
    strata = interval_stratum(slope_batch_robust_z)
    pooled = signed_conformal_bounds(residuals, alpha)
    margins: dict[str, dict[str, float]] = {}
    for k in range(len(INTERVAL_STRATA_EDGES) + 1):
        member = residuals[strata == k]
        bounds, pooled_fallback = pooled, True
        if len(member) >= INTERVAL_MIN_STRATUM:
            try:
                bounds, pooled_fallback = signed_conformal_bounds(member, alpha), False
            except ValueError:
                pass
        # The point forecast always lies inside its own interval: lower margins are
        # capped at zero and upper margins floored at zero.
        bounds = {name: (min(value, 0.0) if name.startswith("lower") else max(value, 0.0)) for name, value in bounds.items()}
        margins[str(k)] = {**bounds, "calibration_components": int(len(member)), "pooled_fallback": pooled_fallback}
    return margins


def stratified_bounds(forecast: np.ndarray, slope_batch_robust_z: np.ndarray, margins: dict[str, dict[str, float]]) -> dict[str, np.ndarray]:
    """Normalized bounds per component: one-sided ``lower``/``upper`` (the reported
    interval), the wider two-sided pair, and the stratum index. Lower bounds are
    clipped at zero leakage."""
    strata = interval_stratum(slope_batch_robust_z)
    forecast = np.asarray(forecast, dtype=float)
    pick = lambda key: np.array([margins[str(k)][key] for k in strata])  # noqa: E731
    return {
        "lower": np.maximum(forecast + pick("lower"), 0.0), "upper": forecast + pick("upper"),
        "lower_two_sided": np.maximum(forecast + pick("lower_two_sided"), 0.0), "upper_two_sided": forecast + pick("upper_two_sided"),
        "stratum": strata,
    }
# These are sklearn's numerical loss/tree objects, not arbitrary uploaded classes.
SKOPS_ALLOWED_TYPES = {
    "numpy.dtype", "sklearn._loss.link.Interval",
    "sklearn.ensemble._hist_gradient_boosting.binning._BinMapper",
    "sklearn._loss.link.IdentityLink", "sklearn._loss.loss.HalfSquaredError",
    "sklearn._loss._loss.CyHalfSquaredError",
    "sklearn.ensemble._hist_gradient_boosting.predictor.TreePredictor",
}


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, np.ndarray)):
        return [_json_safe(v) for v in value]
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.integer, int)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return float(value) if np.isfinite(value) else None
    if value is None or value is pd.NA:
        return None
    return value


def _number(row: pd.Series, column: str) -> float:
    try:
        number = float(row.get(column, np.nan))
        return number if np.isfinite(number) else np.nan
    except (ValueError, TypeError):
        return np.nan


def _unscored(identity: dict[str, Any], reasons: list[str]) -> dict[str, Any]:
    return {
        **identity, "status": "unscored", "as_of_hour": AS_OF_HOUR,
        "unit": UNIT, "target_hour": TARGET_HOUR, "current_value": None,
        "safety_limit": None, "anomaly_score": None, "is_anomaly": None,
        "robust_deviation_score": None, "model_anomaly_score": None,
        "predicted_final_value": None, "prediction_lower": None,
        "prediction_upper": None, "recommendation": "RETEST",
        "reason_codes": [], "recommendation_reasons": reasons,
        "data_quality_warning": "; ".join(reasons),
    }


def prepare_early_features(
    readings: pd.DataFrame, *, as_of_hour: float = AS_OF_HOUR,
) -> tuple[pd.DataFrame, pd.DataFrame, list[dict[str, Any]]]:
    """Validate components individually; discard non-checkpoint/future values.

    Missing identities or columns reject the request. An identifiable component
    with invalid readings returns an explicit unscored result, never a forecast.
    """
    if as_of_hour != AS_OF_HOUR:
        raise ValueError("This trained bundle supports as_of_hour=24 only")
    missing = REQUIRED_COLUMNS.difference(readings.columns)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")
    if readings.empty:
        raise ValueError("The upload contains no readings")
    if readings[GROUP_COLUMNS].isna().any().any():
        raise ValueError("Identity columns cannot contain missing values")
    frame = readings.copy().reset_index(drop=True)
    for column in GROUP_COLUMNS:
        frame[column] = frame[column].astype(str)
        if frame[column].str.strip().eq("").any():
            raise ValueError(f"{column} cannot be blank")
    valid: list[pd.DataFrame] = []
    unscored: list[dict[str, Any]] = []
    for key, group in frame.groupby(GROUP_COLUMNS, sort=False):
        identity = dict(zip(GROUP_COLUMNS, key))
        reasons: list[str] = []
        if identity["component_family"] != "MLCC_X7R":
            reasons.append("Unsupported family: this bundle supports MLCC_X7R only")
        if identity["measurement_name"] != "leakage_ua":
            reasons.append("Unsupported measurement: leakage_ua in microamperes is required")
        hours = pd.to_numeric(group["hours"], errors="coerce")
        if (~np.isfinite(hours)).any() or (hours < 0).any():
            reasons.append("Hours must be finite, numeric and nonnegative")
        early = group.loc[hours.isin([0.0, AS_OF_HOUR])].copy()
        early["hours"] = hours.loc[early.index]
        if len(early) != 2 or set(early["hours"]) != {0.0, AS_OF_HOUR}:
            reasons.append("Exactly one 0-hour and one 24-hour reading are required")
        for column in ("measurement_value", "upper_limit"):
            early[column] = pd.to_numeric(early[column], errors="coerce")
            if not np.isfinite(early[column]).all():
                reasons.append(f"{column} must be finite and numeric at both checkpoints")
        if (early["measurement_value"] < 0).any():
            reasons.append("Leakage must be nonnegative")
        if (early["upper_limit"] <= 0).any() or early["upper_limit"].nunique() != 1:
            reasons.append("A positive, unchanged upper_limit is required")
        if "lower_limit" in early and early["lower_limit"].notna().any():
            reasons.append("This leakage bundle implements upper-limit screening only; lower limits require a separate profile")
        for column in (
            "nominal_capacitance_nf", "rated_voltage_v", "applied_voltage_v",
            "measurement_voltage_v", "temperature_c", "measurement_temperature_c",
            "prior_storage_humidity_pct", "capacitance_nf", "dissipation_factor_pct",
        ):
            if column in early:
                supplied = early[column].notna()
                numeric = pd.to_numeric(early[column], errors="coerce")
                if (~np.isfinite(numeric.loc[supplied])).any():
                    reasons.append(f"Supplied {column} must be finite and numeric")
                early[column] = numeric
        for column in ("profile_id", "part_number", "nominal_capacitance_nf", "rated_voltage_v", "measurement_voltage_v", "measurement_temperature_c"):
            if column in early and early[column].nunique(dropna=False) != 1:
                reasons.append(f"{column} changes between the two checkpoints")
        for unit_column in ("unit", "measurement_unit"):
            if unit_column in early and not early[unit_column].isin([UNIT, "µA", "μA"]).all():
                reasons.append(f"{unit_column} must explicitly specify microamperes (uA)")
        if reasons:
            unscored.append(_unscored(identity, reasons))
        else:
            valid.append(early.sort_values("hours"))
    if not valid:
        return pd.DataFrame(), pd.DataFrame(), unscored
    # Stable peer-reduction order makes explanations reproducible when CSV rows
    # are shuffled, including the last bits of floating-point batch statistics.
    early = pd.concat(valid, ignore_index=True).sort_values(GROUP_COLUMNS + ["hours"]).reset_index(drop=True)
    # Core validation scopes limit consistency by component_id; require that ID
    # denotes one device in this upload rather than silently merging batches.
    if early.groupby("component_id")["batch_id"].nunique().gt(1).any():
        raise ValueError("component_id must identify one device across the upload")
    for column in ("profile_id", "part_number", "upper_limit", "nominal_capacitance_nf", "rated_voltage_v", "measurement_voltage_v", "measurement_temperature_c"):
        if column in early and early.groupby("batch_id")[column].nunique(dropna=False).gt(1).any():
            raise ValueError(f"Mixed {column} within a batch: supply comparable part/test groups separately")
    features = build_component_features(early, as_of_hour=AS_OF_HOUR)
    extras: list[dict[str, Any]] = []
    for key, group in early.groupby(GROUP_COLUMNS, sort=False):
        ordered = group.sort_values("hours")
        first, last = ordered.iloc[0], ordered.iloc[-1]
        nominal = _number(last, "nominal_capacitance_nf")
        rated = _number(last, "rated_voltage_v")
        initial_cap = _number(first, "capacitance_nf")
        current_cap = _number(last, "capacitance_nf")
        initial_df = _number(first, "dissipation_factor_pct")
        current_df = _number(last, "dissipation_factor_pct")
        extras.append({
            **dict(zip(GROUP_COLUMNS, key)),
            "initial_fraction_of_limit": float(first["measurement_value"] / first["upper_limit"]),
            "measurement_temperature_c": _number(last, "measurement_temperature_c"),
            "voltage_stress_ratio": _number(last, "applied_voltage_v") / rated if rated > 0 else np.nan,
            "measurement_voltage_v": _number(last, "measurement_voltage_v"),
            "prior_storage_humidity_pct": _number(last, "prior_storage_humidity_pct"),
            "initial_capacitance_fraction": initial_cap / nominal if nominal > 0 else np.nan,
            "current_capacitance_fraction": current_cap / nominal if nominal > 0 else np.nan,
            "capacitance_change_fraction": (current_cap - initial_cap) / nominal if nominal > 0 else np.nan,
            "initial_dissipation_factor_pct": initial_df,
            "current_dissipation_factor_pct": current_df,
            "dissipation_factor_change_pct": current_df - initial_df,
        })
    features = features.merge(pd.DataFrame(extras), on=GROUP_COLUMNS, validate="one_to_one")
    for column in FORECAST_COLUMNS:
        features[column] = pd.to_numeric(features[column], errors="coerce").replace([np.inf, -np.inf], np.nan)
    return features, early, unscored


def conformal_radius(y: np.ndarray, predictions: np.ndarray, alpha: float = 0.1) -> float:
    """Finite-sample split-conformal absolute residual quantile.

    Row exchangeability is required for the usual marginal guarantee. Devices
    in a batch are dependent: report empirical coverage, not a proven guarantee.
    """
    residuals = np.abs(np.asarray(y) - np.asarray(predictions))
    if not 0 < alpha < 1 or not len(residuals) or not np.isfinite(residuals).all():
        raise ValueError("Finite calibration residuals and 0 < alpha < 1 are required")
    rank = math.ceil((len(residuals) + 1) * (1 - alpha))
    if rank > len(residuals):
        raise ValueError("Too few calibration components for a finite interval at this alpha")
    return float(np.sort(residuals)[rank - 1])


def _predict(name: str, models: dict[str, Any], matrix: np.ndarray, features: pd.DataFrame) -> np.ndarray:
    if name == "persistence":
        prediction = features["limit_fraction"].to_numpy(float)
    elif name == "linear_extrapolation":
        prediction = (features["limit_fraction"] + features["slope_fraction_per_hour"] * (TARGET_HOUR - AS_OF_HOUR)).to_numpy(float)
    else:
        prediction = np.asarray(models[name].predict(matrix), dtype=float)
    if not np.isfinite(prediction).all():
        raise ValueError(f"{name} produced a nonfinite forecast")
    # Leakage cannot be negative. There is deliberately no upper clipping.
    return np.maximum(prediction, 0.0)


def _new_models(seed: int) -> dict[str, Any]:
    from xgboost import XGBRegressor

    return {
        "ridge": make_pipeline(StandardScaler(), Ridge(alpha=10.0)),
        "hist_gradient_boosting": HistGradientBoostingRegressor(
            max_iter=250, max_leaf_nodes=15, learning_rate=0.07,
            l2_regularization=5.0, random_state=seed,
        ),
        "xgboost": XGBRegressor(
            n_estimators=350, max_depth=3, learning_rate=0.04,
            min_child_weight=12, subsample=0.9, colsample_bytree=0.9,
            reg_lambda=10.0, objective="reg:squarederror", tree_method="hist",
            random_state=seed, n_jobs=2,
        ),
        RESIDUAL_XGB_NAME: ResidualOverPersistenceXGB(seed=seed, n_jobs=2),
    }


def _joined_labels(features: pd.DataFrame, labels: pd.DataFrame) -> pd.DataFrame:
    needed = set(GROUP_COLUMNS + ["final_value"])
    missing = needed.difference(labels.columns)
    if missing:
        raise ValueError(f"Labels missing: {', '.join(sorted(missing))}")
    frame = labels.copy()
    for column in GROUP_COLUMNS:
        frame[column] = frame[column].astype(str)
    if frame.duplicated(GROUP_COLUMNS).any():
        raise ValueError("Labels must contain one row per component measurement identity")
    joined = features[GROUP_COLUMNS].merge(frame, on=GROUP_COLUMNS, how="left", validate="one_to_one")
    y = pd.to_numeric(joined["final_value"], errors="coerce")
    if not np.isfinite(y).all() or y.lt(0).any():
        raise ValueError("Every scored component needs a finite nonnegative final_value label")
    joined["final_value"] = y
    return joined


def _classification(truth: np.ndarray, flag: np.ndarray) -> dict[str, Any]:
    truth, flag = np.asarray(truth, dtype=bool), np.asarray(flag, dtype=bool)
    tp = int((truth & flag).sum())
    fn = int((truth & ~flag).sum())
    fp = int((~truth & flag).sum())
    tn = int((~truth & ~flag).sum())
    return {"tp": tp, "fn": fn, "fp": fp, "tn": tn,
            "recall": tp / (tp + fn) if tp + fn else None,
            "false_positive_rate": fp / (fp + tn) if fp + tn else None,
            "precision": tp / (tp + fp) if tp + fp else None}


def _bool_labels(labels: pd.DataFrame, column: str) -> np.ndarray:
    if column not in labels:
        raise ValueError(f"Evaluation requires {column} truth labels")
    values = labels[column]
    if pd.api.types.is_bool_dtype(values):
        return values.to_numpy(bool)
    mapping = {"true": True, "false": False, "1": True, "0": False}
    converted = values.astype(str).str.lower().map(mapping)
    if converted.isna().any():
        raise ValueError(f"{column} must contain booleans")
    return converted.to_numpy(bool)


@dataclass
class ModelBundle:
    manifest: dict[str, Any]
    imputer: SimpleImputer
    detector: BatchAwareAnomalyDetector
    models: dict[str, Any]
    radii: dict[str, float]

    @property
    def selected_model(self) -> str:
        return str(self.manifest["selected_model"])


def screen_readings(
    readings: pd.DataFrame, bundle: ModelBundle, *, as_of_hour: float = AS_OF_HOUR,
    future_outcomes: pd.DataFrame | None = None,
    forecast_model: str | None = None,
) -> dict[str, Any]:
    """Screen a batch with frozen models; safe to call from Ashvitha's backend.

    Optional outcome truth is returned in a separate envelope for demo reveal.
    It is never used for features, predictions, decisions, or the summary.
    """
    active_model = forecast_model or bundle.selected_model
    if active_model not in bundle.radii:
        raise ValueError(f"Unknown forecast model: {active_model}")
    features, early, unscored = prepare_early_features(readings, as_of_hour=as_of_hour)
    supported = set(bundle.manifest.get("supported_profiles", []))
    if supported and not features.empty:
        known_ids = set(early.loc[early.get("profile_id", pd.Series(index=early.index, dtype=str)).isin(supported), "component_id"])
        unsupported = ~features["component_id"].isin(known_ids)
        for identity in features.loc[unsupported, GROUP_COLUMNS].to_dict("records"):
            unscored.append(_unscored(identity, ["Missing or unsupported profile_id for this trained bundle"]))
        features = features.loc[~unsupported].reset_index(drop=True)
        early = early.loc[early["component_id"].isin(known_ids)].copy()
    records: list[dict[str, Any]] = []
    if not features.empty:
        with threadpool_limits(limits=1):
            matrix = bundle.imputer.transform(features[FORECAST_COLUMNS])
            forecasts = _predict(active_model, bundle.models, matrix, features)
            xgb_forecasts = _predict("xgboost", bundle.models, matrix, features)
            scored = bundle.detector.score(features)
            from xgboost import DMatrix

            xgb_contributions = bundle.models["xgboost"].get_booster().predict(
                DMatrix(matrix), pred_contribs=True,
            )
        radius = bundle.radii[active_model]
        stratified = (bundle.manifest.get("interval", {}) or {}).get("stratified") or {}
        use_stratified = bool(stratified) and stratified.get("model") == active_model
        if use_stratified:
            strat = stratified_bounds(forecasts, features["slope_batch_robust_z"].to_numpy(float), stratified["margins"])
        if active_model == RESIDUAL_XGB_NAME:
            with threadpool_limits(limits=1):
                active_contributions = bundle.models[RESIDUAL_XGB_NAME].contributions(matrix)
        early_groups = {key: group.sort_values("hours") for key, group in early.groupby(GROUP_COLUMNS)}
        batch_counts = features.groupby(["batch_id", "component_family", "measurement_name"])["component_id"].transform("count")
        for position, anomaly in enumerate(bundle.detector.to_results(scored)):
            feature = features.iloc[position]
            limit = float(feature["upper_limit"])
            forecast = float(forecasts[position])
            if use_stratified:
                prediction = PredictionResult(
                    predicted_final_value=forecast * limit,
                    prediction_lower=float(strat["lower"][position]) * limit,
                    prediction_upper=float(strat["upper"][position]) * limit,
                )
            else:
                prediction = PredictionResult(
                    predicted_final_value=forecast * limit,
                    prediction_lower=max(0.0, forecast - radius) * limit,
                    prediction_upper=(forecast + radius) * limit,
                )
            record = build_screening_record(anomaly, prediction)
            group = early_groups[tuple(feature[column] for column in GROUP_COLUMNS)]
            last = group.iloc[-1]
            peer_count = int(batch_counts.iloc[position])
            outside_range = [
                column for column, bounds in bundle.manifest.get("training_condition_ranges", {}).items()
                if np.isfinite(feature[column]) and not bounds[0] <= float(feature[column]) <= bounds[1]
            ]
            missing_optional = [column for column in FORECAST_COLUMNS if pd.isna(feature[column])]
            if active_model == RESIDUAL_XGB_NAME:
                contributions, contribution_names = active_contributions[position, :-1], RESIDUAL_XGB_FEATURES
                explanation_base, explanation_text = float(active_contributions[position, -1] * limit), "Active xgboost_v2 forecast: absolute-error correction over the 24 h value (bias includes the persistence margin); associations, not physical causes"
            else:
                contributions, contribution_names = xgb_contributions[position, :-1], FORECAST_COLUMNS
                explanation_base, explanation_text = float(xgb_contributions[position, -1] * limit), "Unclipped XGBoost candidate forecast; associations, not physical causes"
            top_contributors = np.argsort(np.abs(contributions))[-5:][::-1]
            record.update({
                "status": "scored", "unit": UNIT, "forecast_model": active_model,
                "xgboost_candidate_final_value": float(xgb_forecasts[position] * limit),
                "interval_nominal_coverage": (1.0 - 2 * bundle.manifest["alpha"]) if use_stratified else (1.0 - bundle.manifest["alpha"]),
                "interval_method": STRATIFIED_INTERVAL_METHOD if use_stratified else "split_conformal_absolute_residual",
                "interval_stratum": (f"slope_z_stratum_{int(strat['stratum'][position])}" if use_stratified else None),
                "upper_bound_nominal_level": (1.0 - bundle.manifest["alpha"]) if use_stratified else None,
                "prediction_lower_two_sided": (float(strat["lower_two_sided"][position]) * limit if use_stratified else None),
                "prediction_upper_two_sided": (float(strat["upper_two_sided"][position]) * limit if use_stratified else None),
                "interval_warning": (
                    "Each bound is a one-sided 90% calibrated bound (about 10% of comparable synthetic parts end above prediction_upper), so the pair is an 80% interval; the wider 90% two-sided pair is reported separately. Coverage on real components is not established; batch dependence limits the usual guarantee"
                    if use_stratified else "Nominal level; coverage on real components is not established; batch dependence limits the usual guarantee"
                ),
                "anomaly_score_kind": "ranking score, not failure probability",
                "initial_value": float(feature["initial_value"]),
                "delta": float(feature["delta"]), "percent_change": float(feature["percent_change"]) if feature["initial_value"] != 0 else None,
                "slope_per_hour": float(feature["slope"]),
                "limit_fraction": float(feature["limit_fraction"]),
                "current_batch_robust_z": float(feature["current_batch_robust_z"]),
                "slope_batch_robust_z": float(feature["slope_batch_robust_z"]),
                "peer_count": peer_count,
                "peer_comparison_warning": "Fewer than eight comparable peers; batch comparison is weak" if peer_count < 8 else None,
                "early_readings": [{"hours": float(r.hours), "measurement_value": float(r.measurement_value), "unit": UNIT} for r in group.itertuples()],
                "metadata": {column: last[column] for column in METADATA_COLUMNS if column in group},
                "missing_optional_features": missing_optional,
                "prediction_readiness": "outside_training_conditions" if outside_range else ("optional_inputs_imputed" if missing_optional else "ready"),
                "out_of_training_range_features": outside_range,
                "prediction_readiness_warning": "Forecast extrapolates beyond observed training conditions; validation and interval coverage do not transfer" if outside_range else None,
                "xgboost_explanation": {
                    "explains": explanation_text + ("; this part sits inside the quiet gate, so the forecast is the 24 h value with no learned correction" if active_model == RESIDUAL_XGB_NAME and bool(bundle.models[RESIDUAL_XGB_NAME].quiet(matrix[position:position + 1])[0]) else ""),
                    "is_active_forecast": active_model in ("xgboost", RESIDUAL_XGB_NAME),
                    "explained_model": RESIDUAL_XGB_NAME if active_model == RESIDUAL_XGB_NAME else "xgboost",
                    "base_value_ua": explanation_base,
                    "top_contributions": [{"feature": contribution_names[index], "contribution_ua": float(contributions[index] * limit), "feature_value": float(matrix[position, FORECAST_COLUMNS.index(contribution_names[index])])} for index in top_contributors],
                },
            })
            records.append(record)
    records.extend(unscored)
    response = {
        "metadata": {
            "prototype_version": VERSION, "bundle_id": bundle.manifest["bundle_id"],
            "as_of_hour": AS_OF_HOUR, "target_hour": TARGET_HOUR, "unit": UNIT,
            "supported_family": "MLCC_X7R", "supported_measurement": "leakage_ua",
            "selected_model": active_model, "validation_winner": bundle.selected_model, "model_training_data": "synthetic",
            "forecast_selection": "explicit caller choice" if forecast_model else "internal validation winner",
            "selection_warning": "Requested candidate is not the lowest-MAE internal-validation model" if active_model != bundle.selected_model else None,
            "model_fitted_during_request": False,
        },
        "summary": {
            "component_count": len(records), "scored_count": len(records) - len(unscored),
            "unscored_count": len(unscored),
            "recommendations": dict(Counter(record["recommendation"] for record in records)),
            "within_limit_but_anomalous": sum(bool(record["is_anomaly"]) and record["current_value"] < record["safety_limit"] for record in records if record["status"] == "scored"),
        },
        "records": records,
    }
    if future_outcomes is not None:
        if not set(GROUP_COLUMNS).issubset(future_outcomes.columns):
            raise ValueError("Outcome reveal needs complete component measurement identities")
        outcomes = future_outcomes.copy()
        for column in GROUP_COLUMNS:
            outcomes[column] = outcomes[column].astype(str)
        identities = pd.DataFrame([{column: record[column] for column in GROUP_COLUMNS} for record in records])
        outcomes = outcomes.merge(identities, on=GROUP_COLUMNS, how="inner", validate="many_to_one")
        if {"hours", "measurement_value"}.issubset(outcomes.columns):
            for column in ("hours", "measurement_value"):
                outcomes[column] = pd.to_numeric(outcomes[column], errors="coerce")
                if not np.isfinite(outcomes[column]).all():
                    raise ValueError(f"Outcome {column} must be finite")
            if (outcomes["hours"] <= AS_OF_HOUR).any() or outcomes.duplicated(GROUP_COLUMNS + ["hours"]).any():
                raise ValueError("Outcome reveal requires unique observations after 24 h")
            outcomes["unit"] = UNIT
            response["future_outcomes"] = outcomes[GROUP_COLUMNS + ["hours", "measurement_value", "unit"]].to_dict("records")
        elif "final_value" in outcomes:
            allowed = GROUP_COLUMNS + ["final_value", "true_final_value", "is_future_failure", "is_observed_final_exceedance", "is_tester_fault", "scenario"]
            response["simulation_truth"] = outcomes[[c for c in allowed if c in outcomes]].to_dict("records")
        else:
            raise ValueError("Outcomes need hours/measurement_value or explicitly labelled simulator final_value")
    return _json_safe(response)


def _evaluate(
    features: pd.DataFrame, labels: pd.DataFrame, bundle: ModelBundle,
) -> dict[str, Any]:
    matrix = bundle.imputer.transform(features[FORECAST_COLUMNS])
    limits = features["upper_limit"].to_numpy(float)
    actual = labels["final_value"].to_numpy(float)
    y = actual / limits
    observed = actual >= limits
    latent = _bool_labels(labels, "is_future_failure")
    clean_tester = ~_bool_labels(labels, "is_tester_fault")
    anomalies = bundle.detector.score(features)
    anomalous = anomalies["is_anomaly"].to_numpy(bool)
    result: dict[str, Any] = {"components": len(features), "batches": features["batch_id"].nunique(), "models": {}}
    for name in ["persistence", "linear_extrapolation", *bundle.models]:
        pred = _predict(name, bundle.models, matrix, features)
        radius = bundle.radii[name]
        lower, upper = np.maximum(0, pred - radius), pred + radius
        crossing = pred >= 1.0
        metric = {
            "mae_normalized": float(np.abs(pred - y).mean()),
            "mae_ua": float(np.abs(pred * limits - actual).mean()),
            "interval_coverage": float(((y >= lower) & (y <= upper)).mean()),
            "mean_interval_width_normalized": float((upper - lower).mean()),
            "mean_interval_width_ua": float(((upper - lower) * limits).mean()),
            "observed_final_crossing": _classification(observed, crossing),
            "latent_physical_crossing_excluding_tester_faults": _classification(latent[clean_tester], crossing[clean_tester]),
            "by_profile": {},
        }
        if "profile_id" in labels:
            for profile in sorted(labels["profile_id"].unique()):
                mask = labels["profile_id"].eq(profile).to_numpy()
                metric["by_profile"][profile] = {
                    "components": int(mask.sum()), "mae_normalized": float(np.abs(pred[mask] - y[mask]).mean()),
                    "mae_ua": float(np.abs((pred * limits - actual)[mask]).mean()),
                    "interval_coverage": float(((y >= lower) & (y <= upper))[mask].mean()),
                    "mean_interval_width_ua": float(((upper - lower) * limits)[mask].mean()),
                }
        stratified = (bundle.manifest.get("interval", {}) or {}).get("stratified") or {}
        if stratified.get("model") == name:
            s = stratified_bounds(pred, features["slope_batch_robust_z"].to_numpy(float), stratified["margins"])
            healthy_mask = ~_bool_labels(labels, "is_defect") & clean_tester if "is_defect" in labels else None
            covered = (y >= s["lower"]) & (y <= s["upper"]); covered_wide = (y >= s["lower_two_sided"]) & (y <= s["upper_two_sided"])
            per_batch = pd.Series(covered).groupby(features["batch_id"].to_numpy()).mean()
            metric["stratified_interval"] = {
                "method": STRATIFIED_INTERVAL_METHOD,
                "reported_interval": "[one-sided lower, one-sided upper], nominal two-sided 0.8 with a 0.9 one-sided upper bound",
                "coverage": float(covered.mean()), "upper_bound_coverage": float((y <= s["upper"]).mean()),
                "two_sided_90_coverage": float(covered_wide.mean()),
                "mean_width_normalized": float((s["upper"] - s["lower"]).mean()), "median_width_ua": float(np.median((s["upper"] - s["lower"]) * limits)),
                "coverage_healthy": float(covered[healthy_mask].mean()) if healthy_mask is not None and healthy_mask.any() else None,
                "coverage_nonhealthy": float(covered[~healthy_mask].mean()) if healthy_mask is not None and (~healthy_mask).any() else None,
                "per_batch_coverage_min": float(per_batch.min()), "per_batch_coverage_max": float(per_batch.max()),
                "share_upper_at_or_above_limit": float((s["upper"] >= 1.0).mean()),
            }
        result["models"][name] = metric
    selected = _predict(bundle.selected_model, bundle.models, matrix, features)
    radius = bundle.radii[bundle.selected_model]
    stratified = (bundle.manifest.get("interval", {}) or {}).get("stratified") or {}
    if stratified.get("model") == bundle.selected_model:
        sel = stratified_bounds(selected, features["slope_batch_robust_z"].to_numpy(float), stratified["margins"])
        sel_lower, sel_upper = sel["lower"], sel["upper"]
    else:
        sel_lower, sel_upper = np.maximum(0, selected - radius), selected + radius
    actions = []
    for index, anomaly in enumerate(bundle.detector.to_results(anomalies)):
        prediction = PredictionResult(float(selected[index] * limits[index]), float(sel_lower[index] * limits[index]), float(sel_upper[index] * limits[index]))
        actions.append(build_screening_record(anomaly, prediction)["recommendation"])
    alerts = np.array([action != "ACCEPT" for action in actions])
    result["anomaly_detection"] = {
        "observed_final_crossing": _classification(observed, anomalous),
        "latent_physical_crossing_excluding_tester_faults": _classification(latent[clean_tester], anomalous[clean_tester]),
        "note": "Unusual early behaviour and future failure are distinct labels; this is early warning recall against final crossings",
    }
    result["combined_screening"] = {
        "alert_definition": "recommendation is MONITOR, RETEST or ENGINEER_REVIEW",
        "observed_final_crossing": _classification(observed, alerts),
        "latent_physical_crossing_excluding_tester_faults": _classification(latent[clean_tester], alerts[clean_tester]),
        "recommendations": dict(Counter(actions)),
    }
    if "scenario" in labels:
        result["combined_screening"]["by_scenario"] = {
            str(scenario): {"components": int(mask.sum()), "alert_rate": float(alerts[mask].mean())}
            for scenario in sorted(labels["scenario"].unique())
            for mask in [labels["scenario"].eq(scenario).to_numpy()]
        }
    return _json_safe(result)


def _hash(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def train_bundle(
    dataset_dir: str | Path, output_dir: str | Path, *, seed: int = 26170,
    alpha: float = 0.1,
) -> dict[str, Any]:
    """Train offline, calibrate once, evaluate untouched batches and persist."""
    import skops.io as sio

    dataset_dir, output_dir = Path(dataset_dir), Path(output_dir)
    if (output_dir / "manifest.json").exists():
        raise FileExistsError("A bundle already exists here; choose a new output directory")
    prepared: dict[str, tuple[pd.DataFrame, pd.DataFrame]] = {}
    hashes: dict[str, str] = {}
    split_summary: dict[str, Any] = {}
    for split in ("train", "calibration", "test"):
        early_path, label_path = dataset_dir / f"{split}_early.csv", dataset_dir / f"{split}_labels.csv"
        features, split_early, unscored = prepare_early_features(pd.read_csv(early_path, dtype={column: str for column in GROUP_COLUMNS}))
        if unscored or features.empty:
            raise ValueError(f"{split} training/evaluation data has {len(unscored)} invalid components")
        # Match the published dataset's stable batch/device order for sampling
        # and model fitting, independently of input file row order.
        features = features.sort_values(["batch_id", "component_id", "component_family", "measurement_name"]).reset_index(drop=True)
        labels = _joined_labels(features, pd.read_csv(label_path, dtype={column: str for column in GROUP_COLUMNS}))
        prepared[split] = features, labels
        hashes[early_path.name], hashes[label_path.name] = _hash(early_path), _hash(label_path)
        split_summary[split] = {"components": len(features), "batch_ids": sorted(features["batch_id"].unique().tolist())}
    for left, right in (("train", "calibration"), ("train", "test"), ("calibration", "test")):
        for identity in ("batch_id", "component_id"):
            if set(prepared[left][0][identity]) & set(prepared[right][0][identity]):
                raise ValueError(f"{identity} overlaps {left} and {right}; whole batches and devices must be disjoint")
    train, labels = prepared["train"]
    training_readings = pd.read_csv(dataset_dir / "train_early.csv", dtype={column: str for column in GROUP_COLUMNS})
    if train["batch_id"].nunique() < 5:
        raise ValueError("At least five training batches are needed for internal model selection")
    y = labels["final_value"].to_numpy(float) / train["upper_limit"].to_numpy(float)
    fit_index, validation_index = next(GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=seed).split(train, groups=train["batch_id"]))
    internal_imputer = SimpleImputer(strategy="median", keep_empty_features=True)
    internal_fit = internal_imputer.fit_transform(train.iloc[fit_index][FORECAST_COLUMNS])
    internal_validation = internal_imputer.transform(train.iloc[validation_index][FORECAST_COLUMNS])
    internal_models = _new_models(seed)
    with threadpool_limits(limits=1):
        for model in internal_models.values():
            model.fit(internal_fit, y[fit_index])
        validation_mae = {
            name: float(np.abs(_predict(name, internal_models, internal_validation, train.iloc[validation_index]) - y[validation_index]).mean())
            for name in ["persistence", "linear_extrapolation", *internal_models]
        }
        selected = min(validation_mae, key=validation_mae.get)
        imputer = SimpleImputer(strategy="median", keep_empty_features=True)
        train_matrix = imputer.fit_transform(train[FORECAST_COLUMNS])
        models = _new_models(seed)
        for model in models.values():
            model.fit(train_matrix, y)
        detector = BatchAwareAnomalyDetector(contamination=0.1, random_state=seed).fit(train)
        calibration, calibration_labels = prepared["calibration"]
        calibration_matrix = imputer.transform(calibration[FORECAST_COLUMNS])
        calibration_y = calibration_labels["final_value"].to_numpy(float) / calibration["upper_limit"].to_numpy(float)
        radii = {
            name: conformal_radius(calibration_y, _predict(name, models, calibration_matrix, calibration), alpha)
            for name in ["persistence", "linear_extrapolation", *models]
        }
        v2_calibration_residual = calibration_y - _predict(RESIDUAL_XGB_NAME, models, calibration_matrix, calibration)
        stratified_margins = stratified_interval_margins(v2_calibration_residual, calibration["slope_batch_robust_z"].to_numpy(float), alpha)
        manifest = {
            "prototype_version": VERSION, "bundle_id": sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()[:16] + f"-s{seed}",
            "family": "MLCC_X7R", "measurement": "leakage_ua", "unit": UNIT,
            "supported_profiles": sorted(training_readings["profile_id"].dropna().astype(str).unique().tolist()) if "profile_id" in training_readings else [],
            "as_of_hour": AS_OF_HOUR, "target_hour": TARGET_HOUR,
            "feature_columns": FORECAST_COLUMNS, "selected_model": selected,
            "seed": seed, "alpha": alpha, "training_data": "synthetic",
            "target": "observed final_value / per-component upper_limit",
            "target_clipping": "Nonnegative predictions only; no upper clipping",
            "selection": {"rule": "Lowest normalized MAE on internal heldout training batches; calibration and test are not used for selection", "validation_mae_normalized": validation_mae,
                          "fit_batch_ids": sorted(train.iloc[fit_index]["batch_id"].unique().tolist()), "validation_batch_ids": sorted(train.iloc[validation_index]["batch_id"].unique().tolist())},
            "split_summary": split_summary, "dataset_sha256": hashes,
            "interval": {"method": "Split-conformal absolute normalized residual; ceil((n+1)*(1-alpha)) order statistic", "radii_normalized": radii,
                         "stratified": {"model": RESIDUAL_XGB_NAME, "method": STRATIFIED_INTERVAL_METHOD, "stratum_feature": "slope_batch_robust_z", "edges": list(INTERVAL_STRATA_EDGES), "min_stratum_components": INTERVAL_MIN_STRATUM, "margins": stratified_margins,
                                        "reported_interval": "prediction_lower/prediction_upper are the one-sided (1-alpha) bounds of each stratum (a two-sided 1-2*alpha interval); the two-sided (1-alpha) bounds are reported as prediction_lower_two_sided/prediction_upper_two_sided",
                                        "note": "Signed-residual (observed - forecast) quantiles per slope-z stratum on the calibration batches; lower bounds clipped at zero; used only when xgboost_v2 is the active forecast"},
                         "limitation": "Device dependence within batches limits exchangeability; nominal coverage is not a guarantee. Synthetic empirical coverage is not real-world validation."},
            "forecast_v2": {"model": RESIDUAL_XGB_NAME, "features": RESIDUAL_XGB_FEATURES, "objective": RESIDUAL_XGB_PARAMS["objective"], "target": "observed final_value / upper_limit with base_margin = 24 h value / upper_limit (correction over persistence)", "params": RESIDUAL_XGB_PARAMS,
                            "gate": {"rule": "persistence forecast when |slope_batch_robust_z| and |current_batch_robust_z| are both below the threshold", "threshold": RESIDUAL_XGB_GATE_Z},
                            "artifact": RESIDUAL_XGB_FILE, "provenance": "Claude forecasting v2 (training-only whole-batch experiment, 2026-09-06); see docs/CLAUDE_FORECAST_V2_HANDOFF.md"},
            "versions": {package: importlib.metadata.version(package) for package in ("numpy", "pandas", "scikit-learn", "xgboost", "skops")},
            "anomaly": {"contamination": 0.1, "robust_threshold": 3.5, "score_semantics": "Ranking score; not a failure probability", "fit_scope": "Training batches only; batch peer statistics recomputed from the uploaded 0/24 readings"},
            "training_condition_ranges": {column: [float(train[column].min()), float(train[column].max())] for column in CONDITION_COLUMNS if train[column].notna().any()},
            "limitations": ["Only exact 0/24-hour MLCC_X7R leakage measurements in uA are supported", "Synthetic scenarios are not physical diagnoses", "Single sparse batches weaken peer comparison", "Missing optional features are median-imputed; accuracy outside the training distribution is not established", "Candidate hyperparameters were fixed before test evaluation"],
        }
        bundle = ModelBundle(manifest, imputer, detector, models, radii)
        evaluation = {"test": _evaluate(*prepared["test"], bundle), "selected_model": selected, "claim": "Untouched synthetic test batches only; no field accuracy claim"}
        evaluation["xgboost_feature_importance"] = sorted(
            [{"feature": column, "importance": float(importance)} for column, importance in zip(FORECAST_COLUMNS, models["xgboost"].feature_importances_)],
            key=lambda item: item["importance"], reverse=True,
        )
        evaluation["xgboost_v2_feature_importance"] = sorted(
            [{"feature": column, "importance": float(importance)} for column, importance in zip(RESIDUAL_XGB_FEATURES, models[RESIDUAL_XGB_NAME].model.feature_importances_)],
            key=lambda item: item["importance"], reverse=True,
        )
    output_dir.mkdir(parents=True, exist_ok=True)
    state = {"imputer": imputer, "detector_pipeline": detector.pipeline,
             "detector_training_strengths": detector._training_strengths,
             "models": {name: model for name, model in models.items() if name not in ("xgboost", RESIDUAL_XGB_NAME)}, "radii": radii}
    sio.dump(state, output_dir / "state.skops")
    models["xgboost"].save_model(output_dir / "xgboost.json")
    models[RESIDUAL_XGB_NAME].save_model(output_dir / RESIDUAL_XGB_FILE)
    (output_dir / "evaluation.json").write_text(json.dumps(_json_safe(evaluation), indent=2, allow_nan=False) + "\n")
    manifest["artifact_sha256"] = {name: _hash(output_dir / name) for name in ("state.skops", "xgboost.json", RESIDUAL_XGB_FILE, "evaluation.json")}
    (output_dir / "manifest.json").write_text(json.dumps(_json_safe(manifest), indent=2, allow_nan=False) + "\n")
    return {"bundle_dir": str(output_dir.resolve()), "selected_model": selected,
            "validation_mae_normalized": validation_mae, "test": evaluation["test"]}


def load_bundle(path: str | Path) -> ModelBundle:
    """Load a locally approved bundle; do not expose model upload in the API."""
    import skops.io as sio
    from xgboost import XGBRegressor

    directory = Path(path)
    manifest = json.loads((directory / "manifest.json").read_text())
    if manifest.get("prototype_version") not in COMPATIBLE_VERSIONS or manifest.get("feature_columns") != FORECAST_COLUMNS:
        raise ValueError("Unsupported model version or feature schema")
    has_v2 = RESIDUAL_XGB_FILE in manifest.get("artifact_sha256", {})
    for name in ("state.skops", "xgboost.json", "evaluation.json") + ((RESIDUAL_XGB_FILE,) if has_v2 else ()):
        if not (directory / name).is_file() or _hash(directory / name) != manifest["artifact_sha256"][name]:
            raise ValueError(f"Artifact integrity check failed: {name}")
    for package, expected in manifest["versions"].items():
        if importlib.metadata.version(package) != expected:
            raise ValueError(f"Version mismatch for {package}; use the bundle's recorded environment")
    unknown = set(sio.get_untrusted_types(file=directory / "state.skops"))
    if unknown - SKOPS_ALLOWED_TYPES:
        raise ValueError(f"Unexpected model types: {sorted(unknown - SKOPS_ALLOWED_TYPES)}")
    state = sio.load(directory / "state.skops", trusted=sorted(unknown))
    detector = BatchAwareAnomalyDetector(
        contamination=manifest["anomaly"]["contamination"],
        robust_threshold=manifest["anomaly"]["robust_threshold"], random_state=manifest["seed"],
    )
    detector.pipeline = state["detector_pipeline"]
    detector._training_strengths = state["detector_training_strengths"]
    model = XGBRegressor()
    model.load_model(directory / "xgboost.json")
    models = {**state["models"], "xgboost": model}
    if has_v2:
        models[RESIDUAL_XGB_NAME] = ResidualOverPersistenceXGB.load(directory / RESIDUAL_XGB_FILE)
    return ModelBundle(manifest, state["imputer"], detector, models, state["radii"])
