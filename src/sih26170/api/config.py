"""Runtime configuration for the SIH26170 backend.

Owned by the backend workstream (Ashvitha). Nothing here changes core
anomaly thresholds, shared feature definitions or decision semantics.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

# Version of the JSON response envelope. The frontend pins against this.
# Bump only on a breaking field change; additive fields do not bump it.
SCHEMA_VERSION = "1.0.0"


def _service_version() -> str:
    """Version of the installed distribution.

    Read from package metadata rather than a `__version__` attribute, because
    the core package's ``__init__`` does not define one and this layer must not
    modify it.
    """
    from importlib.metadata import PackageNotFoundError, version

    for distribution in ("sih26170-anomaly-core", "sih26170"):
        try:
            return version(distribution)
        except PackageNotFoundError:
            continue
    return "0.0.0+unknown"


SERVICE_VERSION = _service_version()

API_PREFIX = "/api/v1"

# Repository root, derived from this file: src/sih26170/api/config.py -> up 4.
PROJECT_ROOT = Path(__file__).resolve().parents[3]


class ServiceMode(str, Enum):
    """Which capabilities the process is required to provide.

    DEMO is what runs in front of judges: both anomaly and forecast artifacts
    must load and pass an inference probe or /health/ready returns 503.

    ANOMALY_ONLY is an explicitly configured development mode. It is allowed to
    start without a forecast artifact, but it must advertise that limitation in
    every readiness and capability payload. It is never the default.
    """

    DEMO = "demo"
    ANOMALY_ONLY = "anomaly_only"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SIH_",
        env_file=".env",
        extra="ignore",
    )

    mode: ServiceMode = ServiceMode.DEMO

    artifacts_dir: Path = PROJECT_ROOT / "artifacts"
    #: The v2 bundle (mlcc-pilot-1.1) adds the xgboost_v2 forecaster, which won
    #: internal validation and the untouched test batches; the v1 bundle under
    #: outputs/mlcc_v1/model_bundle still loads and can be selected with
    #: SIH_MLCC_BUNDLE_DIR for comparison.
    mlcc_bundle_dir: Path = PROJECT_ROOT / "outputs" / "mlcc_v2" / "model_bundle"

    #: Forecast model requested from the bundle. None uses the artifact's own
    #: internal-validation winner (xgboost_v2 in the v2 bundle); the response
    #: always reports which model actually ran.
    forecast_model: str | None = None
    frontend_dist_dir: Path = PROJECT_ROOT / "frontend" / "dist"

    # Ingestion bounds. The byte bound is enforced while reading the stream,
    # before any pandas parsing happens.
    max_upload_bytes: int = Field(default=10 * 1024 * 1024, gt=0)
    max_data_rows: int = Field(default=100_000, gt=0)

    # The only screening mode validated for SIH: readings at 0 h and 24 h are
    # used to screen and to forecast the 168 h measurement.
    default_as_of_hour: float = 24.0
    required_checkpoint_hours: tuple[float, ...] = (0.0, 24.0)
    default_target_hour: float = 168.0

    # Below this many comparable peers, batch-relative statistics are reported
    # as unavailable rather than presented as reliable batch anomaly detection.
    min_peer_group_size: int = 8

    # Uploaded measurement values are never written to logs.
    log_level: str = "INFO"

    # --- browser access -------------------------------------------------
    #: Origins allowed to call the API from a browser, as a comma-separated
    #: list in SIH_CORS_ALLOW_ORIGINS. The defaults are the usual local Vite
    #: dev servers. In the packaged demo the SPA is served by this same
    #: process, so it is same-origin and needs none of this.
    #:
    #: "*" is deliberately NOT a default. Set it explicitly if you really want
    #: it; credentials are never enabled, so a wildcard cannot leak cookies,
    #: but an explicit list is still the right habit.
    #: NoDecode stops pydantic-settings JSON-decoding the env value before the
    #: validator below sees it, so a plain comma-separated string works.
    cors_allow_origins: Annotated[tuple[str, ...], NoDecode] = (
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    )

    @field_validator("cors_allow_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        """Accept "a,b" from the environment as well as a real list."""
        if isinstance(value, str):
            return tuple(part.strip() for part in value.split(",") if part.strip())
        return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
