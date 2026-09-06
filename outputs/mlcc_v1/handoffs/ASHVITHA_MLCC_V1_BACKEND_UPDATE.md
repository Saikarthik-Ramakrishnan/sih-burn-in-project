# Ashvitha — new MLCC model integration update

Snapshot: 5 September 2026. Paste this into your existing Claude conversation. For a fresh conversation, supply the original backend prompt, your current backend source and the new MLCC prototype pack, then paste this update last. This update takes precedence where model ownership or artifacts differ.

---

Continue Ashvitha's Python backend for SIH26170: component burn-in anomaly detection and 0/24 h → 168 h prediction. Preserve the API, CSV validation, tests and other work already completed in this workspace.

Karthik is now delivering a clearly labelled **synthetic MLCC_X7R prototype** with Isolation Forest and an XGBoost final-leakage regressor in `sih26170.mlcc_prototype`. Our live demonstration uploads measurements, validates them and runs the pre-trained models locally. Isolation Forest identifies unusual early observations; XGBoost predicts final leakage. An anomaly score is not a probability of failure.

**Ownership change:** Karthik owns this prototype's dataset, feature construction, model fitting, calibration, model artifacts and final evaluation. Ashvitha owns FastAPI, upload validation, startup loading, an adapter to the new prototype, response contracts and integration tests. Suspend duplicate forecast/model training for this MLCC profile. Keep any existing forecast work separately, without deleting it or substituting it silently. Continue useful backend work immediately.

## Integration contract

Use the actual exported functions, manifest and sample response in the new pack as the authority. The core mapping below was checked against `src/sih26170/mlcc_prototype.py` during preparation; confirm that it matches the snapshot actually supplied. The HTTP response mapping is **TO VERIFY with your current API implementation**, since that work is in your separate workspace. Produce/update `docs/backend/API_CONTRACT.md` with that mapping. If the module or artifact is missing, list the exact missing file, implement the adapter boundary and explicit unavailable-model state, and continue validation/API tests.

The current core callable interface is:

```python
from sih26170.mlcc_prototype import load_bundle, screen_readings

bundle = load_bundle("outputs/mlcc_v1/model_bundle")  # once at startup
result = screen_readings(early_dataframe, bundle, as_of_hour=24, forecast_model="xgboost")
```

Artifact filenames are `manifest.json`, `state.skops`, `xgboost.json` and `evaluation.json` within `model_bundle/`. The core result contains `metadata`, `summary` and `records`, plus an optional separate `future_outcomes` section. The model owner may retain an XGBoost candidate even when an internal validation baseline performs better; surface the model actually used from the artifact/response, never hard-code “XGBoost” beside every forecast.

Final v1 result: `persistence` won internal validation on normalized MAE. The requested hackathon demo explicitly chooses `forecast_model="xgboost"`; the response preserves `metadata.validation_winner`, `forecast_selection` and `selection_warning`. If you omit the option, the library uses the validation winner. Keep this distinction visible and do not claim XGBoost outperformed the baseline. The saved models are unchanged between these inference choices.

`future_outcomes=...` accepts the supplied long-format later-measurement CSV and returns later `hours`, `measurement_value` and `unit` rows. If simulator labels are supplied instead, they appear as `simulation_truth`, not `future_outcomes`. Neither section is an inference input. Preserve this separation in the HTTP adapter.

| Current core fields | Meaning / adapter responsibility |
|---|---|
| `metadata.prototype_version`, `bundle_id`, `selected_model`, `model_training_data` | Model identity and training provenance; uploaded-file provenance is a separate concept |
| `summary.component_count`, `scored_count`, `unscored_count`, `recommendations`, `within_limit_but_anomalous` | Counts; `recommendations` currently includes `RETEST` for unscored records, so keep the unscored count visible |
| `records[].status` | Lower-case `scored` or `unscored` |
| `current_value`, `initial_value`, `delta`, `slope_per_hour`, `percent_change` | Leakage/current change evidence; percent change is a fraction and is unavailable in the UI when the initial value is zero |
| `safety_limit`, `limit_fraction` | Upper leakage limit in µA and current reading / limit |
| `anomaly_score`, `is_anomaly`, `reason_codes`, `anomaly_score_kind` | Anomaly evidence; score is not failure probability |
| `predicted_final_value`, `prediction_lower`, `prediction_upper`, `target_hour` | Selected model's final-point forecast and interval |
| `forecast_model`, `xgboost_candidate_final_value` | Main forecast model name and separately named XGBoost comparison; do not substitute one for the other |
| `xgboost_explanation` | Native TreeSHAP contributions for the XGBoost candidate; `is_active_forecast` says whether they explain the chosen forecast |
| `prediction_readiness`, `out_of_training_range_features`, `prediction_readiness_warning` | Disclosure of missing/imputed inputs and extrapolation beyond measured training-condition ranges |
| `interval_nominal_coverage`, `interval_method`, `interval_warning` | Interval metadata; nominal level is not achieved field coverage |
| `peer_count`, `current_batch_robust_z`, `slope_batch_robust_z`, `peer_comparison_warning` | Peer evidence; current core warns below eight peers |
| `early_readings`, per-record `metadata`, `missing_optional_features` | Actual early trajectory, available context, imputed-input disclosure |
| `recommendation`, `recommendation_reasons`, `data_quality_warning` | Existing upper-case decision categories; unscored records have `RETEST` and null model outputs |

