"""Claude v2 forecasting candidate for SIH26170 MLCC burn-in screening.

Scope: a training-only experiment runner plus a frozen inference candidate that
predicts the observed 168 h leakage (in uA) from exactly the 0 h and 24 h
readings. Everything here is additive to v1: the shared 0/24 h feature
definitions in ``sih26170.features`` / ``sih26170.mlcc_prototype`` are reused
unchanged, and nothing in this module fits, tunes or downloads anything inside
``predict``. Synthetic benchmark numbers are software-development evidence, not
field accuracy.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
import importlib.metadata
import json
import math
from pathlib import Path
import platform
from typing import Any, Iterable, Sequence

import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

from .features import GROUP_COLUMNS, MODEL_FEATURE_COLUMNS
from .mlcc_prototype import (
    AS_OF_HOUR,
    FORECAST_COLUMNS,
    TARGET_HOUR,
    UNIT,
    prepare_early_features,
)


VERSION = "claude-forecast-v2.0"
FAMILY = "MLCC_X7R"
MEASUREMENT = "leakage_ua"
IDENTITY = list(GROUP_COLUMNS)  # component_id, batch_id, component_family, measurement_name
SORT_KEYS = ["batch_id", "component_id", "component_family", "measurement_name"]
DEFAULT_SEED = 26170
DEFAULT_FOLDS = 5

# --------------------------------------------------------------------------- #
# Feature allowlists. Only 0/24 h information. No identifiers, no labels.
# --------------------------------------------------------------------------- #
LEAKAGE_FEATURES: list[str] = MODEL_FEATURE_COLUMNS + ["initial_fraction_of_limit"]
# Early auxiliary measurements that vary per component (capacitance and loss
# factor at 0/24 h, their change, and the per-component storage history).
AUX_FEATURES: list[str] = [
    "initial_capacitance_fraction",
    "current_capacitance_fraction",
    "capacitance_change_fraction",
    "initial_dissipation_factor_pct",
    "current_dissipation_factor_pct",
    "dissipation_factor_change_pct",
    "prior_storage_humidity_batch_rank_v2",
]
# v2-namespaced feature formulas (documented in docs/CLAUDE_FORECAST_V2_HANDOFF.md).
# prior_storage_humidity_pct has a 0.72 between-batch variance share in training
# (a partial lot identifier), so v2 uses only its within-batch percentile rank.
CHANNEL_PEER_FEATURES: list[str] = [
    "channel_peer_median_current_z_v2",
    "channel_peer_elevated_fraction_v2",
]
MIN_CHANNEL_PEERS = 5
V2_FEATURE_FORMULAS: dict[str, str] = {
    "prior_storage_humidity_batch_rank_v2": "percentile rank (0-1, average ties) of prior_storage_humidity_pct among the components of the same batch_id/component_family/measurement_name in the same upload; NaN when humidity is missing",
    "channel_peer_median_current_z_v2": "leave-one-out median of current_batch_robust_z over the OTHER components sharing the same batch_id/component_family/measurement_name/tester_channel in the same upload; NaN (then median-imputed) when tester_channel is missing or fewer than MIN_CHANNEL_PEERS peers are present",
    "channel_peer_elevated_fraction_v2": "leave-one-out fraction of those channel peers whose current_batch_robust_z exceeds 3; same NaN rule. A shared elevation across a channel indicates a possible instrument/channel effect rather than a component property; tester_channel identity itself is never a feature",
}
# Batch-constant test conditions (one value per batch => 36 distinct values in
# training). They are kept ONLY inside the v1 replica feature set.
CONDITION_FEATURES: list[str] = [
    "temperature_c",
    "measurement_temperature_c",
    "voltage_stress_ratio",
    "measurement_voltage_v",
]
FEATURE_SETS: dict[str, list[str]] = {
    "v1_all": list(FORECAST_COLUMNS),
    "leakage_only": list(LEAKAGE_FEATURES),
    "leakage_plus_aux": list(LEAKAGE_FEATURES) + list(AUX_FEATURES),
    "leakage_plus_channel_peer": list(LEAKAGE_FEATURES) + list(CHANNEL_PEER_FEATURES),
}
FORBIDDEN_FEATURE_TOKENS = (
    "component_id", "batch_id", "profile_id", "part_number", "scenario",
    "final_value", "true_final", "is_future", "is_observed", "is_defect",
    "is_healthy", "is_tester", "onset", "ever_latent", "tester_id",
    "tester_channel", "board_position",
)
for _name, _columns in FEATURE_SETS.items():
    for _column in _columns:
        if any(token in _column for token in FORBIDDEN_FEATURE_TOKENS):
            raise RuntimeError(f"feature set {_name} contains a forbidden column {_column}")

TARGETS = (
    "normalized",                      # y = final / limit
    "log1p_normalized",                # log1p(y)
    "residual_over_persistence",       # y with base_margin = x24 / limit
    "log1p_residual_over_persistence", # log1p(y) with base_margin = log1p(x24 / limit)
)
BASELINE_MODELS = ("persistence", "linear_extrapolation")

# v1 hyperparameters, reused unchanged so that objective / target / feature-set
# comparisons are not confounded with tuning.
V1_XGB_PARAMS: dict[str, Any] = {
    "n_estimators": 350, "max_depth": 3, "learning_rate": 0.04,
    "min_child_weight": 12, "subsample": 0.9, "colsample_bytree": 0.9,
    "reg_lambda": 10.0, "tree_method": "hist",
}


@dataclass(frozen=True)
class CandidateConfig:
    """One predeclared forecasting configuration."""

    name: str
    model: str                       # persistence | linear_extrapolation | xgboost
    target: str = "normalized"
    feature_set: str = "leakage_only"
    objective: str | None = None
    params: dict[str, Any] = field(default_factory=dict)
    description: str = ""

    def __post_init__(self) -> None:
        if self.model not in BASELINE_MODELS + ("xgboost",):
            raise ValueError(f"unknown model family {self.model}")
        if self.target not in TARGETS:
            raise ValueError(f"unknown target {self.target}")
        if self.feature_set not in FEATURE_SETS:
            raise ValueError(f"unknown feature set {self.feature_set}")
        if self.model == "xgboost" and not self.objective:
            raise ValueError("xgboost configurations need an objective")

    @property
    def feature_columns(self) -> list[str]:
        return list(FEATURE_SETS[self.feature_set])

    def to_dict(self) -> dict[str, Any]:
        record = asdict(self)
        record["feature_columns"] = self.feature_columns
        return record


def config_digest(configs: Sequence[CandidateConfig]) -> str:
    payload = json.dumps([c.to_dict() for c in configs], sort_keys=True).encode()
    return sha256(payload).hexdigest()


# --------------------------------------------------------------------------- #
# The predeclared comparison. Fixed from the diagnostic findings BEFORE the
# experiment was run (see outputs/claude_forecast_v2/PREDECLARED_COMPARISON.md);
# scripts/claude_forecast_v2.py refuses to run if this list changes afterwards.
# Ladder from v1 to the hypothesised best: drop batch-identifier columns ->
# residual-over-persistence target -> MAE-consistent objective -> add part-level
# aux or same-channel peer statistics back.
# --------------------------------------------------------------------------- #
PREDECLARED_CONFIGS: tuple[CandidateConfig, ...] = (
    CandidateConfig("persistence", "persistence", description="baseline: 168 h value = 24 h value"),
    CandidateConfig("linear_extrapolation", "linear_extrapolation", description="baseline: 24 h value + 0-24 h slope x 144 h"),
    CandidateConfig("xgb_v1_replica", "xgboost", target="normalized", feature_set="v1_all", objective="reg:squarederror", description="v1 configuration reproduced (includes batch-constant condition columns)"),
    CandidateConfig("xgb_sq_norm_leak", "xgboost", target="normalized", feature_set="leakage_only", objective="reg:squarederror", description="v1 objective/target without aux or condition columns"),
    CandidateConfig("xgb_sq_resid_leak", "xgboost", target="residual_over_persistence", feature_set="leakage_only", objective="reg:squarederror", description="squared error on the correction over persistence"),
    CandidateConfig("xgb_abs_norm_leak", "xgboost", target="normalized", feature_set="leakage_only", objective="reg:absoluteerror", description="MAE-consistent objective on the raw normalized target"),
    CandidateConfig("xgb_abs_resid_leak", "xgboost", target="residual_over_persistence", feature_set="leakage_only", objective="reg:absoluteerror", description="hypothesised best: median correction over persistence, leakage-only"),
    CandidateConfig("xgb_huber_resid_leak", "xgboost", target="residual_over_persistence", feature_set="leakage_only", objective="reg:pseudohubererror", params={"huber_slope": 0.05}, description="pseudo-Huber with delta 0.05 normalized: between L1 and L2"),
    CandidateConfig("xgb_sq_log1p_leak", "xgboost", target="log1p_normalized", feature_set="leakage_only", objective="reg:squarederror", description="squared error on log1p(y): tail-taming transform alone"),
    CandidateConfig("xgb_sq_log1p_resid_leak", "xgboost", target="log1p_residual_over_persistence", feature_set="leakage_only", objective="reg:squarederror", description="squared error on log1p(y) with log1p(persistence) offset: multiplicative correction"),
    CandidateConfig("xgb_abs_resid_aux", "xgboost", target="residual_over_persistence", feature_set="leakage_plus_aux", objective="reg:absoluteerror", description="hypothesised best plus part-level capacitance/loss-factor features and batch-relative humidity rank"),
    CandidateConfig("xgb_abs_resid_peer", "xgboost", target="residual_over_persistence", feature_set="leakage_plus_channel_peer", objective="reg:absoluteerror", description="hypothesised best plus leave-one-out same-channel peer statistics (instrument-fault vs drift disambiguation)"),
)

SELECTION_RULE = (
    "Primary metric: normalized MAE (|prediction - observed final_value| / upper_limit) pooled over out-of-fold predictions on 5 "
    "profile-stratified whole-batch folds; ties broken by fold-mean MAE. Eligibility for recommendation: (a) pooled MAE below "
    "persistence and below persistence in at least 4 of 5 folds; (b) healthy-part MAE (is_healthy, retrospective) at most 0.02 "
    "normalized so the healthy majority is not inflated; (c) feature set must not contain the batch-constant condition columns "
    "(the v1 replica is a reference only, because those columns take one value per batch and act as batch identifiers). If nothing is eligible, persistence is recommended and XGBoost is reported as "
    "not beating the baseline. MAE in uA by profile, RMSE, mean signed error, crossing recall / false-positive rate / confusion "
    "counts (observed, new-below-limit-at-24h, latent excluding tester faults) and by-scenario MAE are reported for tradeoffs "
    "but do not drive selection. Hyperparameters are v1's for every configuration; no tuning."
)


# --------------------------------------------------------------------------- #
# Data loading and validation
# --------------------------------------------------------------------------- #
def _hash_file(path: Path) -> str:
    digest = sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


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


def write_json(path: Path, payload: Any) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(_json_safe(payload), indent=2, allow_nan=False) + "\n")


def _bool_series(values: pd.Series) -> pd.Series:
    if pd.api.types.is_bool_dtype(values):
        return values.astype(bool)
    mapping = {"true": True, "false": False, "1": True, "0": False}
    converted = values.astype(str).str.strip().str.lower().map(mapping)
    if converted.isna().any():
        raise ValueError(f"{values.name} must contain booleans")
    return converted.astype(bool)


def read_identity_csv(path: str | Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype={column: str for column in IDENTITY})


@dataclass
class TrainingData:
    """Aligned 0/24 h features and observed 168 h labels for training batches."""

    features: pd.DataFrame
    labels: pd.DataFrame
    input_hashes: dict[str, str]
    validation: dict[str, Any]

    @property
    def y(self) -> np.ndarray:
        return self.labels["y_normalized"].to_numpy(dtype=float)

    @property
    def limits(self) -> np.ndarray:
        return self.features["upper_limit"].to_numpy(dtype=float)

    @property
    def batch_ids(self) -> np.ndarray:
        return self.features["batch_id"].to_numpy(dtype=str)


def load_training_data(data_dir: str | Path) -> TrainingData:
    """Load, validate and join train_early.csv with train_labels.csv.

    Only 0/24 h rows become predictive features. Labels are joined on the full
    identity (never row position) and kept in a separate frame with the same
    row order. train_readings.csv is not loaded here on purpose.
    """
    data_dir = Path(data_dir)
    early_path, label_path = data_dir / "train_early.csv", data_dir / "train_labels.csv"
    early = read_identity_csv(early_path)
    labels = read_identity_csv(label_path)
    hours = pd.to_numeric(early["hours"], errors="coerce")
    if not set(hours.dropna().unique()).issubset({0.0, AS_OF_HOUR}):
        raise ValueError("train_early.csv must contain exactly 0 h and 24 h observations")
    features, validated_early, unavailable = prepare_early_features(early)
    if unavailable or features.empty:
        raise ValueError(f"{len(unavailable)} training components failed the shared 0/24 h validation")
    features = augment_features(features, validated_early).sort_values(SORT_KEYS).reset_index(drop=True)
    if labels.duplicated(IDENTITY).any():
        raise ValueError("train_labels.csv has duplicate identities")
    joined = features[IDENTITY].merge(labels, on=IDENTITY, how="left", validate="one_to_one")
    final = pd.to_numeric(joined["final_value"], errors="coerce")
    if final.isna().any():
        raise ValueError(f"{int(final.isna().sum())} training components have no observed final_value label")
    if (final < 0).any():
        raise ValueError("final_value must be nonnegative")
    joined["final_value"] = final.astype(float)
    joined["y_normalized"] = joined["final_value"] / features["upper_limit"].to_numpy(dtype=float)
    for column in ("is_future_failure", "is_observed_final_exceedance", "is_tester_fault", "is_defect", "is_healthy"):
        if column in joined:
            joined[column] = _bool_series(joined[column])
    # Profile metadata rides along for stratified evaluation only.
    profile_by_component = early.drop_duplicates("component_id").set_index("component_id")["profile_id"] if "profile_id" in early else None
    if profile_by_component is not None:
        features["profile_id"] = features["component_id"].map(profile_by_component).astype(str)
        joined["profile_id"] = features["profile_id"]
    validation = validate_training_inputs(early, features, joined)
    hashes = {early_path.name: _hash_file(early_path), label_path.name: _hash_file(label_path)}
    return TrainingData(features=features, labels=joined, input_hashes=hashes, validation=validation)


def validate_training_inputs(early: pd.DataFrame, features: pd.DataFrame, labels: pd.DataFrame) -> dict[str, Any]:
    y = labels["y_normalized"].to_numpy(dtype=float)
    quantiles = [0.01, 0.05, 0.25, 0.5, 0.75, 0.9, 0.95, 0.99, 0.999]
    summary: dict[str, Any] = {
        "early_rows": int(len(early)),
        "components": int(features["component_id"].nunique()),
        "batches": int(features["batch_id"].nunique()),
        "components_per_batch": {"min": int(features.groupby("batch_id").size().min()), "max": int(features.groupby("batch_id").size().max())},
        "hours_present": sorted(float(h) for h in pd.to_numeric(early["hours"]).unique()),
        "early_rows_per_component": {str(k): int(v) for k, v in early.groupby("component_id").size().value_counts().items()},
        "missing_values_early": {c: int(n) for c, n in early.isna().sum().items() if n},
        "missing_values_labels": {c: int(n) for c, n in labels.isna().sum().items() if n},
        "nonfinite_feature_values": {c: int((~np.isfinite(pd.to_numeric(features[c], errors="coerce"))).sum()) for c in sorted(set(FORECAST_COLUMNS) | set(AUX_FEATURES) | set(CHANNEL_PEER_FEATURES)) if c in features and (~np.isfinite(pd.to_numeric(features[c], errors="coerce"))).sum()},
        "target": {
            "definition": "y_normalized = observed final_value at 168 h / per-component upper_limit",
            "quantiles": {str(q): float(np.quantile(y, q)) for q in quantiles},
            "mean": float(y.mean()), "std": float(y.std(ddof=0)), "min": float(y.min()), "max": float(y.max()),
            "final_value_ua_quantiles": {str(q): float(np.quantile(labels["final_value"], q)) for q in quantiles},
        },
        "observed_final_crossing_count": int((y >= 1.0).sum()),
        "already_at_or_above_limit_at_24h": int((features["limit_fraction"].to_numpy(dtype=float) >= 1.0).sum()),
    }
    for column in ("is_future_failure", "is_observed_final_exceedance", "is_tester_fault", "is_defect", "is_healthy"):
        if column in labels:
            summary[f"{column}_count"] = int(labels[column].sum())
    if "profile_id" in features:
        summary["profiles"] = {
            str(p): {
                "components": int(mask.sum()), "batches": int(features.loc[mask, "batch_id"].nunique()),
                "upper_limit_ua": sorted(float(v) for v in features.loc[mask, "upper_limit"].unique()),
                "observed_final_crossings": int((y[mask.to_numpy()] >= 1.0).sum()),
                "y_median": float(np.median(y[mask.to_numpy()])),
            }
            for p in sorted(features["profile_id"].unique()) for mask in [features["profile_id"].eq(p)]
        }
        summary["profiles_per_batch"] = {str(k): int(v) for k, v in features.groupby("batch_id")["profile_id"].nunique().value_counts().items()}
    if "scenario" in labels:
        summary["scenario_counts"] = {str(k): int(v) for k, v in labels["scenario"].value_counts().items()}
    return summary


# --------------------------------------------------------------------------- #
# Whole-batch folds
# --------------------------------------------------------------------------- #
def assign_batch_folds(features: pd.DataFrame, *, n_splits: int = DEFAULT_FOLDS) -> pd.DataFrame:
    """Deterministic profile-stratified whole-batch folds.

    Every batch lands in exactly one validation fold (GroupKFold semantics).
    Batches are sorted within each profile and dealt round-robin so every fold
    sees every profile. No randomness, so the assignment is reproducible from
    the batch identifiers alone.
    """
    if n_splits < 2:
        raise ValueError("at least two folds are required")
    batches = features.drop_duplicates("batch_id")[["batch_id"] + (["profile_id"] if "profile_id" in features else [])].copy()
    if "profile_id" not in batches:
        batches["profile_id"] = "*"
    batches = batches.sort_values(["profile_id", "batch_id"]).reset_index(drop=True)
    if batches["batch_id"].nunique() < n_splits:
        raise ValueError("fewer batches than folds")
    folds: list[int] = []
    cursor = 0
    for _, group in batches.groupby("profile_id", sort=True):
        for _ in range(len(group)):
            folds.append(cursor % n_splits)
            cursor += 1
    batches["fold"] = folds
    return batches[["batch_id", "profile_id", "fold"]].sort_values("batch_id").reset_index(drop=True)


def fold_masks(features: pd.DataFrame, folds: pd.DataFrame) -> list[tuple[int, np.ndarray, np.ndarray]]:
    mapping = folds.set_index("batch_id")["fold"]
    assigned = features["batch_id"].map(mapping)
    if assigned.isna().any():
        raise ValueError("every batch needs a fold assignment")
    assigned = assigned.to_numpy(dtype=int)
    out = []
    for k in sorted(set(assigned.tolist())):
        validation = assigned == k
        out.append((int(k), ~validation, validation))
    return out


def assert_folds_disjoint(features: pd.DataFrame, folds: pd.DataFrame) -> None:
    for k, train, valid in fold_masks(features, folds):
        shared_batches = set(features.loc[train, "batch_id"]) & set(features.loc[valid, "batch_id"])
        shared_components = set(features.loc[train, "component_id"]) & set(features.loc[valid, "component_id"])
        if shared_batches or shared_components:
            raise ValueError(f"fold {k} shares batches or components between fit and validation")


# --------------------------------------------------------------------------- #
# Design matrices, targets, models
# --------------------------------------------------------------------------- #
def feature_matrix(features: pd.DataFrame, columns: Sequence[str]) -> pd.DataFrame:
    missing = [c for c in columns if c not in features.columns]
    if missing:
        raise ValueError(f"missing feature columns: {', '.join(missing)}")
    matrix = features[list(columns)].apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan)
    return matrix.astype(float)


def fit_medians(matrix: pd.DataFrame) -> dict[str, float]:
    medians = {}
    for column in matrix.columns:
        value = matrix[column].median(skipna=True)
        medians[column] = float(value) if np.isfinite(value) else 0.0
    return medians


def impute(matrix: pd.DataFrame, medians: dict[str, float]) -> np.ndarray:
    filled = matrix.copy()
    for column in filled.columns:
        filled[column] = filled[column].fillna(medians[column])
    return filled.to_numpy(dtype=float)


def augment_features(features: pd.DataFrame, early: pd.DataFrame | None = None) -> pd.DataFrame:
    """Add the v2-namespaced features to a shared 0/24 h feature frame.

    Uses only columns already present at 0/24 h and only peers inside the same
    uploaded batch; no labels, no fitting, no stored state. ``early`` is the
    validated 0/24 h reading frame (second return of prepare_early_features);
    it supplies tester_channel per component when available."""
    out = features.copy()
    peer_keys = ["batch_id", "component_family", "measurement_name"]
    if "prior_storage_humidity_pct" in out.columns:
        humidity = pd.to_numeric(out["prior_storage_humidity_pct"], errors="coerce")
        out["prior_storage_humidity_batch_rank_v2"] = humidity.groupby([out[k] for k in peer_keys], dropna=False).rank(pct=True, method="average")
    else:
        out["prior_storage_humidity_batch_rank_v2"] = np.nan
    channel = pd.Series(np.nan, index=out.index, dtype=float)
    if early is not None and "tester_channel" in early.columns:
        per_component = early.copy()
        per_component["component_id"] = per_component["component_id"].astype(str)
        per_component["tester_channel"] = pd.to_numeric(per_component["tester_channel"], errors="coerce")
        # a component must sit on one channel; otherwise treat the channel as unknown
        channel_by_component = per_component.groupby("component_id")["tester_channel"].agg(lambda v: v.iloc[0] if v.nunique(dropna=False) == 1 else np.nan)
        channel = out["component_id"].astype(str).map(channel_by_component).astype(float)
    z = pd.to_numeric(out["current_batch_robust_z"], errors="coerce").to_numpy(dtype=float)
    median_peer = np.full(len(out), np.nan)
    elevated_fraction = np.full(len(out), np.nan)
    keys = pd.DataFrame({k: out[k].astype(str).to_numpy() for k in peer_keys})
    keys["channel"] = channel.to_numpy()
    valid = np.isfinite(keys["channel"].to_numpy(dtype=float)) & np.isfinite(z)
    for _, index in keys.loc[valid].groupby(peer_keys + ["channel"], sort=False).indices.items():
        index = np.asarray(index)
        if len(index) - 1 < MIN_CHANNEL_PEERS:
            continue
        group_z = z[index]
        for position, row in enumerate(index):
            peers = np.delete(group_z, position)
            median_peer[row] = float(np.median(peers))
            elevated_fraction[row] = float(np.mean(peers > 3.0))
    out["channel_peer_median_current_z_v2"] = median_peer
    out["channel_peer_elevated_fraction_v2"] = elevated_fraction
    return out


def persistence_forecast(features: pd.DataFrame) -> np.ndarray:
    return features["limit_fraction"].to_numpy(dtype=float)


def linear_extrapolation_forecast(features: pd.DataFrame) -> np.ndarray:
    return (features["limit_fraction"] + features["slope_fraction_per_hour"] * (TARGET_HOUR - AS_OF_HOUR)).to_numpy(dtype=float)


def target_encoding(y: np.ndarray | None, persistence: np.ndarray, target: str) -> tuple[np.ndarray | None, np.ndarray | None]:
    """Return (training label, base_margin) for the chosen parameterisation."""
    persistence = np.asarray(persistence, dtype=float)
    if target == "normalized":
        return (None if y is None else np.asarray(y, dtype=float)), None
    if target == "log1p_normalized":
        return (None if y is None else np.log1p(np.asarray(y, dtype=float))), None
    if target == "residual_over_persistence":
        return (None if y is None else np.asarray(y, dtype=float)), persistence
    if target == "log1p_residual_over_persistence":
        return (None if y is None else np.log1p(np.asarray(y, dtype=float))), np.log1p(persistence)
    raise ValueError(f"unknown target {target}")


def decode_prediction(raw: np.ndarray, target: str) -> np.ndarray:
    raw = np.asarray(raw, dtype=float)
    decoded = np.expm1(raw) if target.startswith("log1p") else raw
    if not np.isfinite(decoded).all():
        raise ValueError("model produced a nonfinite forecast")
    # Leakage cannot be negative; deliberately no upper clipping (same as v1).
    return np.maximum(decoded, 0.0)


def make_xgboost(config: CandidateConfig, seed: int, n_jobs: int = 2):
    from xgboost import XGBRegressor

    params = {**V1_XGB_PARAMS, **config.params}
    return XGBRegressor(objective=config.objective, random_state=seed, n_jobs=n_jobs, **params)


@dataclass
class FittedModel:
    config: CandidateConfig
    medians: dict[str, float]
    booster: Any  # XGBRegressor or None for baselines

    def predict_normalized(self, features: pd.DataFrame) -> np.ndarray:
        persistence = persistence_forecast(features)
        if self.config.model == "persistence":
            return decode_prediction(persistence, "normalized")
        if self.config.model == "linear_extrapolation":
            return decode_prediction(linear_extrapolation_forecast(features), "normalized")
        matrix = impute(feature_matrix(features, self.config.feature_columns), self.medians)
        _, margin = target_encoding(None, persistence, self.config.target)
        raw = self.booster.predict(matrix) if margin is None else self.booster.predict(matrix, base_margin=margin)
        return decode_prediction(raw, self.config.target)


def fit_model(config: CandidateConfig, features: pd.DataFrame, y: np.ndarray, *, seed: int, n_jobs: int = 2) -> FittedModel:
    """Fit one configuration on the supplied rows only (fold training portion)."""
    matrix = feature_matrix(features, config.feature_columns)
    medians = fit_medians(matrix)
    if config.model in BASELINE_MODELS:
        return FittedModel(config, medians, None)
    label, margin = target_encoding(y, persistence_forecast(features), config.target)
    if label is None or not np.isfinite(label).all():
        raise ValueError("training labels must be finite after target encoding")
    model = make_xgboost(config, seed, n_jobs)
    X = impute(matrix, medians)
    if margin is None:
        model.fit(X, label)
    else:
        # With base_margin the margin replaces the intercept; fix base_score so the
        # saved model is unambiguous even if someone predicts without the margin.
        model.set_params(base_score=0.0)
        model.fit(X, label, base_margin=margin)
    return FittedModel(config, medians, model)


# --------------------------------------------------------------------------- #
# Metrics
# --------------------------------------------------------------------------- #
def _confusion(truth: np.ndarray, flag: np.ndarray) -> dict[str, Any]:
    truth, flag = np.asarray(truth, dtype=bool), np.asarray(flag, dtype=bool)
    tp = int((truth & flag).sum()); fn = int((truth & ~flag).sum())
    fp = int((~truth & flag).sum()); tn = int((~truth & ~flag).sum())
    return {
        "tp": tp, "fn": fn, "fp": fp, "tn": tn,
        "recall": tp / (tp + fn) if tp + fn else None,
        "false_positive_rate": fp / (fp + tn) if fp + tn else None,
        "precision": tp / (tp + fp) if tp + fp else None,
    }


STRATA_ORDER = ("healthy", "defect_onset_le24", "defect_onset_gt24", "tester_fault_onset_0_12", "tester_fault_onset_72")


def retrospective_strata(labels: pd.DataFrame) -> np.ndarray | None:
    """Mutually exclusive retrospective strata (labels only; never model inputs).

    Priority: tester fault (by onset) > defect (by onset) > healthy."""
    needed = {"is_defect", "is_tester_fault", "anomaly_onset_hour", "tester_fault_onset_hour"}
    if not needed.issubset(labels.columns):
        return None
    defect = _bool_series(labels["is_defect"]).to_numpy()
    tester = _bool_series(labels["is_tester_fault"]).to_numpy()
    onset = pd.to_numeric(labels["anomaly_onset_hour"], errors="coerce").to_numpy(dtype=float)
    tester_onset = pd.to_numeric(labels["tester_fault_onset_hour"], errors="coerce").to_numpy(dtype=float)
    out = np.full(len(labels), "healthy", dtype=object)
    out[defect & (onset <= AS_OF_HOUR)] = "defect_onset_le24"
    out[defect & (onset > AS_OF_HOUR)] = "defect_onset_gt24"
    out[tester & (tester_onset <= AS_OF_HOUR)] = "tester_fault_onset_0_12"
    out[tester & (tester_onset > AS_OF_HOUR)] = "tester_fault_onset_72"
    return out


def forecast_metrics(pred: np.ndarray, features: pd.DataFrame, labels: pd.DataFrame) -> dict[str, Any]:
    """Metrics for one set of normalized forecasts aligned with features/labels.
    Signed error is prediction minus observed throughout."""
    pred = np.asarray(pred, dtype=float)
    y = labels["y_normalized"].to_numpy(dtype=float)
    limits = features["upper_limit"].to_numpy(dtype=float)
    error = pred - y
    metrics: dict[str, Any] = {
        "components": int(len(y)),
        "batches": int(features["batch_id"].nunique()),
        "mae_normalized": float(np.abs(error).mean()),
        "median_abs_error_normalized": float(np.median(np.abs(error))),
        "rmse_normalized": float(np.sqrt((error ** 2).mean())),
        "mean_signed_error_normalized": float(error.mean()),
        "mae_ua": float(np.abs(error * limits).mean()),
        "observed_final_crossing": _confusion(y >= 1.0, pred >= 1.0),
    }
    already = features["limit_fraction"].to_numpy(dtype=float) >= 1.0
    metrics["already_at_or_above_limit_at_24h"] = {"components": int(already.sum()), "observed_final_crossing": _confusion(y[already] >= 1.0, pred[already] >= 1.0) if already.any() else None}
    metrics["new_observed_crossing_below_limit_at_24h"] = _confusion(y[~already] >= 1.0, pred[~already] >= 1.0)
    if "is_future_failure" in labels and "is_tester_fault" in labels:
        clean = ~labels["is_tester_fault"].to_numpy(dtype=bool)
        metrics["latent_crossing_excluding_tester_faults"] = _confusion(labels["is_future_failure"].to_numpy(dtype=bool)[clean], (pred >= 1.0)[clean])
    metrics["share_predictions_clipped_at_zero"] = float((pred <= 0.0).mean())
    strata = retrospective_strata(labels)
    if strata is not None:
        metrics["by_stratum"] = {
            name: {"components": int(mask.sum()), "mae_normalized": float(np.abs(error[mask]).mean()), "mean_signed_error": float(error[mask].mean()), "observed_final_crossing": _confusion(y[mask] >= 1.0, pred[mask] >= 1.0)}
            for name in STRATA_ORDER for mask in [strata == name] if mask.any()
        }
    if "is_healthy" in labels:
        healthy = labels["is_healthy"].to_numpy(dtype=bool)
        metrics["healthy_mae_normalized"] = float(np.abs(error[healthy]).mean()) if healthy.any() else None
        metrics["healthy_mean_signed_error_normalized"] = float(error[healthy].mean()) if healthy.any() else None
        metrics["nonhealthy_mae_normalized"] = float(np.abs(error[~healthy]).mean()) if (~healthy).any() else None
    if "profile_id" in features:
        metrics["by_profile"] = {}
        for profile in sorted(features["profile_id"].unique()):
            mask = features["profile_id"].eq(profile).to_numpy()
            metrics["by_profile"][str(profile)] = {
                "components": int(mask.sum()),
                "mae_normalized": float(np.abs(error[mask]).mean()),
                "mae_ua": float(np.abs(error[mask] * limits[mask]).mean()),
                "observed_final_crossing": _confusion(y[mask] >= 1.0, pred[mask] >= 1.0),
            }
    if "scenario" in labels:
        metrics["by_scenario_mae_normalized"] = {
            str(s): {"components": int(mask.sum()), "mae_normalized": float(np.abs(error[mask]).mean()), "mean_signed_error": float(error[mask].mean())}
            for s in sorted(labels["scenario"].astype(str).unique()) for mask in [labels["scenario"].astype(str).eq(s).to_numpy()]
        }
    return metrics


def summarize_folds(per_fold: list[dict[str, Any]]) -> dict[str, Any]:
    """Mean and spread across heldout folds of the headline scalar metrics."""
    keys = ["mae_normalized", "mae_ua", "rmse_normalized", "mean_signed_error_normalized", "healthy_mae_normalized", "nonhealthy_mae_normalized"]
    out: dict[str, Any] = {"folds": len(per_fold)}
    for key in keys:
        values = np.array([m[key] for m in per_fold if m.get(key) is not None], dtype=float)
        if len(values):
            out[key] = {"mean": float(values.mean()), "std": float(values.std(ddof=1)) if len(values) > 1 else 0.0, "min": float(values.min()), "max": float(values.max()), "per_fold": values.tolist()}
    recalls = [m["observed_final_crossing"]["recall"] for m in per_fold if m["observed_final_crossing"]["recall"] is not None]
    fprs = [m["observed_final_crossing"]["false_positive_rate"] for m in per_fold if m["observed_final_crossing"]["false_positive_rate"] is not None]
    out["observed_crossing_recall"] = {"mean": float(np.mean(recalls)), "std": float(np.std(recalls, ddof=1)) if len(recalls) > 1 else 0.0, "per_fold": recalls} if recalls else None
    out["observed_crossing_false_positive_rate"] = {"mean": float(np.mean(fprs)), "std": float(np.std(fprs, ddof=1)) if len(fprs) > 1 else 0.0, "per_fold": fprs} if fprs else None
    return out


# --------------------------------------------------------------------------- #
# Cross-validated experiment
# --------------------------------------------------------------------------- #
def environment_record() -> dict[str, Any]:
    packages = ("numpy", "pandas", "scikit-learn", "xgboost", "scipy", "threadpoolctl")
    versions = {}
    for package in packages:
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None
    return {"python": platform.python_version(), "platform": platform.platform(), "versions": versions}


def run_cross_validation(
    training: TrainingData,
    configs: Sequence[CandidateConfig],
    folds: pd.DataFrame,
    *,
    seed: int = DEFAULT_SEED,
    n_jobs: int = 2,
    log=None,
) -> tuple[dict[str, Any], pd.DataFrame]:
    """Fit every configuration on each fold's training batches and score the
    heldout batches. Returns (results, long out-of-fold prediction frame)."""
    names = [c.name for c in configs]
    if len(set(names)) != len(names):
        raise ValueError("configuration names must be unique")
    assert_folds_disjoint(training.features, folds)
    features, labels, y = training.features, training.labels, training.y
    oof_rows: list[pd.DataFrame] = []
    results: dict[str, Any] = {"configs": {}, "fold_assignment": folds.to_dict("records")}
    for config in configs:
        per_fold: list[dict[str, Any]] = []
        pooled = np.full(len(features), np.nan)
        for k, train_mask, valid_mask in fold_masks(features, folds):
            train_features = features.loc[train_mask].reset_index(drop=True)
            fitted = fit_model(config, train_features, y[train_mask], seed=seed, n_jobs=n_jobs)
            pred = fitted.predict_normalized(features.loc[valid_mask].reset_index(drop=True))
            pooled[valid_mask] = pred
            metric = forecast_metrics(pred, features.loc[valid_mask].reset_index(drop=True), labels.loc[valid_mask].reset_index(drop=True))
            metric["fold"] = k
            metric["train_mae_normalized"] = float(np.abs(fitted.predict_normalized(train_features) - y[train_mask]).mean())
            metric["validation_batches"] = sorted(features.loc[valid_mask, "batch_id"].unique().tolist())
            per_fold.append(metric)
            frame = features.loc[valid_mask, IDENTITY + ["upper_limit", "limit_fraction"] + (["profile_id"] if "profile_id" in features else [])].copy()
            frame["fold"] = k
            frame["config"] = config.name
            frame["predicted_normalized"] = pred
            frame["predicted_final_value_ua"] = pred * frame["upper_limit"].to_numpy(dtype=float)
            frame["y_normalized"] = y[valid_mask]
            frame["final_value_ua"] = labels.loc[valid_mask, "final_value"].to_numpy(dtype=float)
            oof_rows.append(frame)
            if log:
                log(f"{config.name} fold {k}: MAE {metric['mae_normalized']:.4f} normalized, {metric['mae_ua']:.4f} uA")
        if np.isnan(pooled).any():
            raise RuntimeError("out-of-fold predictions are incomplete")
        abs_error = np.abs(pooled - y)
        per_batch = pd.Series(abs_error).groupby(features["batch_id"].to_numpy()).mean()
        results["configs"][config.name] = {
            "config": config.to_dict(),
            "pooled": forecast_metrics(pooled, features, labels),
            "fold_summary": summarize_folds(per_fold),
            "per_fold": per_fold,
            "per_batch_mae_normalized": {str(k): float(v) for k, v in per_batch.items()},
        }
    persistence_batches = None
    if "persistence" in results["configs"]:
        persistence_batches = pd.Series(results["configs"]["persistence"]["per_batch_mae_normalized"])
    for name, entry in results["configs"].items():
        if persistence_batches is not None:
            mine = pd.Series(entry["per_batch_mae_normalized"])
            delta = (mine - persistence_batches.reindex(mine.index)).to_numpy(dtype=float)
            entry["batches_beating_persistence"] = int((delta < 0).sum())
            entry["batches_total"] = int(len(mine))
            entry["paired_batch_delta_vs_persistence"] = {"mean": float(delta.mean()), "std": float(delta.std(ddof=1)) if len(delta) > 1 else 0.0, "se": float(delta.std(ddof=1) / np.sqrt(len(delta))) if len(delta) > 1 else 0.0, "definition": "per-batch MAE(config) - MAE(persistence), negative is better"}
            entry["train_mae_normalized_fold_mean"] = float(np.mean([m["train_mae_normalized"] for m in entry["per_fold"]]))
            entry["folds_beating_persistence"] = int(sum(m < p for m, p in zip(entry["fold_summary"]["mae_normalized"]["per_fold"], results["configs"]["persistence"]["fold_summary"]["mae_normalized"]["per_fold"])))
    oof = pd.concat(oof_rows, ignore_index=True).sort_values(["config", "fold"] + SORT_KEYS).reset_index(drop=True)
    return results, oof


def comparison_table(results: dict[str, Any]) -> pd.DataFrame:
    rows = []
    for name, entry in results["configs"].items():
        pooled, summary = entry["pooled"], entry["fold_summary"]
        cross = pooled["observed_final_crossing"]
        latent = pooled.get("latent_crossing_excluding_tester_faults", {})
        rows.append({
            "config": name,
            "model": entry["config"]["model"], "objective": entry["config"]["objective"],
            "target": entry["config"]["target"], "feature_set": entry["config"]["feature_set"],
            "mae_norm_pooled": pooled["mae_normalized"],
            "mae_norm_fold_mean": summary["mae_normalized"]["mean"], "mae_norm_fold_std": summary["mae_normalized"]["std"],
            "folds_beating_persistence": entry.get("folds_beating_persistence"), "batches_beating_persistence": entry.get("batches_beating_persistence"), "batches_total": entry.get("batches_total"),
            "paired_batch_delta_mean": entry.get("paired_batch_delta_vs_persistence", {}).get("mean"), "paired_batch_delta_se": entry.get("paired_batch_delta_vs_persistence", {}).get("se"),
            "train_mae_norm_fold_mean": entry.get("train_mae_normalized_fold_mean"),
            "share_clipped_at_zero": pooled["share_predictions_clipped_at_zero"],
            "mae_ua_pooled": pooled["mae_ua"],
            "rmse_norm_pooled": pooled["rmse_normalized"],
            "mean_signed_error": pooled["mean_signed_error_normalized"],
            "healthy_mae_norm": pooled.get("healthy_mae_normalized"), "nonhealthy_mae_norm": pooled.get("nonhealthy_mae_normalized"),
            "crossing_recall": cross["recall"], "crossing_fpr": cross["false_positive_rate"], "crossing_precision": cross["precision"],
            "crossing_tp": cross["tp"], "crossing_fn": cross["fn"], "crossing_fp": cross["fp"], "crossing_tn": cross["tn"],
            "latent_recall_no_tester": latent.get("recall"), "latent_fpr_no_tester": latent.get("false_positive_rate"),
            "new_crossing_recall": pooled["new_observed_crossing_below_limit_at_24h"]["recall"], "new_crossing_fpr": pooled["new_observed_crossing_below_limit_at_24h"]["false_positive_rate"],
            "new_crossing_tp": pooled["new_observed_crossing_below_limit_at_24h"]["tp"], "new_crossing_fp": pooled["new_observed_crossing_below_limit_at_24h"]["fp"],
        })
    return pd.DataFrame(rows).sort_values("mae_norm_pooled").reset_index(drop=True)


def profile_table(results: dict[str, Any]) -> pd.DataFrame:
    rows = []
    for name, entry in results["configs"].items():
        for profile, metric in entry["pooled"].get("by_profile", {}).items():
            rows.append({"config": name, "profile_id": profile, "components": metric["components"], "mae_normalized": metric["mae_normalized"], "mae_ua": metric["mae_ua"], "crossing_recall": metric["observed_final_crossing"]["recall"], "crossing_fpr": metric["observed_final_crossing"]["false_positive_rate"]})
    return pd.DataFrame(rows)


def scenario_table(results: dict[str, Any]) -> pd.DataFrame:
    rows = []
    for name, entry in results["configs"].items():
        for scenario, metric in entry["pooled"].get("by_scenario_mae_normalized", {}).items():
            rows.append({"config": name, "scenario": scenario, **metric})
    return pd.DataFrame(rows)


def stratum_table(results: dict[str, Any]) -> pd.DataFrame:
    rows = []
    for name, entry in results["configs"].items():
        for stratum, metric in entry["pooled"].get("by_stratum", {}).items():
            rows.append({"config": name, "stratum": stratum, "components": metric["components"], "mae_normalized": metric["mae_normalized"], "mean_signed_error": metric["mean_signed_error"], "crossing_recall": metric["observed_final_crossing"]["recall"], "crossing_fp": metric["observed_final_crossing"]["fp"]})
    return pd.DataFrame(rows)


def run_seed_check(training: TrainingData, config: CandidateConfig, folds: pd.DataFrame, *, seeds: Sequence[int], n_jobs: int = 2) -> dict[str, Any]:
    """Re-run the cross-validation of one configuration with extra seeds to
    quantify stochastic spread (subsample / colsample). Post-selection read-out."""
    out = {"config": config.name, "seeds": {}}
    for seed in seeds:
        results, _ = run_cross_validation(training, [config], folds, seed=seed, n_jobs=n_jobs)
        entry = results["configs"][config.name]
        out["seeds"][str(seed)] = {"pooled_mae_normalized": entry["pooled"]["mae_normalized"], "healthy_mae_normalized": entry["pooled"].get("healthy_mae_normalized"), "crossing_recall": entry["pooled"]["observed_final_crossing"]["recall"], "crossing_fp": entry["pooled"]["observed_final_crossing"]["fp"]}
    values = np.array([v["pooled_mae_normalized"] for v in out["seeds"].values()])
    out["pooled_mae_normalized_spread"] = {"mean": float(values.mean()), "std": float(values.std(ddof=1)) if len(values) > 1 else 0.0, "min": float(values.min()), "max": float(values.max())}
    return out


def run_prevalence_readout(training: TrainingData, configs: Sequence[CandidateConfig], folds: pd.DataFrame, *, keep_fraction: float = 0.5, seed: int = DEFAULT_SEED, n_jobs: int = 2) -> dict[str, Any]:
    """Robustness read-out: refit each configuration with a fixed fraction of the
    is_defect parts removed from every fold's TRAINING portion (validation
    batches untouched) and report how the healthy-part bias moves. Labels are
    used only to subsample the training rows for this diagnostic; they never
    enter features. Not a selection criterion."""
    if "is_defect" not in training.labels:
        raise ValueError("prevalence read-out needs is_defect labels")
    features, labels, y = training.features, training.labels, training.y
    rng = np.random.default_rng(seed)
    defect = labels["is_defect"].to_numpy(dtype=bool)
    keep = np.ones(len(features), dtype=bool)
    defect_index = np.flatnonzero(defect)
    drop = rng.choice(defect_index, size=int(round(len(defect_index) * (1 - keep_fraction))), replace=False)
    keep[drop] = False
    out: dict[str, Any] = {"keep_fraction_of_defects_in_training": keep_fraction, "training_defect_parts_dropped": int(len(drop)), "configs": {}}
    for config in configs:
        pooled = np.full(len(features), np.nan)
        for k, train_mask, valid_mask in fold_masks(features, folds):
            fit_mask = train_mask & keep
            fitted = fit_model(config, features.loc[fit_mask].reset_index(drop=True), y[fit_mask], seed=seed, n_jobs=n_jobs)
            pooled[valid_mask] = fitted.predict_normalized(features.loc[valid_mask].reset_index(drop=True))
        metric = forecast_metrics(pooled, features, labels)
        out["configs"][config.name] = {"mae_normalized": metric["mae_normalized"], "healthy_mae_normalized": metric.get("healthy_mae_normalized"), "healthy_mean_signed_error_normalized": metric.get("healthy_mean_signed_error_normalized"), "crossing_recall": metric["observed_final_crossing"]["recall"], "crossing_fp": metric["observed_final_crossing"]["fp"]}
    return out


# --------------------------------------------------------------------------- #
# Prediction-interval proposal (nested calibration inside each training fold)
# --------------------------------------------------------------------------- #
def choose_calibration_batches(train_features: pd.DataFrame, *, per_profile: int) -> list[str]:
    """Deterministically reserve the last ``per_profile`` batches (sorted id) of
    every profile inside a fold's training portion for calibration."""
    batches = train_features.drop_duplicates("batch_id")[["batch_id"] + (["profile_id"] if "profile_id" in train_features else [])].copy()
    if "profile_id" not in batches:
        batches["profile_id"] = "*"
    chosen: list[str] = []
    for _, group in batches.sort_values(["profile_id", "batch_id"]).groupby("profile_id", sort=True):
        ids = group["batch_id"].tolist()
        if len(ids) <= per_profile:
            raise ValueError("not enough batches per profile to reserve a calibration subset")
        chosen.extend(ids[-per_profile:])
    return sorted(chosen)


