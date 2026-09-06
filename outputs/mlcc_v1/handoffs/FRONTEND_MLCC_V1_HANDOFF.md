# Frontend/designer — live MLCC prototype handoff

Snapshot: 5 September 2026. This adds data and interaction requirements to your existing design assignment. You retain full freedom over visual identity, layout, typography and whether this is one page or several views.

---

Design and build the frontend for SIH26170, our component burn-in screening tool. Engineers upload test measurements, see which MLCC capacitors behave unusually at 24 hours, and inspect a prediction of leakage at 168 hours. The prototype uses Isolation Forest plus XGBoost. All current demonstration data and trained results are synthetic; show that source beside the run, not only in a hidden footer.

Karthik owns datasets/models. Ashvitha owns the Python API and actual response contract. You own UI and integration with her API. Do not implement a second model, invent scores or use browser-side random outcomes. Typed fixtures are fine during layout development when clearly identified as fixtures; replace them with the real sample response before claiming integration is complete.

## What the interface must communicate

| Area | Information to show |
|---|---|
| Upload | CSV selection, supported MLCC leakage profile, units, progress, readable validation errors |
| Run context | Source, model/version when available, cutoff 24 h, target 168 h, batch/component counts, scored/unscored counts |
| Component table | Component/batch identity, 0 h and 24 h leakage in µA, change, applicable upper limit, anomaly flag/score meaning, predicted final leakage, interval if available, review status |
| Evidence detail | Actual early readings, compatible-peer comparison with sample size, model reasons when returned, relevant test conditions, warnings |
| Forecast | A forecast marker at 168 h and its final-point interval; clearly distinguish it from observed values |
| Missing or unsupported | “Unavailable” and a reason; null is never displayed as 0, healthy or passed |

The exact response field names and current score/recommendation semantics are **TO VERIFY from Ashvitha's OpenAPI/API contract and Karthik's generated sample response**. The table describes information requirements, not an invented JSON schema. Bind only fields that actually exist; request missing evidence fields through the backend contract.

The shipped `demo_response.json` is an actual model run on `demo_early.csv`, with `demo_outcomes.csv` supplied only for the separate reveal. It contains `metadata`, `summary`, `records` and `future_outcomes`; Ashvitha may wrap these in her HTTP envelope. `records[].early_readings` contains the actual 0/24 h points. `future_outcomes` contains later measured `hours`/`measurement_value`/`unit` rows keyed by component identity. Match them by identity, never array position.

For this demo, `metadata.selected_model` is `xgboost`, explicitly requested by Karthik; `metadata.validation_winner` is `persistence`. The persistence baseline had lower average error. Preserve `selection_warning` in model details. This is a functioning prototype, not a high-accuracy claim. An `xgboost_explanation` contains native TreeSHAP feature contributions with an `is_active_forecast` flag; these describe model associations rather than physical causes.

Do not display the anomaly score as “failure probability.” Do not infer cracking/water ingress from feature importance. Optional capacitor capacitance, dissipation factor, voltage, temperature, humidity and test location appear only when provided. Derived insulation resistance must be labelled calculated, not a second independent sensor confirmation. Show measurement units consistently and distinguish percentage change from a fraction such as 0.1 = 10%.

Use “prior storage humidity” for `prior_storage_humidity_pct`; do not label it chamber humidity. Separate stress conditions (`temperature_c`, `applied_voltage_v`) from measurement conditions (`measurement_temperature_c`, `measurement_voltage_v`). The model owner is comparing XGBoost with simple baselines, so the UI must name the model actually selected by the artifact/response rather than assume all forecasts use XGBoost.

## Three demonstration interactions

1. **Within limit, still unusual.** Filter for components under the 24 h limit that are flagged by the actual anomaly result. Open an evidence view showing the reading, drift and peer context. “No matching components in this run” is valid.
2. **Predict, then reveal.** Show the early analysis first. If recorded later observations were provided through a separate outcome section, reveal them after a click and compare the final observation with the forecast. Keep future data excluded from early scoring. If only an early CSV was uploaded, display “Later observations not supplied.” Do not draw a smooth future prediction curve when the model predicts only one point.
3. **One clear review card.** Put the component identity, observed readings, anomaly evidence, final forecast/interval and any backend recommendation in one concise view. Exporting a screenshot/report is optional. A missing explanation should appear as unavailable, not a made-up cause.

An observed full-history line may be shown only after outcome reveal and must be labelled observed synthetic data. A dashed line joining 24 h to the forecast is only a visual connector, not a modelled trajectory; prefer a separated final-point marker. Use words/icons as well as colour to identify states. Allow table sorting/filtering, preserve the current selection after errors and keep the last valid analysis visibly tied to its original filename/run.

## Build and integration sequence

Continue your chosen design with fixture-labelled states for empty, uploading, valid analysis, partial/unscored, unsupported profile, bad CSV and backend unavailable. Obtain Ashvitha's real sample response and OpenAPI, then implement one API client and shared response types. Keep HTTP routes configurable to match her current backend. Do not prescribe or duplicate a new API here.

Make the live-demo happy path easy to understand: choose CSV → review upload validation → run analysis → inspect one unusual capacitor → reveal later outcome if available. Use a supplied real-model sample for verification. Check large-table usability, loading/error transitions, units, nulls, source labels and mobile/laptop presentation. Provide the build command, changed files, screenshot/demo notes and any fields still waiting on the API. Report what works with the real backend separately from what still uses fixtures.