Request IDs, durations, filename, validation error schema, HTTP status codes and nesting additions remain owned by your API contract. Do not claim the core already returns them. The exact finished sample response must be generated by the shipped model/API, not typed from this table.

Load the trusted, local model bundle once at startup. Do not retrain, tune, download weights or fit a scaler/detector from the uploaded batch. Peer statistics at scoring time may be calculated as the prototype explicitly specifies; that does not authorise refitting model weights. Verify supported family, measurement, units, part/test profile, checkpoints, feature schema and artifact/dependency versions. Read checksums/version metadata when provided. Do not accept uploaded model files.

Input remains long-form measurements. Use the exact new CSV schema and dictionary rather than renaming an old generic IC fixture. The inference path must select exactly 0 h and 24 h and reject/report missing inputs as specified by the core. Keep future readings and `train_labels.csv` columns out of model features. IDs and grouping metadata are for identity/comparability, not extra numeric predictors. Insulation resistance derived from leakage is not independent diagnostic evidence.

Required core columns are `component_id,batch_id,component_family,hours,measurement_name,measurement_value,upper_limit`; additional profile metadata required by this artifact must be read from its manifest/schema. The supported measurement is `leakage_ua` in µA with a positive upper limit. `prior_storage_humidity_pct` is prior storage history, not hot-chamber humidity. Do not mix stress temperature/voltage with the separate measurement temperature/voltage columns.

Keep a single typed adapter between the existing API and the model's real return object. Retain existing endpoint naming where feasible. A successful response must honestly distinguish scored, unscored and unsupported records, early observations, forecast point, interval availability, model/provenance metadata and warnings. Never convert missing forecast/interval/score values to zero. If there is no calibrated probability field, do not create one by rescaling an anomaly score.

Only enable `MLCC_X7R` / `leakage_ua` for this artifact. Other component families remain unavailable until they have their own validated profiles. A CSV with family names changed is not evidence that a model generalises.

The shipped manifest lists four supported fictional `profile_id` values. Missing/unknown profile IDs are unscored for this bundle. Mixed profiles/part specifications or measurement conditions within a batch are rejected. The core is not a general-purpose unit/profile converter. Supplied lower limits are rejected rather than silently treated as upper-limit screening.

Keep the original constraints on file size, malformed uploads, duplicate identities, changing units/limits, useful structured errors and startup readiness. Reject or explicitly ignore undocumented columns according to the agreed schema, and record that policy. Never expose source tracebacks in API responses.

## Forecast and demo behaviour

The target is 168-hour leakage. A forecast interval, if supplied by the artifact, is an interval for that final point. It is not measured data, guaranteed error bounds or a complete future trajectory. Return nominal interval level and calibration metadata only when provided. Keep held-out empirical coverage in a model information section; do not label it the probability of any one component passing.

Outcome reveal is optional. If implemented, early scoring must complete without access to future observations. Later observed readings belong in a separate retrospective section, with observed-versus-synthetic-latent truth clearly distinguished. Do not return latent generator values as if they were sensor measurements. The demo must remain honest when only early data is uploaded: show that later outcomes are unavailable.

## Required verification and handoff

Add focused tests using the actual loaded bundle: valid early CSV; unsupported profile; missing checkpoint; malformed/oversized input; partial histories if supported; absent artifact; and a stable typed response. Verify that changing every reading after 24 h leaves early features, scores and forecasts unchanged. Verify no fit/train method runs during a request. Check identity joins, row reordering and repeated inference determinism to the precision the prototype documents. Report any batch-composition dependence of peer scores so the frontend can show group size/context.

Create an API sample response from an actual run, not hand-authored fake model numbers. Give the frontend teammate OpenAPI and the exact field/unit/status mapping. Retain nulls and clear reasons. Track current behavior in `docs/backend/STATUS.md`, with actual commands, results, changed files and known limitations.

Return a focused patch/change list plus `API_CONTRACT.md`, OpenAPI, the real sample response and any integration requests. Never overwrite Karthik's source folder with your whole copy. There is no automatic chat/workspace synchronisation: record which dataset/model snapshot you received and any newer local work you preserved. Start integration now and continue independent API work if a single artifact is missing.
