"""The one and only import boundary to the core (Karthik's) modules.

Nothing else in the API imports ``sih26170.features``, ``sih26170.anomaly``,
``sih26170.contracts`` or ``sih26170.decision`` directly. Keeping the boundary
in a single file means that when the core snapshot lands, at most this file
needs adjusting - the routes, schemas and frontend contract do not.

Current state in this working copy: the core modules are ABSENT. The service
therefore starts, reports the capability as unavailable with a readable reason,
and refuses to score. It never substitutes a stand-in implementation.

ASSUMPTIONS THAT NEED CONFIRMING AGAINST THE REAL SNAPSHOT
----------------------------------------------------------
The following are pinned by the project handoff and are treated as contract:

    features = build_component_features(early_readings, as_of_hour=24)
    scored   = fitted_detector.score(features)
    anomalies = fitted_detector.to_results(scored)
    record   = build_screening_record(anomaly, prediction)
    PredictionResult(predicted_final_value=, prediction_lower=,
                     prediction_upper=, target_hour=)

The ATTRIBUTE NAMES on the objects those calls return are not pinned by the
handoff. ``adapt_screening_record`` below reads them through one documented
mapping and raises a loud, specific error rather than silently guessing.
Any mismatch is logged in docs/backend/INTEGRATION_REQUESTS.md.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from types import ModuleType
from typing import Any

from sih26170.api.errors import ApiError, ErrorCode, unavailable

#: Core modules the screening path needs, in the order they are reported.
REQUIRED_CORE_MODULES: tuple[str, ...] = (
    "sih26170.validation",
    "sih26170.features",
    "sih26170.anomaly",
    "sih26170.contracts",
    "sih26170.decision",
)

#: Attribute names this layer reads off a core screening record. If the core
#: uses different names, only this mapping changes.
SCREENING_RECORD_FIELDS: tuple[str, ...] = ("recommendation",)


@dataclass(frozen=True)
class CoreStatus:
    available: bool
    present_modules: tuple[str, ...]
    missing_modules: tuple[str, ...]
    reason: str | None

    @property
    def summary(self) -> str:
        if self.available:
            return "Core modules importable."
        return self.reason or "Core modules unavailable."


def probe_core() -> CoreStatus:
    """Report which core modules can actually be imported right now."""
    present: list[str] = []
    missing: list[str] = []
    failures: list[str] = []

    for name in REQUIRED_CORE_MODULES:
        try:
            importlib.import_module(name)
        except ImportError:
            missing.append(name)
        except Exception as exc:  # a module that exists but blows up on import
            missing.append(name)
            failures.append(f"{name}: {type(exc).__name__}")
        else:
            present.append(name)

    if not missing:
        return CoreStatus(True, tuple(present), (), None)

    reason = (
        "Core screening modules are not importable: "
        + ", ".join(missing)
        + ". The anomaly and screening pipeline cannot run until the core "
        "snapshot is present in this working copy."
    )
    if failures:
        reason += " Import errors: " + "; ".join(failures) + "."
    return CoreStatus(False, tuple(present), tuple(missing), reason)


def _require(module_name: str) -> ModuleType:
    try:
        return importlib.import_module(module_name)
    except ImportError as exc:
        raise unavailable(
            ErrorCode.CORE_UNAVAILABLE,
            f"Core module '{module_name}' is not available in this deployment.",
        ) from exc


def build_component_features(early_readings: Any, *, as_of_hour: float) -> Any:
    """Shared feature builder. Signature pinned by the project handoff.

    ``early_readings`` must already be restricted to the exact checkpoint hours
    for the profile. This function does not do that filtering; the API layer
    does it in ``ingestion.split_early_and_future`` so the 0/24 h claim is true
    of what the model actually consumed.
    """
    features_module = _require("sih26170.features")
    fn = getattr(features_module, "build_component_features", None)
    if fn is None:
        raise unavailable(
            ErrorCode.CORE_UNAVAILABLE,
            "sih26170.features does not expose build_component_features().",
        )
    return fn(early_readings, as_of_hour=as_of_hour)


def make_prediction_result(
    *,
    predicted_final_value: float,
    prediction_lower: float | None,
    prediction_upper: float | None,
    target_hour: float,
) -> Any:
    """Construct the core PredictionResult.

    Callers must not invent bounds. When no calibrated interval exists, pass
    ``None`` for both bounds and let the response carry a null interval with a
    stated reason.
    """
    contracts = _require("sih26170.contracts")
    cls = getattr(contracts, "PredictionResult", None)
    if cls is None:
        raise unavailable(
            ErrorCode.CORE_UNAVAILABLE,
            "sih26170.contracts does not expose PredictionResult.",
        )
    return cls(
        predicted_final_value=predicted_final_value,
        prediction_lower=prediction_lower,
        prediction_upper=prediction_upper,
        target_hour=target_hour,
    )


def build_screening_record(anomaly: Any, prediction: Any) -> Any:
    """Combine an anomaly result and a prediction using core decision logic."""
    decision = _require("sih26170.decision")
    fn = getattr(decision, "build_screening_record", None)
    if fn is None:
        raise unavailable(
            ErrorCode.CORE_UNAVAILABLE,
            "sih26170.decision does not expose build_screening_record().",
        )
    return fn(anomaly, prediction)


def adapt_screening_record(record: Any) -> str:
    """Read the recommendation off a core screening record.

    Raises a specific ApiError instead of guessing, so an interface drift in
    the core surfaces as a clear integration failure rather than a wrong
    ACCEPT on a judge's screen.
    """
    value = getattr(record, "recommendation", None)
    if value is None and isinstance(record, dict):
        value = record.get("recommendation")
    if value is None:
        raise ApiError(
            ErrorCode.CORE_UNAVAILABLE,
            "The core screening record does not expose a 'recommendation' "
            "attribute. The API/core interface has drifted; see "
            "docs/backend/INTEGRATION_REQUESTS.md.",
            http_status=503,
        )
    return getattr(value, "value", value) if not isinstance(value, str) else value