def conformal_radius(residuals: np.ndarray, alpha: float) -> float:
    residuals = np.asarray(residuals, dtype=float)
    if not 0 < alpha < 1 or not len(residuals) or not np.isfinite(residuals).all():
        raise ValueError("finite residuals and 0 < alpha < 1 are required")
    rank = math.ceil((len(residuals) + 1) * (1 - alpha))
    if rank > len(residuals):
        raise ValueError("too few calibration components for this alpha")
    return float(np.sort(residuals)[rank - 1])


def signed_conformal_bounds(residuals: np.ndarray, alpha: float) -> tuple[float, float]:
    """Asymmetric bounds: finite-sample lower alpha/2 and upper 1-alpha/2 quantiles of signed residual y - pred."""
    residuals = np.asarray(residuals, dtype=float)
    n = len(residuals)
    upper_rank = math.ceil((n + 1) * (1 - alpha / 2))
    lower_rank = math.floor((n + 1) * (alpha / 2))
    if upper_rank > n or lower_rank < 1:
        raise ValueError("too few calibration components for asymmetric bounds")
    ordered = np.sort(residuals)
    return float(ordered[lower_rank - 1]), float(ordered[upper_rank - 1])


SLOPE_Z_STRATA_EDGES = (2.0, 5.0)  # strata on signed slope_batch_robust_z: (-inf,2), [2,5), [5,inf)
MIN_STRATUM_CALIBRATION = 20


