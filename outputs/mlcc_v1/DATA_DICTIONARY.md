# MLCC data dictionary

All rows are synthetic. Read `SOURCES_AND_ASSUMPTIONS.md` first. Each readings
row describes one fictional capacitor at one elapsed burn-in time. The main
measurement is leakage in microamps. Auxiliary measurements are extra columns.

## Readings available for analysis

| Column | Meaning | Role |
|---|---|---|
| component_id | Unique capacitor identifier | Join key; never a numeric model input |
| batch_id | Manufacturing/test batch | Peer group and split key |
| component_family | MLCC_X7R | Supported family identifier |
| measurement_name | leakage_ua | Main measurement name and unit convention |
| hours | Elapsed burn-in hours | Time key; early files contain exactly 0 and 24 |
| measurement_value | Observed leakage, µA | Main model observation |
| upper_limit | Fictional upper leakage limit, µA | Simulation screening rule |
| profile_id | One of four fictional part profiles | Identify comparable specifications |
| part_number | Explicitly fictional part number | Traceability, not a real vendor product |
| nominal_capacitance_nf | Nominal capacitance, nF | Specification context |
| rated_voltage_v | Fictional voltage rating, V | Specification context |
| package_code | 0805, 1206 or 1210 | Package context |
| dielectric | X7R | Dielectric profile |
| applied_voltage_v | Applied burn-in stress voltage, V | Stress context |
| voltage_stress_ratio | Applied stress voltage divided by rating | Dimensionless stress context |
| temperature_c | Burn-in stress temperature, °C | Distinct from measurement temperature |
| measurement_voltage_v | Voltage used for the leakage measurement, V | Needed for derived insulation resistance |
| measurement_temperature_c | Temperature during measurement, °C | Measurement comparability |
| prior_storage_humidity_pct | Simulated prior storage humidity, percent RH | History; not chamber humidity or proof of water damage |
| tester_id | Test instrument identifier | Investigate equipment-related patterns |
| tester_channel | Instrument channel | Investigate shared measurement errors |
| board_position | Position number within the batch fixture | Location context; no physical row/column geometry is specified |
| capacitance_nf | Simulated measured capacitance, nF | Auxiliary analysis; nominal and measured differ |
| dissipation_factor_pct | Simulated electrical loss factor in percent | A value of 0.7 means 0.7%, not 70% |
| insulation_resistance_gohm | Derived insulation resistance, GΩ | Exactly V / (1000 × leakage in µA); not independent evidence |
| data_source | synthetic | Preserve in every export and screen |
| is_synthetic | true | Preserve in every export and screen |
| generator_version | Generator version identifier | Reproducibility |

Some metadata are useful for exploratory analysis but are not used in the
first model. Inspect the model manifest's feature allowlist; do not automatically
feed all numeric CSV columns into a model.

## Separate labels: training targets or evaluation only

Labels contain the same component/batch/family/measurement identity plus:

| Column | Meaning |
|---|---|
| profile_id | Fictional profile |
| final_value | Observed leakage at 168 h, including measurement noise and tester error; regression target |
| true_final_value | Simulator's latent 168 h leakage without instrument error; unavailable on real hardware |
| is_future_failure | Latent 168 h leakage exceeds the fictional limit; a simulated threshold event, not a certified physical failure |
| is_observed_final_exceedance | Observed 168 h leakage exceeds the fictional limit |
| ever_latent_exceedance | Latent leakage exceeded the limit at any sampled time; may differ from the 168 h result |
| is_defect | A degradation mechanism was assigned; it can remain below the limit |
| is_tester_fault | A common channel error affected measurements; it can coexist with degradation |
| is_healthy | Neither an assigned degradation mechanism nor a tester fault |
| scenario | Simulated trajectory category; otherwise-healthy channel-affected parts use tester_channel_fault |
| component_scenario | Physical-trajectory category before independent tester effects |
| anomaly_onset_hour | Simulated degradation onset; blank when inapplicable |
| tester_fault_onset_hour | Simulated instrument-fault onset; blank when inapplicable |
| upper_limit | Same fictional leakage limit |
| data_source / is_synthetic | Synthetic provenance |

Blank onset values mean not applicable, not zero. A future observed threshold
crossing, a latent threshold crossing, an assigned mechanism and a tester fault
are different outcomes. Report which definition each analysis uses.

## Files and permissions within the experiment

- `train_readings.csv`: training batches at all ten times. For exploratory work
  and offline training-target construction.
- `train_early.csv`: exactly 0 and 24 h inputs for training-batch capacitors.
- `train_labels.csv`: retrospective truth for training-batch analysis.
- `calibration_*`: separate whole batches used to calibrate prediction ranges;
  keep away from feature selection and exploratory teammates.
- `test_*`: separate whole batches used for final evaluation; never tune on
  their results.
- `batch_splits.csv`: fixed assignment of whole batches to train/calibration/test.
- `demo_early.csv`: first test batch by ID for each profile, selected without
  examining labels or model performance. Not an independent benchmark.
- `demo_outcomes.csv`: later measured readings for the same demo parts. Keep
  separate until the UI's outcome reveal.
- `demo_labels.csv`: privileged simulated truth for evaluation, not upload input.
- `stress_low_prevalence_*`: separate rare-mechanism synthetic stress set.
- `stress_unseen_condition_*`: separate shifted-condition stress set.
- `generation_manifest.json`: exact counts, seeds, assumptions, splits and hashes.

The dataset generator does not simulate missing rows or malformed values in the
main data. Validation/error cases belong in software tests; never silently
corrupt the shared reference CSVs to test the UI.

## Time and grouping rules

Full files use 0, 6, 12, 24, 48, 72, 96, 120, 144 and 168 h. The first SIH model
uses exactly 0 and 24 h, not every reading before 24. For charts, distinguish
measured values from the prediction at 168 h.

Compare matching parts within batch, profile and measurement conditions. The
generator makes each batch homogeneous in its profile. Do not compare raw
leakage from differently rated fictional parts without defining the comparison.
IDs must remain strings. Labels and observations join on identity, never row order.
