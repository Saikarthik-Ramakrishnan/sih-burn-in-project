# Ashvitha's backend handoff — SIH26170

Snapshot checked: 5 September 2026. Give Claude the accompanying source ZIP and paste the prompt below. Claude Code can work directly in the extracted folder; a chat-only Claude session should produce complete files and commands. No access to Karthik's other chats is assumed.

---

You are helping Ashvitha implement the Python backend and forecasting integration for our Smart India Hackathon project, SIH26170: AI-driven anomaly detection in component burn-in and screening. Start implementing immediately from the attached source snapshot. This is a working team project with an existing anomaly module; build on that module.

## Understand the problem and our demo

Burn-in means stressing electronic components with controlled heat and electrical conditions and recording their measurements over time. A part can remain within its approved specification yet change unusually compared with similar parts in its manufacturing batch.

We need two capabilities:
1. Identify unusual components early, including parts still inside the fixed limit.
2. Use measurements at 0 and 24 hours to predict the measurement at 168 hours, with an explanation and an uncertainty interval when supported.

Judges will watch us upload a CSV into a professional dashboard. Python must genuinely validate the file, compute early features, run the loaded models and return results during the demonstration. Training and tuning happen offline before the demonstration. Reliability, missed-failure detection, prediction error and understandable evidence matter more than decorative AI features.

The pilot is X7R multilayer ceramic capacitors (MLCCs), using leakage current as the primary signal. Later profiles: one tantalum capacitor series, precision thin-film resistors and film capacitors. They serve overlapping space, aerospace, defence and industrial electronics applications. Potential users are component-screening and reliability teams; companies discussed include KYOCERA AVX, Exxelia, Vishay, Centum and Data Patterns. These are prospective users, not customers or confirmed partners.

Keep the interface extensible, but only enable a prediction for a family/measurement/test profile covered by its artifact. Separate families need appropriate data and validation. The hackathon uses 168 h; industrial protocols can differ.

## Current verified progress: do not confuse plans with working code

The attached snapshot contains:
- `src/sih26170/validation.py`: long-format CSV dataframe validation.
- `src/sih26170/features.py`: early-window feature engineering and batch-relative statistics.
- `src/sih26170/anomaly.py`: median/MAD plus Isolation Forest anomaly detection.
- `src/sih26170/contracts.py`: `AnomalyResult` and `PredictionResult` dataclasses.
- `src/sih26170/decision.py`: recommendations and combined screening records.
- `synthetic.py`, `splitting.py`, evaluation modules, tests and examples.

The existing pytest suite passes in Karthik's environment as of this snapshot. Rerun it locally; older milestone documents contain obsolete test counts. No FastAPI application, trained forecast artifact, production anomaly artifact or frontend folder was present in the reviewed snapshot. Existing results are synthetic experiments, not validated aerospace accuracy.

The default synthetic generator currently models `Digital IC` / `leakage_ua` and `Power MOSFET` / `rds_on_mohm`. The simple example also uses Digital IC. Do not rename these records MLCC and claim real MLCC validation. They are useful for plumbing tests. A clearly labelled MLCC synthetic demonstration profile may use the existing `FamilySpec` extension without replacing the generator; record its assumptions and distinguish it from measured hardware data.

Important implementation gaps:
- `fit_score()` in the example fits on the submitted batch. That is an example, not the production inference path. Production must call `score()` on an already fitted detector.
- The feature builder uses all readings through the cutoff. For the SIH 0/24 h forecasting claim, explicitly select the 0 h and 24 h readings before feature building and model input. Do not silently use 6/12 h readings from the richer synthetic generator.
- The core may omit histories with too few early readings. The API must identify them explicitly as unscored.
- Decisions currently handle upper limits only. Accepting an optional `lower_limit` column does not implement lower-limit or two-sided screening.
- The core compares peers by batch, family and measurement; the API must prevent incompatible part specifications, test conditions or units from sharing a peer group.

## Team boundaries and synchronisation

Karthik owns the anomaly algorithm, shared feature engineering, dataset assumptions and final scientific validation. Ashvitha owns FastAPI, request/response models, CSV ingestion, model lifecycle/adapters, backend tests and the forecasting workstream, using the shared features. The designer owns frontend layout and visual identity.

Prefer new files in `src/sih26170/api/`, `src/sih26170/prediction/`, `scripts/`, `tests/api/` and `docs/backend/`. Put offline artifacts under `artifacts/` with a manifest. Dependency additions are part of your scope; avoid unrelated upgrades.

Preserve existing core interfaces. If a core change is necessary, document a minimal proposed patch and a failing regression test in `docs/backend/INTEGRATION_REQUESTS.md`; continue independent backend work. Do not silently change anomaly thresholds, shared feature definitions or decision semantics.

Keep `docs/backend/STATUS.md` updated with completed work, exact tests, supported profiles, changed files, missing artifacts and the next integration action. Produce `docs/backend/API_CONTRACT.md` and export OpenAPI early so the frontend teammate can build against stable fields.

