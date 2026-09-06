"""Screening orchestration: ingested dataframe in, typed response out.

Order of operations, and why:

  1. profile resolution      - an unknown family/measurement can never be scored
  2. peer-group compatibility - incompatible specs must not become each other's peers
  3. checkpoint isolation     - exactly 0 h and 24 h reach the model
  4. eligibility              - histories missing a checkpoint become explicit unscored records
  5. capability gate          - a missing model is a 503, never a fabricated number
  6. features -> score -> predict -> combine, joined on the FULL identity
  7. presentation evidence, summaries, evaluation-only outcomes

Post-cutoff observations are separated in step 3 and are read again only in
step 7, into the evaluation section. They never touch features, scores,
predictions, peer statistics or explanations.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterable

import numpy as np
import pandas as pd

from sih26170.api import core_bridge
from sih26170.api.config import Settings
from sih26170.api.errors import ApiError, ErrorCode, ErrorDetail, unavailable
from sih26170.api.ingestion import (
    HISTORY_KEY,
    IngestedDataset,
    split_early_and_future,
)
from sih26170.api.profiles import (
    DataProvenance,
    LimitDirection,
    Profile,
    ProfileStatus,
    find_profile,
)
from sih26170.api.schemas import (
    RECOMMENDATION_URGENCY,
    AnomalyEvidence,
    CapabilityFlags,
    CapabilityStatus,
    ComponentSummary,
    DecisionCounts,
    EvaluationSection,
    FeatureContribution,
    ForecastEvidence,
    LimitInfo,
    OutcomeRecord,
    PeerStatistics,
    Recommendation,
    ResponseWarning,
    ScreenResponse,
    ScreeningRecord,
    TrajectoryPoint,
    UnscoredRecord,
    UnscoredReason,
)
from sih26170.prediction.base import AnomalyOutput, FeatureAttribution, ForecastOutput
from sih26170.prediction.registry import ModelRegistry

Identity = tuple[str, str, str, str]


@dataclass
class ScreeningContext:
    settings: Settings
    registry: ModelRegistry
    as_of_hour: float
    input_source: str
    filename: str | None
    request_id: str


# --------------------------------------------------------------------------
# Provisional decision policy (API layer, clearly separated from core logic)
# --------------------------------------------------------------------------


def provisional_recommendation(
    anomaly: AnomalyOutput, headroom_fraction: float | None
) -> Recommendation:
    """Anomaly-only recommendation used when no forecast is available.

    This is an API-layer fallback, NOT the core's combined decision logic, and
    every record produced through it is flagged ``provisional`` with
    ``recommendation_basis='anomaly_only'``. It is deliberately conservative:
    it never returns ACCEPT for a flagged part, and it never claims the
    stronger RETEST/ENGINEER_REVIEW outcomes that depend on a forecast crossing
    a limit.

    It does not modify, reorder or reinterpret core decision semantics; when a
    forecast is available the core's build_screening_record() decides instead.
    """
    if not anomaly.is_anomaly:
        return Recommendation.ACCEPT
    if headroom_fraction is not None and headroom_fraction <= 0.1:
        return Recommendation.ENGINEER_REVIEW
    return Recommendation.MONITOR


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


def _identity_of(row: pd.Series) -> Identity:
    return (
        str(row["component_id"]),
        str(row["batch_id"]),
        str(row["component_family"]),
        str(row["measurement_name"]),
    )


#: Optional columns carried into the response for presentation only. None of
#: these ever reach feature building.
PRESENTATION_METADATA: tuple[str, ...] = (
    "measurement_unit",
    "part_number",
    "test_condition",
    "board_position",
    "data_source",
)
NUMERIC_METADATA: tuple[str, ...] = (
    "temperature_c",
    "humidity_pct",
    "applied_voltage_v",
)


@dataclass
class HistoryData:
    """One measurement history as plain Python values.

    Built in a single pass over the early frame. The per-record path below then
    does no pandas work at all: doing a handful of dataframe operations per
    record made a 10 000-component upload take tens of seconds.
    """

    identity: Identity
    hours: list[float] = field(default_factory=list)
    values: list[float] = field(default_factory=list)
    upper_limit: float | None = None
    lower_limit: float | None = None
    metadata: dict[str, float | str | None] = field(default_factory=dict)

    def value_at(self, hour: float) -> float | None:
        for index, candidate in enumerate(self.hours):
            if abs(candidate - hour) < 1e-9:
                return self.values[index]
        return None

    def meta(self, column: str) -> float | str | None:
        return self.metadata.get(column)


def prepare_histories(early: pd.DataFrame) -> dict[Identity, HistoryData]:
    """Group the early frame into plain per-history records in one pass."""
    text_columns = [c for c in PRESENTATION_METADATA if c in early.columns]
    numeric_columns = [c for c in NUMERIC_METADATA if c in early.columns]
    has_lower = "lower_limit" in early.columns

    histories: dict[Identity, HistoryData] = {}
    ordered = early.sort_values("hours", kind="stable")

    for row in ordered.itertuples(index=False):
        identity: Identity = (
            str(row.component_id),
            str(row.batch_id),
            str(row.component_family),
            str(row.measurement_name),
        )
        history = histories.get(identity)
        if history is None:
            history = HistoryData(identity=identity)
            histories[identity] = history

        history.hours.append(float(row.hours))
        history.values.append(float(row.measurement_value))

        if history.upper_limit is None:
            upper = float(row.upper_limit)
            if np.isfinite(upper):
                history.upper_limit = upper
        if has_lower and history.lower_limit is None:
            lower = float(getattr(row, "lower_limit", np.nan))
            if np.isfinite(lower):
                history.lower_limit = lower

        for column in text_columns:
            text = str(getattr(row, column, "") or "").strip()
            if text:
                history.metadata[column] = text
        for column in numeric_columns:
            number = getattr(row, column, np.nan)
            if number is not None and np.isfinite(number):
                history.metadata[column] = float(number)

    return histories


def _peer_group_key(row: pd.Series) -> tuple[str, str, str]:
    return (str(row["batch_id"]), str(row["component_family"]), str(row["measurement_name"]))


# --------------------------------------------------------------------------
# Compatibility
# --------------------------------------------------------------------------


def check_peer_group_compatibility(early: pd.DataFrame) -> None:
    """Reject uploads where one peer group mixes incompatible specifications.

    The core compares peers by batch, family and measurement. If two parts in
    that group carry different units, test conditions or specification limits,
    they are not comparable and their batch-relative statistics would be
    meaningless, so the upload is rejected before the core is called.
    """
    details: list[ErrorDetail] = []

    for key, block in early.groupby(
        ["batch_id", "component_family", "measurement_name"], sort=False
    ):
        batch_id, family, measurement = key
        label = f"batch '{batch_id}', family '{family}', measurement '{measurement}'"

        if "measurement_unit" in block.columns:
            units = {u for u in block["measurement_unit"].astype(str) if u.strip()}
            if len(units) > 1:
                details.append(
                    ErrorDetail(
                        code=ErrorCode.INCOMPATIBLE_UNITS,
                        message=(
                            f"Peer group {label} mixes measurement units "
                            f"({', '.join(sorted(units))}). Peers must share one unit."
                        ),
                        column="measurement_unit",
                    )
                )

        if "test_condition" in block.columns:
            conditions = {c for c in block["test_condition"].astype(str) if c.strip()}
            if len(conditions) > 1:
                details.append(
                    ErrorDetail(
                        code=ErrorCode.INCOMPATIBLE_TEST_CONDITIONS,
                        message=(
                            f"Peer group {label} mixes test conditions "
                            f"({', '.join(sorted(conditions))}). Parts screened under "
                            "different conditions are not comparable peers."
                        ),
                        column="test_condition",
                    )
                )

        for limit_column in ("upper_limit", "lower_limit"):
            if limit_column not in block.columns:
                continue
            limits = {float(v) for v in block[limit_column].dropna()}
            if len(limits) > 1:
                details.append(
                    ErrorDetail(
                        code=ErrorCode.INCOMPATIBLE_TEST_CONDITIONS,
                        message=(
                            f"Peer group {label} mixes '{limit_column}' values "
                            f"({', '.join(str(v) for v in sorted(limits))}). Different "
                            "specification limits indicate different part specifications, "
                            "which cannot share a peer group."
                        ),
                        column=limit_column,
                    )
                )

    if details:
        raise ApiError(
            details[0].code,
            "The upload mixes incompatible specifications inside one peer group.",
            details=details[:50],
        )


def check_profile_unit(declared_unit: str, profile: Profile) -> list[ErrorDetail]:
    """Ensure a declared unit matches the profile's unit.

    Units are compared, never converted: silently rescaling a measurement is a
    far worse failure than refusing the file.
    """
    if profile.unit_matches(declared_unit):
        return []
    return [
        ErrorDetail(
            code=ErrorCode.INCOMPATIBLE_UNITS,
            message=(
                f"Profile '{profile.profile_id}' expects unit "
                f"'{profile.measurement_unit}' but the file declares "
                f"'{declared_unit}'. The API does not convert units."
            ),
            column="measurement_unit",
            value=declared_unit,
        )
    ]


# --------------------------------------------------------------------------
# Peer statistics
# --------------------------------------------------------------------------


def compute_peer_statistics(
    early: pd.DataFrame, as_of_hour: float, min_group_size: int
) -> dict[tuple[str, str, str], PeerStatistics]:
    """Batch-relative statistics of the cutoff-hour value, per peer group."""
    stats: dict[tuple[str, str, str], PeerStatistics] = {}
    cutoff = early.loc[(early["hours"] - as_of_hour).abs() < 1e-9]

    for key, block in cutoff.groupby(
        ["batch_id", "component_family", "measurement_name"], sort=False
    ):
        values = block["measurement_value"].to_numpy(dtype=float)
        size = int(len(values))
        sufficient = size >= min_group_size
        if size == 0:
            stats[key] = PeerStatistics(
                sample_size=0,
                sufficient=False,
                status=CapabilityStatus.INSUFFICIENT_DATA,
                note="No readings at the cutoff hour for this peer group.",
            )
            continue

        median = float(np.median(values))
        mad = float(np.median(np.abs(values - median)))
        stats[key] = PeerStatistics(
            sample_size=size,
            sufficient=sufficient,
            status=(
                CapabilityStatus.AVAILABLE if sufficient else CapabilityStatus.INSUFFICIENT_DATA
            ),
            median=median,
            mad=mad,
            peer_min=float(np.min(values)),
            peer_max=float(np.max(values)),
            note=(
                None
                if sufficient
                else (
                    f"Only {size} comparable peers were available; at least "
                    f"{min_group_size} are required before batch-relative statistics "
                    "are treated as reliable. Values are shown for context only."
                )
            ),
        )
    return stats


# --------------------------------------------------------------------------
# Limits
# --------------------------------------------------------------------------


def build_limit_info(
    history: HistoryData, profile: Profile, latest: float | None
) -> LimitInfo:
    upper = history.upper_limit
    lower = history.lower_limit

    if profile.limit_direction is LimitDirection.UPPER:
        applicable = upper
        headroom = (applicable - latest) if (applicable is not None and latest is not None) else None
    elif profile.limit_direction is LimitDirection.LOWER:
        applicable = lower
        headroom = (latest - applicable) if (applicable is not None and latest is not None) else None
    else:
        applicable = upper
        headroom = (applicable - latest) if (applicable is not None and latest is not None) else None

    fraction: float | None = None
    if headroom is not None and applicable not in (None, 0.0):
        fraction = headroom / abs(applicable)

    return LimitInfo(
        direction=profile.limit_direction,
        upper_limit=upper,
        lower_limit=lower,
        applicable_limit=applicable,
        headroom=headroom,
        headroom_fraction=fraction,
    )


# --------------------------------------------------------------------------
# Main entry point
# --------------------------------------------------------------------------


def run_screening(dataset: IngestedDataset, ctx: ScreeningContext) -> ScreenResponse:
    started = time.perf_counter()
    settings = ctx.settings
    registry = ctx.registry
    frame = dataset.frame

    checkpoints = tuple(settings.required_checkpoint_hours)
    if abs(ctx.as_of_hour - settings.default_as_of_hour) > 1e-9:
        raise ApiError(
            ErrorCode.UNSUPPORTED_AS_OF_HOUR,
            f"Only as_of_hour={settings.default_as_of_hour:g} is validated for this "
            f"pilot (checkpoints {', '.join(f'{h:g}' for h in checkpoints)} h). "
            f"Received {ctx.as_of_hour:g}.",
        )

    early, future = split_early_and_future(
        frame, checkpoint_hours=checkpoints, as_of_hour=ctx.as_of_hour
    )

    warnings: list[ResponseWarning] = [
        ResponseWarning(code=w.code, message=w.message, count=w.count) for w in dataset.warnings
    ]

    dropped = len(frame) - len(early) - len(future)
    if dropped > 0:
        warnings.append(
            ResponseWarning(
                code="NON_CHECKPOINT_READINGS_IGNORED",
                message=(
                    "Readings at hours other than the profile checkpoints "
                    f"({', '.join(f'{h:g}' for h in checkpoints)} h) were excluded from "
                    "feature building so the 0/24 h basis is exact."
                ),
                count=int(dropped),
            )
        )

    if early.empty:
        raise ApiError(
            ErrorCode.NO_ELIGIBLE_HISTORIES,
            "No readings were found at the required checkpoint hours "
            f"({', '.join(f'{h:g}' for h in checkpoints)} h).",
        )

    check_peer_group_compatibility(early)

    # --- resolve profiles and eligibility -------------------------------
    unscored: list[UnscoredRecord] = []
    eligible: dict[Identity, HistoryData] = {}
    profiles_by_identity: dict[Identity, Profile] = {}
    unit_errors: list[ErrorDetail] = []
    seen_profiles: dict[str, Profile] = {}

    # Group the early frame once. Looking each history up by key keeps this
    # loop linear; filtering the whole early frame per history made a
    # 10 000-component upload take over a minute.
    histories = prepare_histories(early)

    for key, block in frame.groupby(list(HISTORY_KEY), sort=False):
        identity: Identity = tuple(str(part) for part in key)  # type: ignore[assignment]
        component_id, batch_id, family, measurement = identity
        available_hours = sorted(float(h) for h in block["hours"].unique())

        profile = find_profile(family, measurement)
        if profile is None:
            unscored.append(
                UnscoredRecord(
                    component_id=component_id,
                    batch_id=batch_id,
                    component_family=family,
                    measurement_name=measurement,
                    reason=UnscoredReason.UNSUPPORTED_PROFILE,
                    message=(
                        f"No screening profile is defined for family '{family}' with "
                        f"measurement '{measurement}'. See GET /api/v1/profiles."
                    ),
                    available_hours=available_hours,
                )
            )
            continue

        if profile.status is not ProfileStatus.SUPPORTED:
            unscored.append(
                UnscoredRecord(
                    component_id=component_id,
                    batch_id=batch_id,
                    component_family=family,
                    measurement_name=measurement,
                    reason=UnscoredReason.PROFILE_NOT_AVAILABLE,
                    message=(
                        f"Profile '{profile.profile_id}' is declared but not yet "
                        f"available: {profile.description}"
                    ),
                    available_hours=available_hours,
                )
            )
            continue

        history = histories.get(identity)
        present = (
            {round(hour, 6) for hour in history.hours} if history is not None else set()
        )
        missing = [h for h in checkpoints if round(float(h), 6) not in present]
        if missing:
            unscored.append(
                UnscoredRecord(
                    component_id=component_id,
                    batch_id=batch_id,
                    component_family=family,
                    measurement_name=measurement,
                    reason=UnscoredReason.MISSING_CHECKPOINT,
                    message=(
                        "This history is missing required checkpoint readings at "
                        + ", ".join(f"{h:g} h" for h in missing)
                        + ". The 0/24 h screening mode needs both checkpoints."
                    ),
                    available_hours=available_hours,
                    missing_checkpoint_hours=[float(h) for h in missing],
                )
            )
            continue

        seen_profiles.setdefault(profile.profile_id, profile)
        assert history is not None  # a missing history has no checkpoints
        declared_unit = history.meta("measurement_unit")
        if declared_unit is not None:
            unit_errors.extend(check_profile_unit(str(declared_unit), profile))
        eligible[identity] = history
        profiles_by_identity[identity] = profile

    if unit_errors:
        raise ApiError(
            ErrorCode.INCOMPATIBLE_UNITS,
            "The declared measurement unit does not match the screening profile.",
            details=unit_errors[:50],
        )

    measurement_record_count = dataset.measurement_record_count

    if not eligible:
        raise ApiError(
            ErrorCode.NO_ELIGIBLE_HISTORIES,
            "No component history in this file could be screened. "
            f"{len(unscored)} of {measurement_record_count} histories were rejected; "
            "see 'details' for the specific reasons.",
            details=[
                ErrorDetail(
                    code=ErrorCode.NO_ELIGIBLE_HISTORIES,
                    message=f"{record.component_id} / {record.measurement_name}: {record.message}",
                )
                for record in unscored[:50]
            ],
        )

    # --- capability gate -------------------------------------------------
    anomaly_adapter = registry.anomaly_adapter
    if anomaly_adapter is None:
        raise unavailable(
            ErrorCode.ANOMALY_MODEL_UNAVAILABLE,
            registry.anomaly_state.reason
            or "The anomaly detector is not loaded, so no screening can be performed.",
        )

    # --- features -> score ----------------------------------------------
    # The core feature builder consumes the original long-format rows, so the
    # eligible slice is taken from `early` with a single vectorised mask.
    eligible_mask = [
        (component_id, batch_id, family, measurement) in eligible
        for component_id, batch_id, family, measurement in zip(
            early["component_id"],
            early["batch_id"],
            early["component_family"],
            early["measurement_name"],
        )
    ]
    eligible_early = early.loc[eligible_mask]
    features = core_bridge.build_component_features(eligible_early, as_of_hour=ctx.as_of_hour)
    anomaly_outputs = anomaly_adapter.score(features)
    anomalies: dict[Identity, AnomalyOutput] = {a.identity: a for a in anomaly_outputs}

    # The core may drop histories with too few early readings. Anything that
    # went in but did not come back is reported explicitly, never silently.
    for identity in list(eligible):
        if identity not in anomalies:
            component_id, batch_id, family, measurement = identity
            unscored.append(
                UnscoredRecord(
                    component_id=component_id,
                    batch_id=batch_id,
                    component_family=family,
                    measurement_name=measurement,
                    reason=UnscoredReason.TOO_FEW_EARLY_READINGS,
                    message=(
                        "The shared feature builder returned no features for this "
                        "history, so it could not be scored."
                    ),
                    available_hours=sorted(eligible[identity].hours),
                )
            )
            del eligible[identity]

    # --- forecast --------------------------------------------------------
    forecasts: dict[Identity, ForecastOutput] = {}
    forecast_unavailable_reason: dict[str, str] = {}
    for profile_id, profile in seen_profiles.items():
        adapter = registry.forecast_adapter_for(profile_id)
        if adapter is None:
            forecast_unavailable_reason[profile_id] = (
                registry.forecast_state.reason
                or f"No forecast artifact covers profile '{profile_id}'."
            )
            continue
        subset = [i for i, p in profiles_by_identity.items() if p.profile_id == profile_id and i in eligible]
        if not subset:
            continue
        subset_features = _select_features(features, subset)
        for output in adapter.predict(subset_features):
            forecasts[output.identity] = output

    # --- peer statistics -------------------------------------------------
    peer_stats = compute_peer_statistics(
        early, ctx.as_of_hour, settings.min_peer_group_size
    )

    # --- build records ---------------------------------------------------
    records: list[ScreeningRecord] = []
    counts = DecisionCounts()

    for identity, history in eligible.items():
        profile = profiles_by_identity[identity]
        anomaly = anomalies[identity]
        forecast = forecasts.get(identity)
        record = _build_record(
            identity=identity,
            history=history,
            profile=profile,
            anomaly=anomaly,
            forecast=forecast,
            peer_stats=peer_stats,
            provenance=dataset.provenance,
            as_of_hour=ctx.as_of_hour,
            forecast_reason=forecast_unavailable_reason.get(profile.profile_id),
        )
        records.append(record)
        setattr(counts, record.recommendation.value, getattr(counts, record.recommendation.value) + 1)

    records.sort(
        key=lambda r: (-RECOMMENDATION_URGENCY[r.recommendation], r.component_id, r.measurement_name)
    )

    summaries = _build_summaries(records, unscored)

    if any(r.provisional for r in records):
        warnings.append(
            ResponseWarning(
                code="PROVISIONAL_RECOMMENDATIONS",
                message=(
                    "Some recommendations were made without a 168 h forecast and are "
                    "marked provisional. They rest on early-window anomaly evidence alone."
                ),
                count=sum(1 for r in records if r.provisional),
            )
        )

    if dataset.provenance in (DataProvenance.SYNTHETIC, DataProvenance.MIXED):
        warnings.append(
            ResponseWarning(
                code="SYNTHETIC_DATA",
                message=(
                    "This file is marked as synthetic or partly synthetic. Results "
                    "demonstrate the pipeline; they are not measured hardware validation."
                ),
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

    evaluation = _build_evaluation(future, eligible, profiles_by_identity, settings.default_target_hour)

    limitations = registry.is_ready()[1]
    capabilities = CapabilityFlags(
        anomaly=True,
        forecast=bool(forecasts),
        intervals=any(f.lower is not None and f.upper is not None for f in forecasts.values()),
        explanations=any(f.attributions for f in forecasts.values())
        or any(a.attributions for a in anomalies.values()),
        peer_statistics=any(s.sufficient for s in peer_stats.values()),
        mode=settings.mode.value,
        limitations=limitations,
    )

    duration_ms = (time.perf_counter() - started) * 1000.0

    return ScreenResponse(
        schema_version=_schema_version(),
        request_id=ctx.request_id,
        generated_at=datetime.now(timezone.utc),
        duration_ms=round(duration_ms, 3),
        input_source=ctx.input_source,
        filename=ctx.filename,
        profile_id=next(iter(seen_profiles), None) if len(seen_profiles) == 1 else None,
        as_of_hour=ctx.as_of_hour,
        target_hour=settings.default_target_hour,
        checkpoint_hours_used=[float(h) for h in checkpoints],
        model_versions=registry.model_versions,
        batch_count=dataset.batch_count,
        unique_component_count=dataset.unique_component_count,
        measurement_record_count=measurement_record_count,
        scored_record_count=len(records),
        unscored_record_count=len(unscored),
        decision_counts=counts,
        capabilities=capabilities,
        provenance=dataset.provenance,
        records=records,
        unscored_records=unscored,
        component_summaries=summaries,
        evaluation=evaluation,
        warnings=warnings,
    )


def _schema_version() -> str:
    from sih26170.api.config import SCHEMA_VERSION

    return SCHEMA_VERSION


def _select_features(features: pd.DataFrame, identities: Iterable[Identity]) -> pd.DataFrame:
    """Restrict a feature frame to the given identities, joining on all four keys."""
    wanted = set(identities)
    mask = [
        (
            str(row.component_id),
            str(row.batch_id),
            str(row.component_family),
            str(row.measurement_name),
        )
        in wanted
        for row in features.itertuples()
    ]
    return features.loc[mask]


def _attributions(items: Iterable[FeatureAttribution]) -> list[FeatureContribution]:
    return [
        FeatureContribution(
            feature=a.feature, contribution=a.contribution, direction=a.direction
        )
        for a in items
    ]


def _build_record(
    *,
    identity: Identity,
    history: HistoryData,
    profile: Profile,
    anomaly: AnomalyOutput,
    forecast: ForecastOutput | None,
    peer_stats: dict[tuple[str, str, str], PeerStatistics],
    provenance: DataProvenance,
    as_of_hour: float,
    forecast_reason: str | None,
) -> ScreeningRecord:
    component_id, batch_id, family, measurement = identity

    initial = history.value_at(0.0)
    latest = history.value_at(as_of_hour)

    absolute_change = (latest - initial) if (initial is not None and latest is not None) else None

    percent_change: float | None = None
    percent_available = False
    if initial is not None and latest is not None and initial != 0.0:
        percent_change = (latest - initial) / initial
        percent_available = True

    slope: float | None = None
    if absolute_change is not None and as_of_hour > 0:
        slope = absolute_change / as_of_hour

    limits = build_limit_info(history, profile, latest)

    peers = peer_stats.get(
        (batch_id, family, measurement),
        PeerStatistics(
            sample_size=0,
            sufficient=False,
            status=CapabilityStatus.INSUFFICIENT_DATA,
            note="No comparable peer group was found for this measurement.",
        ),
    )

    anomaly_evidence = AnomalyEvidence(
        status=CapabilityStatus.AVAILABLE,
        score=anomaly.score,
        is_anomaly=anomaly.is_anomaly,
        method=anomaly.method,
        contributing_features=_attributions(anomaly.attributions),
        note=(
            "Relative deviation against comparable peers in the same batch. "
            "This score is not a probability of physical failure."
        ),
    )

    if forecast is not None:
        has_interval = forecast.lower is not None and forecast.upper is not None
        crosses: bool | None = None
        if limits.applicable_limit is not None:
            if profile.limit_direction is LimitDirection.LOWER:
                crosses = forecast.predicted_final_value < limits.applicable_limit
            else:
                crosses = forecast.predicted_final_value > limits.applicable_limit

        forecast_evidence = ForecastEvidence(
            status=CapabilityStatus.AVAILABLE,
            predicted_final_value=forecast.predicted_final_value,
            prediction_lower=forecast.lower,
            prediction_upper=forecast.upper,
            target_hour=forecast.target_hour,
            interval_nominal_coverage=forecast.interval_nominal_coverage,
            interval_method=forecast.interval_method,
            predicted_to_cross_limit=crosses,
            explanation=_attributions(forecast.attributions),
            note=(
                None
                if has_interval
                else (
                    "No calibrated prediction interval is available for this "
                    "artifact, so the bounds are null rather than estimated."
                )
            ),
        )
    else:
        forecast_evidence = ForecastEvidence(
            status=CapabilityStatus.UNAVAILABLE,
            target_hour=None,
            note=forecast_reason or "No forecast model is available for this profile.",
        )

    if forecast is not None:
        prediction_result = core_bridge.make_prediction_result(
            predicted_final_value=forecast.predicted_final_value,
            prediction_lower=forecast.lower,
            prediction_upper=forecast.upper,
            target_hour=forecast.target_hour,
        )
        core_record = core_bridge.build_screening_record(anomaly.raw, prediction_result)
        recommendation = Recommendation(core_bridge.adapt_screening_record(core_record))
        basis = "anomaly_and_forecast"
        provisional = False
    else:
        recommendation = provisional_recommendation(anomaly, limits.headroom_fraction)
        basis = "anomaly_only"
        provisional = True

    trajectory = [
        TrajectoryPoint(hour=hour, value=value)
        for hour, value in zip(history.hours, history.values)
    ]

    return ScreeningRecord(
        component_id=component_id,
        batch_id=batch_id,
        component_family=family,
        measurement_name=measurement,
        recommendation=recommendation,
        recommendation_basis=basis,
        provisional=provisional,
        anomaly=anomaly_evidence,
        forecast=forecast_evidence,
        limits=limits,
        peers=peers,
        measurement_unit=str(
            history.meta("measurement_unit") or profile.measurement_unit
        ),
        initial_value=initial,
        latest_value=latest,
        last_observation_hour=as_of_hour,
        absolute_change=absolute_change,
        percent_change=percent_change,
        percent_change_available=percent_available,
        slope_per_hour=slope,
        early_trajectory=trajectory,
        part_number=history.meta("part_number"),  # type: ignore[arg-type]
        test_condition=history.meta("test_condition"),  # type: ignore[arg-type]
        temperature_c=history.meta("temperature_c"),  # type: ignore[arg-type]
        humidity_pct=history.meta("humidity_pct"),  # type: ignore[arg-type]
        applied_voltage_v=history.meta("applied_voltage_v"),  # type: ignore[arg-type]
        board_position=history.meta("board_position"),  # type: ignore[arg-type]
        data_source=history.meta("data_source"),  # type: ignore[arg-type]
        provenance=provenance,
    )


def _build_summaries(
    records: list[ScreeningRecord], unscored: list[UnscoredRecord]
) -> list[ComponentSummary]:
    """Aggregate per component: most urgent SCORED recommendation wins.

    A component with any unscored measurement is marked ``partial_coverage``
    so the UI cannot present it as fully passed.
    """
    buckets: dict[tuple[str, str, str], dict] = {}

    def bucket(component_id: str, batch_id: str, family: str) -> dict:
        key = (component_id, batch_id, family)
        if key not in buckets:
            buckets[key] = {
                "scored": [],
                "unscored": [],
                "measurements": [],
            }
        return buckets[key]

    for record in records:
        entry = bucket(record.component_id, record.batch_id, record.component_family)
        entry["scored"].append(record.recommendation)
        entry["measurements"].append(record.measurement_name)

    for item in unscored:
        entry = bucket(item.component_id, item.batch_id, item.component_family)
        entry["unscored"].append(item.measurement_name)
        entry["measurements"].append(item.measurement_name)

    summaries: list[ComponentSummary] = []
    for (component_id, batch_id, family), entry in buckets.items():
        scored: list[Recommendation] = entry["scored"]
        summary = (
            max(scored, key=lambda r: RECOMMENDATION_URGENCY[r]) if scored else None
        )
        summaries.append(
            ComponentSummary(
                component_id=component_id,
                batch_id=batch_id,
                component_family=family,
                summary_recommendation=summary,
                scored_measurement_count=len(scored),
                unscored_measurement_count=len(entry["unscored"]),
                partial_coverage=bool(entry["unscored"]),
                measurement_names=sorted(set(entry["measurements"])),
            )
        )

    summaries.sort(key=lambda s: (s.batch_id, s.component_id))
    return summaries


def _build_evaluation(
    future: pd.DataFrame,
    eligible: dict[Identity, HistoryData],
    profiles: dict[Identity, Profile],
    target_hour: float,
) -> EvaluationSection | None:
    """Outcome reveal data. Read only here, after every inference step."""
    if future.empty:
        return None

    outcomes: list[OutcomeRecord] = []
    for row in future.itertuples():
        identity: Identity = (
            str(row.component_id),
            str(row.batch_id),
            str(row.component_family),
            str(row.measurement_name),
        )
        if identity not in eligible:
            continue
        profile = profiles[identity]
        value = float(row.measurement_value)
        limit = float(row.upper_limit)

        # An unknown applicable limit leaves `crossed` null. It must never
        # default to False, which would read as "stayed within limit".
        applicable: float | None
        crossed: bool | None
        if profile.limit_direction is LimitDirection.LOWER:
            lower = getattr(row, "lower_limit", None)
            applicable = float(lower) if lower is not None else None
            crossed = None if applicable is None else value < applicable
        else:
            applicable = limit
            crossed = value > limit

        outcomes.append(
            OutcomeRecord(
                component_id=identity[0],
                batch_id=identity[1],
                component_family=identity[2],
                measurement_name=identity[3],
                observed_value=value,
                observed_hour=float(row.hours),
                applicable_limit=applicable,
                crossed_applicable_limit=crossed,
            )
        )

    if not outcomes:
        return None

    return EvaluationSection(
        available=True,
        target_hour=target_hour,
        note=(
            "Evaluation only. These post-cutoff observations were excluded from "
            "feature building, anomaly scoring, forecasting, peer statistics and "
            "explanations. They exist so a demonstration can reveal the outcome "
            "after the prediction has been shown."
        ),
        outcomes=outcomes,
    )
