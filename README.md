# SIH26170 anomaly-detection core

## MLCC prototype update — 5 September 2026

The new synthetic MLCC dataset, saved Isolation Forest/XGBoost prototype and
role-specific handoffs are described in `outputs/mlcc_v1/START_HERE.md`.
Run `scripts/score_mlcc_prototype.py` against the supplied demo CSV and model
bundle for real local inference. The earlier generic anomaly core below is
preserved. FastAPI and the frontend remain separate teammate workstreams.

This is the technical-lead portion of the SIH26170 prototype. It turns early
burn-in measurements into component-level features, compares each component
with genuinely comparable peers, and returns an explainable anomaly result.

## Current scope

- strict input validation;
- leakage-safe feature engineering up to a chosen `as_of_hour`;
- a transparent median/MAD baseline;
- an Isolation Forest model;
- plain-language reason codes;
- reproducible multi-batch synthetic scenarios kept separate from model inputs;
- held-out-batch evaluation against fixed-limit and robust baselines;
- repeated-split and time-sweep reporting;
- a decision layer that consumes Ashvitha's prediction output contract.

The prediction model, dashboard, production API, and real-world validation are
separate modules. This package does not claim that an anomaly proves a physical
failure mechanism.

## Input contract

Every row is one measurement for one component at one time.

| Column | Meaning |
|---|---|
| `component_id` | Unique component identifier |
| `batch_id` | Manufacturing/test batch |
| `component_family` | Comparable component type |
| `hours` | Hours since burn-in began |
| `measurement_name` | For example, `leakage_ua` |
| `measurement_value` | Observed value |
| `upper_limit` | Approved maximum for this measurement |

Optional columns include `lower_limit`, `temperature_c`, `humidity_pct`,
`test_condition`, and `data_source`.

## Run locally

```bash
python -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/pytest
.venv/bin/python examples/run_anomaly_demo.py
.venv/bin/python examples/run_evaluation.py
.venv/bin/python examples/run_evaluation_harness_demo.py
```

## Stable interface for teammates

```python
features = build_component_features(readings, as_of_hour=24)
detector = BatchAwareAnomalyDetector(contamination=0.1)
results = detector.fit_score(features)
```

The dashboard should consume the fields defined by `AnomalyResult.to_dict()`.
The future-value model can be connected through `PredictionResult` and
`build_screening_record()`.

## Evaluation interpretation

The generated evaluation files are synthetic test-harness results, not evidence
of aerospace performance. Complete batches are held out, scenario labels are
joined only after scoring, and readings later than `as_of_hour` cannot enter a
feature. Read `docs/evaluation_notes.md` before quoting any metric.

## Stress-testing harness

`sih26170.evaluation_harness` compares fixed-limit, median/MAD, Isolation
Forest and the existing combined detector on held-out batches, and adds a
screening-hour ladder that measures how much warning each method actually buys
before a component crosses its limit. `sih26170.splitting` holds the
batch-level split and its leakage guards.

```python
dataset = generate_burn_in_dataset(seed=26170, n_batches=8, components_per_batch=50)
split = split_batches(dataset.readings, test_fraction=0.4, random_state=7)
assert_split_is_leakage_safe(dataset.readings, split, as_of_hour=24)
report = run_holdout_evaluation(dataset, split=split)
```

Recall, false-negative rate, false-positive rate, precision and lead time are
reported; ordinary accuracy is not, because at these defect rates a screen that
flags nothing would score well on it. See `docs/evaluation_notes_harness.md`
for results, failure cases and the open interface questions.