def stratum_index(features: pd.DataFrame) -> np.ndarray:
    z = pd.to_numeric(features["slope_batch_robust_z"], errors="coerce").fillna(0.0).to_numpy(dtype=float)
    return np.digitize(z, SLOPE_Z_STRATA_EDGES)


def stratified_signed_bounds(cal_residual: np.ndarray, cal_strata: np.ndarray, alpha: float) -> dict[int, tuple[float, float, float]]:
    """Per-stratum (lower, upper, one_sided_upper) signed-residual margins with a
    pooled fallback when a stratum has too few calibration components."""
    pooled_lo, pooled_hi = signed_conformal_bounds(cal_residual, alpha)
    pooled_one = conformal_radius(cal_residual, alpha)  # (1-alpha) quantile of signed residual = one-sided upper margin
    bounds: dict[int, tuple[float, float, float]] = {}
    for k in range(len(SLOPE_Z_STRATA_EDGES) + 1):
        member = cal_residual[cal_strata == k]
        if len(member) >= MIN_STRATUM_CALIBRATION:
            try:
                lo, hi = signed_conformal_bounds(member, alpha)
                one = conformal_radius(member, alpha)
                bounds[k] = (lo, hi, one)
                continue
            except ValueError:
                pass
        bounds[k] = (pooled_lo, pooled_hi, pooled_one)
    return bounds


