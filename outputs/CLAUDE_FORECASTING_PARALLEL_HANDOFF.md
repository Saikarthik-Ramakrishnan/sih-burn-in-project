# Karthik's parallel Claude task — improve MLCC forecasting

Extract `CLAUDE_FORECASTING_TRAIN_ONLY_PACK.zip` into a separate folder. Open Claude Code there and paste the prompt below. This is a standalone assignment; no previous chat context is required.

---

You are Karthik's parallel ML collaborator for Smart India Hackathon problem SIH26170: early anomaly detection and final-measurement forecasting during electronic component burn-in screening. Begin implementation using the attached project snapshot. Explain findings simply as you work, and produce runnable code rather than only a plan.

## Our problem and live demonstration

Burn-in tests electronic components under controlled heat and voltage. A component may still be inside its approved measurement limit while behaving unusually compared with its batch. Our pilot uses X7R multilayer ceramic capacitors (MLCCs), which help stabilise electrical power. We measure leakage current in microamps.

An engineer uploads a CSV. The system uses exactly the 0-hour and 24-hour measurements to flag unusual parts and predict leakage at 168 hours. The dashboard shows measured values, batch comparison, forecast, prediction interval, explanations and a review recommendation. Models train offline; uploading a CSV runs inference only.

The current Python prototype works. It combines robust median/MAD statistics and Isolation Forest with an XGBoost forecasting candidate. It also compares persistence (predict the 24 h value), linear extrapolation, Ridge and histogram gradient boosting. XGBoost has not yet beaten persistence on the initial internal-validation average-error comparison. Investigate this honestly; a more complex model is not automatically better.

Every provided measurement is synthetic. The complete experiment has 12,000 capacitors in 60 batches and four fictional part profiles, plus separate stress sets. Your pack contains ONLY the 7,200 training components in 36 batches. Separate calibration/test/stress data and production artifacts are deliberately absent. The existing final test was already inspected during v1 development, so v2 will also need a new untouched evaluation set managed by Codex.

## Exact division of work

YOU / CLAUDE own forecasting experiments and a separate v2 forecast candidate. Investigate why early readings do or do not predict the final measurement. Compare suitable objectives/features on training-batch cross-validation and produce a reproducible candidate and evidence.

CODEX, in Karthik's other workspace, owns anomaly-detector improvement, dataset integrity, false-alert analysis, independent evaluation, final calibration, model selection review and integration into the shared release. Do not duplicate that work or edit its modules.

ASHVITHA owns FastAPI, CSV upload validation, startup model loading and API contracts. The FRONTEND TEAM owns the dashboard and visual design. TWO PYTHON TEAMMATES own training-data exploration without ML. Their findings can be supplied to you later; do not wait for them to start.

There is no automatic synchronisation between these conversations. Never claim to have seen another person's latest changes unless Karthik supplies them. Work in the separate extracted folder. If Git is available, use a separate branch; no Git repository is assumed. Return your new files and notes, not a replacement copy of the entire project.

## Read the actual files first

Read this prompt, `data/DATA_DICTIONARY.md`, `data/SOURCES_AND_ASSUMPTIONS.md`, and:

- `src/sih26170/mlcc_prototype.py`
- `src/sih26170/features.py`
- `src/sih26170/contracts.py`
- `src/sih26170/anomaly.py` and `decision.py` for integration context only.

Treat the existing source as read-only. The old `train_bundle()` expects withheld calibration/test files, so do not run it or invent replacements to make it execute. Build an independent training-only experiment runner using shared feature functions where appropriate.

Input files:
- `data/train_early.csv`: exactly 0/24 h input observations.
- `data/train_readings.csv`: full training histories, for retrospective diagnosis only.
- `data/train_labels.csv`: observed 168 h target and simulator-only labels.

Preserve string IDs. Join on `batch_id`, `component_id`, `component_family`, `measurement_name`; never join by row position. Main value: `measurement_value` in µA, with fictional `upper_limit`. The target is observed `final_value` at 168 h; normalized target is `final_value / upper_limit`. `true_final_value` is privileged simulator truth and must not replace the observed regression target. It can be used for explicitly separate retrospective diagnostics.

Auxiliary capacitance/loss/stress measurements are available at the early checkpoints. `insulation_resistance_gohm` is derived from voltage/leakage, not an independent sensor. Storage humidity is not chamber humidity. Simulated mechanism labels do not prove real cracks or water damage.

## Your implementation scope

Create only:
- `src/sih26170/forecast_v2.py`
- `scripts/claude_forecast_v2.py`
- `tests/test_forecast_v2.py`
- `outputs/claude_forecast_v2/` for reports, CV predictions and candidate artifacts.
- `docs/CLAUDE_FORECAST_V2_HANDOFF.md` for integration instructions.

