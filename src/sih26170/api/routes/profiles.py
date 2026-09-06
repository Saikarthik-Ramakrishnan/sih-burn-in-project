"""Available and planned screening profiles."""

from __future__ import annotations

from fastapi import APIRouter, Request

from sih26170.api.config import SCHEMA_VERSION
from sih26170.api.profiles import ProfileStatus, all_profiles
from sih26170.api.schemas import ProfileItem, ProfilesResponse

router = APIRouter(tags=["profiles"])


@router.get(
    "/profiles",
    response_model=ProfilesResponse,
    summary="Screening profiles and their availability",
    description=(
        "Lists every family/measurement profile the service knows about. A profile "
        "is usable only when its definition is 'supported' AND its artifacts are "
        "loaded. Planned profiles are listed so the roadmap is visible; they are "
        "never scoreable and 'usable' is false for them."
    ),
)
def list_profiles(request: Request) -> ProfilesResponse:
    registry = request.app.state.registry
    settings = request.app.state.settings

    anomaly_ready = registry.anomaly_state.available
    engine = registry.mlcc_engine
    items: list[ProfileItem] = []

    for profile in all_profiles():
        backed_by_bundle = engine is not None and (
            profile.component_family == engine.identity.family
            and profile.measurement_name == engine.identity.measurement
        )
        if backed_by_bundle:
            forecast_ready = registry.forecast_state.available
            part_profiles = list(engine.identity.supported_profiles)
        else:
            forecast_ready = registry.forecast_adapter_for(profile.profile_id) is not None
            part_profiles = []

        definition_ok = profile.status is ProfileStatus.SUPPORTED
        usable = definition_ok and anomaly_ready and (backed_by_bundle or forecast_ready)

        reasons: list[str] = []
        if not definition_ok:
            reasons.append(
                f"Profile '{profile.profile_id}' is planned, not yet validated for screening."
            )
        if definition_ok and not backed_by_bundle and not forecast_ready:
            reasons.append(
                f"No loaded artifact covers {profile.component_family} / "
                f"{profile.measurement_name}."
            )
        if not anomaly_ready and registry.anomaly_state.reason:
            reasons.append(registry.anomaly_state.reason)
        if not forecast_ready and registry.forecast_state.reason:
            reasons.append(registry.forecast_state.reason)

        items.append(
            ProfileItem(
                profile_id=profile.profile_id,
                component_family=profile.component_family,
                measurement_name=profile.measurement_name,
                measurement_unit=profile.measurement_unit,
                limit_direction=profile.limit_direction,
                status=profile.status,
                required_checkpoint_hours=list(profile.required_checkpoint_hours),
                as_of_hour=profile.as_of_hour,
                target_hour=profile.target_hour,
                min_peer_group_size=profile.min_peer_group_size,
                anomaly_available=anomaly_ready and definition_ok,
                forecast_available=forecast_ready and definition_ok,
                usable=usable,
                supported_part_profiles=part_profiles,
                description=profile.description,
                provenance_note=profile.provenance_note or None,
                unavailable_reason=" ".join(reasons) if reasons else None,
            )
        )

    return ProfilesResponse(
        schema_version=SCHEMA_VERSION,
        mode=settings.mode.value,
        profiles=items,
    )
