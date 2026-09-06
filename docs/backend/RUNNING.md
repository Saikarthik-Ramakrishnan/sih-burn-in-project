# Running the backend

Every command below is run from the repository root
(`C:\Users\ashvi\Desktop\SIH Hackathon`) and has actually been run on this
machine. Paths use the Windows venv layout; on macOS/Linux use
`.venv/bin/python` instead of `.venv\Scripts\python.exe`.

---

## 1. Install

The MLCC bundle is deserialised with **skops** and contains an **XGBoost**
model, so the `prototype` extra is not optional for the demo — without it the
service starts but reports the model unavailable.

```bash
py -3.13 -m venv .venv
```

```bash
.venv\Scripts\python.exe -m pip install -e ".[dev]" "xgboost==3.4.1" "skops==0.13.0"
```

Verify the environment matches the artifact:

```bash
.venv\Scripts\python.exe -c "import pandas,numpy,sklearn,xgboost,skops;print(pandas.__version__,numpy.__version__,sklearn.__version__,xgboost.__version__,skops.__version__)"
```

Expected: `3.0.5 2.5.2 1.9.0 3.4.1 0.13.0` — these are the versions the bundle
was built with. `/health/ready` compares them and reports any drift.

## 2. Artifacts

No preparation step is needed. The default bundle ships in the repository at
`outputs/mlcc_v2/model_bundle/` (`manifest.json`, `state.skops`, `xgboost.json`,
`xgboost_v2.ubj`, `evaluation.json`). Every declared checksum is verified at
startup. The v1 bundle remains at `outputs/mlcc_v1/model_bundle/`.

To point at a different bundle, set `SIH_MLCC_BUNDLE_DIR`.

## 3. Tests

```bash
.venv\Scripts\python.exe -m pytest tests -q
```

Expect **273 passed** in roughly 45 s on macOS / 90 s on Windows. This includes
Karthik's core tests, the 38 `forecast_v2` tests and the API tests.

## 4. Start the server

```bash
.venv\Scripts\python.exe -m uvicorn sih26170.api.main:app --host 127.0.0.1 --port 8000
```

Then:

* API docs — <http://127.0.0.1:8000/api/v1/docs>
* Readiness — <http://127.0.0.1:8000/api/v1/health/ready> (expect `200`, `ready: true`)
* Sample CSV — <http://127.0.0.1:8000/api/v1/sample.csv>

Startup takes about **2 s** (bundle load, checksum verification, inference
probe). That cost is paid once, never per request. Add `--reload` for
development only — it re-pays startup on every code change.

One process, one worker is the intended demo deployment. There is no database,
queue or external service.

## 5. Environment settings

All variables use the `SIH_` prefix and can also live in a `.env` file at the
repository root.

| Variable | Default | Purpose |
|---|---|---|
| `SIH_MODE` | `demo` | `demo` requires anomaly **and** forecast for readiness. `anomaly_only` is a development mode that declares its limitations in every payload. |
| `SIH_MLCC_BUNDLE_DIR` | `outputs/mlcc_v2/model_bundle` | Trusted local bundle. Never accepts an uploaded model. Point it at `outputs/mlcc_v1/model_bundle` to run the v1 bundle. |
| `SIH_FORECAST_MODEL` | unset | Default forecast model. Unset uses the artifact's own internal-validation winner (`xgboost_v2` in the v2 bundle). A request's `forecast_model` field overrides it. |
| `SIH_CORS_ALLOW_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Comma-separated browser origins. Empty string disables CORS entirely. |
| `SIH_FRONTEND_DIST_DIR` | `frontend/dist` | SPA build. Served only if it exists; its absence never blocks the API. |
| `SIH_MAX_UPLOAD_BYTES` | `10485760` (10 MB) | Enforced while reading, before parsing. |
| `SIH_MAX_DATA_ROWS` | `100000` | Row cap. |
| `SIH_LOG_LEVEL` | `INFO` | Raw measurement values are never logged at any level. |

Example — serving a Vite dev frontend and forcing the XGBoost candidate:

```bash
SIH_CORS_ALLOW_ORIGINS="http://localhost:5173" SIH_FORECAST_MODEL=xgboost .venv\Scripts\python.exe -m uvicorn sih26170.api.main:app --port 8000
```

With the v2 bundle the validation winner is `xgboost_v2` (normalized MAE 0.1639
vs persistence 0.1795 on internal validation, 0.1362 vs 0.1531 on the untouched
test batches), so no model needs to be forced for the demo. Requesting `xgboost`
(the v1 candidate) or `persistence` still works; the response then carries
`selection_warning` and a `FORECAST_MODEL_NOT_VALIDATION_WINNER` warning.

## 6. Request examples

Single file:

```bash
curl -F "file=@outputs/mlcc_v1/demo_early.csv;type=text/csv" http://127.0.0.1:8000/api/v1/screen
```

With the optional outcome reveal:

```bash
curl -F "file=@early.csv;type=text/csv" -F "outcome_file=@outcomes.csv;type=text/csv" http://127.0.0.1:8000/api/v1/screen
```

Choosing a forecast model:

```bash
curl -F "file=@early.csv;type=text/csv" -F "forecast_model=xgboost" http://127.0.0.1:8000/api/v1/screen
```

Browser JavaScript: see `API_CONTRACT.md` §6, or open
`docs/backend/browser_upload_test.html` served from a different origin:

```bash
cd docs/backend && python -m http.server 5173 --bind 127.0.0.1
```

## 7. Utility scripts

```bash
.venv\Scripts\python.exe scripts/export_openapi.py
```

```bash
.venv\Scripts\python.exe scripts/demo_screen.py
```

```bash
.venv\Scripts\python.exe scripts/compare_api_vs_core.py outputs/mlcc_v1/train_early.csv
```

```bash
.venv\Scripts\python.exe scripts/export_extrapolation.py
```

```bash
.venv\Scripts\python.exe scripts/measure_inference.py
```

`compare_api_vs_core.py` takes an optional second argument naming the forecast
model, and exits non-zero on any disagreement between the API and the core, so
it is usable as a check in CI.

## 8. Docker

From the repository root:

```bash
docker compose up --build
```

`Dockerfile` is a two-stage build: `node:22-alpine` runs `npm run build` for
`frontend/`, then `python:3.12-slim` installs `requirements-docker.txt` (the
exact versions the bundle was validated with) plus `libgomp1` for XGBoost,
copies `src/`, `outputs/mlcc_v2/model_bundle/` and the two demo CSVs, and serves
everything with uvicorn on port 8000. `.dockerignore` keeps training data,
stress sets, experiment outputs and tests out of the image. The `HEALTHCHECK`
polls `/api/v1/health/ready`, so a bundle that fails a checksum or version check
marks the container unhealthy instead of serving a broken model. CORS is
disabled in the image because the dashboard is served same-origin; set
`SIH_CORS_ALLOW_ORIGINS` if a separate frontend origin needs it.
