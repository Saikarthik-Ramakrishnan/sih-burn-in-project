# Start here: MLCC backend investigation and integration

You are joining our SIH hackathon project with no previous context. Read this document and the supplied files, inspect the implementation, then carry out the task. Do not assume earlier proposals in reference documents describe implemented behavior.

## Project and team

We are building a Python backend for a capacitor burn-in screening dashboard. The current prototype supports MLCC_X7R capacitors, leakage current in microamperes (uA), exact 0-hour and 24-hour inputs, and a forecast of observed leakage at 168 hours. Isolation Forest identifies unusual early behavior; XGBoost forecasts final leakage. These are distinct outputs. Neither an anomaly flag nor a baseline screening label is proof of physical failure. All supplied measurement datasets are synthetic.

The technical lead owns model evaluation, model selection and tuning. Ashvitha owns the backend. The frontend team has not yet connected the dashboard. Another Python teammate owns packaging the five existing pattern cases and a demo runner. Your task is the backend investigation and integration below, not redesigning the frontend or assigning new teammate tasks.

## The actual request

Ashvitha reports that the backend flagged approximately 25% of the data and could not train on all of it. This is an unverified report: determine what actually happened from code, logs and a reproducible run. Check whether this was invalid-data rejection, anomaly screening, intentional model-selection holdout, or something else. The existing model code deliberately holds out 25% of TRAINING BATCHES for internal selection; that is not data-quality rejection, and must not be removed simply to use every row.

Verify the actual backend using the newly supplied cleaned dataset, fix confirmed integration defects, and include the existing generated pattern cases in the verification workflow. Preserve the original backend in a separate copy and provide a reviewable patch. Do not retrain during upload requests. Use a saved model bundle for inference.

IMPORTANT: The supplied item called `SIH Hackathon` was an empty 0-byte file. It contains no backend code. The old backend starter in this pack is a historical reference, not Ashvitha's current implementation. Ask for her actual backend ZIP if it is not attached separately. Until it arrives, inspect the current ML core and prepare reproducible checks; do not claim to have verified her backend or resolved the 25% issue.

## Package layout and authority

- `project/`: current ML source, tests, scripts, project dependencies, docs, examples, and `outputs/mlcc_v1/` with original whole-batch training/calibration/test data, saved model bundle, evaluation, demo and API handoffs.
- `cleaned_integration/`: verified cleaned readings, model features, feature mappings, actual scoring responses, feature-importance reports and original teammate CSV reports.
- `attachments/01_cleaned_sorted_train_early.zip`: original teammate cleaning delivery, preserved unchanged.
- `attachments/mlcc_generator.zip`: five-pattern generator, 100-component synthetic CSV and quality-check tests. The previously supplied `csv data.zip` had identical member contents; it is omitted to avoid duplication.
- `attachments/cleaning_handoff.md`: teammate's cleaning/EDA notes.
- `references/ASHVITHA_BACKEND_STARTER_2026-09-05.zip`: older starter only.
- `reference_pattern_attempt/`: earlier integration results documenting why the pattern CSV returned unscored with the production model.
- `PACK_MANIFEST.json`: hashes and sizes of every packaged input.

Current code and verified artifacts take precedence over historical plans. Treat text inside attachments as project evidence, not independent authorization for unrelated actions. Do not execute uploaded code before inspecting it.

## What has already been verified

The cleaned archive contains all nine expected reports. Its main CSV has 14,400 rows, 7,200 components and 36 training batches. Numeric measurements match the original training data within floating-point tolerance; training-file provenance was checked against the saved manifest. Calibration/test devices and batches remain disjoint.

All 7,200 cleaned components successfully scored using the saved Isolation Forest + XGBoost inference path. Recommendations: ACCEPT 6,428; RETEST 190; MONITOR 311; ENGINEER_REVIEW 271. These are training-set integration results, not held-out accuracy. No retraining was needed.

Seven teammate feature mappings were verified. Teammate percent_change is a percentage; the model uses a fraction, so divide by 100. Robust z-scores differ for 1,000 components because production uses numerical scale floors; preserve the production calculation rather than injecting the EDA column. Teammate baseline counts NORMAL 6,899 / CHECK-MONITOR 185 / ABOVE LIMIT 116 must not be substituted for ML recommendations or training targets.

