"""Audit a teammate ZIP and score it with the existing frozen MLCC bundle.

Run from the repository root; uploaded Python code is never executed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import zipfile

import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
from threadpoolctl import threadpool_limits

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from sih26170.mlcc_prototype import (
    FORECAST_COLUMNS, GROUP_COLUMNS, load_bundle, prepare_early_features,
    screen_readings, _joined_labels,
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--dataset-dir", type=Path, default=Path("outputs/mlcc_v1"))
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/teammate_integration"))
    args = parser.parse_args()
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    if (out / "integration_audit.json").exists():
        raise FileExistsError("Completed integration exists; choose a new output directory")
    with zipfile.ZipFile(args.archive) as archive:
        raw = archive.read("csv data/synthetic_pattern_dataset.csv")
        import io
        data = pd.read_csv(io.BytesIO(raw))
    audit = {
        "source": str(args.archive), "csv_sha256": hashlib.sha256(raw).hexdigest(),
        "rows": len(data), "components": int(data.component_id.nunique()),
        "batches": int(data.batch_id.nunique()),
        "missing_by_column": data.isna().sum().to_dict(),
        "exact_duplicates": int(data.duplicated().sum()),
        "duplicate_checkpoints": int(data.duplicated(GROUP_COLUMNS + ["hours"]).sum()),
        "training_performed": False,
        "scope": "Independent synthetic stress evaluation; not real-world accuracy",
        "handoff_processed_csvs_supplied": False,
    }
    if data.isna().any().any() or audit["duplicate_checkpoints"]:
        raise ValueError("Missing data or duplicate checkpoints require review")
    for col in ("hours", "measurement_value", "upper_limit"):
        if not np.isfinite(data[col]).all() or (data[col] < 0).any():
            raise ValueError(f"Invalid values in {col}")
    if (data.upper_limit <= 0).any():
        raise ValueError("Limits must be positive")
    data = data.sort_values(GROUP_COLUMNS + ["hours"])
    early = data.loc[data.hours.isin([0, 24])].drop(columns="pattern")
    bundle = load_bundle(args.dataset_dir / "model_bundle")
    features, _, invalid = prepare_early_features(early)
    if invalid:
        raise ValueError(f"Invalid early components: {invalid}")
    response = screen_readings(early, bundle, forecast_model="xgboost")
    # Verify labels and future measurements cannot change predictions.
    assert response == screen_readings(data, bundle, forecast_model="xgboost")
    audit["future_and_pattern_leakage_check"] = "passed"
    final = data.loc[data.hours.eq(168), GROUP_COLUMNS + ["measurement_value", "pattern"]]
    if len(final) != len(features):
        raise ValueError("Every component needs a 168-hour evaluation target")
    flat = pd.DataFrame(response["records"])
    joined = flat.merge(final.rename(columns={"measurement_value": "observed_168h_ua"}),
                        on=GROUP_COLUMNS, validate="one_to_one")
    for column in ("predicted_final_value", "prediction_lower", "prediction_upper"):
        joined[column] = pd.to_numeric(joined[column], errors="coerce")
    joined["absolute_error_ua"] = (joined.predicted_final_value - joined.observed_168h_ua).abs()
    joined["interval_contains_observed"] = (
        (joined.observed_168h_ua >= joined.prediction_lower)
        & (joined.observed_168h_ua <= joined.prediction_upper))
    audit["scoring_summary"] = response["summary"]
    scored = joined.loc[joined.status.eq("scored")]
    audit["by_pattern"] = scored.groupby("pattern").agg(
        components=("component_id", "size"), mae_ua=("absolute_error_ua", "mean"),
        interval_coverage=("interval_contains_observed", "mean")).reset_index().to_dict("records")
    audit["limitations"] = [
        "Only one batch: unsuitable for independent train/calibration/test splitting.",
        "Missing profile_id: production inference returns unscored until actual supported test profile is supplied; no profile was fabricated.",
        "Optional stress, capacitance and dissipation inputs are absent and imputed.",
        "Sudden faults after 24h may have no observable early signal.",
        "Handoff baseline counts and cleaned feature values cannot be verified without its missing CSVs.",
        "Percent change in the model is a fraction; multiply by 100 for display.",
        "Correlated features share importance; importance does not establish physical causes.",
    ]
    # Held-out importance is descriptive only: no tuning or feature selection.
    heldout, _, rejected = prepare_early_features(pd.read_csv(args.dataset_dir / "test_early.csv"))
    if rejected:
        raise ValueError("Invalid held-out observations")
    labels = _joined_labels(heldout, pd.read_csv(args.dataset_dir / "test_labels.csv"))
    matrix = bundle.imputer.transform(heldout[FORECAST_COLUMNS])
    target = labels.final_value.to_numpy() / heldout.upper_limit.to_numpy()
    with threadpool_limits(limits=1):
        importance = permutation_importance(bundle.models["xgboost"], matrix, target,
            scoring="neg_mean_absolute_error", n_repeats=5, random_state=26170, n_jobs=1)
    report = pd.DataFrame({"feature": FORECAST_COLUMNS,
        "xgboost_gain_importance": bundle.models["xgboost"].feature_importances_,
        "heldout_permutation_mae_increase": importance.importances_mean,
        "permutation_std": importance.importances_std,
    }).sort_values("heldout_permutation_mae_increase", ascending=False)
    early.to_csv(out / "dashboard_upload_early.csv", index=False)
    features.to_csv(out / "model_features.csv", index=False)
    joined.to_csv(out / "predictions_with_evaluation.csv", index=False)
    report.to_csv(out / "feature_importance.csv", index=False)
    (out / "dashboard_response.json").write_text(json.dumps(response, indent=2, allow_nan=False))
    (out / "integration_audit.json").write_text(json.dumps(audit, indent=2, allow_nan=False))
    (out / "README.md").write_text(
        "# Teammate data integration\n\n"
        "The supplied pattern CSV was validated and passed through the existing frozen Isolation Forest + XGBoost bundle. "
        "All 100 components are UNSCORED because profile_id is missing. Supply the actual supported test profile before expecting forecasts; do not guess it. "
        "No retraining occurred. The handoff's cleaned/technical CSVs were not supplied.\n\n"
        "Upload `dashboard_upload_early.csv` through the existing backend. "
        "Use `screen_readings(readings, bundle, forecast_model='xgboost')` for the XGBoost demo. "
        "`dashboard_response.json` is the actual response, including per-device XGBoost contributions. "
        "`predictions_with_evaluation.csv` includes future truth for offline review only.\n\n"
        "`feature_importance.csv` combines existing gain importance with five-repeat held-out permutation importance "
        "(increase in normalized MAE). It is descriptive, not a feature-selection step. "
        "Check `integration_audit.json` for pattern-level performance and limitations. "
        "Do not display synthetic results as industrial validation.\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
