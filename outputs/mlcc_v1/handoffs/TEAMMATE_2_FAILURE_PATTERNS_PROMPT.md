# Teammate 2 — investigate stress, failure patterns and simple screening

Send this prompt to a fresh Claude conversation with the **training-only exploration pack**, including its separately labelled `train_labels.csv`. Use Claude Code in the extracted folder if available.

---

You are helping a teammate who knows basic Python investigate data for Smart India Hackathon problem SIH26170: AI-driven anomaly detection in component burn-in and screening. Teach through runnable Python and short explanations. Start the work now.

We are testing X7R multilayer ceramic capacitors (MLCCs), which help keep electrical power stable. Burn-in applies controlled heat and voltage, then measures parts over time. The main measurement is leakage current in microamps (`leakage_ua`). A simple test compares that reading with an upper limit. Our question is whether changing leakage and comparisons with similar parts reveal extra warning signs by 24 hours. A later model will predict the 168-hour reading from exactly 0 h and 24 h.

Every record here is **synthetic**. The simulated scenarios are assumptions built into a generator. Discovering their patterns does not establish their prevalence in industry or prove a physical cause. Your job is to test whether the data and early signals make sense before we use machine learning.

## Work in two stages

**Stage A — blind observations:** use only `train_early.csv`, `train_readings.csv` and the dictionary/provenance notes. Do not open or load `train_labels.csv` yet. Write and save `BLIND_OBSERVATIONS.md` before proceeding to Stage B. Locate files by name inside the pack. No calibration or test file is authorised for this assignment.

Read the dictionary first. Preserve string IDs and join using batch, component family, component ID and measurement name, checking profile consistency and one-to-one cardinality, never row order. Early data contains exactly 0 h/24 h; the full training histories have 0, 6, 12, 24, 48, 72, 96, 120, 144 and 168 h. Keep later trajectories separate from every early statistic or flag. Investigate variation within compatible part/test groups before pooling data.

The core columns are `component_id,batch_id,component_family,hours,measurement_name,measurement_value,upper_limit`. Read the extra-field dictionary. `prior_storage_humidity_pct` is historical storage humidity, **not hot-chamber humidity**. `applied_voltage_v`/`temperature_c` are stress conditions; `measurement_voltage_v`/`measurement_temperature_c` are measurement conditions. Tester/channel/board fields describe the measurement setup. `insulation_resistance_gohm` is derived from voltage/leakage and must not count as an independent confirming measurement.

Compute leakage at 0/24 h, leakage change, slope per hour and fraction of the upper limit. Plot these against available stress variables. Show sample counts and missingness. If the design contains no variation in a stress variable, say it cannot support a comparison. Do not invent absent measurements or call a constant condition a discovered risk factor.

Use two simple, fixed screening rules:

- **Fixed-limit flag:** leakage at 24 h is greater than its applicable upper limit. Report equality separately if the test profile does not specify whether it fails.
- **Peer-deviation flag:** for positive leakage, use `log10(leakage_24)` and its median and median absolute deviation (MAD) within a compatible batch/profile group. Define `MAD = median(abs(x - median(x)))` and `robust_z = 0.67449 * (x - median(x)) / MAD`. Flag high-side `robust_z > 3.5` as a predeclared descriptive rule. Also tabulate drift using `log10(leakage_24 / leakage_0)` when both readings are positive. When fewer than 10 peers are available or MAD is zero, mark that peer statistic unavailable; do not pretend a substitute constant is a measured spread. These thresholds are simple exploration conventions, not validated industrial release rules.

Save counts, example identities and a scatter plot that highlights **within limit but unusual** parts. Do not adjust the threshold after seeing labels. Explain that an outlier means unusual, not necessarily defective.

**Stage B — labelled training audit:** only after saving the blind note, open `train_labels.csv`. Join safely and verify one label record per expected identity. Keep these distinct:

- `final_value`: observed final leakage, which can include measurement effects.
- `true_final_value`: the simulator's latent final leakage, inaccessible for real uploaded data.
- `is_future_failure`: whether latent leakage at 168 h exceeds the applicable limit; this is the simulated physical-outcome target.
- `is_observed_final_exceedance`: whether the observed final reading exceeds its limit.
- `is_tester_fault`: simulated measurement-system fault; it does not by itself establish that the capacitor failed.
- `scenario`: the simulated mechanism or behaviour category, used only for this retrospective analysis.

Other generator-only labels include `component_scenario`, `is_defect` and `anomaly_onset_hour`. Do not mistake a simulated defect designation for inevitable limit failure. Scenarios include normal settling/noise, gradual or accelerating drift, late onset, intermittent leakage, a moisture-associated history and tester-channel faults. Keep labels and future/latent values out of all early rules.

Compare early fixed-limit, peer-deviation and combined OR flags against each relevant outcome **separately**. For each rule, give true positives, false positives, false negatives and true negatives; explain them as caught cases, false alarms, missed cases and correctly unflagged cases. Give recall and false-positive rate with raw denominators. Use unavailable when a denominator is zero. These are exploratory results on training data, not final prototype performance or estimated real-world accuracy.

Create scenario-by-rule and stress-by-outcome summary tables, always with counts. Examine cases where observed and latent outcomes disagree, especially tester faults. Explain why leakage patterns alone cannot distinguish moisture ingress, cracks and tester effects with certainty. Associations involving generator labels show what was simulated, not causal proof.

Check whether a scenario is too easy to identify from a single metadata field, whether healthy variation is too narrow, and whether failure scenarios have any realistic overlap with normal observations. Report potential shortcuts to Karthik. Do not change the dataset, invent new measurements, tune thresholds on labels, fit an ML model or inspect calibration/test results.

## Deliverables

Use Python, pandas, NumPy and matplotlib/seaborn. Create two runnable scripts: `analysis/teammate_2/blind_patterns.py` and `analysis/teammate_2/labelled_audit.py`. The first must not read the labels at all. The second should require the saved blind note to exist. Keep outputs in `analysis/teammate_2/results/`.

Deliver the blind note, a concise `FINDINGS.md`, four to six labelled charts, early-rule comparison tables and exact commands that reproduce them. Give five evidence-backed findings, three generator/model questions and a short glossary explaining leakage, drift, median, MAD, false alarm and missed case. State what ran and what did not run. Keep all raw data unchanged.

The ML prototype is proceeding in parallel so the team can integrate a demo. Your findings should challenge its training assumptions and guide a later version; the held-out test set must remain outside your workflow.
