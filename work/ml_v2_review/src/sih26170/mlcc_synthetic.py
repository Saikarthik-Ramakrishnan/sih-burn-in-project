"""Fictional X7R MLCC burn-in trajectories for software development.

These distributions and limits are illustrative assumptions, NOT validated
physics, manufacturer specifications, reliability rates, or qualification data.
Measurement noise and shared tester faults are distinct from latent component
current. Ground truth lives only in the labels table, never in model inputs.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd

VERSION = "mlcc-synthetic-1.0.0"
HOURS = (0, 6, 12, 24, 48, 72, 96, 120, 144, 168)
HEALTHY_SCENARIOS = ("healthy_settling", "ordinary_noise")
DEFECT_SCENARIOS = (
    "gradual_drift", "accelerating_drift", "late_abrupt_onset",
    "intermittent_leakage", "moisture_associated_history",
)


@dataclass(frozen=True)
class MLCCProfile:
    profile_id: str
    part_number: str
    nominal_capacitance_nf: float
    rated_voltage_v: float
    package_code: str
    upper_limit_ua: float


# Explicitly fictional product identifiers; thresholds are demonstration values.
PROFILES = (
    MLCCProfile("SIM_X7R_10N_50V", "FICTIONAL-MLCC-01", 10.0, 50.0, "0805", 0.12),
    MLCCProfile("SIM_X7R_100N_50V", "FICTIONAL-MLCC-02", 100.0, 50.0, "0805", 0.25),
    MLCCProfile("SIM_X7R_1U_25V", "FICTIONAL-MLCC-03", 1000.0, 25.0, "1206", 0.70),
    MLCCProfile("SIM_X7R_4U7_16V", "FICTIONAL-MLCC-04", 4700.0, 16.0, "1210", 1.30),
)


@dataclass(frozen=True)
class MLCCDataset:
    readings: pd.DataFrame
    labels: pd.DataFrame
    batch_splits: pd.DataFrame
    seed: int
    condition: str
    configured_defect_prevalence: float


def _trajectory(
    rng: np.random.Generator,
    *,
    scenario: str,
    initial: float,
    upper_limit: float,
    stress_factor: float,
) -> tuple[np.ndarray, np.ndarray, float]:
    """Return latent current, degradation term, and simulated onset hour.

    Late shocks and intermittent pulses are deliberately not knowable perfectly
    from early observations. Severity is sampled independently from initial
    current; no final label is placed into the 0-hour/24-hour inputs.
    """
    t = np.asarray(HOURS, dtype=float)
    settling = rng.uniform(0.02, 0.25) * np.exp(-t / rng.uniform(4, 30))
    baseline = initial * (1.0 + settling)
    # Independent small physical variation, not merely monotone toy curves.
    baseline *= np.exp(rng.normal(0, 0.012, size=len(t)))
    degradation = np.zeros(len(t))
    onset = float("nan")
    severity = upper_limit * rng.lognormal(np.log(0.65), 0.75) * stress_factor
    severity = min(severity, 5.0 * upper_limit)
    if scenario == "gradual_drift":
        onset = float(rng.choice((0, 6, 12)))
        degradation = severity * np.maximum(t - onset, 0) / (168 - onset)
    elif scenario == "accelerating_drift":
        onset = float(rng.choice((0, 6, 12, 24)))
        progress = np.maximum(t - onset, 0) / (168 - onset)
        degradation = severity * progress ** rng.uniform(1.4, 3.3)
    elif scenario == "late_abrupt_onset":
        onset = float(rng.choice((48, 72, 96, 120, 144)))
        degradation = severity * (t >= onset) * (
            1 + 0.25 * np.maximum(t - onset, 0) / (168 - onset)
        )
    elif scenario == "intermittent_leakage":
        onset = float(rng.choice((6, 12, 24, 48)))
        eligible = t >= onset
        pulses = (rng.random(len(t)) < rng.uniform(0.25, 0.65)) & eligible
        degradation = severity * pulses * rng.uniform(0.5, 1.3, size=len(t))
    elif scenario == "moisture_associated_history":
        onset = float(rng.choice((0, 6, 12, 24, 48)))
        progress = np.maximum(t - onset, 0) / (168 - onset)
        degradation = severity * progress ** rng.uniform(0.7, 1.7)
        degradation *= np.exp(rng.normal(0, 0.06, size=len(t)))
    # The noise-only scenario has no added latent degradation term.
    return np.maximum(baseline + degradation, 1e-9), degradation, onset


def generate_mlcc_dataset(
    *,
    seed: int = 26170,
    n_batches: int = 60,
    components_per_batch: int = 200,
    defect_prevalence: float = 0.20,
    tester_fault_batch_rate: float = 0.45,
    condition: str = "standard",
    identity_prefix: str = "MLCC",
) -> MLCCDataset:
    """Generate equal profile counts and exact 60/20/20 whole-batch splits.

    ``defect_prevalence`` controls simulated mechanism assignment, not final
    failures. Instrument faults can coexist with a physical mechanism. The
    ``unseen_condition`` stress set changes measurement/test conditions and is
    not used to fit a model or select a threshold.
    """
    if n_batches < 20 or n_batches % 20:
        raise ValueError("n_batches must be a positive multiple of 20 (four profiles × five splits)")
    if components_per_batch < 8:
        raise ValueError("components_per_batch must be at least 8")
    if not 0 <= defect_prevalence < 1 or not 0 <= tester_fault_batch_rate <= 1:
        raise ValueError("prevalence/rate must be probabilities, with defect_prevalence < 1")
    if condition not in {"standard", "low_prevalence", "unseen_condition"}:
        raise ValueError("unknown condition")
    if not identity_prefix or not identity_prefix.replace("_", "").isalnum():
        raise ValueError("identity_prefix must use letters, digits, or underscores")

    rng = np.random.default_rng(seed)
    batches_per_profile = n_batches // len(PROFILES)
    # IDs, profiles, channel assignments, and simulated mechanisms are shuffled
    # separately; component identifiers never encode a mechanism or severity.
    shuffled_batch_numbers = rng.permutation(np.arange(1, n_batches + 1))
    component_numbers = rng.permutation(np.arange(1, n_batches * components_per_batch + 1))
    reading_rows: list[dict[str, object]] = []
    label_rows: list[dict[str, object]] = []
    split_rows: list[dict[str, object]] = []
    serial = 0
    scenario_names = (*HEALTHY_SCENARIOS, *DEFECT_SCENARIOS)
    scenario_weights = np.array([
        (1 - defect_prevalence) * 0.78, (1 - defect_prevalence) * 0.22,
        defect_prevalence * 0.23, defect_prevalence * 0.26,
        defect_prevalence * 0.18, defect_prevalence * 0.15,
        defect_prevalence * 0.18,
    ])

    for profile_index, profile in enumerate(PROFILES):
        splits = np.array(
            ["train"] * (batches_per_profile * 3 // 5)
            + ["calibration"] * (batches_per_profile // 5)
            + ["test"] * (batches_per_profile // 5)
        )
        rng.shuffle(splits)
        for batch_offset, split in enumerate(splits):
            batch_number = int(shuffled_batch_numbers[profile_index * batches_per_profile + batch_offset])
            batch_id = f"{identity_prefix}_B{batch_number:03d}"
            split_rows.append({"batch_id": batch_id, "profile_id": profile.profile_id, "split": str(split)})
            shifted = condition == "unseen_condition"
            stress_temperature = rng.uniform(100, 110) if shifted else rng.uniform(120, 125)
            stress_ratio = rng.uniform(0.60, 0.70) if shifted else rng.uniform(0.88, 1.00)
            measurement_temperature = rng.uniform(40, 45) if shifted else rng.uniform(23, 27)
            measurement_voltage = profile.rated_voltage_v * rng.uniform(0.97, 1.00)
            humidity = rng.uniform(65, 85) if shifted else rng.uniform(20, 75)
            lot_multiplier = float(rng.lognormal(0, 0.12))
            stress_factor = np.exp((stress_temperature - 122.5) / 45) * stress_ratio ** 1.3
            measurement_factor = np.exp((measurement_temperature - 25) / 35)
            channels = np.arange(components_per_batch) % 16 + 1
            rng.shuffle(channels)
            faulty_channel = int(rng.choice(np.unique(channels))) if rng.random() < tester_fault_batch_rate else -1
            channel_onset = int(rng.choice((0, 12, 72)))
            channel_offset = profile.upper_limit_ua * rng.uniform(0.45, 1.30)
            shared_channel_signal = channel_offset * (
                np.asarray(HOURS) >= channel_onset
            ) * (1.0 + rng.normal(0, 0.025, len(HOURS)))

            for position in range(components_per_batch):
                component_id = f"{identity_prefix}_C{int(component_numbers[serial]):06d}"
                serial += 1
                scenario = str(rng.choice(scenario_names, p=scenario_weights))
                channel = int(channels[position])
                tester_fault = channel == faulty_channel
                initial = profile.upper_limit_ua * 0.11 * lot_multiplier * rng.lognormal(0, 0.29)
                latent, degradation, onset = _trajectory(
                    rng, scenario=scenario, initial=float(initial),
                    upper_limit=profile.upper_limit_ua, stress_factor=float(stress_factor),
                )
                latent *= measurement_factor
                noise_sigma = rng.uniform(0.07, 0.17) if scenario == "ordinary_noise" else rng.uniform(0.012, 0.045)
                observed = latent * rng.lognormal(-0.5 * noise_sigma**2, noise_sigma, len(HOURS))
                observed += rng.normal(0, profile.upper_limit_ua * 0.0005, len(HOURS))
                if tester_fault:
                    observed += shared_channel_signal
                observed = np.maximum(observed, 1e-9)
                # Auxiliary readings are noisy, overlapping indicators. They do
                # not identify a particular physical cause or define the label.
                cap_initial = profile.nominal_capacitance_nf * rng.normal(1, 0.035)
                cap = cap_initial * (
                    1 - 0.0015 * np.log1p(np.asarray(HOURS))
                    - 0.009 * np.minimum(degradation / profile.upper_limit_ua, 3)
                    + rng.normal(0, 0.003, len(HOURS))
                )
                df_initial = rng.lognormal(np.log(0.70), 0.22)
                dissipation = np.maximum(
                    df_initial + 0.045 * degradation / profile.upper_limit_ua
                    + rng.normal(0, 0.035, len(HOURS)), 0.01,
                )
                # Moisture-associated cases overlap strongly with the healthy
                # storage-history distribution; this field cannot prove cause.
                history_humidity = np.clip(humidity + rng.normal(0, 9) + (
                    rng.uniform(0, 12) if scenario == "moisture_associated_history" else 0
                ), 5, 95)
                common = {
                    "component_id": component_id, "batch_id": batch_id,
                    "component_family": "MLCC_X7R", "measurement_name": "leakage_ua",
                    "upper_limit": profile.upper_limit_ua,
                    "profile_id": profile.profile_id, "part_number": profile.part_number,
                    "nominal_capacitance_nf": profile.nominal_capacitance_nf,
                    "rated_voltage_v": profile.rated_voltage_v, "package_code": profile.package_code,
                    "dielectric": "X7R", "applied_voltage_v": profile.rated_voltage_v * stress_ratio,
                    "voltage_stress_ratio": stress_ratio,
                    "measurement_voltage_v": measurement_voltage,
                    "prior_storage_humidity_pct": float(history_humidity),
                    "tester_id": f"TESTER_{batch_number % 3 + 1}",
                    "tester_channel": channel, "board_position": position + 1,
                    "data_source": "synthetic", "is_synthetic": True,
                    "generator_version": VERSION,
                }
                for i, hour in enumerate(HOURS):
                    reading_rows.append({
                        **common, "hours": hour, "measurement_value": float(observed[i]),
                        "temperature_c": float(stress_temperature + rng.normal(0, 0.15)),
                        "measurement_temperature_c": float(measurement_temperature),
                        "capacitance_nf": float(cap[i]),
                        "dissipation_factor_pct": float(dissipation[i]),
                        "insulation_resistance_gohm": float(measurement_voltage / (observed[i] * 1000)),
                    })
                physical_defect = scenario in DEFECT_SCENARIOS
                reported_scenario = "tester_channel_fault" if tester_fault and not physical_defect else scenario
                label_rows.append({
                    "component_id": component_id, "batch_id": batch_id,
                    "component_family": "MLCC_X7R", "measurement_name": "leakage_ua",
                    "profile_id": profile.profile_id, "scenario": reported_scenario,
                    "component_scenario": scenario,
                    "is_defect": bool(physical_defect), "is_healthy": bool(not physical_defect and not tester_fault),
                    "is_tester_fault": bool(tester_fault),
                    "anomaly_onset_hour": onset,
                    "tester_fault_onset_hour": channel_onset if tester_fault else float("nan"),
                    "final_value": float(observed[-1]), "true_final_value": float(latent[-1]),
                    "is_future_failure": bool(latent[-1] > profile.upper_limit_ua),
                    "is_observed_final_exceedance": bool(observed[-1] > profile.upper_limit_ua),
                    "ever_latent_exceedance": bool((latent > profile.upper_limit_ua).any()),
                    "upper_limit": profile.upper_limit_ua,
                    "data_source": "synthetic", "is_synthetic": True,
                })
    readings = pd.DataFrame(reading_rows).sort_values(["batch_id", "component_id", "hours"]).reset_index(drop=True)
    labels = pd.DataFrame(label_rows).sort_values(["batch_id", "component_id"]).reset_index(drop=True)
    batch_splits = pd.DataFrame(split_rows).sort_values("batch_id").reset_index(drop=True)
    return MLCCDataset(readings, labels, batch_splits, seed, condition, defect_prevalence)


def export_mlcc_dataset(
    dataset: MLCCDataset, output_dir: str | Path, *, include_stress: bool = True,
) -> dict[str, object]:
    """Write development CSVs, holdout demo and an auditable manifest.

    The demo is the lexicographically first heldout batch for each profile.
    Selection does not inspect model scores, scenarios, labels, or outcomes.
    """
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    files: dict[str, dict[str, object]] = {}

    def save(name: str, frame: pd.DataFrame) -> None:
        path = output / name
        frame.to_csv(path, index=False, float_format="%.12g")
        files[name] = {
            "rows": len(frame), "components": int(frame.component_id.nunique()) if "component_id" in frame else None,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }

    for split in ("train", "calibration", "test"):
        batch_ids = set(dataset.batch_splits.loc[dataset.batch_splits.split == split, "batch_id"])
        readings = dataset.readings[dataset.readings.batch_id.isin(batch_ids)]
        labels = dataset.labels[dataset.labels.batch_id.isin(batch_ids)]
        save(f"{split}_readings.csv", readings)
        save(f"{split}_early.csv", readings[readings.hours.isin((0, 24))])
        save(f"{split}_labels.csv", labels)
    save("batch_splits.csv", dataset.batch_splits)
    test_batches = dataset.batch_splits[dataset.batch_splits.split == "test"]
    demo_batches = test_batches.sort_values("batch_id").groupby("profile_id", sort=True).head(1).batch_id.tolist()
    demo = dataset.readings[dataset.readings.batch_id.isin(demo_batches)]
    save("demo_early.csv", demo[demo.hours.isin((0, 24))])
    # Late measurements remain a separate reveal file, not part of early input.
    save("demo_outcomes.csv", demo[demo.hours > 24])
    save("demo_labels.csv", dataset.labels[dataset.labels.batch_id.isin(demo_batches)])

    stress_counts: dict[str, object] = {}
    if include_stress:
        for offset, name, prevalence, fault_rate in (
            (101, "low_prevalence", 0.005, 0.05),
            (202, "unseen_condition", dataset.configured_defect_prevalence, 0.45),
        ):
            stress = generate_mlcc_dataset(
                seed=dataset.seed + offset, n_batches=20, components_per_batch=100,
                defect_prevalence=prevalence, tester_fault_batch_rate=fault_rate,
                condition=name, identity_prefix=f"MLCC_{name.upper()}",
            )
            save(f"stress_{name}_readings.csv", stress.readings)
            save(f"stress_{name}_early.csv", stress.readings[stress.readings.hours.isin((0, 24))])
            save(f"stress_{name}_labels.csv", stress.labels)
            stress_counts[name] = {
                "seed": stress.seed, "components": len(stress.labels),
                "configured_mechanism_prevalence": prevalence,
                "actual_final_latent_exceedances": int(stress.labels.is_future_failure.sum()),
                "use": "Evaluation only; never threshold/model selection or training",
            }

    manifest: dict[str, object] = {
        "generator_version": VERSION, "seed": dataset.seed, "data_source": "synthetic",
        "is_synthetic": True, "physical_validation": False,
        "provenance": "Generated entirely from explicitly fictional assumptions; no Kaggle/NASA/manufacturer rows copied or augmented.",
        "condition": dataset.condition, "hours": list(HOURS), "early_hours": [0, 24], "target_hours": 168,
        "components": len(dataset.labels), "readings": len(dataset.readings),
        "batches": len(dataset.batch_splits), "profiles": [asdict(p) for p in PROFILES],
        "configured_mechanism_prevalence": dataset.configured_defect_prevalence,
        "actual_final_latent_exceedances": int(dataset.labels.is_future_failure.sum()),
        "scenario_counts": {str(k): int(v) for k, v in dataset.labels.scenario.value_counts().items()},
        "split_policy": "60/20/20 whole batches, stratified by fictional profile. Profiles appear in every split. IDs never model features.",
        "split_batches": {str(k): int(v) for k, v in dataset.batch_splits.split.value_counts().items()},
        "demo_batch_ids": demo_batches,
        "demo_selection": "First test batch by batch ID for each profile; selection independent of labels and predictions. Demo is part of test, not an independent benchmark.",
        "label_definitions": {
            "final_value": "Observed leakage at 168h including measurement noise and any tester fault; forecasting regression target.",
            "true_final_value": "Latent component leakage at 168h before measurement noise/tester error; privileged simulator truth.",
            "is_future_failure": "true_final_value > fictional upper_limit at168h. Does not mean actual device failure or qualified reject.",
            "is_observed_final_exceedance": "final_value > fictional upper_limit at168h; may reflect tester error.",
            "is_defect": "A simulated physical degradation mechanism was assigned, including subthreshold cases; differs from final failure.",
            "is_tester_fault": "Component measured on a channel with a shared additive instrument fault; may coexist with physical degradation.",
            "scenario": "Physical scenario, except otherwise-healthy channel-affected parts are shown as tester_channel_fault.",
            "component_scenario": "Original physical scenario before any independent instrument fault.",
            "ever_latent_exceedance": "Latent leakage exceeds limit at any sampled time; intermittent events may recover by168h.",
        },
        "assumptions_and_limits": [
            "Illustrative stress/measurement relationships, not validated material physics; all part numbers, distributions and acceptance limits fictional.",
            "Stress temperature and applied voltage differ from measurement temperature and measurement voltage; values include their units in field names except temperature_c (stress).",
            "Insulation resistance is DERIVED from the same measured leakage and measurement voltage: R_Gohm = V/(I_uA*1000); it is not independent evidence.",
            "Capacitance and dissipation are overlapping, noisy auxiliary signals. Units nF and percent respectively.",
            "Moisture-associated history is an illustrative association, not a ground-truthed diagnosis of moisture damage; storage humidity is not hot-chamber humidity.",
            "Healthy settling can decrease leakage. Noise and intermittent behavior mean trajectories need not be monotone.",
            "Late abrupt events after24h may be unpredictable from0h/24h; report this limitation rather than manipulating examples.",
            "Development prevalence is deliberately enriched. Low-prevalence stress data tests false-alert burden but cannot estimate real industrial performance.",
            "Unseen conditions change measurement temperature to40–45C, stress temperature100–110C and voltage ratio0.60–0.70; this is a distribution-shift check.",
            "No time after24h, labels, scenario, true_final_value or final_value may enter early predictive features. Labels can only supply training targets and evaluation truth.",
            "Claims of accuracy apply only to this synthetic generator; independent measured batches are required for real-world validation.",
        ],
        "reading_columns": dataset.readings.columns.tolist(), "label_columns": dataset.labels.columns.tolist(),
        "stress_datasets": stress_counts, "files": files,
    }
    (output / "generation_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest
