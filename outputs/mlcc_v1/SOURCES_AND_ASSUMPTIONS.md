# MLCC dataset sources and assumptions

Research checked 5 September 2026.

## What these files are

The accompanying CSVs are newly generated synthetic X7R MLCC screening data.
They are a reproducible engineering test fixture for the SIH26170 prototype,
not measurements from NASA, ISRO, Kaggle, a capacitor vendor or a laboratory.
No external experimental rows have been mixed into them.

Four fictional part profiles, manufacturing-batch variation, operating
conditions and multiple trajectory patterns make the software exercise more
substantial than adding random columns to an unrelated dataset. The generator
and manifest specify the actual numerical assumptions. They have not been
fitted to a real MLCC manufacturer's population or approved screening rules.

## Public data checked

| Source | What it supports | Decision for this prototype |
|---|---|---|
| [Kaggle capacitor ageing candidate](https://www.kaggle.com/datasets/sellerans/capacitor-aging-analysis-under-electrical-stress/data) | A public capacitor electrical-stress dataset listing | The listing does not establish the individual MLCC 0/24/168 h measurement structure and provenance required here. Not imported. |
| [2023 MLCC study](https://doi.org/10.1063/5.0158360) and [author repository](https://github.com/asepehri93/MLCC-LifeTime-Prediction) | X7R population mean-time-to-failure modelling at different stress conditions; authors provide data/code links | Relevant methodology reference. Population lifetime observations cannot simply be converted into individual 24 h leakage histories by adding columns. Not imported. |
| [2025 individual leakage-based MLCC failure prediction, publisher supplement collection](https://aip.figshare.com/collections/_strong_Time_to_Failure_Prediction_for_MLCCs_A_Machine_Learning_Approach_Based_on_Leakage_Current_Data_strong_/7736447) | A closer precedent: individual failure prediction from leakage curves and accelerated testing | The collection lists a supplementary figure item. A suitable raw longitudinal dataset was not verified in this pass. Keep as a candidate for further data acquisition and a novelty reference. |
| [NASA 2024 cracking/screening analysis](https://ntrs.nasa.gov/citations/20240003605) | A documented reason to monitor leakage during testing and investigate screening weaknesses | Supports choice of signal and use case; does not validate this generator's constants or physical diagnoses. |
| [Murata leakage/insulation FAQ](https://www.murata.com/en-global/support/faqs/capacitor/ceramiccapacitor/char/0039) | Relationship between leakage, voltage and insulation resistance | Supports unit conversion; calculated leakage and a guaranteed insulation specification must not be treated as interchangeable guarantees. |

Research already includes individual MLCC failure prediction. Our defensible
proposal is a usable early-screening workflow with batch comparison, prediction
uncertainty, evidence and integration with test CSVs. Do not claim that MLCC
failure prediction or anomaly detection has never been done.

## Meaning of the simulation

- Leakage values and limits are in microamps (`leakage_ua`). They are explicitly
  hypothetical test-profile values. No single universal MLCC leakage limit is
  claimed.
- A healthy capacitor may settle or fluctuate; an increase is not automatically
  a physical failure.
- Gradual, accelerating, late-onset and intermittent trajectories deliberately
  overlap. Some later events have no useful warning at 24 h. The model should
  be allowed to miss them and report uncertainty.
- A moisture-associated scenario is a simulated hypothesis, not a diagnosis
  of water ingress. Environmental history, test humidity and a confirmed
  physical cause are different quantities.
- Instrument/channel faults corrupt observed measurements. Separate latent
  component measurements allow us to avoid counting a tester error as a
  physical component failure.
- Capacitance and dissipation factor are auxiliary observations for pattern
  exploration. Their simulated correlations are not evidence of universal
  relationships in real components.
- `insulation_resistance_gohm = measurement_voltage_v / (1000 * leakage_ua)`.
  This column is derived, so its relationship with leakage is an identity, not
  a newly discovered predictive signal.
- The first model uses an explicit early feature allowlist. Part IDs, scenario
  labels, 168 h values and derived future outcomes cannot enter training inputs.

## Keeping the experiment honest

Training, calibration and test sets contain different complete batches. The
two pattern-analysis teammates receive training data only. They can challenge
generator assumptions and recommend new experiments, but cannot tune the
prototype using calibration/test results.

The deployed model sees exactly the 0 h and 24 h observations for the SIH mode.
Full histories remain useful for exploratory work and retrospective scoring.
Changing 96/168 h observations must not change an already defined 24 h input,
score or forecast.

Calibration estimates a nominal prediction interval. Empirical test coverage
must be reported, and dependence among parts in the same batch limits a simple
row-level conformal guarantee. Synthetic coverage does not establish coverage
on real hardware.

The nominal scenario mix is deliberately useful for testing; it is not a
manufacturer's defect prevalence. Separate rare-defect and shifted-condition
stress sets probe how performance changes. They are synthetic stress tests too.

## Next real-data requirement

Request de-identified records with component and lot IDs, exact measurement
times, units, approved test limits, part specifications, measurement conditions,
test-equipment metadata and actual later readings. For suspected causes, request
inspection/retest findings separately. Preserve the original data and provenance;
never fill missing real histories with simulated values without labelling them.
