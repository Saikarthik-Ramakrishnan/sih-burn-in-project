# Evaluation notes

See also [`evaluation_notes_harness.md`](evaluation_notes_harness.md) for the
independent stress-testing harness: batch-split leakage guards, the screening
hour ladder and lead-time analysis, the parameter sweep, and the interface
issues those measurements exposed.

## What was evaluated

The reference run uses generator seed `26170`, 12 synthetic batches, 60
components per batch, ten measurement times from 0 to 168 hours, and two
component families. Eight complete batches train the unsupervised model and
four complete batches are held out for testing. The 24-hour test therefore
contains 240 components. Scenario labels and future outcomes are stored in a
separate label table and are joined only after scoring.

The methods are:

1. fixed approved upper limit;
2. batch median plus median absolute deviation;
3. Isolation Forest on unit-normalized and batch-relative features;
4. the union of robust and Isolation Forest flags.

No Bayesian optimisation was used. The robust threshold is 3.5 and Isolation
Forest contamination is 0.1. These are recorded with random seeds in
`outputs/evaluation_24h/run_metadata.json`.

## Meaning of the metrics

- **Review recall** treats simulated component defects and simulated tester
  faults as cases that should be surfaced for review. It deliberately includes
  defects that may not yet be observable at the selected hour.
- **Defect recall** covers simulated component defects only.
- **Tester-fault recall** is reported separately so corrupted measurements are
  never presented as physical component failures.
- **Future-failure recall** covers only component defects that eventually cross
  their upper limit. Tester faults cannot count as component failures.
- **False-positive rate** uses genuinely healthy simulated components.
- **Early-warning lead time** is reported only for correctly flagged component
  defects whose first limit crossing happens after the scoring hour.
- **Started-anomaly recall** uses the simulated mechanism onset. A mechanism
  having started does not guarantee that its signal is practically observable.

## Reference 24-hour results

On the fixed reference split, the combined detector achieved 44.1% review
recall, 50.0% future-failure recall, a 1.16% false-positive rate, and 93.8%
precision. The median lead time among correctly identified future failures was
96 hours. Fixed-limit screening achieved only 4.4% review recall and 5.6%
future-failure recall at this early checkpoint, with no genuine early-warning
lead-time value because it only flagged readings that had already reached the
limit.

Across five held-out-batch splits, combined review recall was 44.4% ± 4.5
percentage points, future-failure recall was 49.6% ± 4.3 points, and the mean
false-positive rate was 0.70%. The robust baseline alone reached 42.1% review
recall, while Isolation Forest reached 38.5%. This is important: the current
synthetic problem does not justify claiming that ML dramatically beats robust
statistics. The value of the combined design is complementary detection and a
clear benchmark, not an invented superiority claim.

## What the time sweep shows

The combined detector's fixed-split review recall increased from 30.9% at 6
hours to 44.1% at 24 hours, 57.4% at 48 hours, 79.4% at 72 hours, and 85.3% at
96 hours. The corresponding false-positive rate fell from 6.98% at 6 hours to
1.16% at 24 hours and zero in this particular held-out set from 48 hours onward.

Accelerating degradation is intentionally hard at 24 hours because its early
quadratic change can resemble normal variation. The anomaly model detects it
much more reliably after additional measurements. Ashvitha's future-value
predictor is intended to address this gap; its value must be evaluated on held-
out batches rather than assumed.

## Claims that must not be made

- These figures are not measured aerospace performance.
- Synthetic precision is inflated by the deliberately high defect prevalence.
- A trajectory does not prove moisture ingress, thermal overstress, or another
  physical cause without trustworthy cause labels or failure analysis.
- The software is decision support and does not automatically certify or reject
  a real component.
- Results from one random split must not be quoted without the repeated-split
  uncertainty beside them.

## Files produced by the reference run

- `metrics.csv`: fixed-split method comparison;
- `scenario_metrics.csv`: flag rate for each simulated scenario;
- `scored_components.csv`: auditable component-level results;
- `time_sweep_metrics.csv`: performance as measurements accumulate;
- `repeated_split_metrics.csv`: all five held-out-batch runs;
- `repeated_split_summary.csv`: mean and sample standard deviation;
- `run_metadata.json`: seeds, thresholds, split and synthetic-data warning.

