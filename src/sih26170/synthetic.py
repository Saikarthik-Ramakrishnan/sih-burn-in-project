"""Reproducible, physics-guided synthetic burn-in data for evaluation only.

Every row produced by this module is synthetic. Rows carry
``data_source == "synthetic"`` and ``is_synthetic == True`` so synthetic
material can never be mistaken for measured hardware data.

Physical picture
----------------
Burn-in stresses a population of nominally identical parts at an elevated
temperature. Three effects shape the healthy population:

* part-to-part spread - initial values are log-normal around a family nominal;
* chamber temperature - each batch sits at a slightly different setpoint and an
  Arrhenius factor (``Ea = 0.7 eV``) turns that offset into a batch-level scale
  change. This is the reason a component must be compared with its own batch
  rather than with a global threshold;
* early-life settling - healthy parts move a little and then plateau.

Defect scenarios add a degradation term on top of that healthy trajectory. The
tester-fault scenario instead corrupts the *measurement* of an otherwise
healthy part, which is why it is labelled separately from component defects.

Nothing here claims to reproduce a specific failure mechanism of a specific
device. The generator exists so that detection behaviour can be measured
against known ground truth.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import numpy as np
import pandas as pd

GENERATOR_VERSION = "1.0.0"
SYNTHETIC_DATA_SOURCE = "synthetic"
SYNTHETIC_MARKER_COLUMN = "is_synthetic"

BOLTZMANN_EV_PER_K = 8.617333262e-5
ACTIVATION_ENERGY_EV = 0.7
REFERENCE_TEMPERATURE_C = 125.0

DEFAULT_HOURS: tuple[float, ...] = (0.0, 6.0, 12.0, 24.0, 48.0, 72.0, 96.0, 120.0, 144.0, 168.0)

HEALTHY_SCENARIOS: tuple[str, ...] = ("healthy_stable", "ordinary_noise")
DEFECT_SCENARIOS: tuple[str, ...] = (
    "gradual_drift",
    "accelerating_drift",
    "sudden_step",
    "intermittent",
)
FAULT_SCENARIOS: tuple[str, ...] = ("tester_fault",)
SCENARIOS: tuple[str, ...] = HEALTHY_SCENARIOS + DEFECT_SCENARIOS + FAULT_SCENARIOS

_HEALTHY_RATIOS = {"healthy_stable": 50.0, "ordinary_noise": 22.0}
_DEFECT_RATIOS = {
    "gradual_drift": 8.0,
    "accelerating_drift": 7.0,
    "sudden_step": 5.0,
    "intermittent": 4.0,
}

LABEL_COLUMNS = [
    "component_id",
    "batch_id",
    "component_family",
    "measurement_name",
    "scenario",
    "is_defect",
    "is_tester_fault",
    "is_healthy",
    "anomaly_onset_hour",
    "first_exceedance_hour",
    "final_value",
    "upper_limit",
    "batch_temperature_c",
    "is_synthetic",
]


@dataclass(frozen=True)
class FamilySpec:
    """Population parameters for one comparable component family."""

    component_family: str
    measurement_name: str
    nominal_value: float
    upper_limit: float
    unit_spread: float = 0.08
    settle_fraction: float = 0.05
    settle_tau_hours: float = 12.0
    noise_fraction: float = 0.02

    def __post_init__(self) -> None:
        if self.nominal_value <= 0:
            raise ValueError("nominal_value must be positive")
        if self.upper_limit <= self.nominal_value:
            raise ValueError("upper_limit must sit above the family nominal value")
        if self.unit_spread <= 0 or self.noise_fraction < 0:
            raise ValueError("unit_spread must be positive and noise_fraction non-negative")


DEFAULT_FAMILIES: tuple[FamilySpec, ...] = (
    FamilySpec(
        component_family="Digital IC",
        measurement_name="leakage_ua",
        nominal_value=10.0,
        upper_limit=50.0,
    ),
    FamilySpec(
        component_family="Power MOSFET",
        measurement_name="rds_on_mohm",
        nominal_value=45.0,
        upper_limit=120.0,
        unit_spread=0.05,
        settle_fraction=0.02,
        settle_tau_hours=18.0,
        noise_fraction=0.015,
    ),
)


@dataclass(frozen=True)
class SyntheticDataset:
    """Synthetic readings plus the ground-truth labels that generated them.

    ``readings`` matches the public input contract and deliberately carries no
    scenario label, so a label can never reach a feature by accident.
    """

    readings: pd.DataFrame
    labels: pd.DataFrame
    seed: int
    hours: tuple[float, ...]
    generator_version: str = GENERATOR_VERSION

    @property
    def batch_ids(self) -> list[str]:
        return sorted(self.readings["batch_id"].unique().tolist())

    @property
    def horizon_hours(self) -> float:
        return float(max(self.hours))

    def scenario_counts(self) -> pd.Series:
        return self.labels["scenario"].value_counts().sort_index()


def arrhenius_acceleration(
    temperature_c: float,
    *,
    reference_temperature_c: float = REFERENCE_TEMPERATURE_C,
    activation_energy_ev: float = ACTIVATION_ENERGY_EV,
) -> float:
    """Return the Arrhenius rate ratio between two burn-in temperatures."""

    kelvin = float(temperature_c) + 273.15
    reference_kelvin = float(reference_temperature_c) + 273.15
    if kelvin <= 0 or reference_kelvin <= 0:
        raise ValueError("temperatures must be above absolute zero")
    exponent = (activation_energy_ev / BOLTZMANN_EV_PER_K) * (
        1.0 / reference_kelvin - 1.0 / kelvin
    )
    return float(np.exp(exponent))


def scenario_weights(
    *, defect_prevalence: float = 0.24, tester_fault_rate: float = 0.04
) -> dict[str, float]:
    """Return scenario weights for a chosen defect prevalence.

    Real burn-in defect rates are far below the values used here. A high
    prevalence keeps the evaluation statistically stable; it also inflates
    precision, which is stated in ``docs/evaluation_notes.md``.
    """

    if not 0.0 < defect_prevalence < 1.0:
        raise ValueError("defect_prevalence must sit strictly between 0 and 1")
    if not 0.0 <= tester_fault_rate < 1.0:
        raise ValueError("tester_fault_rate must sit in [0, 1)")
    healthy_share = 1.0 - defect_prevalence - tester_fault_rate
    if healthy_share <= 0.0:
        raise ValueError("defect_prevalence and tester_fault_rate leave no healthy parts")

    weights: dict[str, float] = {}
    defect_total = sum(_DEFECT_RATIOS.values())
    for name, ratio in _DEFECT_RATIOS.items():
        weights[name] = defect_prevalence * ratio / defect_total
    healthy_total = sum(_HEALTHY_RATIOS.values())
    for name, ratio in _HEALTHY_RATIOS.items():
        weights[name] = healthy_share * ratio / healthy_total
    weights["tester_fault"] = tester_fault_rate
    return weights


DEFAULT_SCENARIO_WEIGHTS: dict[str, float] = scenario_weights()


def _allocate_counts(weights: Mapping[str, float], n: int) -> dict[str, int]:
    """Split ``n`` components across scenarios by largest remainder."""

    names = sorted(weights)
    raw = np.array([float(weights[name]) for name in names], dtype=float)
    if (raw < 0).any() or raw.sum() <= 0:
        raise ValueError("scenario weights must be non-negative and not all zero")
    expected = raw / raw.sum() * n
    counts = np.floor(expected).astype(int)
    remainder = int(n - counts.sum())
    order = np.argsort(-(expected - counts), kind="stable")
    for position in range(remainder):
        counts[order[position]] += 1
    return {name: int(count) for name, count in zip(names, counts)}


def _healthy_baseline(hours: np.ndarray, family: FamilySpec, initial_value: float) -> np.ndarray:
    settling = 1.0 + family.settle_fraction * (
        1.0 - np.exp(-hours / family.settle_tau_hours)
    )
    return initial_value * settling


def _simulate_component(
    rng: np.random.Generator,
    *,
    family: FamilySpec,
    hours: np.ndarray,
    acceleration: float,
    scenario: str,
) -> tuple[np.ndarray, float]:
    """Return the measured trajectory and the hour the abnormality begins."""

    initial_value = (
        family.nominal_value * float(rng.lognormal(0.0, family.unit_spread)) * acceleration
    )
    baseline = _healthy_baseline(hours, family, initial_value)
    values = baseline.copy()
    noise_fraction = family.noise_fraction
    onset_hour = float("nan")
    horizon = float(hours[-1])
    interior_hours = hours[1:-1] if len(hours) > 2 else hours[1:]

    if scenario == "healthy_stable":
        pass
    elif scenario == "ordinary_noise":
        noise_fraction = family.noise_fraction * 3.0
    elif scenario in {"gradual_drift", "accelerating_drift"}:
        if scenario == "gradual_drift":
            end_multiple = float(rng.uniform(0.95, 1.4))
            power = float(rng.uniform(0.95, 1.1))
        else:
            end_multiple = float(rng.uniform(1.0, 1.6))
            power = float(rng.uniform(1.8, 3.0))
        amplitude = (family.upper_limit * end_multiple - float(baseline[-1])) * acceleration
        values = baseline + amplitude * (hours / horizon) ** power
        onset_hour = 0.0
    elif scenario == "sudden_step":
        step_hour = float(rng.choice(interior_hours))
        step = family.upper_limit * float(rng.uniform(0.35, 1.2)) * acceleration
        values = baseline + step * (hours >= step_hour)
        onset_hour = step_hour
    elif scenario == "intermittent":
        noise_fraction = family.noise_fraction * 2.0
        candidates = hours[1:]
        spike_count = int(rng.integers(1, 4))
        spike_count = min(spike_count, len(candidates))
        spike_hours = rng.choice(candidates, size=spike_count, replace=False)
        for spike_hour in spike_hours:
            magnitude = family.upper_limit * float(rng.uniform(0.3, 1.1)) * acceleration
            values = values + magnitude * (hours == spike_hour)
        onset_hour = float(np.min(spike_hours))
    elif scenario == "tester_fault":
        onset_hour = float(rng.choice(hours[1:]))
    else:  # pragma: no cover - guarded by the caller
        raise ValueError(f"unknown scenario: {scenario}")

    measurement_noise = rng.normal(0.0, noise_fraction, size=hours.shape) * np.maximum(
        baseline, 1e-9
    )
    values = values + measurement_noise

    if scenario == "tester_fault":
        values = _apply_tester_fault(rng, values=values, hours=hours, fault_hour=onset_hour, family=family)

    floor = family.nominal_value * 1e-3
    return np.maximum(values, floor), onset_hour


def _apply_tester_fault(
    rng: np.random.Generator,
    *,
    values: np.ndarray,
    hours: np.ndarray,
    fault_hour: float,
    family: FamilySpec,
) -> np.ndarray:
    """Corrupt the measurement of a healthy part from ``fault_hour`` onwards."""

    corrupted = values.copy()
    faulty = hours >= fault_hour
    mode = str(rng.choice(("stuck", "gain_offset", "dropout")))
    if mode == "stuck":
        corrupted[faulty] = float(corrupted[faulty][0])
    elif mode == "gain_offset":
        if bool(rng.integers(0, 2)):
            gain = float(rng.uniform(1.25, 1.8))
        else:
            gain = float(rng.uniform(0.45, 0.75))
        corrupted[faulty] = corrupted[faulty] * gain + family.upper_limit * 0.02
    else:
        corrupted[faulty] = family.nominal_value * 0.02
    return corrupted


def _first_exceedance_hour(hours: np.ndarray, values: np.ndarray, upper_limit: float) -> float:
    crossed = np.flatnonzero(values >= upper_limit)
    if crossed.size == 0:
        return float("nan")
    return float(hours[crossed[0]])


def generate_burn_in_dataset(
    *,
    seed: int = 26170,
    n_batches: int = 6,
    components_per_batch: int = 40,
    hours: Sequence[float] = DEFAULT_HOURS,
    families: Sequence[FamilySpec] = DEFAULT_FAMILIES,
    weights: Mapping[str, float] | None = None,
    temperature_spread_c: float = 2.5,
) -> SyntheticDataset:
    """Generate labelled synthetic burn-in readings for several batches.

    The same ``seed`` always returns identical readings and labels. Batches are
    seeded independently, so adding a batch never changes an existing one.
    """

    if n_batches < 1 or components_per_batch < 1:
        raise ValueError("n_batches and components_per_batch must be positive")
    if len(families) < 1:
        raise ValueError("at least one component family is required")
    hour_grid = np.asarray(sorted(float(hour) for hour in hours), dtype=float)
    if hour_grid.size < 2:
        raise ValueError("at least two measurement hours are required")
    if hour_grid[0] < 0:
        raise ValueError("hours cannot be negative")
    if len(np.unique(hour_grid)) != hour_grid.size:
        raise ValueError("measurement hours must be unique")

    active_weights = dict(DEFAULT_SCENARIO_WEIGHTS if weights is None else weights)
    unknown = sorted(set(active_weights).difference(SCENARIOS))
    if unknown:
        raise ValueError(f"unknown scenarios in weights: {', '.join(unknown)}")

    root = np.random.SeedSequence(seed)
    setup_seed, *batch_seeds = root.spawn(n_batches + 1)
    setup_rng = np.random.default_rng(setup_seed)
    temperature_offsets = np.round(
        setup_rng.uniform(-temperature_spread_c, temperature_spread_c, size=n_batches), 1
    )

    reading_rows: list[dict[str, object]] = []
    label_rows: list[dict[str, object]] = []

    for batch_index in range(n_batches):
        batch_id = f"B{batch_index + 1:02d}"
        family = families[batch_index % len(families)]
        batch_temperature = REFERENCE_TEMPERATURE_C + float(temperature_offsets[batch_index])
        acceleration = arrhenius_acceleration(batch_temperature)
        rng = np.random.default_rng(batch_seeds[batch_index])

        counts = _allocate_counts(active_weights, components_per_batch)
        assigned = np.array(
            [name for name in sorted(counts) for _ in range(counts[name])], dtype=object
        )
        rng.shuffle(assigned)

        for position, scenario in enumerate(assigned, start=1):
            component_id = f"{batch_id}-C{position:03d}"
            values, onset_hour = _simulate_component(
                rng,
                family=family,
                hours=hour_grid,
                acceleration=acceleration,
                scenario=str(scenario),
            )
            temperatures = batch_temperature + rng.normal(0.0, 0.3, size=hour_grid.shape)
            humidity = 15.0 + rng.normal(0.0, 1.5, size=hour_grid.shape)

            for hour, value, temperature, humidity_value in zip(
                hour_grid, values, temperatures, humidity
            ):
                reading_rows.append(
                    {
                        "component_id": component_id,
                        "batch_id": batch_id,
                        "component_family": family.component_family,
                        "hours": float(hour),
                        "measurement_name": family.measurement_name,
                        "measurement_value": float(value),
                        "upper_limit": float(family.upper_limit),
                        "temperature_c": float(temperature),
                        "humidity_pct": float(humidity_value),
                        "test_condition": "dynamic_burn_in",
                        "data_source": SYNTHETIC_DATA_SOURCE,
                        SYNTHETIC_MARKER_COLUMN: True,
                    }
                )

            label_rows.append(
                {
                    "component_id": component_id,
                    "batch_id": batch_id,
                    "component_family": family.component_family,
                    "measurement_name": family.measurement_name,
                    "scenario": str(scenario),
                    "is_defect": str(scenario) in DEFECT_SCENARIOS,
                    "is_tester_fault": str(scenario) in FAULT_SCENARIOS,
                    "is_healthy": str(scenario) in HEALTHY_SCENARIOS,
                    "anomaly_onset_hour": float(onset_hour),
                    "first_exceedance_hour": _first_exceedance_hour(
                        hour_grid, values, family.upper_limit
                    ),
                    "final_value": float(values[-1]),
                    "upper_limit": float(family.upper_limit),
                    "batch_temperature_c": batch_temperature,
                    "is_synthetic": True,
                }
            )

    readings = pd.DataFrame(reading_rows)
    labels = pd.DataFrame(label_rows)[LABEL_COLUMNS]
    return SyntheticDataset(
        readings=readings,
        labels=labels,
        seed=seed,
        hours=tuple(float(hour) for hour in hour_grid),
    )
