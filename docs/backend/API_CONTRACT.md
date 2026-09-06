# SIH26170 Backend API Contract

**Schema version:** `1.0.0` · **Base path:** `/api/v1`
**OpenAPI:** [`openapi.json`](openapi.json) (live at `/api/v1/openapi.json`, docs at `/api/v1/docs`)
**Real sample response:** [`sample_response.json`](sample_response.json) — produced by an actual run of the shipped model, not hand-authored.

Updated 2026-09-06 for the MLCC v2 forecaster (`xgboost_v2`, bundle `mlcc-pilot-1.1`). All changes are additive; schema version unchanged.

---

## 1. How to read the numbers

These rules matter more than the field list. Getting them wrong produces a
dashboard that misleads a judge.

| Rule | Detail |
|---|---|
| **`percent_change` is a fraction** | `0.1` means **10 %**. Multiply by 100. |
| **Zero baseline has no percentage** | `percent_change: null` + `percent_change_available: false`. Show the absolute change. Never render `0 %` or `∞ %`. |
| **`null` never means zero** | Anything not supplied stays `null`. A missing forecast is `null` bounds plus a `status`. |
| **The anomaly score is not a probability** | `anomaly.score_kind` says it verbatim: *"ranking score, not failure probability"*. Never label it "% confident". |
| **Name the model that actually ran** | Use `model_info.selected_model`. The default is now `xgboost_v2`; print exactly that name. Do **not** print "XGBoost" beside a forecast unless that field says `xgboost` or `xgboost_v2`. |
| **The selected model may not be the best one** | When `model_info.selection_warning` is non-null, the chosen model did **not** win internal validation. Show that. Never imply it outperformed the baseline. |
| **The XGBoost candidate is a separate number** | `forecast.xgboost_candidate_final_value` is the v1 XGBoost comparison value. `xgboost_explanation.explained_model` names which tree model the contributions explain (`xgboost_v2` for the default forecast); when `is_active_forecast` is `false`, those contributions do **not** explain the displayed forecast. |
| **Explanations are not causes** | Contributions explain model behaviour, not water ingress or cracking. |
| **Intervals are nominal** | For `xgboost_v2`, `interval_nominal_coverage` is `0.8` and `upper_bound_nominal_level` is `0.9`: each bound is a one-sided 90 % bound, so the pair is an 80 % interval; the wider 90 % pair is in `prediction_lower_two_sided`/`prediction_upper_two_sided`. Other models report `0.9` with a symmetric radius. Nominal, not achieved field coverage. `interval_warning` carries the artifact's own caveat — display it. |
| **Extrapolation invalidates the interval** | Non-empty `forecast.out_of_training_range_features` means the inputs sit outside the training ranges. On the current sample this is ~25 % of records. |
| **Unscored is not a pass** | `unscored_records` were **not** screened. `decision_counts` covers scored records only. `partial_coverage: true` must never render as passed. |
| **Peer scores depend on the uploaded batch** | Always show `peers.sample_size` next to `current_batch_robust_z`. |
| **No acceleration from two points** | `acceleration` is always `null` in the 0/24 h mode. |

---

## 2. Endpoints

### `GET /api/v1/health/live`
Process liveness. Always `200` while running. Says nothing about models.

### `GET /api/v1/health/ready`
`200` only when the bundle loads, **every checksum matches**, library versions are
compared and a real inference probe passes. Otherwise `503` **with the same body**,
so the UI can render the reason.

```jsonc
{
  "ready": true, "mode": "demo", "version": "0.1.0", "schema_version": "1.0.0",
  "capabilities": [
    { "name": "core_modules", "available": true, "reason": null, "checks": [...] },
    { "name": "anomaly",  "available": true, "artifact_id": "b5553f6f7032092e-s26170",
      "model_version": "mlcc-pilot-1.0",
      "checks": [ {"name":"checksum:state.skops","passed":true,"detail":null},
                  {"name":"version:xgboost","passed":true,"detail":null},
                  {"name":"inference_probe","passed":true,"detail":null} ] },
    { "name": "forecast", "available": true, ... }
  ],
  "limitations": []
}
```

### `GET /api/v1/profiles`

