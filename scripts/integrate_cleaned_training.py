"""Verify teammate cleaning against trained data and export model-ready artifacts."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import sys
from zipfile import ZipFile, ZIP_DEFLATED

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from sih26170.mlcc_prototype import (
    FORECAST_COLUMNS, GROUP_COLUMNS, load_bundle, prepare_early_features, screen_readings,
)


def restore_package_metadata(output, dataset):
    """Restore identifier formatting from source; never modify numeric model outputs."""
    source = pd.read_csv(dataset / "train_early.csv", dtype={"package_code": str})
    codes = source.drop_duplicates("component_id").set_index("component_id").package_code
    for name in ("integrated_train_early.csv", "demo_upload_early.csv"):
        frame = pd.read_csv(output / name)
        frame["package_code"] = frame.component_id.map(codes)
        if frame.package_code.isna().any():
            raise ValueError("Unknown component in package metadata restoration")
        frame.to_csv(output / name, index=False)
    for name in ("training_screening_response.json", "demo_response.json"):
        response = json.loads((output / name).read_text())
        for record in response["records"]:
            record["metadata"]["package_code"] = codes.loc[record["component_id"]]
        (output / name).write_text(json.dumps(response, indent=2, allow_nan=False))
    audit = json.loads((output / "integration_audit.json").read_text())
    audit["package_code_formatting"] = "Restored from original component metadata (805 -> 0805); no model feature or prediction changed."
    (output / "integration_audit.json").write_text(json.dumps(audit, indent=2, allow_nan=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--output", type=Path, default=Path("outputs/cleaned_training_integration"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    dataset = root / "outputs/mlcc_v1"
    output = args.output
    if output.exists():
        raise FileExistsError("Choose a fresh output directory")
    with ZipFile(args.archive) as archive:
        members = {n: archive.read(n) for n in archive.namelist() if n.endswith('.csv')}
    clean = pd.read_csv(io.BytesIO(members["01_cleaned_sorted_train_early.csv"]))
    technical = pd.read_csv(io.BytesIO(members["06_component_analysis_technical.csv"]))
    original = pd.read_csv(dataset / "train_early.csv")
    keys = GROUP_COLUMNS + ["hours"]
    clean = clean.sort_values(keys).reset_index(drop=True)
    original = original.sort_values(keys).reset_index(drop=True)
    pd.testing.assert_frame_equal(clean[original.columns], original,
        check_dtype=False, check_exact=False, rtol=1e-12, atol=1e-12)
    if clean.duplicated(keys).any() or clean.isna().any().any():
        raise ValueError("Cleaned training data contains missing or duplicate observations")
    bundle = load_bundle(dataset / "model_bundle")
    original_hash = hashlib.sha256((dataset / "train_early.csv").read_bytes()).hexdigest()
    if original_hash != bundle.manifest["dataset_sha256"]["train_early.csv"]:
        raise ValueError("Original training file no longer matches model provenance")
    for split in ("calibration", "test"):
        other = pd.read_csv(dataset / f"{split}_early.csv")
        for col in ("component_id", "batch_id"):
            if set(clean[col]) & set(other[col]):
                raise ValueError(f"{split} overlaps training {col}")
    features, _, rejected = prepare_early_features(clean)
    original_features, _, _ = prepare_early_features(original)
    if rejected or len(features) != 7200:
        raise ValueError("Unexpected component count or invalid components")
    pd.testing.assert_frame_equal(features[FORECAST_COLUMNS], original_features[FORECAST_COLUMNS],
        check_exact=False, rtol=1e-12, atol=1e-12)
    comparison = features.merge(technical, on=["component_id", "batch_id", "component_family"],
        suffixes=("_model", "_teammate"), validate="one_to_one")
    if len(comparison) != len(features) or len(technical) != len(features):
        raise ValueError("Technical feature identities do not match cleaned components")
    mapping = {
        "leakage_0h_ua": ("initial_value", 1),
        "leakage_24h_ua": ("current_value", 1),
        "upper_limit_ua": ("upper_limit", 1),
        "change_0h_to_24h_ua": ("delta", 1),
        "percent_change_teammate": ("percent_change_model", 0.01),
        "slope_ua_per_hour": ("slope", 1),
        "fraction_of_limit": ("limit_fraction", 1),
    }
    checks = []
    for source, (target, factor) in mapping.items():
        error = (comparison[source] * factor - comparison[target]).abs()
        ok = np.allclose(comparison[source] * factor, comparison[target], rtol=1e-8, atol=1e-10)
        checks.append({"teammate_feature": source, "model_feature": target,
                       "multiply_by": factor, "matches": bool(ok), "max_absolute_error": float(error.max())})
        if not ok:
            raise ValueError(f"Feature mismatch: {source}")
    robust_difference = (comparison.robust_z_score - comparison.current_batch_robust_z).abs()
    response = screen_readings(clean, bundle, forecast_model="xgboost")
    if response["summary"]["unscored_count"]:
        raise ValueError("Cleaned data failed production scoring")
    # Verify real scored predictions, not just the all-unscored response path.
    demo_batch = clean.loc[clean.batch_id.eq(clean.batch_id.iloc[0])]
    expected = screen_readings(demo_batch, bundle, forecast_model="xgboost")
    shuffled = screen_readings(demo_batch.sample(frac=1, random_state=42), bundle, forecast_model="xgboost")
    if shuffled != expected:
        raise ValueError("Row order changed inference")
    audit = {
        "archive_sha256": hashlib.sha256(args.archive.read_bytes()).hexdigest(),
        "model_bundle_id": bundle.manifest["bundle_id"],
        "rows": len(clean), "components": len(features), "batches": int(clean.batch_id.nunique()),
        "original_training_data_equivalent": True, "model_features_equivalent": True,
        "training_provenance_verified": True, "split_overlap": False,
        "retrained": False, "reason": "Cleaned measurements and model features match the existing trained data within floating-point tolerance.",
        "feature_checks": checks,
        "robust_z_differences_over_1e_8": int((robust_difference > 1e-8).sum()),
        "robust_z_max_difference": float(robust_difference.max()),
        "robust_z_policy": "Preserve production MAD scale floor (1% of median, 10% of std, epsilon); teammate robust_z is an EDA reference only.",
        "teammate_baseline_counts": technical.status.value_counts().to_dict(),
        "production_summary": response["summary"],
        "shuffled_batch_prediction_check": "passed",
        "interpretation": "Training-set scoring verifies integration only; do not use it to report model accuracy. Existing held-out evaluation remains unchanged.",
    }
    output.mkdir(parents=True)
    (output / "teammate_originals").mkdir()
    for name, raw in members.items():
        if Path(name).name != name:
            raise ValueError("Archive filenames must be flat")
        (output / "teammate_originals" / name).write_bytes(raw)
    clean.to_csv(output / "integrated_train_early.csv", index=False)
    features.to_csv(output / "model_features.csv", index=False)
    pd.DataFrame(checks).to_csv(output / "feature_mapping.csv", index=False)
    (output / "integration_audit.json").write_text(json.dumps(audit, indent=2, allow_nan=False))
    (output / "training_screening_response.json").write_text(json.dumps(response, indent=2, allow_nan=False))
    demo_batch.to_csv(output / "demo_upload_early.csv", index=False)
    (output / "demo_response.json").write_text(json.dumps(expected, indent=2, allow_nan=False))
    evaluation = json.loads((dataset / "model_bundle/evaluation.json").read_text())
    pd.DataFrame(evaluation["xgboost_feature_importance"]).to_csv(output / "xgboost_gain_importance.csv", index=False)
    permutation = root / "outputs/teammate_integration/feature_importance.csv"
    if permutation.exists():
        (output / "heldout_feature_importance.csv").write_bytes(permutation.read_bytes())
    (output / "README.md").write_text(
        "# Cleaned training integration\n\n"
        "Verified 14,400 readings / 7,200 components / 36 batches against the actual training-file hash recorded by the model. "
        "All components score with the saved Isolation Forest + XGBoost models. No retraining was needed.\n\n"
        "Teammate percent_change uses percent; production uses fractional change (divide teammate values by 100). "
        "Production robust-z calculations retain their numerical scale floors. Screening status is never an input feature or a future-failure label.\n\n"
        "Backend: use integrated_train_early.csv with the existing score_mlcc_prototype.py, or "
        "screen_readings(readings, bundle, forecast_model='xgboost'). "
        "demo_upload_early.csv and demo_response.json provide a one-batch integration example. "
        "No API or frontend implementation is changed by this pack.\n\n"
        "training_screening_response.json is an integration result on TRAINING data, not an accuracy benchmark. "
        "Keep the existing held-out test evaluation for reporting. Original teammate files are preserved under teammate_originals/.\n")
    restore_package_metadata(output, dataset)
    pack = output.parent / "MLCC_CLEANED_INTEGRATION_HANDOFF.zip"
    with ZipFile(pack, "x", compression=ZIP_DEFLATED) as archive:
        for path in sorted(output.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(output))
        archive.write(Path(__file__), "scripts/integrate_cleaned_training.py")
    with ZipFile(pack) as archive:
        if archive.testzip():
            raise ValueError("Handoff archive integrity failed")
    print(json.dumps(audit, indent=2))
    print(f"Handoff: {pack}")


if __name__ == "__main__":
    main()
