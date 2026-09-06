"""CSV ingestion and API-layer validation.

This module owns everything that happens between "bytes arrived" and "a clean
long-format dataframe exists". It never logs raw measurement values.

Ordering matters and is deliberate:

  1. bytes are counted while the stream is read, so an oversized upload is
     rejected before pandas ever sees it;
  2. binary container formats are rejected by magic bytes, not by MIME header
     or file extension;
  3. the header line is inspected for duplicates before pandas silently
     de-duplicates them;
  4. every column is parsed as text so leading zeros in IDs survive, then
     numerics are converted under explicit finite checks.

The core module owns dataframe-level scientific validation. This layer is the
gate in front of it, not a replacement for it.
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from typing import BinaryIO, Iterable

import numpy as np
import pandas as pd

from sih26170.api.errors import ApiError, ErrorCode, ErrorDetail, payload_too_large
from sih26170.api.profiles import DataProvenance, classify_provenance

# --------------------------------------------------------------------------
# Column contract (preserved from the core input format)
# --------------------------------------------------------------------------

REQUIRED_COLUMNS: tuple[str, ...] = (
    "component_id",
    "batch_id",
    "component_family",
    "hours",
    "measurement_name",
    "measurement_value",
    "upper_limit",
)

#: Optional columns the core already recognises.
CORE_OPTIONAL_COLUMNS: tuple[str, ...] = (
    "lower_limit",
    "temperature_c",
    "humidity_pct",
    "test_condition",
    "data_source",
)

#: Additional metadata accepted at the API/profile layer only. These are
#: carried through to the response for presentation and compatibility checks.
#: They are NEVER passed into feature building.
API_OPTIONAL_COLUMNS: tuple[str, ...] = (
    "measurement_unit",
    "part_number",
    "applied_voltage_v",
    "board_position",
)

OPTIONAL_NUMERIC_COLUMNS: tuple[str, ...] = (
    "lower_limit",
    "temperature_c",
    "humidity_pct",
    "applied_voltage_v",
)

STRING_ID_COLUMNS: tuple[str, ...] = (
    "component_id",
    "batch_id",
    "component_family",
    "measurement_name",
)

#: Columns that must never reach a predictive feature vector, because they
#: leak the answer or identify the row rather than describing early behaviour.
LEAKAGE_COLUMNS: frozenset[str] = frozenset(
    {
        "component_id",
        "batch_id",
        "scenario",
        "scenario_label",
        "will_fail",
        "future_failure",
        "failed",
        "final_value",
        "final_measurement_value",
        "outcome",
        "label",
        "true_label",
        "target",
    }
)

#: The identity of one measurement history.
HISTORY_KEY: tuple[str, ...] = (
    "component_id",
    "batch_id",
    "component_family",
    "measurement_name",
)

#: Magic-byte prefixes for container formats that must not be accepted as CSV.
_BINARY_SIGNATURES: tuple[tuple[bytes, str], ...] = (
    (b"PK\x03\x04", "ZIP archive or Office/OpenDocument workbook"),
    (b"PK\x05\x06", "empty ZIP archive"),
    (b"\xd0\xcf\x11\xe0", "legacy Microsoft Office document (.xls/.doc)"),
    (b"MZ", "Windows executable"),
    (b"\x7fELF", "ELF executable"),
    (b"\x1f\x8b", "gzip archive"),
    (b"%PDF", "PDF document"),
    (b"\x89PNG", "PNG image"),
    (b"\x80\x04\x95", "Python pickle"),
    (b"\x80\x05\x95", "Python pickle"),
    (b"\x93NUMPY", "NumPy array file"),
    (b"BZh", "bzip2 archive"),
    (b"\xfd7zXZ", "xz archive"),
    (b"SQLite format", "SQLite database"),
)

_HOUR_TOLERANCE = 1e-9


# --------------------------------------------------------------------------
# Result types
# --------------------------------------------------------------------------


@dataclass
class IngestWarning:
    code: str
    message: str
    count: int | None = None


@dataclass
class IngestedDataset:
    """A validated long-format dataset plus what the API learned about it."""

    frame: pd.DataFrame
    provenance: DataProvenance
    warnings: list[IngestWarning] = field(default_factory=list)
    present_optional_columns: tuple[str, ...] = ()
    data_row_count: int = 0

    @property
    def batch_count(self) -> int:
        return int(self.frame["batch_id"].nunique())

    @property
    def unique_component_count(self) -> int:
        return int(self.frame["component_id"].nunique())

    @property
    def measurement_record_count(self) -> int:
        return int(self.frame.groupby(list(HISTORY_KEY), sort=False).ngroups)


# --------------------------------------------------------------------------
# Step 1 - bounded read
# --------------------------------------------------------------------------


def read_bounded(stream: BinaryIO, max_bytes: int, chunk_size: int = 64 * 1024) -> bytes:
    """Read at most ``max_bytes`` from ``stream``, failing if more remain.

    The bound is enforced during reading. One byte past the limit is enough to
    stop; the whole payload is never materialised beyond the cap.
    """
    buffer = bytearray()
    while True:
        chunk = stream.read(chunk_size)
        if not chunk:
            break
        buffer.extend(chunk)
        if len(buffer) > max_bytes:
            raise payload_too_large(
                f"Upload exceeds the {max_bytes // (1024 * 1024)} MB limit.",
                details=[
                    ErrorDetail(
                        code=ErrorCode.FILE_TOO_LARGE,
                        message=(
                            f"Reading stopped after {len(buffer)} bytes, which is past "
                            f"the {max_bytes}-byte cap."
                        ),
                    )
                ],
            )
    return bytes(buffer)


# --------------------------------------------------------------------------
# Step 2 - content sniffing and decoding
# --------------------------------------------------------------------------


def reject_binary_payload(raw: bytes) -> None:
    head = raw[:16]
    for signature, label in _BINARY_SIGNATURES:
        if raw.startswith(signature):
            raise ApiError(
                ErrorCode.UNSUPPORTED_FILE_TYPE,
                f"The upload looks like a {label}, not a CSV file.",
                http_status=415,
            )
    if b"\x00" in head:
        raise ApiError(
            ErrorCode.UNSUPPORTED_FILE_TYPE,
            "The upload contains NUL bytes and is not a text CSV file.",
            http_status=415,
        )


def decode_text(raw: bytes) -> tuple[str, list[IngestWarning]]:
    """Decode CSV bytes, preferring UTF-8 and tolerating Excel's cp1252.

    Content is validated rather than trusting the browser's Content-Type, so an
    upload sent as application/vnd.ms-excel but containing UTF-8 CSV is fine.
    """
    warnings: list[IngestWarning] = []
    for encoding, note in (
        ("utf-8-sig", None),
        ("utf-8", None),
        ("cp1252", "cp1252"),
    ):
        try:
            text = raw.decode(encoding)
        except UnicodeDecodeError:
            continue
        if note:
            warnings.append(
                IngestWarning(
                    code="NON_UTF8_ENCODING",
                    message=(
                        "The file was not valid UTF-8 and was decoded as cp1252 "
                        "(typical of an Excel export). Check that unit symbols "
                        "read correctly."
                    ),
                )
            )
        return text, warnings

    raise ApiError(
        ErrorCode.ENCODING_INVALID,
        "The file could not be decoded as UTF-8 or cp1252 text.",
    )


def check_header(text: str) -> list[str]:
    """Return header names, rejecting duplicates before pandas renames them."""
    first_line = text.split("\n", 1)[0].strip("\r")
    if not first_line.strip():
        raise ApiError(ErrorCode.FILE_EMPTY, "The file has no header row.")

    header = next(csv.reader([first_line]))
    header = [h.strip() for h in header]

    seen: dict[str, int] = {}
    duplicates: list[ErrorDetail] = []
    for index, name in enumerate(header):
        if name in seen:
            duplicates.append(
                ErrorDetail(
                    code=ErrorCode.DUPLICATE_HEADER,
                    message=(
                        f"Column '{name}' appears more than once "
                        f"(positions {seen[name] + 1} and {index + 1})."
                    ),
                    row=1,
                    column=name,
                )
            )
        else:
            seen[name] = index

    if duplicates:
        raise ApiError(
            ErrorCode.DUPLICATE_HEADER,
            "The header row contains duplicate column names.",
            details=duplicates,
        )
    return header


def check_required_columns(header: Iterable[str]) -> None:
    present = set(header)
    missing = [c for c in REQUIRED_COLUMNS if c not in present]
    if missing:
        raise ApiError(
            ErrorCode.MISSING_REQUIRED_COLUMNS,
            "The file is missing required columns: " + ", ".join(missing),
            details=[
                ErrorDetail(
                    code=ErrorCode.MISSING_REQUIRED_COLUMNS,
                    message=f"Required column '{name}' is absent.",
                    row=1,
                    column=name,
                )
                for name in missing
            ],
        )


# --------------------------------------------------------------------------
# Step 3 - parse and validate values
# --------------------------------------------------------------------------


def _line_number(positional_index: int) -> int:
    """Map a 0-based dataframe row to a 1-based CSV line including the header."""
    return positional_index + 2


def _parse_float_column(
    frame: pd.DataFrame,
    column: str,
    *,
    required: bool,
    errors: list[ErrorDetail],
) -> pd.Series:
    """Convert a text column to float, recording per-row problems.

    Empty cells are missing. ``inf``/``nan`` text and unparseable text are both
    rejected: a burn-in measurement is never legitimately non-finite.
    """
    raw = frame[column].fillna("").astype(str).str.strip()

    # Vectorised conversion first; the per-row loop below runs only over the
    # cells that actually failed, so a clean file costs one pass.
    values = pd.to_numeric(raw, errors="coerce")
    empty = raw == ""
    unparseable = values.isna() & ~empty
    non_finite = np.isinf(values.to_numpy(dtype="float64", na_value=0.0))

    if required:
        for position in np.flatnonzero(empty.to_numpy()):
            errors.append(
                ErrorDetail(
                    code=ErrorCode.NON_FINITE_VALUE,
                    message=f"Required numeric column '{column}' is empty.",
                    row=_line_number(int(position)),
                    column=column,
                )
            )

    bad_code = ErrorCode.NON_FINITE_VALUE if required else ErrorCode.INVALID_OPTIONAL_FIELD
    for position in np.flatnonzero(unparseable.to_numpy()):
        errors.append(
            ErrorDetail(
                code=bad_code,
                message=f"Column '{column}' contains a value that is not a number.",
                row=_line_number(int(position)),
                column=column,
            )
        )

    for position in np.flatnonzero(non_finite):
        errors.append(
            ErrorDetail(
                code=ErrorCode.NON_FINITE_VALUE,
                message=(
                    f"Column '{column}' contains a non-finite value "
                    "(infinity or NaN), which is not a valid measurement."
                ),
                row=_line_number(int(position)),
                column=column,
            )
        )

    return values.astype("float64").mask(non_finite)


def _validate_identity_strings(frame: pd.DataFrame, errors: list[ErrorDetail]) -> None:
    for column in STRING_ID_COLUMNS:
        blanks = frame.index[frame[column].str.strip() == ""]
        for label in blanks:
            errors.append(
                ErrorDetail(
                    code=ErrorCode.AMBIGUOUS_COMPONENT_IDENTITY,
                    message=f"Identity column '{column}' is empty.",
                    row=_line_number(int(frame.index.get_loc(label))),
                    column=column,
                )
            )


def _validate_component_id_uniqueness(
    frame: pd.DataFrame, errors: list[ErrorDetail]
) -> None:
    """Require each component_id to belong to exactly one batch and family.

    The core joins peers by batch, family and measurement. Reusing one
    component_id across batches or families cannot be resolved safely without
    changing the core, so for this pilot the API requires globally unique
    component IDs within an upload and says so explicitly. This constraint is
    documented in docs/backend/API_CONTRACT.md.
    """
    counts = frame.groupby("component_id", sort=False)[
        ["batch_id", "component_family"]
    ].nunique()
    offenders = counts.index[(counts["batch_id"] > 1) | (counts["component_family"] > 1)]

    for component_id in offenders:
        block = frame.loc[frame["component_id"] == component_id]
        batches = sorted(set(block["batch_id"]))
        families = sorted(set(block["component_family"]))
        errors.append(
            ErrorDetail(
                code=ErrorCode.AMBIGUOUS_COMPONENT_IDENTITY,
                message=(
                    f"component_id '{component_id}' appears under more than one "
                    f"batch_id ({', '.join(batches)}) or component_family "
                    f"({', '.join(families)}). This pilot requires component IDs "
                    "to be unique within an upload."
                ),
                column="component_id",
                value=str(component_id),
            )
        )


def _validate_hours(frame: pd.DataFrame, errors: list[ErrorDetail]) -> None:
    hours = frame["hours"].to_numpy(dtype="float64", na_value=np.nan)
    # NaN compares false, so rows already reported by the numeric parser are skipped.
    for position in np.flatnonzero(hours < 0):
        errors.append(
            ErrorDetail(
                code=ErrorCode.INVALID_HOURS,
                message="Column 'hours' must not be negative.",
                row=_line_number(int(position)),
                column="hours",
                value=str(hours[position]),
            )
        )


def _validate_limits(frame: pd.DataFrame, errors: list[ErrorDetail]) -> None:
    if "lower_limit" not in frame.columns:
        return
    both = frame[["upper_limit", "lower_limit"]].dropna()
    bad = both[both["lower_limit"] >= both["upper_limit"]]
    for label in bad.index:
        errors.append(
            ErrorDetail(
                code=ErrorCode.INVALID_LIMIT,
                message="lower_limit must be strictly below upper_limit.",
                row=_line_number(int(frame.index.get_loc(label))),
                column="lower_limit",
            )
        )


def _validate_duplicate_identities(
    frame: pd.DataFrame, errors: list[ErrorDetail]
) -> None:
    key = list(HISTORY_KEY) + ["hours"]
    duplicated = frame.duplicated(subset=key, keep=False)
    if not duplicated.any():
        return
    offenders = frame.loc[duplicated, key]
    for label, row in offenders.iterrows():
        errors.append(
            ErrorDetail(
                code=ErrorCode.DUPLICATE_MEASUREMENT_IDENTITY,
                message=(
                    "More than one row describes the same component, measurement "
                    f"and hour ({row['component_id']} / {row['measurement_name']} "
                    f"at {row['hours']} h)."
                ),
                row=_line_number(int(frame.index.get_loc(label))),
                column="hours",
            )
        )


def _validate_stable_limits(frame: pd.DataFrame, errors: list[ErrorDetail]) -> None:
    """A single history must be screened against a single specification."""
    limit_columns = ["upper_limit"] + (
        ["lower_limit"] if "lower_limit" in frame.columns else []
    )
    # One vectorised nunique per limit column instead of a Python loop over
    # every history, which dominated runtime on large uploads.
    counts = frame.groupby(list(HISTORY_KEY), sort=False)[limit_columns].nunique()
    for column in limit_columns:
        for key in counts.index[counts[column] > 1]:
            component_id, _, _, measurement_name = key
            errors.append(
                ErrorDetail(
                    code=ErrorCode.LIMIT_CHANGED_WITHIN_HISTORY,
                    message=(
                        f"Column '{column}' changes within the history of "
                        f"component '{component_id}' / measurement "
                        f"'{measurement_name}'. A history must have one "
                        "specification limit."
                    ),
                    column=column,
                )
            )


# --------------------------------------------------------------------------
# Public entry point
# --------------------------------------------------------------------------


def ingest_csv(
    raw: bytes,
    *,
    max_data_rows: int,
) -> IngestedDataset:
    """Validate raw CSV bytes and return a clean long-format dataset."""
    if not raw.strip():
        raise ApiError(ErrorCode.FILE_EMPTY, "The uploaded file is empty.")

    reject_binary_payload(raw)
    text, warnings = decode_text(raw)

    header = check_header(text)
    check_required_columns(header)

    try:
        frame = pd.read_csv(
            io.StringIO(text),
            dtype=str,            # every column as text: leading zeros survive
            keep_default_na=False,  # "NA" in an ID column stays the string "NA"
            na_values=[],
            skip_blank_lines=True,
        )
    except pd.errors.EmptyDataError as exc:
        raise ApiError(ErrorCode.FILE_EMPTY, "The uploaded file has no data rows.") from exc
    except pd.errors.ParserError as exc:
        raise ApiError(
            ErrorCode.CSV_PARSE_FAILED,
            "The file could not be parsed as CSV. Check for unbalanced quotes "
            "or an inconsistent number of fields.",
            details=[
                ErrorDetail(
                    code=ErrorCode.CSV_PARSE_FAILED,
                    message=str(exc).splitlines()[0][:200],
                )
            ],
        ) from exc

    frame.columns = [str(c).strip() for c in frame.columns]

    if len(frame) == 0:
        raise ApiError(ErrorCode.FILE_EMPTY, "The uploaded file has a header but no data rows.")

    if len(frame) > max_data_rows:
        raise payload_too_large(
            f"The file contains {len(frame)} data rows, above the "
            f"{max_data_rows}-row limit.",
            details=[
                ErrorDetail(
                    code=ErrorCode.TOO_MANY_ROWS,
                    message=f"Row limit is {max_data_rows}.",
                )
            ],
        )

    frame = frame.reset_index(drop=True)
    data_row_count = len(frame)

    # Identity columns stay text so leading zeros are preserved verbatim.
    for column in STRING_ID_COLUMNS:
        frame[column] = frame[column].fillna("").astype(str).str.strip()

    errors: list[ErrorDetail] = []
    _validate_identity_strings(frame, errors)

    frame["hours"] = _parse_float_column(frame, "hours", required=True, errors=errors)
    frame["measurement_value"] = _parse_float_column(
        frame, "measurement_value", required=True, errors=errors
    )
    frame["upper_limit"] = _parse_float_column(
        frame, "upper_limit", required=True, errors=errors
    )

    present_optional: list[str] = []
    for column in CORE_OPTIONAL_COLUMNS + API_OPTIONAL_COLUMNS:
        if column not in frame.columns:
            continue
        present_optional.append(column)
        if column in OPTIONAL_NUMERIC_COLUMNS:
            frame[column] = _parse_float_column(
                frame, column, required=False, errors=errors
            )
        else:
            frame[column] = frame[column].fillna("").astype(str).str.strip()

    # Value-level problems are fatal; stop before the structural checks so the
    # caller gets the root cause rather than downstream noise.
    if errors:
        raise ApiError(
            ErrorCode.NON_FINITE_VALUE if any(
                e.code == ErrorCode.NON_FINITE_VALUE for e in errors
            ) else errors[0].code,
            "The file contains invalid values.",
            details=errors[:50],
        )

    _validate_hours(frame, errors)
    _validate_limits(frame, errors)
    _validate_duplicate_identities(frame, errors)
    _validate_stable_limits(frame, errors)
    _validate_component_id_uniqueness(frame, errors)

    if errors:
        raise ApiError(errors[0].code, "The file failed validation.", details=errors[:50])

    provenance = classify_provenance(
        set(frame["data_source"]) if "data_source" in frame.columns else set()
    )

    return IngestedDataset(
        frame=frame,
        provenance=provenance,
        warnings=warnings,
        present_optional_columns=tuple(present_optional),
        data_row_count=data_row_count,
    )


# --------------------------------------------------------------------------
# Checkpoint isolation
# --------------------------------------------------------------------------


def split_early_and_future(
    frame: pd.DataFrame,
    *,
    checkpoint_hours: Iterable[float],
    as_of_hour: float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split into the exact early checkpoints and everything after the cutoff.

    The early frame contains ONLY the requested checkpoint hours. Intermediate
    readings a richer generator may provide (6 h, 12 h) are deliberately
    excluded so the 0/24 h claim is literally true of what the model consumed.

    The future frame is evaluation-only and must never reach feature building.
    """
    targets = list(checkpoint_hours)
    hours = frame["hours"]

    on_checkpoint = pd.Series(False, index=frame.index)
    for target in targets:
        on_checkpoint |= (hours - target).abs() < _HOUR_TOLERANCE

    early = frame.loc[on_checkpoint].copy()
    future = frame.loc[hours > as_of_hour + _HOUR_TOLERANCE].copy()
    return early, future


