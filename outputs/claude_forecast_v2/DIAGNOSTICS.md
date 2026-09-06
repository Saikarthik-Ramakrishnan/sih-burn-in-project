# Training-only diagnostics (Claude forecasting v2)

Six independent diagnostic passes over the 7,200 training components (36 batches). Every number below was computed by a script under `outputs/claude_forecast_v2/scratch/diag_*.py` on the training pack only; labels were used to explain errors retrospectively and never as model inputs. All data are synthetic. These diagnostics motivated the predeclared comparison in `PREDECLARED_COMPARISON.md`; they are not selection results.

## Headline conclusions

1. **The v1 XGBoost loss is an objective problem, not a feature problem.** Squared error predicts the conditional mean of a heavy-tailed target; for the 78% healthy parts that mean sits +0.10 to +0.14 above the median, so v1 inflates healthy forecasts (mean +0.115 normalized, worse than persistence on 98% of healthy parts) and loses to persistence in every fold and every batch while winning on RMSE. Ridge and histogram gradient boosting fail identically.
2. **Persistence error is defect error.** Healthy parts contribute 3.9% of persistence's absolute error; defects 91%. An oracle perfect on defects with onset at or before 24 h would reach MAE 0.061; realistic 24 h-only headroom is roughly 0.10 to 0.13 because most early-onset defects are not visible in the 24 h robust-z features and late-onset events (369 parts) plus 72 h tester faults (77 parts) carry no 24 h signal at all.
3. **The honest crossing-recall ceiling for a 24 h-only forecaster is about 42 to 52%.** 322 of 553 observed crossings have no slope or delta warning at 24 h. Persistence's apparent recall (0.186) comes entirely from 103 parts already over the limit at 24 h, 98 of which are instrument faults.
4. **Auxiliary measurements add nothing measurable**, and four condition columns (measurement_temperature_c, voltage_stress_ratio, applied_voltage_v, measurement_voltage_v) take exactly one value per batch, so they are batch identifiers. Storage humidity is a partial lot identifier (0.72 between-batch variance share) with only weak moisture-scenario signal. insulation_resistance_gohm is an exact transform of leakage.
5. **Tester faults are whole-channel offsets of about one upper limit.** A leave-one-out same-channel peer statistic flags all 113 visible faults with zero false positives and separates instrument faults from real drift among high-z parts (AUC 0.99 vs 0.92 for the part's own z). The 77 onset-72 h faults are unpredictable and cost 6.8% of persistence error.
6. **A single symmetric conformal radius (v1) is the wrong interval.** It covers 100% of healthy parts and 53% of defects, is 229 times the healthy median error, and puts 98% of lower bounds below zero leakage. Asymmetric signed-residual quantiles stratified by slope z keep 89% coverage, raise defect coverage from 0.51 to 0.76, and halve width. Within-batch dependence is small (ICC 0.004, design effect 1.75) but per-batch coverage still ranges 0.82 to 0.955.

## Target shape and objective choice

Script: `outputs/claude_forecast_v2/scratch/diag_target_shape.py`

The normalized target y = final/limit is a two-component mixture, not a skewed unimodal variable: 73.5% of parts have a persistence residual |r| <= 0.02 (healthy MAE 0.0078), while the 18.1% of parts with |r| >= 0.2 hold 94.5% of the total absolute error. Among the three requested parameterisations, log1p(y) is the lightest-tailed by moments (skew 2.51, excess kurtosis 6.65 vs y 4.22/28.5 and r 4.60/35.8), and log(y/persistence) is lighter still (1.90/3.47), but every one of them keeps a positive quartile skew of 0.25-0.39, so no monotone transform makes the target symmetric. A squared-error learner loses to persistence on MAE because inside every bin of the 24h state the conditional mean sits 0.10-0.14 above the conditional median: predicting the in-sample conditional mean in 39 bins gives MAE 0.2205 (worse on 81% of parts) while the conditional median gives 0.1540 vs persistence 0.1592; the same holds out-of-fold with whole-batch GroupKFold (bin mean 0.2232, bin median 0.1557, median wins 3 of 5 folds, mean wins 0) even though the mean has the best RMSE (0.417 vs 0.450). Defects hold 91.3% of persistence error (defect-only 87.4%, 979 sub-limit defect parts alone hold 35.8%), tester faults 8.7%, healthy parts 3.9%, and the 116 parts already >= limit at 24h only 2.8% (persistence is nearly unbiased on them). A perfect forecaster for defects with onset <= 24h would reach MAE 0.0607 (61.9% of error removed), but only 416 of those 1062 parts show a robust-z > 3 at 24h, and fixing just those gives 0.1147; the observed-target noise floor is 0.0324 (0.957 on tester-fault parts), so the all-oracle 0 is not reachable by predicting latent truth. Microamp MAE ranks profiles differently from normalized MAE (Spearman 0.40): the 1.3 uA profile holds 53.3% of uA error but 23.4% of normalized error, while the 0.25 uA profile has the highest normalized MAE (0.1925) because it has the highest crossing rate (11.1%).

### Findings

- **y is a spike-plus-right-tail mixture; log1p(y) is the lightest-tailed of the three requested parameterisations but none is symmetric, and the persistence residual r is the most extreme spike-plus-tail shape.** (confidence high)
  - Evidence: y: p50 0.1216, p95 1.227, p99 2.212, max 6.85, skew 4.22, excess kurtosis 28.5, Bowley (quartile) skew 0.385, (p99-p1)/IQR 25.1; shares y<0.3 80.5%, 0.3-1 11.85%, >=1 7.68%. log1p(y): skew 2.51, ex-kurt 6.65, Bowley 0.369, tail ratio 14.7. r = y - limit_fraction: median -0.0013, MAD 0.0066, IQR 0.0157, p99 1.95, skew 4.60, ex-kurt 35.8, Bowley 0.267, tail ratio 128.2; 73.5% of parts |r|<=0.02, 5.6% in (0.02,0.3], 10.8% in (0.3,1), 4.6% >=1, only 1.2% below -0.05. log(y/persistence): skew 1.90, ex-kurt 3.47, Bowley 0.245. Per profile, y skew ranges 3.81-4.42 and Bowley 0.28-0.48, so the shape is the same in all four profiles.
  - Design implication: The objective matters more than the transform. Model the residual r (or log(y/persistence)) so that a zero prediction reproduces persistence, and train with an L1/quantile-0.5 or small-delta Huber loss. If a Gaussian-like working variable is needed (e.g. for an interval model), log(y/persistence) is the least heavy-tailed choice (skew 1.9, ex-kurt 3.5). Do not expect a log or Box-Cox transform alone to fix a two-component mixture.
- **A squared-error learner loses to persistence on MAE because the conditional mean of y given the 24h state is pulled 0.10-0.14 above the conditional median in the bins that hold 96.6% of parts; the conditional median matches or beats persistence, and the effect survives whole-batch holdout.** (confidence high)
  - Evidence: In-sample oracle, 39 bins of limit_fraction decile x slope_batch_robust_z category: MAE persistence 0.1592, conditional mean 0.2205, conditional median 0.1540; RMSE 0.4495 / 0.4128 / 0.4323; conditional mean is worse than persistence on 81.2% of parts. Alternate binnings agree (decile x delta_fraction: 0.2210/0.1542; 100 cells: 0.2187/0.1554; deciles only: 0.2401/0.1719). 33 of 39 bins have mean - median > 0.05, holding 6955 parts (96.6%) and 95.0% of error; in them persistence 0.1565, cond. mean 0.2229, cond. median 0.1545. In the remaining 6 bins (245 parts, mostly slope_z>3, 84% defects) both mean and median help (0.2357 -> 0.1515 / 0.1406). Even the unconditional bias correction persistence+0.142 raises MAE from 0.1592 to 0.2443 (healthy 0.0078 -> 0.1458). Out-of-fold GroupKFold(5) over sorted batches, bin edges and statistics from train folds: persistence 0.1592, bin mean 0.2232, bin median 0.1557; RMSE bin mean 0.4171 (best); median beats persistence in 3 of 5 folds (0.1421 vs 0.1476, 0.1343 vs 0.1393, 0.1568 vs 0.1709; loses 0.1743 vs 0.1685 and 0.1729 vs 0.1714), mean beats it in 0 folds.
  - Design implication: Use an MAE-consistent objective (reg:absoluteerror, quantile alpha=0.5, or Huber with delta ~0.02-0.05 in normalized units) rather than reg:squarederror; squared error is the correct choice only if the deliverable is scored on RMSE. A median-objective model will behave like persistence on the healthy bulk and only move on the high robust-z minority, which is exactly the behaviour needed. Report both MAE and RMSE so this trade-off is explicit.
- **Persistence error is almost entirely defect error, with a large sub-limit drifter component; healthy parts and the 116 parts already over the limit at 24h contribute almost nothing.** (confidence high)
  - Evidence: Mutually exclusive categories: healthy 5624 parts (78.1%) MAE 0.0078 -> 3.85% of total abs error; defect-only 1386 (19.3%) MAE 0.7229 -> 87.4%; defect+tester 45 (0.6%) MAE 0.985 -> 3.9%; tester-fault-only 145 (2.0%) MAE 0.385 -> 4.9%. Overlapping flags: is_defect 1431 parts 91.3%, is_tester_fault 190 parts 8.7%. By observed y>=1: 553 parts (7.7%) MAE 1.214 -> 58.6% of error; y<1 6647 parts MAE 0.0714 -> 41.4%. Defect-only parts with y<1: 979 parts, MAE 0.419, mean residual +0.365, 35.8% of error; defect-only with y>=1: 407 parts, MAE 1.453, 51.6%. The 116 parts with limit_fraction>=1 at 24h: MAE 0.276, mean residual +0.032, median residual -0.011, 2.79% of error; 88.8% are still >=1 at 168h; 72 are tester_channel_fault and 25 intermittent_leakage.
  - Design implication: Optimising MAE is equivalent to forecasting the magnitude of defect drift; 36% of the error is sub-limit drift, so a pure exceedance classifier would miss a third of the reducible error, and a regression on the residual is needed. Do not build special handling or upper clipping for parts already over the limit: persistence is already unbiased on them. Healthy parts set a floor of 0.0078 that any model should preserve (i.e. the model must not move them).
- **The early-detectable oracle floor is 0.0607 (61.9% of persistence error removed), but the realistic headroom is much smaller because most early-onset defects are not visible in the 24h robust-z features, and late-onset defects plus 72h tester faults are unreachable.** (confidence high)
  - Evidence: Oracle floors (perfect on subset, persistence elsewhere): defect onset<=24h (1062 parts) 0.0607; plus tester onset<=24h (1152) 0.0595; onset<=12h only (863) 0.0787; any defect (1431) 0.0139; any defect or tester fault (1576) 0.0061; all parts 0. Late-onset defects (>24h, 369 parts) hold 29.4% of error (floor 0.1124 if only they were fixed); tester onset 72h (77 parts, MAE 1.018) hold 6.84%; onset 120h parts have the largest per-part MAE 1.236. Visibility at 24h (slope_batch_robust_z>3 or current_batch_robust_z>3): onset 0h 53.7%, 6h 44.1%, 12h 35.4%, 24h 19.1%, 48h+ 0-3.8%, healthy 3.0%. Only 416 of 1062 onset<=24h defects are z-visible; perfect prediction on them gives floor 0.1147 (27.9% removed); perfect prediction on all 598 z-visible parts (label-free subset) gives 0.1129. Observed-target noise floor |y - true_final/limit|: 0.0324 overall, 0.0044 healthy, 0.957 on tester-fault parts.
  - Design implication: Set expectations at MAE roughly 0.11-0.13 with 24h-only inputs unless new features detect early-onset defects that the existing robust-z features miss (some 60% of early-onset defects); anything below 0.06 is not attainable from 0/24h inputs, and a model that predicts latent truth cannot beat 0.032 on the observed target. Prediction intervals must carry the irreducible late-onset and 72h tester-fault mass in their upper tail rather than pretend it is predictable.
- **Microamp MAE ranks the profiles differently from normalized MAE and is dominated by the largest-limit profile, so the normalized metric is the fair one for cross-profile evaluation.** (confidence high)
  - Evidence: Normalized MAE: 10N (0.12 uA) 0.1475, 100N (0.25 uA) 0.1925, 1U (0.7 uA) 0.1481, 4U7 (1.3 uA) 0.1487 -> ranks 100N > 4U7 > 1U > 10N. Microamp MAE: 0.0177, 0.0481, 0.1037, 0.1933 -> ranks 4U7 > 1U > 100N > 10N; Spearman 0.40. The 4U7 profile holds 53.3% of uA error vs 23.4% of normalized error; overall persistence MAE 0.0907 uA. Healthy-only noise floor scales 0.00094 -> 0.01005 uA (10.7x) across profiles while normalized stays 0.0077-0.0081. 100N has the highest normalized MAE because it has the highest crossing rate (11.06% y>=1 vs 5.8-7.8%) and highest tester-fault share (4.9%).
  - Design implication: Train and evaluate in normalized units (y = value/limit) and report per-profile normalized MAE; a uA-weighted loss would spend model capacity on the 1.3 uA profile and under-weight the 0.12 uA profile where the same fractional drift matters equally for screening. If a uA figure is required for the UI, convert after prediction.

### Tables

| target | p50 | p95 | p99 | max | skew | ex-kurt | Bowley | (p99-p1)/IQR | share >5 MAD |
|---|---|---|---|---|---|---|---|---|---|
| y = final/limit | 0.1216 | 1.227 | 2.212 | 6.85 | 4.22 | 28.5 | 0.385 | 25.1 | 0.198 |
| log1p(y) | 0.1147 | 0.801 | 1.167 | 2.06 | 2.51 | 6.65 | 0.369 | 14.7 | 0.194 |
| r = y - limit_fraction | -0.0013 | 0.963 | 1.949 | 6.70 | 4.60 | 35.8 | 0.267 | 128.2 | 0.219 |
| log(y/persistence) | -0.0122 | 2.072 | 2.833 | - | 1.90 | 3.47 | 0.245 | 24.7 | 0.209 |

| y bucket share | overall | 10N (0.12) | 100N (0.25) | 1U (0.7) | 4U7 (1.3) |
|---|---|---|---|---|---|
| y < 0.3 | 0.805 | 0.806 | 0.779 | 0.818 | 0.816 |
| 0.3 <= y < 1 | 0.119 | 0.117 | 0.111 | 0.121 | 0.126 |
| y >= 1 | 0.077 | 0.078 | 0.111 | 0.061 | 0.058 |

| r signed bucket | r<-0.05 | -0.05..-0.02 | abs(r)<=0.02 | 0.02..0.3 | 0.3..1 | r>=1 |
|---|---|---|---|---|---|---|
| share of parts | 0.012 | 0.043 | 0.735 | 0.056 | 0.108 | 0.046 |

| predictor (in-sample oracle unless noted) | MAE | RMSE | worse than persistence on share of parts |
|---|---|---|---|
| persistence | 0.1592 | 0.4495 | - |
| persistence + mean residual (+0.142) | 0.2443 | - | - |
| persistence + median residual (-0.0013) | 0.1591 | - | - |
| cond. mean, 39 bins (lf decile x slope_z cat) | 0.2205 | 0.4128 | 0.812 |
| cond. median, 39 bins | 0.1540 | 0.4323 | 0.540 |
| cond. mean, 100 cells | 0.2187 | 0.4100 | 0.809 |
| cond. median, 100 cells | 0.1554 | 0.4292 | 0.485 |
| OOF bin mean, GroupKFold(5) batches | 0.2232 | 0.4171 | 0.812 |
| OOF bin median, GroupKFold(5) batches | 0.1557 | 0.4341 | 0.546 |

| persistence error decomposition | n | share parts | MAE | mean r | share total abs err |
|---|---|---|---|---|---|
| healthy | 5624 | 0.781 | 0.0078 | -0.004 | 0.039 |
| defect only | 1386 | 0.193 | 0.7229 | +0.684 | 0.874 |
| defect + tester fault | 45 | 0.006 | 0.9854 | +0.948 | 0.039 |
| tester fault only | 145 | 0.020 | 0.3848 | +0.364 | 0.049 |
| y >= 1 | 553 | 0.077 | 1.2141 | +1.208 | 0.586 |
| y < 1 | 6647 | 0.923 | 0.0714 | +0.054 | 0.414 |
| defect only & y < 1 | 979 | 0.136 | 0.4193 | +0.365 | 0.358 |
| already >= limit at 24h | 116 | 0.016 | 0.2761 | +0.032 | 0.028 |

| oracle subset (perfect there, persistence elsewhere) | n perfect | MAE floor | share of error removed |
|---|---|---|---|
| none (persistence) | 0 | 0.1592 | 0.000 |
| defect onset <= 24h | 1062 | 0.0607 | 0.619 |
| defect onset <= 24h or tester onset <= 24h | 1152 | 0.0595 | 0.626 |
| defect onset <= 12h | 863 | 0.0787 | 0.506 |
| defect onset <= 24h AND z-visible (slope_z>3 or current_z>3) | 416 | 0.1147 | 0.279 |
| any z-visible part (label-free) | 598 | 0.1129 | 0.291 |
| defect onset > 24h only | 369 | 0.1124 | 0.294 |
| tester onset 72h only | 77 | 0.1483 | 0.068 |
| any defect | 1431 | 0.0139 | 0.913 |
| any defect or tester fault | 1576 | 0.0061 | 0.962 |
| all parts | 7200 | 0.0000 | 1.000 |
| observed-target noise floor abs(y - true/limit) | - | 0.0324 (healthy 0.0044, tester fault 0.957) | - |

| onset hour | n | MAE pers | share total err | share z-visible at 24h |
|---|---|---|---|---|
| 0 | 257 | 0.760 | 0.170 | 0.537 |
| 6 | 295 | 0.609 | 0.157 | 0.441 |
| 12 | 311 | 0.660 | 0.179 | 0.354 |
| 24 | 199 | 0.650 | 0.113 | 0.191 |
| 48 | 133 | 0.677 | 0.079 | 0.038 |
| 72 | 59 | 0.918 | 0.047 | 0.017 |
| 96 | 64 | 0.958 | 0.054 | 0.031 |
| 120 | 57 | 1.236 | 0.062 | 0.018 |
| 144 | 56 | 1.089 | 0.053 | 0.000 |
| healthy ref | 5624 | 0.0078 | 0.039 | ~0.017 |

| profile | limit uA | MAE norm | rank norm | MAE uA | rank uA | share norm err | share uA err | share y>=1 | healthy MAE uA |
|---|---|---|---|---|---|---|---|---|---|
| SIM_X7R_10N_50V | 0.12 | 0.1475 | 4 | 0.0177 | 4 | 0.232 | 0.049 | 0.078 | 0.00094 |
| SIM_X7R_100N_50V | 0.25 | 0.1925 | 1 | 0.0481 | 3 | 0.302 | 0.133 | 0.111 | 0.00203 |
| SIM_X7R_1U_25V | 0.70 | 0.1481 | 3 | 0.1037 | 2 | 0.233 | 0.286 | 0.061 | 0.00536 |
| SIM_X7R_4U7_16V | 1.30 | 0.1487 | 2 | 0.1933 | 1 | 0.234 | 0.533 | 0.058 | 0.01005 |
| Spearman(norm, uA) | | | | | | 0.40 | | | |

### Caveats

- All conditional mean/median comparisons in Q2 are in-sample oracles (bin statistics computed on the parts they score); the out-of-fold GroupKFold(5) repeat supports the direction (median 0.1557 vs persistence 0.1592 vs mean 0.2232) but the median's edge is small (0.0035) and fold-dependent (wins 3 of 5 folds), so treat it as 'median does not lose' rather than a guaranteed gain.
- Bins were chosen by hand (limit_fraction deciles x slope_batch_robust_z edges at -1, 1, 3); three alternate binnings gave the same ordering (mean 0.219-0.240, median 0.154-0.172), but a different state representation could shift the absolute numbers.
- No model was fitted; labels (scenario, onset hours, is_defect, is_tester_fault, true_final_value) were used only to decompose persistence error and define oracle subsets, never as inputs.
- The 'z-visible' subset uses a fixed threshold (slope_batch_robust_z > 3 or current_batch_robust_z > 3) as one crude detector; better 24h features may detect more early-onset defects, so the realistic headroom estimate (MAE ~0.11-0.13) is a rough bracket, not a bound.
- The all-oracle floor of 0 assumes the observed 168h measurement noise and tester error are predictable; the noise floor |final - true_final|/limit is 0.0324 overall and 0.957 on tester-fault parts, so a predictor of latent truth cannot reach 0 on the observed target.
- The shape statistics (moment skew, excess kurtosis) are sensitive to the few extreme parts (max y 6.85); the robust measures (Bowley skew, tail ratio, share beyond 5 MAD) are reported alongside for that reason.
- Persistence MAE reproduced as 0.1592 (known 0.159); healthy MAE 0.0078 is the part-weighted combination of healthy_settling 0.0056 (4428) and ordinary_noise 0.0162 (1196). is_defect and is_tester_fault overlap on 45 parts, so the mutually exclusive health categories were used for the decomposition.
- All data are synthetic; the mixture shape (78% near-zero residual plus a right tail) is a property of the simulator and may not transfer to real burn-in hardware.
- Sibling analysts are writing to the same scratch directory; this angle wrote only diag_target_shape.py, diag_target_shape_summary.json, diag_target_shape_bins.csv and diag_target_shape_stdout.txt.

## Reproduction of v1 baselines on whole-batch folds

Script: `outputs/claude_forecast_v2/scratch/diag_baseline_reproduction.py`

On fixed whole-batch GroupKFold(5) folds, the v1 baselines reproduce exactly: persistence pooled out-of-fold MAE 0.1592 normalized (0.0907 uA), mean signed error (pred - y) -0.142. The v1 XGBoost config (squared error, 350 trees, depth 3) gets pooled MAE 0.2092, HGB 0.2156, Ridge 0.2376, linear extrapolation 0.2625; XGBoost loses to persistence in every fold (+0.035 to +0.065) and in all 36 of 36 batches, even though it wins on RMSE in every fold (0.407 vs 0.450 pooled) and has near-zero mean bias (-0.003). The loss is entirely a healthy-part calibration failure: on the 5,624 healthy parts XGBoost predicts above the actual value 99.1% of the time (mean pred - y = +0.1145, median +0.104; mean forecast 0.230 vs mean actual 0.116), is worse than persistence on 98.4% of them, and healthy parts add +601.5 to its summed absolute error, which more than cancels the -243.3 it gains on defect-only parts (net +360.4 vs persistence's 1146.2 total). HGB and Ridge show the same pattern (healthy mean pred - y +0.120 and +0.136; worse than persistence on 97.2% and 98.8% of healthy parts). XGBoost's gains are real but concentrated in early-onset defects (onset 0-12 h: MAE 0.37-0.45 vs 0.61-0.74 for persistence, observed-crossing recall 22-56% vs 0-3%); for defects with onset >= 48 h (357 parts) and tester faults with 72 h onset (77 parts) no model detects a single crossing and MAE stays 0.6-1.2. Crossing metrics are confounded by tester faults: 98 of the 116 parts already over the limit at 24 h are tester-fault parts, persistence's 103 observed-crossing true positives are all already-crossed parts (0 of 450 new crossings), and latent (is_future_failure, non-tester-fault) recall is 2.0% for persistence vs 22.1% for XGBoost at 0.9% FPR.

### Findings

- **v1 baselines reproduce on fixed whole-batch folds; the v1 XGBoost loses to persistence on MAE in every fold and every batch, but beats it on RMSE in every fold.** (confidence high)
  - Evidence: Pooled OOF MAE (normalized): persistence 0.1592, linear extrapolation 0.2625, ridge 0.2376, HGB 0.2156, XGB 0.2092. Per-fold XGB minus persistence MAE: +0.0647, +0.0627, +0.0423, +0.0350, +0.0435; batches where XGB MAE < persistence MAE: 0/36 (median batch delta +0.0526); same 0/36 for ridge, HGB, linear. Pooled RMSE: persistence 0.4495, XGB 0.4073, HGB 0.4144, ridge 0.4256; XGB RMSE lower than persistence in all 5 folds (0.4096 vs 0.4435, 0.3678 vs 0.4052, 0.4304 vs 0.4755, 0.4102 vs 0.4599, 0.4155 vs 0.4609). Mean signed error (pred - y): persistence -0.1421, XGB -0.0029, HGB +0.0036, ridge -0.0014. Median |error|: persistence 0.0073, XGB 0.1138. Run-to-run identical (seed 26170, threadpool_limits(1)).
  - Design implication: The 'winner' is decided by the metric, not the model: squared-error training optimizes RMSE and delivers it, while the project's headline metric is MAE. v2 must predeclare the evaluation loss; if it is MAE (or MAE in uA), a squared-error objective on y is the wrong objective and persistence is the baseline that any learned model must beat per batch, not just pooled.
- **XGBoost's loss to persistence is entirely a healthy-part inflation: it forecasts roughly twice the actual value for healthy parts, and the healthy-part cost exceeds the whole net loss.** (confidence high)
  - Evidence: Healthy parts (n=5624): XGB mean pred - y = +0.1145, median +0.1043, p90 +0.184, p99 +0.374; pred > y on 99.1% of healthy parts; |XGB err| > |persistence err| on 98.4%; healthy MAE 0.1148 (0.0643 uA) vs persistence 0.0078 (0.0046 uA), a 14.7x increase. Mean forecast on healthy parts 0.2302 vs mean actual 0.1157 (persistence 0.1194); 2582/5624 healthy parts have XGB forecast > 2x actual; 5054 have pred - y > 0.05. Summed absolute error attribution of XGB net loss vs persistence (+360.4 of 1146.2): healthy +601.5, defect-only -243.3, defect+tester -4.3, tester-only +6.4. Healthy parts contribute 42.9% of XGB's total absolute error (645.6/1506.6) vs 3.9% for persistence (44.1/1146.2). Inflation is uniform across profiles (healthy mean pred - y by profile 0.099-0.122).
  - Design implication: Under squared error with a heavy-tailed target (y median 0.12, p99 2.21, max 6.85), the conditional mean for a healthy-looking part is pulled up by the ~20% of defect parts that look identical at 24 h; the MAE-optimal forecast for such parts is the conditional median, which is essentially persistence. v2 should either (a) model the residual y - limit_fraction with an L1/quantile (median) objective so a zero correction is the default, or (b) gate the learned correction so that healthy-looking parts fall back to persistence. Either way the target/objective choice, not feature engineering, is the first lever.
- **HGB and Ridge fail in exactly the same way, so this is a property of squared-error regression on this target, not of XGBoost.** (confidence high)
  - Evidence: Healthy parts: HGB mean pred - y +0.1201 (median +0.1002), pred > y on 96.0%, worse than persistence on 97.2%, MAE 0.1218; Ridge mean pred - y +0.1357 (median +0.1397), pred > y on 97.9%, worse than persistence on 98.8%, MAE 0.1377. Net loss attribution: HGB +405.8 = healthy +640.9, defect-only -236.1, defect+tester -5.8, tester-only +6.8; Ridge +564.2 = healthy +730.3, defect-only -167.0, defect+tester -5.3, tester-only +6.2. HGB is the only model flagging healthy parts as crossings (2 of 5624); XGB, ridge, persistence flag 0.
  - Design implication: Swapping tree libraries or tuning hyperparameters within the squared-error family will not fix the healthy inflation; the v2 experiment budget should go to the objective/target formulation (median or residual-to-persistence) rather than to model-family search.
- **The learned models' genuine gains are confined to defects whose onset is at or before 12 h; for onset >= 24 h they are no better than persistence, and for onset >= 48 h and 72 h tester faults nothing detects a crossing.** (confidence high)
  - Evidence: Defect-only parts by anomaly_onset_hour, MAE persistence vs XGB and observed-crossing recall persistence vs XGB: onset 0 (n=252): 0.743 vs 0.405, recall 0.000 vs 0.556 (81 positives); onset 6 (n=286): 0.610 vs 0.374, 0.032 vs 0.419; onset 12 (n=295): 0.635 vs 0.445, 0.015 vs 0.221; onset 24 (n=196): 0.655 vs 0.651, 0.096 vs 0.058; onset 48 (n=128): 0.673 vs 0.604, 0 vs 0; onset 72-144 (n=229): 0.90-1.25 vs 0.80-1.14, 0 vs 0. Mean signed error for onset >= 48 h ranges -0.57 to -1.14 for XGB. Tester-fault onset 72 h (n=77): observed y mean 1.164, latent 0.302, MAE persistence 1.018, XGB 0.890. Per scenario, XGB reduces summed absolute error most on gradual_drift (-141.7; MAE 0.244 vs 0.652), moisture_associated_history (-58.8), accelerating_drift (-49.7), late_abrupt_onset (-29.5), and increases it on healthy_settling (+463.7), ordinary_noise (+137.8), intermittent_leakage (+32.1; MAE 0.523 vs 0.365), tester_channel_fault (+6.4).
  - Design implication: There is exploitable early signal for roughly 833 early-onset defect parts, so a v2 that applies a learned upward correction only where the 0-24 h evidence supports it can keep the -243 defect gain without the +601 healthy cost. Parts whose anomaly starts after 24 h (about 434 parts, 6% of the set, contributing roughly 0.05 of persistence's 0.159 MAE) are an irreducible point-forecast floor and must be handled by the interval/decision layer (e.g. a wide upper interval or a retest recommendation), not by the point model.
- **Observed-crossing detection is dominated by tester faults and by parts already over the limit at 24 h, so v1-style crossing recall overstates forecasting skill.** (confidence high)
  - Evidence: 116 parts have limit_fraction >= 1 at 24 h; 103 of them have observed y >= 1 at 168 h but only 14 are latent is_future_failure. 98 of the 116 are tester-fault parts (64 with onset 0 h, 33 with onset 12 h, 1 with 72 h): 72 tester-only, 26 defect+tester, 18 defect-only. Persistence's observed-crossing result (tp 103, fn 450, fp 13, recall 0.186, FPR 0.0020) comes entirely from already-crossed parts: 0/450 new crossings detected. XGB: tp 182, fn 371, fp 67, recall 0.329, FPR 0.0101, 90/450 new crossings; HGB 176/377/66, recall 0.318, 82 new; linear extrapolation 167/386/69, recall 0.302, 73 new; ridge 97/456/35, recall 0.175, 5 new. Latent is_future_failure recall excluding tester faults (n=7010, 403 positives): persistence 0.020 (tp 8, fp 10), ridge 0.027, linear 0.194, HGB 0.204, XGB 0.221 (tp 89, fp 57, FPR 0.0086, precision 0.61). Tester-fault parts with onset 0/12 h have observed y mean 1.34/1.25 but latent 0.30/0.26; persistence MAE on them 0.195/0.186 vs XGB 0.279/0.338.
  - Design implication: v2 should report crossing metrics in three separate strata: already-over-limit at 24 h, newly forecast observed crossing, and latent (is_future_failure) crossing excluding tester-fault parts; otherwise persistence looks competitive on recall for the wrong reason. Because the regression target is the observed final_value (instrument error included), training teaches the model that a high 24 h reading persists, which is correct for observed but wrong for latent truth; the tester-fault/observed-vs-latent distinction should be an explicit design decision in v2's target definition.
- **Error is extremely skewed, so a single global interval radius or pooled MAE hides the two regimes; per-group RMSE and MAE differ by two orders of magnitude.** (confidence high)
  - Evidence: Persistence: healthy MAE 0.0078, RMSE 0.0120, mean signed +0.0037; defect-only MAE 0.723, RMSE 0.982, mean signed -0.684; defect+tester MAE 0.985; tester-only MAE 0.385. Pooled median |persistence error| 0.0073 vs mean 0.159. Share of total absolute error from the 553 parts with y >= 1: persistence 58.6% (671.4/1146.2), XGB 36.4% (548.3/1506.6), HGB 35.4%, ridge 35.4%. MAE on y >= 1 parts: persistence 1.214, XGB 0.992 (mean signed -1.208 vs -0.940); on y < 1 parts: persistence 0.071, XGB 0.144. Per-profile MAE in uA (persistence / XGB): 100N_50V 0.048/0.061, 10N_50V 0.018/0.025, 1U_25V 0.104/0.140, 4U7_16V 0.193/0.241, i.e. XGB is worse in every profile.
  - Design implication: Intervals in v2 need to be conditional (heteroscedastic, asymmetric with a long upper tail) rather than a single split-conformal absolute-residual radius; a global radius calibrated to 90% coverage would be far wider than needed for the 78% healthy majority and still miss late-onset defects. Point forecast should be evaluated both pooled and within the healthy / early-defect / late-onset strata so a healthy-part regression is visible immediately.
- **GroupKFold(5) on 36 single-profile batches gives uneven profile coverage across folds, which adds fold-to-fold variance unrelated to model quality.** (confidence medium)
  - Evidence: Validation batches per profile by fold (100N_50V, 10N_50V, 1U_25V, 4U7_16V): fold 0 = 2,2,2,2; fold 1 = 3,2,0,2; fold 2 = 1,0,4,2; fold 3 = 1,3,1,2; fold 4 = 2,2,2,1. Fold 0 holds out 8 batches (1600 parts), folds 1-4 hold out 7 (1400). Persistence MAE by fold ranges 0.1393-0.1714; MAE in uA by fold ranges 0.0669-0.1330 (fold 2, heavy in the 0.7 uA-limit profile).
  - Design implication: v2 evaluation should use profile-stratified whole-batch folds (or report per-batch paired deltas against persistence, as done here with 36 batch-level comparisons) so that fold-level differences reflect the model and not which profiles happen to be held out.

### Tables

Pooled out-of-fold (7200 parts, GroupKFold(5) on batch_id, signed = pred - y)

| model | MAE norm | median abs | MAE uA | RMSE norm | mean signed |
|---|---|---|---|---|---|
| persistence | 0.1592 | 0.0073 | 0.0907 | 0.4495 | -0.1421 |
| linear_extrapolation | 0.2625 | 0.0806 | 0.1386 | 0.8214 | -0.0969 |
| ridge | 0.2376 | 0.1498 | 0.1332 | 0.4256 | -0.0014 |
| hist_gradient_boosting | 0.2156 | 0.1158 | 0.1198 | 0.4144 | +0.0036 |
| xgboost (v1 cfg) | 0.2092 | 0.1138 | 0.1166 | 0.4073 | -0.0029 |

Normalized MAE by fold (val batches: f0=B003,B010,B015,B025,B037,B044,B050,B058; f1=B009,B014,B024,B036,B043,B049,B057; f2=B008,B013,B022,B033,B042,B047,B054; f3=B007,B012,B021,B028,B041,B046,B053; f4=B005,B011,B016,B027,B039,B045,B051)

| fold | pers | linx | ridge | hgb | xgb | xgb-pers | RMSE pers | RMSE xgb |
|---|---|---|---|---|---|---|---|---|
| 0 | 0.1476 | 0.2665 | 0.2369 | 0.2181 | 0.2123 | +0.0647 | 0.4435 | 0.4096 |
| 1 | 0.1393 | 0.2654 | 0.2340 | 0.2090 | 0.2019 | +0.0627 | 0.4052 | 0.3678 |
| 2 | 0.1685 | 0.2387 | 0.2381 | 0.2170 | 0.2108 | +0.0423 | 0.4755 | 0.4304 |
| 3 | 0.1714 | 0.2691 | 0.2444 | 0.2132 | 0.2064 | +0.0350 | 0.4599 | 0.4102 |
| 4 | 0.1709 | 0.2720 | 0.2345 | 0.2201 | 0.2144 | +0.0435 | 0.4609 | 0.4155 |
| batches model beats pers | - | 0/36 | 0/36 | 0/36 | 0/36 | | | |

MAE in uA per profile (pooled OOF)

| profile | n | upper_limit | pers | linx | ridge | hgb | xgb |
|---|---|---|---|---|---|---|---|
| SIM_X7R_100N_50V | 1800 | 0.25 | 0.0481 | 0.0791 | 0.0705 | 0.0632 | 0.0606 |
| SIM_X7R_10N_50V | 1800 | 0.12 | 0.0177 | 0.0352 | 0.0277 | 0.0259 | 0.0252 |
| SIM_X7R_1U_25V | 1800 | 0.70 | 0.1037 | 0.1538 | 0.1562 | 0.1412 | 0.1396 |
| SIM_X7R_4U7_16V | 1800 | 1.30 | 0.1933 | 0.2864 | 0.2786 | 0.2491 | 0.2412 |

Crossing detection, pooled OOF. Observed: forecast>=1 vs y>=1 (553 positives). Latent: is_future_failure excluding is_tester_fault parts (n=7010, 403 positives). 'new' = observed true positives among parts with limit_fraction<1 at 24h (450 such positives).

| model | obs tp | fn | fp | tn | recall | FPR | new/450 | latent tp | fp | recall | FPR |
|---|---|---|---|---|---|---|---|---|---|---|---|
| pers | 103 | 450 | 13 | 6634 | 0.186 | 0.0020 | 0 | 8 | 10 | 0.020 | 0.0015 |
| linx | 167 | 386 | 69 | 6578 | 0.302 | 0.0104 | 73 | 78 | 63 | 0.194 | 0.0095 |
| ridge | 97 | 456 | 35 | 6612 | 0.175 | 0.0053 | 5 | 11 | 30 | 0.027 | 0.0045 |
| hgb | 176 | 377 | 66 | 6581 | 0.318 | 0.0099 | 82 | 82 | 62 | 0.204 | 0.0094 |
| xgb | 182 | 371 | 67 | 6580 | 0.329 | 0.0101 | 90 | 89 | 57 | 0.221 | 0.0086 |

Already >= limit at 24h: 116 parts (72 tester-only, 26 defect+tester, 18 defect-only); 103 have y>=1 at 168h; 14 are latent is_future_failure; 98 are tester-fault parts (onset 0h: 64, 12h: 33, 72h: 1).

Healthy parts (n=5624): is the model inflating forecasts? (signed = pred - y, normalized)

| model | mean signed | median | p90 | MAE | MAE uA | frac pred>y | frac worse than pers | mean forecast (actual 0.1157) |
|---|---|---|---|---|---|---|---|---|
| pers | +0.0037 | +0.0031 | +0.0147 | 0.0078 | 0.0046 | 0.693 | 0.000 | 0.1194 |
| linx | -0.0565 | -0.0606 | +0.0134 | 0.0721 | 0.0424 | 0.138 | 0.950 | 0.0592 |
| ridge | +0.1357 | +0.1397 | +0.2022 | 0.1377 | 0.0762 | 0.979 | 0.988 | 0.2514 |
| hgb | +0.1201 | +0.1002 | +0.2374 | 0.1218 | 0.0683 | 0.960 | 0.972 | 0.2359 |
| xgb | +0.1145 | +0.1043 | +0.1839 | 0.1148 | 0.0643 | 0.991 | 0.984 | 0.2302 |

XGBoost error decomposition by part group (pooled OOF; total abs error 1506.6 vs persistence 1146.2) and attribution of net loss vs persistence

| group | n | xgb MAE | xgb mean signed | xgb sum abs | share of xgb total | frac worse than pers | delta sum abs vs pers: xgb | hgb | ridge |
|---|---|---|---|---|---|---|---|---|---|
| healthy | 5624 | 0.1148 | +0.1145 | 645.6 | 42.9% | 0.984 | +601.5 | +640.9 | +730.3 |
| defect_only | 1386 | 0.5474 | -0.4258 | 758.7 | 50.4% | 0.097 | -243.3 | -236.1 | -167.0 |
| defect+tester | 45 | 0.8901 | -0.8202 | 40.1 | 2.7% | 0.311 | -4.3 | -5.8 | -5.3 |
| tester_only | 145 | 0.4292 | -0.2608 | 62.2 | 4.1% | 0.545 | +6.4 | +6.8 | +6.2 |
| net | 7200 | 0.2092 | -0.0029 | 1506.6 | 100% | | +360.4 | +405.8 | +564.2 |

Share of total absolute error from parts with y>=1 (n=553): pers 58.6%, linx 44.8%, ridge 35.4%, hgb 35.4%, xgb 36.4%. MAE on y>=1 parts: pers 1.214, xgb 0.992; on y<1 parts: pers 0.071, xgb 0.144.

Per-scenario normalized MAE and summed-abs-error delta vs persistence (pooled OOF)

| scenario | n | y mean | pers | linx | ridge | hgb | xgb | dsum xgb | dsum hgb | dsum ridge |
|---|---|---|---|---|---|---|---|---|---|---|
| healthy_settling | 4428 | 0.116 | 0.0056 | 0.0674 | 0.1380 | 0.1171 | 0.1103 | +463.7 | +493.9 | +586.5 |
| ordinary_noise | 1196 | 0.116 | 0.0162 | 0.0896 | 0.1365 | 0.1391 | 0.1314 | +137.8 | +147.0 | +143.8 |
| accelerating_drift | 375 | 0.932 | 0.7946 | 0.8262 | 0.6501 | 0.6563 | 0.6620 | -49.7 | -51.9 | -54.2 |
| gradual_drift | 347 | 0.875 | 0.6519 | 0.2940 | 0.4530 | 0.2634 | 0.2436 | -141.7 | -134.8 | -69.0 |
| late_abrupt_onset | 278 | 1.155 | 1.0167 | 1.1263 | 0.8844 | 0.9097 | 0.9105 | -29.5 | -29.7 | -36.8 |
| moisture_associated_history | 227 | 0.916 | 0.7268 | 0.6272 | 0.5566 | 0.4716 | 0.4678 | -58.8 | -57.9 | -38.6 |
| intermittent_leakage | 204 | 0.502 | 0.3652 | 1.8532 | 0.4939 | 0.5242 | 0.5227 | +32.1 | +32.4 | +26.3 |
| tester_channel_fault | 145 | 1.073 | 0.3848 | 1.6471 | 0.4279 | 0.4319 | 0.4292 | +6.4 | +6.8 | +6.2 |

Defect-only parts (n=1386) by anomaly_onset_hour: MAE, mean signed error, observed-crossing recall (pers vs xgb)

| onset h | n | y mean | MAE pers | MAE xgb | MAE hgb | signed pers | signed xgb | recall pers | recall xgb | positives |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 252 | 0.936 | 0.743 | 0.405 | 0.418 | -0.743 | -0.268 | 0.000 | 0.556 | 81 |
| 6 | 286 | 0.773 | 0.610 | 0.374 | 0.383 | -0.570 | -0.237 | 0.032 | 0.419 | 62 |
| 12 | 295 | 0.772 | 0.635 | 0.445 | 0.449 | -0.584 | -0.297 | 0.015 | 0.221 | 68 |
| 24 | 196 | 0.775 | 0.655 | 0.651 | 0.652 | -0.519 | -0.414 | 0.096 | 0.058 | 52 |
| 48 | 128 | 0.787 | 0.673 | 0.604 | 0.601 | -0.671 | -0.567 | 0.000 | 0.000 | 36 |
| 72 | 57 | 1.018 | 0.904 | 0.800 | 0.801 | -0.904 | -0.800 | 0.000 | 0.000 | 19 |
| 96 | 61 | 1.060 | 0.946 | 0.841 | 0.835 | -0.946 | -0.841 | 0.000 | 0.000 | 30 |
| 120 | 56 | 1.371 | 1.248 | 1.144 | 1.144 | -1.248 | -1.142 | 0.000 | 0.000 | 27 |
| 144 | 55 | 1.204 | 1.080 | 0.957 | 0.967 | -1.080 | -0.956 | 0.000 | 0.000 | 32 |

Tester-fault parts by tester_fault_onset_hour (n, observed y mean, latent y_true mean, MAE pers, MAE xgb): 0h (76, 1.336, 0.300, 0.195, 0.279); 12h (37, 1.253, 0.264, 0.186, 0.338); 72h (77, 1.164, 0.302, 1.018, 0.890).

Batch -> fold assignment (GroupKFold(5), frame sorted by batch_id then component_id; 200 parts per batch)

| fold | batches (profile) |
|---|---|
| 0 | B003 (1U_25V), B010 (1U_25V), B015 (10N_50V), B025 (4U7_16V), B037 (100N_50V), B044 (10N_50V), B050 (100N_50V), B058 (4U7_16V) |
| 1 | B009 (10N_50V), B014 (10N_50V), B024 (100N_50V), B036 (4U7_16V), B043 (100N_50V), B049 (100N_50V), B057 (4U7_16V) |
| 2 | B008 (1U_25V), B013 (1U_25V), B022 (1U_25V), B033 (100N_50V), B042 (4U7_16V), B047 (4U7_16V), B054 (1U_25V) |
| 3 | B007 (100N_50V), B012 (4U7_16V), B021 (10N_50V), B028 (4U7_16V), B041 (10N_50V), B046 (10N_50V), B053 (1U_25V) |
| 4 | B005 (1U_25V), B011 (10N_50V), B016 (4U7_16V), B027 (100N_50V), B039 (10N_50V), B045 (100N_50V), B051 (1U_25V) |

Validation batches per profile (100N_50V, 10N_50V, 1U_25V, 4U7_16V): f0 2,2,2,2; f1 3,2,0,2; f2 1,0,4,2; f3 1,3,1,2; f4 2,2,2,1.

### Caveats

- All data are synthetic; every number is a software benchmark on the simulator, not evidence of field accuracy.
- Signed error is defined as forecast minus actual (pred - y) throughout; the v1 'mean residual +0.142' for persistence corresponds to -0.1421 here.
- These folds are a fixed GroupKFold(5) over 36 batches, not v1's GroupShuffleSplit, so pooled numbers may differ slightly from v1's reported figures; persistence MAE (0.1592) and bias match the previously established values exactly.
- Single seed (26170), no repeated CV. The direction of the XGB-vs-persistence MAE gap is robust (all 5 folds, all 36 batches) but individual fold MAEs move by about 0.01-0.03 with fold composition, largely because GroupKFold does not stratify by profile (fold 1 has no 1U_25V validation batch; fold 2 has four).
- The SimpleImputer is a no-op on this data (no missing values in FORECAST_COLUMNS); it was kept for fidelity to v1.
- Within-batch robust-z features are computed from the held-out batch's own peers at feature-build time; this is legitimate at inference (a whole batch is uploaded together) and involves no labels, but it means each validation batch's features depend on its own 200 parts.
- Part groups are mutually exclusive (healthy 5624, defect-only 1386, defect+tester 45, tester-only 145); is_defect totals 1431 and is_tester_fault totals 190 when the 45 overlap parts are counted in both.
- Observed-crossing metrics use the observed final_value (instrument error included); latent metrics use is_future_failure and exclude all 190 tester-fault parts. Only 14 of the 116 already-crossed parts are latent failures, so observed and latent recall diverge sharply for persistence.
- The 'irreducible floor' estimate (~0.05 of persistence's 0.159 normalized MAE from onset>=48h defects and 72h tester faults) is an arithmetic sum of the per-onset MAEs reported, not a fitted bound.
- No alternative objectives, targets, or hyperparameters were tried, per the assignment; design implications about median/residual objectives are inferences from the error decomposition, to be tested in the predeclared v2 experiment.
- Other diag_* files in the scratch directory belong to sibling angles and were not read or modified; this angle wrote only diag_baseline_reproduction.py, diag_baseline_reproduction_oof.csv (7200 rows, identity + fold + upper_limit + y + five forecasts) and diag_baseline_reproduction_summary.json.

## Which scenarios are predictable from 0/24 h

Script: `outputs/claude_forecast_v2/scratch/diag_scenario_predictability.py`

Predictability from 0/24h readings splits cleanly by scenario and onset. Gradual drift (onset 0-12h) is highly visible at 24h (delta_fraction_of_limit mean 0.05-0.11 vs healthy -0.012; slope_batch_robust_z mean 4.1-8.2; AUC vs healthy 0.98) and its 168h residual tracks the 24h delta (Spearman 0.83), but the true 24h->168h growth is ~9.5x the 0->24h change, not the 6x that linear extrapolation assumes, so linear extrapolation still undershoots (+0.18 mean residual). Accelerating drift (onset 0-24h, 375 parts, 111 crossers) is essentially invisible at 24h: median delta -0.0005 to -0.012, AUC vs healthy 0.62, Spearman(delta, residual) 0.13, and its 24h slope is slightly negative so linear extrapolation is worse than persistence (+0.83 vs +0.79). Every onset>24h defect (late_abrupt_onset 278 parts, moisture onset 48, intermittent onset 48, tester fault onset 72) has AUC 0.49-0.51 vs healthy on all four 24h features, i.e. zero signal. Of the 553 observed crossings, 322 (58%) have no slope/delta warning (|slope_z|<2 and delta<0.05) and 267 (48%) also have |current_z|<2 and limit_fraction<0.5; the honest recall ceiling for any 24h-only forecaster is therefore about 42-52%, and the 5,997 parts that look healthy at 24h carry 62% of total persistence absolute error, setting an MAE floor of 0.099 (vs 0.159) even if every warned part were forecast perfectly. Healthy settling falls a further 2.8% from 24h to 168h (median y/persistence 0.972, residual -0.0030, consistent across all four profiles), which is a real but tiny bias worth 0.0005 overall MAE; the 90% absolute-residual quantile is 0.012 for healthy parts versus 0.60 for all parts, a 51x gap that a single conformal radius cannot bridge.

### Findings

- **Onset>24h defects carry no 24h signal at all; late_abrupt_onset is indistinguishable from healthy on every early feature.** (confidence high)
  - Evidence: late_abrupt_onset (n=278, 129 crossers, onsets 48-144): AUC vs healthy_settling = 0.498 (delta_fraction_of_limit), 0.510 (percent_change), 0.494 (slope_batch_robust_z), 0.512 (current_batch_robust_z), 0.500 (|slope_z|), 0.505 (limit_fraction); per-onset AUCs range 0.42-0.58 with n=42-64. Median delta -0.009 to -0.013 (healthy -0.011), median slope_z -0.23 to +0.05 (healthy -0.08). Mean normalized trajectory sits at 0.12-0.17 until onset then jumps to 0.81-1.13 in one checkpoint and creeps +0.03-0.12 per 24h afterwards. Same for moisture onset 48 (n=50: delta mean 0.011, cur_z AUC 0.43), intermittent onset 48 (n=41: AUC 0.50-0.54), tester fault onset 72 (n=63, 33 crossers: delta -0.0125, slope_z -0.18, cur_z 0.17, mean resid +0.85). All onset>24 crossers (156) vs all non-crossers: AUC 0.48-0.51 on all features.
  - Design implication: Do not spend model capacity or features on these; no 24h-only feature set can recover them. Their 156 crossings (28% of 553) and ~0.25+0.05+0.03 share of absolute error are an irreducible floor. Any evaluation should report metrics separately for onset<=24 vs onset>24 so the v2 model is judged on what is knowable; the tail probability for a 'looks healthy' part should be a population hazard (about 4.5%), not a per-part prediction.
- **Accelerating drift with onset 0-24h is nearly invisible at 24h: it is the largest error source (26% of absolute error) yet its only 24h signature is a weak failure to settle.** (confidence high)
  - Evidence: n=375, 111 crossers, mean y 0.77-1.08. delta_fraction_of_limit mean by onset 0/6/12/24 = +0.003/-0.005/-0.008/-0.013 (median -0.0005/-0.006/-0.008/-0.012) vs healthy mean -0.012 (sd 0.010); slope_z mean 1.05/0.30/0.14/-0.20. AUC vs healthy: delta 0.618, slope_z 0.615, cur_z 0.576, |slope_z| 0.569. Mean trajectory (onset 0): 0.153 at 0h, 0.156 at 24h, 0.197 at 48h, 0.278 at 72h, 1.08 at 168h. Spearman(delta, residual)=0.13, Pearson r^2=0.04. Only 37/375 have delta>0.01; for those the median growth multiplier (y168-y24)/(y24-y0) is 44.6. Unwarned crossers: 87/111 (78%) under the loose rule. Linear extrapolation mean residual +0.83 vs persistence +0.79 and it over-predicts 0% of these parts.
  - Design implication: Never extrapolate the 24h slope for this population: it is zero or negative. The only usable cue is 'did not settle' (delta near 0 instead of -0.012), which is roughly a 1-sd shift and can at best raise a mild tail probability. Recall on accelerating drift will remain low (~22%) regardless of objective; report it explicitly rather than tuning toward it.
- **Gradual drift (onset 0-12h) is the one drift scenario that is both detectable and quantitatively predictable from 24h, but the correct extrapolation multiplier is ~9.5x, not the 6x implied by linear extrapolation.** (confidence high)
  - Evidence: n=347, 96 crossers. delta mean 0.109/0.077/0.049 and slope_z mean 8.2/6.3/4.1 for onset 0/6/12; AUC vs healthy 0.979 (delta), 0.976 (slope_z), 0.876 (cur_z). Spearman(delta, residual)=0.83, Spearman(slope_z, residual)=0.74, Spearman(delta, y)=0.84, Pearson r=0.53 (r^2 0.28). Median (y168-y24)/(y24-y0) = 9.51 (IQR 7.17-13.50) for 312 parts with delta>0.01. Linear extrapolation: MAE 0.294 vs persistence 0.652; mean residual +0.18 overall, +0.02/+0.18/+0.34 by onset 0/6/12 (median +0.06/+0.19/+0.35); it over-predicts only 20.7%/2.6%/0.9% of parts. Mean trajectory is nearly straight from 24h to 168h (0.246->0.923, increments 0.11-0.12 per 24h). Only 2/96 crossers are unwarned. Moisture onset<=12 behaves similarly but weaker: AUC 0.82, Spearman 0.31, multiplier median 12.0 (IQR 7.5-23.4), linext mean residual +0.45, MAE 0.55 vs 0.72.
  - Design implication: A slope-based feature set already separates this group; what is missing is the gain. A learned multiplier on delta (roughly 9-12 instead of 6, larger for later onset because the first 0-6h of drift is partly cancelled by settling) or a log/ratio target will beat linear extrapolation here. Because the residual is monotone in delta (Spearman 0.83) but only weakly linear (r^2 0.28), a tree/GBM or rank-preserving nonlinearity on delta is more appropriate than a linear coefficient.
- **Healthy settling has a small, consistent downward bias from 24h to 168h that a model can correct, but it is worth only ~0.0005 overall MAE; its real relevance is to interval width and the mean-residual metric.** (confidence high)
  - Evidence: n=4428. Mean normalized trajectory: 0.1315 (0h), 0.1259 (6h), 0.1227 (12h), 0.1192 (24h), 0.1168 (48h), 0.1160 (72h), 0.1157 (168h); settling is essentially complete by 72h. Residual y-persistence: mean -0.0036, median -0.0030, 5-95% [-0.0149, +0.0059]; y/persistence median 0.972 (5-95% 0.89-1.05); 72% of parts fall. Median ratio by profile 0.971/0.974/0.973/0.971. Healthy MAE 0.0056; observation-noise floor |y - y_true| 0.0027; |y_true - persistence| 0.0049. Multiplicative correction x0.972 lowers healthy MAE to 0.0048 and overall MAE 0.1592 -> 0.1587; a perfect oracle on healthy parts only reaches 0.1574. Healthy carries 2.2% of total absolute error; ordinary_noise (n=1196, MAE 0.0162, ratio 0.962) carries 1.7%. 90% quantile of |residual|: healthy 0.0117 vs all parts 0.6008 (51x).
  - Design implication: Include the ~0.97 settling factor (equivalently allow the model to predict slightly below persistence) mainly so the lower interval bound and reported mean bias are honest; do not expect it to move MAE. Intervals must be conditional/heteroscedastic: a single split-conformal radius (~0.60 at 90%) is 50x too wide for 5/6 of parts, while an interval fit on healthy-looking parts alone must still be asymmetric (upper tail) to cover latent defects.
- **Intermittent leakage is a spiky, memoryless trajectory; the 24h reading is itself a spike in 23% of parts, which is why persistence has mean residual +0.095 but median -0.002.** (confidence medium)
  - Evidence: n=204 (onset 6:51, 12:54, 24:58, 48:41). Spike = value > median-of-10 + max(0.10, 1x median); spike frequency by hour 0h 0%, 6h 6%, 12h 15%, 24h 23%, 48-168h 29-33%; spikes per part 0:33, 1:31, 2:31, 3:52, 4:57; amplitude median 0.55, q90 1.53, max 4.9 normalized; baseline median 0.137 (q90 0.60). 24h spike in 47 parts -> mean residual -0.354; no 24h spike (157) -> +0.230; 168h spike in 67 parts (33%) -> +0.566; 109 parts with no spike at 24h or 168h have median residual -0.003. Residual q05 -0.80, q95 +1.19; top 20 parts carry 60% of positive residual mass. Crossers at 168h: 33 observed (26 latent y_true>=1, 72 ever_latent_exceedance); 22 of 33 crossers are 168h spikes, 8 have baseline>=1. 24h features are bimodal: slope_z mean 15.7 vs median 0.38; delta mean 0.245 vs median -0.004. A 24h/0h ratio>2 flags 70 intermittent parts (all 47 spike parts) and 0 healthy/ordinary_noise parts but also 116 other parts. Anchoring on 0h instead of 24h for spike parts reduces MAE only from 0.467 to 0.408; mean(0h,24h) gives 0.401.
  - Design implication: The 168h value of an intermittent part is a coin flip between baseline and a spike, so its point forecast is irreducibly poor (MAE ~0.35-0.4 whatever the anchor). Use a 24h/0h ratio>2 or large positive delta with high current_z as a 'possible spike' flag that (a) shrinks the point forecast toward the 0h/baseline level rather than persisting the spike and (b) widens the interval both ways. Do not let these ~50 parts dominate a squared-error objective; MAE or a robust loss keeps them from dragging healthy predictions up.
- **58% of observed crossings (322/553) have no slope/delta warning at 24h; even counting elevated current level as a warning leaves 267 (48%) unwarned, so the recall ceiling of a 24h-only forecaster is roughly 42-52%.** (confidence high)
  - Evidence: Crossings by scenario: late_abrupt_onset 129 (23.3%, 123 unwarned), accelerating_drift 111 (20.1%, 87 unwarned), tester_channel_fault 103 (18.6%, 70 already >=1 at 24h, 54 unwarned by slope rule of which 24 are onset-0 parts sitting flat at 1.16x limit and 30 are onset-72), gradual_drift 96 (17.4%, 2 unwarned), moisture 81 (14.6%, 38 unwarned), intermittent 33 (6.0%, 18 unwarned). Unwarned crossers by onset: 0h 41/133, 6h 17/69, 12h 41/107, 24h 45/55, 48h 39/41, 72h 49/54, 96h 30/33, 120h 27/28, 144h 33/33. Unwarned crossers are not near-misses: y median 1.35 (IQR 1.18-1.82), 249/322 also exceed latently, only 47 lie in [1,1.1). The loose rule flags 720/6647 non-crossers (10.8%): ordinary_noise 279, gradual_drift 186, healthy 118. Sensitivity: |slope_z|<3 & delta<0.05 -> 350 unwarned (63%) with 387 (5.8%) false flags; |slope_z|<1.5 -> 297 (54%) with 1050 (15.8%) false flags. Will-cross AUC (all parts): limit_fraction 0.739, cur_z 0.736, slope_z 0.666; excluding parts already >=1 at 24h: 0.68/0.68/0.66; onset<=24 crossers vs all non-crossers 0.79-0.81; onset>24 crossers 0.48-0.51.
  - Design implication: Any headline recall/F1 above ~50% at a low false-alarm rate on this data would indicate leakage or over-fitting to batch identity. Set the classification target and threshold expecting recall near 0.4-0.5, and communicate the residual hazard for unflagged parts rather than promising detection. The 70 tester-fault parts already above the limit at both 0h and 24h are trivially predicted by persistence and should not be counted as forecasting skill.
- **Parts that look healthy at 24h (83% of all parts) carry 62% of total persistence absolute error, giving an overall MAE floor of ~0.099 for any 24h-only model, and their residual distribution is a spike at -0.002 with a heavy upper tail.** (confidence high)
  - Evidence: Filter |slope_z|<2 & delta<0.05 & |cur_z|<2 & limit_fraction<0.5 selects 5,997 parts: healthy 4176, ordinary_noise 896, accelerating 321, late_abrupt 255, moisture 128, intermittent 117, tester fault 56, gradual 48; 869 defects and 267 crossers (4.45%); 10.2% end with y>=0.5. Persistence residual in this group: mean +0.110, median -0.0018, MAE 0.1189, q90 0.40, q95 0.82, q99 1.82. Best constant shift (median) leaves MAE at 0.1188. Absolute error 713.3 of 1146.2 total (62.2%) -> if the 1,203 warned parts were forecast perfectly overall MAE would still be 0.0991 vs 0.1592. The warned group has 286 crossers (23.8%), persistence MAE 0.360, mean residual +0.30, and contains 300 ordinary_noise and 252 healthy parts.
  - Design implication: A squared-error objective on the pooled data will push the looks-healthy mass up by ~+0.1 to chase the tail and ruin the 5,000 genuinely healthy forecasts, while an MAE/quantile objective will (correctly) predict persistence x0.97 for them and accept the tail miss. Choose the loss by the deliverable: MAE/median for the point forecast, plus a separate upper quantile (q90 ~ +0.40, q95 ~ +0.82 above persistence) or exceedance probability for the interval. Realistic v2 MAE target is ~0.10-0.13, not near the healthy noise floor.

### Tables

| scenario | onset | n | cross | mean y | mean resid | delta mean/med | slope_z mean/med | cur_z med | AUC vs healthy (delta) |
|---|---|---|---|---|---|---|---|---|---|
| healthy_settling | - | 4428 | 0 | 0.116 | -0.004 | -0.012/-0.011 | -0.19/-0.08 | -0.11 | ref |
| ordinary_noise | - | 1196 | 0 | 0.116 | -0.004 | -0.012/-0.010 | -0.16/-0.04 | -0.09 | - |
| accelerating_drift | 0 | 90 | 30 | 1.080 | +0.924 | +0.003/-0.001 | 1.05/0.56 | 0.58 | 0.62 (all onsets) |
| accelerating_drift | 6 | 86 | 19 | 0.772 | +0.647 | -0.005/-0.006 | 0.30/0.28 | 0.17 | |
| accelerating_drift | 12 | 101 | 31 | 0.948 | +0.806 | -0.008/-0.008 | 0.14/0.09 | 0.12 | |
| accelerating_drift | 24 | 98 | 31 | 0.921 | +0.794 | -0.013/-0.012 | -0.20/-0.14 | -0.14 | |
| gradual_drift | 0 | 116 | 41 | 0.923 | +0.677 | 0.109/0.080 | 8.21/6.33 | 2.32 | 0.98 (all onsets) |
| gradual_drift | 6 | 116 | 24 | 0.862 | +0.642 | 0.077/0.046 | 6.34/4.40 | 1.92 | |
| gradual_drift | 12 | 115 | 31 | 0.839 | +0.637 | 0.049/0.028 | 4.09/2.99 | 1.21 | |
| moisture | 0 | 51 | 15 | 0.850 | +0.656 | 0.065/0.034 | 5.21/3.54 | 1.33 | 0.82 (onset<=24) |
| moisture | 6 | 42 | 19 | 1.033 | +0.767 | 0.061/0.034 | 4.48/3.23 | 1.39 | |
| moisture | 12 | 41 | 15 | 0.987 | +0.760 | 0.041/0.022 | 3.48/2.01 | 1.41 | |
| moisture | 24 | 43 | 14 | 0.837 | +0.692 | 0.007/-0.013 | 0.19/-0.19 | 0.05 | |
| moisture | 48 | 50 | 18 | 0.896 | +0.769 | 0.011/-0.007 | 0.62/0.10 | -0.23 | 0.62 |
| late_abrupt_onset | 48 | 42 | 14 | 1.006 | +0.849 | -0.015/-0.013 | -0.38/-0.20 | 0.08 | 0.42 |
| late_abrupt_onset | 72 | 59 | 21 | 1.048 | +0.918 | 0.002/-0.011 | 0.03/-0.19 | -0.12 | 0.48 |
| late_abrupt_onset | 96 | 64 | 33 | 1.104 | +0.958 | 0.003/-0.010 | 0.17/-0.11 | -0.14 | 0.54 |
| late_abrupt_onset | 120 | 57 | 28 | 1.379 | +1.236 | 0.008/-0.013 | 0.19/-0.23 | -0.12 | 0.45 |
| late_abrupt_onset | 144 | 56 | 33 | 1.212 | +1.089 | -0.010/-0.009 | 0.00/0.05 | -0.10 | 0.57 |
| intermittent | 6 | 51 | 7 | 0.496 | +0.085 | 0.253/-0.004 | 16.4/0.32 | 0.45 | 0.75 (onset<=24) |
| intermittent | 12 | 54 | 7 | 0.451 | +0.080 | 0.208/-0.002 | 15.5/0.64 | 0.80 | |
| intermittent | 24 | 58 | 10 | 0.518 | -0.086 | 0.453/0.265 | 26.5/12.8 | 7.74 | |
| intermittent | 48 | 41 | 9 | 0.554 | +0.383 | -0.011/-0.009 | -0.09/0.03 | 0.05 | 0.53 |
| tester_fault | 0 | 54 | 47 | 1.161 | +0.008 | -0.010/-0.015 | -0.03/-0.25 | 25.9 | - |
| tester_fault | 12 | 28 | 23 | 1.123 | -0.034 | 1.016/0.961 | 25.3/26.9 | 26.3 | - |
| tester_fault | 72 | 63 | 33 | 0.975 | +0.847 | -0.013/-0.012 | -0.18/-0.15 | -0.02 | - |

| will-cross (y>=1) AUC setting | n_pos | n_neg | slope_z | delta | cur_z | limit_frac | pct_change |
|---|---|---|---|---|---|---|---|
| all parts | 553 | 6647 | 0.666 | 0.670 | 0.736 | 0.739 | 0.712 |
| all, excluding already >=1 at 24h | 450 | 6647 | 0.657 | 0.660 | 0.676 | 0.680 | 0.673 |
| onset<=24 crossers vs all non-crossers | 294 | 6647 | 0.793 | 0.794 | 0.812 | 0.808 | 0.811 |
| onset>24 crossers vs all non-crossers | 156 | 6647 | 0.479 | 0.485 | 0.509 | 0.514 | 0.502 |
| onset<=24 crossers vs healthy | 294 | 4428 | 0.822 | 0.822 | 0.832 | 0.826 | 0.845 |
| onset>24 crossers vs healthy | 156 | 4428 | 0.515 | 0.522 | 0.530 | 0.532 | 0.542 |
| within defects onset<=24: cross vs not | 294 | 768 | 0.617 | 0.622 | 0.685 | 0.686 | 0.619 |
| within defects onset>24: cross vs not | 156 | 213 | 0.503 | 0.508 | 0.546 | 0.565 | 0.531 |

| drift scenario (group) | n | cross | Spearman(delta,resid) | Spearman(slope_z,resid) | Pearson r^2 | median mult (y168-y24)/(y24-y0) | persist mean resid / MAE | linext mean resid / MAE | linext over-predicts |
|---|---|---|---|---|---|---|---|---|---|
| gradual_drift (onset<=24) | 347 | 96 | 0.830 | 0.744 | 0.279 | 9.51 (IQR 7.2-13.5, n=312) | +0.652 / 0.652 | +0.183 / 0.294 | 20.7%/2.6%/0.9% by onset 0/6/12 |
| accelerating_drift (onset<=24) | 375 | 111 | 0.132 | 0.122 | 0.043 | 44.6 (n=37 with delta>0.01) | +0.795 / 0.795 | +0.826 / 0.826 | 0% |
| moisture (onset<=24) | 177 | 63 | 0.313 | 0.270 | 0.104 | 11.95 (IQR 7.5-23.4, n=104) | +0.715 / 0.715 | +0.448 / 0.551 | 19.6%/14.3%/0%/2.3% by onset 0/6/12/24 |
| moisture (onset>24) | 50 | 18 | -0.045 | -0.068 | 0.001 | n/a | +0.769 / 0.769 | +0.698 / 0.896 | - |
| late_abrupt_onset (onset>24) | 278 | 129 | 0.004 | -0.015 | 0.000 | n/a | +1.017 / 1.017 | +1.021 / 1.126 | - |
| gradual_drift linext by onset 0/6/12 | 116/116/115 | 41/24/31 | | | | | +0.677/+0.642/+0.637 | +0.025/+0.182/+0.343 (median +0.06/+0.19/+0.35) | |

| scenario | crossings | share of 553 | already >=1 at 24h | unwarned (slope_z<2 & delta<0.05) | unwarned + cur_z<2 & limit_frac<0.5 | median limit_frac@24h | mean y |
|---|---|---|---|---|---|---|---|
| late_abrupt_onset | 129 | 23.3% | 4 | 123 | 115 | 0.119 | 1.78 |
| accelerating_drift | 111 | 20.1% | 3 | 87 | 74 | 0.144 | 1.72 |
| tester_channel_fault | 103 | 18.6% | 70 | 54 | 28 | 1.149 | 1.19 |
| gradual_drift | 96 | 17.4% | 7 | 2 | 0 | 0.270 | 1.64 |
| moisture | 81 | 14.6% | 5 | 38 | 33 | 0.171 | 1.53 |
| intermittent | 33 | 6.0% | 14 | 18 | 17 | 0.168 | 1.68 |
| TOTAL | 553 | 100% | 103 | 322 (58.2%) | 267 (48.3%) | | |
| recall ceiling | | | | 0.418 | 0.517 | | |
| non-crossers flagged by same rule | | | | 720/6647 (10.8%) | | | |

| crossers by onset | 0 | 6 | 12 | 24 | 48 | 72 | 96 | 120 | 144 |
|---|---|---|---|---|---|---|---|---|---|
| n_cross | 133 | 69 | 107 | 55 | 41 | 54 | 33 | 28 | 33 |
| unwarned | 41 | 17 | 41 | 45 | 39 | 49 | 30 | 27 | 33 |

| population | n | crossers | persist MAE | mean resid | median resid | resid q90 / q95 / q99 | abs-error share | 90% |resid| quantile |
|---|---|---|---|---|---|---|---|---|
| healthy_settling | 4428 | 0 | 0.0056 | -0.0036 | -0.0030 | +0.0038 / +0.0059 / +0.0109 | 2.2% | 0.0117 |
| ordinary_noise | 1196 | 0 | 0.0162 | -0.0040 | -0.0040 | - | 1.7% | - |
| looks-healthy at 24h (all 4 conditions) | 5997 | 267 (4.45%) | 0.1189 | +0.110 | -0.0018 | +0.40 / +0.82 / +1.82 | 62.2% | 0.4002 |
| warned at 24h | 1203 | 286 (23.8%) | 0.3599 | +0.302 | - | - | 37.8% | - |
| all parts | 7200 | 553 | 0.1592 | +0.142 | - | - | 100% | 0.6008 |
| intermittent, 24h is spike (retrospective) | 47 | 6 | 0.467 | -0.354 | - | - | - | - |
| intermittent, 24h not spike | 157 | 27 | 0.335 | +0.230 | - | - | - | - |
| healthy bias correction x0.972 | 4428 | - | 0.0048 | overall MAE 0.1592 -> 0.1587 | | | | |
| MAE floor if all warned parts perfect | 7200 | - | 0.0991 | | | | | |

### Caveats

- All data are synthetic; the scenario taxonomy, onset distribution and the very sharp late_abrupt_onset jumps are generator artefacts, so the 42-52% recall ceiling is a property of this simulator, not of real X7R MLCCs.
- No cross-validation was needed because nothing was fitted: AUCs, Spearman/Pearson correlations and quantiles are computed on all 36 training batches. The 'unwarned' thresholds (|slope_z|<2, delta<0.05, |cur_z|<2, limit_fraction<0.5) were fixed a priori, not tuned; a sensitivity table (slope_z 1.5/2/3, delta 0.02/0.05/0.10) shows the unwarned share moves only between 54% and 64%.
- The intermittent-leakage 'spike' definition uses the median of all ten checkpoints as baseline, so it is a retrospective description; the only 24h-available proxy tested (24h/0h ratio>2) captures all 47 spike parts but also flags 116 non-intermittent parts (gradual drift, tester fault onset 12, etc.).
- The growth multiplier (y168-y24)/(y24-y0) is only meaningful for parts with a clearly positive 0->24h delta (>0.01 normalized); it is computed on 312/347 gradual, 104/177 moisture and just 37/375 accelerating parts, so the accelerating figure (44.6) should be read as 'extreme', not as a usable coefficient.
- AUC vs healthy_settling excludes ordinary_noise and other scenarios from the negative class; AUCs against all non-crossers (also reported) are 0.02-0.03 lower for onset<=24 crossers because ordinary_noise parts have larger slope_z dispersion.
- Persistence residuals are in normalized units (y = final_value/upper_limit) and use the observed 168h value, which includes measurement noise (~0.0027 MAE on healthy parts) and any tester fault; 249 of the 322 unwarned crossers also exceed the limit latently, so the finding is not a noise artefact.
- Robust z features are computed within batch over the training parts of that batch exactly as in sih26170.features; in a batch where many parts drift (e.g. gradual-drift-heavy batches), the median slope shifts and z-scores of drifting parts shrink, which may understate their detectability slightly.
- tester_channel_fault onset 0 and 12 parts sit flat at ~1.15x the limit from the fault onwards; persistence 'predicts' them with near-zero residual, so they inflate crossing recall and precision trivially and should be separated in any headline metric.

## Auxiliary early measurements

Script: `outputs/claude_forecast_v2/scratch/diag_auxiliary_signal.py`

The auxiliary 0h/24h measurements carry almost no forecast information beyond leakage. Every aux column's Spearman correlation with the persistence residual r = y - limit_fraction is |rho| < 0.04 overall and < 0.07 within defect parts, versus 0.13 (variability_fraction_of_limit) and 0.35 with |r| (limit_fraction) for the leakage features; capacitance_change_fraction and dissipation_factor_change_pct discriminate is_defect at AUC 0.478 and 0.517 (Cohen's d -0.09 and +0.07), against 0.708 for delta_fraction_of_limit alone. prior_storage_humidity_pct is the only aux column with any signal: AUC 0.610 for moisture_associated_history vs the rest (0.662 on within-batch rank, 0.522 on batch mean), but it does not grade severity inside that scenario (rho = 0.012 with r) and it carries a 72% between-batch variance share plus a spurious batch coincidence with tester-fault batches (their batch-mean humidity 22.8-68.5, 11 of 15 above the 39.8 non-fault mean). In the 5-fold GroupKFold Ridge diagnostic the leakage-only set gives mean MAE 0.2381 vs 0.2376 with all aux and 0.2378 with part-level aux only, differences of 0.0003-0.0006 against fold-to-fold spread of 0.017, and aux wins in only 2/5 folds. Four condition columns (measurement_temperature_c, voltage_stress_ratio, applied_voltage_v, measurement_voltage_v) take exactly one value per batch (36 distinct values, nine per profile) and temperature_c has a 0.989 between-batch variance share, so they are batch identifiers and should be excluded; insulation_resistance_gohm equals measurement_voltage_v/(1000*leakage) to a max relative error of 1.0e-11 and is redundant.

### Findings

- **insulation_resistance_gohm is an exact deterministic transform of leakage and measurement voltage, so it adds no information and must be excluded.** (confidence high)
  - Evidence: Over all 14,400 early rows, max |insulation_resistance_gohm - measurement_voltage_v/(1000*measurement_value)| / expected = 1.013e-11; 0 rows exceed relative error 1e-6.
  - Design implication: Drop insulation_resistance_gohm from any v2 feature list; it would only duplicate limit_fraction (and, because measurement_voltage_v is batch-constant, smuggle in a batch identifier).
- **Four condition columns are pure batch identifiers: measurement_temperature_c, voltage_stress_ratio, applied_voltage_v and measurement_voltage_v each take exactly 1 distinct value per batch (36 distinct values total, 9 per profile), and temperature_c is a noisy batch identifier.** (confidence high)
  - Evidence: distinct_per_batch min=median=max=1 and between_batch_var_share=1.000 for all four; temperature_c has 200 distinct values per batch but between-batch variance share 0.9887 (SD of batch means 1.41 C vs median within-batch SD 0.15 C; 0h->24h within-part change SD 0.21 C). Within each profile the 9 batches have 9 distinct values, so profile + any one condition column uniquely names the batch. Batch-level Spearman of these columns with batch-mean residual (36 points) is weak: 0.17 (vsr), 0.20 (meas temp), 0.34 (meas voltage), 0.14 (temperature_c).
  - Design implication: Exclude CONDITION_COLUMNS and temperature_c from v2 model inputs. With only 36 training batches a model can memorize batch-mean residual through these columns and the effect is invisible in-fold but cannot transfer to unseen batches (and cannot transfer at all to the shifted-condition stress set). If stress level must be represented, use profile_id-level categorical context or a physics prior, not these continuous batch constants.
- **Part-level auxiliary measurements (capacitance and dissipation factor at 0h/24h and their changes) have essentially no relationship to the persistence residual or to defect status.** (confidence high)
  - Evidence: Spearman with r overall: initial_capacitance_fraction 0.009, current_capacitance_fraction 0.009, capacitance_change_fraction -0.002, initial_dissipation_factor_pct -0.014, current_dissipation_factor_pct -0.010, dissipation_factor_change_pct 0.009; within is_defect parts the largest is capacitance_change_fraction at 0.062; within-batch mean Spearman all |rho| <= 0.015. AUC for is_defect: capacitance_change_fraction 0.478 (sign-flipped 0.522), dissipation_factor_change_pct 0.517; for onset<=24 defects vs everything else 0.460 and 0.519. Cohen's d defect vs non-defect: cap change -0.092, DF change +0.070. Scenario means of capacitance_change_fraction all lie in -0.0067..-0.0043 (SD 0.0043); DF change means in -0.0006..+0.0075 (SD 0.049). Reference leakage-only AUCs for is_defect: delta_fraction_of_limit 0.708, slope_batch_robust_z 0.705, limit_fraction 0.650.
  - Design implication: Do not expect capacitance or dissipation-factor features to reduce error on the drift scenarios that dominate MAE; leakage-derived trend features remain the only useful defect signal at 24h. They can be kept as low-priority optional inputs (they are part-level, non-identifying) but should not drive objective or feature design.
- **prior_storage_humidity_pct is the only aux column with a detectable relationship to a scenario, and it is weak: it modestly flags moisture_associated_history membership but does not predict how large the residual will be.** (confidence high)
  - Evidence: AUC(moisture vs rest) = 0.610 on raw humidity (approx. SE 0.019 with 227 positives), 0.662 on within-batch rank, 0.522 on batch mean; moisture parts average 50.6 %RH vs 44.0 for others (Cohen's d +0.39). Threshold view: RH>=50 selects 2,675 parts of which 4.4% are moisture (captures 52% of moisture parts); RH>=70 selects 528 parts, 5.5% moisture, captures 12.8%. Within the 227 moisture parts Spearman(humidity, r) = 0.012 although their mean r is 0.727. Overall Spearman(humidity, r) = 0.035, within-batch 0.022, AUC for is_defect 0.521.
  - Design implication: Humidity is not a severity feature; at most it can shift a prior on moisture-scenario probability, and the enrichment it provides (4-6% moisture prevalence vs 3.2% base rate) is too small to justify a scenario-specific branch or a quantile/interval widening rule on its own. Its within-batch rank is more informative than its raw value, so if kept, a batch-relative transform is preferable.
- **Humidity is largely a batch (storage lot) attribute and coincides with tester-fault batches, creating a spurious batch-level association that a model fit on 36 batches can absorb.** (confidence medium)
  - Evidence: Between-batch variance share 0.722 (SD of batch means 14.7 vs overall SD 17.1; batch means range 21.1-71.6); constant over time (0h->24h change has exactly 1 distinct value, 0). Univariate AUC for is_tester_fault = 0.630, higher than for moisture (0.610); batch-level Spearman(batch-mean humidity, n_tester_fault) = +0.398 across 36 batches vs +0.181 with n_moisture and +0.105 with n_defect; 15 tester-fault batches (12-13 affected parts each) have batch-mean humidity 22.8-68.5, 11 of 15 above the non-fault-batch mean of 39.8 (SD 13.4). The Ridge assigned humidity the largest standardized aux coefficient (0.012-0.014 r-units per SD) in both aux sets.
  - Design implication: Treat prior_storage_humidity_pct as a partial batch identifier: if used, include it only in batch-demeaned or within-batch-rank form and confirm on the held-out calibration batches that it does not degrade; never let it stand in for tester-fault detection, which is a batch/channel phenomenon it only coincidentally tracks in this training draw.
- **In the fixed GroupKFold Ridge diagnostic, adding auxiliary features changes out-of-fold MAE by at most a few ten-thousandths, far inside fold-to-fold noise, so the aux columns add no measurable linear information beyond leakage. This is an information-content diagnostic, not a model selection.** (confidence high)
  - Evidence: 5-fold GroupKFold over batches sorted by batch_id, Ridge(alpha=10) with median imputation + StandardScaler fit per fold on r; forecast = limit_fraction + r_hat clipped at 0. Mean MAE: persistence 0.1595, linear extrapolation 0.2623, (a) leakage-only 10 features 0.2381, (b) +12 aux (21) 0.2376, (c) +part-level aux without condition columns (17) 0.2378. Per-fold MAE(b)-MAE(a): +0.0025, +0.0058, -0.0066, +0.0007, -0.0053 (aux better in 2/5); MAE(c)-MAE(a): -0.0009, +0.0020, -0.0040, +0.0001, +0.0012 (2/5). Fold-to-fold range of MAE(a) is 0.2282-0.2447. Ablations: A+humidity 0.2377 (3/5 folds better, mean -0.0004), A+cap/DF change 0.2382 (mean +0.0000), A+condition columns only 0.2378 (2/5). Defect-only OOF MAE: 0.6089 (a), 0.6106 (b), 0.6094 (c). By scenario, no aux set moves any scenario's OOF MAE by more than 0.004.
  - Design implication: Do not budget v2 modelling effort on auxiliary inputs; the residual error lives in defect-onset timing that leakage trend features only partly capture (Ridge OOF MAE on defects 0.61 vs persistence 0.73) and aux columns do not resolve it. Any apparent aux gain of <0.001 in future experiments should be treated as noise.
- **The linear residual model itself is a poor forecaster on this target, which bounds what this diagnostic can show: it trades a small gain on defects for a large loss on healthy parts.** (confidence medium)
  - Evidence: OOF MAE persistence vs Ridge(a): healthy_settling 0.0056 vs 0.139, ordinary_noise 0.016 vs 0.137, late_abrupt_onset 1.017 vs 0.885, accelerating_drift 0.795 vs 0.648, gradual_drift 0.652 vs 0.449, moisture 0.727 vs 0.560, tester_channel_fault 0.385 vs 0.429, intermittent_leakage 0.365 vs 0.491. Overall Ridge 0.238 vs persistence 0.160 despite lowering defect MAE from 0.731 to 0.610.
  - Design implication: The aux-adds-nothing conclusion is established for additive linear information; a v2 objective that separates the healthy majority (where persistence is near-perfect) from the drift minority is more important than any feature addition, and a nonlinear or mixture-style model would be needed to reopen the aux question, though the univariate AUCs (0.48-0.52 for cap/DF) make a different answer unlikely.
- **Recommended v2 aux allowlist: keep the six part-level capacitance/dissipation-factor features as optional low-priority inputs, keep prior_storage_humidity_pct only in batch-relative form if at all, and exclude all condition/identifier columns.** (confidence high)
  - Evidence: Part-level features have between-batch variance share 0.004-0.007 and 200 distinct values per batch (non-identifying) but AUC 0.48-0.52 and |rho| < 0.015 (no signal). Humidity has between-batch share 0.72, AUC 0.61 for moisture (0.66 within-batch rank), and coincides with tester-fault batches (Spearman 0.40 at batch level). Condition columns have 1 value per batch; temperature_c has between-batch share 0.989. insulation_resistance_gohm is exact V/(1000*I) (rel err 1e-11).
  - Design implication: ALLOW (part-level, non-identifying, near-zero signal): initial_capacitance_fraction, current_capacitance_fraction, capacitance_change_fraction, initial_dissipation_factor_pct, current_dissipation_factor_pct, dissipation_factor_change_pct. CONDITIONAL: prior_storage_humidity_pct as within-batch rank or batch-demeaned value only, verified on calibration batches. EXCLUDE (batch identifiers or redundant): temperature_c, measurement_temperature_c, voltage_stress_ratio, applied_voltage_v, measurement_voltage_v, insulation_resistance_gohm, raw capacitance_nf and nominal_capacitance_nf (profile identifiers: between-batch share 0.998), tester_id, tester_channel, board_position as numeric inputs.

### Tables

| aux feature | distinct/batch (min-max) | distinct total | between-batch var share | batch-identifier-like |
|---|---|---|---|---|
| measurement_temperature_c | 1-1 | 36 | 1.000 | yes |
| voltage_stress_ratio | 1-1 | 36 | 1.000 | yes |
| applied_voltage_v | 1-1 | 36 | 1.000 | yes |
| measurement_voltage_v | 1-1 | 36 | 1.000 | yes |
| temperature_c (24h) | 200-200 | 7200 | 0.989 | yes (noisy setpoint) |
| capacitance_nf raw | 200-200 | 7200 | 0.998 | yes (nominal by profile) |
| prior_storage_humidity_pct | 192-200 | 7172 | 0.722 | partial (lot-level) |
| capacitance_nf 0->24 change | 200-200 | 7200 | 0.458 | partial (nominal scale) |
| initial/current_capacitance_fraction | 200-200 | 7200 | 0.004 | no |
| capacitance_change_fraction | 200-200 | 7200 | 0.004 | no |
| initial/current_dissipation_factor_pct | 200-200 | 7200 | 0.007 | no |
| dissipation_factor_change_pct | 200-200 | 7200 | 0.005 | no |
| insulation_resistance_gohm | - | - | - | redundant: = V/(1000*I), rel err 1e-11 |

| feature | Spearman r (all) | Spearman r (within-batch mean) | Spearman r (defects) | AUC is_defect | AUC moisture | AUC tester_fault |
|---|---|---|---|---|---|---|
| prior_storage_humidity_pct | 0.035 | 0.022 | 0.039 | 0.521 | 0.610 | 0.630 |
| capacitance_change_fraction | -0.002 | -0.001 | 0.062 | 0.478 | 0.483 | 0.501 |
| dissipation_factor_change_pct | 0.009 | 0.009 | 0.009 | 0.517 | 0.504 | 0.525 |
| current_capacitance_fraction | 0.009 | 0.008 | 0.014 | 0.511 | 0.497 | 0.505 |
| current_dissipation_factor_pct | -0.010 | -0.010 | -0.036 | 0.503 | 0.482 | 0.489 |
| temperature_c | 0.000 | -0.025 | 0.065 | 0.499 | 0.488 | 0.517 |
| measurement_voltage_v | 0.016 | n/a (batch const) | 0.037 | 0.506 | 0.526 | 0.606 |
| voltage_stress_ratio | -0.006 | n/a | 0.027 | 0.507 | 0.540 | 0.487 |
| ref: delta_fraction_of_limit | 0.025 | 0.021 | -0.047 | 0.708 | 0.726 | 0.592 |
| ref: variability_fraction_of_limit | 0.131 | 0.134 | 0.023 | 0.618 | 0.622 | 0.671 |
| ref: limit_fraction | -0.048 | -0.047 | 0.012 | 0.650 | 0.636 | 0.819 |

| fold | test parts | persistence | linear extrap | (a) leakage-only 10 | (b) +all aux 21 | (c) +aux no condition 17 |
|---|---|---|---|---|---|---|
| 0 | 1600 | 0.1476 | 0.2665 | 0.2343 | 0.2368 | 0.2334 |
| 1 | 1400 | 0.1393 | 0.2654 | 0.2282 | 0.2341 | 0.2302 |
| 2 | 1400 | 0.1685 | 0.2387 | 0.2447 | 0.2381 | 0.2407 |
| 3 | 1400 | 0.1714 | 0.2691 | 0.2438 | 0.2445 | 0.2439 |
| 4 | 1400 | 0.1709 | 0.2720 | 0.2397 | 0.2345 | 0.2409 |
| mean | 1440 | 0.1595 | 0.2623 | 0.2381 | 0.2376 | 0.2378 |
| (b)-(a) per fold | | | | | +0.0025, +0.0058, -0.0066, +0.0007, -0.0053 (2/5 better) | |
| (c)-(a) per fold | | | | | | -0.0009, +0.0020, -0.0040, +0.0001, +0.0012 (2/5 better) |

| Ridge ablation (same GroupKFold protocol) | mean MAE | mean MAE defects only | folds better than (a) |
|---|---|---|---|
| (a) leakage-only (10) | 0.2381 | 0.6089 | - |
| (a) + prior_storage_humidity_pct (11) | 0.2377 | 0.6085 | 3/5 |
| (a) + cap & DF change (12) | 0.2382 | 0.6091 | 3/5 (deltas within 0.0002) |
| (a) + all part-level aux (17) | 0.2378 | 0.6087 | 2/5 |
| (a) + condition columns only (14) | 0.2378 | 0.6098 | 2/5 |

| scenario | n | mean humidity %RH | mean cap change frac | mean DF change pct | mean r | OOF MAE persistence | OOF MAE Ridge (a) | Ridge (b) |
|---|---|---|---|---|---|---|---|---|
| healthy_settling | 4428 | 43.7 | -0.0049 | -0.0001 | -0.004 | 0.0056 | 0.139 | 0.138 |
| ordinary_noise | 1196 | 44.2 | -0.0047 | -0.0006 | -0.004 | 0.016 | 0.137 | 0.137 |
| accelerating_drift | 375 | 44.3 | -0.0047 | 0.0017 | 0.795 | 0.795 | 0.648 | 0.650 |
| gradual_drift | 347 | 44.3 | -0.0058 | 0.0023 | 0.652 | 0.652 | 0.449 | 0.453 |
| late_abrupt_onset | 278 | 45.2 | -0.0043 | 0.0039 | 1.017 | 1.017 | 0.885 | 0.884 |
| moisture_associated_history | 227 | 50.6 | -0.0052 | 0.0027 | 0.727 | 0.727 | 0.560 | 0.557 |
| intermittent_leakage | 204 | 42.5 | -0.0067 | 0.0075 | 0.095 | 0.365 | 0.491 | 0.494 |
| tester_channel_fault | 145 | 52.0 | -0.0050 | 0.0022 | 0.364 | 0.385 | 0.429 | 0.428 |

### Caveats

- All data are synthetic; the absence of capacitance/dissipation-factor signal reflects how the generator was built (aux columns appear to be drawn independently of the leakage mechanism apart from a humidity shift for the moisture scenario) and says nothing about real X7R physics.
- The fitted diagnostic is a single Ridge(alpha=10) on the persistence residual with the prototype's default alpha; it is a weak forecaster (OOF MAE 0.238 vs persistence 0.160) because it spreads the defect-driven positive residual onto healthy parts. The 'aux adds nothing' conclusion is therefore about additive linear information; a nonlinear model was deliberately not tried per the assignment, although the univariate AUCs of 0.48-0.52 make a different outcome unlikely.
- Fold-to-fold MAE spread (0.228-0.245 for the leakage-only set) is 20-50x larger than any aux-induced difference, and with only 5 folds over 36 batches no formal significance test is meaningful; the per-fold win counts (2/5 or 3/5) are reported instead.
- The humidity/tester-fault coincidence (batch-level Spearman 0.40 over 36 batches) is a property of this training draw; it could not be checked on calibration or test batches, which were kept away from this analysis.
- prior_storage_humidity_pct has 7,172 distinct values across 7,200 parts and a 0.72 between-batch variance share; the 'lot-level' interpretation is inferred from the variance decomposition, not from generator documentation.
- Univariate AUC standard errors are approximately 0.019 for the moisture label (227 positives) and 0.008 for is_defect (1,431 positives), so AUC 0.610 is distinguishable from chance while 0.478/0.517 are not meaningfully so.
- The script also writes diag_auxiliary_signal_*.csv/json and a stdout capture next to itself; those are the only files created, and nothing under src/ was modified.

## Tester/channel faults and batch structure

Script: `outputs/claude_forecast_v2/scratch/diag_tester_faults_and_batch_effects.py`

Tester faults are perfectly channel-structured: the 190 is_tester_fault parts are exactly 15 batches x one channel each x every part on that channel (15/15 channels 100% faulted, 0 unflagged parts on those channels), with onsets 0 h (6 batches, 76 parts), 12 h (3 batches, 37) and 72 h (6 batches, 77). The fault is an additive offset of about +1.0 x upper_limit that persists to 168 h (median excess over healthy batch median 1.06-1.09 for onset 0, 0.98 for onset 12, 0.86 for onset 72), so observed final_value differs from true_final_value by MAE 0.957 limit-units for faulted parts versus 0.0073 for everyone else, 130 of the 553 observed crossings (23.5%) are pure instrument artifacts, and 98 of the 116 parts already over the limit at 24 h are tester faults whose persistence residual is ~0 (median -0.008). Onset-0/12 faults are trivially visible at 24 h (batch robust z median 26, AUC 0.997) and a leave-one-out within-(batch, channel) peer statistic separates them from real defects with zero false positives (peer flag: 113 flagged, all faulted; among the 351 z>3 parts AUC 0.988-0.998 vs 0.92-0.93 for the part's own z), while onset-72 faults are invisible at 24 h (AUC 0.48-0.56) and contribute 6.8% of total persistence absolute error that no 24 h model can remove. Batch structure is weak for the residual (ICC 0.0038 within batch, 0.0007 healthy-only; per-batch persistence MAE mean 0.159 sd 0.040 range 0.071-0.264; 5-fold GroupKFold persistence MAE 0.139-0.171, sd 0.015) and batch-level 24 h aggregates carry no information about individual residuals (|Spearman| <= 0.026, partial <= 0.015 given the part's own feature); their batch-crossing correlations (0.53-0.60, n=36) shrink to 0.22-0.53 once the 15 fault batches are removed (null 95th pct 0.43). After dividing by the limit the four profiles are essentially interchangeable (healthy delta_fraction medians -0.0106 to -0.0110, residual 95th pct 0.0105-0.0126, measurement noise 0.0042-0.0046 limit-units in every profile, defect growth multiple 4.0-4.3), so one shared normalized model is justified.

### Findings

- **Tester faults hit whole channels: every is_tester_fault part sits on one of 15 (batch_id, tester_channel) cells, each cell is 100% faulted, and no other channel in those batches is affected.** (confidence high)
  - Evidence: 190 faulted parts = 15 batches x 1 channel x 12-13 parts; affected cells: n_fault/n_parts = 1.000 in all 15 (min=max=1.0); 0 non-flagged parts on affected channels; 21 of 36 batches have no fault. Onsets: 0 h in B041,B042,B043,B046,B050,B054 (76 parts); 12 h in B011,B044,B049 (37); 72 h in B005,B007,B012,B024,B027,B033 (77). Defects per (batch,channel) cell have var/mean 0.80 (Poisson-like, not clustered); tester faults var/mean 12.4. 145 faulted parts are otherwise healthy/ordinary (scenario tester_channel_fault), 45 coexist with a defect.
  - Design implication: A shared-channel anomaly is the only structure in the data that is channel-local, so a within-(batch, tester_channel) peer statistic is a clean discriminator between 'elevated because the instrument is off' and 'elevated because the part is degrading'. Any explanation/decision layer should emit an explicit 'suspected channel fault' reason when >=50% of channel peers are jointly elevated.
- **The fault is an additive offset of roughly one upper_limit that persists to 168 h; it is the dominant source of observed-vs-latent target noise and of spurious observed crossings.** (confidence high)
  - Evidence: Median excess of tester_channel_fault parts over the healthy batch median (limit units) at hours 0..168: onset 0 = 1.06-1.09 at every hour; onset 12 = 0.005 at 0/6 h then 0.98/0.98/0.96/0.99/0.91/0.97/1.00/0.94; onset 72 = 0.002-0.004 through 48 h then 0.87/0.84/0.85/0.87/0.86. Healthy noise band (5-95%) is -0.05 to +0.07. |final_value - true_final_value|/limit: faulted MAE 0.957 (mean +0.957, p90 1.157, max 1.237, 0.371 uA raw) vs non-faulted MAE 0.0073 (median 0.003, p90 0.018; healthy_settling 0.0027, ordinary_noise 0.0108, defect scenarios 0.042-0.056). 190 faulted parts (2.6% of rows) carry 77.9% of total |observed - latent|. 152 parts disagree on observed vs latent exceedance; 130 are tester faults (observed True, latent False) = 23.5% of the 553 observed crossings; only 16 of 190 faulted parts truly exceed.
  - Design implication: The regression target (observed final_value) legitimately contains the offset, so for onset-0/12 faulted parts the correct forecast is 'stay at the 24 h reading' and the model must not extrapolate. Classification-style metrics on is_observed_final_exceedance will reward flagging channel faults as crossings; if the product wants physical failures, report is_future_failure separately and show that 130 observed crossings are instrument artifacts.
- **Onset-0/12 faults are trivially detectable at 24 h with existing features, but onset-12 faults masquerade as an enormous 0->24 h jump that wrecks linear extrapolation.** (confidence high)
  - Evidence: 24 h medians: onset 0 limit_fraction 1.20, current_batch_robust_z 26.2, delta_fraction -0.009; onset 12 limit_fraction 1.09, z 26.2, delta_fraction 0.961, slope_batch_robust_z 26.9; onset 72 limit_fraction 0.129, z 0.05 (healthy 0.114, -0.10). AUC for is_tester_fault by onset using current_batch_robust_z: 0.9974 (onset 0), 0.9976 (12), 0.533 (72); limit_fraction 0.998/0.998/0.556. Linear extrapolation on the 37 onset-12 parts: median forecast 6.86 vs observed y median 1.10, MAE 6.08, 11.9% of ALL linear-extrapolation absolute error (225 of 1890); the three onset-12 batches have the worst per-batch lin MAE (0.53, 0.60, 0.65 vs 0.16-0.37 elsewhere).
  - Design implication: Do not use raw slope/linear extrapolation as a base learner or as a feature without a channel-peer guard; a tree model will otherwise learn that huge delta_fraction sometimes means 'no further growth' from only 37 examples in 3 batches. Cap or winsorize slope features and give the model the peer flag so it can route these parts to persistence.
- **98 of the 116 parts already at or over the limit at 24 h are tester faults for which persistence is essentially exact; the remaining 18 are intermittent_leakage parts that fall back below.** (confidence high)
  - Evidence: limit_fraction >= 1 at 24 h: 116 parts = 72 tester_channel_fault + 26 defect-with-fault (onsets 0:64, 12:33, 72:1) + 18 intermittent_leakage (no fault). Residual y - persistence: faulted median -0.008, mean +0.119, MAE 0.167; intermittent mean -0.447, median -0.590, MAE 0.869. Observed final exceedance rate: 96.9% (faulted) vs 44.4% (intermittent).
  - Design implication: Over-limit-at-24 h is not a single regime: with the peer flag the model can keep faulted parts at persistence while learning that isolated over-limit spikes revert (negative residual). Without the flag it sees mixed signs for the same limit_fraction and averages them.
- **Onset-72 tester faults are an irreducible 6.8% of total persistence absolute error and cannot be predicted from 24 h data.** (confidence high)
  - Evidence: 77 onset-72 parts: persistence MAE 1.018 (mean residual +1.018), sum |resid| 78.4 of 1146.2 total (6.84%); versus latent truth their persistence MAE is only 0.170. All 24 h features have AUC 0.48-0.56 for these parts; every peer statistic has AUC 0.50-0.65 for them. By contrast onset-0/12 parts have persistence MAE 0.19 vs observed but 0.92-0.93 vs latent (offset persists, so persistence is right about the observed target).
  - Design implication: Set the error floor: even a perfect 24 h model retains ~0.011 normalized MAE (78.4/7200) from onset-72 faults, and conformal intervals cannot cover them (residual ~1.0 vs 90% radius 0.60). Expect per-batch coverage to drop to ~0.82-0.84 in the 6 onset-72 batches (B007 0.820, B033 0.835).
- **A leave-one-out within-(batch, tester_channel) peer statistic is a near-perfect, zero-false-positive detector of visible channel faults and resolves the defect-vs-fault ambiguity that the part's own z-score cannot.** (confidence high)
  - Evidence: LOO channel median of current_batch_robust_z: AUC 1.000 for onset-0/12 faults, 0.829 for all 190 (onset 72 undetectable). Peer flag = fraction of channel peers with z>3 >= 0.5: flags 113 parts, all faulted (76 onset-0 + 37 onset-12), 0 of 7010 non-faulted flagged. Among the 351 parts with own z>3 (115 faulted, 215 defects, 53 healthy/ordinary): AUC for is_tester_fault = 0.988 (peer frac z>3), 0.995 (peer median z), 0.998 (peer median limit_fraction) vs 0.919 (own z), 0.932 (own limit_fraction); confusion: flagged 113/0, unflagged 2/236. Residual within z>3 group: peer-flagged mean 0.151 (median 0.009) vs unflagged mean 0.451 (median 0.235); Spearman(peer stat, resid | z>3) -0.13 to -0.17. Whole-population Spearman with residual is ~0 (|rho| <= 0.02) because only 1.6% of parts are affected. tester_id and tester_channel identities carry no cross-batch information (mean residual by tester 0.139-0.145; Kruskal residual~channel p=0.09).
  - Design implication: Add LOO peer features computed only from same-upload, same-batch, <=24 h rows: channel median of current_batch_robust_z (or of limit_fraction) and fraction of channel peers with z>3; never use tester_channel or tester_id as a categorical. Fairness: tester_channel is instrument metadata present in the upload and the data dictionary explicitly earmarks it for shared-measurement-error investigation; it is the same class of input as current_batch_robust_z (batch peers), so I consider it a fair inference-time input provided (a) the statistic degrades to NaN/0 when fewer than ~5 channel peers are uploaded, (b) it is surfaced as a data-quality reason code, not a component property, and (c) the manifest states the synthetic fault model (whole channel, ~1x limit offset) it was validated on.
- **Between-batch variation in persistence error is moderate and mostly explained by defect prevalence; the 5-fold GroupKFold spread the experiment runner should expect is about +/-0.015 MAE.** (confidence high)
  - Evidence: Per-batch persistence MAE (n=36): mean 0.1592, sd 0.0396, CV 0.25, min 0.0711 (B003), max 0.2639 (B007); Spearman with batch defect count 0.60 (p=1e-4) and with batch crossings 0.51. Per-batch crossings mean 15.4 sd 6.4 (4-29); defects mean 39.8 sd 5.7 (26-52). GroupKFold(5) on sorted batches gives 8/7/7/7/7 batches per fold; persistence MAE per fold 0.1476, 0.1393, 0.1685, 0.1714, 0.1709 (mean 0.1595, sd 0.0150); linear extrapolation 0.2665, 0.2654, 0.2387, 0.2691, 0.2720; crossings per fold 102/110/124/114/103; tester-faulted parts per fold 24/38/37/52/39. Fold 1 contains no SIM_X7R_1U_25V batches and fold 2 no SIM_X7R_10N_50V batches. Fold membership: f0 B003,B010,B015,B025,B037,B044,B050,B058; f1 B009,B014,B024,B036,B043,B049,B057; f2 B008,B013,B022,B033,B042,B047,B054; f3 B007,B012,B021,B028,B041,B046,B053; f4 B005,B011,B016,B027,B039,B045,B051.
  - Design implication: A model improvement smaller than ~0.015 normalized MAE on a single fold is within fold noise; report the per-fold vector and compare fold-by-fold against these persistence numbers. sklearn GroupKFold does not produce contiguous folds, and two folds miss a profile entirely, so pin the exact fold membership (or use the batch_id list above) for reproducibility.
- **Within-batch dependence of the persistence residual is tiny (ICC 0.004); the dependence that matters for conformal coverage is within the tester channel, and it is entirely due to the fault offset.** (confidence high)
  - Evidence: ICC(1) one-way ANOVA: residual within batch 0.0038 (F=1.76), |residual| 0.0039, y 0.0063; healthy-only residual ICC 0.0007 (per-batch mean residual sd 0.00096 vs within-batch sd 0.0114). Within (batch, channel): residual 0.051, y 0.123, observed-latent noise 0.990 (F=1273), linear-extrapolation residual 0.317. Design effect for a 200-part batch: 1.75 (effective n ~4100 of 7200). Pooled 90% |residual| radius 0.601; per-batch coverage of that radius mean 0.900, sd 0.0287 vs binomial reference 0.0212, min 0.820 (B007), max 0.955; excluding onset-72 faulted parts sd 0.0238, min 0.865.
  - Design implication: Split conformal on pooled residuals is close to exchangeable at the batch level (coverage inflation modest), so calibrating on whole held-out batches is sufficient; there is no need for batch-level random effects. The channel is the real cluster: an onset-72 fault fails 12-13 parts at once, so per-batch coverage will dip ~6% in such batches. Quote empirical per-batch coverage with its range, not a marginal guarantee.
- **Batch-level 24 h aggregates carry no information about an individual part's residual and their batch-level correlations are largely a tester-fault artifact; including them risks memorizing 36 batches for no gain.** (confidence high)
  - Evidence: Spearman(aggregate mapped to part, part residual), n=7200: b_med_delta +0.015, b_med_lf -0.026, b_frac_slopez3 -0.003, b_frac_curz3 -0.006, b_p90_delta -0.010, b_frac_ge_limit -0.012; partial Spearman given the part's own delta_fraction_of_limit or slope_batch_robust_z |rho| <= 0.015. Spearman with batch crossing count, n=36: b_frac_ge_limit 0.60, b_frac_curz3 0.55, b_frac_slopez3 0.54, b_p90_delta 0.53, b_med_lf 0.30, b_med_delta -0.05 (permutation null 95th pct 0.33); on the 21 batches without a tester fault: 0.22, 0.43, 0.53, 0.28, 0.20, -0.01 (null 95th pct 0.43); against latent crossings: 0.12, 0.27, 0.50, 0.44, 0.30, 0.02. A fault channel adds 12-13 observed crossings and +0.06-0.065 to b_frac_curz3/b_frac_ge_limit. Distinct values: 36 for medians/p90, 14-15 for the fraction features, 6 for b_frac_ge_limit.
  - Design implication: Exclude batch-level aggregates from the v2 feature set: with 36 distinct values a tree can isolate individual training batches, GroupKFold will show no out-of-batch gain, and the only real signal (defect prevalence via b_frac_slopez3, rho 0.50 with latent crossings) is already present in each part's own slope_batch_robust_z. If any batch-level quantity is kept, make it a coarse data-quality count (e.g., number of channels flagged) rather than a continuous feature.
- **Dividing by upper_limit makes the four profiles (limits 0.12/0.25/0.7/1.3 uA) comparably distributed; a shared normalized model is justified and separate per-profile models are not.** (confidence medium)
  - Evidence: Healthy-only after normalization: limit_fraction median 0.121/0.114/0.112/0.110 (5-95%: 0.069-0.206, 0.069-0.190, 0.066-0.180, 0.067-0.180; Kruskal p=4e-13 but a 10% shift); delta_fraction_of_limit median -0.0110/-0.0109/-0.0106/-0.0107 (p=0.54); residual median -0.0031 to -0.0033, 95th pct 0.0126/0.0115/0.0105/0.0105 (p=0.84); observed-latent noise MAE 0.0046/0.0043/0.0044/0.0042 limit-units (0.0012/0.0005/0.0031/0.0055 uA raw; ~2.2% of true value in every profile). y 99th pct 2.26/2.34/2.14/2.06; Spearman(y, limit_fraction) 0.74/0.76/0.74/0.73; defects with onset<=12: median growth multiple y/limit_fraction 4.26/4.01/3.98/4.33. Scenario mix per profile is balanced (defects 354-361). Profile SIM_X7R_100N_50V has higher persistence MAE 0.1925 vs 0.1475-0.1487, but 6 of the 15 fault batches are 100N (88 faulted parts vs 20-51): without faulted parts 0.163 vs 0.143-0.146, defects-only 0.794 vs 0.693-0.704, healthy-only 0.0081 vs 0.0077-0.0079; crossings 199 vs 105-140 (126 vs 92-95 without faults).
  - Design implication: Keep the limit-normalized target and features and fit one model on all profiles (separate models would have ~7 training batches per fold). Do not add profile_id or upper_limit as features unless a later check shows the 100N residual gap survives GroupKFold; the residual difference seen here is dominated by the uneven placement of fault batches across profiles, not by normalization failure.

### Tables

| Tester fault onset | batches | parts | 24h median batch z | 24h median delta_frac | AUC own z for fault | persistence MAE vs observed | persistence MAE vs latent | share of total |resid| |
|---|---|---|---|---|---|---|---|---|
| 0 h | 6 | 76 | 26.2 | -0.009 | 0.997 | 0.195 | 0.917 | 1.3% |
| 12 h | 3 | 37 | 26.2 | 0.961 | 0.998 | 0.186 | 0.933 | 0.6% |
| 72 h | 6 | 77 | 0.05 | -0.012 | 0.533 | 1.018 | 0.170 | 6.8% |
| none | 36 (7010 parts) | 7010 | -0.01 | -0.010 | - | 0.149 | 0.148 | 91.3% |

| Observed vs latent 168 h (limit units) | n | MAE | mean | median abs | p90 abs |
|---|---|---|---|---|---|
| is_tester_fault = False | 7010 | 0.0073 | -0.0001 | 0.0030 | 0.018 |
| is_tester_fault = True | 190 | 0.957 | +0.957 | 1.042 | 1.157 |
| healthy_settling | 4428 | 0.0027 | 0.0001 | - | 0.0059 |
| ordinary_noise | 1196 | 0.0108 | 0.0001 | - | 0.023 |
| defect scenarios (4) | 375/347/278/227 | 0.042-0.056 | 0.020-0.036 | - | 0.052-0.064 |
| Exceedance disagreement (observed != latent) | 152 | 130 tester faults (obs True, latent False), 13 obs-only, 9 latent-only |

| Peer / own feature | Spearman resid (all) | AUC fault all 190 | AUC fault onset 0/12 | AUC fault among z>3 (n=351) | Spearman resid among z>3 |
|---|---|---|---|---|---|
| ch_med_z_loo (LOO channel median batch z) | 0.003 | 0.829 | 1.000 | 0.995 | -0.135 |
| ch_med_lf_loo | -0.015 | 0.821 | 1.000 | 0.998 | -0.171 |
| ch_frac_elev_z3_loo (frac peers z>3) | -0.005 | 0.785 | 1.000 | 0.988 | -0.126 |
| ch_med_delta_loo | -0.012 | 0.569 | 0.652 | - | - |
| own current_batch_robust_z | -0.045 | 0.809 | 0.998 | 0.919 | -0.282 |
| own limit_fraction | -0.048 | 0.819 | 0.998 | 0.932 | -0.273 |
| own delta_fraction_of_limit | 0.025 | 0.592 | 0.671 | 0.415 | -0.122 |
| Peer flag (frac peers z>3 >= 0.5): flagged 113 = all onset-0/12 faults, 0 of 7010 non-fault; among z>3: mean resid flagged 0.151 vs unflagged 0.451 |

| GroupKFold fold (sorted batches) | n batches | persistence MAE | linear MAE | RMSE | crossings | defects | tester-faulted | profiles missing |
|---|---|---|---|---|---|---|---|---|
| 0 | 8 | 0.1476 | 0.2665 | 0.444 | 102 | 302 | 24 | none |
| 1 | 7 | 0.1393 | 0.2654 | 0.405 | 110 | 245 | 38 | 1U_25V |
| 2 | 7 | 0.1685 | 0.2387 | 0.476 | 124 | 286 | 37 | 10N_50V |
| 3 | 7 | 0.1714 | 0.2691 | 0.460 | 114 | 300 | 52 | none |
| 4 | 7 | 0.1709 | 0.2720 | 0.461 | 103 | 298 | 39 | none |
| mean / sd | - | 0.1595 / 0.0150 | 0.2623 | - | - | - | - | - |
| per-batch (n=36) | - | mean 0.159, sd 0.040, min 0.071 (B003), max 0.264 (B007) | | | mean 15.4, sd 6.4 | mean 39.8, sd 5.7 | | |

| ICC(1) quantity | within batch | within (batch, channel) | within profile |
|---|---|---|---|
| persistence residual | 0.0038 (F=1.76) | 0.051 | 0.0026 |
| abs residual | 0.0039 | 0.051 | 0.0022 |
| y | 0.0063 | 0.123 | 0.0052 |
| observed - latent noise | 0.036 | 0.990 (F=1273) | 0.012 |
| linear-extrapolation residual | 0.019 | 0.317 | 0.0014 |
| healthy-only residual | 0.0007 | - | - |
| Design effect (200-part batch) 1.75; effective n ~4100 of 7200. Pooled 90% radius 0.601: per-batch coverage mean 0.900, sd 0.029 (binomial 0.021), min 0.820 (B007), max 0.955 |

| Batch aggregate (36 values) | Spearman w/ part resid | partial | own delta | Spearman w/ batch crossings (n=36) | same, 21 no-fault batches | w/ latent crossings | distinct values |
|---|---|---|---|---|---|---|
| b_frac_ge_limit | -0.012 | - | 0.599 | 0.223 | 0.124 | 6 |
| b_frac_curz3 | -0.006 | -0.007 | 0.555 | 0.428 | 0.269 | 15 |
| b_frac_slopez3 | -0.003 | -0.004 | 0.541 | 0.526 | 0.502 | 14 |
| b_p90_delta | -0.010 | -0.011 | 0.532 | 0.282 | 0.443 | 36 |
| b_med_lf | -0.026 | - | 0.297 | 0.204 | 0.296 | 36 |
| b_med_delta | 0.015 | 0.013 | -0.045 | -0.010 | 0.015 | 36 |
| permutation null 95th pct of |Spearman|: 0.334 (n=36), 0.433 (n=21) |

| Profile (limit uA) | healthy limit_fraction median (5-95%) | healthy delta_frac median | healthy resid p95 | noise MAE limit-units (uA) | y p99 | persistence MAE all / no-fault / defects-only / healthy | crossings all / no-fault | tester-faulted |
|---|---|---|---|---|---|---|---|---|
| SIM_X7R_10N_50V (0.12) | 0.114 (0.069-0.190) | -0.0109 | 0.0115 | 0.0043 (0.0005) | 2.34 | 0.148 / 0.146 / 0.703 / 0.0079 | 140 / 95 | 51 |
| SIM_X7R_100N_50V (0.25) | 0.121 (0.069-0.206) | -0.0110 | 0.0126 | 0.0046 (0.0012) | 2.26 | 0.193 / 0.163 / 0.794 / 0.0081 | 199 / 126 | 88 |
| SIM_X7R_1U_25V (0.7) | 0.112 (0.066-0.180) | -0.0106 | 0.0105 | 0.0044 (0.0031) | 2.14 | 0.148 / 0.143 / 0.693 / 0.0077 | 109 / 94 | 26 |
| SIM_X7R_4U7_16V (1.3) | 0.110 (0.067-0.180) | -0.0107 | 0.0105 | 0.0042 (0.0055) | 2.06 | 0.149 / 0.145 / 0.704 / 0.0077 | 105 / 92 | 25 |
| Kruskal healthy: limit_fraction p=4e-13 (10% shift), delta_frac p=0.54, resid p=0.84; defect growth multiple (onset<=12) 4.01-4.33 |

### Caveats

- All data are synthetic; the tester-fault model is idealized (every part on exactly one channel per affected batch, a near-constant additive offset of ~1x upper_limit, only three onset times 0/12/72 h, offset persists unchanged to 168 h). Real channel faults may be partial, intermittent or scale-dependent, so the zero-false-positive peer flag and the AUC=1.000 numbers are upper bounds.
- Peer statistics were computed with all 200 parts of each batch present (12-13 parts per channel). At inference a partial upload (few parts per channel) will make the leave-one-out channel median noisy or undefined; the feature needs a minimum-peer-count fallback and a manifest note.
- tester_channel is instrument metadata, not a component property; I judge a within-upload peer statistic fair because it is the same class of input as the existing batch robust z and the data dictionary earmarks tester_channel for shared-error investigation, but the categorical identity of channel/tester must never be a feature (no cross-batch information: residual by tester 0.139-0.145, Kruskal by channel p=0.09).
- No predictive model was fitted; all evidence is descriptive (Spearman, AUC, ICC, quantiles). Spearman on n=36 batches has a permutation null 95th percentile of 0.33 (0.43 for n=21), so batch-level correlations near 0.5 are only moderately significant and the no-fault subset is underpowered.
- The GroupKFold fold membership reported comes from sklearn 1.9.0 GroupKFold(n_splits=5) with default (non-shuffled) settings on data sorted by batch_id then component_id; it is not contiguous in batch order and a different sklearn version or shuffle setting would change the folds and therefore the per-fold MAE vector.
- Kruskal-Wallis p-values on 5624 healthy parts detect very small shifts (the 100N profile healthy limit_fraction median is 0.121 vs 0.110-0.114); the practical difference is about 10% and disappears in delta_fraction and residual distributions.
- The profile SIM_X7R_100N_50V shows a residual gap even after removing tester faults (defects-only MAE 0.79 vs 0.69-0.70; 126 vs 92-95 crossings); with 9 batches per profile this could be sampling variation in defect severity rather than a normalization failure, and it was not tested further.
- Onset-72 fault parts are counted as irreducible from 24 h data on the basis of AUC ~0.5 for every available feature; a model could still reduce their contribution indirectly only by predicting the batch-level fault probability, which is 6 of 36 batches and unlearnable.
- The 18 intermittent_leakage parts that are over the limit at 24 h (mean residual -0.45) were noted but belong to another angle; their reversion behaviour was not analysed further.

## Prediction-interval design

Script: `outputs/claude_forecast_v2/scratch/diag_interval_design.py`

Persistence residuals r = y - limit_fraction (7,200 parts, 36 batches) are extremely heteroscedastic and one-sided: healthy parts have median |r| 0.0052 (p90 0.017) while defect parts have median r 0.55 and p95 1.95, so the v1-style single symmetric 90% radius (0.60, width 1.20) covers 100% of healthy parts, only 53% of defects (37% of late_abrupt_onset) and 59% of tester-fault parts, and is 229x the healthy median error; 97.8% of its lower bounds fall below zero leakage and it misses 700 parts above vs 19 below. Nested whole-batch calibration is stable in coverage but not in radius: with 4/6/8 calibration batches the validation coverage across 5 GroupKFold folds is 0.874-0.914 (sd 0.011-0.014) while the radius swings 0.42-0.72 (max/min 1.5-1.7x) depending on which batches are used, because the 90% quantile sits inside the ~20% defect tail. Within-batch dependence is modest (ICC of r 0.0038, design effect 1.75, n_eff ~4,100; coverage-indicator ICC 0.0043, design effect 1.85), but tester faults cluster strongly (design effect 7.8) and per-batch coverage of the single radius ranges 0.82-0.955 with 18/36 batches below 0.90 and profile 100N_50V occupying the 6 lowest. Asymmetric residual quantiles stratified by slope_batch_robust_z (<2, 2-5, >=5) keep overall coverage at 0.894 (fold sd 0.007) while raising defect coverage from 0.51 to 0.76, lifting z>=5 coverage from 0.43 to 0.94, cutting median width from 1.15 to 0.80, and eliminating sub-zero lower bounds (3.8% vs 97.8%). The hard floor: even the quietest 0/24h-definable stratum (77% of parts) still contains 13.5% defects (308 with onset >24h), so its 90% upper margin is 0.35 and its 95% margin 0.79 versus a healthy-only 95th percentile of 0.011; narrow intervals for the healthy majority are only possible below ~85% nominal coverage or with a forecaster that separates early-onset defects.

### Findings

- **Residual spread is heteroscedastic by two orders of magnitude, driven by defect contamination rather than by profile: |slope_batch_robust_z| and delta_fraction_of_limit are the strongest separators, limit_fraction separates only above 0.16, and profile barely matters after limit normalization.** (confidence high)
  - Evidence: IQR of r by |z| bin: <1: 0.0106 (n=5157, 14.5% defects), 1-2: 0.0178, 2-5: 0.343, 5-10: 0.501, >=10: 1.131 (84% defects); MAD 0.0052 vs 0.627 (120x). By limit_fraction: IQR 0.0073-0.0150 for <0.16, 0.379 at [0.16,0.25), 1.216 at [0.25,0.5); parts already >=1 at 24h (n=116) have p5 = -1.035 (they can fall back). By delta_fraction: <-0.03 (n=505, 8% defects) abs_r p90 0.050; [0.03,0.1) 82% defects median r 0.50; [0.1,0.3) 100% defects median 0.97. By profile: IQR 0.0137-0.0199, p95 0.849-1.104 (100N_50V widest, abs_r p90 0.815 vs 0.52-0.57). Signed z < -2 (n=314, 7.3% defects) is the narrowest group: abs_r p90 0.044.
  - Design implication: Any interval must be conditional on early-drift features (slope z, delta, current z, limit_fraction >0.16); a single marginal width is wrong for essentially every subgroup. Profile is a weak stratifier but 100N_50V deserves per-profile reporting. Negative slope z (settling) is informative and should not be folded into |z|.
- **A single absolute-residual conformal radius (v1 method) is simultaneously far too wide for the healthy majority and far too narrow for drifting parts.** (confidence high)
  - Evidence: Conformal 90% quantile of |r| over all parts = 0.6008, width 1.2016. Coverage: all 0.900, healthy 1.000 (n=5624), defect 0.533 (n=1431), tester fault 0.590 (n=190); defects with onset <=24h 0.571, onset >24h 0.426; late_abrupt_onset 0.367, moisture 0.476, accelerating_drift 0.501, gradual_drift 0.602. Healthy |r|: median 0.0052, p90 0.0171, p99 0.0448, so the width is 229x the healthy median error and 70x the healthy p90. Radius that would suffice for healthy parts alone: 0.0171; for defects alone: 1.52; for 99% of all parts: 1.96.
  - Design implication: Do not carry v1's single radius into v2. Its 90% marginal coverage is an artifact of bimodality (always covers healthy, covers about half the defects), which is the opposite of what a screening tool needs.
- **Residuals are one-sided: symmetric intervals waste roughly half their width below the forecast and produce physically impossible negative lower bounds.** (confidence high)
  - Evidence: Percentiles of r: all p5 -0.021 / p95 0.963; defects p5 -0.0074 / p95 1.955 (92.1% positive); healthy p5 -0.0207 / p95 0.0114; tester faults p5 -0.049 / p95 1.56. With the single symmetric radius, 700 parts miss above vs 19 below (37:1). Lower bound below zero for 97.8% of parts (symmetric) vs 0% (asymmetric q05/q95). Asymmetric [q05,q95] width 0.985 vs symmetric 1.202 (82%); 48% of the symmetric width lies below the forecast beyond where r ever reaches at the 5% level. Healthy min r = -0.112, 0.1st percentile -0.071.
  - Design implication: Use signed-residual quantiles (asymmetric lower/upper margins), clip the lower bound at 0, and consider pushing most of the miscoverage budget to the lower side or reporting a one-sided upper bound, since lower misses on healthy parts are harmless for screening.
- **Nested whole-batch calibration gives a stable coverage estimate but an unstable radius; going from 4 to 8 calibration batches barely helps because the 90% quantile sits inside the defect tail.** (confidence high)
  - Evidence: Last-k training batches per fold (5 GroupKFold folds): k=4 radius 0.526-0.613 (sd 0.036), val coverage 0.874-0.909 (mean 0.894, sd 0.014); k=6 radius sd 0.030, coverage 0.879-0.914 (sd 0.013); k=8 radius 0.534-0.601 (sd 0.029), coverage 0.878-0.909 (mean 0.896, sd 0.011); all 28-29 training batches: radius 0.586-0.611 (sd 0.011), coverage 0.889-0.913 (sd 0.010). Defect coverage 0.477-0.550 for every k. Across all disjoint k-batch chunks: k=4 radius 0.423-0.724 (max/min 1.71x), coverage 0.848-0.926; k=8 radius 0.451-0.685 (1.52x), coverage 0.855-0.923. Calibration defect share ranged 18.0-23.4%. The last-8 rule left fold 3 with zero 10N_50V batches (others 1-3 per profile). Fold 4 tester-fault coverage was 0.308 vs 0.62-0.71 elsewhere.
  - Design implication: Use 8 calibration batches (>=1600 parts, ~300 defects, >=49 parts in the z>=5 stratum), selected stratified 2 per profile by sorted batch_id rather than last-k; do not go below 6 (z>=5 stratum had only 22 parts at k=4). Quote nested coverage as a range (about +/-2 pp across folds, +/-4 pp across subset choice) and treat Codex's calibration on the separate calibration_* batches as authoritative.
- **Within-batch dependence is modest for residuals but strong for tester faults, and per-batch coverage varies far more than an iid guarantee implies.** (confidence high)
  - Evidence: One-way ANOVA ICC (m=200): r 0.0038 (design effect 1.75, n_eff 4109/7200), |r| 0.0039 (1.78), coverage indicator 0.0043 (1.85, n_eff 3897); within-profile r ICC 0.0013 (1.27), so about two-thirds of the batch clustering is the profile effect; is_defect ICC 0.0001 (defects assigned iid); is_tester_fault ICC 0.0343 (design effect 7.8, n_eff 921). SE of the overall coverage estimate: 0.0035 naive vs 0.0048 design-adjusted (cluster SE 0.0048). Per-batch coverage of the single radius: 0.820-0.955 (sd 0.029), 18/36 batches below 0.90, 2 below 0.85; the 6 lowest are all 100N_50V (0.82-0.875).
  - Design implication: The row-level conformal guarantee is marginal over exchangeable rows; with batch clustering the effective calibration size shrinks by ~1.85x (7.8x for tester-fault events), so a nominal 90% interval should be documented as 'about 90% on average across batches, 82-96% within a batch', and coverage must be reported per batch and per profile, not only pooled.
- **Asymmetric residual quantiles stratified by slope_batch_robust_z (<2, 2-5, >=5) keep marginal coverage while roughly halving width and raising defect coverage by 24 pp; per-bin symmetric radii do not help.** (confidence high)
  - Evidence: k=8, means over 5 validation folds. A single symmetric: coverage 0.896 (sd 0.011), healthy 1.00, defect 0.515, median width 1.147, lower<0 for 97.8%. B per-bin symmetric: coverage 0.893, defect 0.507, late-onset defect coverage 0.233, width 0.707 in z<2 but 3.48 in z>=5. C per-bin asymmetric: coverage 0.894 (sd 0.007, min fold 0.885), healthy 0.935, defect 0.756 (min 0.741), late-onset (>24h) defect 0.539, tester 0.682; median width 0.797 (z<2), 1.27 (2-5), 3.42 (>=5); lower<0 for 3.8%. Per bin z>=5: coverage A 0.43 vs C 0.944; 2<=z<5: A 0.774 vs C 0.90. Per-batch coverage (nested): A 0.820-0.955, C 0.845-0.950, one-sided upper 0.83-0.965. Share of parts whose C upper bound reaches the limit: 12.1% overall (3.5-25% per batch). One-sided 90% upper margin in z<2: 0.353 vs two-sided q95 margin 0.780.
  - Design implication: v2 interval = stratified asymmetric split-conformal on signed residuals of the point forecast, strata by slope z (fallback to pooled quantiles when a stratum has <20 calibration parts), lower bound clipped at 0, plus an explicit one-sided 90% upper bound and a 'may exceed limit' flag when upper >= 1. Strata and quantiles must be recomputed on the v2 model's residuals (the point forecast may itself become the stratifier, CQR-style).
- **There is a hard floor on how narrow a 90% interval can be for the healthy-looking majority: undetectable defects inside the quiet stratum set the upper margin, not measurement noise.** (confidence high)
  - Evidence: z<2 bin (n=6568, 14.6% defects, 365 with onset >24h): r quantiles q80 0.0097, q84 0.027, q86 0.136, q88 0.269, q90 0.408, q95 0.821; healthy-only q95 0.0114. Quiet subgroup (z<2 & limit_fraction<0.16 & current_z<2 & delta<0.01; n=5534, 76.9% of parts) still has 13.5% defects (308 onset >24h, 440 onset <=24h), 1.0% tester faults, 4.1% ending >= limit; its r quantiles: q84 0.015, q86 0.032, q90 0.354, q95 0.788, q99 1.76 vs median |r| 0.0057.
  - Design implication: At 90% nominal the healthy majority will get an upper margin of about 0.35 (about 60x their actual error) no matter how the strata are drawn from 0/24h data; a narrow interval requires either a lower nominal level (<=85%) or a forecaster that separates early-onset defects (which would shrink the 440 early-onset residuals but cannot touch the 308 late-onset ones). State explicitly that the 5.1% late-onset defects (369 parts) are unpredictable from the inputs and are the reason a 90% interval is wide.

### Tables

| |slope_batch_robust_z| bin | n | defect share | IQR of r | MAD | r p5 | r p95 | abs_r p50 | abs_r p90 |
|---|---|---|---|---|---|---|---|---|
| [0,1) | 5157 | 0.145 | 0.0106 | 0.0052 | -0.016 | 0.823 | 0.0059 | 0.401 |
| [1,2) | 1097 | 0.171 | 0.0178 | 0.0078 | -0.022 | 0.875 | 0.0082 | 0.485 |
| [2,5) | 618 | 0.359 | 0.343 | 0.032 | -0.037 | 0.959 | 0.027 | 0.692 |
| [5,10) | 154 | 0.831 | 0.501 | 0.249 | -0.053 | 2.13 | 0.621 | 1.43 |
| [10,inf) | 174 | 0.839 | 1.131 | 0.627 | -0.858 | 2.16 | 0.635 | 1.68 |

| limit_fraction (x24/limit) bin | n | defect share | IQR of r | MAD | r p5 | r p95 | abs_r p50 |
|---|---|---|---|---|---|---|---|
| [0,0.08) | 844 | 0.127 | 0.0073 | 0.0033 | -0.008 | 0.826 | 0.0035 |
| [0.08,0.12) | 2908 | 0.140 | 0.0107 | 0.0051 | -0.014 | 0.735 | 0.0057 |
| [0.12,0.16) | 2053 | 0.188 | 0.0150 | 0.0071 | -0.020 | 0.944 | 0.0080 |
| [0.16,0.25) | 1079 | 0.311 | 0.379 | 0.0153 | -0.031 | 1.074 | 0.016 |
| [0.25,0.5) | 148 | 0.737 | 1.216 | 0.632 | -0.154 | 2.29 | 0.623 |
| [0.5,1.0) | 52 | 0.808 | 0.591 | 0.380 | -0.708 | 1.98 | 0.413 |
| [1.0,inf) | 116 | 0.379 | 0.086 | 0.039 | -1.035 | 0.907 | 0.044 |

| Single symmetric radius (v1 method), R = conformal q90 of |r| = 0.6008, width 1.2016 | value |
|---|---|
| coverage all / healthy / defect / tester fault | 0.900 / 1.000 / 0.533 / 0.590 |
| coverage defect onset <=24h / >24h | 0.571 / 0.426 |
| coverage late_abrupt / moisture / accel / gradual / tester_channel / intermittent | 0.367 / 0.476 / 0.501 / 0.602 / 0.648 / 0.765 |
| healthy abs_r median / p90 / p99 | 0.0052 / 0.0171 / 0.0448 |
| width / healthy median error; width / healthy p90 error | 229x ; 70x |
| radius needed: healthy only q90 / defects only q90 / all q99 | 0.0171 / 1.52 / 1.96 |
| misses below vs above; share of lower bounds < 0 | 19 vs 700 ; 97.8% |

| Sign asymmetry of r | n | p5 | p50 | p95 | share r>0 |
|---|---|---|---|---|---|
| all | 7200 | -0.0210 | -0.0013 | 0.963 | 0.436 |
| is_defect | 1431 | -0.0074 | 0.546 | 1.955 | 0.921 |
| not defect | 5769 | -0.0214 | -0.0030 | 0.0144 | 0.316 |
| is_healthy | 5624 | -0.0207 | -0.0031 | 0.0114 | 0.307 |
| tester fault | 190 | -0.049 | 0.367 | 1.56 | 0.726 |
| asymmetric [q05,q95] width 0.985 vs symmetric 1.202 (82%); lower<0 share 0% vs 97.8% | | | | | |

| Nested calibration (last k training batches, 5 GroupKFold folds) | radius mean (min-max) | val coverage mean (min-max), sd | defect cov (min-max) | radius range over all disjoint k-chunks (max/min) | coverage range over chunks |
|---|---|---|---|---|---|
| k=4 (800 parts) | 0.570 (0.526-0.613) | 0.894 (0.874-0.909), 0.014 | 0.506 (0.477-0.546) | 0.423-0.724 (1.71x) | 0.848-0.926 |
| k=6 (1200) | 0.578 (0.548-0.616) | 0.897 (0.879-0.914), 0.013 | 0.517 (0.477-0.543) | 0.469-0.692 (1.48x) | 0.861-0.921 |
| k=8 (1600) | 0.574 (0.534-0.601) | 0.896 (0.878-0.909), 0.011 | 0.515 (0.477-0.550) | 0.451-0.685 (1.52x) | 0.855-0.923 |
| all 28-29 train batches | 0.600 (0.586-0.611) | 0.901 (0.889-0.913), 0.010 | 0.537 (0.507-0.554) | - | - |

| Within-batch dependence (one-way ANOVA, m=200) | ICC | design effect | n_eff (of 7200) |
|---|---|---|---|
| r | 0.0038 | 1.75 | 4109 |
| |r| | 0.0039 | 1.78 | 4051 |
| coverage indicator at single radius | 0.0043 | 1.85 | 3897 |
| r within profile (profile mean removed) | 0.0013 | 1.27 | 5679 |
| is_defect | 0.0001 | 1.01 | 7124 |
| is_tester_fault | 0.0343 | 7.82 | 921 |
| SE of coverage: naive 0.0035, design-adjusted 0.0048, cluster (batch means) 0.0048; per-batch coverage 0.820-0.955, 18/36 below 0.90 | | | |

| Method (k=8, mean over 5 val folds) | coverage (sd, min) | healthy | defect | defect onset>24h | tester | median width | width z<2 / 2-5 / >=5 | lower<0 share |
|---|---|---|---|---|---|---|---|---|
| A single symmetric | 0.896 (0.011, 0.878) | 1.000 | 0.515 | 0.418 | 0.592 | 1.147 | 1.15 / 1.15 / 1.15 | 0.978 |
| B per-z-bin symmetric | 0.893 (0.014, 0.877) | 1.000 | 0.507 | 0.233 | 0.587 | 0.707 | 0.71 / 1.90 / 3.48 | 0.989 |
| C per-z-bin asymmetric [q05,q95] | 0.894 (0.007, 0.885) | 0.935 | 0.756 | 0.539 | 0.682 | 0.797 | 0.80 / 1.27 / 3.42 | 0.038 |
| U per-z-bin one-sided upper q90 | 0.891-0.915 per bin | - | 0.32 (z<2), 0.86, 0.91 | - | - | upper margin | 0.35 / 0.95 / 1.74 | 0 |
| per-bin coverage z>=5: A 0.43, B 0.91, C 0.944; 2<=z<5: A 0.77, B 0.92, C 0.90; per-batch coverage A 0.82-0.955, C 0.845-0.95 | | | | | | | | |

| Upper quantile of r as nominal coverage rises | z<2 bin all (n=6568) | z<2 healthy only | quiet stratum (n=5534, 13.5% defects) |
|---|---|---|---|
| q80 | 0.0097 | 0.0024 | 0.0077 |
| q84 | 0.027 | 0.0035 | 0.015 |
| q86 | 0.136 | 0.0043 | 0.032 |
| q88 | 0.269 | 0.0050 | 0.209 |
| q90 | 0.408 | 0.0060 | 0.354 |
| q95 | 0.821 | 0.0114 | 0.788 |
| q99 | 1.815 | 0.0303 | 1.764 |

### Caveats

- All numbers use persistence residuals as a proxy; a v2 forecaster will shrink residuals for early-onset defects (440 of the 748 defects inside the quiet stratum have onset <=24h), so strata, quantiles and widths must be recomputed on the actual model's held-out residuals before any is quoted.
- Sections 1-2 and the single-radius coverage table are in-sample descriptive numbers (radius and coverage on the same 7,200 parts); only sections 3, 5 and the per-batch nested table hold out whole batches.
- Fold assignment is sklearn GroupKFold(5) on the frame sorted by batch_id and component_id (deterministic here because all batches have 200 parts); a different fold rule would move coverage numbers by roughly the reported fold sd (0.007-0.014).
- The last-k and disjoint-chunk calibration rules are arbitrary orderings by batch_id; the last-8 rule gave 1-3 batches per profile and zero 10N_50V batches in fold 3, so the reported variability partly reflects profile imbalance.
- Per-stratum quantiles in the z>=5 and 2-5 bins rest on 22-59 calibration parts at k=4..8, so their 95th percentiles are set by 2-3 parts; the fallback threshold of 20 parts is a judgment call.
- Conformal quantiles use the finite-sample rank ceil((n+1)(1-alpha)); asymmetric bounds use floor/ceil ranks at alpha/2 each side, which is slightly conservative and not a joint guarantee.
- ICC is a one-way ANOVA estimate assuming balanced groups; it measures batch clustering of residuals, not of the model errors a fitted forecaster will produce, and with 36 batches the ICC itself is imprecise.
- Widths are reported unclipped; clipping the lower bound at 0 shortens the symmetric intervals for 97.8% of parts but does not change their coverage.
- Labels (scenario, onset hours, is_defect, is_tester_fault) were used only to explain coverage retrospectively; the strata and calibration use only 0/24h features.
- All data are synthetic; nothing here is evidence about real MLCC failure behaviour, and the final interval calibration is Codex's responsibility on the withheld calibration_* batches.