def interval_metrics(lower: np.ndarray, upper: np.ndarray, features: pd.DataFrame, labels: pd.DataFrame) -> dict[str, Any]:
    y = labels["y_normalized"].to_numpy(dtype=float)
    limits = features["upper_limit"].to_numpy(dtype=float)
    covered = (y >= lower) & (y <= upper)
    width = upper - lower
    per_batch = pd.Series(covered.astype(float)).groupby(features["batch_id"].to_numpy()).mean()
    out: dict[str, Any] = {
        "components": int(len(y)),
        "coverage": float(covered.mean()),
        "upper_only_coverage": float((y <= upper).mean()),
        "per_batch_coverage": {"min": float(per_batch.min()), "max": float(per_batch.max()), "std": float(per_batch.std(ddof=1)) if len(per_batch) > 1 else 0.0, "values": {str(k): float(v) for k, v in per_batch.items()}},
        "median_width_normalized": float(np.median(width)),
        "mean_width_normalized": float(width.mean()),
        "median_width_ua": float(np.median(width * limits)),
        "share_upper_below_limit": float((upper < 1.0).mean()),
        "share_lower_at_or_above_limit": float((lower >= 1.0).mean()),
    }
    if "is_healthy" in labels:
        healthy = labels["is_healthy"].to_numpy(dtype=bool)
        out["coverage_healthy"] = float(covered[healthy].mean()) if healthy.any() else None
        out["coverage_nonhealthy"] = float(covered[~healthy].mean()) if (~healthy).any() else None
        out["median_width_normalized_healthy"] = float(np.median(width[healthy])) if healthy.any() else None
    crossing = y >= 1.0
    if crossing.any():
        out["coverage_observed_crossers"] = float(covered[crossing].mean())
        out["share_crossers_with_upper_at_or_above_limit"] = float((upper[crossing] >= 1.0).mean())
    if "profile_id" in features:
        out["coverage_by_profile"] = {str(p): float(covered[features["profile_id"].eq(p).to_numpy()].mean()) for p in sorted(features["profile_id"].unique())}
    return out


