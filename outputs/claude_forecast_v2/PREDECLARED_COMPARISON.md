# Predeclared forecasting comparison

Recorded 2026-09-05T18:44:46Z. Digest `27702108c22c7315`. 12 configurations including baselines.

This list was fixed before scripts/claude_forecast_v2.py experiment was run. Any later change requires a new predeclaration and must be disclosed.

## Selection rule

Primary metric: normalized MAE (|prediction - observed final_value| / upper_limit) pooled over out-of-fold predictions on 5 profile-stratified whole-batch folds; ties broken by fold-mean MAE. Eligibility for recommendation: (a) pooled MAE below persistence and below persistence in at least 4 of 5 folds; (b) healthy-part MAE (is_healthy, retrospective) at most 0.02 normalized so the healthy majority is not inflated; (c) feature set must not contain the batch-constant condition columns (the v1 replica is a reference only, because those columns take one value per batch and act as batch identifiers). If nothing is eligible, persistence is recommended and XGBoost is reported as not beating the baseline. MAE in uA by profile, RMSE, mean signed error, crossing recall / false-positive rate / confusion counts (observed, new-below-limit-at-24h, latent excluding tester faults) and by-scenario MAE are reported for tradeoffs but do not drive selection. Hyperparameters are v1's for every configuration; no tuning.

| # | name | model | objective | target | feature set | note |
|---|---|---|---|---|---|---|
| 1 | `persistence` | persistence | - | normalized | leakage_only | baseline: 168 h value = 24 h value |
| 2 | `linear_extrapolation` | linear_extrapolation | - | normalized | leakage_only | baseline: 24 h value + 0-24 h slope x 144 h |
| 3 | `xgb_v1_replica` | xgboost | reg:squarederror | normalized | v1_all | v1 configuration reproduced (includes batch-constant condition columns) |
| 4 | `xgb_sq_norm_leak` | xgboost | reg:squarederror | normalized | leakage_only | v1 objective/target without aux or condition columns |
| 5 | `xgb_sq_resid_leak` | xgboost | reg:squarederror | residual_over_persistence | leakage_only | squared error on the correction over persistence |
| 6 | `xgb_abs_norm_leak` | xgboost | reg:absoluteerror | normalized | leakage_only | MAE-consistent objective on the raw normalized target |
| 7 | `xgb_abs_resid_leak` | xgboost | reg:absoluteerror | residual_over_persistence | leakage_only | hypothesised best: median correction over persistence, leakage-only |
| 8 | `xgb_huber_resid_leak` | xgboost | reg:pseudohubererror | residual_over_persistence | leakage_only | pseudo-Huber with delta 0.05 normalized: between L1 and L2 |
| 9 | `xgb_sq_log1p_leak` | xgboost | reg:squarederror | log1p_normalized | leakage_only | squared error on log1p(y): tail-taming transform alone |
| 10 | `xgb_sq_log1p_resid_leak` | xgboost | reg:squarederror | log1p_residual_over_persistence | leakage_only | squared error on log1p(y) with log1p(persistence) offset: multiplicative correction |
| 11 | `xgb_abs_resid_aux` | xgboost | reg:absoluteerror | residual_over_persistence | leakage_plus_aux | hypothesised best plus part-level capacitance/loss-factor features and batch-relative humidity rank |
| 12 | `xgb_abs_resid_peer` | xgboost | reg:absoluteerror | residual_over_persistence | leakage_plus_channel_peer | hypothesised best plus leave-one-out same-channel peer statistics (instrument-fault vs drift disambiguation) |

## Feature sets

- `v1_all` (21): percent_change, delta_fraction_of_limit, slope_fraction_per_hour, acceleration_fraction_per_hour2, variability_fraction_of_limit, limit_fraction, distance_fraction_to_upper_limit, current_batch_robust_z, slope_batch_robust_z, initial_fraction_of_limit, temperature_c, measurement_temperature_c, voltage_stress_ratio, measurement_voltage_v, prior_storage_humidity_pct, initial_capacitance_fraction, current_capacitance_fraction, capacitance_change_fraction, initial_dissipation_factor_pct, current_dissipation_factor_pct, dissipation_factor_change_pct
- `leakage_only` (10): percent_change, delta_fraction_of_limit, slope_fraction_per_hour, acceleration_fraction_per_hour2, variability_fraction_of_limit, limit_fraction, distance_fraction_to_upper_limit, current_batch_robust_z, slope_batch_robust_z, initial_fraction_of_limit
- `leakage_plus_aux` (17): percent_change, delta_fraction_of_limit, slope_fraction_per_hour, acceleration_fraction_per_hour2, variability_fraction_of_limit, limit_fraction, distance_fraction_to_upper_limit, current_batch_robust_z, slope_batch_robust_z, initial_fraction_of_limit, initial_capacitance_fraction, current_capacitance_fraction, capacitance_change_fraction, initial_dissipation_factor_pct, current_dissipation_factor_pct, dissipation_factor_change_pct, prior_storage_humidity_batch_rank_v2
- `leakage_plus_channel_peer` (12): percent_change, delta_fraction_of_limit, slope_fraction_per_hour, acceleration_fraction_per_hour2, variability_fraction_of_limit, limit_fraction, distance_fraction_to_upper_limit, current_batch_robust_z, slope_batch_robust_z, initial_fraction_of_limit, channel_peer_median_current_z_v2, channel_peer_elevated_fraction_v2

