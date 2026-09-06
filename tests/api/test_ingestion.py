"""Ingestion and validation tests."""

from __future__ import annotations

import io
import math

import pytest

from sih26170.api.errors import ApiError, ErrorCode
from sih26170.api.ingestion import (
    HISTORY_KEY,
    ingest_csv,
    read_bounded,
    split_early_and_future,
    strip_leakage_columns,
)
from sih26170.api.profiles import DataProvenance

from .conftest import burn_in_rows, make_csv

MAX_ROWS = 100_000


def ingest(raw: bytes, max_data_rows: int = MAX_ROWS):
    return ingest_csv(raw, max_data_rows=max_data_rows)


# --------------------------------------------------------------------------
# Bounded reading
# --------------------------------------------------------------------------


def test_read_bounded_accepts_payload_at_limit():
    payload = b"x" * 1000
    assert read_bounded(io.BytesIO(payload), max_bytes=1000) == payload


def test_read_bounded_rejects_before_full_materialisation():
    """The cap is enforced during reading, not after loading everything."""
    payload = b"y" * (5 * 1024 * 1024)
    with pytest.raises(ApiError) as excinfo:
        read_bounded(io.BytesIO(payload), max_bytes=1024, chunk_size=256)
    assert excinfo.value.code is ErrorCode.FILE_TOO_LARGE
    assert excinfo.value.http_status == 413


# --------------------------------------------------------------------------
# File-level rejection
# --------------------------------------------------------------------------


def test_empty_file_rejected():
    with pytest.raises(ApiError) as excinfo:
        ingest(b"")
    assert excinfo.value.code is ErrorCode.FILE_EMPTY


def test_header_only_file_rejected():
    with pytest.raises(ApiError) as excinfo:
        ingest(make_csv([]))
    assert excinfo.value.code is ErrorCode.FILE_EMPTY


@pytest.mark.parametrize(
    "payload",
    [
        b"PK\x03\x04rest of an xlsx",
        b"\xd0\xcf\x11\xe0legacy xls",
        b"MZ\x90\x00executable",
        b"%PDF-1.7",
        b"\x80\x04\x95pickled model",
        b"\x1f\x8bgzip",
    ],
)
def test_binary_containers_rejected_by_magic_bytes(payload: bytes):
    with pytest.raises(ApiError) as excinfo:
        ingest(payload)
    assert excinfo.value.code is ErrorCode.UNSUPPORTED_FILE_TYPE
    assert excinfo.value.http_status == 415


def test_row_limit_enforced():
    rows = burn_in_rows(n_components=6)
    with pytest.raises(ApiError) as excinfo:
        ingest(make_csv(rows), max_data_rows=5)
    assert excinfo.value.code is ErrorCode.FILE_TOO_LARGE
    assert excinfo.value.http_status == 413


# --------------------------------------------------------------------------
# Schema-level rejection
# --------------------------------------------------------------------------


def test_missing_required_columns_named_individually():
    rows = burn_in_rows(n_components=2)
    for row in rows:
        del row["upper_limit"]
    with pytest.raises(ApiError) as excinfo:
        ingest(make_csv(rows))
    assert excinfo.value.code is ErrorCode.MISSING_REQUIRED_COLUMNS
    assert {d.column for d in excinfo.value.details} == {"upper_limit"}


def test_duplicate_header_rejected():
    body = (
        "component_id,batch_id,component_family,hours,measurement_name,"
        "measurement_value,upper_limit,upper_limit\n"
        "C0001,B-001,Digital IC,0,leakage_ua,1.0,10.0,11.0\n"
    )
    with pytest.raises(ApiError) as excinfo:
        ingest(body.encode())
    assert excinfo.value.code is ErrorCode.DUPLICATE_HEADER
    assert excinfo.value.details[0].column == "upper_limit"


# --------------------------------------------------------------------------
# Value-level rejection
# --------------------------------------------------------------------------


