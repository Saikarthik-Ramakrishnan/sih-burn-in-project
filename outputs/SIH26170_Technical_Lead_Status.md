# SIH26170 technical-lead milestone status

Date: 4 September 2026

## Outcome

The anomaly-detection foundation and its evaluation harness are executable and
tested. This milestone does not claim that the complete SIH product is ready;
the trained 168-hour prediction model, final dashboard, and validation on real
or authoritative data remain separate workstreams.

## Implemented

- Long-format measurement contract and strict input validation
- Early-window feature engineering with future-data leakage prevention
- Unit-normalized change, slope, acceleration, variability, and limit margin
- Batch/family/measurement-relative robust deviation features
- Median/MAD benchmark
- Isolation Forest detector and calibrated presentation score
- Combined robust + Isolation Forest flag
- Plain-language reason codes
- Prediction-result contract and dashboard-ready combined screening record
- Reproducible multi-batch synthetic generator
- Separate ground-truth labels that never enter model inputs
- Whole-batch train/test splitting
- Fixed-limit, robust, Isolation Forest, and combined comparisons
- Failure-focused metrics, scenario breakdown, time sweep, and five repeated
  held-out-batch splits

## Verification

- 18 automated tests pass.
- Package dependencies are internally consistent.
- All source, test, and example files compile.
- An adversarial regression test changes every measurement after 24 hours by
  100× and confirms that 24-hour features, scores, and flags remain identical.
- Raw-unit measurements and ground-truth labels are explicitly excluded from
  the Isolation Forest feature list.
- Tester faults can require review but cannot count as physical component
  failures in future-failure recall.

## Reference synthetic result at 24 hours

The reference test holds out four complete batches containing 240 components.

| Method | Review recall | False-positive rate | Future-failure recall | Precision |
|---|---:|---:|---:|---:|
| Fixed limit | 4.4% | 0.00% | 5.6% | 100.0% |
| Robust MAD | 42.6% | 0.58% | 50.0% | 96.7% |
| Isolation Forest | 41.2% | 1.16% | 46.3% | 93.3% |
| Combined | 44.1% | 1.16% | 50.0% | 93.8% |

The combined method provided a median 96-hour lead among correctly identified
future component failures. Across five held-out-batch splits, combined review
recall was 44.4% ± 4.5 percentage points and its mean false-positive rate was
0.70%.

These are synthetic test-harness results, not aerospace performance claims.
The simulated defect prevalence is intentionally high and therefore inflates
precision compared with a realistic rare-defect population.

## Main technical interpretation

The fixed limit is ineffective as an early-warning mechanism. Robust batch
statistics provide most of the current 24-hour detection value. Isolation
Forest adds complementary flags but does not yet justify a claim of dramatic ML
superiority. Accelerating degradation remains difficult at 24 hours because
very early curvature resembles normal variation. The future-value predictor
must demonstrate improvement on this group using held-out batches.

## Next integration gates

1. Ashvitha returns predictions through `PredictionResult`, including lower and
   upper uncertainty bounds.
2. Evaluate the predictor on complete held-out batches using MAE, failure recall
   and prediction-interval coverage.
3. Compare anomaly-only recommendations with anomaly + prediction decisions.
4. Connect `build_screening_record()` to the Streamlit dashboard.
5. Replace or supplement synthetic data with authoritative sample data when it
   becomes available, while keeping sources visibly separated.

