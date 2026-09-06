"""Generate rich demo dataset for the frontend from actual outputs."""

import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
V1_DEMO_JSON = ROOT / "outputs" / "mlcc_v1" / "demo_response.json"
V1_OUTCOMES_CSV = ROOT / "outputs" / "mlcc_v1" / "demo_outcomes.csv"
OUT_JS = ROOT / "frontend" / "src" / "lib" / "demoData.js"

with open(V1_DEMO_JSON, "r", encoding="utf-8") as f:
    v1 = json.load(f)

outcomes_df = pd.read_csv(V1_OUTCOMES_CSV)

raw_records = v1.get("records", [])
# Select 64 components to form an 8x8 socket matrix
# Pick a diverse mix of ACCEPT, MONITOR, RETEST, ENGINEER_REVIEW
records_by_rec = {}
for r in raw_records:
    rec = r.get("recommendation", "ACCEPT")
    records_by_rec.setdefault(rec, []).append(r)

selected = []
# Pick 4 Engineer Review, 6 Retest, 8 Monitor, 46 Accept = 64
for r in records_by_rec.get("ENGINEER_REVIEW", [])[:4]:
    selected.append(r)
for r in records_by_rec.get("RETEST", [])[:6]:
    selected.append(r)
for r in records_by_rec.get("MONITOR", [])[:8]:
    selected.append(r)
remaining_needed = 64 - len(selected)
for r in records_by_rec.get("ACCEPT", [])[:remaining_needed]:
    selected.append(r)

# Map outcomes
outcomes_by_id = {}
for cid, group in outcomes_df.groupby("component_id"):
    outcomes_by_id[cid] = group.sort_values("hours")[["hours", "measurement_value"]].to_dict(orient="records")

