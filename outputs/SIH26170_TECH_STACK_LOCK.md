# SIH26170 technology stack lock

Status: **Locked for the nomination prototype**  
Date: 5 September 2026

## Final decision

Use a polished React single-page application compiled once and served by one
FastAPI process. The backend validates and scores the uploaded CSV live. The
supervised prediction model is trained and frozen before the demonstration.

```text
React + TypeScript + Vite static build
                  |
                  | same-origin POST /api/v1/screen
                  v
FastAPI + Pydantic response contracts
                  |
                  v
CSV validation -> feature engineering -> anomaly models
                                      -> 168-hour predictor
                                      -> uncertainty + explanations
                                      -> decision support
                  |
                  v
Typed JSON response -> tables, trajectory chart and reason panel
```

This is designed to be failure-resistant, not literally risk-free. Reliability
comes from removing unnecessary runtime services, freezing artifacts and
testing one exact demonstration path.

## Locked stack

| Layer | Choice | Reason |
|---|---|---|
| Language | Python 3.12 | Stable ecosystem for data, ML and FastAPI |
| Backend API | FastAPI | Typed request/response handling, file uploads and health endpoints |
| API contracts | Pydantic v2 | Prevent malformed responses and generate OpenAPI schema |
| CSV/data operations | pandas + NumPy | Already used and tested by the anomaly core |
| Anomaly orchestration | scikit-learn | Pipelines, robust preprocessing and Isolation Forest |
| Future-value prediction | XGBoost `XGBRegressor` | Strong tabular candidate with native tree-model persistence |
| Prediction uncertainty | MAPIE split conformal regression | Auditable intervals from held-out calibration data |
| Prediction explanations | SHAP `TreeExplainer` | Exact, efficient contribution explanations for tree ensembles |
| Frontend | React 19 + TypeScript + Vite | Professional static UI; no frontend server during the demo |
| Components | shadcn/ui, `new-york` style | Accessible, editable components rather than an opaque runtime |
| Styling | Tailwind CSS 4 with semantic tokens | Small, consistent design system |
| Charts | Recharts through shadcn chart wrapper | Responsive React charts with controlled styling |
| Icons | Lucide React | Consistent functional icons |
| Table | TanStack Table | Sorting and filtering for component results |
| Backend tests | pytest + FastAPI TestClient/httpx | Unit, contract and upload integration tests |
| Frontend tests | Vitest + React Testing Library | Component and response-state tests |
| End-to-end smoke test | Playwright, one golden path | Proves upload-to-result behavior |
| Dependency locking | Exact `requirements.lock` and committed `package-lock.json` | Rebuilds the tested environment |
| Runtime | Uvicorn, one worker | One loaded model set and predictable behavior |

Exact versions must be frozen after the first fully passing integration build.
Do not use `latest`, caret ranges or floating production dependencies after it.

## Explicitly rejected

### Streamlit

Useful for experiments, but its visual language and rerun/state model make the
final product look like a notebook application. Keep it only as an optional
internal ML diagnostic tool, not the judging interface.

### Next.js

Server-side rendering adds a Node runtime and another process without value for
this local demonstration. Vite produces a static bundle FastAPI can serve.

### Database and distributed services

The demo processes one uploaded CSV and returns one response. Do not add a
database, Redis, Celery, Kafka or external storage. Uploaded data stays in
memory and is discarded after scoring.

### Training during the demonstration

Do not train or tune XGBoost live. The upload is genuinely validated, converted
into features and scored in front of judges, but approved model artifacts load
once at application startup.

### Deep sequence models

Do not use an LSTM or Transformer unless real data contains many closely spaced
time points and held-out-batch evaluation proves an improvement.

## Backend architecture

### Endpoints

`GET /api/v1/health/live` confirms that the process runs. It does not imply
models are ready.

`GET /api/v1/health/ready` returns ready only after checking:

- anomaly artifact loaded;
- XGBoost artifact loaded;
- conformal calibration loaded;
- artifact checksums match the manifest;
- feature schema version matches the API;
- golden in-memory inference passes.

`POST /api/v1/screen` accepts one multipart CSV using FastAPI `UploadFile` and
an `as_of_hour` parameter. Enforce:

- `.csv` extension and accepted MIME type;
- maximum 10 MB file size;
- maximum 100,000 rows;
- required columns and numeric types;
- no duplicate component/time/measurement identity;
- limits constant within a component measurement history;
- at least two early observations per scored component;
- no readings after `as_of_hour` entering early features.

Return structured 4xx validation errors with row and column details. Never
return a Python traceback to the interface.

### Response envelope

```json
{
  "request_id": "uuid",
  "schema_version": "1.0",
  "model_version": "nomination-1",
  "as_of_hour": 24,
  "duration_ms": 381,
  "data_source": "synthetic",
  "summary": {
    "components": 240,
    "accept": 207,
    "monitor": 18,
    "retest": 11,
    "engineer_review": 4,
    "data_quality_warnings": 0
  },
  "components": [],
  "warnings": []
}
```

Component objects must come from `build_screening_record()`. The frontend must
not recalculate scores or recommendations.

### One-process production layout

During development, Vite and FastAPI may run separately. Before presenting:

