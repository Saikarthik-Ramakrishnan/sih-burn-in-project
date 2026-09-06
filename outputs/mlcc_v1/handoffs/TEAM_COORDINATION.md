# MLCC v1 — team ownership and synchronisation

Snapshot date: 5 September 2026. This pack introduces the synthetic `MLCC_X7R` / `leakage_ua` pilot and an Isolation Forest + XGBoost prototype. It updates the original generic-component handoff. It does not prove performance on physical components.

| Owner | Owns | Deliver next |
|---|---|---|
| Karthik | Synthetic generator/assumptions, shared early features, ML prototype, fitting/calibration, artifacts, final evaluation | Versioned source/data/model pack, data dictionary, genuine sample model response and validation notes |
| Ashvitha | Existing FastAPI backend, CSV validation, model-loading adapter, typed API, API tests | Updated contract/OpenAPI, actual API response, focused patch and integration requests |
| Python teammate 1 | Blind training-data quality/EDA | `analysis/teammate_1/` scripts, figures, counts, observations/questions |
| Python teammate 2 | Blind statistical comparisons, then labelled training audit | `analysis/teammate_2/` scripts, frozen blind note, training-only pattern/rule report |
| Designer/frontend | Visual identity, interaction, frontend API client | Working upload/evidence/forecast UI, real-response integration status |

Start with the prompt named for each assignment. Python teammates should receive only the training exploration pack, not the model evaluation pack. Both can analyse training full histories retrospectively, but every “known by 24 h” feature must use exactly 0/24 h. Teammate 1 must not receive labels; teammate 2 reads them only after saving blind observations. Neither reads calibration/test data or tunes against final prototype metrics.

The two authorised training measurement files contain 7,200 components across 36 batches: 72,000 full-history rows and 14,400 early rows. Supply a training-only dictionary/provenance note. The complete generator manifest contains scenario and held-out outcome summaries, so do not include that unfiltered manifest in either exploration pack. Teammate 1 receives no component label file; teammate 2 receives `train_labels.csv` as a separate Stage B input. Do not distribute the final model report to either analysis teammate before their findings are recorded.

The first model is a parallel implementation milestone. The independent EDA can still find shortcuts, unrealistic assumptions and missing cases. It is not a completed pre-ML review. Karthik records changes motivated by those findings and makes a new version. Once a test result has been inspected, do not repeatedly tune against it and keep calling it an untouched test; use training-only validation for iteration and reserve fresh held-out data for a later confirmatory check where needed.

## Share snapshots, not competing folders

1. Record the received snapshot name/date and source/model versions from its manifest. Preserve local work already completed, particularly Ashvitha's API.
2. Work only in your owned files or separate extracted copy. If Git is available, use your own branch; otherwise return changed files plus an exact change list. Do not overwrite another person's project folder wholesale.
3. Shared contract/schema/core changes require a written integration request naming the current behavior, proposed change, affected fields and a small example. Continue independent work while it is resolved.
4. Return scripts/source, reproducible commands, observed test/run results and a brief implemented/pending note. Karthik integrates and records the resulting snapshot.
5. Send the new API contract and real response to the frontend whenever fields change. The API response, model result and uploaded raw CSV are different layers; do not bind the UI directly to a guessed training-table schema.

There is no automatic synchronisation between Claude accounts or local workspaces. A prompt is an assignment, not evidence that files have been transferred or someone else's implementation is complete.

## Shared data/ML rules

- All current examples are synthetic and must stay labelled as such in charts, dashboards and pitch evidence.
- Model input is 0/24 h only; later values, scenario labels and generator truth are evaluation material. IDs preserve identity but are not physical predictor features.
- Whole batches are separated into train/calibration/test by the supplied manifest. Do not randomly re-split rows or copy the same component into different splits.
- Isolation Forest flags unusual behavior. XGBoost forecasts a measurement. Neither result alone proves a physical failure mechanism.
- Observed final leakage and the simulator's latent true final leakage differ deliberately in some cases. Name the target explicitly in every metric or plot.
- Missing values/results remain unavailable. An anomaly score is not a failure probability. A derived insulation-resistance column is not independent corroborating evidence.
- Only the MLCC leakage profile is operational in this snapshot. Other planned components need their own data/profile validation before predictions are enabled.

## Ready for a coordinated demo when

The model pack has been loaded by Ashvitha's backend; a real CSV produces typed model results; the frontend displays that response and truthful source/availability states; and changing hidden later readings cannot change early predictions. Show the prototype's measured synthetic results and limitations. Treat teammate findings and unresolved issues as recorded engineering work, not invisible corrections to the demo.
