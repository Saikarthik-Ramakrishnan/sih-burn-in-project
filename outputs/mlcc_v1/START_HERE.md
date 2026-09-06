# MLCC prototype v1 — start here

The synthetic dataset, trained model bundle and local CSV-to-result prototype
are ready. This is the ML engine for Ashvitha's backend and the designer's UI;
it does not include their separate FastAPI or frontend implementation.

## What is included

- 12,000 fictional capacitors in 60 batches: 120,000 full-history readings.
- Four X7R part profiles, all explicitly fictional.
- 7,200 training, 2,400 calibration and 2,400 test components, split by whole batch.
- Two separate stress sets: 2,000 rare-mechanism components and 2,000 components
  under shifted conditions, adding 40,000 readings.
- A fixed 800-component demo from four test batches, chosen without model/label
  inspection. Its early input has 1,600 rows; later measurements are separate.
- Saved Isolation Forest, XGBoost and baseline models, calibration state,
  version/checksum manifest, tests, source and reproducible commands.

All data and benchmark results are synthetic. Read `SOURCES_AND_ASSUMPTIONS.md`
and `DATA_DICTIONARY.md` before interpreting patterns. No measured Kaggle rows
were augmented or relabelled as MLCC observations.

## Who receives what

| Recipient | Archive | Assignment |
|---|---|---|
| Python teammate 1 | MLCC_TEAMMATE_1_PATTERN_PACK.zip | Blind training-data quality and exploratory analysis; no labels or ML |
| Python teammate 2 | MLCC_TEAMMATE_2_PATTERN_PACK.zip | Blind observations first, then labelled training audit and simple statistical rules; no ML |
| Ashvitha | MLCC_PROTOTYPE_AND_BACKEND_HANDOFF.zip | Integrate the supplied model into her existing API; preserve her backend work |
| Frontend team | MLCC_FRONTEND_HANDOFF.zip | Use demo CSV and generated response to bind UI; use Ashvitha's actual HTTP contract |
| Karthik | MLCC_COMPLETE_SYNTHETIC_DATASET.zip and full prototype pack | Own generator, model evaluation and the next model version |

Each teammate pack contains a Claude prompt. They can extract it, open Claude
Code in that folder and paste the prompt. A chat-only Claude must be given the
files and must distinguish generated instructions from code it actually ran.

Do not send the complete dataset/model archive to the two exploration teammates.
Their packs intentionally omit calibration/test data and final model metrics.

## Run the existing demo on Karthik's machine

From the project root:

```bash
.venv/bin/python scripts/score_mlcc_prototype.py outputs/mlcc_v1/demo_early.csv --forecast-model xgboost --future-outcomes outputs/mlcc_v1/demo_outcomes.csv --output outputs/mlcc_v1/demo_response.json
```

This loads saved models and produces actual JSON results. It does not train.
Omit `--future-outcomes` for an early-only run with no recorded outcome reveal.
The response contains `metadata`, `summary`, `records`, and, only when supplied,
`future_outcomes` with later measured readings. Simulator truth is a separate
optional section and never a model input.

The verified run scored 800 parts with zero unscored histories. Local scoring
took approximately 2.5 seconds and model loading approximately 1 second in one
measurement. Runtime will vary by machine and load.

## Setup on a teammate's machine

Use Python 3.12. From the extracted full prototype root:

```bash
python -m venv .venv
```

Activate the environment using the appropriate command:

```bash
# macOS / Linux
source .venv/bin/activate
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Then:

```bash
python -m pip install -r outputs/mlcc_v1/requirements-prototype.lock
python -m pip install -e . --no-deps
python -m pytest
python scripts/score_mlcc_prototype.py outputs/mlcc_v1/demo_early.csv --forecast-model xgboost --output outputs/mlcc_v1/my_demo_response.json
```

On macOS, XGBoost also needs OpenMP. If its import reports a missing
`libomp.dylib`, install `libomp` using Homebrew. Karthik's machine already has
this runtime. The bundle loader checks exact Python-package versions. Preserve
Ashvitha's API environment separately until the dependency sets are integrated.

## Ashvitha's model call

```python
import pandas as pd
from sih26170.mlcc_prototype import load_bundle, screen_readings

