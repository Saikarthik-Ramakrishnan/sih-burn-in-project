"""Pydantic v2 response models - the stable contract for the frontend.

Conventions the UI must rely on:

  * ``percent_change`` is a FRACTION. 0.1 means 10 %. Multiply by 100 to
    display. It is null when the initial value is zero (a percentage is
    genuinely undefined there) even though the model's internal feature uses
    an epsilon-guarded ratio.
  * Any field the upload did not supply stays null. Null never means zero.
  * A missing forecast is null forecast fields plus a ``status`` explaining
    why - never fabricated bounds.
  * The anomaly score is a relative deviation score, not a probability of
    physical failure.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from sih26170.api.profiles import DataProvenance, LimitDirection, ProfileStatus


class Recommendation(str, Enum):
    """Preserved verbatim from the core decision module."""

    ACCEPT = "ACCEPT"
    MONITOR = "MONITOR"
    RETEST = "RETEST"
    ENGINEER_REVIEW = "ENGINEER_REVIEW"


#: Urgency order used by the documented per-component summary aggregation.
#: Higher wins. This ordering lives in the API layer only; it does not change
#: core decision semantics.
RECOMMENDATION_URGENCY: dict[Recommendation, int] = {
    Recommendation.ACCEPT: 0,
    Recommendation.MONITOR: 1,
    Recommendation.RETEST: 2,
    Recommendation.ENGINEER_REVIEW: 3,
}


class CapabilityStatus(str, Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    INSUFFICIENT_DATA = "insufficient_data"
    NOT_SUPPORTED = "not_supported"


class UnscoredReason(str, Enum):
    MISSING_CHECKPOINT = "missing_checkpoint"
    TOO_FEW_EARLY_READINGS = "too_few_early_readings"
    UNSUPPORTED_PROFILE = "unsupported_profile"
    PROFILE_NOT_AVAILABLE = "profile_not_available"
    INSUFFICIENT_PEERS = "insufficient_peers"
    ANOMALY_MODEL_UNAVAILABLE = "anomaly_model_unavailable"
    CORE_ERROR = "core_error"


class Base(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


# --------------------------------------------------------------------------
# Health
# --------------------------------------------------------------------------


class ProbeCheck(Base):
    name: str
    passed: bool
    detail: str | None = None


class CapabilityReport(Base):
    name: str = Field(description="Capability identifier, e.g. 'anomaly' or 'forecast'.")
    available: bool
    reason: str | None = Field(
        default=None,
        description="Why the capability is unavailable. Null when available.",
    )
    artifact_id: str | None = None
    model_version: str | None = None
    checks: list[ProbeCheck] = Field(
        default_factory=list,
        description="Artifact presence, schema, checksum and inference-probe results.",
    )


class LivenessResponse(Base):
    status: str = "alive"
    service: str = "sih26170-backend"
    version: str
    schema_version: str
    timestamp: datetime


class ReadinessResponse(Base):
    ready: bool
    mode: str = Field(
        description="'demo' requires anomaly + forecast; 'anomaly_only' is a development mode."
    )
    service: str = "sih26170-backend"
    version: str
    schema_version: str
    timestamp: datetime
    capabilities: list[CapabilityReport]
    limitations: list[str] = Field(
        default_factory=list,
        description="Human-readable limitations of the current mode. Non-empty in anomaly_only mode.",
    )


# --------------------------------------------------------------------------
# Profiles
# --------------------------------------------------------------------------


class ProfileItem(Base):
    profile_id: str
    component_family: str
    measurement_name: str
    measurement_unit: str
    limit_direction: LimitDirection
    status: ProfileStatus = Field(
        description="'supported' means the profile definition is complete; it still needs artifacts to run."
    )
    required_checkpoint_hours: list[float]
    as_of_hour: float
    target_hour: float
    min_peer_group_size: int = Field(
        description="Below this many comparable peers, batch-relative statistics are reported as unavailable."
    )
    anomaly_available: bool
    forecast_available: bool
    usable: bool = Field(
        description="True only when status is 'supported' AND the required artifacts are loaded."
    )
    supported_part_profiles: list[str] = Field(
        default_factory=list,
        description=(
            "Part/test profile ids the loaded artifact was trained on. When "
            "non-empty, each uploaded row must carry a profile_id from this list "
            "or its history is reported unscored."
        ),
    )
    description: str
    provenance_note: str | None = None
    unavailable_reason: str | None = None


class ProfilesResponse(Base):
    schema_version: str
    mode: str
    profiles: list[ProfileItem]


# --------------------------------------------------------------------------
# Screening evidence
# --------------------------------------------------------------------------


class TrajectoryPoint(Base):
    hour: float
    value: float


class PeerStatistics(Base):
    """Batch-relative context for one measurement, computed from early data only."""

    sample_size: int = Field(
        description="Number of comparable peers in the same batch/family/measurement/condition."
    )
    sufficient: bool = Field(
        description="False when sample_size is below the profile's min_peer_group_size."
    )
    status: CapabilityStatus
    median: float | None = None
    mad: float | None = Field(default=None, description="Median absolute deviation.")
    peer_min: float | None = None
    peer_max: float | None = None
    current_batch_robust_z: float | None = Field(
        default=None,
        description="Robust z-score of the cutoff value against comparable peers in the batch.",
    )
    slope_batch_robust_z: float | None = Field(
        default=None,
        description="Robust z-score of the early slope against the same peers.",
    )
    warning: str | None = Field(
        default=None,
        description="The core's own peer-comparison caveat, e.g. fewer than eight peers.",
    )
    note: str | None = None


class LimitInfo(Base):
    direction: LimitDirection
    upper_limit: float | None = None
    lower_limit: float | None = None
    applicable_limit: float | None = Field(
        default=None,
        description="The limit the decision was actually taken against.",
    )
    headroom: float | None = Field(
        default=None,
        description="Signed distance from the latest early value to the applicable limit, in measurement units.",
    )
    headroom_fraction: float | None = Field(
        default=None,
        description="headroom divided by the applicable limit. Null when the limit is zero.",
    )
    limit_fraction: float | None = Field(
        default=None, description="latest_value divided by the applicable limit."
    )


class FeatureContribution(Base):
    feature: str
    contribution: float
    direction: str = Field(description="'increases' or 'decreases' the predicted value.")


class AnomalyEvidence(Base):
    status: CapabilityStatus
    score: float | None = Field(
        default=None,
        description=(
            "Relative deviation score from the fitted detector. NOT a probability "
            "of physical failure and not a confidence level."
        ),
    )
    is_anomaly: bool | None = None
    method: str | None = Field(
        default=None, description="e.g. 'median_mad+isolation_forest'."
    )
    model_version: str | None = None
    contributing_features: list[FeatureContribution] = Field(default_factory=list)
    reason_codes: list[str] = Field(
        default_factory=list,
        description="Plain-language reason codes from the core detector.",
    )
    score_kind: str | None = Field(
        default=None,
        description=(
            "The core's own description of what the score is, e.g. "
            "'ranking score, not failure probability'."
        ),
    )
    model_score: float | None = Field(
        default=None, description="Isolation Forest component of the score."
    )
    robust_deviation_score: float | None = Field(
        default=None, description="Median/MAD component of the score."
    )
    note: str | None = None


class XgboostContribution(Base):
    feature: str
    contribution_ua: float
    feature_value: float


class XgboostExplanation(Base):
    """TreeSHAP contributions for the XGBoost candidate.

    ``is_active_forecast`` is false when a different model produced the forecast
    shown beside it. In that case these contributions explain the CANDIDATE, not
    the number on screen, and the UI must say so.
    """

    explains: str
    is_active_forecast: bool
    explained_model: str | None = Field(
        default=None,
        description=(
            "Which tree model these contributions explain: 'xgboost_v2' when that "
            "model produced the forecast, otherwise the v1 'xgboost' candidate."
        ),
    )
    base_value_ua: float
    top_contributions: list[XgboostContribution] = Field(default_factory=list)


class ForecastEvidence(Base):
    status: CapabilityStatus
    predicted_final_value: float | None = None
    prediction_lower: float | None = None
    prediction_upper: float | None = None
    target_hour: float | None = None
    interval_nominal_coverage: float | None = Field(
        default=None,
        description=(
            "Nominal coverage of the interval, e.g. 0.9. Empirical coverage is "
            "reported per-artifact in the manifest, not per-record, and may differ."
        ),
    )
    interval_method: str | None = Field(
        default=None,
        description="e.g. 'split_conformal'. Null when no calibrated interval is available.",
    )
    interval_stratum: str | None = Field(
        default=None,
        description=(
            "For the stratified v2 interval: which 24 h slope robust-z stratum "
            "supplied the margins (slope_z_stratum_0: z < 2, 1: 2 to 5, 2: >= 5)."
        ),
    )
    upper_bound_nominal_level: float | None = Field(
        default=None,
        description=(
            "For the stratified v2 interval: nominal one-sided level of "
            "prediction_upper (0.9 means about 10 % of comparable synthetic parts end above it). "
            "The pair (prediction_lower, prediction_upper) is then an 80 % interval."
        ),
    )
    prediction_lower_two_sided: float | None = Field(
        default=None, description="Wider two-sided 90 % lower bound (v2 stratified interval only)."
    )
    prediction_upper_two_sided: float | None = Field(
        default=None, description="Wider two-sided 90 % upper bound (v2 stratified interval only)."
    )
    model_version: str | None = None
    predicted_to_cross_limit: bool | None = Field(
        default=None,
        description="Whether the point prediction crosses the applicable limit at target_hour.",
    )
    explanation: list[FeatureContribution] = Field(
        default_factory=list,
        description=(
            "Feature contributions explaining model behaviour. These do not "
            "establish a physical cause such as water ingress or cracking."
        ),
    )
    interval_warning: str | None = Field(
        default=None,
        description="The artifact's own caveat about what the nominal level does and does not mean.",
    )
    prediction_readiness: str | None = Field(
        default=None,
        description="'ready', 'optional_inputs_imputed' or 'outside_training_conditions'.",
    )
    out_of_training_range_features: list[str] = Field(
        default_factory=list,
        description=(
            "Inputs beyond the ranges observed in training. Non-empty means the "
            "forecast extrapolates and its interval coverage does not transfer."
        ),
    )
    prediction_readiness_warning: str | None = None
    missing_optional_features: list[str] = Field(
        default_factory=list,
        description="Optional inputs that were absent and median-imputed.",
    )
    xgboost_candidate_final_value: float | None = Field(
        default=None,
        description=(
            "The XGBoost candidate's forecast, reported separately. It is NOT a "
            "substitute for predicted_final_value unless forecast_model is 'xgboost'."
        ),
    )
    xgboost_explanation: XgboostExplanation | None = None
    note: str | None = None


class ScreeningRecord(Base):
    """One (component, measurement) screening result."""

    # --- identity: the join key, never row order and never component_id alone
    component_id: str
    batch_id: str
    component_family: str
    measurement_name: str

    # --- core decision
    recommendation: Recommendation
    recommendation_basis: str = Field(
        description="'anomaly_and_forecast' or 'anomaly_only' (provisional when the forecast is unavailable)."
    )
    provisional: bool = Field(
        description="True when the recommendation was reached without a forecast."
    )

    # --- evidence
    anomaly: AnomalyEvidence
    forecast: ForecastEvidence
    limits: LimitInfo
    peers: PeerStatistics

    # --- presentation values, all derived from early data only
    measurement_unit: str | None = None
    initial_value: float | None = Field(default=None, description="Value at hour 0.")
    latest_value: float | None = Field(default=None, description="Value at the cutoff hour.")
    last_observation_hour: float | None = Field(
        default=None,
        description="Hour of the latest reading used for inference (the cutoff).",
    )
    absolute_change: float | None = Field(
        default=None, description="latest_value minus initial_value."
    )
    percent_change: float | None = Field(
        default=None,
        description="FRACTION, not a percentage. 0.1 means 10 %. Null when initial_value is 0.",
    )
    percent_change_available: bool = Field(
        description="False when initial_value is zero, where a displayable percentage is undefined."
    )
    slope_per_hour: float | None = Field(
        default=None,
        description="absolute_change divided by the elapsed hours between the two checkpoints.",
    )
    acceleration: None = Field(
        default=None,
        description=(
            "Always null in the 0/24 h mode. Two observations cannot evidence "
            "acceleration; the field exists so richer checkpoint profiles can populate it later."
        ),
    )
    early_trajectory: list[TrajectoryPoint] = Field(
        default_factory=list,
        description="The early readings actually used, ordered by hour.",
    )

    # --- optional uploaded metadata, null when not supplied
    part_number: str | None = None
    test_condition: str | None = None
    temperature_c: float | None = None
    humidity_pct: float | None = None
    applied_voltage_v: float | None = None
    board_position: str | None = None
    data_source: str | None = None
    provenance: DataProvenance
    profile_id: str | None = Field(
        default=None, description="Part/test profile this component was screened under."
    )
    recommendation_reasons: list[str] = Field(default_factory=list)
    data_quality_warning: str | None = None
    context: dict[str, str | float | None] = Field(
        default_factory=dict,
        description=(
            "Per-record context the upload supplied (part number, tester, board "
            "position, stress and measurement conditions). Presentation only - "
            "never a predictive input."
        ),
    )


class UnscoredRecord(Base):
    """A (component, measurement) history the service could not score.

    These are reported explicitly so the UI never implies a silent pass.
    """

    component_id: str
    batch_id: str
    component_family: str
    measurement_name: str
    reason: UnscoredReason
    message: str
    available_hours: list[float] = Field(default_factory=list)
    missing_checkpoint_hours: list[float] = Field(default_factory=list)


class ComponentSummary(Base):
    """Documented aggregation across the measurements of one component.

    ``summary_recommendation`` is the most urgent SCORED recommendation. It is
    null when no measurement of the component was scored. ``partial_coverage``
    is true whenever at least one measurement went unscored - the UI must not
    render such a component as fully passed.
    """

    component_id: str
    batch_id: str
    component_family: str
    summary_recommendation: Recommendation | None
    scored_measurement_count: int
    unscored_measurement_count: int
    partial_coverage: bool
    measurement_names: list[str]


class DecisionCounts(Base):
    ACCEPT: int = 0
    MONITOR: int = 0
    RETEST: int = 0
    ENGINEER_REVIEW: int = 0


class CapabilityFlags(Base):
    anomaly: bool
    forecast: bool
    intervals: bool = Field(
        description="Whether calibrated prediction intervals are available."
    )
    explanations: bool
    peer_statistics: bool
    mode: str
    limitations: list[str] = Field(default_factory=list)


class OutcomeRecord(Base):
    """EVALUATION ONLY.

    Populated from observations after the cutoff when the upload contains them.
    These values never enter feature building, scoring, peer statistics or
    explanations. The section is omitted entirely for early-only uploads.
    """

    component_id: str
    batch_id: str
    component_family: str
    measurement_name: str
    observed_value: float
    observed_hour: float
    applicable_limit: float | None = Field(
        default=None,
        description=(
            "The specification limit this outcome was compared against, taken "
            "from the uploaded history. Null when the upload declared no limit "
            "for this component."
        ),
    )
    crossed_applicable_limit: bool | None = Field(
        default=None,
        description=(
            "True when the observed value breached the applicable limit. "
            "NULL means the limit was unknown, so no comparison was possible - "
            "it does NOT mean the component stayed inside its limit."
        ),
    )


class EvaluationSection(Base):
    available: bool
    source_filename: str | None = Field(
        default=None,
        description=(
            "Filename of the separate outcome file these came from, when one was "
            "uploaded. Null when the outcomes were extra rows in the main file."
        ),
    )
    kind: str = Field(
        default="observed_readings",
        description=(
            "'observed_readings' means real later measurements. "
            "'simulation_truth' means latent generator values, which are NOT "
            "sensor measurements and must be labelled as such in the UI."
        ),
    )
    target_hour: float
    note: str = Field(
        description="States that these values were excluded from all inference."
    )
    outcomes: list[OutcomeRecord] = Field(default_factory=list)


class ResponseWarning(Base):
    code: str
    message: str
    count: int | None = None


class ModelInfo(Base):
    """Identity and honest provenance of the models that produced this response.

    ``selected_model`` is the model that ACTUALLY produced every
    ``predicted_final_value``. ``validation_winner`` is the model that scored
    best on internal validation. When they differ, ``selection_warning`` is
    non-null, and the UI must not imply the selected model outperformed the
    baseline.
    """

    prototype_version: str | None = None
    bundle_id: str | None = None
    selected_model: str | None = Field(
        default=None,
        description="The model that produced the forecasts in this response.",
    )
    validation_winner: str | None = Field(
        default=None, description="Lowest-error model on internal validation batches."
    )
    forecast_selection: str | None = Field(
        default=None,
        description="'explicit caller choice' or 'internal validation winner'.",
    )
    selection_warning: str | None = Field(
        default=None,
        description="Non-null when the selected model is not the validation winner.",
    )
    model_training_data: str | None = Field(
        default=None,
        description=(
            "Provenance of the TRAINING data. Separate from the uploaded file's provenance."
        ),
    )
    model_fitted_during_request: bool | None = Field(
        default=None, description="The core's own declaration. Must be false."
    )
    supported_family: str | None = None
    supported_measurement: str | None = None
    available_models: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class ScreenResponse(Base):
    # --- envelope
    schema_version: str
    request_id: str
    generated_at: datetime
    duration_ms: float = Field(
        description="Measured server-side processing time for this request."
    )

    # --- input description
    input_source: str = Field(description="'upload' or 'sample'.")
    filename: str | None = None
    profile_id: str | None = None
    as_of_hour: float
    target_hour: float
    checkpoint_hours_used: list[float]

    # --- model identity
    model_versions: dict[str, str | None]
    model_info: ModelInfo = Field(default_factory=ModelInfo)

    # --- dataset shape
    batch_count: int
    unique_component_count: int
    measurement_record_count: int = Field(
        description="Number of (component, measurement) histories present in the upload."
    )
    scored_record_count: int
    unscored_record_count: int

    # --- results
    decision_counts: DecisionCounts
    capabilities: CapabilityFlags
    provenance: DataProvenance
    records: list[ScreeningRecord]
    unscored_records: list[UnscoredRecord]
    component_summaries: list[ComponentSummary]
    evaluation: EvaluationSection | None = Field(
        default=None, description="Omitted when the upload contains only early data."
    )
    warnings: list[ResponseWarning] = Field(default_factory=list)
