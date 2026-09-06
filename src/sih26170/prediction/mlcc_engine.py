"""The single typed adapter between the API and the MLCC prototype bundle.

Ownership (per Karthik's 5 Sep 2026 handoff): he owns the dataset, feature
construction, model fitting, calibration, artifacts and evaluation. This module
owns only the boundary - loading the trusted local bundle once at startup,
verifying it, and calling ``screen_readings`` with a frame the core expects.

Nothing here retrains, tunes, downloads or fits anything. ``screen_readings``
itself reports ``model_fitted_during_request: False``; the readiness probe below
asserts that flag rather than taking it on trust.

Two honesty rules are enforced by the mapping, not by convention:

  * The forecast model actually used is read from the response
    (``metadata.selected_model``). "XGBoost" is never hard-coded next to a
    forecast. When the caller's choice differs from the internal validation
    winner, ``selection_warning`` is carried through verbatim.
  * Later observations are returned by the core in a separate ``future_outcomes``
    (observed readings) or ``simulation_truth`` (latent generator values)
    envelope. The two are never merged, and neither is an inference input.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

#: Columns that identify a component history. Kept as text so leading zeros and
#: identifiers like "MLCC_C000062" survive intact.
IDENTITY_COLUMNS: tuple[str, ...] = (
    "component_id",
    "batch_id",
    "component_family",
    "measurement_name",
)

#: Columns that are categorical text even though they may look numeric.
TEXT_COLUMNS: frozenset[str] = frozenset(
    {
        "profile_id",
        "part_number",
        "package_code",
        "dielectric",
        "tester_id",
        "data_source",
        "generator_version",
        "scenario",
        "component_scenario",
    }
)

#: Files every bundle must carry. A bundle may declare more (the v2 bundle adds
#: xgboost_v2.ubj); every declared artifact is checksum-verified as well.
BUNDLE_FILES: tuple[str, ...] = ("state.skops", "xgboost.json", "evaluation.json")


class MlccEngineUnavailable(RuntimeError):
    """Raised when the bundle cannot be loaded or verified."""


@dataclass(frozen=True)
class BundleIdentity:
    """What the loaded artifact says about itself."""

    prototype_version: str
    bundle_id: str
    family: str
    measurement: str
    unit: str
    as_of_hour: float
    target_hour: float
    selected_model: str
    supported_profiles: tuple[str, ...]
    training_data: str
    available_models: tuple[str, ...]


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def to_core_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Give the core numeric columns without losing string identities.

    The API ingests every column as text so leading zeros survive validation.
    The prototype expects real numbers for its feature columns, so each
    non-identity, non-categorical column is converted only when every non-empty
    value in it parses as a number. A column with any genuinely textual value is
    left alone rather than being silently coerced to NaN.
    """
    out = frame.copy()
    for column in out.columns:
        if column in IDENTITY_COLUMNS or column in TEXT_COLUMNS:
            out[column] = out[column].astype(str)
            continue
        series = out[column]
        if not (series.dtype == object or str(series.dtype).startswith("str")):
            continue  # already numeric
        text = series.astype(str).str.strip()
        non_empty = text[text != ""]
        if non_empty.empty:
            continue
        converted = pd.to_numeric(non_empty, errors="coerce")
        if converted.notna().all():
            out[column] = pd.to_numeric(text.where(text != ""), errors="coerce")
    return out


class MlccEngine:
    """Loaded MLCC bundle plus the one call the API is allowed to make."""

    def __init__(self, bundle: Any, manifest: dict[str, Any], directory: Path) -> None:
        self._bundle = bundle
        self._manifest = manifest
        self._directory = directory

        interval = manifest.get("interval", {}) or {}
        radii = interval.get("radii_normalized", {}) or {}

        self.identity = BundleIdentity(
            prototype_version=str(manifest.get("prototype_version", "unknown")),
            bundle_id=str(manifest.get("bundle_id", "unknown")),
            family=str(manifest.get("family", "")),
            measurement=str(manifest.get("measurement", "")),
            unit=str(manifest.get("unit", "")),
            as_of_hour=float(manifest.get("as_of_hour", 24.0)),
            target_hour=float(manifest.get("target_hour", 168.0)),
            selected_model=str(manifest.get("selected_model", "")),
            supported_profiles=tuple(manifest.get("supported_profiles", []) or ()),
            training_data=str(manifest.get("training_data", "unknown")),
            available_models=tuple(sorted(radii)),
        )

    @property
    def manifest(self) -> dict[str, Any]:
        return self._manifest

    def supports_model(self, name: str) -> bool:
        return name in self.identity.available_models

    def screen(
        self,
        readings: pd.DataFrame,
        *,
        as_of_hour: float,
        forecast_model: str | None = None,
        future_outcomes: pd.DataFrame | None = None,
    ) -> dict[str, Any]:
        """Run the frozen models. The only core entry point the API calls."""
        from sih26170.mlcc_prototype import screen_readings

        return screen_readings(
            to_core_frame(readings),
            self._bundle,
            as_of_hour=as_of_hour,
            forecast_model=forecast_model,
            future_outcomes=(
                to_core_frame(future_outcomes) if future_outcomes is not None else None
            ),
        )