bundle = load_bundle("outputs/mlcc_v1/model_bundle")  # once at startup
readings = pd.read_csv("outputs/mlcc_v1/demo_early.csv", dtype={
    "component_id": str, "batch_id": str,
    "component_family": str, "measurement_name": str,
})
result = screen_readings(readings, bundle, as_of_hour=24, forecast_model="xgboost")
```

The demo explicitly requests XGBoost. If `forecast_model` is omitted, the
function uses the internal-validation winner recorded in the manifest.
The response names both the active forecast model and the validation winner.
Do not label them interchangeably.

Read `handoffs/ASHVITHA_MLCC_V1_BACKEND_UPDATE.md` for the ownership change.
Ashvitha should integrate these artifacts rather than duplicate training, while
retaining any forecasting code she has already written for later comparison.

## What the model currently does

The existing robust median/MAD detector and frozen Isolation Forest supply
early anomaly evidence. XGBoost predicts normalized final leakage from an
allowlist of 0/24 h features, including available auxiliary measurements. The
prediction is converted back to microamps using the part's fictional limit.
The existing decision function combines anomaly and forecast evidence.

Native XGBoost TreeSHAP contributions explain the candidate forecast. They are
feature contributions, not diagnoses of cracks or water ingress. Derived
insulation resistance is not treated as independent evidence.

Intervals use the finite-sample split-conformal absolute-residual calculation
implemented directly in Python. MAPIE is not a runtime dependency for this
prototype. Calibration batches are separate; within-batch dependence means the
nominal 90% level is not a real-world guarantee.

## Honest first result

XGBoost did not beat the persistence baseline on average error. Persistence
simply forecasts that the 168 h reading will equal the 24 h reading. It won the
predeclared internal training-batch validation comparison. XGBoost remains
available as the explicitly requested demonstration model, with the comparison
visible in its response metadata.

On 2,400 held-out synthetic test parts:

| Measurement | Result |
|---|---|
| XGBoost normalized mean absolute error | 0.2145 of each part's leakage limit |
| Persistence normalized mean absolute error | 0.1531 of each part's leakage limit |
| XGBoost nominal 90% interval empirical coverage | 90.79% |
| Combined robust/IF + XGBoost alerts against latent final crossings, excluding tester faults | 57 caught / 138 crossings; 81 missed |
| Same alert rule's false alerts among noncrossing parts, excluding tester faults | 176 / 2,213 = 7.95% |

These results do not justify a high-accuracy or deployment-ready claim. The
prototype validates the workflow and makes weaknesses measurable. Late-onset
cases are deliberately difficult to infer from two early readings. Interval
coverage alone does not imply useful narrow intervals or good failure recall.

The rare-mechanism stress set contains only two latent final crossings. Its
recall is too uncertain for a strong conclusion. On the shifted-condition set,
false alerts increased substantially and XGBoost interval coverage fell to
85.25%. The response warns when measurements lie outside training conditions.

Next: use the teammates' training-only findings to review early observability,
loss functions, false-alert burden and auxiliary features. Freeze the next
version before evaluating new untouched batches. Do not reshape this dataset
or pick demo cases to manufacture a better score.

## Rebuild and verify

The shipped artifacts work without retraining. For an intentional regeneration:

```bash
python scripts/generate_mlcc_data.py --output-dir work/mlcc_rebuild
python scripts/train_mlcc_prototype.py --dataset-dir work/mlcc_rebuild --output-dir work/mlcc_rebuild_bundle
```

Use a new output directory to retain the original benchmark. The trainer
refuses to overwrite an existing bundle manifest.

`python scripts/verify_mlcc_release.py` verifies dataset hashes, split identities,
derived-unit relations, loaded inference, late-reading exclusion, row-order
invariance and the separate stress benchmarks. The results are saved under
`evaluation/`. It does not fit or tune a model.

Verification completed: 82 automated tests passed; the affected prototype tests
also passed after inference-order hardening. All 19 data-file hashes were
checked, and the actual 800-part demo passed the future-data and reorder checks.

## Current boundaries

- MLCC_X7R leakage in microamps, upper-limit screening, exactly 0/24 → 168 h.
- Supported fictional profiles appear in the bundle manifest. Other component
  families and lower-limit/two-sided rules are not enabled.
- Mixed part/test specifications within one batch are rejected.
- Missing/invalid histories have explicit unscored records; missing inputs are
  not silently displayed as zero predictions.
- Fewer than eight peers is marked as a weak comparison; this pilot is intended
  for whole-batch uploads. The backend should enforce its agreed minimum.
- Real hardware data and validation, final API deployment and frontend
  integration remain separate workstreams.
