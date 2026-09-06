# Evaluation notes — stress-testing harness

Companion to [`evaluation_notes.md`](evaluation_notes.md). That document covers
the reference run and repeated-split uncertainty. This one covers the
independent stress-testing harness in `src/sih26170/evaluation_harness.py`,
the batch-split leakage guards in `src/sih26170/splitting.py`, the hour ladder
and lead-time analysis, the parameter sweep, and the interface issues the
measurements exposed.

Every number here comes from **synthetic data**. It measures how the detector
behaves against known ground truth. It is not evidence about any physical
component and it is not qualification data. The software recommends `ACCEPT`,
`MONITOR`, `RETEST` or `ENGINEER_REVIEW`; it never certifies or rejects a real
component. A qualified engineer does.

## Reproducing these numbers

```bash
.venv/bin/pytest
.venv/bin/python examples/run_evaluation_harness_demo.py --output-dir outputs/evaluation
```

Fixed run: seed `26170`, 8 batches x 50 components = 400 components, 10
measurement hours to 168 h. Training batches `B02, B03, B06, B07`; held-out
batches `B01, B04, B05, B08` (200 components: 48 defects, 144 healthy, 8 tester
faults). Detector defaults: `contamination=0.1`, `robust_threshold=3.5`,
`random_state=42`, one Isolation Forest per component family.

This is a different split and a smaller population than the reference run in
`evaluation_notes.md`, and the metric populations differ (see *Metrics*), so
the two documents' percentages are not directly comparable.

## Assumptions

**Generator.** `src/sih26170/synthetic.py`. Healthy parts start log-normal
around a family nominal and settle towards a plateau. Each batch sits at its
own chamber temperature, and an Arrhenius factor (`Ea = 0.7 eV`) turns that
offset into a batch-level scale change of roughly +-13%. That is precisely why
a component is compared with its own batch rather than a global threshold.
Two families: `Digital IC / leakage_ua` (limit 50) and
`Power MOSFET / rds_on_mohm` (limit 120).

**Scenarios.** `healthy_stable`, `ordinary_noise` (healthy, three times
noisier), `gradual_drift`, `accelerating_drift`, `sudden_step`, `intermittent`,
`tester_fault`.

**Labelling.** A defect is a component whose *physics* is wrong:
`gradual_drift`, `accelerating_drift`, `sudden_step`, `intermittent`. A
`tester_fault` corrupts the *measurement* of a healthy part (stuck reading,
gain/offset miscalibration, dropout), so it is neither defective nor healthy.
It is excluded from recall and precision and reported on its own line, with
`false_positive_rate_incl_tester_faults` giving the pessimistic reading.

**Prevalence.** 24% defects and 4% tester faults. Real burn-in defect rates are
orders of magnitude lower. This keeps the metrics statistically stable and
**inflates precision**; see the last section.

**Marking.** Every generated row carries `data_source="synthetic"` and
`is_synthetic=True`. Scenario labels live only in `dataset.labels`, never in
`dataset.readings`, so a label cannot reach a feature by accident.

## Split and leakage guards

`src/sih26170/splitting.py` assigns **whole batches**, stratified by family so
an evaluation family always has a training counterpart. Three properties are
tested directly in `tests/test_splitting.py`:

1. no batch and no component appears on both sides of the split;
2. multiplying every observation after `as_of_hour` by 1e6 leaves the feature
   table bit-identical, so a future reading cannot enter an early-warning
   feature;
3. features built for the held-out batches alone equal the same rows built from
   the whole dataset, so batch-relative statistics never borrow from another
   batch.

`tests/test_evaluation_harness.py` adds the model-side check: deleting a whole
held-out batch does not move the scores of the remaining held-out batches.

## Metrics

Reported: **defect recall**, **false-negative rate**, **false-positive rate**,
**precision** and **early-warning lead time**. Ordinary accuracy is not
computed anywhere. At 24% prevalence a screen that flags nothing already scores
76% accuracy while missing every defect.

Recall here counts **component defects only**, over the 48 held-out defects.
`evaluation_notes.md` also reports a wider "review recall" that includes tester
faults as cases to surface. Both are defensible; they are simply different
denominators, which is most of why the two documents' figures differ.

Lead time has two forms, both measured against the hour the component
*actually* first crosses its approved limit:

* single-hour tables: `first_exceedance_hour - as_of_hour`, over defects the
  method caught before that crossing;
* the hour ladder: `first_exceedance_hour - first_flag_hour`, the warning the
  method would really have bought.

## Results at hour 24

