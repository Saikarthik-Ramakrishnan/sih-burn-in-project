# Frozen ML v2 review — Codex

Claude's source workspace is `../claude_forecast_v2_pack/` relative to the main project. Its STATUS marks experiments and candidate fitting complete; the mentioned final adversarial-review section is absent and the advertised deliverable ZIP is absent. Those omissions do not require repeating the training experiments.

Codex owns this isolated `work/ml_v2_review/` snapshot and `outputs/codex_ml_v2_review/`. Claude's files, the production src tree, v1 bundle, and backend are not edited. If Claude resumes, send it this ownership note: experiments are already saved; do not rerun training or independent evaluation while Codex reviews the frozen candidate. Return any unfinished verification findings separately.

## Evaluation protocol fixed before running

- Candidate: saved xgb_abs_resid_leak only; no hyperparameter or feature search, no refitting. Baselines: saved v1 XGBoost and persistence.
- Run the combined 82 original + 32 candidate tests in the snapshot (114 passed on initial check, 2026-09-06).
- Verify artifact hashes, original training input hashes, disjoint batch/device identities, and source snapshot stability.
- Calibrate candidate intervals ONLY on existing calibration batches using Claude's proposed signed-slope strata (<2, 2–5, >=5), asymmetric 90% intervals, and a separate one-sided 90% upper bound; use pooled fallback when a stratum cannot support the quantile. No tuning on evaluation results.
- Evaluate existing test (already inspected in v1; not a pristine final test), existing low-prevalence/unseen-condition stress sets, and ONE fresh synthetic set: generator unchanged, seed 20260906, 20 complete batches, 200 components per batch, prefix V2AUDIT20260906. Use all 4,000 fresh components only for evaluation, regardless of generator split annotations. The new random draw is independent of fitting, but same-generator evaluation does not prove real-world or new-physics validity.
- Report normalized MAE, per-profile uA MAE, healthy MAE, observed crossing confusion, new crossing recall below the limit at 24h, and per-batch paired errors. Audit the unchanged anomaly detector separately. Retrospective simulator labels never enter model inputs.
- Report interval coverage and width overall, by profile, by batch, and by slope stratum. Nominal coverage is not a batch-independent guarantee.
- Descriptive review gates (not automatic deployment): candidate improves MAE on fresh data by at least 0.01 versus persistence; show both healthy MAE <=0.02 and stricter <=1.5x persistence; report all false-alarm tradeoffs. If evidence is mixed, retain v1 as production default. No changing gates after seeing fresh results.
- Persist results and a resume checklist. Reuse completed work; never restart experiments to obtain a favorable seed.

Next after this review: resolve any defects/tradeoffs, then build a separately versioned inference adapter with candidate-specific calibration and explanations. Never replace v1's XGBoost inside the old bundle or reuse its interval radius/explanations for a different forecast.
