"""Reproduce and export the demo's extrapolation warnings.

The bundle records the condition ranges it was trained over. When a component's
input falls outside one of those ranges, the core lists the feature in
``out_of_training_range_features`` and the API raises a response-level
FORECAST_EXTRAPOLATES warning.

This script pins down, per affected component, exactly which feature was out of
range, what value it had, and what the training bounds were - so a genuine
out-of-range condition can be told apart from a parsing or conversion bug.

Writes docs/backend/extrapolation_report.csv and prints a summary.

Usage (from the repository root):

    .venv/Scripts/python.exe scripts/export_extrapolation.py [csv_path]
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pandas as pd
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from sih26170.api.config import ServiceMode, Settings  # noqa: E402
from sih26170.api.main import create_app  # noqa: E402
from sih26170.api.sample_data import build_sample_csv  # noqa: E402

BUNDLE = PROJECT_ROOT / "outputs" / "mlcc_v2" / "model_bundle"
REPORT = PROJECT_ROOT / "docs" / "backend" / "extrapolation_report.csv"


def main() -> None:
    manifest = json.loads((BUNDLE / "manifest.json").read_text(encoding="utf-8"))
    ranges: dict[str, list[float]] = manifest.get("training_condition_ranges", {})

    if len(sys.argv) > 1:
        source = Path(sys.argv[1])
        payload = source.read_bytes()
        label = source.name
    else:
        payload = build_sample_csv()
        label = "demo sample (sample_data.build_sample_csv)"

    uploaded = pd.read_csv(pd.io.common.BytesIO(payload), dtype=str)

    settings = Settings(mode=ServiceMode.DEMO, mlcc_bundle_dir=BUNDLE)
    app = create_app(settings)
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/screen",
            files={"file": (label, payload, "text/csv")},
        )
    response.raise_for_status()
    body = response.json()

    print(f"source                : {label}")
    print(f"scored                : {body['scored_record_count']}")
    print(f"unscored              : {body['unscored_record_count']}")

    warning = next(
        (w for w in body["warnings"] if w["code"] == "FORECAST_EXTRAPOLATES"), None
    )
    print(f"FORECAST_EXTRAPOLATES : {warning['count'] if warning else 0}")
    print()
    print("training condition ranges declared by the bundle:")
    for feature, (low, high) in ranges.items():
        print(f"  {feature:32} [{low:.6f}, {high:.6f}]")
    print()

    # Per-component uploaded values, so a reported value can be traced back to
    # the exact cell in the CSV.
    by_component: dict[str, dict[str, str]] = {}
    for row in uploaded.itertuples(index=False):
        by_component.setdefault(str(row.component_id), {})
        for feature in ranges:
            value = getattr(row, feature, None)
            if value is not None and str(value).strip():
                by_component[str(row.component_id)][feature] = str(value)

    rows: list[dict[str, object]] = []
    per_feature: dict[str, int] = {}

    for record in body["records"]:
        features = record["forecast"].get("out_of_training_range_features") or []
        if not features:
            continue
        component_id = record["component_id"]
        for feature in features:
            per_feature[feature] = per_feature.get(feature, 0) + 1
            bounds = ranges.get(feature, [None, None])
            raw = by_component.get(component_id, {}).get(feature)
            numeric: float | None
            try:
                numeric = float(raw) if raw is not None else None
            except ValueError:
                numeric = None

            if numeric is None or bounds[0] is None:
                verdict = "value not in upload (imputed) or no declared bound"
            elif numeric < bounds[0]:
                verdict = f"below training minimum by {bounds[0] - numeric:.6g}"
            elif numeric > bounds[1]:
                verdict = f"above training maximum by {numeric - bounds[1]:.6g}"
            else:
                verdict = "INSIDE declared bounds - investigate parsing/conversion"

            rows.append(
                {
                    "component_id": component_id,
                    "batch_id": record["batch_id"],
                    "profile_id": record.get("profile_id"),
                    "feature": feature,
                    "uploaded_value": raw,
                    "parsed_value": numeric,
                    "training_min": bounds[0],
                    "training_max": bounds[1],
                    "verdict": verdict,
                    "recommendation": record["recommendation"],
                    "predicted_final_value": record["forecast"]["predicted_final_value"],
                }
            )

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    with REPORT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "component_id",
                "batch_id",
                "profile_id",
                "feature",
                "uploaded_value",
                "parsed_value",
                "training_min",
                "training_max",
                "verdict",
                "recommendation",
                "predicted_final_value",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    affected = {r["component_id"] for r in rows}
    print(f"affected components   : {len(affected)}")
    print(f"feature-level flags   : {len(rows)}")
    print()
    print("by feature:")
    for feature, count in sorted(per_feature.items(), key=lambda kv: -kv[1]):
        print(f"  {feature:32} {count}")
    print()
    print("by verdict:")
    verdicts: dict[str, int] = {}
    for row in rows:
        key = str(row["verdict"]).split(" by ")[0]
        verdicts[key] = verdicts.get(key, 0) + 1
    for verdict, count in sorted(verdicts.items(), key=lambda kv: -kv[1]):
        print(f"  {count:5}  {verdict}")

    suspicious = [r for r in rows if "investigate" in str(r["verdict"])]
    print()
    if suspicious:
        print(f"*** {len(suspicious)} flags where the uploaded value is INSIDE the")
        print("    declared bounds. That points at parsing/conversion, not physics:")
        for row in suspicious[:5]:
            print(
                f"      {row['component_id']} {row['feature']}="
                f"{row['uploaded_value']} bounds=[{row['training_min']}, {row['training_max']}]"
            )
    else:
        print("No flag had an in-range uploaded value: every warning traces to a")
        print("genuine out-of-range condition in the file, not a conversion bug.")

    print()
    print(f"wrote {REPORT.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