1. build the frontend;
2. point FastAPI to `frontend/dist`;
3. serve `/api/*` first and the React SPA as fallback;
4. run one Uvicorn process on `127.0.0.1`;
5. open the local browser URL.

This removes CORS, a Node server and internet access from the live path.

## ML framework decision

The framework is locked; the final estimator remains performance-gated.

### Anomaly branch

- Deterministic feature engineering
- Median/MAD batch-relative benchmark
- Isolation Forest using only dimensionless and robust features
- Combined flag when either detector supplies sufficient evidence
- Reason codes based on observable measurements

### Prediction branch

- Linear regression baseline
- scikit-learn histogram gradient boosting baseline
- XGBoost primary candidate
- Target: measurement at 168 hours
- Inputs: observations available at the chosen early checkpoint only
- Split: complete batches using `GroupKFold`; never random rows
- Main regression metric: MAE normalized by each measurement's upper limit
- Safety metric: recall for components later crossing the approved limit

XGBoost becomes final only if it beats both baselines on held-out batches.
“XGBoost is accurate” is not accepted as evidence.

### Uncertainty

Reserve a conformalization set of complete batches. Use MAPIE
`SplitConformalRegressor` for a nominal 90% interval. Report actual coverage and
mean interval width on untouched test batches. If coverage is poor, say the
uncertainty is not calibrated instead of displaying false confidence.

### Explanation

Use SHAP `TreeExplainer` for XGBoost predictions. Display at most five drivers,
translated into domain wording. SHAP describes feature contribution, not
physical causality. Probable degradation causes remain a separate,
evidence-qualified layer.

### Tuning

Use a small deterministic search over depth, learning rate, estimators,
subsample and regularization inside grouped validation. Bayesian optimisation
is optional and excluded from the nomination build. Never tune on final tests.

## Model artifact policy

- Save XGBoost with native `.json` or `.ubj` format.
- Save the native scikit-learn pipeline with `skops.io`, not an untrusted pickle.
- Never accept uploaded model artifacts.
- Bundle `model_manifest.json` with SHA-256 checksums, schema version, feature
  order, training-data hash, library versions, seeds and held-out metrics.
- Fail `/ready` if a checksum or schema version differs.
- Load artifacts once during FastAPI lifespan startup.

## UX design system

Visual direction: an industrial reliability console, not a startup landing page.

- White surfaces on a cool-gray background
- Navy primary and restrained teal accent
- Green, amber, orange and red reserved for decision states
- 8–10 px radius, subtle borders and almost no shadows
- System or bundled font; no web-font dependency
- Dense but readable at 1440 px and usable at 1024 px
- No gradients, glassmorphism, glow, decorative blobs, huge hero text, emojis,
  fake terminals or excessive animation

Required information hierarchy:

1. Is the model ready, and which version is loaded?
2. Was the CSV accepted, and what was validated?
3. How many components require attention?
4. Which component is selected?
5. What happened over time?
6. What does the system predict?
7. How uncertain is it?
8. Why was the recommendation made?
9. What should the engineer do next?

Color must never be the only indicator; every status requires text and an icon.

## Repository shape

```text
backend/
  api/
  services/
  schemas/
frontend/
  src/components/
  src/features/upload/
  src/features/results/
  src/lib/api/
models/
  model_manifest.json
  anomaly_detector.skops
  drift_predictor.json
  conformal_calibration.*
src/sih26170/
tests/
scripts/
```

The existing `src/sih26170` package remains the domain core. FastAPI wraps it;
API code must not duplicate feature or decision logic.

## Definition of judging-ready

- One command starts the complete local application.
- No internet connection is required.
- `/ready` verifies artifacts and runs a golden inference.
- Uploading the golden CSV returns the expected flagged component.
- A malformed CSV produces a clear field-level error.
- API response validates against Pydantic.
- Frontend types are generated from OpenAPI.
- Production frontend contains no mock-result path.
- Backend, frontend and one Playwright upload test pass.
- A CLI fallback runs the same CSV through the same domain service.
- Three consecutive cold starts succeed during rehearsal.

## Authoritative references

- FastAPI uploads: https://fastapi.tiangolo.com/tutorial/request-files/
- FastAPI lifespan: https://fastapi.tiangolo.com/advanced/events/
- FastAPI frontend serving: https://fastapi.tiangolo.com/tutorial/frontend/
- scikit-learn GroupKFold: https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GroupKFold.html
- scikit-learn persistence: https://scikit-learn.org/stable/model_persistence.html
- XGBoost Python API: https://xgboost.readthedocs.io/en/stable/python/python_api.html
- XGBoost persistence: https://xgboost.readthedocs.io/en/stable/tutorials/saving_model.html
- MAPIE algorithm selection: https://mapie.readthedocs.io/en/stable/content/getting-started/choosing-algorithm/
- SHAP TreeExplainer: https://shap.readthedocs.io/en/stable/generated/shap.TreeExplainer.html
- Vite production build: https://vite.dev/guide/build
- shadcn components: https://ui.shadcn.com/docs/components
- Tailwind theme variables: https://tailwindcss.com/docs/theme
- Recharts guide: https://recharts.github.io/en-US/guide/

