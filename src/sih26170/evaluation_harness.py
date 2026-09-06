"""Screening comparison, lead-time analysis and stress tests for the detector.

This module measures the existing detector; it does not replace it. The
Isolation Forest and combined results come from
:class:`~sih26170.anomaly.BatchAwareAnomalyDetector`, and the repository's
robust baseline comes from :func:`~sih26170.anomaly.apply_robust_baseline`.

Methods compared
----------------
``fixed_limit``
    Screen against the approved upper limit, which is current practice.
``robust_mad``
    The repository's median/MAD batch-relative rule.
``isolation_forest``
    The Isolation Forest half of the existing detector on its own.
``combined``
    The existing detector's published decision: robust OR Isolation Forest.
``robust_mad_strict``
    A diagnostic textbook median/MAD rule using ``1.4826 * MAD`` as the scale
    with no extra floor terms. It exists only to measure the cost of the
    additional scale floors in ``features._add_robust_z``.

Accuracy is deliberately absent from every table. When defective components
are a minority, a screen that flags nothing scores well on accuracy and is
useless.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, replace

import numpy as np
import pandas as pd

from .anomaly import BatchAwareAnomalyDetector
from .contracts import AnomalyResult
from .decision import recommend_action
from .features import BATCH_COLUMNS
from .splitting import BatchHoldout, build_split_features, split_batches
from .synthetic import SyntheticDataset

ENGINEER_REVIEW_DISCLAIMER = (
    "Synthetic evaluation only. The software ranks and explains suspicious "
    "components; a qualified engineer decides whether a real component is "
    "accepted, retested or rejected."
)

PRIMARY_METHODS: tuple[str, ...] = (
    "fixed_limit",
    "robust_mad",
    "isolation_forest",
    "combined",
)
DIAGNOSTIC_METHODS: tuple[str, ...] = ("robust_mad_strict",)
ALL_METHODS: tuple[str, ...] = PRIMARY_METHODS + DIAGNOSTIC_METHODS

METHOD_LABELS: dict[str, str] = {
    "fixed_limit": "Fixed upper-limit screening",
    "robust_mad": "Median/MAD robust screening (repository rule)",
    "isolation_forest": "Isolation Forest",
    "combined": "Combined robust + Isolation Forest (existing detector)",
    "robust_mad_strict": "Median/MAD, textbook scale (diagnostic)",
}

METHOD_PARAMETERS: dict[str, tuple[str, ...]] = {
    "fixed_limit": ("as_of_hour", "fixed_limit_fraction"),
    "robust_mad": ("as_of_hour", "robust_threshold"),
    "isolation_forest": ("as_of_hour", "contamination", "fit_scope"),
    "combined": ("as_of_hour", "contamination", "robust_threshold", "fit_scope"),
    "robust_mad_strict": ("as_of_hour", "robust_threshold"),
}

_LABEL_MERGE_COLUMNS = [
    "component_id",
    "measurement_name",
    "scenario",
    "is_defect",
    "is_tester_fault",
    "is_healthy",
    "first_exceedance_hour",
]

# The generator has carried this label under more than one name. Resolve it at
# run time so the harness does not break on a rename.
_ONSET_COLUMN_CANDIDATES = ("anomaly_onset_hour", "defect_onset_hour")

DEFAULT_LADDER_HOURS: tuple[float, ...] = (6.0, 12.0, 24.0, 48.0, 72.0, 96.0, 120.0, 144.0)


@dataclass(frozen=True)
class ScreeningConfig:
    """Parameters shared by every screening run."""

    as_of_hour: float = 24.0
    contamination: float = 0.1
    robust_threshold: float = 3.5
    fixed_limit_fraction: float = 1.0
    random_state: int = 42
    fit_scope: str = "per_family"
    minimum_observations: int = 2

    def __post_init__(self) -> None:
        if self.fit_scope not in {"per_family", "pooled"}:
            raise ValueError("fit_scope must be 'per_family' or 'pooled'")
        if not 0.0 < self.fixed_limit_fraction <= 2.0:
            raise ValueError("fixed_limit_fraction must sit in (0, 2]")

    def to_dict(self) -> dict[str, object]:
        return {
            "as_of_hour": self.as_of_hour,
            "contamination": self.contamination,
            "robust_threshold": self.robust_threshold,
            "fixed_limit_fraction": self.fixed_limit_fraction,
            "random_state": self.random_state,
            "fit_scope": self.fit_scope,
            "minimum_observations": self.minimum_observations,
        }


@dataclass(frozen=True)
class EvaluationReport:
    """Everything produced by one held-out screening run."""

    config: ScreeningConfig
    split: BatchHoldout
    metrics: pd.DataFrame
    scenario_flag_rates: pd.DataFrame
    screened: pd.DataFrame
    n_train_components: int
    n_test_components: int
    disclaimer: str = ENGINEER_REVIEW_DISCLAIMER


@dataclass(frozen=True)
class LadderReport:
    """Screening repeated at a ladder of early-warning hours."""

    metrics: pd.DataFrame
    lead_times: pd.DataFrame
    summary: pd.DataFrame
    as_of_hours: tuple[float, ...]
    split: BatchHoldout
    disclaimer: str = ENGINEER_REVIEW_DISCLAIMER


def _onset_column(frame: pd.DataFrame) -> str:
    """Return the column holding the hour an abnormality begins."""

    for candidate in _ONSET_COLUMN_CANDIDATES:
        if candidate in frame.columns:
            return candidate
    raise ValueError(
        "labels must carry an onset column, one of: "
        + ", ".join(_ONSET_COLUMN_CANDIDATES)
    )


def _logistic_risk(raw_score: float, threshold: float) -> float:
    return float(1.0 / (1.0 + math.exp(-(float(raw_score) - float(threshold)))))


def batch_relative_mad_z(
    features: pd.DataFrame,
    value_column: str,
    *,
    group_columns: Sequence[str] = tuple(BATCH_COLUMNS),
) -> pd.Series:
    """Textbook median/MAD z-score inside each batch, family and measurement.

    The scale is ``1.4826 * MAD`` with no additional floor. When a group has a
    zero MAD the scale falls back to a small fraction of the group median so
    the division stays defined.
    """

    values = features[value_column].astype(float)
    keys = [features[column] for column in group_columns]
    medians = values.groupby(keys, dropna=False).transform("median")
    deviations = (values - medians).abs()
    mad = deviations.groupby(keys, dropna=False).transform("median")
    scale = 1.4826 * mad.to_numpy(dtype=float)
    fallback = np.maximum(medians.abs().to_numpy(dtype=float) * 1e-3, 1e-12)
    scale = np.where(scale > 0.0, scale, fallback)
    return pd.Series(
        (values.to_numpy(dtype=float) - medians.to_numpy(dtype=float)) / scale,
        index=features.index,
        name=f"{value_column}_mad_z",
    )


POOLED_KEY = ("*", "*")


def _group_key(family: object, measurement: object) -> tuple[str, str]:
    return (str(family), str(measurement))


def fit_detectors(
    train_features: pd.DataFrame, config: ScreeningConfig
) -> dict[tuple[str, str], BatchAwareAnomalyDetector]:
    """Fit one detector per family, or a single pooled detector.

    The fit depends only on the training features, ``contamination`` and
    ``random_state``. ``robust_threshold`` is applied at scoring time, so a
    fitted detector can be reused across thresholds.
    """

    def _new() -> BatchAwareAnomalyDetector:
        return BatchAwareAnomalyDetector(
            contamination=config.contamination,
            robust_threshold=config.robust_threshold,
            random_state=config.random_state,
        )

    if config.fit_scope == "pooled":
        return {POOLED_KEY: _new().fit(train_features)}

    detectors: dict[tuple[str, str], BatchAwareAnomalyDetector] = {}
    group_columns = ["component_family", "measurement_name"]
    for key, group in train_features.groupby(group_columns, sort=True, dropna=False):
        detectors[_group_key(*key)] = _new().fit(group) if len(group) >= 8 else None
    return {key: value for key, value in detectors.items() if value is not None}


def _score_with(
    detectors: dict[tuple[str, str], BatchAwareAnomalyDetector],
    test_features: pd.DataFrame,
    config: ScreeningConfig,
) -> pd.DataFrame:
    if config.fit_scope == "pooled":
        detector = detectors[POOLED_KEY]
        detector.robust_threshold = config.robust_threshold
        return detector.score(test_features)

    group_columns = ["component_family", "measurement_name"]
    scored_parts: list[pd.DataFrame] = []
    for key, test_group in test_features.groupby(group_columns, sort=True, dropna=False):
        detector = detectors.get(_group_key(*key))
        if detector is None:
            family, measurement = key
            raise ValueError(
                f"no fitted detector for {family}/{measurement}; the detector needs "
                "at least eight comparable reference components in the training batches"
            )
        detector.robust_threshold = config.robust_threshold
        scored_parts.append(detector.score(test_group))
    return pd.concat(scored_parts, ignore_index=True)


def screen_components(
    train_features: pd.DataFrame,
    test_features: pd.DataFrame,
    config: ScreeningConfig = ScreeningConfig(),
    *,
    detectors: dict[tuple[str, str], BatchAwareAnomalyDetector] | None = None,
) -> pd.DataFrame:
    """Score held-out components with every compared screening method.

    Pass ``detectors`` from :func:`fit_detectors` to reuse a fit across the
    parameters the Isolation Forest cannot see, such as ``robust_threshold``
    and ``fixed_limit_fraction``.
    """

    if detectors is None:
        detectors = fit_detectors(train_features, config)
    scored = _score_with(detectors, test_features, config)

    scored = scored.sort_values("component_id").reset_index(drop=True)

    limit = scored["upper_limit"].astype(float)
    current = scored["current_value"].astype(float)
    scored["fixed_limit_flag"] = current >= config.fixed_limit_fraction * limit
    scored["fixed_limit_score"] = (current / limit).clip(upper=2.0)

    scored["robust_mad_flag"] = scored["is_robust_anomaly"].astype(bool)
    scored["robust_mad_score"] = scored["robust_anomaly_score"].astype(float)

    scored["isolation_forest_flag"] = scored["is_model_anomaly"].astype(bool)
    scored["isolation_forest_score"] = scored["model_anomaly_score"].astype(float)

    scored["combined_flag"] = scored["is_anomaly"].astype(bool)
    scored["combined_score"] = scored["anomaly_score"].astype(float)

    strict_current = batch_relative_mad_z(scored, "current_value").abs()
    strict_slope = batch_relative_mad_z(scored, "slope").abs()
    strict_deviation = pd.concat([strict_current, strict_slope], axis=1).max(axis=1)
    scored["robust_mad_strict_deviation"] = strict_deviation
    scored["robust_mad_strict_flag"] = strict_deviation >= config.robust_threshold
    scored["robust_mad_strict_score"] = strict_deviation.map(
        lambda value: _logistic_risk(value, config.robust_threshold)
    )
    scored["as_of_hour"] = float(config.as_of_hour)
    return scored


def _attach_labels(screened: pd.DataFrame, labels: pd.DataFrame) -> pd.DataFrame:
    slim = labels[[*_LABEL_MERGE_COLUMNS, _onset_column(labels)]]
    merged = screened.merge(
        slim, on=["component_id", "measurement_name"], how="inner", validate="one_to_one"
    )
    if len(merged) != len(screened):
        raise ValueError(
            f"{len(screened) - len(merged)} screened component(s) have no ground-truth label"
        )
    return merged


def _rate(numerator: float, denominator: float) -> float:
    return float(numerator) / float(denominator) if denominator else float("nan")


def _method_metrics(merged: pd.DataFrame, method: str, *, as_of_hour: float) -> dict[str, object]:
    flag_column = f"{method}_flag"
    if flag_column not in merged.columns:
        raise ValueError(f"screened frame has no column {flag_column}")

    flags = merged[flag_column].to_numpy(dtype=bool)
    is_defect = merged["is_defect"].to_numpy(dtype=bool)
    is_tester_fault = merged["is_tester_fault"].to_numpy(dtype=bool)

    # A tester fault is a broken measurement, not a broken component, so it is
    # scored separately instead of being forced into either class.
    scoreable = ~is_tester_fault
    defect = is_defect & scoreable
    healthy = (~is_defect) & scoreable

    true_positives = int(np.sum(flags & defect))
    false_negatives = int(np.sum((~flags) & defect))
    false_positives = int(np.sum(flags & healthy))
    true_negatives = int(np.sum((~flags) & healthy))

    onset = merged[_onset_column(merged)].to_numpy(dtype=float)
    started = defect & (onset <= float(as_of_hour))
    recall_after_onset = _rate(int(np.sum(flags & started)), int(np.sum(started)))

    first_exceedance = merged["first_exceedance_hour"].to_numpy(dtype=float)
    detected = flags & defect
    crosses_later = (
        detected & np.isfinite(first_exceedance) & (first_exceedance > float(as_of_hour))
    )
    lead_hours = first_exceedance[crosses_later] - float(as_of_hour)
    detected_after_crossing = int(
        np.sum(detected & np.isfinite(first_exceedance) & (first_exceedance <= float(as_of_hour)))
    )
    detected_never_crossing = int(np.sum(detected & ~np.isfinite(first_exceedance)))

    n_tester_flagged = int(np.sum(flags & is_tester_fault))
    n_tester = int(np.sum(is_tester_fault))

    return {
        "method": method,
        "method_label": METHOD_LABELS.get(method, method),
        "as_of_hour": float(as_of_hour),
        "n_components": int(len(merged)),
        "n_defects": int(np.sum(defect)),
        "n_healthy": int(np.sum(healthy)),
        "n_tester_faults": n_tester,
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "true_negatives": true_negatives,
        "defect_recall": _rate(true_positives, true_positives + false_negatives),
        "false_negative_rate": _rate(false_negatives, true_positives + false_negatives),
        "false_positive_rate": _rate(false_positives, false_positives + true_negatives),
        "precision": _rate(true_positives, true_positives + false_positives),
        "recall_after_onset": recall_after_onset,
        "n_early_warnings": int(lead_hours.size),
        "median_lead_time_hours": float(np.median(lead_hours)) if lead_hours.size else float("nan"),
        "mean_lead_time_hours": float(np.mean(lead_hours)) if lead_hours.size else float("nan"),
        "min_lead_time_hours": float(np.min(lead_hours)) if lead_hours.size else float("nan"),
        "n_detected_after_crossing": detected_after_crossing,
        "n_detected_never_crossing": detected_never_crossing,
        "tester_fault_flag_rate": _rate(n_tester_flagged, n_tester),
        "false_positive_rate_incl_tester_faults": _rate(
            false_positives + n_tester_flagged,
            true_negatives + false_positives + n_tester,
        ),
    }


def evaluate_screening(
    screened: pd.DataFrame,
    labels: pd.DataFrame,
    *,
    as_of_hour: float | None = None,
    methods: Iterable[str] = ALL_METHODS,
) -> pd.DataFrame:
    """Return one metric row per screening method.

    ``median_lead_time_hours`` is the warning the method buys: hours between
    the screening decision and the first moment the component actually crosses
    its approved limit, over defects the method caught before that crossing.
    """

    merged = _attach_labels(screened, labels)
    hour = float(as_of_hour) if as_of_hour is not None else float(merged["as_of_hour"].iloc[0])
    rows = [_method_metrics(merged, method, as_of_hour=hour) for method in methods]
    return pd.DataFrame(rows)


def scenario_flag_rates(
    screened: pd.DataFrame,
    labels: pd.DataFrame,
    *,
    methods: Iterable[str] = ALL_METHODS,
) -> pd.DataFrame:
    """Flag rate per labelled scenario.

    For defect scenarios this is recall, for healthy scenarios it is the false
    alarm rate, and for tester faults it is the data-quality catch rate.
    """

    merged = _attach_labels(screened, labels)
    rows: list[dict[str, object]] = []
    for scenario, group in merged.groupby("scenario", sort=True):
        row: dict[str, object] = {"scenario": scenario, "n_components": int(len(group))}
        for method in methods:
            row[method] = float(group[f"{method}_flag"].mean())
        rows.append(row)
    return pd.DataFrame(rows)


def run_holdout_evaluation(
    dataset: SyntheticDataset,
    *,
    config: ScreeningConfig = ScreeningConfig(),
    split: BatchHoldout | None = None,
    test_fraction: float = 0.4,
    random_state: int = 7,
    methods: Iterable[str] = ALL_METHODS,
) -> EvaluationReport:
    """Fit on complete training batches and screen complete held-out batches."""

    active_split = split or split_batches(
        dataset.readings, test_fraction=test_fraction, random_state=random_state
    )
    train_features, test_features = build_split_features(
        dataset.readings,
        active_split,
        as_of_hour=config.as_of_hour,
        minimum_observations=config.minimum_observations,
    )
    screened = screen_components(train_features, test_features, config)
    methods = tuple(methods)
    return EvaluationReport(
        config=config,
        split=active_split,
        metrics=evaluate_screening(
            screened, dataset.labels, as_of_hour=config.as_of_hour, methods=methods
        ),
        scenario_flag_rates=scenario_flag_rates(screened, dataset.labels, methods=methods),
        screened=screened,
        n_train_components=int(len(train_features)),
        n_test_components=int(len(test_features)),
    )


def run_early_warning_ladder(
    dataset: SyntheticDataset,
    *,
    config: ScreeningConfig = ScreeningConfig(),
    as_of_hours: Sequence[float] = DEFAULT_LADDER_HOURS,
    split: BatchHoldout | None = None,
    test_fraction: float = 0.4,
    random_state: int = 7,
    methods: Iterable[str] = ALL_METHODS,
) -> LadderReport:
    """Repeat the screen at increasing hours and measure detection lead time.

    ``lead_hours`` is the gap between the first hour a method flags a component
    and the first hour that component actually crosses its approved limit.
    """

    active_split = split or split_batches(
        dataset.readings, test_fraction=test_fraction, random_state=random_state
    )
    methods = tuple(methods)
    metric_frames: list[pd.DataFrame] = []
    first_flag: dict[tuple[str, str], float] = {}
    seen_components: set[str] = set()

    for hour in sorted(float(value) for value in as_of_hours):
        hour_config = replace(config, as_of_hour=hour)
        train_features, test_features = build_split_features(
            dataset.readings,
            active_split,
            as_of_hour=hour,
            minimum_observations=config.minimum_observations,
        )
        screened = screen_components(train_features, test_features, hour_config)
        metric_frames.append(
            evaluate_screening(screened, dataset.labels, as_of_hour=hour, methods=methods)
        )
        seen_components.update(screened["component_id"].astype(str))
        for method in methods:
            flagged = screened.loc[screened[f"{method}_flag"], "component_id"].astype(str)
            for component_id in flagged:
                first_flag.setdefault((method, component_id), hour)

    onset_column = _onset_column(dataset.labels)
    labels = dataset.labels.set_index("component_id")
    rows: list[dict[str, object]] = []
    for method in methods:
        for component_id in sorted(seen_components):
            label = labels.loc[component_id]
            flag_hour = first_flag.get((method, component_id), float("nan"))
            exceedance = float(label["first_exceedance_hour"])
            lead = (
                exceedance - flag_hour
                if np.isfinite(flag_hour) and np.isfinite(exceedance)
                else float("nan")
            )
            rows.append(
                {
                    "method": method,
                    "component_id": component_id,
                    "batch_id": str(label["batch_id"]),
                    "scenario": str(label["scenario"]),
                    "is_defect": bool(label["is_defect"]),
                    "is_tester_fault": bool(label["is_tester_fault"]),
                    "anomaly_onset_hour": float(label[onset_column]),
                    "first_flag_hour": flag_hour,
                    "first_exceedance_hour": exceedance,
                    "lead_hours": lead,
                }
            )
    lead_times = pd.DataFrame(rows)
    return LadderReport(
        metrics=pd.concat(metric_frames, ignore_index=True),
        lead_times=lead_times,
        summary=summarise_lead_times(lead_times),
        as_of_hours=tuple(sorted(float(value) for value in as_of_hours)),
        split=active_split,
    )


def summarise_lead_times(lead_times: pd.DataFrame) -> pd.DataFrame:
    """Aggregate the per-component ladder outcome into one row per method."""

    rows: list[dict[str, object]] = []
    defects = lead_times.loc[lead_times["is_defect"]]
    for method, group in defects.groupby("method", sort=True):
        flagged = group["first_flag_hour"].notna()
        early = group["lead_hours"] > 0
        never_crosses = group["first_exceedance_hour"].isna()
        rows.append(
            {
                "method": method,
                "method_label": METHOD_LABELS.get(str(method), str(method)),
                "n_defects": int(len(group)),
                "n_ever_flagged": int(flagged.sum()),
                "n_flagged_before_crossing": int((flagged & early).sum()),
                "n_flagged_never_crossing": int((flagged & never_crosses).sum()),
                "median_first_flag_hour": (
                    float(group.loc[flagged, "first_flag_hour"].median())
                    if flagged.any()
                    else float("nan")
                ),
                "median_lead_hours": (
                    float(group.loc[flagged & early, "lead_hours"].median())
                    if (flagged & early).any()
                    else float("nan")
                ),
                "mean_lead_hours": (
                    float(group.loc[flagged & early, "lead_hours"].mean())
                    if (flagged & early).any()
                    else float("nan")
                ),
            }
        )
    return pd.DataFrame(rows)


def run_parameter_sweep(
    dataset: SyntheticDataset,
    *,
    as_of_hours: Sequence[float] = (12.0, 24.0, 48.0),
    contaminations: Sequence[float] = (0.05, 0.1, 0.15, 0.2),
    robust_thresholds: Sequence[float] = (2.5, 3.5, 4.5),
    fixed_limit_fractions: Sequence[float] = (0.8, 1.0),
    base_config: ScreeningConfig = ScreeningConfig(),
    split: BatchHoldout | None = None,
    test_fraction: float = 0.4,
    random_state: int = 7,
    methods: Iterable[str] = ALL_METHODS,
) -> pd.DataFrame:
    """Deterministic grid sweep over the screening parameters."""

    active_split = split or split_batches(
        dataset.readings, test_fraction=test_fraction, random_state=random_state
    )
    methods = tuple(methods)
    feature_cache: dict[float, tuple[pd.DataFrame, pd.DataFrame]] = {}
    frames: list[pd.DataFrame] = []

    for hour in sorted(float(value) for value in as_of_hours):
        if hour not in feature_cache:
            feature_cache[hour] = build_split_features(
                dataset.readings,
                active_split,
                as_of_hour=hour,
                minimum_observations=base_config.minimum_observations,
            )
        train_features, test_features = feature_cache[hour]
        for contamination in contaminations:
            # The forest sees neither the robust threshold nor the fixed-limit
            # fraction, so it is fitted once and reused across both.
            detectors = fit_detectors(
                train_features,
                replace(base_config, as_of_hour=hour, contamination=float(contamination)),
            )
            for robust_threshold in robust_thresholds:
                for fixed_limit_fraction in fixed_limit_fractions:
                    config = replace(
                        base_config,
                        as_of_hour=hour,
                        contamination=float(contamination),
                        robust_threshold=float(robust_threshold),
                        fixed_limit_fraction=float(fixed_limit_fraction),
                    )
                    screened = screen_components(
                        train_features, test_features, config, detectors=detectors
                    )
                    metrics = evaluate_screening(
                        screened, dataset.labels, as_of_hour=hour, methods=methods
                    )
                    for name, value in config.to_dict().items():
                        metrics[name] = value
                    frames.append(metrics)
    return pd.concat(frames, ignore_index=True)


def sweep_summary(sweep: pd.DataFrame) -> pd.DataFrame:
    """Drop the parameters a method cannot see, then remove duplicate rows."""

    reported = [
        "defect_recall",
        "false_negative_rate",
        "false_positive_rate",
        "precision",
        "median_lead_time_hours",
        "n_early_warnings",
    ]
    frames: list[pd.DataFrame] = []
    for method, group in sweep.groupby("method", sort=True):
        parameters = [
            name
            for name in METHOD_PARAMETERS.get(str(method), ("as_of_hour",))
            if name in group.columns
        ]
        subset = group[["method", "method_label", *parameters, *reported]].drop_duplicates(
            subset=["method", *parameters]
        )
        for name in METHOD_PARAMETERS["combined"]:
            if name not in subset.columns:
                subset[name] = pd.NA
        frames.append(subset)
    combined = pd.concat(frames, ignore_index=True)
    ordered = ["method", "method_label", *METHOD_PARAMETERS["combined"], *reported]
    return combined[[column for column in ordered if column in combined.columns]]


def compare_fit_scopes(
    dataset: SyntheticDataset,
    *,
    config: ScreeningConfig = ScreeningConfig(),
    split: BatchHoldout | None = None,
    test_fraction: float = 0.4,
    random_state: int = 7,
) -> pd.DataFrame:
    """Measure the effect of pooling unlike families in one Isolation Forest."""

    active_split = split or split_batches(
        dataset.readings, test_fraction=test_fraction, random_state=random_state
    )
    frames: list[pd.DataFrame] = []
    for scope in ("per_family", "pooled"):
        report = run_holdout_evaluation(
            dataset,
            config=replace(config, fit_scope=scope),
            split=active_split,
            methods=("isolation_forest", "combined"),
        )
        metrics = report.metrics.copy()
        metrics["fit_scope"] = scope
        frames.append(metrics)
    return pd.concat(frames, ignore_index=True)


def summarise_recommendations(report: EvaluationReport, labels: pd.DataFrame) -> pd.DataFrame:
    """Route the combined result through the existing recommendation rules.

    The software recommends; it never certifies. Every component lands in
    ACCEPT, MONITOR, RETEST or ENGINEER_REVIEW and a person decides next.
    """

    results: list[AnomalyResult] = BatchAwareAnomalyDetector.to_results(report.screened)
    frame = pd.DataFrame(
        {
            "component_id": [result.component_id for result in results],
            "recommended_action": [recommend_action(result)[0] for result in results],
        }
    )
    merged = frame.merge(
        labels[["component_id", "scenario", "is_defect", "is_tester_fault"]],
        on="component_id",
        how="left",
    )
    summary = (
        merged.groupby("recommended_action", sort=True)
        .agg(
            n_components=("component_id", "size"),
            n_true_defects=("is_defect", "sum"),
            n_tester_faults=("is_tester_fault", "sum"),
        )
        .reset_index()
    )
    summary["share_of_components"] = summary["n_components"] / len(merged)
    return summary