@pytest.mark.parametrize("bad", ["inf", "-inf", "nan", "Infinity", "NaN"])
def test_non_finite_measurement_rejected(bad: str):
    rows = burn_in_rows(n_components=2)
    rows[1]["measurement_value"] = bad
    with pytest.raises(ApiError) as excinfo:
        ingest(make_csv(rows))
    assert excinfo.value.code is ErrorCode.NON_FINITE_VALUE
    assert excinfo.value.details[0].column == "measurement_value"


def test_non_numeric_measurement_rejected_with_row_number():
    rows = burn_in_rows(n_components=2)
    rows[2]["measurement_value"] = "not-a-number"
    with pytest.raises(ApiError) as excinfo:
        ingest(make_csv(rows))
    detail = excinfo.value.details[0]
    # header is line 1, data rows start at line 2, so rows[2] is line 4
    assert detail.row == 4
    assert detail.column == "measurement_value"


def test_negative_hours_rejected():
    rows = burn_in_rows(n_components=2)
    rows[0]["hours"] = -1
    with pytest.raises(ApiError) as excinfo:
        ingest(make_csv(rows))
    assert excinfo.value.code is ErrorCode.INVALID_HOURS


def test_lower_limit_above_upper_limit_rejected():
    rows = burn_in_rows(n_components=2, extra={"lower_limit": 99.0})
    with pytest.raises(ApiError) as excinfo:
        ingest(make_csv(rows))
    assert excinfo.value.code is ErrorCode.INVALID_LIMIT


def test_invalid_optional_numeric_rejected():
    rows = burn_in_rows(n_components=2, extra={"temperature_c": "hot"})
    with pytest.raises(ApiError) as excinfo:
        ingest(make_csv(rows))
    assert excinfo.value.code is ErrorCode.INVALID_OPTIONAL_FIELD


def test_duplicate_measurement_identity_rejected():
    rows = burn_in_rows(n_components=2)
    rows.append(dict(rows[0]))
    with pytest.raises(ApiError) as excinfo:
        ingest(make_csv(rows))
    assert excinfo.value.code is ErrorCode.DUPLICATE_MEASUREMENT_IDENTITY


def test_limit_changing_within_history_rejected():
    rows = burn_in_rows(n_components=2)
    rows[1]["upper_limit"] = 20.0  # same component, different hour
    with pytest.raises(ApiError) as excinfo:
        ingest(make_csv(rows))
    assert excinfo.value.code is ErrorCode.LIMIT_CHANGED_WITHIN_HISTORY


def test_component_id_reused_across_batches_rejected():
    rows = burn_in_rows(n_components=2, batch_id="B-001")
    rows += burn_in_rows(n_components=2, batch_id="B-002")
    with pytest.raises(ApiError) as excinfo:
        ingest(make_csv(rows))
    assert excinfo.value.code is ErrorCode.AMBIGUOUS_COMPONENT_IDENTITY


# --------------------------------------------------------------------------
# Successful ingestion
# --------------------------------------------------------------------------


def test_valid_file_ingests_with_expected_shape(valid_csv_bytes: bytes):
    dataset = ingest(valid_csv_bytes)
    assert dataset.batch_count == 1
    assert dataset.unique_component_count == 12
    assert dataset.measurement_record_count == 12
    assert dataset.data_row_count == 24
    assert list(dataset.frame.columns)[:7] == [
        "component_id",
        "batch_id",
        "component_family",
        "hours",
        "measurement_name",
        "measurement_value",
        "upper_limit",
    ]


def test_leading_zero_ids_preserved():
    rows = burn_in_rows(n_components=3, id_prefix="", id_width=6)
    dataset = ingest(make_csv(rows))
    ids = sorted(set(dataset.frame["component_id"]))
    assert ids == ["000000", "000001", "000002"]
    # Assert the behaviour, not the internal dtype: pandas 2 stores text columns
    # as `object` and pandas 3 as StringDtype, but both must keep the leading
    # zeros and hand back real Python strings.
    assert all(isinstance(value, str) for value in dataset.frame["component_id"])


