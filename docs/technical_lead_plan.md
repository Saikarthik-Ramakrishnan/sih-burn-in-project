# Technical-lead execution plan

## Goal

Build a defensible early-warning engine that finds unusual component behaviour
before a fixed burn-in limit is crossed. It must remain understandable to a
quality engineer and must not claim that an anomaly proves a physical cause.

## Locked architecture

1. Validate long-format readings.
2. Select only observations at or before the requested early-warning hour.
3. Build component features: change, percentage change, slope, acceleration,
   variability, limit margin, and batch-relative robust deviations.
4. Run a median/MAD benchmark.
5. Run Isolation Forest over the component feature table.
6. Combine both signals and generate plain-language reason codes.
7. Accept the separate future-value prediction result.
8. Recommend accept, monitor, retest, or engineer review.

## Interfaces that are now stable

- Input schema: documented in the project README and enforced by
  `validate_readings()`.
- Early features: `build_component_features(readings, as_of_hour=...)`.
- Anomaly model: `BatchAwareAnomalyDetector.fit()` and `.score()`.
- Dashboard output: `AnomalyResult.to_dict()`.
- Prediction hand-off: `PredictionResult`.
- Combined recommendation: `recommend_action()`.

## Next implementation milestones

### Milestone 1 — evaluation harness — completed

- Generates several batches with labelled synthetic scenarios.
- Splits complete batches rather than individual rows.
- Compares fixed limit, robust baseline, Isolation Forest, and combined model.
- Reports defect recall, false-negative rate, false-positive rate, and lead time.
- Repeats five held-out-batch splits and measures performance as evidence grows.

### Milestone 2 — prediction integration — interface completed

- Connects Ashvitha's 168-hour prediction through `PredictionResult` and
  `build_screening_record()`; the trained predictor remains her module.
- Check prediction-interval coverage.
- Tests the four decisions on controlled scenarios.

### Milestone 3 — dashboard integration

- Export a list of `AnomalyResult` dictionaries.
- Display component trajectory, batch norm, score, reason, and recommendation.
- Clearly label all synthetic demonstrations.

### Milestone 4 — validation and nomination demo

- Freeze a held-out set of complete batches.
- Record model parameters and random seed.
- Demonstrate one component that the fixed threshold passes but the proposed
  approach flags before 168 hours.
- State limitations and avoid invented aerospace-performance claims.

## Definition of done for the anomaly module

- A future reading cannot influence an early-warning feature.
- Components are compared only with the same batch, family, and measurement.
- A simple baseline is always reported alongside the ML result.
- Every flag has at least one understandable reason.
- Synthetic defect scenarios are detected on held-out batches.
- False negatives and false positives are both visible.
