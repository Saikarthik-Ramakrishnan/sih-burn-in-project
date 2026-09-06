"""The screening endpoint and the synthetic sample download."""

from __future__ import annotations

import logging

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import Response

from sih26170.api.errors import ErrorResponse
from sih26170.api.ingestion import ingest_csv, ingest_outcome_csv, read_bounded
from sih26170.api.sample_data import SAMPLE_FILENAME, build_sample_csv
from sih26170.api.service_mlcc import run_mlcc_screening
from sih26170.api.schemas import ScreenResponse
from sih26170.api.service import ScreeningContext, run_screening

logger = logging.getLogger(__name__)

router = APIRouter(tags=["screening"])


@router.post(
    "/screen",
    response_model=ScreenResponse,
    summary="Screen a burn-in CSV",
    responses={
        413: {"model": ErrorResponse, "description": "Upload exceeds the size or row limit."},
        415: {"model": ErrorResponse, "description": "Payload is not a text CSV file."},
        422: {"model": ErrorResponse, "description": "The file is invalid or nothing in it is eligible."},
        503: {"model": ErrorResponse, "description": "A required model or core module is unavailable."},
    },
    description=(
        "Accepts a long-format burn-in CSV as multipart form field 'file'. "
        "Only the validated 0/24 h -> 168 h mode is supported, so as_of_hour must "
        "be 24. The file is processed in memory; raw measurement values are never "
        "logged. Histories missing a required checkpoint are returned as explicit "
        "unscored records rather than being silently dropped."
    ),
)
async def screen(
    request: Request,
    file: UploadFile = File(..., description="Long-format burn-in CSV."),
    as_of_hour: float = Form(
        default=24.0,
        description="Cutoff hour. Only 24 is validated for this pilot.",
    ),
    forecast_model: str | None = Form(
        default=None,
        description=(
            "Optional forecast model to request from the bundle. Omit to use the "
            "artifact's own internal-validation winner. The response always "
            "reports which model actually produced the forecasts, and warns when "
            "the requested one is not the validation winner."
        ),
    ),
    outcome_file: UploadFile | None = File(
        default=None,
        description=(
            "OPTIONAL second CSV of observations strictly AFTER the cutoff, for "
            "the outcome reveal. Matched to the main file on component_id, "
            "batch_id, component_family and measurement_name. Its values and any "
            "limits it carries are never used to build features, produce "
            "forecasts or change recommendations - comparison limits come from "
            "the early file. Omit it and the endpoint behaves exactly as before. "
            "This is a presentation convenience, not a blind-testing mechanism."
        ),
    ),
) -> ScreenResponse:
    settings = request.app.state.settings
    registry = request.app.state.registry

    raw = read_bounded(file.file, max_bytes=settings.max_upload_bytes)
    dataset = ingest_csv(raw, max_data_rows=settings.max_data_rows)

    # An empty multipart part arrives as an UploadFile with no filename; treat
    # that as absent so existing single-file clients are unaffected.
    outcome_dataset = None
    outcome_filename = None
    if outcome_file is not None and outcome_file.filename:
        outcome_raw = read_bounded(
            outcome_file.file, max_bytes=settings.max_upload_bytes
        )
        outcome_dataset = ingest_outcome_csv(
            outcome_raw, max_data_rows=settings.max_data_rows
        )
        outcome_filename = outcome_file.filename

    logger.info(
        "screen request %s: %d rows, %d components, %d batches",
        getattr(request.state, "request_id", "-"),
        dataset.data_row_count,
        dataset.unique_component_count,
        dataset.batch_count,
    )

    request_id = getattr(request.state, "request_id", "unknown")

    # The MLCC prototype bundle is the validated pilot path. When it is loaded
    # it owns eligibility, scoring, forecasting and the decision; this layer
    # only maps its real return object onto the response contract.
    engine = registry.mlcc_engine
    if engine is not None:
        return run_mlcc_screening(
            dataset,
            engine=engine,
            settings=settings,
            as_of_hour=as_of_hour,
            forecast_model=forecast_model or settings.forecast_model,
            request_id=request_id,
            input_source="upload",
            filename=file.filename,
            outcome_dataset=outcome_dataset,
            outcome_filename=outcome_filename,
        )

    context = ScreeningContext(
        settings=settings,
        registry=registry,
        as_of_hour=as_of_hour,
        input_source="upload",
        filename=file.filename,
        request_id=request_id,
    )
    return run_screening(dataset, context)


@router.get(
    "/sample.csv",
    response_class=Response,
    summary="Download the labelled synthetic sample CSV",
    description=(
        "A deterministic slice of the project's synthetic MLCC_X7R / leakage_ua "
        "demonstration data, with 0 h and 24 h readings plus the 168 h outcome. "
        "Every row is marked synthetic in its data_source column: it is "
        "generated data for demonstrating the pipeline, NOT measured hardware."
    ),
    responses={200: {"content": {"text/csv": {}}, "description": "Synthetic sample CSV."}},
)
def sample_csv() -> Response:
    return Response(
        content=build_sample_csv(),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{SAMPLE_FILENAME}"',
            "X-Data-Provenance": "synthetic",
        },
    )