def run_interval_experiment(
    training: TrainingData,
    config: CandidateConfig,
    folds: pd.DataFrame,
    *,
    alpha: float = 0.1,
    calibration_batches_per_profile: int = 2,
    seed: int = DEFAULT_SEED,
    n_jobs: int = 2,
    quantile_params: dict[str, Any] | None = None,
    log=None,
) -> dict[str, Any]:
    """Interval proposal evaluated with nested calibration.

    Inside each fold, the model is fitted on the fold's training batches minus a
    reserved calibration subset (whole batches, stratified by profile). Residual
    quantiles are taken on the calibration subset only and evaluated on the
    heldout validation batches. Validation residuals never calibrate their own
    interval. Three methods are compared:
      * symmetric_absolute: v1's split-conformal absolute-residual radius;
      * asymmetric_signed: separate lower/upper signed-residual quantiles;
      * stratified_asymmetric_signed: asymmetric signed-residual quantiles inside
        strata of the 24 h slope robust z (<2, 2-5, >=5), pooled fallback below
        MIN_STRATUM_CALIBRATION calibration components;
      * stratified_one_sided_upper: same strata, one-sided (1-alpha) upper margin
        with the lower bound at zero leakage;
      * cqr_quantile_xgboost: conformalized quantile regression using an XGBoost
        reg:quantileerror model for alpha/2 and 1-alpha/2, adjusted on the
        calibration subset (Romano et al. 2019 style).
    """
    from xgboost import XGBRegressor

    assert_folds_disjoint(training.features, folds)
    features, labels, y = training.features, training.labels, training.y
    methods = ("symmetric_absolute", "asymmetric_signed", "stratified_asymmetric_signed", "stratified_one_sided_upper", "cqr_quantile_xgboost")
    per_fold: dict[str, list[dict[str, Any]]] = {m: [] for m in methods}
    calibration_log: list[dict[str, Any]] = []
    qparams = {**V1_XGB_PARAMS, **(quantile_params or {})}
    for k, train_mask, valid_mask in fold_masks(features, folds):
        train_features = features.loc[train_mask].reset_index(drop=True)
        train_y = y[train_mask]
        cal_batches = choose_calibration_batches(train_features, per_profile=calibration_batches_per_profile)
        cal_mask = train_features["batch_id"].isin(cal_batches).to_numpy()
        fit_features, fit_y = train_features.loc[~cal_mask].reset_index(drop=True), train_y[~cal_mask]
        cal_features, cal_y = train_features.loc[cal_mask].reset_index(drop=True), train_y[cal_mask]
        valid_features = features.loc[valid_mask].reset_index(drop=True)
        valid_labels = labels.loc[valid_mask].reset_index(drop=True)
        fitted = fit_model(config, fit_features, fit_y, seed=seed, n_jobs=n_jobs)
        cal_pred, valid_pred = fitted.predict_normalized(cal_features), fitted.predict_normalized(valid_features)
        cal_residual = cal_y - cal_pred
        radius = conformal_radius(np.abs(cal_residual), alpha)
        lo_q, hi_q = signed_conformal_bounds(cal_residual, alpha)
        cal_strata, valid_strata = stratum_index(cal_features), stratum_index(valid_features)
        strata_bounds = stratified_signed_bounds(cal_residual, cal_strata, alpha)
        entry = {"fold": k, "fit_batches": int(fit_features["batch_id"].nunique()), "calibration_batches": cal_batches, "calibration_components": int(len(cal_y)), "symmetric_radius": radius, "asymmetric_bounds": [lo_q, hi_q],
                 "stratified_bounds": {str(kk): {"lower_margin": v[0], "upper_margin": v[1], "one_sided_upper_margin": v[2], "calibration_components": int((cal_strata == kk).sum())} for kk, v in strata_bounds.items()}}
        per_fold["symmetric_absolute"].append({"fold": k, **interval_metrics(np.maximum(valid_pred - radius, 0.0), valid_pred + radius, valid_features, valid_labels)})
        per_fold["asymmetric_signed"].append({"fold": k, **interval_metrics(np.maximum(valid_pred + lo_q, 0.0), valid_pred + hi_q, valid_features, valid_labels)})
        strat_lo = np.array([strata_bounds[int(kk)][0] for kk in valid_strata]); strat_hi = np.array([strata_bounds[int(kk)][1] for kk in valid_strata]); strat_one = np.array([strata_bounds[int(kk)][2] for kk in valid_strata])
        per_fold["stratified_asymmetric_signed"].append({"fold": k, **interval_metrics(np.maximum(valid_pred + strat_lo, 0.0), valid_pred + strat_hi, valid_features, valid_labels)})
        per_fold["stratified_one_sided_upper"].append({"fold": k, **interval_metrics(np.zeros(len(valid_pred)), valid_pred + strat_one, valid_features, valid_labels)})
        # CQR: quantile model on the fit subset with the same feature set and margin.
        matrix_fit = impute(feature_matrix(fit_features, config.feature_columns), fitted.medians)
        matrix_cal = impute(feature_matrix(cal_features, config.feature_columns), fitted.medians)
        matrix_valid = impute(feature_matrix(valid_features, config.feature_columns), fitted.medians)
        margin_target = config.target if config.model == "xgboost" else "normalized"
        label_fit, margin_fit = target_encoding(fit_y, persistence_forecast(fit_features), margin_target)
        _, margin_cal = target_encoding(None, persistence_forecast(cal_features), margin_target)
        _, margin_valid = target_encoding(None, persistence_forecast(valid_features), margin_target)
        quantile_model = XGBRegressor(objective="reg:quantileerror", quantile_alpha=np.array([alpha / 2, 1 - alpha / 2]), random_state=seed, n_jobs=n_jobs, **qparams)
        if margin_fit is None:
            quantile_model.fit(matrix_fit, label_fit)
            q_cal, q_valid = quantile_model.predict(matrix_cal), quantile_model.predict(matrix_valid)
        else:
            quantile_model.fit(matrix_fit, label_fit, base_margin=np.repeat(margin_fit[:, None], 2, axis=1))
            q_cal = quantile_model.predict(matrix_cal, base_margin=np.repeat(margin_cal[:, None], 2, axis=1))
            q_valid = quantile_model.predict(matrix_valid, base_margin=np.repeat(margin_valid[:, None], 2, axis=1))
        q_cal, q_valid = decode_prediction(q_cal, margin_target).reshape(len(cal_y), 2), decode_prediction(q_valid, margin_target).reshape(len(valid_features), 2)
        lo_cal, hi_cal = np.minimum(q_cal[:, 0], q_cal[:, 1]), np.maximum(q_cal[:, 0], q_cal[:, 1])
        lo_val, hi_val = np.minimum(q_valid[:, 0], q_valid[:, 1]), np.maximum(q_valid[:, 0], q_valid[:, 1])
        cqr_scores = np.maximum(lo_cal - cal_y, cal_y - hi_cal)
        cqr_adjust = conformal_radius(cqr_scores, alpha) if (cqr_scores >= 0).all() else float(np.sort(cqr_scores)[math.ceil((len(cqr_scores) + 1) * (1 - alpha)) - 1])
        entry["cqr_adjustment"] = cqr_adjust
        per_fold["cqr_quantile_xgboost"].append({"fold": k, **interval_metrics(np.maximum(lo_val - cqr_adjust, 0.0), hi_val + cqr_adjust, valid_features, valid_labels)})
        calibration_log.append(entry)
        if log:
            log(f"interval fold {k}: coverage sym {per_fold['symmetric_absolute'][-1]['coverage']:.3f} asym {per_fold['asymmetric_signed'][-1]['coverage']:.3f} cqr {per_fold['cqr_quantile_xgboost'][-1]['coverage']:.3f}")
    summary = {}
    for method, entries in per_fold.items():
        coverage = np.array([e["coverage"] for e in entries])
        widths = np.array([e["median_width_normalized"] for e in entries])
        summary[method] = {
            "nominal_coverage": 1 - alpha,
            "coverage_mean": float(coverage.mean()), "coverage_std": float(coverage.std(ddof=1)) if len(coverage) > 1 else 0.0, "coverage_min": float(coverage.min()), "coverage_max": float(coverage.max()),
            "upper_only_coverage_mean": float(np.mean([e["upper_only_coverage"] for e in entries])),
            "per_batch_coverage_min": float(min(e["per_batch_coverage"]["min"] for e in entries)), "per_batch_coverage_max": float(max(e["per_batch_coverage"]["max"] for e in entries)),
            "median_width_normalized_mean": float(widths.mean()),
            "coverage_healthy_mean": float(np.mean([e["coverage_healthy"] for e in entries if e.get("coverage_healthy") is not None])) if any(e.get("coverage_healthy") is not None for e in entries) else None,
            "coverage_nonhealthy_mean": float(np.mean([e["coverage_nonhealthy"] for e in entries if e.get("coverage_nonhealthy") is not None])) if any(e.get("coverage_nonhealthy") is not None for e in entries) else None,
            "share_upper_below_limit_mean": float(np.mean([e["share_upper_below_limit"] for e in entries])),
            "per_fold": entries,
        }
    return {
        "config": config.to_dict(), "alpha": alpha, "calibration_rule": f"last {calibration_batches_per_profile} batch id(s) per profile inside each fold's training portion; validation residuals never calibrate their own interval",
        "methods": summary, "calibration_log": calibration_log,
        "limitations": [
            "Parts within a batch are dependent; the row-level exchangeability behind the nominal level does not hold, so report empirical coverage rather than a guarantee",
            "Coverage on synthetic training folds is development evidence only; Codex performs the release calibration on separate calibration batches",
            "Interval bounds are not failure probabilities and the anomaly score is not a confidence",
        ],
    }