| Method | Recall | FNR | FPR | Precision | Early warnings | Median lead |
|---|---|---|---|---|---|---|
| Fixed upper limit | 0.083 | 0.917 | 0.000 | 1.000 | **0** | n/a |
| Median/MAD (repository rule) | 0.458 | 0.542 | 0.000 | 1.000 | 14 | 108 h |
| Isolation Forest | 0.438 | 0.562 | 0.000 | 1.000 | 13 | 96 h |
| Combined (existing detector) | 0.458 | 0.542 | 0.000 | 1.000 | 14 | 108 h |
| Median/MAD, textbook scale | 0.521 | 0.479 | 0.021 | 0.893 | 15 | 96 h |

The fixed limit produces **zero early warnings, by construction**: it can only
fire once the value has already crossed the limit, so its lead time can never
be positive. That is the clearest single argument for a batch-relative screen,
and it holds without any appeal to machine learning.

Flag rate per scenario at hour 24 — recall for defects, false-alarm rate for
healthy parts, data-quality catch rate for tester faults:

| Scenario | n | Fixed limit | Robust | Isolation Forest | Combined |
|---|---|---|---|---|---|
| healthy_stable | 100 | 0.000 | 0.000 | 0.000 | 0.000 |
| ordinary_noise | 44 | 0.000 | 0.000 | 0.000 | 0.000 |
| gradual_drift | 16 | 0.000 | 0.875 | 0.812 | 0.875 |
| accelerating_drift | 12 | 0.000 | 0.000 | 0.000 | 0.000 |
| sudden_step | 12 | 0.167 | 0.333 | 0.333 | 0.333 |
| intermittent | 8 | 0.250 | 0.500 | 0.500 | 0.500 |
| tester_fault | 8 | 0.000 | 0.125 | 0.125 | 0.125 |

## Results over the screening ladder

Defect recall by screening hour:

| Hour | Fixed limit | Robust | Isolation Forest | Combined | Textbook MAD |
|---|---|---|---|---|---|
| 6 | 0.042 | 0.062 | 0.188 | 0.188 | 0.167 |
| 12 | 0.083 | 0.271 | 0.292 | 0.354 | 0.438 |
| 24 | 0.083 | 0.458 | 0.438 | 0.458 | 0.521 |
| 48 | 0.083 | 0.646 | 0.458 | 0.646 | 0.750 |
| 72 | 0.188 | 0.812 | 0.500 | 0.812 | 0.896 |
| 96 | 0.188 | 0.896 | 0.479 | 0.917 | 0.958 |
| 120 | 0.375 | 0.938 | 0.417 | 0.938 | 0.979 |
| 144 | 0.625 | 0.938 | 0.479 | 0.938 | 1.000 |

Detection lead time across all 48 held-out defects:

| Method | Ever flagged | Flagged before crossing | Median first flag | Median lead |
|---|---|---|---|---|
| Fixed upper limit | 37 | **0** | 120 h | n/a |
| Median/MAD (repository) | 48 | 28 | 24 h | 96 h |
| Isolation Forest | 41 | 23 | 24 h | 114 h |
| Combined | 48 | 28 | 24 h | 96 h |

Six further defects are flagged but never cross the limit within 168 h. They
are censored: not counted as early warnings, and not counted as false alarms.

## Sensitivity

A deterministic grid over `as_of_hour x contamination x robust_threshold x
fixed_limit_fraction` is written to
`outputs/evaluation/parameter_sweep.csv`. No Bayesian optimisation was used.

* `as_of_hour` dominates every other parameter. Moving the screen from 12 h to
  48 h changes combined recall from 0.354 to 0.646; no parameter change at a
  fixed hour moves it by more than 0.15.
* `contamination` acts as a flag budget, not a risk setting. At hour 24 it
  moves recall 0.458 -> 0.604 and false-positive rate 0.000 -> 0.104.
* `robust_threshold` between 2.5 and 4.5 changes recall by at most 0.06.
* A guard band matters. Screening at `0.6 x upper_limit` instead of at the
  limit turns the fixed rule from zero early warnings into a usable baseline.
  If a fixed-threshold comparison is kept in the demo, it should be a guard
  band rather than the approved limit, otherwise the comparison flatters the
  proposed method.

**Read every difference against the split noise.** The repeated-split study in
`evaluation_notes.md` puts the uncertainty on a recall figure at roughly +-4.5
percentage points. Differences below about 0.09 on a single split, including
several in the tables above, should not be treated as real.

## Failure cases

1. **Accelerating drift is invisible at 24 h.** No method flags any of the 12
   held-out accelerating drifts at hour 24; the added signal is smaller than
   the measurement noise until roughly 48-72 h. Any claim of "early warning at
   24 hours" must exclude this scenario.
