"""Artifact manifests and integrity verification.

Every artifact directory carries a ``manifest.json`` describing what the model
is, what data produced it, how the data was split, and what it measured on a
held-out set. The service refuses to load an artifact whose files do not match
the checksums in its manifest.

Metrics use ``null`` plus a stated reason when a denominator is zero, so an
empty test slice never masquerades as a perfect score.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

MANIFEST_FILENAME = "manifest.json"
MANIFEST_VERSION = "1.0.0"


class ArtifactKind(str, Enum):
    ANOMALY = "anomaly"
    FORECAST = "forecast"


class ArtifactFile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    filename: str
    sha256: str
    size_bytes: int
    role: str = Field(description="e.g. 'model', 'calibrator', 'feature_spec'.")


class DataProvenanceBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: str = Field(
        description="'synthetic' or a description of the measured dataset. Never 'verified real' unless independently confirmed."
    )
    generator: str | None = Field(
        default=None, description="Generator module/function for synthetic data."
    )
    generator_version: str | None = None
    seed: int | None = None
    dataset_sha256: str | None = Field(
        default=None, description="Hash of the exact training dataset."
    )
    component_count: int | None = None
    note: str = ""


class SplitBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    strategy: str = Field(
        default="by_batch",
        description="Train/calibration/test are separated by WHOLE batches so peers never straddle a split.",
    )
    train_batches: list[str] = Field(default_factory=list)
    calibration_batches: list[str] = Field(default_factory=list)
    test_batches: list[str] = Field(default_factory=list)
    seed: int | None = None


class MetricValue(BaseModel):
    """A metric that is allowed to be undefined, with the reason recorded."""

    model_config = ConfigDict(extra="forbid")

    value: float | None = None
    unavailable_reason: str | None = Field(
        default=None,
        description="Set when value is null, e.g. 'no limit crossings in the test split (denominator 0)'.",
    )


class ForecastMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    measurement_unit: str
    mae: MetricValue = Field(description="Mean absolute error in the measurement unit.")
    limit_normalized_mae: MetricValue = Field(
        description="MAE divided by the specification limit."
    )
    recall_limit_crossing: MetricValue = Field(
        description="Recall for components that later cross the applicable limit."
    )
    false_positive_rate: MetricValue = Field(
        description="Rate of components predicted to cross that did not."
    )
    interval_nominal_coverage: float | None = None
    interval_empirical_coverage: MetricValue = Field(
        default_factory=MetricValue,
        description="Measured coverage on the held-out test split. Compare against nominal; a gap means poor calibration.",
    )
    mean_interval_width: MetricValue = Field(default_factory=MetricValue)
    test_component_count: int = 0
    calibration_component_count: int = 0
    note: str = ""


class ArtifactManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    manifest_version: str = MANIFEST_VERSION
    artifact_id: str
    kind: ArtifactKind
    model_version: str
    created_at: datetime

    python_version: str
    library_versions: dict[str, str] = Field(default_factory=dict)

    supported_profiles: list[str]
    checkpoint_hours: list[float]
    as_of_hour: float
    target_hour: float | None = None

    feature_order: list[str] = Field(
        description="Exact column order the model expects. Order is part of the contract."
    )
    feature_schema_sha256: str = Field(
        description="Hash of the feature order plus dtypes, so a silent feature change is detectable."
    )

    data: DataProvenanceBlock
    splits: SplitBlock
    metrics: ForecastMetrics | None = None
    files: list[ArtifactFile] = Field(default_factory=list)

    supports_intervals: bool = False
    supports_explanations: bool = False
    notes: str = ""


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def feature_schema_hash(feature_order: list[str]) -> str:
    """Stable hash of the feature contract."""
    payload = json.dumps({"feature_order": feature_order}, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_manifest(directory: Path) -> ArtifactManifest:
    path = directory / MANIFEST_FILENAME
    if not path.is_file():
        raise FileNotFoundError(f"No {MANIFEST_FILENAME} in {directory}")
    return ArtifactManifest.model_validate_json(path.read_text(encoding="utf-8"))


def verify_artifact_files(
    manifest: ArtifactManifest, directory: Path
) -> list[tuple[str, bool, str | None]]:
    """Check that every declared file exists and matches its checksum."""
    checks: list[tuple[str, bool, str | None]] = []
    if not manifest.files:
        checks.append(("files_declared", False, "Manifest declares no artifact files."))
        return checks

    for declared in manifest.files:
        target = directory / declared.filename
        if not target.is_file():
            checks.append((f"file:{declared.filename}", False, "File is missing."))
            continue
        actual = sha256_file(target)
        if actual != declared.sha256:
            checks.append(
                (
                    f"checksum:{declared.filename}",
                    False,
                    "Checksum does not match the manifest.",
                )
            )
        else:
            checks.append((f"checksum:{declared.filename}", True, None))
    return checks


def verify_feature_schema(manifest: ArtifactManifest) -> tuple[str, bool, str | None]:
    expected = feature_schema_hash(manifest.feature_order)
    if expected != manifest.feature_schema_sha256:
        return (
            "feature_schema",
            False,
            "feature_schema_sha256 does not match feature_order.",
        )
    return ("feature_schema", True, None)