# --------------------------------------------------------------------------- #
# Frozen candidate: save / load / predict
# --------------------------------------------------------------------------- #
UNAVAILABLE_STATUS = "unavailable"
FORECAST_STATUS = "forecast"
OUTPUT_COLUMNS = IDENTITY + [
    "status", "predicted_final_value", "predicted_normalized", "unit", "target_hour", "as_of_hour",
    "upper_limit", "value_at_24h", "persistence_final_value", "profile_id", "peer_count",
    "unavailable_reason", "candidate_version", "candidate_name",
]


@dataclass
class ForecastCandidate:
    """Frozen v2 candidate. ``predict`` never fits, tunes, downloads or reads labels."""

    manifest: dict[str, Any]
    booster: Any  # xgboost.XGBRegressor or None

    @property
    def config(self) -> CandidateConfig:
        c = dict(self.manifest["config"])
        c.pop("feature_columns", None)
        return CandidateConfig(**c)

    def _fitted(self) -> FittedModel:
        return FittedModel(self.config, dict(self.manifest["imputation_medians"]), self.booster)

    def predict(self, early_readings: pd.DataFrame) -> pd.DataFrame:
        """One row per complete identity with predicted_final_value in uA at 168 h.

        Whole-upload structural problems (missing columns, blank identities,
        mixed profiles inside a batch) raise ValueError, exactly like v1's
        ``prepare_early_features``. Per-component problems (missing checkpoint,
        nonfinite value, unsupported family/measurement/profile) return a row
        with status ``unavailable`` and a reason. Output order is sorted by
        identity, so shuffled input produces identical output.
        """
        features, early, unscored = prepare_early_features(early_readings, as_of_hour=AS_OF_HOUR)
        rows: list[dict[str, Any]] = []
        for record in unscored:
            rows.append(self._unavailable_row({c: record[c] for c in IDENTITY}, str(record.get("data_quality_warning") or "invalid early readings")))
        if not features.empty:
            supported = set(self.manifest.get("supported_profiles", []))
            profile = pd.Series([None] * len(features), index=features.index, dtype=object)
            if "profile_id" in early:
                mapping = early.drop_duplicates("component_id").set_index("component_id")["profile_id"]
                profile = features["component_id"].map(mapping)
            features = augment_features(features, early)
            features["profile_id"] = profile.astype(object).where(profile.notna(), None)
            ok = features["profile_id"].isin(supported).to_numpy() if supported else np.ones(len(features), dtype=bool)
            for _, row in features.loc[~ok].iterrows():
                rows.append(self._unavailable_row({c: row[c] for c in IDENTITY}, "Missing or unsupported profile_id for this candidate"))
            scored = features.loc[ok].reset_index(drop=True)
            if not scored.empty:
                peer_counts = scored.groupby(["batch_id", "component_family", "measurement_name"])["component_id"].transform("count").to_numpy()
                with threadpool_limits(limits=1):
                    pred = self._fitted().predict_normalized(scored)
                limits = scored["upper_limit"].to_numpy(dtype=float)
                for index, row in scored.iterrows():
                    rows.append({
                        **{c: row[c] for c in IDENTITY},
                        "status": FORECAST_STATUS,
                        "predicted_final_value": float(pred[index] * limits[index]),
                        "predicted_normalized": float(pred[index]),
                        "unit": UNIT, "target_hour": TARGET_HOUR, "as_of_hour": AS_OF_HOUR,
                        "upper_limit": float(limits[index]),
                        "value_at_24h": float(row["current_value"]),
                        "persistence_final_value": float(row["current_value"]),
                        "profile_id": row["profile_id"],
                        "peer_count": int(peer_counts[index]),
                        "unavailable_reason": None,
                        "candidate_version": VERSION, "candidate_name": self.manifest["config"]["name"],
                    })
        out = pd.DataFrame(rows, columns=OUTPUT_COLUMNS)
        return out.sort_values(SORT_KEYS).reset_index(drop=True)

    def _unavailable_row(self, identity: dict[str, Any], reason: str) -> dict[str, Any]:
        return {
            **identity, "status": UNAVAILABLE_STATUS, "predicted_final_value": None, "predicted_normalized": None,
            "unit": UNIT, "target_hour": TARGET_HOUR, "as_of_hour": AS_OF_HOUR, "upper_limit": None,
            "value_at_24h": None, "persistence_final_value": None, "profile_id": None, "peer_count": None,
            "unavailable_reason": reason, "candidate_version": VERSION, "candidate_name": self.manifest["config"]["name"],
        }