def verify_bundle(directory: Path, manifest: dict[str, Any]) -> list[tuple[str, bool, str | None]]:
    """Check every declared artifact exists and matches its manifest checksum."""
    checks: list[tuple[str, bool, str | None]] = []
    declared = manifest.get("artifact_sha256", {}) or {}

    for filename in BUNDLE_FILES + tuple(name for name in declared if name not in BUNDLE_FILES):
        path = directory / filename
        if not path.is_file():
            checks.append((f"file:{filename}", False, "Artifact file is missing."))
            continue
        expected = declared.get(filename)
        if not expected:
            checks.append(
                (f"checksum:{filename}", False, "Manifest declares no checksum for this file.")
            )
            continue
        actual = sha256_file(path)
        checks.append(
            (
                f"checksum:{filename}",
                actual == expected,
                None if actual == expected else "Checksum does not match the manifest.",
            )
        )
    return checks


def check_library_versions(manifest: dict[str, Any]) -> list[tuple[str, bool, str | None]]:
    """Compare installed versions against the ones the artifact was built with.

    A mismatch is reported but is not fatal on its own: the checksum and the
    inference probe decide whether the bundle is actually usable.
    """
    import importlib

    checks: list[tuple[str, bool, str | None]] = []
    for package, expected in (manifest.get("versions", {}) or {}).items():
        module_name = {"scikit-learn": "sklearn"}.get(package, package)
        try:
            installed = importlib.import_module(module_name).__version__
        except Exception:
            checks.append((f"version:{package}", False, "Package is not importable."))
            continue
        matches = installed == expected
        checks.append(
            (
                f"version:{package}",
                matches,
                None if matches else f"installed {installed}, artifact built with {expected}",
            )
        )
    return checks


def load_mlcc_engine(directory: Path) -> tuple[MlccEngine, list[tuple[str, bool, str | None]]]:
    """Load and verify the bundle. Raises MlccEngineUnavailable on failure."""
    import json

    manifest_path = directory / "manifest.json"
    if not manifest_path.is_file():
        raise MlccEngineUnavailable(f"No manifest.json in {directory}.")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    checks = verify_bundle(directory, manifest)
    failed = [name for name, passed, _ in checks if not passed]
    if failed:
        raise MlccEngineUnavailable(
            "Bundle integrity check failed for: " + ", ".join(failed)
        )

    checks.extend(check_library_versions(manifest))

    try:
        from sih26170.mlcc_prototype import load_bundle
    except ImportError as exc:  # xgboost / skops absent
        raise MlccEngineUnavailable(
            f"A library required by the MLCC prototype is not installed: {exc.name}. "
            "Install the 'prototype' extra."
        ) from exc

    try:
        bundle = load_bundle(directory)
    except Exception as exc:
        logger.warning("MLCC bundle failed to load: %s", type(exc).__name__)
        raise MlccEngineUnavailable(
            f"The MLCC bundle could not be deserialised ({type(exc).__name__})."
        ) from exc

    checks.append(("bundle_load", True, None))
    return MlccEngine(bundle, manifest, directory), checks


def inference_probe(engine: MlccEngine) -> tuple[bool, str | None]:
    """Score two synthetic rows so readiness reflects real usability.

    Also asserts the core's own declaration that no model was fitted during the
    call, so a regression there fails startup rather than a demo.
    """
    profile = engine.identity.supported_profiles[0] if engine.identity.supported_profiles else ""
    base = {
        "component_id": "__probe__",
        "batch_id": "__probe_batch__",
        "component_family": engine.identity.family,
        "measurement_name": engine.identity.measurement,
        "upper_limit": 1.0,
        "profile_id": profile,
    }
    frame = pd.DataFrame(
        [
            {**base, "hours": 0.0, "measurement_value": 0.10},
            {**base, "hours": engine.identity.as_of_hour, "measurement_value": 0.12},
        ]
    )
    try:
        result = engine.screen(frame, as_of_hour=engine.identity.as_of_hour)
    except Exception as exc:
        return False, f"Inference probe failed ({type(exc).__name__})."

    if not result.get("records"):
        return False, "Inference probe returned no records."
    if result.get("metadata", {}).get("model_fitted_during_request") is not False:
        return False, "The core did not confirm that no model was fitted during the request."
    return True, None
