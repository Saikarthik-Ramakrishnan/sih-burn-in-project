# Claude forecasting v2 deliverable (new files only)

Extract over the training-only pack (or copy the three code files and the candidate folder into the release workspace; see `docs/CLAUDE_FORECAST_V2_HANDOFF.md`, section 10).

- `src/sih26170/forecast_v2.py` — module (experiment runner + frozen candidate)
- `scripts/claude_forecast_v2.py` — runner (`--data-dir outputs/mlcc_v1` in the release layout)
- `tests/test_forecast_v2.py` — 38 fast tests
- `docs/CLAUDE_FORECAST_V2_HANDOFF.md` — recommendation, results, interface, integration steps
- `outputs/claude_forecast_v2/` — STATUS.md, DIAGNOSTICS.md, PREDECLARED_COMPARISON.*, COMPARISON.md, comparison_*.csv, cv_results.json, oof_predictions.csv, interval_experiment__*.json, seed_check, prevalence_readout, candidate/{xgb_abs_resid_leak,xgb_abs_resid_aux}/, predict previews, and `scratch/` with the diagnostic and verification scripts (the 39 MB integration test copy and pre-fix backups are excluded)

Recommended candidate: `outputs/claude_forecast_v2/candidate/xgb_abs_resid_leak/`.
