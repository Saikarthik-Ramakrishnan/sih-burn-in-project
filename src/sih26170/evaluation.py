"""Leakage-safe evaluation for labelled burn-in datasets."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from .anomaly import BatchAwareAnomalyDetector
from .features import GROUP_COLUMNS, build_component_features
from .synthetic import SyntheticDataset


GROUND_TRUTH_COLUMNS = {
    *GROUP_COLUMNS,
    "scenario",
    "is_defect",
    "is_tester_fault",
    "anomaly_onset_hour",
    "first_exceedance_hour",
}

METHOD_FLAGS = {
    "fixed_limit": "flag_fixed_limit",
    "robust_mad": "flag_robust_mad",
    "isolation_forest": "flag_isolation_forest",
    "combined": "flag_combined",
}


@dataclass(frozen=True)
class BatchSplit:
    train_batch_ids: tuple[str, ...]
    test_batch_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.train_batch_ids or not self.test_batch_ids:
            raise ValueError("both train and test splits must contain batches")
        overlap = set(self.train_batch_ids).intersection(self.test_batch_ids)
        if overlap:
            raise ValueError(f"batches occur in both splits: {sorted(overlap)}")


@dataclass(frozen=True)
class EvaluationReport:
    as_of_hour: float
    split: BatchSplit
    metrics: pd.DataFrame
    scenario_metrics: pd.DataFrame
    scored_components: pd.DataFrame
    dataset_seed: int
    generator_version: str
    contamination: float
    robust_threshold: float
    split_random_state: int
    detector_random_state: int
    train_components: int
    test_components: int


def make_batch_split(
    readings: pd.DataFrame,
    *,
    test_fraction: float = 1.0 / 3.0,
    random_state: int = 26170,
) -> BatchSplit:
    """Split complete batches, never individual component rows."""

    if not 0.0 < test_fraction < 1.0:
        raise ValueError("test_fraction must sit strictly between zero and one")
    if "batch_id" not in readings:
        raise ValueError("readings must contain batch_id")
    batch_ids = np.array(sorted(readings["batch_id"].astype(str).unique()))
    if len(batch_ids) < 2:
        raise ValueError("at least two batches are required for evaluation")

    rng = np.random.default_rng(random_state)
    shuffled = batch_ids.copy()
    rng.shuffle(shuffled)
    test_count = max(1, min(len(shuffled) - 1, int(round(len(shuffled) * test_fraction))))
    test_ids = tuple(sorted(shuffled[:test_count].tolist()))
    train_ids = tuple(sorted(shuffled[test_count:].tolist()))
    return BatchSplit(train_batch_ids=train_ids, test_batch_ids=test_ids)


def _validate_labels(labels: pd.DataFrame) -> None:
    missing = sorted(GROUND_TRUTH_COLUMNS.difference(labels.columns))
    if missing:
        raise ValueError(f"labels are missing required columns: {', '.join(missing)}")
    if labels.duplicated(GROUP_COLUMNS).any():
        raise ValueError("ground-truth labels must have one row per component measurement")


def _safe_ratio(numerator: int, denominator: int) -> float:
    return float(numerator / denominator) if denominator else float("nan")


def _recall(flags: pd.Series, truth: pd.Series) -> float:
    positives = int(truth.sum())
    return _safe_ratio(int((flags & truth).sum()), positives)


def _method_metrics(
    scored: pd.DataFrame,
    *,
    method: str,
    flag_column: str,
    as_of_hour: float,
) -> dict[str, object]:
    flags = scored[flag_column].astype(bool)
    truth = scored["is_true_anomaly"].astype(bool)
    healthy = ~truth
    true_positive = int((flags & truth).sum())
    false_positive = int((flags & healthy).sum())
    false_negative = int((~flags & truth).sum())
    true_negative = int((~flags & healthy).sum())

    early_failures = scored["is_early_future_failure"].astype(bool)
    lead_mask = flags & early_failures
    lead_hours = (
        scored.loc[lead_mask, "first_exceedance_hour"].astype(float) - as_of_hour
    )

    return {
        "method": method,
        "evaluated_components": int(len(scored)),
        "flagged_components": int(flags.sum()),
        "true_positive": true_positive,
        "false_positive": false_positive,
        "false_negative": false_negative,
        "true_negative": true_negative,
        "review_recall": _safe_ratio(true_positive, int(truth.sum())),
        "false_negative_rate": _safe_ratio(false_negative, int(truth.sum())),
        "false_positive_rate": _safe_ratio(false_positive, int(healthy.sum())),
        "precision": _safe_ratio(true_positive, int(flags.sum())),
        "defect_recall": _recall(flags, scored["is_defect"].astype(bool)),
        "tester_fault_recall": _recall(
            flags, scored["is_tester_fault"].astype(bool)
        ),
        "started_anomaly_recall": _recall(
            flags, scored["is_started_by_as_of"].astype(bool)
        ),
        "future_failure_recall": _recall(
            flags, scored["is_future_limit_failure"].astype(bool)
        ),
        "early_failure_recall": _recall(flags, early_failures),
        "median_early_warning_lead_hours": (
            float(lead_hours.median()) if not lead_hours.empty else float("nan")
        ),
    }


def _scenario_metrics(scored: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for method, flag_column in METHOD_FLAGS.items():
        for scenario, group in scored.groupby("scenario", sort=True):
            rows.append(
                {
                    "method": method,
                    "scenario": str(scenario),
                    "components": int(len(group)),
                    "flagged": int(group[flag_column].astype(bool).sum()),
                    "flag_rate": float(group[flag_column].astype(bool).mean()),
                }
            )
    return pd.DataFrame(rows)


def evaluate_synthetic_dataset(
    dataset: SyntheticDataset,
    *,
    as_of_hour: float = 24.0,
    test_fraction: float = 1.0 / 3.0,
    split_random_state: int = 26170,
    detector_random_state: int = 42,
    contamination: float = 0.1,
    robust_threshold: float = 3.5,
) -> EvaluationReport:
    """Evaluate all screening methods on held-out complete batches.

    Ground-truth labels are joined only after models have produced their scores.
    This prevents scenario names and future outcomes from becoming features.
    """

    _validate_labels(dataset.labels)
    split = make_batch_split(
        dataset.readings,
        test_fraction=test_fraction,
        random_state=split_random_state,
    )
    train_readings = dataset.readings.loc[
        dataset.readings["batch_id"].astype(str).isin(split.train_batch_ids)
    ].copy()
    test_readings = dataset.readings.loc[
        dataset.readings["batch_id"].astype(str).isin(split.test_batch_ids)
    ].copy()

    train_features = build_component_features(train_readings, as_of_hour=as_of_hour)
    test_features = build_component_features(test_readings, as_of_hour=as_of_hour)
    detector = BatchAwareAnomalyDetector(
        contamination=contamination,
        robust_threshold=robust_threshold,
        random_state=detector_random_state,
    ).fit(train_features)
    scored = detector.score(test_features)

    scored["flag_fixed_limit"] = scored["current_value"] >= scored["upper_limit"]
    scored["flag_robust_mad"] = scored["is_robust_anomaly"].astype(bool)
    scored["flag_isolation_forest"] = scored["is_model_anomaly"].astype(bool)
    scored["flag_combined"] = scored["is_anomaly"].astype(bool)

    truth_columns = [
        *GROUP_COLUMNS,
        "scenario",
        "is_defect",
        "is_tester_fault",
        "anomaly_onset_hour",
        "first_exceedance_hour",
    ]
    scored = scored.merge(
        dataset.labels[truth_columns],
        on=GROUP_COLUMNS,
        how="left",
        validate="one_to_one",
    )
    if scored["scenario"].isna().any():
        raise ValueError("one or more scored components have no ground-truth label")

    scored["is_true_anomaly"] = (
        scored["is_defect"].astype(bool) | scored["is_tester_fault"].astype(bool)
    )
    onset = pd.to_numeric(scored["anomaly_onset_hour"], errors="coerce")
    scored["is_started_by_as_of"] = scored["is_true_anomaly"] & (
        onset.notna() & (onset <= as_of_hour)
    )
    first_exceedance = pd.to_numeric(
        scored["first_exceedance_hour"], errors="coerce"
    )
    scored["is_future_limit_failure"] = (
        scored["is_defect"].astype(bool) & first_exceedance.notna()
    )
    scored["is_early_future_failure"] = (
        scored["is_defect"].astype(bool) & (first_exceedance > as_of_hour)
    )

    metric_rows = [
        _method_metrics(
            scored,
            method=method,
            flag_column=flag_column,
            as_of_hour=as_of_hour,
        )
        for method, flag_column in METHOD_FLAGS.items()
    ]
    metrics = pd.DataFrame(metric_rows)
    scenario_metrics = _scenario_metrics(scored)
    return EvaluationReport(
        as_of_hour=float(as_of_hour),
        split=split,
        metrics=metrics,
        scenario_metrics=scenario_metrics,
        scored_components=scored,
        dataset_seed=dataset.seed,
        generator_version=dataset.generator_version,
        contamination=float(contamination),
        robust_threshold=float(robust_threshold),
        split_random_state=int(split_random_state),
        detector_random_state=int(detector_random_state),
        train_components=int(len(train_features)),
        test_components=int(len(test_features)),
    )


def evaluate_time_sweep(
    dataset: SyntheticDataset,
    *,
    as_of_hours: tuple[float, ...] = (6.0, 12.0, 24.0, 48.0, 72.0, 96.0),
    **evaluation_kwargs: object,
) -> pd.DataFrame:
    """Measure how screening performance changes as evidence accumulates."""

    if not as_of_hours:
        raise ValueError("as_of_hours cannot be empty")
    rows: list[pd.DataFrame] = []
    expected_split: BatchSplit | None = None
    for as_of_hour in as_of_hours:
        report = evaluate_synthetic_dataset(
            dataset,
            as_of_hour=float(as_of_hour),
            **evaluation_kwargs,
        )
        if expected_split is None:
            expected_split = report.split
        elif report.split != expected_split:
            raise RuntimeError("time sweep produced inconsistent batch splits")
        metrics = report.metrics.copy()
        metrics.insert(0, "as_of_hour", float(as_of_hour))
        rows.append(metrics)
    return pd.concat(rows, ignore_index=True)


def evaluate_repeated_splits(
    dataset: SyntheticDataset,
    *,
    as_of_hour: float = 24.0,
    split_random_states: tuple[int, ...] = (101, 211, 307, 401, 503),
    **evaluation_kwargs: object,
) -> pd.DataFrame:
    """Repeat held-out-batch evaluation so one lucky split cannot dominate."""

    if not split_random_states:
        raise ValueError("split_random_states cannot be empty")
    rows: list[pd.DataFrame] = []
    for split_state in split_random_states:
        report = evaluate_synthetic_dataset(
            dataset,
            as_of_hour=as_of_hour,
            split_random_state=int(split_state),
            **evaluation_kwargs,
        )
        metrics = report.metrics.copy()
        metrics.insert(0, "split_random_state", int(split_state))
        metrics.insert(0, "as_of_hour", float(as_of_hour))
        rows.append(metrics)
    return pd.concat(rows, ignore_index=True)


def summarize_repeated_splits(repeated_metrics: pd.DataFrame) -> pd.DataFrame:
    """Return mean and sample standard deviation for core metrics."""

    required = {
        "method",
        "review_recall",
        "false_negative_rate",
        "false_positive_rate",
        "precision",
        "future_failure_recall",
        "early_failure_recall",
    }
    missing = required.difference(repeated_metrics.columns)
    if missing:
        raise ValueError(f"repeated metrics missing columns: {', '.join(sorted(missing))}")
    metric_columns = sorted(required.difference({"method"}))
    summary = repeated_metrics.groupby("method")[metric_columns].agg(["mean", "std"])
    summary.columns = [f"{metric}_{stat}" for metric, stat in summary.columns]
    return summary.reset_index()


def write_evaluation_report(report: EvaluationReport, output_dir: str | Path) -> Path:
    """Write auditable CSV results and run metadata."""

    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    report.metrics.to_csv(destination / "metrics.csv", index=False)
    report.scenario_metrics.to_csv(destination / "scenario_metrics.csv", index=False)
    report.scored_components.to_csv(destination / "scored_components.csv", index=False)
    metadata = {
        "as_of_hour": report.as_of_hour,
        "train_batch_ids": list(report.split.train_batch_ids),
        "test_batch_ids": list(report.split.test_batch_ids),
        "dataset_seed": report.dataset_seed,
        "generator_version": report.generator_version,
        "contamination": report.contamination,
        "robust_threshold": report.robust_threshold,
        "split_random_state": report.split_random_state,
        "detector_random_state": report.detector_random_state,
        "train_components": report.train_components,
        "test_components": report.test_components,
        "synthetic_data_only": True,
        "warning": "Results from synthetic data are not aerospace validation.",
    }
    (destination / "run_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    return destination
