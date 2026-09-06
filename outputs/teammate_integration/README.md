# Teammate data integration

The supplied pattern CSV was validated and passed through the existing frozen Isolation Forest + XGBoost bundle. All 100 components are UNSCORED because profile_id is missing. Supply the actual supported test profile before expecting forecasts; do not guess it. No retraining occurred. The handoff's cleaned/technical CSVs were not supplied.

Upload `dashboard_upload_early.csv` through the existing backend. Use `screen_readings(readings, bundle, forecast_model='xgboost')` for the XGBoost demo. `dashboard_response.json` is the actual response, including per-device XGBoost contributions. `predictions_with_evaluation.csv` includes future truth for offline review only.

`feature_importance.csv` combines existing gain importance with five-repeat held-out permutation importance (increase in normalized MAE). It is descriptive, not a feature-selection step. Check `integration_audit.json` for pattern-level performance and limitations. Do not display synthetic results as industrial validation.