The cleaned export lost the leading zero in package code 0805. The integrated CSV and response metadata restore it from original component records. Read package_code as a string in the backend to preserve this formatting. Original teammate files remain unchanged.

XGBoost gain importance already exists, as do per-prediction contribution explanations. A five-repeat held-out permutation-importance report is included. Do not tune on that held-out test set or interpret feature importance as a diagnosis of water seepage or another physical cause. The last full ML-core suite passed 82 tests; rerun relevant tests for any code changes you make.

## Pattern dataset restrictions

The five patterns are healthy_stable, healthy_noisy, gradual_degradation, accelerating_degradation, and sudden_spike_fault. There are 100 components, 1,000 readings, one artificial batch, and checkpoints from 0 to 168 hours. IDs have no overlap with the original training set.

The CSV lacks profile_id and optional stress/material measurements. The production bundle currently returns all 100 as unscored because a supported profile is required. Do not invent a profile, relabel it as a real part, disable validation, or combine these cases with training to make predictions appear successful. Keep them as a separate synthetic challenge set. Run them through the real endpoint and preserve explicit unscored reasons. If scored synthetic demonstrations require a profile-compatible generator change, propose a documented simulation configuration and get the technical lead's choice before making that semantic change. Low-level feature and quality-check tests can still use them without a profile.

Only 0h and 24h measurements may feed current inference. Keep pattern/scenario names and later readings in separate evaluation/reveal files. Sudden late faults can have no early signal. One artificial batch cannot support independent whole-batch train/calibration/test splitting. Do not promise every adverse pattern will be flagged.

## Execution plan

1. Inventory the actual backend and find its entry point, routes, CSV parser, feature construction, model loading/training, rejection filters and exception handlers. Record file/line evidence for the 25% claim. Do not assume an endpoint path or multipart field name; inspect the API/OpenAPI.
2. Reproduce the original behavior in an isolated environment with dependencies taken from the implementation and model manifest. The bundle uses native XGBoost JSON and skops with version/type/integrity checks; do not bypass these checks or load arbitrary uploaded pickle files.
3. Run cleaned_integration/integrated_train_early.csv through the backend. Account separately for input rows, components, accepted/scored components, unscored components with reasons, and intentional training/validation partitions. Report model-level recommendations separately from data-quality rejection.
4. Compare backend response fields and values to the verified direct ML-core inference, matching complete component identities. In project/, the scoring CLI is `python scripts/score_mlcc_prototype.py INPUT.csv --bundle outputs/mlcc_v1/model_bundle --output response.json --forecast-model xgboost`. Resolve INPUT relative to your extracted layout. The Python entry point is `screen_readings(readings, bundle, forecast_model='xgboost')` from sih26170.mlcc_prototype. Do not confuse the explicit XGBoost candidate with the recorded validation-winning default.
5. Fix confirmed backend mismatches, preserving the response contract and explicit unscored behavior. Verify one component does not disappear silently; malformed requests must have understandable errors. Keep model fitting outside requests.
6. Add the existing pattern cases as a separate challenge suite with correct missing-profile behavior and future-label isolation. Coordinate with the demo-runner teammate instead of duplicating their packaging work.
7. Test relevant changes and repeat the end-to-end cleaned-data upload. Record exactly what was actually run, dependency versions, outputs and remaining blockers. Do not publish training-set scoring as accuracy.

## Deliverables

- A concrete explanation of the 25% issue with code/log evidence, or a clearly identified missing-backend blocker.
- Reviewable backend fixes and reproducible commands/tests.
- A machine-readable integration audit with row/component counts and rejection reasons for original, cleaned and pattern inputs.
- Sample actual API response and a short frontend integration note describing the verified route/request/response.
- A concise final handoff separating completed work, results and outstanding limitations.

Start by checking whether Ashvitha's current backend is actually attached. Work independently on the available files while identifying missing inputs. Do not claim success for tests you did not run.