If you discover a core bug, describe it and provide a proposed patch separately. Do not silently change shared feature formulas, Isolation Forest, thresholds, decision rules, data generator, existing artifacts or backend/frontend code. Record extra dependency requirements separately; use the supplied environment versions where possible.

## Work sequence

1. Validate the training inputs and target joins. Record file hashes, row/component/batch counts, missingness, target distribution and how many outcomes cross the limit. Use only 0/24 h observations for predictive features.
2. Reproduce persistence, linear extrapolation and the current XGBoost configuration on one fixed set of whole-batch folds. Use up to five GroupKFold folds, fitting imputers/scalers on each fold's training portion only. Never split rows or parts from one batch across fit/validation.
3. Diagnose performance on those folds. Examine healthy-majority effects, skewed errors, rare final crossings, tester faults and late-onset events. Labels may explain retrospective errors, not enter model inputs or set oracle-dependent inference behaviour.
4. Run a bounded, predeclared comparison. Sensible candidates include XGBoost squared-error versus absolute-error objectives, a log1p-normalized target, and leakage-only versus early-auxiliary feature sets. Verify objective support in the installed library. Keep the initial comparison small (at most 12 configurations including baselines); record it before executing. Do not search indefinitely until a favourable result appears.
5. Keep selection honest. Report normalized MAE, MAE in µA by profile, point-forecast crossing recall, false-positive rate and raw confusion counts. Include mean and spread across heldout batches, not only an average over all rows. Treat CV estimates used for selection as development results, not final validation. Show tradeoffs when a model improves rare-event recall but worsens average error or false alarms.
6. Produce a prediction-interval proposal. Any interval experiment needs a separate calibration subset inside each training fold; validation residuals cannot calibrate their own interval. Final release calibration remains Codex's task. State within-batch dependence limitations; do not label an anomaly score as confidence or failure probability.
7. Save out-of-fold forecasts keyed by complete identity, fold membership, candidate configuration, feature allowlist, library versions, seeds and input hashes. Fit the chosen candidate on all provided training batches only after the experiment is fixed. Save native XGBoost JSON/UBJ and trusted preprocessing metadata when relevant. Do not overwrite v1.

No identifiers, batch/profile names, scenario labels, defect flags, onset times, final values or observations after 24 h can be predictive inputs. Profile metadata can control appropriate normalization or stratified evaluation, but cannot be used to encode hidden outcomes. If any alternate feature formula is proposed, implement it under your own v2 namespace and document it.

## Candidate interface to hand back

Keep inference separate from training. Prefer:

```python
candidate = load_forecast_candidate(path)
predictions = candidate.predict(early_readings_dataframe)
```

Return one row per complete identity with `predicted_final_value` in µA and `target_hour=168`. Preserve row identity regardless of input order. Include a documented unavailable status for invalid inputs. Do not fabricate interval bounds to satisfy the existing `PredictionResult` contract: Codex will connect separately calibrated intervals.

No fitting, tuning, file downloads or target-label access is allowed inside `predict()`. Supply the feature schema, assumptions, supported profiles/checkpoints and missing-value policy. Existing recommendation semantics remain unchanged until integration review.

## Setup and meaningful checks

Use Python 3.12. In your extracted pack, create/activate a virtual environment, install `requirements-prototype.lock`, then `python -m pip install -e . --no-deps`. On macOS XGBoost may need Homebrew `libomp`. Do not rebuild the complete demo/backend environment.

Tests should verify disjoint batch folds, no future or label leakage, identical results under input reordering, correct target-unit conversion, saved-candidate reload and no inference-time fitting. Changing a 96/168 h observation must leave predictions unchanged. Use a small test fixture to keep the tests fast. Report tests you actually ran.

If operating in chat without execution access, supply complete files and local commands and explicitly mark execution as not run. If files are missing, identify them precisely and continue independent code/test work without inventing their contents.

## Return a concrete handoff

Deliver the new source/tests, a runnable experiment command, candidate artifacts if created, fold/candidate comparison tables, keyed out-of-fold predictions, and `docs/CLAUDE_FORECAST_V2_HANDOFF.md` explaining:
- Which candidate you recommend and which metrics support it.
- Where it loses to a baseline or remains uninformative.
- Whether the same feature/profile/target definitions were preserved.
- Exact load/predict example and dependency changes.
- How Codex should integrate and independently test it.

Write `outputs/claude_forecast_v2/STATUS.md` after each milestone with completed work and remaining limitations. Begin with the data validation and reproducible baseline comparison now. Do not change the dataset to make XGBoost win.
