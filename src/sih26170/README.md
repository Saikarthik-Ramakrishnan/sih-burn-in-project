# Core package `sih26170`

The science lives here; the API only calls it.

| Module | Role |
|---|---|
| `validation.py`, `features.py` | Reject bad input, then turn the 0 h and 24 h readings of each part into leakage-safe features, including robust z-scores against batch peers |
| `anomaly.py`, `decision.py` | Median/MAD baseline plus Isolation Forest, and the ACCEPT / MONITOR / RETEST / ENGINEER_REVIEW rule |
| `mlcc_prototype.py` | The MLCC bundle: training (`train_bundle`), loading (`load_bundle`) and frozen inference (`screen_readings`). Holds the `xgboost_v2` forecaster and its stratified interval |
| `forecast_v2.py` | The whole-batch experiment runner that produced `xgboost_v2`, plus a standalone frozen candidate |
| `api/`, `prediction/` | FastAPI backend and the bundle adapter (see `docs/backend/README.md`) |

Rules that every module keeps: only 0 h and 24 h observations reach a model, labels join on the four identity columns, whole batches stay together in every split, and every request runs inference only.

```python
from sih26170.mlcc_prototype import load_bundle, screen_readings
bundle = load_bundle("outputs/mlcc_v2/model_bundle")
result = screen_readings(readings, bundle)        # readings: long-format DataFrame, IDs as str
```

Tests: `pytest tests -q`. Background reading: `docs/evaluation_notes.md`, `docs/evaluation_notes_harness.md`, `docs/CLAUDE_FORECAST_V2_HANDOFF.md`.
