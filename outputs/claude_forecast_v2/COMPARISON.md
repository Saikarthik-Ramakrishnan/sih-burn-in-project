# Cross-validated comparison (training batches only)

Recorded 2026-09-05T23:15:07Z; seed 26170; 5 profile-stratified whole-batch folds; predeclaration digest `27702108c22c7315`.

Development results, not final validation. Lower MAE is better. Signed error is prediction minus observed. Recall/FPR use the point forecast >= limit against the observed 168 h crossing; 'new' restricts to parts below the limit at 24 h; 'latent' uses is_future_failure and excludes tester-fault parts. 'batches' counts the 36 whole batches where the configuration's MAE is below persistence's; the paired delta is the per-batch MAE difference to persistence (negative is better) with its standard error.

| config | MAE norm (pooled) | fold mean ± std | folds < pers | batches < pers | paired Δ vs pers (SE) | train MAE | MAE µA | healthy MAE | non-healthy MAE | mean signed err | crossing recall | crossing FPR | tp/fn/fp/tn | new recall (tp/fp) | latent recall (no tester) | clipped at 0 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `xgb_abs_resid_aux` | 0.1427 | 0.1427 ± 0.0017 | 5/5 | 36/36 | -0.0164 (0.0018) | 0.1396 | 0.0804 | 0.0165 | 0.5932 | -0.1011 | 0.318 | 0.0059 | 176/377/39/6608 | 0.178 (80/29) | 0.208 | 0.0000 |
| `xgb_abs_resid_peer` | 0.1428 | 0.1427 ± 0.0018 | 5/5 | 35/36 | -0.0164 (0.0018) | 0.1400 | 0.0804 | 0.0164 | 0.5939 | -0.1012 | 0.316 | 0.0060 | 175/378/40/6607 | 0.180 (81/31) | 0.213 | 0.0000 |
| `xgb_abs_resid_leak` | 0.1429 | 0.1429 ± 0.0016 | 5/5 | 35/36 | -0.0163 (0.0017) | 0.1403 | 0.0804 | 0.0165 | 0.5940 | -0.1007 | 0.315 | 0.0057 | 174/379/38/6609 | 0.180 (81/29) | 0.216 | 0.0000 |
| `xgb_huber_resid_leak` | 0.1442 | 0.1440 ± 0.0029 | 5/5 | 36/36 | -0.0150 (0.0017) | 0.1418 | 0.0812 | 0.0165 | 0.5997 | -0.0996 | 0.340 | 0.0084 | 188/365/56/6591 | 0.193 (87/44) | 0.228 | 0.0000 |
| `xgb_abs_norm_leak` | 0.1446 | 0.1445 ± 0.0018 | 5/5 | 33/36 | -0.0146 (0.0019) | 0.1416 | 0.0809 | 0.0174 | 0.5984 | -0.1034 | 0.306 | 0.0056 | 169/384/37/6610 | 0.180 (81/32) | 0.196 | 0.0000 |
| `persistence` | 0.1592 | 0.1590 ± 0.0059 | 0/5 | 0/36 | +0.0000 (0.0000) | 0.1592 | 0.0907 | 0.0078 | 0.6993 | -0.1421 | 0.186 | 0.0020 | 103/450/13/6634 | 0.000 (0/0) | 0.020 | 0.0000 |
| `xgb_sq_log1p_resid_leak` | 0.1881 | 0.1880 ± 0.0023 | 0/5 | 1/36 | +0.0289 (0.0021) | 0.1789 | 0.1068 | 0.0842 | 0.5588 | -0.0354 | 0.293 | 0.0071 | 162/391/47/6600 | 0.173 (78/42) | 0.189 | 0.0000 |
| `xgb_sq_log1p_leak` | 0.1888 | 0.1887 ± 0.0032 | 0/5 | 1/36 | +0.0296 (0.0020) | 0.1792 | 0.1072 | 0.0847 | 0.5600 | -0.0357 | 0.288 | 0.0071 | 159/394/47/6600 | 0.156 (70/39) | 0.181 | 0.0000 |
| `xgb_sq_resid_leak` | 0.2097 | 0.2097 ± 0.0024 | 0/5 | 0/36 | +0.0505 (0.0025) | 0.1983 | 0.1198 | 0.1158 | 0.5449 | -0.0000 | 0.320 | 0.0110 | 177/376/73/6574 | 0.202 (91/66) | 0.226 | 0.0000 |
| `xgb_v1_replica` | 0.2100 | 0.2098 ± 0.0061 | 0/5 | 0/36 | +0.0508 (0.0033) | 0.1920 | 0.1175 | 0.1161 | 0.5454 | -0.0006 | 0.338 | 0.0113 | 187/366/75/6572 | 0.207 (93/65) | 0.231 | 0.0000 |
| `xgb_sq_norm_leak` | 0.2101 | 0.2100 ± 0.0028 | 0/5 | 0/36 | +0.0509 (0.0023) | 0.1988 | 0.1200 | 0.1161 | 0.5455 | +0.0002 | 0.325 | 0.0102 | 180/373/68/6579 | 0.196 (88/59) | 0.221 | 0.0000 |
| `linear_extrapolation` | 0.2625 | 0.2616 ± 0.0328 | 0/5 | 0/36 | +0.1033 (0.0184) | 0.2624 | 0.1386 | 0.0721 | 0.9418 | -0.0969 | 0.302 | 0.0104 | 167/386/69/6578 | 0.162 (73/56) | 0.194 | 0.2004 |

