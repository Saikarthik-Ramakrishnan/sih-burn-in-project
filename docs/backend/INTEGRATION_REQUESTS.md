# Integration requests — backend → core

For Karthik. Updated 2026-09-05 after integrating the MLCC v1 pack. No core
source file has been modified.

---

## 0a. Resolved 2026-09-06 by the v2 integration

- **Forecast never flagged true crossings (§2).** Addressed by the `xgboost_v2`
  model: on the untouched test batches its point forecast flags 43 of 166
  observed crossings (persistence: 14, all of them parts already over the limit
  at 24 h), and the stratified upper bound now drives MONITOR with a stated
  one-sided 90 % level. The 800-part demo reveal shows 17 of 43 crossers flagged.
- **Decision on `xgboost` vs `persistence` for the demo (§2, §4).** Neither: the
  bundle's validation winner is `xgboost_v2`, so the default needs no override.
- **Newer bundle (§4).** Dropped in at `outputs/mlcc_v2/model_bundle`; the API
  verifies all four artifact checksums and the library versions at startup.
- **A1 (machine-readable unscored reasons)** and **A3 (Python version)** remain
  open on the core side; the free-text mapping still works and 3.12 vs 3.13 has
  not caused a failure.

## 0. Resolved by the snapshot

The earlier questions about `AnomalyResult` attribute names, the feature frame's
identity columns and `build_screening_record`'s return shape are **closed**. The
API no longer uses that lower-level path for MLCC; it calls `load_bundle` /
`screen_readings` as the handoff specifies, and reads `metadata`, `summary` and
`records` from the returned dict.

Also resolved: **pandas**. The manifest says the artifact was built on 3.0.5, so
the backend's earlier `pandas<3` pin is gone and the environment now matches your
lock exactly for pandas, numpy, scikit-learn, xgboost and skops.

---

## 1. Four things to confirm

**A1 — Unscored records carry their explanation in `recommendation_reasons`, not
`reason_codes`.** For an unscored record `_unscored()` sets `reason_codes: []`
and puts the text in `recommendation_reasons` and `data_quality_warning`. The API
reads `recommendation_reasons` first and falls back to `reason_codes`. Please
confirm that is intended and stable, since the API maps that text onto a stable
`reason` enum (`missing_checkpoint`, `unsupported_profile`, …) for the frontend.
Free text is a fragile thing to pattern-match on; a machine-readable code on
unscored records would make this robust.

**A2 — Unscored records get `recommendation: "RETEST"` and are counted in
`summary.recommendations`.** The API deliberately does **not** surface that:
`decision_counts` covers scored records only, and unscored ones are listed
separately. Otherwise a component that was never screened appears in the same
tally as one that was assessed and needs a retest. Flagging so we present the
same story — happy to align either way, but the UI should not merge them.

**A3 — Python version.** Your lock says 3.12; this machine runs 3.13.3. All
checksums, all library versions and the inference probe pass, and 204 tests are
green. Are you deliberately on 3.12, or can we standardise?

**A4 — Startup cost.** `load_bundle` takes ~2.1 s (`state.skops` is 9.2 MB). Paid
once at process start, so it does not affect requests. Just confirming that is
expected and not a sign of something being rebuilt at load time.

---

## 2. Observations, no change requested

- **Mixed `profile_id` within a batch raises `ValueError`** ("supply comparable
  part/test groups separately"). Correct and matches the handoff. The API turns
  it into a 422 with `row: null`, because the core reports it for the dataset as
  a whole and inventing a row number would be a lie.
- **Extrapolation disclosure is doing real work.** On the 240-component sample,
  **61 records** come back with non-empty `out_of_training_range_features`. The
  API raises this to a response-level warning. That is a quarter of the sample —
  worth knowing whether the demo dataset is expected to sit that far outside the
  training condition ranges, or whether it points at something in the generator.
- **The forecast flagged none of the true crossings on the demo slice.** With
  the outcome comparison fixed, 7 of the 240 sample components exceed their limit
  at 168 h. All 7 came back `predicted_to_cross_limit: false` — the point
  forecast never reached the limit, even for the component that ended at 1.51 uA
  against a 1.30 limit. The 4 that were caught were caught by the anomaly
  detector alone. Two thoughts: (a) `persistence` predicting the 24 h value
  forward will structurally under-predict any component that accelerates after
  the cutoff, which is precisely the failure mode we care about; (b) the
  conformal interval's *upper* bound does cross the limit for some of these, so
  a limit-crossing flag based on the interval rather than the point estimate may
  be the more useful signal. Your call — this is model territory, not API.

- **`persistence` beat `xgboost`** on internal validation (0.1795 vs 0.2183
  normalized MAE). The API defaults to your validation winner, supports
  `forecast_model=xgboost` for the demo, and always reports which model produced
  the numbers plus your `selection_warning`. It never claims XGBoost is better.

---

## 3. Still open: lower-limit / two-sided screening

Unchanged from the previous version of this document, and **not needed for the
MLCC pilot**, which is upper-limit only.

Current mitigation, now enforced at the MLCC boundary too: an upload supplying
`lower_limit` values is **rejected with 422**, rather than silently screened
against the upper limit. There is a test for it
(`test_lower_limit_is_rejected_not_screened_as_upper`).

The proposed minimal patch to `decision.py` — an explicit `limit_direction`
parameter defaulting to `UPPER` so existing callers are unaffected — and its
failing regression test stand as previously written. Only needed when a
lower-limit family (film capacitors, thin-film resistors) gets its own validated
profile.

---

## 4. What the backend needs next

Nothing blocking. When you have them:

1. A machine-readable reason code on unscored records (A1).
2. Any newer bundle — it drops in by replacing `outputs/mlcc_v1/model_bundle/`;
   the API verifies the manifest checksums and library versions at startup and
   refuses to serve a bundle that fails either. No frontend contract change is
   needed for a new bundle of the same family.
3. A decision on `xgboost` vs `persistence` for the demo (§2).
