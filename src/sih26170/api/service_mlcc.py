"""MLCC screening path: Karthik's prototype behind Ashvitha's response contract.

Division of responsibility, deliberately narrow:

  * The API owns transport - byte limits, encoding, CSV schema, duplicate
    identities, unit/limit gating, request ids, durations, warnings, and the
    typed response the frontend pins against.
  * The CORE owns the science - eligibility, feature construction, anomaly
    scoring, forecasting, intervals and the decision. This module does not
    recompute, second-guess or round any of it.

Three honesty rules are enforced here rather than assumed:

  1. ``decision_counts`` counts SCORED records only. The core's own
     ``summary.recommendations`` folds unscored records in as ``RETEST``; that
     would read as "32 parts need a retest" when some of them were never
     screened at all. The unscored count stays separately visible.
  2. The forecast model is whatever ``metadata.selected_model`` says. XGBoost is
     never named beside a forecast it did not produce, and ``selection_warning``
     travels with the response when the caller's choice is not the validation
     winner.
  3. Later observations arrive from the core in one of two envelopes and are
     never merged: ``future_outcomes`` are observed readings,
     ``simulation_truth`` are latent generator values that are not sensor
     measurements at all.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

import pandas as pd

from sih26170.api.config import SCHEMA_VERSION, Settings
from sih26170.api.errors import ApiError, ErrorCode, ErrorDetail, unavailable
from sih26170.api.ingestion import HISTORY_KEY, IngestedDataset, split_early_and_future
from sih26170.api.profiles import DataProvenance, LimitDirection
from sih26170.api.schemas import (
    RECOMMENDATION_URGENCY,
    AnomalyEvidence,
    CapabilityFlags,
    CapabilityStatus,
    ComponentSummary,
    DecisionCounts,
    EvaluationSection,
    ForecastEvidence,
    LimitInfo,
    ModelInfo,
    OutcomeRecord,
    PeerStatistics,
    Recommendation,
    ResponseWarning,
    ScreenResponse,
    ScreeningRecord,
    TrajectoryPoint,
    UnscoredRecord,
    UnscoredReason,
    XgboostContribution,
    XgboostExplanation,
)
from sih26170.prediction.mlcc_engine import MlccEngine

#: Per-record context carried through for display. Never a predictive input.
CONTEXT_KEYS: tuple[str, ...] = (
    "part_number",
    "nominal_capacitance_nf",
    "rated_voltage_v",
    "package_code",
    "dielectric",
    "applied_voltage_v",
    "measurement_voltage_v",
    "temperature_c",
    "measurement_temperature_c",
    "prior_storage_humidity_pct",
    "tester_id",
    "tester_channel",
    "board_position",
    "data_source",
    "generator_version",
)


def _f(value: Any) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number == number and abs(number) != float("inf") else None


def _unscored_reason(reason_codes: list[str]) -> UnscoredReason:
    """Map the core's free-text reasons onto the API's stable reason enum."""
    joined = " ".join(reason_codes).casefold()
    if "0-hour" in joined or "24-hour" in joined or "hour reading" in joined:
        return UnscoredReason.MISSING_CHECKPOINT
    if "profile_id" in joined or "unsupported profile" in joined:
        return UnscoredReason.UNSUPPORTED_PROFILE
    if "unsupported family" in joined or "unsupported measurement" in joined:
        return UnscoredReason.UNSUPPORTED_PROFILE
    if "hours must be" in joined:
        return UnscoredReason.MISSING_CHECKPOINT
    return UnscoredReason.CORE_ERROR


def preflight(dataset: IngestedDataset, engine: MlccEngine) -> list[ResponseWarning]:
    """Gate the upload against what this artifact actually supports.

    Runs before the core is called so an unusable file fails with a structured
    error instead of a stack trace, and so a lower limit can never be quietly
    screened as an upper limit.
    """
    frame = dataset.frame
    identity = engine.identity
    warnings: list[ResponseWarning] = []

    if "lower_limit" in frame.columns:
        supplied = frame["lower_limit"].dropna()
        if len(supplied) > 0:
            raise ApiError(
                ErrorCode.UNSUPPORTED_PROFILE,
                "This artifact screens against an upper leakage limit only. The "
                "file supplies lower_limit values, which would require two-sided "
                "screening that has not been validated. The file is rejected "
                "rather than screened against the wrong side of the specification.",
                details=[
                    ErrorDetail(
                        code=ErrorCode.UNSUPPORTED_PROFILE,
                        message="Remove lower_limit, or wait for a validated two-sided profile.",
                        column="lower_limit",
                    )
                ],
            )

    families = set(frame["component_family"].astype(str))
    measurements = set(frame["measurement_name"].astype(str))
    if families != {identity.family} or measurements != {identity.measurement}:
        unsupported_f = sorted(families - {identity.family})
        unsupported_m = sorted(measurements - {identity.measurement})
        if unsupported_f or unsupported_m:
            warnings.append(
                ResponseWarning(
                    code="UNSUPPORTED_FAMILY_OR_MEASUREMENT_PRESENT",
                    message=(
                        f"This bundle supports {identity.family} / "
                        f"{identity.measurement} only. Rows for other "
                        f"families {unsupported_f or '[]'} or measurements "
                        f"{unsupported_m or '[]'} will be reported unscored. "
                        "Renaming a family does not make a model apply to it."
                    ),
                )
            )

    if "measurement_unit" in frame.columns:
        units = {u for u in frame["measurement_unit"].astype(str) if u.strip()}
        bad = {u for u in units if u.casefold() not in {identity.unit.casefold(), "ua", "µa", "μa"}}
        if bad:
            raise ApiError(
                ErrorCode.INCOMPATIBLE_UNITS,
                f"This artifact requires {identity.measurement} in {identity.unit}. "
                f"The file declares {sorted(bad)}. The API does not convert units.",
                details=[
                    ErrorDetail(
                        code=ErrorCode.INCOMPATIBLE_UNITS,
                        message=f"Expected unit '{identity.unit}'.",
                        column="measurement_unit",
                        value=sorted(bad)[0],
                    )
                ],
            )

    if "profile_id" not in frame.columns:
        warnings.append(
            ResponseWarning(
                code="PROFILE_ID_COLUMN_ABSENT",
                message=(
                    "The file has no profile_id column, so no row can be matched "
                    f"to one of this bundle's supported profiles "
                    f"({', '.join(identity.supported_profiles)}). Every history "
                    "will be reported unscored."
                ),
            )
        )
    return warnings


def _build_record(
    core: dict[str, Any], provenance: DataProvenance, unit: str
) -> ScreeningRecord:
    metadata = core.get("metadata") or {}
    limit = _f(core.get("safety_limit"))
    latest = _f(core.get("current_value"))

    headroom = (limit - latest) if (limit is not None and latest is not None) else None
    headroom_fraction = (
        headroom / abs(limit) if (headroom is not None and limit not in (None, 0.0)) else None
    )

    explanation_payload = core.get("xgboost_explanation") or None
    explanation = None
    if explanation_payload:
        explanation = XgboostExplanation(
            explains=str(explanation_payload.get("explains", "")),
            is_active_forecast=bool(explanation_payload.get("is_active_forecast", False)),
            explained_model=(
                str(explanation_payload["explained_model"])
                if explanation_payload.get("explained_model") is not None
                else None
            ),
            base_value_ua=float(explanation_payload.get("base_value_ua", 0.0)),
            top_contributions=[
                XgboostContribution(
                    feature=str(item["feature"]),
                    contribution_ua=float(item["contribution_ua"]),
                    feature_value=float(item["feature_value"]),
                )
                for item in explanation_payload.get("top_contributions", [])
            ],
        )

    trajectory = [
        TrajectoryPoint(hour=float(point["hours"]), value=float(point["measurement_value"]))
        for point in core.get("early_readings", [])
    ]
    initial = _f(core.get("initial_value"))
    percent_change = _f(core.get("percent_change"))

    predicted = _f(core.get("predicted_final_value"))
    lower = _f(core.get("prediction_lower"))
    upper = _f(core.get("prediction_upper"))
    crosses = (
        (predicted > limit) if (predicted is not None and limit is not None) else None
    )

    peer_count = int(core.get("peer_count") or 0)

    return ScreeningRecord(
        component_id=str(core["component_id"]),
        batch_id=str(core["batch_id"]),
        component_family=str(core["component_family"]),
        measurement_name=str(core["measurement_name"]),
        recommendation=Recommendation(core["recommendation"]),
        recommendation_basis="anomaly_and_forecast",
        provisional=False,
        anomaly=AnomalyEvidence(
            status=CapabilityStatus.AVAILABLE,
            score=_f(core.get("anomaly_score")),
            is_anomaly=bool(core.get("is_anomaly")),
            method="median_mad+isolation_forest",
            reason_codes=[str(r) for r in core.get("reason_codes", [])],
            score_kind=core.get("anomaly_score_kind"),
            model_score=_f(core.get("model_anomaly_score")),
            robust_deviation_score=_f(core.get("robust_deviation_score")),
            note=(
                "Relative deviation against comparable peers in the same batch. "
                "This score is not a probability of physical failure."
            ),
        ),
        forecast=ForecastEvidence(
            status=(
                CapabilityStatus.AVAILABLE if predicted is not None else CapabilityStatus.UNAVAILABLE
            ),
            predicted_final_value=predicted,
            prediction_lower=lower,
            prediction_upper=upper,
            target_hour=_f(core.get("target_hour")),
            interval_nominal_coverage=_f(core.get("interval_nominal_coverage")),
            interval_method=core.get("interval_method"),
            interval_stratum=core.get("interval_stratum"),
            upper_bound_nominal_level=_f(core.get("upper_bound_nominal_level")),
            prediction_lower_two_sided=_f(core.get("prediction_lower_two_sided")),
            prediction_upper_two_sided=_f(core.get("prediction_upper_two_sided")),
            interval_warning=core.get("interval_warning"),
            model_version=core.get("forecast_model"),
            predicted_to_cross_limit=crosses,
            prediction_readiness=core.get("prediction_readiness"),
            out_of_training_range_features=list(core.get("out_of_training_range_features", [])),
            prediction_readiness_warning=core.get("prediction_readiness_warning"),
            missing_optional_features=list(core.get("missing_optional_features", [])),
            xgboost_candidate_final_value=_f(core.get("xgboost_candidate_final_value")),
            xgboost_explanation=explanation,
        ),
        limits=LimitInfo(
            direction=LimitDirection.UPPER,
            upper_limit=limit,
            lower_limit=None,
            applicable_limit=limit,
            headroom=headroom,
            headroom_fraction=headroom_fraction,
            limit_fraction=_f(core.get("limit_fraction")),
        ),
        peers=PeerStatistics(
            sample_size=peer_count,
            sufficient=peer_count >= 8,
            status=(
                CapabilityStatus.AVAILABLE if peer_count >= 8 else CapabilityStatus.INSUFFICIENT_DATA
            ),
            current_batch_robust_z=_f(core.get("current_batch_robust_z")),
            slope_batch_robust_z=_f(core.get("slope_batch_robust_z")),
            warning=core.get("peer_comparison_warning"),
        ),
        measurement_unit=core.get("unit") or unit,
        initial_value=initial,
        latest_value=latest,
        last_observation_hour=_f(core.get("as_of_hour")),
        absolute_change=_f(core.get("delta")),
        percent_change=percent_change,
        percent_change_available=percent_change is not None,
        slope_per_hour=_f(core.get("slope_per_hour")),
        early_trajectory=trajectory,
        part_number=(str(metadata["part_number"]) if metadata.get("part_number") is not None else None),
        test_condition=None,
        temperature_c=_f(metadata.get("temperature_c")),
        humidity_pct=None,
        applied_voltage_v=_f(metadata.get("applied_voltage_v")),
        board_position=(
            str(metadata["board_position"]) if metadata.get("board_position") is not None else None
        ),
        data_source=(str(metadata["data_source"]) if metadata.get("data_source") is not None else None),
        provenance=provenance,
        profile_id=(str(metadata["profile_id"]) if metadata.get("profile_id") is not None else None),
        recommendation_reasons=[str(r) for r in core.get("recommendation_reasons", [])],
        data_quality_warning=core.get("data_quality_warning"),
        context={
            key: (_f(metadata[key]) if isinstance(metadata[key], (int, float)) else str(metadata[key]))
            for key in CONTEXT_KEYS
            if metadata.get(key) is not None
        },
    )


def _summaries(
    records: list[ScreeningRecord], unscored: list[UnscoredRecord]
) -> list[ComponentSummary]:
    buckets: dict[tuple[str, str, str], dict] = {}

    def bucket(component_id: str, batch_id: str, family: str) -> dict:
        return buckets.setdefault(
            (component_id, batch_id, family),
            {"scored": [], "unscored": [], "measurements": []},
        )

    for record in records:
        entry = bucket(record.component_id, record.batch_id, record.component_family)
        entry["scored"].append(record.recommendation)
        entry["measurements"].append(record.measurement_name)
    for item in unscored:
        entry = bucket(item.component_id, item.batch_id, item.component_family)
        entry["unscored"].append(item.measurement_name)
        entry["measurements"].append(item.measurement_name)

    summaries = [
        ComponentSummary(
            component_id=component_id,
            batch_id=batch_id,
            component_family=family,
            summary_recommendation=(
                max(entry["scored"], key=lambda r: RECOMMENDATION_URGENCY[r])
                if entry["scored"]
                else None
            ),
            scored_measurement_count=len(entry["scored"]),
            unscored_measurement_count=len(entry["unscored"]),
            partial_coverage=bool(entry["unscored"]),
            measurement_names=sorted(set(entry["measurements"])),
        )
        for (component_id, batch_id, family), entry in buckets.items()
    ]
    summaries.sort(key=lambda s: (s.batch_id, s.component_id))
    return summaries


def limits_by_identity(frame: pd.DataFrame) -> dict[tuple[str, str, str, str], float]:
    """Map each history to its upper limit, for scoring outcomes after the fact.

    The core's ``future_outcomes`` rows carry the later reading but not the
    specification limit, so the limit is taken from the uploaded history.
    Ingestion has already rejected any file where a limit changes within a
    history, so the first value per history is the only value.
    """
    limits: dict[tuple[str, str, str, str], float] = {}
    if "upper_limit" not in frame.columns:
        return limits

    for row in frame.itertuples(index=False):
        limit = _f(row.upper_limit)
        if limit is None:
            continue
        limits.setdefault(
            (
                str(row.component_id),
                str(row.batch_id),
                str(row.component_family),
                str(row.measurement_name),
            ),
            limit,
        )
    return limits


def _evaluation(
    result: dict[str, Any],
    target_hour: float,
    limits: dict[tuple[str, str, str, str], float],
    source_filename: str | None = None,
) -> EvaluationSection | None:
    """Map the core's outcome envelope, keeping observed and latent distinct."""
    observed = result.get("future_outcomes")
    latent = result.get("simulation_truth")

    if observed:
        outcomes: list[OutcomeRecord] = []
        for row in observed:
            identity = (
                str(row["component_id"]),
                str(row["batch_id"]),
                str(row["component_family"]),
                str(row["measurement_name"]),
            )
            value = float(row["measurement_value"])
            limit = limits.get(identity)
            # This bundle screens one side only, and preflight rejects any file
            # supplying lower limits, so "crossed" is unambiguously "above".
            # An unknown limit stays null rather than defaulting to False, which
            # would read as a component that safely stayed in spec.
            outcomes.append(
                OutcomeRecord(
                    component_id=identity[0],
                    batch_id=identity[1],
                    component_family=identity[2],
                    measurement_name=identity[3],
                    observed_value=value,
                    observed_hour=float(row["hours"]),
                    applicable_limit=limit,
                    crossed_applicable_limit=None if limit is None else value > limit,
                )
            )

        return EvaluationSection(
            available=True,
            kind="observed_readings",
            source_filename=source_filename,
            target_hour=target_hour,
            note=(
                "Evaluation only. These are later OBSERVED measurements. They were "
                "excluded from feature building, anomaly scoring, forecasting and "
                "peer statistics, and reached the response only after screening."
            ),
            outcomes=outcomes,
        )

    if latent:
        return EvaluationSection(
            available=True,
            kind="simulation_truth",
            source_filename=source_filename,
            target_hour=target_hour,
            note=(
                "Evaluation only, and NOT sensor measurements. These are latent "
                "values from the synthetic generator, supplied as simulator labels. "
                "They must never be presented as observed readings."
            ),
            outcomes=[],
        )
    return None