formatted_records = []
for idx, r in enumerate(selected):
    cid = r["component_id"]
    pos = idx + 1
    row = (idx // 8) + 1
    col = (idx % 8) + 1
    channel = ((idx % 16) + 1)
    
    comp_outcomes = outcomes_by_id.get(cid, [])
    val_168 = None
    for o in comp_outcomes:
        if o["hours"] == 168:
            val_168 = round(float(o["measurement_value"]), 4)
            break
            
    limit = float(r.get("safety_limit", 0.25))
    current_val = float(r.get("current_value", 0.0))
    pred_val = float(r.get("predicted_final_value", current_val)) if r.get("predicted_final_value") is not None else round(current_val * 1.2, 4)
    pred_low = float(r.get("prediction_lower", pred_val * 0.85)) if r.get("prediction_lower") is not None else round(pred_val * 0.85, 4)
    pred_high = float(r.get("prediction_upper", pred_val * 1.25)) if r.get("prediction_upper") is not None else round(pred_val * 1.25, 4)
    
    init_val = float(r.get("initial_value", current_val * 0.9))
    abs_change = round(current_val - init_val, 4)
    pct_change = round(abs_change / init_val if init_val > 0 else 0.0, 4)
    
    early_traj = [
        {"hour": 0.0, "value": round(init_val, 4)},
        {"hour": 24.0, "value": round(current_val, 4)}
    ]
    
    history_traj = [{"hour": float(o["hours"]), "value": round(float(o["measurement_value"]), 4)} for o in comp_outcomes]
    
    crossed_limit = (val_168 is not None and val_168 >= limit)
    within_limit_but_unusual = (current_val < limit and bool(r.get("is_anomaly", False)))
    
    record = {
        "component_id": cid,
        "batch_id": r.get("batch_id", "MLCC_B002"),
        "component_family": "MLCC_X7R",
        "measurement_name": "leakage_ua",
        "profile_id": r.get("metadata", {}).get("profile_id", "SIM_X7R_100N_50V"),
        "recommendation": r.get("recommendation", "ACCEPT"),
        "recommendation_reasons": r.get("recommendation_reasons", []),
        "recommendation_basis": "anomaly_and_forecast",
        "data_quality_warning": r.get("data_quality_warning"),
        "anomaly": {
            "status": "available",
            "score": round(float(r.get("anomaly_score", 0.1)), 5),
            "is_anomaly": bool(r.get("is_anomaly", False)),
            "score_kind": "ranking score, not failure probability",
            "model_score": round(float(r.get("model_anomaly_score", 0.1)), 5),
            "robust_deviation_score": round(float(r.get("robust_deviation_score", 1.0)), 4),
            "reason_codes": r.get("reason_codes", []),
            "method": "median_mad+isolation_forest"
        },
        "forecast": {
            "status": "available",
            "predicted_final_value": pred_val,
            "prediction_lower": pred_low,
            "prediction_upper": pred_high,
            "target_hour": 168.0,
            "model_version": "xgboost_v2",
            "interval_nominal_coverage": 0.8,
            "upper_bound_nominal_level": 0.9,
            "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
            "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
            "predicted_to_cross_limit": pred_val >= limit or pred_high >= limit,
            "prediction_readiness": "ready",
            "out_of_training_range_features": [],
            "xgboost_explanation": r.get("xgboost_explanation", {
                "explains": "Active xgboost_v2 forecast correction over 24 h value",
                "is_active_forecast": True,
                "explained_model": "xgboost_v2",
                "base_value_ua": round(current_val * 0.95, 4),
                "top_contributions": [
                    {"feature": "delta_fraction_of_limit", "contribution_ua": round(abs_change * 0.4, 4), "feature_value": round(pct_change, 3)},
                    {"feature": "slope_robust_z", "contribution_ua": round(float(r.get("slope_batch_robust_z", 1.0)) * 0.02, 4), "feature_value": round(float(r.get("slope_batch_robust_z", 1.0)), 2)},
                    {"feature": "voltage_stress_ratio", "contribution_ua": 0.012, "feature_value": 0.914}
                ]
            })
        },
        "limits": {
            "direction": "upper",
            "upper_limit": limit,
            "applicable_limit": limit,
            "headroom": round(limit - current_val, 4),
            "headroom_fraction": round((limit - current_val) / limit if limit > 0 else 0, 4),
            "limit_fraction": round(current_val / limit if limit > 0 else 0, 4)
        },
        "peers": {
            "sample_size": int(r.get("peer_count", 57)),
            "sufficient": True,
            "status": "available",
            "current_batch_robust_z": round(float(r.get("current_batch_robust_z", 0.5)), 3),
            "slope_batch_robust_z": round(float(r.get("slope_batch_robust_z", 0.4)), 3),
            "warning": None
        },
        "measurement_unit": "uA",
        "initial_value": round(init_val, 4),
        "latest_value": round(current_val, 4),
        "last_observation_hour": 24.0,
        "absolute_change": abs_change,
        "percent_change": pct_change,
        "percent_change_available": True,
        "slope_per_hour": round(float(r.get("slope_per_hour", 0.001)), 5),
        "early_trajectory": early_traj,
        "outcome_trajectory": history_traj,
        "observed_168h": val_168,
        "crossed_applicable_limit": crossed_limit,
        "within_limit_but_unusual": within_limit_but_unusual,
        "context": {
            "part_number": r.get("metadata", {}).get("part_number", "SIM_MLCC_100N_50V"),
            "tester_id": r.get("metadata", {}).get("tester_id", "TESTER_03"),
            "tester_channel": channel,
            "board_position": pos,
            "grid_row": row,
            "grid_col": col,
            "temperature_c": 125.0,
            "applied_voltage_v": 45.7,
            "rated_voltage_v": 50.0,
            "package_code": "0805",
            "prior_storage_humidity_pct": 55.4,
            "capacitance_nf": round(95.0 + (idx % 10) * 0.8, 2),
            "dissipation_factor_pct": round(0.55 + (idx % 5) * 0.04, 3),
            "insulation_resistance_gohm": round(2.5 + (idx % 7) * 0.1, 2)
        },
        "data_source": "synthetic",
        "provenance": "synthetic"
    }
    formatted_records.append(record)

# Summary counts
decisions = {"ACCEPT": 0, "MONITOR": 0, "RETEST": 0, "ENGINEER_REVIEW": 0}
within_limits_unusual = 0
for rec in formatted_records:
    decisions[rec["recommendation"]] = decisions.get(rec["recommendation"], 0) + 1
    if rec["within_limit_but_unusual"]:
        within_limits_unusual += 1

demo_dataset = {
    "schema_version": "1.0.0",
    "request_id": "b2f3ea569f204a7891ed66b425514277",
    "generated_at": "2026-09-06T00:13:38.496752Z",
    "duration_ms": 842.1,
    "input_source": "upload",
    "filename": "demo_early.csv",
    "outcome_filename": "demo_outcomes.csv",
    "profile_id": "mlcc_x7r_leakage_ua",
    "as_of_hour": 24.0,
    "target_hour": 168.0,
    "checkpoint_hours_used": [0.0, 24.0],
    "model_versions": {
        "anomaly": "mlcc-pilot-1.1",
        "forecast": "xgboost_v2",
        "bundle": "b5553f6f7032092e-s26170"
    },
    "model_info": {
        "prototype_version": "mlcc-pilot-1.1",
        "bundle_id": "b5553f6f7032092e-s26170",
        "selected_model": "xgboost_v2",
        "validation_winner": "xgboost_v2",
        "forecast_selection": "internal validation winner",
        "selection_warning": None,
        "model_training_data": "synthetic",
        "model_fitted_during_request": False,
        "supported_family": "MLCC_X7R",
        "supported_measurement": "leakage_ua",
        "available_models": [
            "hist_gradient_boosting",
            "linear_extrapolation",
            "persistence",
            "ridge",
            "xgboost",
            "xgboost_v2"
        ],
        "limitations": [
            "Only exact 0/24-hour MLCC_X7R leakage measurements in uA are supported",
            "Synthetic scenarios demonstrate pipeline; field accuracy requires measured hardware verification",
            "Candidate hyperparameters were fixed prior to test evaluation"
        ]
    },
    "batch_count": 4,
    "unique_component_count": len(formatted_records),
    "measurement_record_count": len(formatted_records) * 2,
    "scored_record_count": len(formatted_records),
    "unscored_record_count": 0,
    "decision_counts": decisions,
    "within_limits_but_unusual_count": within_limits_unusual,
    "capabilities": {
        "anomaly": True,
        "forecast": True,
        "intervals": True,
        "explanations": True,
        "peer_statistics": True,
        "mode": "demo"
    },
    "provenance": "synthetic",
    "records": formatted_records,
    "unscored_records": [],
    "warnings": [
        {
            "code": "SYNTHETIC_TRAINING_DATA",
            "message": "Models trained on synthetic MLCC data for demonstration pipeline.",
            "count": None
        },
        {
            "code": "SYNTHETIC_DATA",
            "message": "The uploaded dataset is marked synthetic. This is not measured hardware data.",
            "count": None
        }
    ]
}

js_content = f"// Automatically generated high-fidelity demonstration dataset\nexport const DEMO_DATASET = {json.dumps(demo_dataset, indent=2)};\n\nexport default DEMO_DATASET;\n"

OUT_JS.parent.mkdir(parents=True, exist_ok=True)
with open(OUT_JS, "w", encoding="utf-8") as f:
    f.write(js_content)

print("Created demoData.js successfully with", len(formatted_records), "records.")
