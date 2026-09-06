# Leakage Lens: one image, one process. Stage 1 builds the dashboard, stage 2
# serves the API and the built dashboard from uvicorn on port 8000.

# ---- stage 1: dashboard -----------------------------------------------------
FROM node:22-alpine AS frontend
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# ---- stage 2: backend + model -----------------------------------------------
FROM python:3.12-slim AS runtime
# XGBoost needs OpenMP at runtime.
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 curl \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

COPY requirements-docker.txt ./
RUN pip install -r requirements-docker.txt

COPY pyproject.toml README.md ./
COPY src/ ./src/
RUN pip install --no-deps -e .

# Release bundle plus the two demo CSVs the sample endpoint serves. Training
# data, stress sets and experiment outputs stay out of the image.
COPY outputs/mlcc_v2/model_bundle/ ./outputs/mlcc_v2/model_bundle/
COPY outputs/mlcc_v1/demo_early.csv outputs/mlcc_v1/demo_outcomes.csv ./outputs/mlcc_v1/
COPY --from=frontend /build/dist ./frontend/dist

ENV SIH_MODE=demo \
    SIH_MLCC_BUNDLE_DIR=/app/outputs/mlcc_v2/model_bundle \
    SIH_FRONTEND_DIST_DIR=/app/frontend/dist \
    SIH_CORS_ALLOW_ORIGINS=""

EXPOSE 8000
# Readiness = checksums, library versions, bundle load and an inference probe.
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8000/api/v1/health/ready > /dev/null || exit 1

RUN useradd --create-home --uid 1000 app && chown -R app:app /app
USER app
CMD ["uvicorn", "sih26170.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