def validate_outcomes(
    outcome: IngestedDataset,
    early_frame: pd.DataFrame,
    engine: MlccEngine,
    as_of_hour: float,
) -> tuple[pd.DataFrame, list[ResponseWarning]]:
    """Check a separate outcome file against the early input it belongs to.

    The core inner-joins outcome rows against scored records, so an identity it
    does not recognise is silently dropped. That is the wrong behaviour for a
    demo: pairing the wrong outcome file would quietly reveal nothing. Every
    check here therefore runs before the core sees the rows.

    Nothing validated here can influence inference. The frame returned is used
    only for the evaluation section.
    """
    frame = outcome.frame
    warnings = [
        ResponseWarning(code=w.code, message=w.message, count=w.count)
        for w in outcome.warnings
    ]
    identity_columns = list(HISTORY_KEY)

    # 1. Strictly after the cutoff.
    early_or_before = frame.loc[frame["hours"] <= as_of_hour + 1e-9]
    if not early_or_before.empty:
        offenders = sorted({f"{h:g}" for h in early_or_before["hours"].unique()})
        raise ApiError(
            ErrorCode.INVALID_HOURS,
            f"The outcome file must contain observations strictly after "
            f"{as_of_hour:g} h. It contains readings at {', '.join(offenders)} h.",
            details=[
                ErrorDetail(
                    code=ErrorCode.INVALID_HOURS,
                    message=(
                        f"{len(early_or_before)} row(s) are at or before the cutoff. "
                        "Early measurements belong in the main file."
                    ),
                    column="hours",
                )
            ],
        )

    # 2. One observation per identity per hour.
    duplicated = frame.duplicated(subset=identity_columns + ["hours"], keep=False)
    if duplicated.any():
        sample = frame.loc[duplicated, identity_columns + ["hours"]].head(3)
        raise ApiError(
            ErrorCode.DUPLICATE_MEASUREMENT_IDENTITY,
            "The outcome file repeats the same component, measurement and hour.",
            details=[
                ErrorDetail(
                    code=ErrorCode.DUPLICATE_MEASUREMENT_IDENTITY,
                    message=(
                        f"{row.component_id} / {row.measurement_name} at "
                        f"{float(row.hours):g} h appears more than once."
                    ),
                    column="hours",
                )
                for row in sample.itertuples(index=False)
            ],
        )

    # 3. Every identity must exist in the early input.
    known = set(
        zip(
            early_frame["component_id"].astype(str),
            early_frame["batch_id"].astype(str),
            early_frame["component_family"].astype(str),
            early_frame["measurement_name"].astype(str),
        )
    )
    present = list(
        zip(
            frame["component_id"].astype(str),
            frame["batch_id"].astype(str),
            frame["component_family"].astype(str),
            frame["measurement_name"].astype(str),
        )
    )
    unknown = sorted({identity for identity in present if identity not in known})
    if unknown:
        raise ApiError(
            ErrorCode.AMBIGUOUS_COMPONENT_IDENTITY,
            f"The outcome file refers to {len(unknown)} component/measurement "
            "identities that are not in the early file. Outcomes are matched on "
            "component_id, batch_id, component_family and measurement_name; "
            "check that the two files describe the same run.",
            details=[
                ErrorDetail(
                    code=ErrorCode.AMBIGUOUS_COMPONENT_IDENTITY,
                    message=(
                        f"'{component_id}' / '{measurement}' in batch '{batch}' "
                        f"(family '{family}') has no early history."
                    ),
                    column="component_id",
                    value=component_id,
                )
                for component_id, batch, family, measurement in unknown[:20]
            ],
        )

    # 4. Declared units must match the artifact. Never converted.
    if "measurement_unit" in frame.columns:
        units = {u for u in frame["measurement_unit"].astype(str) if u.strip()}
        allowed = {engine.identity.unit.casefold(), "ua", "µa", "μa"}
        bad = sorted({u for u in units if u.casefold() not in allowed})
        if bad:
            raise ApiError(
                ErrorCode.INCOMPATIBLE_UNITS,
                f"The outcome file declares unit(s) {bad}; this artifact requires "
                f"{engine.identity.unit}. The API does not convert units.",
                details=[
                    ErrorDetail(
                        code=ErrorCode.INCOMPATIBLE_UNITS,
                        message=f"Expected unit '{engine.identity.unit}'.",
                        column="measurement_unit",
                        value=bad[0],
                    )
                ],
            )

    covered = len({identity for identity in present})
    if covered < len(known):
        warnings.append(
            ResponseWarning(
                code="OUTCOME_COVERAGE_PARTIAL",
                message=(
                    f"The outcome file covers {covered} of {len(known)} uploaded "
                    "histories. The rest have no revealed outcome; that is not the "
                    "same as having stayed within limit."
                ),
                count=len(known) - covered,
            )
        )

    return frame, warnings


