# Forecasting experiment (v2)

Why the first XGBoost lost to "the value stays where it is", and what fixed it. Twelve predeclared configurations were compared on five whole-batch folds of the 7,200 training parts; an absolute-error model of the correction over persistence won and became `xgboost_v2` in the release bundle.

| File | What it holds |
|---|---|
| [PREDECLARED_COMPARISON.md](PREDECLARED_COMPARISON.md) | The twelve configurations and the selection rule, frozen before running |
| [COMPARISON.md](COMPARISON.md) | Results per fold, profile, stratum and scenario |
| [DIAGNOSTICS.md](DIAGNOSTICS.md) | Six analyses of what 0/24 h readings can and cannot predict |
| [STATUS.md](STATUS.md) | Milestones, disclosures and the verification pass |
| `oof_predictions.csv`, `cv_results.json`, `interval_experiment__*.json` | Keyed out-of-fold forecasts and interval read-outs |
| `candidate/` | The frozen standalone candidates with manifests |

Full write-up: [docs/CLAUDE_FORECAST_V2_HANDOFF.md](../../docs/CLAUDE_FORECAST_V2_HANDOFF.md). Independent check on untouched batches: `outputs/codex_ml_v2_review/`.
