"""Run the real MLCC bundle through the API and save a genuine sample response.

Everything here comes from an actual run of the shipped mlcc-pilot-1.1 (v2) artifact
through the real HTTP surface. Nothing is hand-authored, and no model numbers
are invented.

Writes docs/backend/sample_response.json for the frontend to build against.

Usage (from the repository root):

    .venv/Scripts/python.exe scripts/demo_screen.py
    .venv/Scripts/python.exe scripts/demo_screen.py --forecast-model xgboost
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from sih26170.api.config import ServiceMode, Settings  # noqa: E402
from sih26170.api.main import create_app  # noqa: E402
from sih26170.api.sample_data import build_sample_csv  # noqa: E402

BUNDLE = PROJECT_ROOT / "outputs" / "mlcc_v2" / "model_bundle"
OUTPUT = PROJECT_ROOT / "docs" / "backend" / "sample_response.json"

#: How many records to keep in the saved sample response. The full run is
#: summarised in the console output; the file stays small enough to read.
SAMPLE_RECORDS = 3


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--forecast-model",
        default=None,
        help="Model to request. Omit to use the artifact's internal-validation winner.",
    )
    args = parser.parse_args()

    settings = Settings(mode=ServiceMode.DEMO, mlcc_bundle_dir=BUNDLE)
    app = create_app(settings)
    payload = build_sample_csv()

    with TestClient(app) as client:
        ready = client.get("/api/v1/health/ready")
        print(f"readiness           HTTP {ready.status_code}  ready={ready.json()['ready']}")

        data = {"forecast_model": args.forecast_model} if args.forecast_model else None
        started = time.perf_counter()
        response = client.post(
            "/api/v1/screen",
            files={"file": ("sih26170_mlcc_synthetic_sample.csv", payload, "text/csv")},
            data=data,
        )
        wall_ms = (time.perf_counter() - started) * 1000

    response.raise_for_status()
    body = response.json()
    info = body["model_info"]

    print(f"HTTP {response.status_code}   request_id {body['request_id']}")
    print("-" * 78)
    print(f"  file                {body['filename']}  ({len(payload) / 1024:.0f} KiB)")
    print(f"  cutoff -> target    {body['as_of_hour']:g} h -> {body['target_hour']:g} h")
    print(f"  batches/components  {body['batch_count']} / {body['unique_component_count']}")
    print(f"  scored / unscored   {body['scored_record_count']} / {body['unscored_record_count']}")
    print(f"  decisions           {body['decision_counts']}")
    print(f"  server duration_ms  {body['duration_ms']}   (wall {wall_ms:.0f} ms)")
    print(f"  uploaded provenance {body['provenance']}")
    print()
    print("  MODEL")
    print(f"    prototype         {info['prototype_version']}  bundle {info['bundle_id']}")
    print(f"    forecasts from    {info['selected_model']}")
    print(f"    validation winner {info['validation_winner']}")
    print(f"    selection         {info['forecast_selection']}")
    print(f"    selection warning {info['selection_warning']}")
    print(f"    trained on        {info['model_training_data']}")
    print(f"    fitted in request {info['model_fitted_during_request']}")
    print()
    print("  WARNINGS")
    for warning in body["warnings"]:
        count = f" (x{warning['count']})" if warning.get("count") else ""
        print(f"    - {warning['code']}{count}")
        print(f"      {warning['message'][:96]}")

    print()
    print("  MOST URGENT RECORD")
    record = body["records"][0]
    forecast = record["forecast"]
    print(f"    {record['component_id']}  batch {record['batch_id']}  profile {record['profile_id']}")
    print(f"    recommendation    {record['recommendation']}  {record['recommendation_reasons']}")
    print(
        f"    early             {record['initial_value']:.4f} -> {record['latest_value']:.4f} uA"
        f"  ({record['percent_change'] * 100:+.1f} %)"
        if record["percent_change"] is not None
        else f"    early             {record['initial_value']} -> {record['latest_value']} uA"
    )
    print(
        f"    limit             {record['limits']['applicable_limit']} uA"
        f"  (using {record['limits']['limit_fraction'] * 100:.1f} % of it)"
    )
    print(f"    anomaly           score {record['anomaly']['score']:.3f}  flagged={record['anomaly']['is_anomaly']}")
    print(f"                      {record['anomaly']['score_kind']}")
    print(
        f"    forecast @168h    {forecast['predicted_final_value']:.4f} uA"
        f"  [{forecast['prediction_lower']:.4f}, {forecast['prediction_upper']:.4f}]"
        f"  from '{forecast['model_version']}'"
    )
    print(f"    crosses limit     {forecast['predicted_to_cross_limit']}")
    print(f"    readiness         {forecast['prediction_readiness']}")
    print(
        f"    peers             n={record['peers']['sample_size']}"
        f"  robust z={record['peers']['current_batch_robust_z']:.2f}"
    )

    evaluation = body.get("evaluation")
    print()
    print("  EVALUATION-ONLY SECTION")
    if evaluation is None:
        print("    omitted: the upload contained only early data")
    else:
        print(f"    kind              {evaluation['kind']}")
        print(f"    outcomes          {len(evaluation['outcomes'])} at {evaluation['target_hour']:g} h")

    # Save a trimmed but genuine response for the frontend.
    saved = dict(body)
    saved["records"] = body["records"][:SAMPLE_RECORDS]
    if evaluation:
        saved["evaluation"] = dict(evaluation)
        saved["evaluation"]["outcomes"] = evaluation["outcomes"][:SAMPLE_RECORDS]
    saved["component_summaries"] = body["component_summaries"][:SAMPLE_RECORDS]
    saved["_note"] = (
        f"Genuine response from a real run of {info['prototype_version']} on the "
        f"synthetic MLCC sample. records/component_summaries/evaluation.outcomes "
        f"are truncated to {SAMPLE_RECORDS} entries for readability; every other "
        "field is exactly as returned. Model numbers are not hand-authored."
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(saved, indent=2) + "\n", encoding="utf-8")
    print()
    print(f"wrote {OUTPUT.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