```jsonc
{ "schema_version": "1.0.0", "mode": "demo", "profiles": [{
    "profile_id": "mlcc_x7r_leakage_ua",
    "component_family": "MLCC_X7R", "measurement_name": "leakage_ua",
    "measurement_unit": "uA", "limit_direction": "upper",
    "status": "supported",
    "required_checkpoint_hours": [0.0, 24.0], "as_of_hour": 24.0, "target_hour": 168.0,
    "min_peer_group_size": 8,
    "anomaly_available": true, "forecast_available": true, "usable": true,
    "supported_part_profiles": ["SIM_X7R_100N_50V","SIM_X7R_10N_50V","SIM_X7R_1U_25V","SIM_X7R_4U7_16V"],
    "provenance_note": "The models are trained on SYNTHETIC MLCC data...",
    "unavailable_reason": null
}]}
```

**`mlcc_x7r_leakage_ua` is the only `usable: true` profile.**
`digital_ic_leakage_ua`, `power_mosfet_rds_on_mohm` and `film_cap_capacitance_nf`
are `planned` with no artifact — render them as unavailable.
`supported_part_profiles` are the `profile_id` values an upload must carry.

### `POST /api/v1/screen`
`multipart/form-data`:

| field | type | required | notes |
|---|---|---|---|
| `file` | file | yes | Long-format CSV. Content validated; browser MIME not trusted. |
| `as_of_hour` | float | no (`24`) | Only `24` is supported. Else `422 UNSUPPORTED_AS_OF_HOUR`. |
| `forecast_model` | string | no | One of `xgboost_v2`, `persistence`, `linear_extrapolation`, `ridge`, `hist_gradient_boosting`, `xgboost`. Omit to use the artifact's validation winner (`xgboost_v2` in the v2 bundle). |
| `outcome_file` | file | **no** | Second CSV of observations strictly **after** the cutoff, for the outcome reveal. See below. |

#### The optional `outcome_file`

Existing single-file requests are unaffected: omit the part and nothing changes.

Required columns (note: **no limit columns**):

```
component_id,batch_id,component_family,hours,measurement_name,measurement_value
```

Outcomes are matched to the early file on all four identity fields
(`component_id`, `batch_id`, `component_family`, `measurement_name`).

**It cannot influence anything.** Its values never build features, produce
forecasts or change a recommendation, and it cannot supply a limit: if it
carries `upper_limit`/`lower_limit` those columns are **dropped** and you get an
`OUTCOME_LIMITS_IGNORED` warning. Comparison limits always come from the
validated early file, so a later file cannot move the goalposts. There are tests
asserting that changing every outcome value leaves every forecast, anomaly score
and recommendation bit-identical.

This is a **presentation convenience, not a blind-testing mechanism** - the
client holds both files and simply chooses when to render the reveal.

Rejections (all `422` unless noted):

| Condition | `error` |
|---|---|
| any row at or before the cutoff | `INVALID_HOURS` |
| same identity + hour twice (within the file, or across both files) | `DUPLICATE_MEASUREMENT_IDENTITY` |
| an identity with no early history | `AMBIGUOUS_COMPONENT_IDENTITY` |
| declared unit is not uA | `INCOMPATIBLE_UNITS` |
| non-finite or non-numeric value | `NON_FINITE_VALUE` |
| missing a required column | `MISSING_REQUIRED_COLUMNS` |
| not a text CSV | `UNSUPPORTED_FILE_TYPE` (`415`) |

Partial coverage is allowed and produces an `OUTCOME_COVERAGE_PARTIAL` warning:
components without a revealed outcome are **not** the same as components that
stayed within limit.

### `GET /api/v1/sample.csv`
240 components sliced from the shipped MLCC demo dataset, plus their 168 h rows
for the outcome reveal. Header `X-Data-Provenance: synthetic`.

---

## 3. Input CSV

**Required:** `component_id,batch_id,component_family,hours,measurement_name,measurement_value,upper_limit`

**Required by this artifact in addition:** `profile_id` — one of the four
`supported_part_profiles`. Without the column, nothing scores.

**Optional, carried into `record.context`:** `part_number`,
`nominal_capacitance_nf`, `rated_voltage_v`, `package_code`, `dielectric`,
`applied_voltage_v`, `measurement_voltage_v`, `temperature_c`,
`measurement_temperature_c`, `prior_storage_humidity_pct`, `tester_id`,
`tester_channel`, `board_position`, `data_source`.

Enforced before the core is called:

