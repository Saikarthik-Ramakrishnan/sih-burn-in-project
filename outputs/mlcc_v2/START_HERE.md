# MLCC prototype v2 bundle — start here

`outputs/mlcc_v2/model_bundle/` is the release bundle as of 2026-09-06. It was
trained by `scripts/train_mlcc_prototype.py --dataset-dir outputs/mlcc_v1
--output-dir outputs/mlcc_v2/model_bundle` from the same synthetic train /
calibration / test batches as v1 (same bundle id), with the shared core
`src/sih26170/mlcc_prototype.py` extended additively (version `mlcc-pilot-1.1`).

What is new:

- **`xgboost_v2`**: XGBoost with an absolute-error objective on the correction
  over persistence (base margin = 24 h value / limit), ten leakage-only 0/24 h
  features, v1 hyperparameters, plus a quiet-part gate (below). It won the
  internal validation (normalized MAE 0.1625 vs persistence 0.1795) and the
  untouched test batches (0.1348 vs 0.1531; v1 XGBoost 0.2145), so it is the
  bundle's `selected_model`.

Quiet-part gate (added 2026-09-06, after the robustness check): when a part's 24 h
level and drift are both within 2 robust standard deviations of its batch, the
forecast is the plain 24 h value with no learned correction. Chosen on the
whole-batch training folds (pooled MAE 0.1415 vs 0.1429, healthy-part MAE
0.0128 vs 0.0165, better in 36 of 36 batches); on the untouched test batches the
gated model scores 0.1348 (this was the second and final look at the test set,
the first being 0.1362 for the ungated model). Bagging five seeds was also
tried and changed nothing (0.14150 vs 0.14152), so it was left out. Full table:
`outputs/claude_forecast_v2/robustness_stage_table.csv`.
- **Stratified asymmetric interval** for `xgboost_v2` (strata on the 24 h slope
  robust z; signed-residual quantiles from the calibration batches). Reported
  bounds are one-sided 90 % bounds (an 80 % pair); the wider two-sided 90 %
  pair is reported alongside. Test-batch coverage: 0.830 for the pair, 0.919 for
  the upper bound.
- Native `xgboost_v2.ubj` artifact, checksummed in the manifest; v1 bundles
  (`mlcc-pilot-1.0`) still load with the new core.
- `screen_readings(..., forecast_model="xgboost_v2")` explains the active
  forecast with its own TreeSHAP contributions (`explained_model`).

What did not change: the anomaly detector, the feature formulas, the decision
rules, the v1 bundle under `outputs/mlcc_v1/`, and the response fields v1
produced (new fields are additive).

Evidence and provenance: `docs/CLAUDE_FORECAST_V2_HANDOFF.md`,
`outputs/claude_forecast_v2/` (predeclared comparison, diagnostics, out-of-fold
forecasts), `outputs/codex_ml_v2_review/` (Codex's independent evaluation of the
same candidate on test, fresh and stress sets), and `outputs/mlcc_v2/model_bundle/evaluation.json`
(one-shot test evaluation written at training time).

Test-set screening with the shared decision rule (2,400 parts): ACCEPT 2,124 ·
MONITOR 110 · RETEST 103 · ENGINEER_REVIEW 63; alerts catch 75 of 166 observed
crossings at a 9.0 % false-alert rate among non-crossers (latent, excluding
tester faults: 57 of 138). All data are synthetic; nothing here is field
accuracy.