2. **A step that has not happened cannot be seen.** Two thirds of the synthetic
   step faults begin after hour 24, capping recall at 0.333 there. That is a
   property of the physics, not of the model.
3. **Intermittent faults alias against the sampling grid.** Recall is 0.500,
   set largely by whether a spike lands on a sampled hour.
4. **Isolation Forest degrades as the population gets worse.** Its recall peaks
   near 0.50 at hour 72 and falls to 0.417 by hour 120: a fixed `contamination`
   keeps flagging a fixed fraction while the true anomalous fraction grows. The
   robust rule has no such behaviour, and the combined result is carried by the
   robust half at later hours.
5. **Tester faults are effectively missed.** Only 1 of 8 is flagged, and the
   recommendation layer sends 7 of 8 to `ACCEPT`. A corrupted measurement is
   currently indistinguishable from a healthy one.
6. **Precision here is not trustworthy.** See the last section.

## Findings for the main implementation

**1. The robust scale is not robust (evidence, medium confidence).**
`features._add_robust_z` sets the scale to
`max(MAD, |median| * 0.01, std * 0.1, 1e-9)`. A batch standard deviation is
inflated by exactly the outliers the rule exists to find, so the `std * 0.1`
term wins in 6 of the 8 held-out (batch, column) groups and widens the slope
scale by a median factor of **1.66x**, worst case 2.38x. Screening with a
textbook `1.4826 * MAD` scale raises recall at every hour from 12 onwards
(0.271 -> 0.438 at hour 12; 0.646 -> 0.750 at hour 48; 0.938 -> 1.000 at hour
144). It is not free: the false-positive rate rises from 0.000 to between 0.007
and 0.049 depending on the hour. This is a threshold trade rather than a pure
win, so it is the main implementation's call — but the current floor makes
sensitivity *depend on how bad the batch already is*, which is backwards.
`evaluation_harness.batch_relative_mad_z` implements the comparison, and
`robust_mad_strict` carries it through every table.

**2. `data_quality_warning` is never populated (confirmed).** No code path
sets it, so `AnomalyResult.data_quality_warning` is always `None` and the
`RETEST` branch of `recommend_action` that depends on it is unreachable. Tester
faults therefore route to `ACCEPT`. Cheap checks would cover most of the
synthetic fault modes: zero variance across a window (stuck reading), a
physically implausible value, or a discontinuity inconsistent with the rest of
the batch.

**3. `contamination` sets a flag budget, not a risk tolerance (confirmed).**
It is the parameter that moves the false-positive rate most, and it is why
Isolation Forest recall falls as the batch worsens. Consider exposing an
explicit score threshold, or fitting on a reference population believed healthy
rather than on the batch being screened.

**4. The minimum-population rule needs a documented fallback (confirmed).**
`BatchAwareAnomalyDetector.fit` requires eight reference components. Once
fitting is done per family and measurement, a small production family can fall
below that. The harness raises an error naming the family; the main
implementation should decide whether to fall back to the robust rule alone.

**5. Pooling families in one forest: measured, no change recommended.**
Fitting one Isolation Forest across both families instead of one per family
changed recall 0.438 -> 0.396 with the current limit-normalised features, and
not at all with the handoff's raw-scale features. Both differences are two
components out of 48, inside the noise of this test set. `per_family` is kept
as the conservative default, not because a penalty was demonstrated.

**6. A label column was renamed mid-flight.** `defect_onset_hour` became
`anomaly_onset_hour` in `synthetic.py`. `evaluation_harness` resolves either
name at run time. Worth settling on one before the dashboard reads it.

## What cannot be claimed from this work

* **Nothing about real components.** No detection rate, lead time or
  false-alarm rate here transfers to hardware. The generator encodes the
  failure shapes we chose to model; a real population will contain shapes it
  does not.
* **Precision and false-positive rate do not transfer.** At the 24% prevalence
  used here, precision at hour 24 is 1.000. At a realistic burn-in defect rate
  of, say, 0.1%, the same false-positive rate would put nearly every flag on a
  healthy part. Precision must be re-derived from a real prevalence before it
  is quoted anywhere.
* **No physical failure mechanism is demonstrated.** A flag says a component
  behaves unlike its batch peers. It does not identify a mechanism, and it is
  not a prediction that the part will fail.
* **No qualification or aerospace claim.** Nothing here is screening
  validation, and no result may be presented as such.
* **This is not a model selection.** Four screens were run at one set of
  defaults on one synthetic population. Choosing an operating point for real
  use needs real data, a real prevalence, and an agreed cost of a missed defect
  against a false alarm.