- `component_family` must be `MLCC_X7R`, `measurement_name` `leakage_ua` in **µA**. Units are compared, never converted.
- **Exactly one 0 h and one 24 h reading** per component. Other hours are excluded from inference; later hours become the outcome-reveal section.
- **`lower_limit` is rejected with 422.** This artifact is upper-limit only; screening a lower limit against the upper side would pass genuinely failing parts.
- **Mixed `profile_id` inside one batch is rejected** — incomparable parts must not become each other's peers.
- `component_id` must be unique within an upload.
- One history, one limit. IDs are strings; leading zeros preserved.
- Limits: **10 MB**, **100 000 rows**; the byte cap is enforced while reading.

`prior_storage_humidity_pct` is prior storage history, **not** chamber humidity.
Stress temperature/voltage and measurement temperature/voltage are different
columns — do not merge them in the UI.

---

## 4. `POST /api/v1/screen` response

Top level adds `model_info` to what you already had:

```jsonc
{
  "schema_version": "1.0.0", "request_id": "f9ce…", "generated_at": "…Z",
  "duration_ms": 1792.6, "input_source": "upload", "filename": "…csv",
  "profile_id": "mlcc_x7r_leakage_ua",
  "as_of_hour": 24.0, "target_hour": 168.0, "checkpoint_hours_used": [0.0, 24.0],
  "model_versions": { "anomaly": "mlcc-pilot-1.0", "forecast": "xgboost", "bundle": "b5553f…" },

  "model_info": {
    "prototype_version": "mlcc-pilot-1.0", "bundle_id": "b5553f6f7032092e-s26170",
    "selected_model": "xgboost",             // produced every forecast below
    "validation_winner": "persistence",       // the model that actually scored best
    "forecast_selection": "explicit caller choice",
    "selection_warning": "Requested candidate is not the lowest-MAE internal-validation model",
    "model_training_data": "synthetic",
    "model_fitted_during_request": false,
    "supported_family": "MLCC_X7R", "supported_measurement": "leakage_ua",
    "available_models": ["hist_gradient_boosting","linear_extrapolation","persistence","ridge","xgboost"],
    "limitations": ["Only exact 0/24-hour MLCC_X7R leakage measurements in uA are supported", "..."]
  },

  "batch_count": 4, "unique_component_count": 240, "measurement_record_count": 240,
  "scored_record_count": 240, "unscored_record_count": 0,
  "decision_counts": { "ACCEPT": 214, "MONITOR": 10, "RETEST": 8, "ENGINEER_REVIEW": 8 },
  "capabilities": { "anomaly": true, "forecast": true, "intervals": true,
                    "explanations": true, "peer_statistics": true,
                    "mode": "demo", "limitations": [...] },
  "provenance": "synthetic",          // of the UPLOADED FILE, not the model
  "records": [...], "unscored_records": [...], "component_summaries": [...],
  "evaluation": {...} | null,
  "warnings": [...]
}
```

`provenance` describes the uploaded file. `model_info.model_training_data`
describes the model. They are different things.

### ScreeningRecord — new and changed fields

