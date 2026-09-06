# SIH26170: early anomaly detection for component burn-in

Burn-in runs electronic parts hot and under voltage for a week. This project reads only the first two measurements (0 h and 24 h), flags parts that behave oddly next to their batch mates, and forecasts each part's leakage at 168 h with a calibrated interval. It ships as a Python core, a FastAPI backend and a React dashboard.

Pilot scope: X7R ceramic capacitors, leakage current in µA. All data are synthetic, so the results demonstrate the pipeline; field accuracy remains to be established on measured hardware. The release forecaster `xgboost_v2` reaches normalized MAE 0.136 on untouched test batches, compared with 0.153 for persistence.

## About the Project

An engineer uploads a CSV of 0 h and 24 h readings. The backend validates it, builds batch-relative features, scores each part with a median/MAD baseline and an Isolation Forest, forecasts the 168 h value with `xgboost_v2`, attaches a calibrated interval and TreeSHAP explanation, and returns one of ACCEPT, MONITOR, RETEST or ENGINEER_REVIEW per part. The dashboard renders that response. Models are trained offline from whole-batch splits and load once at startup; a request only runs inference.

## Quick start

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]" "xgboost==3.4.1" "skops==0.13.0"
pytest tests -q
uvicorn sih26170.api.main:app --port 8000
```

Upload `outputs/mlcc_v1/demo_early.csv` at `http://127.0.0.1:8000/api/v1/docs`. macOS needs `brew install libomp`.

## Documentation

Start here and work deeper:

| Document | Description |
|---|---|
| [Core package](src/sih26170/README.md) | Features, anomaly detector, decision rules, the MLCC bundle and how to call it |
| [Backend](docs/backend/README.md) | Run the API, endpoints, contract, status |
| [Model bundle](outputs/mlcc_v2/START_HERE.md) | What the release bundle contains and how it was trained and tested |
| [Datasets](outputs/mlcc_v1/README.md) | The synthetic data, its splits and column meanings |
| [Forecasting experiment](outputs/claude_forecast_v2/README.md) | Why v1 lost to persistence and how v2 was chosen |
| [Dashboard](my-app/README.md) | React + Vite front end and its field dictionary |

## Validation

```bash
pytest tests -q
python scripts/compare_api_vs_core.py outputs/mlcc_v1/demo_early.csv
```

The full suite (273 tests), then the same CSV through the HTTP API and the core directly; the second command fails on any disagreement.
