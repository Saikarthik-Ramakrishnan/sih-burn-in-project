"""Check exported data, loaded inference and separate synthetic stress sets."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sys
from time import perf_counter

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from sih26170.features import GROUP_COLUMNS  # noqa: E402
from sih26170.mlcc_prototype import (  # noqa: E402
    ModelBundle, _evaluate, _joined_labels, load_bundle, prepare_early_features, screen_readings,
)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    data = root / "outputs/mlcc_v1"
    destination = data / "evaluation"
    destination.mkdir(exist_ok=True)
    ids = {column: str for column in GROUP_COLUMNS}
    manifest = json.loads((data / "generation_manifest.json").read_text())
    counts = {}
    split_ids = {}
    split_batches = {}
    for name, info in manifest["files"].items():
        path = data / name
        assert sha256(path.read_bytes()).hexdigest() == info["sha256"], name
    for split in ("train", "calibration", "test"):
        full = pd.read_csv(data / f"{split}_readings.csv", dtype=ids)
        early = pd.read_csv(data / f"{split}_early.csv", dtype=ids)
        labels = pd.read_csv(data / f"{split}_labels.csv", dtype=ids)
        pd.testing.assert_frame_equal(
            early.reset_index(drop=True), full.loc[full.hours.isin((0, 24))].reset_index(drop=True),
        )
        assert not full.duplicated(GROUP_COLUMNS + ["hours"]).any()
        assert labels.component_id.is_unique
        assert set(labels.component_id) == set(full.component_id)
        assert full.data_source.eq("synthetic").all()
        assert full.is_synthetic.all()
        assert not set(labels.columns).intersection({"scenario", "final_value", "is_future_failure"}).intersection(full.columns)
        for column in ("measurement_value", "upper_limit", "capacitance_nf", "dissipation_factor_pct", "insulation_resistance_gohm"):
            assert np.isfinite(full[column]).all() and full[column].gt(0).all(), column
        np.testing.assert_allclose(full.insulation_resistance_gohm, full.measurement_voltage_v / (1000 * full.measurement_value), rtol=1e-9)
        split_ids[split] = set(full.component_id)
        split_batches[split] = set(full.batch_id)
        counts[split] = {"components": len(split_ids[split]), "batches": len(split_batches[split]), "readings": len(full), "early_readings": len(early)}
    for a, b in (("train", "calibration"), ("train", "test"), ("calibration", "test")):
        assert not split_ids[a] & split_ids[b]
        assert not split_batches[a] & split_batches[b]

    start = perf_counter()
    bundle = load_bundle(data / "model_bundle")
    load_seconds = perf_counter() - start
    early = pd.read_csv(data / "demo_early.csv", dtype=ids)
    later = pd.read_csv(data / "demo_outcomes.csv", dtype=ids)
    start = perf_counter()
    first = screen_readings(early, bundle, forecast_model="xgboost")
    score_seconds = perf_counter() - start
    changed_later = later.copy()
    changed_later["measurement_value"] *= 1000
    second = screen_readings(pd.concat([early, changed_later], ignore_index=True).sample(frac=1, random_state=11), bundle, forecast_model="xgboost")
    key = lambda row: tuple(row[column] for column in GROUP_COLUMNS)
    assert sorted(first["records"], key=key) == sorted(second["records"], key=key)
    assert first["summary"] == second["summary"]
    reveal = screen_readings(early, bundle, future_outcomes=later, forecast_model="xgboost")
    assert first["records"] == reveal["records"]
    assert len(reveal["future_outcomes"]) == len(later)
    (data / "demo_response.json").write_text(json.dumps(reveal, indent=2, allow_nan=False) + "\n")

    xgb_bundle = ModelBundle({**bundle.manifest, "selected_model": "xgboost"}, bundle.imputer, bundle.detector, bundle.models, bundle.radii)
    test_features, _, invalid = prepare_early_features(pd.read_csv(data / "test_early.csv", dtype=ids))
    assert not invalid
    test_labels = _joined_labels(test_features, pd.read_csv(data / "test_labels.csv", dtype=ids))
    (destination / "xgboost_demo_test_metrics.json").write_text(json.dumps(_evaluate(test_features, test_labels, xgb_bundle), indent=2, allow_nan=False) + "\n")
    stress_results = {}
    for name in ("low_prevalence", "unseen_condition"):
        readings = pd.read_csv(data / f"stress_{name}_early.csv", dtype=ids)
        labels = pd.read_csv(data / f"stress_{name}_labels.csv", dtype=ids)
        features, _, unscored = prepare_early_features(readings)
        assert not unscored
        result = _evaluate(features, _joined_labels(features, labels), xgb_bundle)
        result["interpretation"] = (
            "Separate synthetic stress test. No training, tuning or selection used these rows. "
            "Rare-set recall has very few events; shifted-condition interval coverage is not assured."
        )
        stress_results[name] = result
    (destination / "stress_metrics.json").write_text(json.dumps(stress_results, indent=2, allow_nan=False) + "\n")
    verification = {
        "data_source": "synthetic", "dataset_checksums_verified": len(manifest["files"]),
        "counts": counts, "whole_batch_and_device_disjointness": True,
        "derived_insulation_resistance_checked": True, "future_reading_mutation_invariance": True,
        "record_reordering_invariance": True, "loaded_bundle_seconds": load_seconds,
        "demo_scoring_seconds": score_seconds, "demo_summary": first["summary"],
        "demo_later_measurements": len(later), "demo_forecast_model": "xgboost", "validation_winner": bundle.selected_model,
        "timing_scope": "Single local run with this environment; not a performance guarantee",
    }
    (destination / "release_verification.json").write_text(json.dumps(verification, indent=2) + "\n")
    print(json.dumps(verification, indent=2))


if __name__ == "__main__":
    main()
