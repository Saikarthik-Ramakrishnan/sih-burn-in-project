"""Structured API errors.

Rules enforced here:
  * Every failure carries a stable machine-readable ``code``.
  * ``row`` / ``column`` are populated only when this layer actually computed
    them. A dataset-level failure raised by the core never gets a fabricated
    row number - it reports ``row=None`` and says so in the message.
  * Server tracebacks never reach the response body.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from fastapi import Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field


class ErrorCode(str, Enum):
    # --- transport / file level (413, 415, 422) ---
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    FILE_EMPTY = "FILE_EMPTY"
    UNSUPPORTED_FILE_TYPE = "UNSUPPORTED_FILE_TYPE"
    ENCODING_INVALID = "ENCODING_INVALID"
    CSV_PARSE_FAILED = "CSV_PARSE_FAILED"
    TOO_MANY_ROWS = "TOO_MANY_ROWS"

    # --- schema level ---
    MISSING_REQUIRED_COLUMNS = "MISSING_REQUIRED_COLUMNS"
    DUPLICATE_HEADER = "DUPLICATE_HEADER"

    # --- value level ---
    NON_FINITE_VALUE = "NON_FINITE_VALUE"
    INVALID_HOURS = "INVALID_HOURS"
    INVALID_LIMIT = "INVALID_LIMIT"
    INVALID_OPTIONAL_FIELD = "INVALID_OPTIONAL_FIELD"
    LIMIT_CHANGED_WITHIN_HISTORY = "LIMIT_CHANGED_WITHIN_HISTORY"
    DUPLICATE_MEASUREMENT_IDENTITY = "DUPLICATE_MEASUREMENT_IDENTITY"
    AMBIGUOUS_COMPONENT_IDENTITY = "AMBIGUOUS_COMPONENT_IDENTITY"

    # --- profile / compatibility level ---
    UNSUPPORTED_PROFILE = "UNSUPPORTED_PROFILE"
    INCOMPATIBLE_UNITS = "INCOMPATIBLE_UNITS"
    INCOMPATIBLE_TEST_CONDITIONS = "INCOMPATIBLE_TEST_CONDITIONS"
    UNSUPPORTED_AS_OF_HOUR = "UNSUPPORTED_AS_OF_HOUR"

    # --- eligibility level ---
    NO_ELIGIBLE_HISTORIES = "NO_ELIGIBLE_HISTORIES"

    # --- capability level (503) ---
    ANOMALY_MODEL_UNAVAILABLE = "ANOMALY_MODEL_UNAVAILABLE"
    FORECAST_MODEL_UNAVAILABLE = "FORECAST_MODEL_UNAVAILABLE"
    CORE_UNAVAILABLE = "CORE_UNAVAILABLE"
    SERVICE_NOT_READY = "SERVICE_NOT_READY"

    NOT_FOUND = "NOT_FOUND"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class ErrorDetail(BaseModel):
    """One specific problem inside an upload.

    ``row`` is the 1-based line number in the submitted CSV *including* the
    header line, so the first data row is ``2``. It is null whenever the
    problem is dataset-level rather than row-level.
    """

    code: ErrorCode
    message: str
    row: int | None = None
    column: str | None = None
    value: str | None = Field(
        default=None,
        description=(
            "Offending value as text, included only for schema/identity fields. "
            "Raw measurement values are never echoed back."
        ),
    )


class ErrorResponse(BaseModel):
    error: ErrorCode
    message: str
    request_id: str | None = None
    details: list[ErrorDetail] = Field(default_factory=list)


class ApiError(Exception):
    """Raised anywhere in the request path to produce a structured response."""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        *,
        http_status: int = status.HTTP_422_UNPROCESSABLE_CONTENT,
        details: list[ErrorDetail] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.http_status = http_status
        self.details = details or []

    def to_response(self, request_id: str | None = None) -> JSONResponse:
        payload = ErrorResponse(
            error=self.code,
            message=self.message,
            request_id=request_id,
            details=self.details,
        )
        return JSONResponse(
            status_code=self.http_status,
            content=payload.model_dump(mode="json"),
        )


def payload_too_large(message: str, **kw: Any) -> ApiError:
    return ApiError(
        ErrorCode.FILE_TOO_LARGE,
        message,
        http_status=status.HTTP_413_CONTENT_TOO_LARGE,
        **kw,
    )


def unavailable(code: ErrorCode, message: str, **kw: Any) -> ApiError:
    return ApiError(
        code, message, http_status=status.HTTP_503_SERVICE_UNAVAILABLE, **kw
    )


async def api_error_handler(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, ApiError)
    return exc.to_response(getattr(request.state, "request_id", None))


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Last resort. The traceback is logged by the server, never returned."""
    payload = ErrorResponse(
        error=ErrorCode.INTERNAL_ERROR,
        message="An internal error occurred while processing the request.",
        request_id=getattr(request.state, "request_id", None),
    )
    return JSONResponse(status_code=500, content=payload.model_dump(mode="json"))