```jsonc
{
  "component_id": "MLCC_C000147", "batch_id": "MLCC_B018",
  "component_family": "MLCC_X7R", "measurement_name": "leakage_ua",
  "profile_id": "SIM_X7R_1U_25V",

  "recommendation": "ENGINEER_REVIEW",
  "recommendation_reasons": [
    "Current value is unusually above the batch norm",
    "Drift is unusually faster than comparable components",
    "The predicted final value crosses the approved limit",
    "The prediction range includes a possible limit crossing"
  ],
  "recommendation_basis": "anomaly_and_forecast", "provisional": false,
  "data_quality_warning": null,

  "anomaly": {
    "status": "available", "score": 0.99994, "is_anomaly": true,
    "score_kind": "ranking score, not failure probability",
    "model_score": 0.89131, "robust_deviation_score": 13.2431,
    "reason_codes": ["..."], "method": "median_mad+isolation_forest"
  },

  "forecast": {
    "status": "available",
    "predicted_final_value": 0.9337,
    "prediction_lower": 0.6267, "prediction_upper": 1.2407,
    "target_hour": 168.0,
    "model_version": "xgboost_v2",                 // <- the model that produced it
    "interval_nominal_coverage": 0.8,              // one-sided 90 % bounds -> 80 % pair (v2 only)
    "upper_bound_nominal_level": 0.9,
    "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
    "interval_stratum": "slope_z_stratum_2",       // 0: slope z < 2, 1: 2-5, 2: >= 5
    "prediction_lower_two_sided": 0.0, "prediction_upper_two_sided": 1.8079,   // wider 90 % pair
    "interval_warning": "Nominal level; coverage on real components is not established…",
    "predicted_to_cross_limit": true,
    "prediction_readiness": "ready",               // | optional_inputs_imputed | outside_training_conditions
    "out_of_training_range_features": [],
    "prediction_readiness_warning": null,
    "missing_optional_features": [],
    "xgboost_candidate_final_value": 0.9337,
    "xgboost_explanation": {
      "explains": "Active xgboost_v2 forecast: absolute-error correction over the 24 h value ...",
      "is_active_forecast": true,
      "explained_model": "xgboost_v2",
      "base_value_ua": 0.20293,
      "top_contributions": [ {"feature":"delta_fraction_of_limit","contribution_ua":0.30716,"feature_value":0.13080} ]
    }
  },

  "limits": { "direction": "upper", "upper_limit": 0.7, "lower_limit": null,
              "applicable_limit": 0.7, "headroom": 0.47081,
              "headroom_fraction": 0.67259, "limit_fraction": 0.32741 },

  "peers": { "sample_size": 57, "sufficient": true, "status": "available",
             "current_batch_robust_z": 7.70297, "slope_batch_robust_z": 13.24312,
             "warning": null,
             // median / mad / peer_min / peer_max are null on the MLCC path:
             // the core supplies robust z-scores rather than raw peer summaries.
             "median": null, "mad": null, "peer_min": null, "peer_max": null },

  "measurement_unit": "uA",
  "initial_value": 0.1376, "latest_value": 0.2292, "last_observation_hour": 24.0,
  "absolute_change": 0.09156,
  "percent_change": 0.66523,          // FRACTION -> 66.5 %
  "percent_change_available": true,
  "slope_per_hour": 0.00381, "acceleration": null,
  "early_trajectory": [ {"hour":0.0,"value":0.1376}, {"hour":24.0,"value":0.2292} ],

  "context": { "part_number": "FICTIONAL-MLCC-11", "tester_id": "TESTER_3",
               "board_position": "165", "temperature_c": 122.6, ... },
  "data_source": "synthetic", "provenance": "synthetic"
}
```

Every value above is copied from [`sample_response.json`](sample_response.json),
which came from a real run. None of it is illustrative.

That record is the story to tell: **32.7 % of its limit — comfortably inside
spec — but 7.7 robust z above its 57 batch peers on current value, 13.2 on drift
rate, and forecast to cross the limit at 168 h.**

### UnscoredRecord

`reason` ∈ `missing_checkpoint`, `unsupported_profile`, `too_few_early_readings`,
`profile_not_available`, `insufficient_peers`, `anomaly_model_unavailable`,
`core_error`. `message` carries the core's own words.

### EvaluationSection — outcome reveal

```jsonc
"evaluation": {
  "available": true,
  "kind": "observed_readings",     // or "simulation_truth"
  "source_filename": "outcomes_168h.csv",   // null when the rows came from the main file
  "target_hour": 168.0,
  "note": "Evaluation only. These are later OBSERVED measurements…",
  "outcomes": [ {"component_id":"…","batch_id":"…","component_family":"MLCC_X7R",
                 "measurement_name":"leakage_ua",
                 "observed_value":0.2638,"observed_hour":168.0,
                 "applicable_limit":0.25,
                 "crossed_applicable_limit":true} ]
}
```