def fit_final_candidate(
    training: TrainingData,
    config: CandidateConfig,
    *,
    seed: int = DEFAULT_SEED,
    n_jobs: int = 2,
    experiment_reference: dict[str, Any] | None = None,
) -> ForecastCandidate:
    """Fit the chosen configuration on ALL provided training batches. Call this
    only after the predeclared experiment is finished and recorded."""
    fitted = fit_model(config, training.features, training.y, seed=seed, n_jobs=n_jobs)
    supported = sorted(training.features["profile_id"].astype(str).unique().tolist()) if "profile_id" in training.features else []
    manifest = {
        "candidate_version": VERSION,
        "config": config.to_dict(),
        "family": FAMILY, "measurement": MEASUREMENT, "unit": UNIT,
        "as_of_hour": AS_OF_HOUR, "target_hour": TARGET_HOUR,
        "supported_checkpoints_hours": [0.0, AS_OF_HOUR],
        "supported_profiles": supported,
        "feature_columns": config.feature_columns,
        "imputation_medians": fitted.medians,
        "missing_value_policy": "Leakage checkpoints must be finite (else unavailable). Optional auxiliary columns may be missing and are filled with the training medians recorded in imputation_medians. No other preprocessing.",
        "target": {
            "definition": "observed final_value at 168 h divided by the per-component upper_limit; predictions are multiplied back by upper_limit to give uA",
            "parameterisation": config.target,
            "clipping": "nonnegative only; no upper clipping",
            "base_margin_required_at_predict": config.model == "xgboost" and config.target.endswith("residual_over_persistence"),
        },
        "training": {
            "components": int(len(training.features)), "batches": int(training.features["batch_id"].nunique()),
            "batch_ids": sorted(training.features["batch_id"].unique().tolist()),
            "input_sha256": training.input_hashes, "seed": seed, "data": "synthetic training batches only",
        },
        "environment": environment_record(),
        "experiment_reference": experiment_reference or {},
        "interval": "none: this candidate returns point forecasts only; Codex connects separately calibrated intervals",
        "assumptions": [
            "Only exact 0 h and 24 h MLCC_X7R leakage_ua readings in uA are supported",
            "Batch-relative features are recomputed from the uploaded batch peers, so a small uploaded batch weakens them (see peer_count)",
            "Synthetic training data; no field accuracy is claimed",
            "Simulated scenario labels never enter inference",
        ],
    }
    return ForecastCandidate(manifest=manifest, booster=fitted.booster)