def test_batch_ids_that_look_numeric_stay_strings():
    rows = burn_in_rows(n_components=2, batch_id="00420")
    dataset = ingest(make_csv(rows))
    assert set(dataset.frame["batch_id"]) == {"00420"}


def test_utf8_bom_accepted():
    raw = b"\xef\xbb\xbf" + make_csv(burn_in_rows(n_components=2))
    dataset = ingest(raw)
    assert dataset.unique_component_count == 2


def test_cp1252_decoded_with_warning():
    rows = burn_in_rows(n_components=2, extra={"test_condition": "125\xb0C"})
    raw = make_csv(rows).decode("utf-8").encode("cp1252")
    dataset = ingest(raw)
    assert any(w.code == "NON_UTF8_ENCODING" for w in dataset.warnings)


# --------------------------------------------------------------------------
# Provenance
# --------------------------------------------------------------------------


def test_absent_data_source_is_unknown_not_verified(valid_csv_bytes: bytes):
    assert ingest(valid_csv_bytes).provenance is DataProvenance.UNKNOWN


def test_synthetic_marker_detected():
    rows = burn_in_rows(n_components=2, extra={"data_source": "synthetic_v3"})
    assert ingest(make_csv(rows)).provenance is DataProvenance.SYNTHETIC


def test_synthetic_marker_not_upgraded_by_a_real_claim():
    rows = burn_in_rows(n_components=2, extra={"data_source": "synthetic_v3"})
    rows += burn_in_rows(
        n_components=2, id_prefix="R", extra={"data_source": "lab_bench_2026"}
    )
    assert ingest(make_csv(rows)).provenance is DataProvenance.MIXED


def test_uploader_claim_is_unverified_not_verified():
    rows = burn_in_rows(n_components=2, extra={"data_source": "verified_real_hardware"})
    # The word "verified" in an uploaded cell must not produce a verified status.
    assert ingest(make_csv(rows)).provenance is DataProvenance.MEASURED_UNVERIFIED


# --------------------------------------------------------------------------
# Checkpoint isolation and leakage
# --------------------------------------------------------------------------


def test_split_selects_exact_checkpoints_only():
    """6 h and 12 h readings must not slip into the 0/24 h early window."""
    rows = burn_in_rows(n_components=3, hours=(0.0, 6.0, 12.0, 24.0, 168.0))
    dataset = ingest(make_csv(rows))
    early, future = split_early_and_future(
        dataset.frame, checkpoint_hours=(0.0, 24.0), as_of_hour=24.0
    )
    assert sorted(set(early["hours"])) == [0.0, 24.0]
    assert sorted(set(future["hours"])) == [168.0]
    assert len(early) == 6


def test_split_excludes_the_cutoff_hour_from_future():
    rows = burn_in_rows(n_components=2, hours=(0.0, 24.0))
    dataset = ingest(make_csv(rows))
    _, future = split_early_and_future(
        dataset.frame, checkpoint_hours=(0.0, 24.0), as_of_hour=24.0
    )
    assert future.empty


def test_strip_leakage_columns_removes_outcome_and_identifier_fields():
    rows = burn_in_rows(n_components=2)
    dataset = ingest(make_csv(rows))
    frame = dataset.frame.copy()
    frame["scenario"] = "degrading"
    frame["will_fail"] = "1"
    frame["final_value"] = "9.9"
    stripped = strip_leakage_columns(frame)
    for column in ("scenario", "will_fail", "final_value", "component_id", "batch_id"):
        assert column not in stripped.columns
    assert "measurement_value" in stripped.columns


def test_history_key_is_the_full_identity():
    assert HISTORY_KEY == (
        "component_id",
        "batch_id",
        "component_family",
        "measurement_name",
    )