There is no automatic synchronisation with Karthik's separate workspace/chat. Use only the files and updates actually provided. The reviewed folder was not a Git repository. If the working copy has Git, use a separate backend branch; otherwise work in a separate extracted copy and supply changed files plus a diff/change list. Never overwrite Karthik's folder wholesale.

Read, in order: this prompt; `README.md`; the six core files above; the tests; `outputs/SIH26170_TECH_STACK_LOCK.md`; `outputs/SIH26170_DESIGNER_DASHBOARD_PROMPT.md`; relevant evaluation notes. Source code determines current behaviour. This prompt determines your assignment. The newer stack document supersedes old references to Streamlit; the designer has freedom over appearance.

## Stack and runtime

Target Python 3.12, FastAPI, Pydantic v2, pandas, NumPy, scikit-learn and Uvicorn. The existing package allows Python >=3.11; test on the chosen runtime and document it. Use pytest and FastAPI TestClient/httpx for backend tests.

Forecasting plan: compare a linear baseline and scikit-learn histogram gradient boosting with XGBoost. Use MAPIE split conformal calibration for intervals when the installed, pinned version supports the selected workflow. SHAP explains a supported tree model when available. Do not force a framework over a better validated baseline. Verify library APIs in the installed versions.

The frontend is React + TypeScript + Vite, compiled and served by FastAPI. Demo production uses one local Uvicorn process/worker and bundled assets. No database, Redis, Celery, cloud inference dependency or frontend server is needed. Uploads are processed in memory. Do not log raw uploaded measurements.

Pin a reproducible dependency set after tests pass. Load trusted local artifacts once during startup; never accept model uploads or download models in a scoring request.

## Preserve these source contracts

Input is long format: one row per component, measurement and time.

Required columns:
`component_id,batch_id,component_family,hours,measurement_name,measurement_value,upper_limit`

Existing optional columns include `lower_limit,temperature_c,humidity_pct,test_condition,data_source`. IDs are strings and must preserve leading zeros. The current leakage example name is `leakage_ua` (microamps). Do not silently interpret it as nanoamps. Additional metadata such as part number, unit, applied voltage and board position can be added at the API/profile layer with documented meaning.

Stable anomaly integration:
```python
features = build_component_features(early_readings, as_of_hour=24)
scored = fitted_detector.score(features)
anomalies = fitted_detector.to_results(scored)
```

The fitting process must also preserve detector state such as `_training_strengths`, feature order and settings; saving only the Isolation Forest estimator is insufficient. Use trusted serialization with explicit allowed types and matching versions. Prefer the stack's skops format and native XGBoost JSON/UBJ where applicable.

Stable forecast result:
```python
PredictionResult(
    predicted_final_value=...,
    prediction_lower=...,
    prediction_upper=...,
    target_hour=168.0,
)
```

Use `build_screening_record(anomaly, prediction)` to combine results. Join by batch, family, component and measurement, not row order or component ID alone. Preserve `ACCEPT`, `MONITOR`, `RETEST`, `ENGINEER_REVIEW`. The anomaly score is not a probability of physical failure. If forecast/interval prerequisites are missing, do not manufacture bounds to construct `PredictionResult`; return explicit capability status, nullable forecast fields and provisional anomaly-only recommendations.

## Implement the API in this order

1. `GET /api/v1/health/live`: process is alive.
2. `GET /api/v1/health/ready`: 200 only when the configured mode's artifacts, schema, checksums and a small inference probe pass; otherwise 503 with readable capability details. Demo mode requires anomaly and forecast readiness. An explicitly configured anomaly-only development mode must identify its limitations.
3. `GET /api/v1/profiles`: available family/measurement profiles, units, supported checkpoints, target hours, limit direction and anomaly/forecast availability. Planned profiles are visibly unavailable, not working models.
4. `POST /api/v1/screen`: multipart `file`, default `as_of_hour=24`; initially support only the validated 0/24 → 168 h mode. Validate, isolate early data, compute features, score, predict, combine and return typed JSON.
5. `GET /api/v1/sample.csv`: deterministic, clearly labelled synthetic example, tied to its documented profile. Do not present the existing generic fixture as an MLCC sample.

Let FastAPI publish OpenAPI. Serve frontend static files only when its build exists; absence must not prevent backend development. Keep `/api/*` routing separate from the SPA fallback.

Return a versioned response containing request ID, schema/model versions, input source, filename, cutoff, target, duration, batch count, unique component count, measurement-record count, decision counts, capability flags, records, unscored records and warnings.

Each record should preserve the existing screening fields and add available presentation evidence: measurement unit, initial/latest value, last observation hour, absolute change, percentage change, slope, applicable limit metadata, early trajectory and comparable-peer statistics with sample size. Keep unprovided metadata null.

The shared `percent_change` is a fraction; a value of 0.1 means 10%. Explicitly document conversion. When the initial value is zero, a UI percentage is unavailable even if the model's internal feature uses an epsilon. Do not describe acceleration from only two observations as measured evidence.

For more than one measurement per component, preserve per-measurement decisions. Define a documented summary aggregation separately: use the most urgent scored recommendation; mark partial coverage and never imply all measurements passed when one is unscored. Keep recommendation counts and unscored/partial counts clearly distinguished.

