# STATUS — Claude forecasting v2 (training-only workspace)

Workspace: extracted pack `claude_forecast_v2_pack/` (sibling of the main project). Python 3.12.13 virtual environment from the supplied `requirements-prototype.lock` (xgboost 3.4.1, scikit-learn 1.9.0, pandas 3.0.5, numpy 2.5.2). Nothing under `src/` other than the new `forecast_v2.py` was modified. All data are synthetic; all results are development results on training-batch folds.

## Milestone 1 — data validation, baseline reproduction, diagnostics (done)

- `data_validation.json`: 14,400 early rows, 7,200 components, 36 batches (200 each, one profile per batch, 9 per profile), no missing values, exactly 0 h and 24 h per component, labels join one-to-one on identity. Target y = final_value / upper_limit: median 0.122, 99th percentile 2.21, max 6.85; 553 observed crossings; 116 parts already at or above the limit at 24 h. Input hashes match `SNAPSHOT.json`.
- `fold_assignment.csv`: 5 deterministic profile-stratified whole-batch folds.
- `DIAGNOSTICS.md`: six diagnostic passes. Persistence pooled MAE 0.1592 reproduced; v1 XGBoost 0.2100, losing in every fold and batch because squared error inflates healthy forecasts by +0.116.

## Milestone 2 — predeclared comparison (done)

- `PREDECLARED_COMPARISON.md/json`: 12 configurations and the selection rule frozen before execution (digest `27702108c22c7315`); the runner refuses to run if the list changes.
- `COMPARISON.md`, `comparison_*.csv`, `cv_results.json`, `oof_predictions.csv` (86,400 keyed out-of-fold forecasts).
- Result: every absolute-error residual-over-persistence configuration reaches pooled MAE 0.1427 to 0.1429 (persistence 0.1592), 5/5 folds, 35–36/36 batches, paired per-batch delta −0.016 (SE 0.0017), healthy MAE 0.0165. Every squared-error configuration loses in 0/36 batches; log1p targets help squared error only partially (0.188). The three absolute-error feature sets are a tie on magnitude (aux − leak −0.00017 ± 0.00021; peer − leak −0.00011 ± 0.00012, although peer wins 25/36 batches). The predeclared rule, applied literally, selects `xgb_abs_resid_aux` (ahead of peer by 0.00007 and of leak by 0.00017); `xgb_abs_resid_leak` (leakage-only) is recommended on parsimony as a disclosed deviation, and both candidates are saved.

## Milestone 3 — intervals, final candidates, robustness read-outs (done)

