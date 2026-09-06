"""Screening profile registry.

A profile pins one (component_family, measurement_name) pair to its unit, its
limit direction, the checkpoints it needs and the peer-group size below which
batch-relative statistics are not claimed to be reliable.

Two separate ideas are kept apart on purpose:

  ``status``      - is the profile *definition* complete and validated?
  availability    - are the artifacts for it actually loaded right now?

A profile is only usable when both hold. Planned profiles are advertised so the
roadmap is visible in the UI, but they can never score anything.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class LimitDirection(str, Enum):
    """Which side of the specification counts as a failure."""

    UPPER = "upper"
    LOWER = "lower"
    TWO_SIDED = "two_sided"


class ProfileStatus(str, Enum):
    SUPPORTED = "supported"
    PLANNED = "planned"


class DataProvenance(str, Enum):
    """How the data reaching the API was produced.

    ``MEASURED_UNVERIFIED`` is an uploader's *claim* of hardware data. The API
    cannot independently verify provenance, so a claim is never promoted to
    verified, and an absent ``data_source`` column stays ``UNKNOWN``.
    """

    SYNTHETIC = "synthetic"
    UNKNOWN = "unknown"
    MEASURED_UNVERIFIED = "measured_unverified"
    MIXED = "mixed"


# Tokens in a `data_source` value that mark a row as generated, not measured.
SYNTHETIC_MARKERS = ("synthetic", "simulated", "generated", "synth", "fake", "demo")


@dataclass(frozen=True)
class Profile:
    profile_id: str
    component_family: str
    measurement_name: str
    measurement_unit: str
    limit_direction: LimitDirection
    status: ProfileStatus
    description: str
    required_checkpoint_hours: tuple[float, ...] = (0.0, 24.0)
    as_of_hour: float = 24.0
    target_hour: float = 168.0
    min_peer_group_size: int = 8
    unit_aliases: frozenset[str] = field(default_factory=frozenset)
    provenance_note: str = ""

    @property
    def key(self) -> tuple[str, str]:
        return (self.component_family, self.measurement_name)

    def unit_matches(self, declared: str) -> bool:
        candidate = declared.strip()
        if candidate == self.measurement_unit:
            return True
        return candidate.casefold() in {a.casefold() for a in self.unit_aliases}


# ---------------------------------------------------------------------------
# Registry
#
# The two SUPPORTED profiles below deliberately mirror the families the existing
# synthetic generator already produces (Digital IC / leakage_ua and
# Power MOSFET / rds_on_mohm). They are plumbing profiles backed by synthetic
# development data - not validated hardware screening.
#
# The MLCC pilot is PLANNED: it is the real target of the project, but no
# artifact and no measured data exist for it yet, so it must not score.
# ---------------------------------------------------------------------------

_PROFILES: tuple[Profile, ...] = (
    Profile(
        profile_id="digital_ic_leakage_ua",
        component_family="Digital IC",
        measurement_name="leakage_ua",
        measurement_unit="uA",
        unit_aliases=frozenset({"ua", "µa", "μa", "microamp", "microamps"}),
        limit_direction=LimitDirection.UPPER,
        status=ProfileStatus.PLANNED,
        description=(
            "Digital IC leakage current in microamps. A generic synthetic "
            "development family with no trained artifact of its own, so it "
            "cannot be scored. The MLCC bundle does not apply to it."
        ),
        provenance_note=(
            "No artifact. Renaming a component_family does not make a model "
            "apply to that family."
        ),
    ),
    Profile(
        profile_id="power_mosfet_rds_on_mohm",
        component_family="Power MOSFET",
        measurement_name="rds_on_mohm",
        measurement_unit="mOhm",
        unit_aliases=frozenset({"mohm", "milliohm", "milliohms", "mΩ"}),
        limit_direction=LimitDirection.UPPER,
        status=ProfileStatus.PLANNED,
        description=(
            "Power MOSFET on-state resistance in milliohms. A generic synthetic "
            "development family with no trained artifact, so it cannot be scored."
        ),
        provenance_note="No artifact.",
    ),
    Profile(
        profile_id="mlcc_x7r_leakage_ua",
        component_family="MLCC_X7R",
        measurement_name="leakage_ua",
        measurement_unit="uA",
        unit_aliases=frozenset({"ua", "µa", "μa", "microamp", "microamps"}),
        limit_direction=LimitDirection.UPPER,
        status=ProfileStatus.SUPPORTED,
        description=(
            "PILOT PROFILE. X7R multilayer ceramic capacitor leakage current in "
            "microamps, screened at 0 h and 24 h against a 168 h target by the "
            "loaded MLCC bundle. Rows must carry a profile_id matching one of "
            "the bundle's supported part/test profiles."
        ),
        provenance_note=(
            "The models are trained on SYNTHETIC MLCC data. No measured hardware "
            "data has been supplied, so this demonstrates the pipeline and is not "
            "validated hardware screening."
        ),
    ),
    Profile(
        profile_id="film_cap_capacitance_nf",
        component_family="Film Capacitor",
        measurement_name="capacitance_nf",
        measurement_unit="nF",
        unit_aliases=frozenset({"nf", "nanofarad", "nanofarads"}),
        limit_direction=LimitDirection.LOWER,
        status=ProfileStatus.PLANNED,
        description=(
            "Film capacitor capacitance in nanofarads. Failure is loss of "
            "capacitance, so this profile is LOWER limit. The current core "
            "decision logic handles upper limits only, so this profile cannot "
            "be scored until two-sided screening exists."
        ),
        provenance_note="Lower-limit profile; no artifact.",
    ),
)

_BY_KEY: dict[tuple[str, str], Profile] = {p.key: p for p in _PROFILES}
_BY_ID: dict[str, Profile] = {p.profile_id: p for p in _PROFILES}


def all_profiles() -> tuple[Profile, ...]:
    return _PROFILES


def find_profile(component_family: str, measurement_name: str) -> Profile | None:
    return _BY_KEY.get((component_family, measurement_name))


def get_profile_by_id(profile_id: str) -> Profile | None:
    return _BY_ID.get(profile_id)


def classify_provenance(values: set[str]) -> DataProvenance:
    """Map the distinct ``data_source`` values of an upload to a provenance.

    An empty set (column absent) is UNKNOWN, never "verified real". A value
    containing a synthetic marker is SYNTHETIC and is never upgraded.
    """
    cleaned = {v.strip().casefold() for v in values if v and v.strip()}
    if not cleaned:
        return DataProvenance.UNKNOWN

    def is_synth(v: str) -> bool:
        return any(marker in v for marker in SYNTHETIC_MARKERS)

    synth = {v for v in cleaned if is_synth(v)}
    if synth == cleaned:
        return DataProvenance.SYNTHETIC
    if not synth:
        return DataProvenance.MEASURED_UNVERIFIED
    return DataProvenance.MIXED