For the optional outcome-reveal interaction, future observations belong in a separate evaluation-only response section. They must never enter inference, early peer statistics or explanations. No stored session is needed: the client can retain the response and reveal the later observations on demand. Omit outcome fields when the CSV has only early data.

## Ingestion and error behaviour

- Bound reads to 10 MB and 100,000 data rows; enforce the byte limit during reading, before pandas parsing.
- Accept ordinary CSV uploads without depending on one exact browser MIME value. Validate content and encoding; do not accept ZIP, spreadsheet or executable/model files.
- Reject missing required columns, duplicate headers, empty files, nonfinite numeric values, invalid hours/limits, duplicate measurement identities and changing limits within a history. Validate optional numeric fields when supplied.
- Preserve string IDs and reject ambiguous identity reuse the current core cannot safely handle. Either consistently support the full identity or require globally unique component IDs for this pilot and document that constraint.
- Require the exact 0 h and 24 h inputs for the SIH mode. Clearly identify missing checkpoints. If some histories are eligible, return partial results and explicit unscored reasons; if none are eligible, return a structured 422.
- Enforce profile/unit/test-condition compatibility before calling the core. If comparable peers are too few, return unavailable/provisional status rather than an unsupported claim of reliable batch anomaly detection; make the required peer count explicit in the profile.
- Keep scenario labels, future-failure flags, final values and identifiers out of predictive numeric features. Preserve provenance; absent source means unknown, never verified real. Detect synthetic markers and never upgrade them to real; distinguish uploaded claims from independently verified provenance.
- Return structured errors with code, message and row/column where known. Never fabricate a precise row number from a dataset-level core error. Use 413 for oversized uploads, 422 for invalid data and 503 for unavailable required models. Keep server tracebacks out of responses.

## Forecast workstream and model handoff

Build an adapter interface first so API tests and frontend contracts do not depend on a final model. Test doubles are allowed only in tests; production must never fall back to fake predictions.

For a real initial implementation, train an offline baseline using the existing synthetic harness, explicitly labelled as a synthetic development model. Separate train, calibration and untouched test data by whole batches; tune only within training batches. Train the final-measurement predictor using only 0/24 h features and use 168 h values solely as training targets or evaluation outcomes.

Compare candidate models under identical splits. Report MAE in the measurement unit, limit-normalized MAE, recall for later limit crossings, false-positive rate, interval coverage and interval width. Use null/undefined with a reason for metrics whose denominator is zero. Avoid quoting ordinary accuracy as the main metric.

Do not claim 90% confidence from an anomaly score. A nominal 90% prediction interval needs held-out calibration, with empirical coverage reported separately. Poor calibration or inadequate calibration data must be visible. Feature contributions explain model behaviour; they do not prove water ingress, cracking or another cause.

Bundle an artifact manifest containing versions, feature order/schema hash, supported profiles/checkpoints, data provenance/hash, batch splits, seeds, metrics and artifact checksums. Add an offline packaging command for Karthik's fitted anomaly detector; do not retune his algorithm. When real/profile-specific artifacts arrive, swap them through the adapters without changing the frontend contract.

## Minimum meaningful verification

Run the existing suite before and after your changes. Add focused API tests for:
- Valid CSV → typed real-service results, with consistent summaries and IDs.
- Empty/malformed/oversized input, infinity/NaN, leading-zero IDs, duplicate rows and inconsistent units/limits.
- Partial histories, unsupported profiles, missing artifacts and truthful readiness.
- No request-time model fitting and reproducible inference from loaded artifacts.
- Changing or removing every observation after 24 h leaves early features, scores, predictions and recommendations unchanged. Evaluation-only outcomes may change.
- Forecast identity joins survive row reordering and do not swap components.
- Synthetic/unknown provenance remains visible; missing forecasts do not become zeros.
- Lower-limit profiles cannot silently invoke upper-limit decisions.

Keep test fixtures distinct from runtime assets. Measure inference duration on a representative dataset and report the measured result, without a fabricated guarantee.

## Start now and deliver usable milestones

First implement the FastAPI skeleton, typed contracts, input validation and model adapters, and provide the API contract to the frontend teammate. Continue with the actual core integration, explicit missing-artifact states, offline baseline/artifact packaging and meaningful tests. Do not stop after a plan or scaffold while independent work remains.

If a required file is absent from the provided workspace, say exactly which file is missing. Continue isolated API/schema/test work where possible; do not reconstruct Karthik's algorithm from memory. If using a chat-only environment without file execution, provide complete file contents and exact local commands, and label testing as not run.

At handoff, provide:
1. Files changed and a concise implemented-vs-pending status.
2. Exact install, artifact-preparation, test and server-start commands, with expected working directory.
3. OpenAPI JSON, API contract, sample request/response and synthetic sample instructions.
4. Test results actually observed and model/data limitations.
5. A short integration message for Karthik listing interfaces consumed, artifacts/data needed and any proposed core changes.

Use this handoff as your active assignment, not the older `CLAUDE_HANDOFF_SIH26170.md` anomaly-audit assignment. Keep the existing core intact while delivering the backend around it.