def save_forecast_candidate(candidate: ForecastCandidate, path: str | Path) -> Path:
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    manifest = dict(candidate.manifest)
    artifacts: dict[str, str] = {}
    if candidate.booster is not None:
        candidate.booster.save_model(directory / "model.ubj")
        candidate.booster.save_model(directory / "model.json")
        artifacts = {"model.ubj": _hash_file(directory / "model.ubj"), "model.json": _hash_file(directory / "model.json")}
    manifest["artifact_sha256"] = artifacts
    write_json(directory / "manifest.json", manifest)
    return directory


def load_forecast_candidate(path: str | Path, *, strict_versions: bool = True) -> ForecastCandidate:
    """Load a saved candidate. Verifies artifact hashes and (by default) that the
    numeric libraries match the training environment exactly."""
    directory = Path(path)
    manifest = json.loads((directory / "manifest.json").read_text())
    if manifest.get("candidate_version") != VERSION:
        raise ValueError("Unsupported candidate version")
    for name, digest in manifest.get("artifact_sha256", {}).items():
        if _hash_file(directory / name) != digest:
            raise ValueError(f"Artifact integrity check failed: {name}")
    recorded = manifest.get("environment", {}).get("versions", {})
    current = environment_record()["versions"]
    mismatched = {p: (recorded.get(p), current.get(p)) for p in ("numpy", "pandas", "scikit-learn", "xgboost") if recorded.get(p) != current.get(p)}
    if mismatched and strict_versions:
        raise ValueError(f"Library version mismatch versus the candidate's training environment: {mismatched}")
    booster = None
    if manifest["config"]["model"] == "xgboost":
        from xgboost import XGBRegressor

        booster = XGBRegressor()
        booster.load_model(directory / "model.ubj")
    return ForecastCandidate(manifest=manifest, booster=booster)