## Per-fold normalized MAE

| config | fold 0 | fold 1 | fold 2 | fold 3 | fold 4 |
|---|---|---|---|---|---|
| `persistence` | 0.1662 | 0.1604 | 0.1527 | 0.1624 | 0.1532 |
| `linear_extrapolation` | 0.2911 | 0.2655 | 0.2941 | 0.2390 | 0.2185 |
| `xgb_v1_replica` | 0.2187 | 0.2046 | 0.2044 | 0.2131 | 0.2082 |
| `xgb_sq_norm_leak` | 0.2110 | 0.2133 | 0.2060 | 0.2114 | 0.2085 |
| `xgb_sq_resid_leak` | 0.2119 | 0.2119 | 0.2065 | 0.2098 | 0.2083 |
| `xgb_abs_norm_leak` | 0.1467 | 0.1451 | 0.1420 | 0.1455 | 0.1434 |
| `xgb_abs_resid_leak` | 0.1455 | 0.1425 | 0.1410 | 0.1423 | 0.1430 |
| `xgb_huber_resid_leak` | 0.1491 | 0.1423 | 0.1435 | 0.1423 | 0.1429 |
| `xgb_sq_log1p_leak` | 0.1894 | 0.1925 | 0.1842 | 0.1906 | 0.1870 |
| `xgb_sq_log1p_resid_leak` | 0.1896 | 0.1902 | 0.1850 | 0.1891 | 0.1862 |
| `xgb_abs_resid_aux` | 0.1455 | 0.1414 | 0.1410 | 0.1429 | 0.1425 |
| `xgb_abs_resid_peer` | 0.1457 | 0.1424 | 0.1407 | 0.1420 | 0.1429 |

## MAE in µA by profile (pooled out-of-fold)

| config | SIM_X7R_100N_50V | SIM_X7R_10N_50V | SIM_X7R_1U_25V | SIM_X7R_4U7_16V |
|---|---|---|---|---|
| `persistence` | 0.0481 | 0.0177 | 0.1037 | 0.1933 |
| `linear_extrapolation` | 0.0791 | 0.0352 | 0.1538 | 0.2864 |
| `xgb_v1_replica` | 0.0617 | 0.0247 | 0.1408 | 0.2428 |
| `xgb_sq_norm_leak` | 0.0594 | 0.0245 | 0.1421 | 0.2541 |
| `xgb_sq_resid_leak` | 0.0596 | 0.0244 | 0.1411 | 0.2541 |
| `xgb_abs_norm_leak` | 0.0445 | 0.0164 | 0.0941 | 0.1685 |
| `xgb_abs_resid_leak` | 0.0433 | 0.0162 | 0.0936 | 0.1686 |
| `xgb_huber_resid_leak` | 0.0436 | 0.0163 | 0.0944 | 0.1705 |
| `xgb_sq_log1p_leak` | 0.0546 | 0.0219 | 0.1259 | 0.2264 |
| `xgb_sq_log1p_resid_leak` | 0.0546 | 0.0217 | 0.1252 | 0.2257 |
| `xgb_abs_resid_aux` | 0.0433 | 0.0161 | 0.0935 | 0.1687 |
| `xgb_abs_resid_peer` | 0.0432 | 0.0162 | 0.0936 | 0.1686 |

## Normalized MAE by retrospective stratum (labels used only to explain errors)

Counts: healthy = 5624, defect_onset_le24 = 1029, defect_onset_gt24 = 357, tester_fault_onset_0_12 = 113, tester_fault_onset_72 = 77

