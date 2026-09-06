"""Liveness and readiness endpoints."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Request, Response, status

from sih26170.api.config import SCHEMA_VERSION, SERVICE_VERSION
from sih26170.api.schemas import (
    CapabilityReport,
    LivenessResponse,
    ProbeCheck,
    ReadinessResponse,
)
from sih26170.prediction.base import CapabilityState

router = APIRouter(prefix="/health", tags=["health"])


def _to_report(state: CapabilityState) -> CapabilityReport:
    return CapabilityReport(
        name=state.name,
        available=state.available,
        reason=state.reason,
        artifact_id=state.artifact_id,
        model_version=state.model_version,
        checks=[
            ProbeCheck(name=name, passed=passed, detail=detail)
            for name, passed, detail in state.checks
        ],
    )


@router.get(
    "/live",
    response_model=LivenessResponse,
    summary="Process liveness",
    description="Returns 200 whenever the process is running. It says nothing about model availability.",
)
def live() -> LivenessResponse:
    return LivenessResponse(
        version=SERVICE_VERSION,
        schema_version=SCHEMA_VERSION,
        timestamp=datetime.now(timezone.utc),
    )


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    summary="Readiness for the configured mode",
    responses={503: {"model": ReadinessResponse, "description": "Required capabilities are unavailable."}},
    description=(
        "Returns 200 only when the configured mode's artifacts, schema, checksums "
        "and a small inference probe all pass. Otherwise 503 with the specific "
        "reason for each capability. Demo mode requires both anomaly and forecast."
    ),
)
def ready(request: Request, response: Response) -> ReadinessResponse:
    registry = request.app.state.registry
    settings = request.app.state.settings

    is_ready, limitations = registry.is_ready()

    core = registry.core_status
    reports = [
        CapabilityReport(
            name="core_modules",
            available=core.available,
            reason=core.reason,
            checks=[
                ProbeCheck(
                    name=module,
                    passed=module in core.present_modules,
                    detail=None if module in core.present_modules else "Module not importable.",
                )
                for module in (*core.present_modules, *core.missing_modules)
            ],
        ),
        _to_report(registry.anomaly_state),
        _to_report(registry.forecast_state),
    ]

    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return ReadinessResponse(
        ready=is_ready,
        mode=settings.mode.value,
        version=SERVICE_VERSION,
        schema_version=SCHEMA_VERSION,
        timestamp=datetime.now(timezone.utc),
        capabilities=reports,
        limitations=limitations,
    )
