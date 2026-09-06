# SIH26170 — early anomaly detection for component burn-in

Burn-in runs electronic parts hot and under voltage for a week and checks whether they drift out of spec. This project reads only the first two measurements of that week (0 h and 24 h), spots parts that behave oddly next to their batch mates, and forecasts where each part's leakage current will be at 168 h. It ships as a Python core, a FastAPI backend, and a React dashboard.

The pilot covers one part family: X7R multilayer ceramic capacitors, leakage current in µA. Every dataset in this repository is synthetic. The numbers here demonstrate that the pipeline works; they are not evidence of field accuracy.

## What it does

- **Anomaly screening.** A median/MAD baseline plus an Isolation Forest compare each part with comparable peers in the same batch, so a part can be flagged while still inside its limit.
- **Forecasting.** `xgboost_v2` predicts the 168 h leakage from the 0/24 h readings. It learns a correction on top of "the value stays where it is" with an absolute-error objective, which is why it beats persistence where the earlier squared-error model did not (normalized MAE 0.136 vs 0.153 on untouched test batches).
- **Calibrated uncertainty.** Each forecast carries a stratified prediction interval and a one-sided 90% upper bound that drives the MONITOR decision.
- **Explanations and honesty flags.** TreeSHAP contributions for the active forecast, explicit unscored records, and warnings whenever a number should not be read at face value.

## Repository layout

| Path | What lives there |
|---|---|
| `src/sih26170/` | Shared core: validation, features, anomaly detector, decision rules, the MLCC prototype and the `forecast_v2` experiment runner |
| `src/sih26170/api/`, `src/sih26170/prediction/` | FastAPI backend: ingestion, response contract, bundle loading |
| `outputs/mlcc_v2/model_bundle/` | The release bundle the backend loads (`mlcc-pilot-1.1`) |
| `outputs/mlcc_v1/` | Synthetic datasets (train / calibration / test / stress / demo) and the earlier v1 bundle |
| `outputs/claude_forecast_v2/` | Forecasting experiment: predeclared comparison, diagnostics, out-of-fold forecasts |
| `outputs/codex_ml_v2_review/` | Independent evaluation of the v2 candidate on test, fresh and stress batches |
| `my-app/` | React + Vite dashboard |
| `tests/` | 273 tests across core, forecasting and API |

## Quick start

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]" "xgboost==3.4.1" "skops==0.13.0"
pytest tests -q
uvicorn sih26170.api.main:app --port 8000
```

Then open `http://127.0.0.1:8000/api/v1/docs`, or upload `outputs/mlcc_v1/demo_early.csv`:

```bash
curl -F "file=@outputs/mlcc_v1/demo_early.csv;type=text/csv" http://127.0.0.1:8000/api/v1/screen
```

On macOS, XGBoost needs `brew install libomp`. The dashboard runs separately with `cd my-app && npm install && npm run dev`.

## Documentation

Start here and work deeper:

| Document | Description |
|---|---|
| [Running the backend](docs/backend/RUNNING.md) | Install, environment variables, start the server, request examples |
| [API contract](docs/backend/API_CONTRACT.md) | Endpoints, request and response fields, how to read every number without misleading a judge |
| [Backend status](docs/backend/STATUS.md) | What is verified, measured performance, known limitations, files changed |
| [Integration requests](docs/backend/INTEGRATION_REQUESTS.md) | Open questions between the backend and the core, and what has been resolved |
| [v2 bundle: start here](outputs/mlcc_v2/START_HERE.md) | What the release bundle contains, how it was trained, test-set results |
| [Forecasting v2 handoff](docs/CLAUDE_FORECAST_V2_HANDOFF.md) | Why persistence beat v1, the predeclared experiment, interval design, integration notes |
| [Forecasting diagnostics](outputs/claude_forecast_v2/DIAGNOSTICS.md) | Six analyses of what 0/24 h readings can and cannot predict |
| [Cross-validated comparison](outputs/claude_forecast_v2/COMPARISON.md) | Twelve configurations on whole-batch folds, per fold, profile, stratum and scenario |
| [v1 bundle: start here](outputs/mlcc_v1/START_HERE.md) | The first prototype, who received which pack, honest first results |
| [Data dictionary](outputs/mlcc_v1/DATA_DICTIONARY.md) | Every column in the synthetic datasets and how it may be used |
| [Sources and assumptions](outputs/mlcc_v1/SOURCES_AND_ASSUMPTIONS.md) | What the generator assumes, which public data was checked, what is not claimed |
| [Evaluation notes](docs/evaluation_notes.md) | How held-out batches and time sweeps are evaluated, and how to quote a metric |
| [Stress-testing harness](docs/evaluation_notes_harness.md) | Fixed-limit vs robust vs Isolation Forest, and how much warning each buys |
| [Technical lead plan](docs/technical_lead_plan.md) | Scope, milestones and ownership across the team |
| [Cleaned training integration](outputs/cleaned_training_integration/README.md) | How the teammates' cleaned data and feature mappings were verified against the core |
| [Dashboard field dictionary](my-app/docs/dashboardAdapterFieldDictionary.md) | Which response fields the dashboard binds to and how to display them |
| [Dashboard app](my-app/README.md) | React + Vite setup for the frontend |

Handoff prompts and team briefs live in `outputs/*.md` and `outputs/mlcc_v1/handoffs/`.

## Validation

```bash
pytest tests -q
python scripts/compare_api_vs_core.py outputs/mlcc_v1/demo_early.csv
```

The first runs the full suite; the second pushes the same CSV through the HTTP API and through the core directly and exits non-zero if any of twelve per-component fields disagree.