**`crossed_applicable_limit` is `true` / `false` / `null`.** It is computed by
comparing `observed_value` against `applicable_limit`, which is taken from the
uploaded history (the core's outcome rows carry the reading but not the limit).

`null` means **the limit was unknown, so no comparison was possible** — it does
*not* mean the component stayed inside its limit. Render the three states
distinctly; collapsing `null` into "passed" is exactly the bug this field had.

**`kind` matters.** `observed_readings` are real later measurements.
`simulation_truth` are latent generator values that are **not sensor
measurements** and must be labelled as such. Omitted entirely for early-only
uploads.

### Warnings to surface

`FORECAST_MODEL_NOT_VALIDATION_WINNER`, `SYNTHETIC_TRAINING_DATA`,
`SYNTHETIC_DATA`, `UNKNOWN_PROVENANCE`, `FORECAST_EXTRAPOLATES` (with a count),
`UNSCORED_RECORDS_PRESENT`, `PROFILE_ID_COLUMN_ABSENT`,
`UNSUPPORTED_FAMILY_OR_MEASUREMENT_PRESENT`, `NON_UTF8_ENCODING`.

---

## 5. Errors

```jsonc
{ "error": "INCOMPATIBLE_UNITS", "message": "…", "request_id": "…",
  "details": [ { "code": "…", "message": "…", "row": 4, "column": "upper_limit", "value": null } ] }
```

`row` is the 1-based CSV line **including the header**, so the first data row is
`2`. It is `null` for dataset-level problems — a row number is never invented.
No tracebacks, ever.

| Status | Codes |
|---|---|
| `413` | `FILE_TOO_LARGE`, `TOO_MANY_ROWS` |
| `415` | `UNSUPPORTED_FILE_TYPE` (ZIP/xlsx/exe/PDF/pickle by magic bytes) |
| `422` | `FILE_EMPTY`, `MISSING_REQUIRED_COLUMNS`, `DUPLICATE_HEADER`, `NON_FINITE_VALUE`, `INVALID_HOURS`, `INVALID_LIMIT`, `INVALID_OPTIONAL_FIELD`, `DUPLICATE_MEASUREMENT_IDENTITY`, `LIMIT_CHANGED_WITHIN_HISTORY`, `AMBIGUOUS_COMPONENT_IDENTITY`, `INCOMPATIBLE_UNITS`, `UNSUPPORTED_PROFILE`, `UNSUPPORTED_AS_OF_HOUR`, `NO_ELIGIBLE_HISTORIES` |
| `503` | `ANOMALY_MODEL_UNAVAILABLE`, `FORECAST_MODEL_UNAVAILABLE`, `CORE_UNAVAILABLE` |

**Partial success is a `200`** with `unscored_records`. `422
NO_ELIGIBLE_HISTORIES` means nothing could be screened.

---

## 6. Calling the API from a browser

In the packaged demo the SPA is served by this same process, so it is
same-origin and needs no CORS at all. For development against a Vite dev server,
set the allowed origins:

```bash
SIH_CORS_ALLOW_ORIGINS="http://localhost:5173,http://127.0.0.1:5173"
```

Comma-separated. Defaults to those two values. Set it to an empty string to
disable CORS entirely. Credentials are never enabled (the API has no cookies or
auth), methods are limited to `GET, POST, OPTIONS`, and **`x-request-id` is
exposed** so `fetch` can read it - quote it in any bug report.

### Working fetch example

```js
const API = "http://127.0.0.1:8000/api/v1";

async function screen(earlyFile, outcomeFile /* optional */) {
  const form = new FormData();
  form.append("file", earlyFile);
  if (outcomeFile) form.append("outcome_file", outcomeFile);
  // form.append("forecast_model", "xgboost");   // optional

  // Do NOT set Content-Type. The browser must set the multipart boundary
  // itself; setting it by hand produces a 422.
  const res = await fetch(`${API}/screen`, { method: "POST", body: form });

  const requestId = res.headers.get("x-request-id");
  const body = await res.json();          // errors are JSON too

  if (!res.ok) {
    // body = { error, message, request_id, details: [{code, message, row, column}] }
    throw new Error(`${body.error}: ${body.message} (request ${requestId})`);
  }
  return body;
}

// Readiness: render capabilities[].reason verbatim rather than a generic error.
async function ready() {
  const res = await fetch(`${API}/health/ready`);   // 200 or 503, JSON either way
  return res.json();
}
```

`docs/backend/browser_upload_test.html` is a self-contained page that exercises
readiness, `sample.csv` and an upload. Serve it from a *different* origin so CORS
is genuinely tested:

```bash
python -m http.server 5173 --bind 127.0.0.1    # run inside docs/backend/
```

## 7. Frontend notes

- Generate types from `openapi.json` (regenerate: `scripts/export_openapi.py`).
- Build against `sample_response.json` — it is a real run.
- Poll `/health/ready` on load; render `capabilities[].reason` verbatim.
- `/api/*` never falls through to the SPA; a wrong path returns JSON `404`.
- The SPA is served from `frontend/dist` only if that build exists.
- Every response carries `x-request-id`.
- **Timing:** ~0.5 s for 60 components, ~1.8 s for 240, ~5.8 s for 800 on the
  development machine. Show a progress state for larger uploads.