- `interval_experiment__{xgb_abs_resid_leak,xgb_abs_resid_aux,persistence}.json`: nested calibration (8 calibration batches per fold, 2 per profile, window rotated by fold so 31 distinct batches calibrate). Stratified asymmetric signed-residual intervals keep 90 % coverage (fold range 0.86–0.93) and lift non-healthy coverage from 0.56 (v1's symmetric radius) to 0.75; one-sided 90 % upper margin about 0.40 of the limit in the quiet stratum; per-batch coverage 0.84–0.96.
- `candidate/xgb_abs_resid_leak/` and `candidate/xgb_abs_resid_aux/`: fitted on all 36 training batches after the experiment was fixed; native UBJ/JSON plus JSON manifest with feature allowlist, imputation medians, target parameterisation, input hashes, seed, library versions.
- `seed_check__xgb_abs_resid_leak.json`: pooled MAE std 0.00005 over five seeds. `prevalence_readout.json`: with half the defects removed from training, v1 healthy bias +0.116 → +0.075, recommended candidate +0.015 → +0.005.
- Tests: `tests/test_forecast_v2.py` (fast fixture, 38 tests, about 7 s) covering disjoint folds, future/label leakage at the booster-input level, reordering invariance, µA conversion for every predeclared configuration, save/reload with manifest binding and tampering, no inference-time fitting (booster-input spy), unavailable statuses, base_margin consistency, provenance and configuration digests, nested calibration disjointness and rotation.
- `docs/CLAUDE_FORECAST_V2_HANDOFF.md`: recommendation, tradeoffs, interface, integration and independent-testing steps for Codex.

## Disclosures

- Before the comparison list was frozen, a code smoke test executed persistence, linear extrapolation, the v1 replica and one absolute-error residual configuration (leakage + part-level aux with raw humidity); its pooled MAE 0.143 and healthy MAE 0.0167 were seen. The list was then fixed from the diagnostic findings; humidity was changed to a within-batch rank before predeclaration; no other learned configuration ran before freezing.
- The six diagnostics inspected the labels of the same 36 batches used for cross-validation, so these are development results with selection bias. Only Codex's untouched evaluation set is unbiased.
- The healthy-part gate (0.02 normalized) was set after the smoke result was seen; the stricter 1.5× alternative (0.012) proposed independently by the critic pass would exclude every learned configuration, and both are reported.

## Remaining limitations and open items

- Late-onset defects (357) and 72 h tester faults (77) are unpredictable from 0/24 h data for every configuration; they set an MAE floor near 0.10–0.11 and a recall ceiling near 0.42–0.52.
- Intermittent-leakage and channel-fault parts are slightly worse than persistence under the candidate.
- Interval margins for the two high-slope strata rest on 55–66 calibration parts per fold and are noisy; release calibration belongs to Codex.
- Partial uploads change batch-relative features; `peer_count` is reported so the API can warn.

## Milestone 4 — adversarial verification and fixes (done)

Six independent verification passes (scripts `scratch/verify_*.py`): label/future leakage, fold contamination, metric recomputation, inference contract, test audit, integration into a copy of the main project. Confirmed: no post-24 h reading, label, identifier, channel relabel or condition value changes a prediction bit (11 adversarial upload variants per candidate); fold hygiene and out-of-fold file consistency; every reported number recomputed independently to 1e-9; the original 82 main-project tests plus the new tests pass in the main project's environment; the candidate forecasts the 800-part demo upload in 1.8 s. No blocker. Minor findings and what was done:

- Predeclaration digest did not cover shared hyperparameters, feature/interval constants or source files → `provenance` block and `provenance_digest` added to predeclaration and experiment outputs (the runner now refuses on hyperparameter/constant drift and warns on source drift); an addendum with the same block was added to the frozen `PREDECLARED_COMPARISON.json` without changing its configuration digest.
- Interval calibration reused the same 12 highest-id batches in every fold → calibration window now rotates by fold (31 distinct batches); the interval numbers above are from the rotated run and show a wider, more honest fold spread.
- Runner default `--data-dir data` fails in the release layout → clear `FileNotFoundError` naming the flag; handoff step 2 documents `--data-dir outputs/mlcc_v1`.
- Latent-recall column formatting in `COMPARISON.md`; stratum caption now states tester-fault priority (45 overlap parts); prediction previews moved out of the candidate folders.
- Documented: `acceleration_fraction_per_hour2` is identically zero (constant placeholder); the (fraction, robust z) pairs implicitly encode the uploaded batch's median and scale (v1 design; whole-batch holdout tests it honestly); strict version check is a hard failure; the recommendation departs from the rule's letter under a tie.
- Inference-contract review (major): the manifest was neither hashed nor schema-validated, so an emptied `artifact_sha256`, an edited `config.target` or a missing imputation median loaded silently → the manifest's behaviour-determining content is now digested and bound into the model files as a booster attribute, the loader validates the manifest schema, and `strict_versions=False` emits a warning. Also added: stable output dtypes (nullable `Int64`/`boolean`), `predict_records()` for JSON-safe output, `weak_peer_warning` and `imputed_feature_count` columns, and a documented list of which input problems reject the whole upload versus one row.
- Test audit with mutation testing found three regressions the original tests would have missed (upload-median imputation, a baseline dropping the µA conversion, a future-row leak into aux features); the suite now has 38 tests that catch every injected mutant.
- After the fixes the experiment was re-run: all metric blocks and all 86,400 out-of-fold forecasts are bit-identical to the pre-fix run. The candidates were re-saved: tree dumps identical, predictions on all 7,200 training parts identical to 4e-16; model file hashes changed only because of the embedded manifest digest. One non-reproducible test failure was observed while the audit pass was still editing the file concurrently; it did not recur in eight later runs.

