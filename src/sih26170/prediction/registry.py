"""Startup-time model loading, verification and capability reporting.

Artifacts are loaded ONCE, when the process starts, from a trusted local
directory. A scoring request never loads, downloads or fits a model, and the
service never accepts an uploaded model.

Each artifact directory under ``artifacts/`` must contain a ``manifest.json``.
Loading an artifact runs four gates in order - manifest parse, feature-schema
hash, file checksums, and a small inference probe. A failure at any gate leaves
the capability unavailable with the specific reason recorded, rather than
half-loaded.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from sih26170.api.config import ServiceMode, Settings
from sih26170.api.core_bridge import CoreStatus, probe_core
from sih26170.prediction.artifacts import (
    ArtifactKind,
    ArtifactManifest,
    load_manifest,
    verify_artifact_files,
    verify_feature_schema,
)
from sih26170.prediction.base import (
    AnomalyAdapter,
    CapabilityState,
    ForecastAdapter,
)
from sih26170.prediction.mlcc_engine import (
    MlccEngine,
    MlccEngineUnavailable,
    inference_probe,
    load_mlcc_engine,
)

logger = logging.getLogger(__name__)


class ModelRegistry:
    """Holds the loaded adapters and why anything missing is missing."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._anomaly: AnomalyAdapter | None = None
        self._forecasts: list[ForecastAdapter] = []
        self._anomaly_state = CapabilityState("anomaly", available=False, reason="Not loaded.")
        self._forecast_state = CapabilityState("forecast", available=False, reason="Not loaded.")
        self._core_status: CoreStatus | None = None
        self._mlcc: MlccEngine | None = None
        self._loaded = False

    # -- lifecycle ---------------------------------------------------------

    def load(self) -> None:
        """Load every artifact once. Safe to call again; it is a no-op."""
        if self._loaded:
            return
        self._core_status = probe_core()

        # The MLCC bundle is the validated pilot artifact and backs BOTH the
        # anomaly and forecast capabilities. The generic artifacts/ scan below
        # is only reached when no bundle is present.
        mlcc_state = self._load_mlcc()
        if mlcc_state.available:
            self._anomaly_state = mlcc_state
            self._forecast_state = CapabilityState(
                "forecast",
                available=True,
                artifact_id=mlcc_state.artifact_id,
                model_version=mlcc_state.model_version,
                checks=list(mlcc_state.checks),
            )
        else:
            self._anomaly_state = self._load_kind(ArtifactKind.ANOMALY)
            self._forecast_state = self._load_kind(ArtifactKind.FORECAST)
            if mlcc_state.reason:
                self._anomaly_state.reason = mlcc_state.reason
                self._forecast_state.reason = mlcc_state.reason
                self._anomaly_state.checks.extend(mlcc_state.checks)
                self._forecast_state.checks.extend(mlcc_state.checks)
        self._loaded = True

    def _load_mlcc(self) -> CapabilityState:
        """Load and probe the MLCC prototype bundle once."""
        state = CapabilityState("anomaly", available=False)
        directory = self._settings.mlcc_bundle_dir

        if not directory.is_dir():
            state.add_check("bundle_present", False, f"No bundle directory at {directory}.")
            state.reason = (
                f"The MLCC model bundle is not present at {directory}. "
                "Screening is unavailable until it is supplied."
            )
            return state

        try:
            engine, checks = load_mlcc_engine(directory)
        except MlccEngineUnavailable as exc:
            state.add_check("bundle_load", False, str(exc))
            state.reason = str(exc)
            return state

        state.checks.extend(checks)
        probe_ok, probe_detail = inference_probe(engine)
        state.add_check("inference_probe", probe_ok, probe_detail)
        if not probe_ok:
            state.reason = probe_detail
            return state

        self._mlcc = engine
        state.available = True
        state.artifact_id = engine.identity.bundle_id
        state.model_version = engine.identity.prototype_version
        return state

    def _artifact_dirs(self) -> list[Path]:
        root = self._settings.artifacts_dir
        if not root.is_dir():
            return []
        return sorted(p for p in root.iterdir() if p.is_dir() and (p / "manifest.json").is_file())

    def _load_kind(self, kind: ArtifactKind) -> CapabilityState:
        state = CapabilityState(kind.value, available=False)

        # The anomaly capability additionally needs the core modules, because
        # feature building and decision logic live there.
        if kind is ArtifactKind.ANOMALY and self._core_status and not self._core_status.available:
            state.add_check("core_modules", False, self._core_status.reason)
            state.reason = self._core_status.reason
            return state
        if kind is ArtifactKind.ANOMALY and self._core_status:
            state.add_check("core_modules", True, None)

        directories = self._artifact_dirs()
        if not directories:
            state.add_check(
                "artifact_present",
                False,
                f"No artifact directory with a manifest.json under {self._settings.artifacts_dir}.",
            )
            state.reason = (
                f"No {kind.value} artifact has been packaged yet. Run the offline "
                f"preparation script to produce one under {self._settings.artifacts_dir}."
            )
            return state

        for directory in directories:
            try:
                manifest = load_manifest(directory)
            except Exception as exc:
                logger.warning("Unreadable manifest in %s: %s", directory.name, type(exc).__name__)
                state.add_check(f"manifest:{directory.name}", False, "Manifest is unreadable or invalid.")
                continue

            if manifest.kind is not kind:
                continue

            state.artifact_id = manifest.artifact_id
            state.model_version = manifest.model_version
            state.add_check(f"manifest:{directory.name}", True, None)

            schema_check = verify_feature_schema(manifest)
            state.checks.append(schema_check)
            if not schema_check[1]:
                state.reason = schema_check[2]
                return state

            file_checks = verify_artifact_files(manifest, directory)
            state.checks.extend(file_checks)
            if any(not passed for _, passed, _ in file_checks):
                state.reason = "One or more artifact files failed checksum or presence verification."
                return state

            adapter, failure = self._build_adapter(kind, manifest, directory)
            if adapter is None:
                state.add_check("adapter_load", False, failure)
                state.reason = failure
                return state
            state.add_check("adapter_load", True, None)

            probe_ok, probe_detail = self._inference_probe(kind, adapter, manifest)
            state.add_check("inference_probe", probe_ok, probe_detail)
            if not probe_ok:
                state.reason = probe_detail
                return state

            if kind is ArtifactKind.ANOMALY:
                self._anomaly = adapter  # type: ignore[assignment]
            else:
                self._forecasts.append(adapter)  # type: ignore[arg-type]

            state.available = True
            state.reason = None
            return state

        state.add_check("artifact_present", False, f"No artifact of kind '{kind.value}' found.")
        state.reason = (
            f"No {kind.value} artifact has been packaged yet. Run the offline "
            f"preparation script to produce one under {self._settings.artifacts_dir}."
        )
        return state

    def _build_adapter(
        self, kind: ArtifactKind, manifest: ArtifactManifest, directory: Path
    ) -> tuple[object | None, str | None]:
        """Deserialise an artifact into an adapter.

        Deserialisation is deliberately restricted to trusted local files
        produced by this project's own offline scripts.
        """
        try:
            if kind is ArtifactKind.FORECAST:
                from sih26170.prediction.baseline import load_forecast_adapter

                return load_forecast_adapter(manifest, directory), None
            from sih26170.prediction.anomaly_adapter import load_anomaly_adapter

            return load_anomaly_adapter(manifest, directory), None
        except ImportError as exc:
            return None, f"A library required to load this artifact is not installed: {exc.name}."
        except Exception as exc:
            logger.warning("Adapter load failed for %s: %s", directory.name, type(exc).__name__)
            return None, f"Artifact could not be loaded ({type(exc).__name__})."

    def _inference_probe(
        self, kind: ArtifactKind, adapter: object, manifest: ArtifactManifest
    ) -> tuple[bool, str | None]:
        """Run one tiny prediction so readiness reflects real usability."""
        probe = pd.DataFrame(
            [{name: 0.0 for name in manifest.feature_order}],
            columns=manifest.feature_order,
        )
        probe.insert(0, "component_id", "__probe__")
        probe.insert(1, "batch_id", "__probe__")
        probe.insert(2, "component_family", "__probe__")
        probe.insert(3, "measurement_name", "__probe__")
        try:
            if kind is ArtifactKind.FORECAST:
                outputs = adapter.predict(probe)  # type: ignore[attr-defined]
            else:
                outputs = adapter.score(probe)  # type: ignore[attr-defined]
        except Exception as exc:
            return False, f"Inference probe failed ({type(exc).__name__})."
        if not outputs:
            return False, "Inference probe returned no result."
        return True, None

    # -- accessors ---------------------------------------------------------

    @property
    def core_status(self) -> CoreStatus:
        if self._core_status is None:
            self._core_status = probe_core()
        return self._core_status

    @property
    def anomaly_state(self) -> CapabilityState:
        return self._anomaly_state

    @property
    def forecast_state(self) -> CapabilityState:
        return self._forecast_state

    @property
    def mlcc_engine(self) -> MlccEngine | None:
        """The loaded MLCC prototype bundle, or None when unavailable."""
        return self._mlcc

    @property
    def anomaly_adapter(self) -> AnomalyAdapter | None:
        return self._anomaly

    def forecast_adapter_for(self, profile_id: str) -> ForecastAdapter | None:
        for adapter in self._forecasts:
            if adapter.supports_profile(profile_id):
                return adapter
        return None

    def supports_intervals(self, profile_id: str | None = None) -> bool:
        adapters = (
            [a for a in self._forecasts if profile_id is None or a.supports_profile(profile_id)]
        )
        return any(a.supports_intervals for a in adapters)

    def supports_explanations(self, profile_id: str | None = None) -> bool:
        adapters = (
            [a for a in self._forecasts if profile_id is None or a.supports_profile(profile_id)]
        )
        return any(a.supports_explanations for a in adapters)

    @property
    def model_versions(self) -> dict[str, str | None]:
        return {
            "anomaly": self._anomaly_state.model_version,
            "forecast": self._forecast_state.model_version,
        }

    @property
    def supported_profile_ids(self) -> tuple[str, ...]:
        return self._mlcc.identity.supported_profiles if self._mlcc else ()

    def is_ready(self) -> tuple[bool, list[str]]:
        """Readiness for the configured mode, plus that mode's limitations."""
        limitations: list[str] = []
        if self._settings.mode is ServiceMode.DEMO:
            ready = self._anomaly_state.available and self._forecast_state.available
            return ready, limitations

        limitations.append(
            "Running in anomaly_only development mode: no 168 h forecast, no "
            "prediction intervals and no forecast explanations are produced. "
            "Recommendations are provisional and based on early-window anomaly "
            "evidence alone. This mode must not be used for the demonstration."
        )
        return self._anomaly_state.available, limitations

    # -- dependency injection for tests ------------------------------------

    def _install_test_adapters(
        self,
        *,
        anomaly: AnomalyAdapter | None = None,
        forecast: ForecastAdapter | None = None,
        core_status: CoreStatus | None = None,
    ) -> None:
        """Install adapters directly. FOR TESTS ONLY.

        The production path is artifact loading in ``load()``. This entry point
        exists so API behaviour can be tested before real artifacts exist; it is
        never called from request handling.
        """
        self._loaded = True
        if core_status is not None:
            self._core_status = core_status
        if anomaly is not None:
            self._anomaly = anomaly
            self._anomaly_state = CapabilityState(
                "anomaly",
                available=True,
                artifact_id="test-double",
                model_version=anomaly.model_version,
            )
        if forecast is not None:
            self._forecasts = [forecast]
            self._forecast_state = CapabilityState(
                "forecast",
                available=True,
                artifact_id="test-double",
                model_version=forecast.model_version,
            )