def strip_leakage_columns(frame: pd.DataFrame) -> pd.DataFrame:
    """Drop identifier and outcome columns before any modelling step."""
    drop = [c for c in frame.columns if c.casefold() in LEAKAGE_COLUMNS]
    return frame.drop(columns=drop, errors="ignore")


# --------------------------------------------------------------------------
# Optional outcome file (evaluation only)
# --------------------------------------------------------------------------

#: An outcome file describes what happened AFTER the cutoff. It carries no
#: specification limits on purpose: comparison limits are taken from the
#: validated early input, so an outcome file can never move the goalposts.
OUTCOME_REQUIRED_COLUMNS: tuple[str, ...] = (
    "component_id",
    "batch_id",
    "component_family",
    "hours",
    "measurement_name",
    "measurement_value",
)

#: Limit columns are dropped from an outcome file rather than trusted.
OUTCOME_IGNORED_COLUMNS: tuple[str, ...] = ("upper_limit", "lower_limit")


def ingest_outcome_csv(raw: bytes, *, max_data_rows: int) -> IngestedDataset:
    """Validate a separate outcome CSV of post-cutoff observations.

    Deliberately NOT the same contract as the early file:
      * ``upper_limit``/``lower_limit`` are not required, and are dropped if
        present, so a later file cannot change what a component is judged
        against;
      * everything else - byte bounds, binary sniffing, encoding, duplicate
        headers, finite numerics, text-preserved identities - is identical.

    Identity membership and the "strictly after the cutoff" rule are checked by
    the caller, which is the only place that knows the early input.
    """
    if not raw.strip():
        raise ApiError(ErrorCode.FILE_EMPTY, "The outcome file is empty.")

    reject_binary_payload(raw)
    text, warnings = decode_text(raw)

    header = check_header(text)
    missing = [c for c in OUTCOME_REQUIRED_COLUMNS if c not in set(header)]
    if missing:
        raise ApiError(
            ErrorCode.MISSING_REQUIRED_COLUMNS,
            "The outcome file is missing required columns: " + ", ".join(missing),
            details=[
                ErrorDetail(
                    code=ErrorCode.MISSING_REQUIRED_COLUMNS,
                    message=f"Required column '{name}' is absent from the outcome file.",
                    row=1,
                    column=name,
                )
                for name in missing
            ],
        )

    try:
        frame = pd.read_csv(
            io.StringIO(text),
            dtype=str,
            keep_default_na=False,
            na_values=[],
            skip_blank_lines=True,
        )
    except pd.errors.EmptyDataError as exc:
        raise ApiError(
            ErrorCode.FILE_EMPTY, "The outcome file has no data rows."
        ) from exc
    except pd.errors.ParserError as exc:
        raise ApiError(
            ErrorCode.CSV_PARSE_FAILED,
            "The outcome file could not be parsed as CSV.",
            details=[
                ErrorDetail(
                    code=ErrorCode.CSV_PARSE_FAILED,
                    message=str(exc).splitlines()[0][:200],
                )
            ],
        ) from exc

    frame.columns = [str(c).strip() for c in frame.columns]

    if len(frame) == 0:
        raise ApiError(
            ErrorCode.FILE_EMPTY, "The outcome file has a header but no data rows."
        )
    if len(frame) > max_data_rows:
        raise payload_too_large(
            f"The outcome file contains {len(frame)} data rows, above the "
            f"{max_data_rows}-row limit.",
            details=[
                ErrorDetail(
                    code=ErrorCode.TOO_MANY_ROWS, message=f"Row limit is {max_data_rows}."
                )
            ],
        )

    frame = frame.reset_index(drop=True)
    data_row_count = len(frame)

    dropped = [c for c in OUTCOME_IGNORED_COLUMNS if c in frame.columns]
    if dropped:
        frame = frame.drop(columns=dropped)
        warnings.append(
            IngestWarning(
                code="OUTCOME_LIMITS_IGNORED",
                message=(
                    "The outcome file supplied "
                    + ", ".join(dropped)
                    + ". Those columns were ignored: comparison limits are taken "
                    "from the validated early input so that a later file cannot "
                    "change what a component is judged against."
                ),
                count=len(dropped),
            )
        )

    for column in STRING_ID_COLUMNS:
        frame[column] = frame[column].fillna("").astype(str).str.strip()

    errors: list[ErrorDetail] = []
    _validate_identity_strings(frame, errors)
    frame["hours"] = _parse_float_column(frame, "hours", required=True, errors=errors)
    frame["measurement_value"] = _parse_float_column(
        frame, "measurement_value", required=True, errors=errors
    )
    for column in ("temperature_c", "humidity_pct"):
        if column in frame.columns:
            frame[column] = _parse_float_column(
                frame, column, required=False, errors=errors
            )

    if errors:
        raise ApiError(
            ErrorCode.NON_FINITE_VALUE,
            "The outcome file contains invalid values.",
            details=errors[:50],
        )

    return IngestedDataset(
        frame=frame,
        provenance=classify_provenance(
            set(frame["data_source"]) if "data_source" in frame.columns else set()
        ),
        warnings=warnings,
        data_row_count=data_row_count,
    )
