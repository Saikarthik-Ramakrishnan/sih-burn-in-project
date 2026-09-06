"""FastAPI application factory.

Startup loads trusted local artifacts exactly once. Requests never load,
download or fit a model.

Static frontend assets are served only when a build exists. Their absence must
never block backend development, and it never shadows ``/api/*``.
"""

from __future__ import annotations

import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from sih26170.api.config import (
    API_PREFIX,
    SCHEMA_VERSION,
    SERVICE_VERSION,
    Settings,
    get_settings,
)
from sih26170.api.errors import (
    ApiError,
    ErrorCode,
    ErrorResponse,
    api_error_handler,
    unhandled_error_handler,
)
from sih26170.api.routes import health, profiles, screen
from sih26170.prediction.registry import ModelRegistry

logger = logging.getLogger(__name__)

DESCRIPTION = """
Backend for SIH26170 - AI-driven anomaly detection in component burn-in and screening.

**What this service does**

* flags components that drift unusually compared with comparable peers in the
  same batch, including parts still inside the specification limit;
* where an artifact supports it, predicts the 168 h measurement from the 0 h and
  24 h readings, with an explanation and, when calibrated, an uncertainty interval.

**What the numbers are not**

* the anomaly score is a relative deviation score, not a probability of physical
  failure and not a confidence level;
* feature contributions explain model behaviour; they do not establish a physical
  cause such as water ingress or cracking;
* a nominal interval is only as good as its held-out calibration, which is
  reported per artifact rather than per record.

`percent_change` is a **fraction**: 0.1 means 10 %.
""".strip()


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings: Settings = app.state.settings

    # Reuse a registry that was already configured on the app (create_app builds
    # one; tests may install adapters into it). load() is idempotent, so an
    # already-loaded registry is left untouched rather than silently replaced.
    registry = getattr(app.state, "registry", None) or ModelRegistry(settings)
    registry.load()
    app.state.registry = registry

    logger.info(
        "startup: mode=%s anomaly=%s forecast=%s core=%s",
        settings.mode.value,
        registry.anomaly_state.available,
        registry.forecast_state.available,
        registry.core_status.available,
    )
    if not registry.anomaly_state.available:
        logger.warning("anomaly capability unavailable: %s", registry.anomaly_state.reason)
    if not registry.forecast_state.available:
        logger.warning("forecast capability unavailable: %s", registry.forecast_state.reason)

    yield


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    app = FastAPI(
        title="SIH26170 Burn-in Screening API",
        version=SERVICE_VERSION,
        description=DESCRIPTION,
        lifespan=lifespan,
        openapi_url=f"{API_PREFIX}/openapi.json",
        docs_url=f"{API_PREFIX}/docs",
        redoc_url=None,
    )
    app.state.settings = settings
    app.state.registry = ModelRegistry(settings)

    # Browser access. In the packaged demo the SPA is same-origin and this is
    # inert; it exists so the frontend can be developed against a Vite dev
    # server. Credentials are never enabled - the API has no cookies or auth -
    # so a permissive origin list cannot leak a session.
    if settings.cors_allow_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(settings.cors_allow_origins),
            allow_credentials=False,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["*"],
            # Without this the browser hides the header from fetch(), and the
            # request id is what makes a bug report traceable.
            expose_headers=["x-request-id"],
            max_age=600,
        )
        logger.info("CORS enabled for: %s", ", ".join(settings.cors_allow_origins))

    @app.middleware("http")
    async def attach_request_id(request: Request, call_next):
        request.state.request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
        response = await call_next(request)
        response.headers["x-request-id"] = request.state.request_id
        return response

    app.add_exception_handler(ApiError, api_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)

    api_routers = (health.router, profiles.router, screen.router)
    for router in api_routers:
        app.include_router(router, prefix=API_PREFIX)

    _mount_frontend(app, settings)
    return app


def _mount_frontend(app: FastAPI, settings: Settings) -> None:
    """Serve the compiled SPA when it exists, without shadowing /api/*."""
    dist = settings.frontend_dist_dir
    index = dist / "index.html"

    if not index.is_file():
        logger.info("no frontend build at %s; serving API only", dist)

        @app.get("/", include_in_schema=False)
        async def no_frontend() -> JSONResponse:
            return JSONResponse(
                {
                    "service": "sih26170-backend",
                    "version": SERVICE_VERSION,
                    "schema_version": SCHEMA_VERSION,
                    "frontend": "not built",
                    "docs": f"{API_PREFIX}/docs",
                    "openapi": f"{API_PREFIX}/openapi.json",
                }
            )

        return

    assets = dist / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    # response_model=None is required: FastAPI otherwise tries to build a
    # Pydantic response model from the FileResponse | JSONResponse union and
    # raises at app-creation time, which takes the whole service down the
    # moment a frontend build exists.
    @app.get("/{full_path:path}", include_in_schema=False, response_model=None)
    async def spa_fallback(full_path: str) -> FileResponse | JSONResponse:
        # /api/* is handled by the routers above; anything still reaching here
        # under that prefix is a genuine 404, not an SPA route.
        if full_path.startswith("api/"):
            payload = ErrorResponse(
                error=ErrorCode.NOT_FOUND,
                message=f"No API route matches /{full_path}.",
            )
            return JSONResponse(status_code=404, content=payload.model_dump(mode="json"))
        candidate = dist / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(index)


app = create_app()
