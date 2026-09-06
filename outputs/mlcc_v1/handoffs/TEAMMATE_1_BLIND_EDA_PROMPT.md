# Teammate 1 — understand the MLCC data before machine learning

Send this prompt to a fresh Claude conversation together with the **training-only exploration pack**. Use Claude Code in the extracted folder if available. A chat-only Claude must say which steps it cannot execute rather than claim they passed.

---

You are helping a teammate who knows basic Python explore data for our Smart India Hackathon project, SIH26170: AI-driven anomaly detection in component burn-in and screening. Explain each calculation in plain language and create runnable scripts as you work. Begin now; do not stop at a plan.

Our component is an X7R multilayer ceramic capacitor, or MLCC. Capacitors help stabilise electrical power. During a controlled heat-and-voltage test, we measure leakage current: electricity that passes through the capacitor's insulating material. A part can be below the allowed leakage limit at 24 hours yet behave unusually compared with similar parts. Our eventual software will flag unusual early behaviour and predict leakage at 168 hours from the readings at exactly 0 and 24 hours.

**All data in this pack is synthetic.** It was generated for a working demonstration. It is not a Kaggle measurement study, a manufacturer dataset or proof of aerospace reliability. We want your observations to challenge the generator and reveal unrealistic shortcuts before we trust a model trained on it.

## Your assignment and boundary

Perform data quality checks and exploratory analysis only. Do **not** train, tune or import an ML model. Do not inspect scenario labels or any calibration/test data. Your allowed inputs are `train_readings.csv`, `train_early.csv` and the accompanying data dictionary/provenance notes. Locate these by name inside the supplied pack. If they are absent, identify the missing file and continue with the available training files; do not invent records.

`train_readings.csv` contains training histories at 0, 6, 12, 24, 48, 72, 96, 120, 144 and 168 hours. `train_early.csv` contains exactly the 0 h and 24 h checkpoints. Use early data for every claim about what could be known at 24 h. Use later readings only in separately labelled descriptive trajectory/outcome views. Never transfer later observations into early feature calculations.

The main series is `component_family=MLCC_X7R`, `measurement_name=leakage_ua`; `measurement_value` is leakage in microamps. Data is long format: one measurement for one component at one time per row. Preserve IDs as strings. Read the supplied dictionary for the exact schema and units before coding. The core columns are `component_id,batch_id,component_family,hours,measurement_name,measurement_value,upper_limit`. Group histories by batch, family, component and measurement, also verifying that `profile_id` does not change within a history.

Available auxiliary columns include `capacitance_nf`, `dissipation_factor_pct`, `insulation_resistance_gohm`, part/profile metadata, rated/applied/measurement voltages, stress/measurement temperatures, tester/channel/board location, and synthetic-source markers. `prior_storage_humidity_pct` describes storage history, **not humidity in the hot burn-in chamber**. `applied_voltage_v` and `temperature_c` are stress conditions; `measurement_voltage_v` and `measurement_temperature_c` are measurement conditions. Keep those distinctions in charts. Insulation resistance is calculated from measurement voltage and leakage; it is **not** an independent confirming sensor.

## Work to produce

1. **A trustworthy inventory.** Count rows, unique components, batches and checkpoints. Use the documented complete identity when grouping; do not assume a component ID is globally unique. Check missing values, duplicate identity/time/measurement rows, invalid numbers, inconsistent units or limits, time ordering and missing 0/24 h pairs. Check whether the early file matches the 0/24 h subset of the full training file. Report problems; never silently delete, fill or alter the source data.
2. **Five understandable early measurements per component.** Calculate leakage at 0 h, leakage at 24 h, absolute change, percentage change when the initial value is positive, and slope `(value_24 - value_0) / 24`. Also show `value_24 / upper_limit`, clearly called fraction of the limit. Keep the meaning and unit beside every formula. If the denominator is zero or missing, report unavailable instead of infinity or an invented zero.
3. **Fair peer comparisons.** Group only compatible parts: family, measurement, part/profile, relevant test voltage/temperature and batch, as supported by the dictionary. Plot 24 h leakage and drift by batch, showing sample size. Describe which parts look different without calling them defective. A shared batch offset could be manufacturing variation or a test effect.
4. **Four to six useful figures.** Include checkpoint completeness, a 24 h leakage distribution with units, a drift-by-batch comparison, a 0 h-versus-24 h scatter, and a small selection of full trajectories in a clearly marked retrospective figure. Use a log scale for positive leakage if it improves readability, and state that choice. Show the fixed limit where it is applicable. Avoid hundreds of unreadable lines.
5. **A one-page findings note.** Give five observations with actual counts or values, three questions for Karthik and two possible weaknesses in the synthetic dataset. Explain what each chart tells a beginner and what it cannot prove. Look for suspiciously perfect group separation, repeated curves, unrealistic jumps, duplicate histories and metadata that trivially identifies an outcome.

Use Python, pandas, NumPy and matplotlib/seaborn. Start with the environment already provided; keep added dependencies small. Create `analysis/teammate_1/explore_training.py`, a requirements note if needed, and an `analysis/teammate_1/results/` folder containing figures, summary tables and `FINDINGS.md`. Make the script reproducible with one documented command. A notebook is optional; the script is required. Tables in CSV form must have explicit names and units in the dictionary/readme.

Keep raw files unchanged. Exclude IDs, batch names and source/scenario labels from any proposed predictive feature list. You may analyse batch variation descriptively; the batch identifier itself is not a learned physical explanation. Do not claim a correlation proves cracking, moisture ingress or another physical cause.

Finish by explaining what you found in language a Python beginner can present, listing files produced, the exact command run, and any checks that could not be completed. Return findings to Karthik before proposing changes. He owns the generator and model. The first prototype is being built in parallel; your analysis can improve its next version using training data, but must never guide tuning on the held-out test set.