XGBoost hyperparameters are v1's, unchanged for every configuration: {"n_estimators": 350, "max_depth": 3, "learning_rate": 0.04, "min_child_weight": 12, "subsample": 0.9, "colsample_bytree": 0.9, "reg_lambda": 10.0, "tree_method": "hist"}. No tuning is part of this comparison.

## Rationale (fixed before execution)

The list is a ladder from the v1 configuration to the hypothesised best, so each step isolates one change:

1. `xgb_v1_replica` reproduces v1 (squared error, raw normalized target, all v1 columns including the four batch-constant condition columns).
2. `xgb_sq_norm_leak` drops the auxiliary and condition columns (feature effect under the v1 objective).
3. `xgb_sq_resid_leak` switches to the residual-over-persistence target via `base_margin` (target effect under squared error).
4. `xgb_abs_norm_leak` switches objective to absolute error without the residual target (objective effect alone).
5. `xgb_abs_resid_leak` combines both (the hypothesis from the diagnostics: the conditional median matches persistence on the healthy majority and only moves on the drifting minority).
6. `xgb_huber_resid_leak` sits between L1 and L2 with `huber_slope` 0.05 in normalized units (the healthy MAD is 0.0066, so the default slope 1.0 would be squared error everywhere).
7. `xgb_sq_log1p_leak` is the log1p target named in the assignment, with squared error (the transform that log1p is meant to help).
8. `xgb_sq_log1p_resid_leak` is squared error on the lightest-tailed working variable found in the diagnostics (log ratio to persistence, skew 1.9 vs 4.2 for y).
9. `xgb_abs_resid_aux` adds the six part-level capacitance / loss-factor features and the within-batch rank of storage humidity to the hypothesised best. The diagnostics predict a null result (Ridge delta 0.0003 to 0.0006, univariate AUC 0.48 to 0.52); it is included because the assignment asks for a leakage-only versus early-auxiliary comparison.
10. `xgb_abs_resid_peer` adds leave-one-out same-channel peer statistics (median peer z, fraction of peers with z > 3), the only new feature with demonstrated signal (flags all 113 visible channel faults with zero false positives).

Omitted on purpose: `reg:quantileerror` at alpha 0.5 (same population optimum as absolute error; near duplicate), absolute error on log1p (median is equivariant under monotone transforms; near duplicate of `xgb_abs_resid_leak`), any configuration adding v1's condition columns to the new objectives (they take exactly one value per batch and are batch identifiers), raw `prior_storage_humidity_pct` (0.72 between-batch variance share and a batch-level coincidence with tester-fault batches), batch-level aggregates (36 distinct values), `insulation_resistance_gohm` (exact transform of leakage), and any hyperparameter search.

Fold rule: the experiment uses the deterministic profile-stratified whole-batch folds in `fold_assignment.csv` (every fold holds out every profile). The diagnostics in `DIAGNOSTICS.md` used sklearn `GroupKFold(5)` on sorted batch ids, which left two folds without a profile; per-fold numbers therefore differ between the two documents, while pooled and per-batch paired numbers do not depend on the fold rule.

Healthy-part gate: the eligibility gate of 0.02 normalized (2% of the limit) is a round number about four times the healthy measurement-noise floor (0.0044) and far below the v1 inflation (0.115). The critic pass independently proposed a stricter 1.5x-persistence gate (0.012); both are reported in the results.

## Disclosures

- Before this list was frozen, a code smoke test of the runner executed persistence, linear extrapolation, the v1 replica and one absolute-error residual-over-persistence configuration with leakage plus part-level aux and RAW humidity on the same five folds. Its pooled MAE (0.143 normalized, healthy MAE 0.0167) was seen. None of the twelve configurations above is that configuration (humidity was changed to a within-batch rank on the auxiliary diagnostic's advice), and no other learned configuration was run before freezing.
- Six diagnostic passes inspected the labels of these same 36 training batches and shaped this list, so cross-validated results here carry selection bias and are development results only. The untouched evaluation set managed by Codex is the only unbiased check.
- Expected detection limit: paired per-batch MAE differences to persistence have a standard error near 0.0035 for tree models on 36 batches; differences under about 0.01 should be read as ties.
