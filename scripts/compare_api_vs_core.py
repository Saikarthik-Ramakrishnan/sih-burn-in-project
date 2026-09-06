"""Compare API screening output against direct ML-core inference.

Same CSV, same bundle, same forecast model, complete batches. The API path adds
text-first ingestion, validation and a typed mapping; the core path calls
``screen_readings`` directly on a plain pandas read. Any disagreement means the
API layer changed a number it had no business changing.

Usage (from the repository root, with the server NOT required):

    .venv/Scripts/python.exe scripts/compare_api_vs_core.py [csv_path]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from sih26170.api.config import ServiceMode, Settings  # noqa: E402
from sih26170.api.main import create_app  # noqa: E402
from sih26170.mlcc_prototype import load_bundle, screen_readings  # noqa: E402

BUNDLE = PROJECT_ROOT / "outputs" / "mlcc_v2" / "model_bundle"
DEFAULT_CSV = PROJECT_ROOT / "outputs" / "mlcc_v1" / "train_early.csv"

#: Fields that must agree exactly between the two paths.
NUMERIC_FIELDS = (
    "anomaly_score",
    "predicted_final_value",
    "prediction_lower",
    "prediction_upper",
    "current_batch_robust_z",
    "slope_batch_robust_z",
    "percent_change",
    "slope_per_hour",
    "limit_fraction",
)
EXACT_FIELDS = ("recommendation", "is_anomaly", "status")

TOLERANCE = 1e-9


def api_records(csv_path: Path, forecast_model: str | None) -> dict[str, dict]:
    settings = Settings(mode=ServiceMode.DEMO, mlcc_bundle_dir=BUNDLE)
    app = create_app(settings)
    data = {"forecast_model": forecast_model} if forecast_model else None
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/screen",
            files={"file": (csv_path.name, csv_path.read_bytes(), "text/csv")},
            data=data,
        )
    response.raise_for_status()
    body = response.json()
    out: dict[str, dict] = {}
    for record in body["records"]:
        out[record["component_id"]] = {
            "anomaly_score": record["anomaly"]["score"],
            "is_anomaly": record["anomaly"]["is_anomaly"],
            "predicted_final_value": record["forecast"]["predicted_final_value"],
            "prediction_lower": record["forecast"]["prediction_lower"],
            "prediction_upper": record["forecast"]["prediction_upper"],
            "current_batch_robust_z": record["peers"]["current_batch_robust_z"],
            "slope_batch_robust_z": record["peers"]["slope_batch_robust_z"],
            "percent_change": record["percent_change"],
            "slope_per_hour": record["slope_per_hour"],
            "limit_fraction": record["limits"]["limit_fraction"],
            "recommendation": record["recommendation"],
            "status": "scored",
        }
    for record in body["unscored_records"]:
        out[record["component_id"]] = {"status": "unscored"}
    return out


def core_records(csv_path: Path, forecast_model: str | None) -> dict[str, dict]:
    frame = pd.read_csv(csv_path)
    bundle = load_bundle(BUNDLE)
    result = screen_readings(
        frame, bundle, as_of_hour=24.0, forecast_model=forecast_model
    )
    out: dict[str, dict] = {}
    for record in result["records"]:
        out[str(record["component_id"])] = {
            key: record.get(key)
            for key in (*NUMERIC_FIELDS, "recommendation", "is_anomaly", "status")
        }
    return out


def compare(api: dict[str, dict], core: dict[str, dict]) -> int:
    only_api = sorted(set(api) - set(core))
    only_core = sorted(set(core) - set(api))
    shared = sorted(set(api) & set(core))

    print(f"components: api={len(api)}  core={len(core)}  shared={len(shared)}")
    if only_api:
        print(f"  ONLY IN API  ({len(only_api)}): {only_api[:5]}")
    if only_core:
        print(f"  ONLY IN CORE ({len(only_core)}): {only_core[:5]}")

    mismatches: dict[str, list[tuple[str, object, object]]] = {}
    for component_id in shared:
        a, c = api[component_id], core[component_id]
        for field in EXACT_FIELDS:
            if field in a and field in c and a[field] != c[field]:
                mismatches.setdefault(field, []).append((component_id, a[field], c[field]))
        for field in NUMERIC_FIELDS:
            av, cv = a.get(field), c.get(field)
            if av is None and cv is None:
                continue
            if av is None or cv is None:
                mismatches.setdefault(field, []).append((component_id, av, cv))
                continue
            if abs(float(av) - float(cv)) > TOLERANCE:
                mismatches.setdefault(field, []).append((component_id, av, cv))

    print()
    for field in (*EXACT_FIELDS, *NUMERIC_FIELDS):
        bad = mismatches.get(field, [])
        flag = "OK  " if not bad else "DIFF"
        print(f"  {flag} {field:26} mismatches={len(bad)}")
        for component_id, av, cv in bad[:3]:
            print(f"         {component_id}: api={av!r}  core={cv!r}")

    total = sum(len(v) for v in mismatches.values())
    print()
    print(f"total field mismatches: {total}")
    return 0 if (total == 0 and not only_api and not only_core) else 1


def main() -> None:
    csv_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CSV
    forecast_model = sys.argv[2] if len(sys.argv) > 2 else None
    print(f"csv            : {csv_path.name}")
    print(f"forecast_model : {forecast_model or '(bundle validation winner)'}")
    print("-" * 70)

    api = api_records(csv_path, forecast_model)
    core = core_records(csv_path, forecast_model)
    sys.exit(compare(api, core))


if __name__ == "__main__":
    main()
