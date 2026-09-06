# Backend

FastAPI service that validates an uploaded burn-in CSV, runs the frozen MLCC bundle once per request, and returns a typed JSON response the dashboard pins against. Models load once at startup and are never fitted or downloaded during a request.

```bash
pip install -e ".[dev]" "xgboost==3.4.1" "skops==0.13.0"
uvicorn sih26170.api.main:app --port 8000
curl -F "file=@outputs/mlcc_v1/demo_early.csv;type=text/csv" http://127.0.0.1:8000/api/v1/screen
```

Endpoints: `GET /api/v1/health/ready`, `GET /api/v1/profiles`, `POST /api/v1/screen` (optional `outcome_file` and `forecast_model`), `GET /api/v1/sample.csv`. Interactive docs at `/api/v1/docs`.

Read next:

- [RUNNING.md](RUNNING.md) — install, environment variables, scripts
- [API_CONTRACT.md](API_CONTRACT.md) — every field and how to read it honestly
- [STATUS.md](STATUS.md) — what is verified and what is not
- [INTEGRATION_REQUESTS.md](INTEGRATION_REQUESTS.md) — open questions with the core