| config | healthy | defect_onset_le24 | defect_onset_gt24 | tester_fault_onset_0_12 | tester_fault_onset_72 |
|---|---|---|---|---|---|
| `persistence` | 0.0078 (+0.004) | 0.6582 (-0.607) | 0.9093 (-0.909) | 0.1922 (-0.151) | 1.0184 (-1.018) |
| `linear_extrapolation` | 0.0721 (-0.057) | 0.7804 (-0.162) | 0.9724 (-0.972) | 2.1987 (+1.871) | 1.1112 (-1.009) |
| `xgb_v1_replica` | 0.1161 (+0.116) | 0.4539 (-0.295) | 0.8145 (-0.799) | 0.3026 (+0.004) | 0.8762 (-0.876) |
| `xgb_sq_norm_leak` | 0.1161 (+0.116) | 0.4564 (-0.282) | 0.8153 (-0.799) | 0.2559 (-0.043) | 0.9093 (-0.909) |
| `xgb_sq_resid_leak` | 0.1158 (+0.116) | 0.4544 (-0.281) | 0.8157 (-0.799) | 0.2679 (-0.057) | 0.9055 (-0.906) |
| `xgb_abs_norm_leak` | 0.0174 (+0.015) | 0.5004 (-0.399) | 0.9043 (-0.903) | 0.2488 (-0.189) | 1.0020 (-1.002) |
| `xgb_abs_resid_leak` | 0.0165 (+0.015) | 0.4962 (-0.384) | 0.9043 (-0.903) | 0.2291 (-0.115) | 0.9979 (-0.998) |
| `xgb_huber_resid_leak` | 0.0165 (+0.015) | 0.5054 (-0.379) | 0.9044 (-0.903) | 0.2274 (-0.093) | 0.9934 (-0.993) |
| `xgb_sq_log1p_leak` | 0.0847 (+0.085) | 0.4661 (-0.342) | 0.8416 (-0.830) | 0.2668 (-0.106) | 0.9389 (-0.939) |
| `xgb_sq_log1p_resid_leak` | 0.0842 (+0.084) | 0.4635 (-0.340) | 0.8415 (-0.831) | 0.2757 (-0.074) | 0.9370 (-0.937) |
| `xgb_abs_resid_aux` | 0.0165 (+0.015) | 0.4962 (-0.388) | 0.9041 (-0.903) | 0.2213 (-0.103) | 0.9945 (-0.995) |
| `xgb_abs_resid_peer` | 0.0164 (+0.015) | 0.4960 (-0.386) | 0.9043 (-0.903) | 0.2292 (-0.119) | 0.9978 (-0.998) |

Cell format: MAE (mean signed error). Strata are mutually exclusive with tester-fault priority: the 45 parts flagged both defect and tester fault are counted as tester faults (so the two defect strata sum to 1,386 of 1,431 is_defect parts) and are excluded from the latent-crossing metric.

## Normalized MAE by simulated scenario (retrospective explanation only)

| config | accelerating_drift | gradual_drift | healthy_settling | intermittent_leakage | late_abrupt_onset | moisture_associated_history | ordinary_noise | tester_channel_fault |
|---|---|---|---|---|---|---|---|---|
| `persistence` | 0.7946 | 0.6519 | 0.0056 | 0.3652 | 1.0167 | 0.7268 | 0.0162 | 0.3848 |
| `linear_extrapolation` | 0.8262 | 0.2940 | 0.0674 | 1.8532 | 1.1263 | 0.6272 | 0.0896 | 1.6471 |
| `xgb_v1_replica` | 0.6597 | 0.2446 | 0.1119 | 0.5232 | 0.9068 | 0.4588 | 0.1315 | 0.4431 |
| `xgb_sq_norm_leak` | 0.6567 | 0.2367 | 0.1125 | 0.5487 | 0.9087 | 0.4764 | 0.1292 | 0.4038 |
| `xgb_sq_resid_leak` | 0.6569 | 0.2379 | 0.1126 | 0.5407 | 0.9082 | 0.4730 | 0.1278 | 0.4122 |
| `xgb_abs_norm_leak` | 0.7657 | 0.2707 | 0.0108 | 0.4594 | 1.0126 | 0.5553 | 0.0422 | 0.4187 |
| `xgb_abs_resid_leak` | 0.7665 | 0.2604 | 0.0095 | 0.4469 | 1.0120 | 0.5562 | 0.0426 | 0.4109 |
| `xgb_huber_resid_leak` | 0.7665 | 0.2715 | 0.0095 | 0.4745 | 1.0110 | 0.5520 | 0.0427 | 0.4160 |
| `xgb_sq_log1p_leak` | 0.6907 | 0.2529 | 0.0808 | 0.4885 | 0.9407 | 0.5041 | 0.0994 | 0.4147 |
| `xgb_sq_log1p_resid_leak` | 0.6907 | 0.2529 | 0.0804 | 0.4805 | 0.9394 | 0.4979 | 0.0982 | 0.4252 |
| `xgb_abs_resid_aux` | 0.7660 | 0.2636 | 0.0095 | 0.4429 | 1.0112 | 0.5519 | 0.0425 | 0.4101 |
| `xgb_abs_resid_peer` | 0.7671 | 0.2614 | 0.0094 | 0.4450 | 1.0123 | 0.5547 | 0.0423 | 0.4108 |