def run_mlcc_screening(
    dataset: IngestedDataset,
    *,
    engine: MlccEngine,
    settings: Settings,
    as_of_hour: float,
    forecast_model: str | None,
    request_id: str,
    input_source: str,
    filename: str | None,
    outcome_dataset: IngestedDataset | None = None,
    outcome_filename: str | None = None,
) -> ScreenResponse:
    started = time.perf_counter()
    identity = engine.identity

    if abs(as_of_hour - identity.as_of_hour) > 1e-9:
        raise ApiError(
            ErrorCode.UNSUPPORTED_AS_OF_HOUR,
            f"This bundle supports as_of_hour={identity.as_of_hour:g} only; received {as_of_hour:g}.",
        )
    if forecast_model is not None and not engine.supports_model(forecast_model):
        raise ApiError(
            ErrorCode.UNSUPPORTED_PROFILE,
            f"Unknown forecast model '{forecast_model}'. This bundle provides: "
            + ", ".join(identity.available_models),
        )

    warnings = [ResponseWarning(code=w.code, message=w.message, count=w.count) for w in dataset.warnings]
    warnings.extend(preflight(dataset, engine))

    early, future = split_early_and_future(
        dataset.frame, checkpoint_hours=(0.0, identity.as_of_hour), as_of_hour=as_of_hour
    )
    if early.empty:
        raise ApiError(
            ErrorCode.NO_ELIGIBLE_HISTORIES,
            f"No readings were found at the required checkpoints (0 h and {identity.as_of_hour:g} h).",
        )

    # Post-cutoff observations can arrive two ways: as extra rows in the main
    # file, or as a separate outcome file. Both are evaluation-only and are
    # combined into one envelope. Neither is an inference input, and neither
    # contributes a specification limit.
    outcome_sources = [future] if not future.empty else []
    if outcome_dataset is not None:
        validated, outcome_warnings = validate_outcomes(
            outcome_dataset, dataset.frame, engine, as_of_hour
        )
        warnings.extend(outcome_warnings)
        outcome_sources.append(validated)

    if len(outcome_sources) == 2:
        combined_check = pd.concat(
            [source[list(HISTORY_KEY) + ["hours"]] for source in outcome_sources],
            ignore_index=True,
        )
        if combined_check.duplicated().any():
            raise ApiError(
                ErrorCode.DUPLICATE_MEASUREMENT_IDENTITY,
                "The same post-cutoff observation appears in both the main file "
                "and the outcome file. Supply each later reading once.",
                details=[
                    ErrorDetail(
                        code=ErrorCode.DUPLICATE_MEASUREMENT_IDENTITY,
                        message="Reported across the two files; no single row is implicated.",
                    )
                ],
            )

    outcomes_frame = (
        pd.concat(outcome_sources, ignore_index=True) if outcome_sources else None
    )

    try:
        result = engine.screen(
            early,
            as_of_hour=as_of_hour,
            forecast_model=forecast_model,
            future_outcomes=outcomes_frame,
        )
    except ValueError as exc:
        # The core rejects a dataset-level problem. It reports no row number, so
        # none is invented here.
        raise ApiError(
            ErrorCode.NO_ELIGIBLE_HISTORIES,
            f"The screening core rejected this file: {exc}",
            details=[
                ErrorDetail(
                    code=ErrorCode.NO_ELIGIBLE_HISTORIES,
                    message="Reported by the core for the dataset as a whole; no single row is implicated.",
                )
            ],
        ) from exc

    core_meta = result.get("metadata", {})
    records: list[ScreeningRecord] = []
    unscored: list[UnscoredRecord] = []

    for core_record in result.get("records", []):
        if core_record.get("status") == "scored":
            records.append(_build_record(core_record, dataset.provenance, identity.unit))
            continue
        # The core puts an unscored record's explanation in
        # recommendation_reasons; reason_codes is empty for those.
        reasons = [
            str(r)
            for r in (
                core_record.get("recommendation_reasons")
                or core_record.get("reason_codes")
                or []
            )
        ]
        unscored.append(
            UnscoredRecord(
                component_id=str(core_record["component_id"]),
                batch_id=str(core_record["batch_id"]),
                component_family=str(core_record["component_family"]),
                measurement_name=str(core_record["measurement_name"]),
                reason=_unscored_reason(reasons),
                message=" ".join(reasons) or "The core could not score this history.",
            )
        )

    counts = DecisionCounts()
    for record in records:
        setattr(counts, record.recommendation.value, getattr(counts, record.recommendation.value) + 1)

    records.sort(
        key=lambda r: (-RECOMMENDATION_URGENCY[r.recommendation], r.component_id, r.measurement_name)
    )

    if unscored:
        warnings.append(
            ResponseWarning(
                code="UNSCORED_RECORDS_PRESENT",
                message=(
                    "Some histories could not be screened and are listed in "
                    "unscored_records. They have not passed; they were not assessed. "
                    "decision_counts covers scored records only."
                ),
                count=len(unscored),
            )
        )

    selection_warning = core_meta.get("selection_warning")
    if selection_warning:
        warnings.append(
            ResponseWarning(
                code="FORECAST_MODEL_NOT_VALIDATION_WINNER",
                message=(
                    f"Forecasts came from '{core_meta.get('selected_model')}', which is not "
                    f"the internal validation winner ('{core_meta.get('validation_winner')}'). "
                    f"{selection_warning}. This is not evidence that the selected model is better."
                ),
            )
        )

    if identity.training_data == "synthetic":
        warnings.append(
            ResponseWarning(
                code="SYNTHETIC_TRAINING_DATA",
                message=(
                    "These models were trained on synthetic MLCC data. Results "
                    "demonstrate the pipeline and are not validated hardware screening."
                ),
            )
        )
    if dataset.provenance is DataProvenance.SYNTHETIC:
        warnings.append(
            ResponseWarning(
                code="SYNTHETIC_DATA",
                message="The uploaded file is marked synthetic. This is not measured hardware data.",
            )
        )
    elif dataset.provenance is DataProvenance.UNKNOWN:
        warnings.append(
            ResponseWarning(
                code="UNKNOWN_PROVENANCE",
                message=(
                    "The file declares no data_source, so its provenance is unknown. "
                    "Unknown is not the same as verified measured data."
                ),
            )
        )

    extrapolating = sum(1 for r in records if r.forecast.out_of_training_range_features)
    if extrapolating:
        warnings.append(
            ResponseWarning(
                code="FORECAST_EXTRAPOLATES",
                message=(
                    "Some components have inputs beyond the ranges seen in training. "
                    "Their forecasts extrapolate and the interval coverage does not transfer."
                ),
                count=extrapolating,
            )
        )

    model_info = ModelInfo(
        prototype_version=core_meta.get("prototype_version"),
        bundle_id=core_meta.get("bundle_id"),
        selected_model=core_meta.get("selected_model"),
        validation_winner=core_meta.get("validation_winner"),
        forecast_selection=core_meta.get("forecast_selection"),
        selection_warning=selection_warning,
        model_training_data=core_meta.get("model_training_data"),
        model_fitted_during_request=core_meta.get("model_fitted_during_request"),
        supported_family=core_meta.get("supported_family"),
        supported_measurement=core_meta.get("supported_measurement"),
        available_models=list(identity.available_models),
        limitations=list(engine.manifest.get("limitations", [])),
    )

    # Limits come from the uploaded histories, not from the outcome rows, which
    # carry only the later reading.
    evaluation = _evaluation(
        result,
        identity.target_hour,
        limits_by_identity(dataset.frame),
        source_filename=outcome_filename,
    )

    capabilities = CapabilityFlags(
        anomaly=True,
        forecast=bool(records),
        intervals=any(r.forecast.prediction_lower is not None for r in records),
        explanations=any(r.forecast.xgboost_explanation is not None for r in records),
        peer_statistics=any(r.peers.sufficient for r in records),
        mode=settings.mode.value,
        limitations=list(engine.manifest.get("limitations", [])),
    )

    duration_ms = (time.perf_counter() - started) * 1000.0

    return ScreenResponse(
        schema_version=SCHEMA_VERSION,
        request_id=request_id,
        generated_at=datetime.now(timezone.utc),
        duration_ms=round(duration_ms, 3),
        input_source=input_source,
        filename=filename,
        profile_id=f"{identity.family.lower()}_{identity.measurement}",
        as_of_hour=as_of_hour,
        target_hour=identity.target_hour,
        checkpoint_hours_used=[0.0, identity.as_of_hour],
        model_versions={
            "anomaly": identity.prototype_version,
            "forecast": core_meta.get("selected_model"),
            "bundle": identity.bundle_id,
        },
        model_info=model_info,
        batch_count=dataset.batch_count,
        unique_component_count=dataset.unique_component_count,
        measurement_record_count=dataset.measurement_record_count,
        scored_record_count=len(records),
        unscored_record_count=len(unscored),
        decision_counts=counts,
        capabilities=capabilities,
        provenance=dataset.provenance,
        records=records,
        unscored_records=unscored,
        component_summaries=_summaries(records, unscored),
        evaluation=evaluation,
        warnings=warnings,
    )
