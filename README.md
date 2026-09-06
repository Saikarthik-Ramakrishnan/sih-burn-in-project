# SIH26170: early anomaly detection for component burn-in

Burn-in screening for electronic components: parts are held at elevated temperature and voltage for 168 h and measured at fixed checkpoints. This system uses the 0 h and 24 h leakage-current readings to (1) detect components that are drifting differently from the rest of their batch and (2) forecast the 168 h leakage with a calibrated prediction interval. Components are ranked into ACCEPT, MONITOR, RETEST or ENGINEER_REVIEW.

The pilot targets X7R ceramic capacitors, measuring leakage current in µA. All training and test data are synthetic. On held-out test batches the forecaster predicts the 168 h leakage with a mean error of 13.6 % of the part's limit, compared with 15.3 % for simply carrying the 24 h reading forward. Performance on measured hardware is still to be validated.

Stack: Python 3.12 core (numpy, pandas, scikit-learn, XGBoost), FastAPI backend, React + Vite dashboard.

## About the Project

Input: a long-format CSV with one row per component per checkpoint (identity columns, `hours`, `measurement_value`, `upper_limit`, `profile_id`).

Processing, per upload:

1. Validate the file and keep exactly the 0 h and 24 h rows per component.
2. Build features: level, change, slope, fraction of limit, and robust z-scores against the other parts in the same batch.
3. Anomaly score: median/MAD baseline combined with an Isolation Forest.
4. Forecast: `xgboost_v2` predicts the 168 h value as a correction on top of the 24 h value, with a stratified conformal interval and a one-sided 90 % upper bound.
5. Decision: the shared rule turns anomaly flag, forecast and upper bound into one recommendation per part, with reason codes and TreeSHAP contributions.

Output: one JSON record per component plus unscored records, decision counts and warnings. Models are trained offline and loaded once at startup; a request runs inference only.

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
