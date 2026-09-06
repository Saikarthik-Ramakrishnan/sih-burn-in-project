# SIH26170 component and industry landscape

**Research date:** 5 September 2026  
**Decision:** Use **high-reliability X7R multilayer ceramic capacitors (MLCCs)**
as the nomination-demo pilot, with **leakage current / insulation resistance** as
the primary degradation signal. Keep the software schema device-agnostic so it
can still accept ISRO's hidden generic component data.

## Executive conclusion

The best balance of industrial importance, documented screening weakness,
fit to the SIH time points, and prototype clarity is:

> **Lot-aware early anomaly detection and 168-hour leakage-drift prediction for
> high-reliability MLCCs used in spacecraft and automotive power electronics.**

This is a better pilot than a generic digital IC, silicon MOSFET, memory device,
or semiconductor laser:

- NASA reports that cracking is the dominant MLCC failure concern and that
  capacitance is relatively insensitive to cracking.
- NASA also reports that cracks may not produce a short circuit during burn-in;
  continuously monitored leakage current is more useful than relying only on a
  post-test result.
- NASA's reviewed MLCC burn-in conditions include **168-264 hours at 125 C**,
  directly matching SIH26170's 0 h, 24 h, 96 h and 168 h framing.
- A 2023 physics-informed ML paper predicts *population mean time to failure*
  for X7R MLCCs. That validates ML feasibility but does not provide the same
  product as SIH26170: per-component, lot-relative outlier screening plus a
  168-hour parametric forecast from early readings.
- Existing commercial offerings found in this scan are predominantly test
  hardware, inspection, yield/PAT analytics, or in-field chip telemetry. None
  of the public product material reviewed documents this exact, vendor-neutral
  MLCC workflow from an ordinary burn-in CSV.

The runner-up is the **enhancement-mode GaN power FET**. It has a very strong
emerging-market story and a real reliability gap, but current NASA GaN work
uses a 48-hour high-temperature gate-bias protocol and small research cohorts,
making it a weaker fit to SIH's 168-hour demonstration and harder to validate.

## 1. What SIH26170 actually asks for

The official ISRO statement is not general predictive maintenance. It asks for:

1. a dynamic outlier detector that catches a component abnormal relative to
   its lot even while it remains inside its absolute data-sheet limit;
2. a regression model using 0-hour and 24-hour readings to forecast the
   168-hour value;
3. strong protection against false negatives;
4. low mean absolute prediction error; and
5. an explanation a QA inspector can understand.

The statement gives IDDQ, leakage current and propagation delay as examples,
not an exclusive list. A capacitor's leakage current / insulation resistance is
therefore a direct fit.

Official statement: <https://www.sih.gov.in/sih2026PS>

## 2. The existing industry stack

There is already substantial technology around component screening. Our claim
must be narrower than "AI has never been used in electronics reliability."

### Layer A - qualification and statistical screening

The Automotive Electronics Council has separate qualification families for
integrated circuits (AEC-Q100), discrete semiconductors (AEC-Q101),
optoelectronics (AEC-Q102), sensors (AEC-Q103), multichip modules (AEC-Q104),
and passives (AEC-Q200). AEC-Q001 already specifies Part Average Testing, and
AEC-Q002 covers statistical yield analysis. These establish that lot-relative
statistics are standard industrial practice; our contribution is the time
trajectory and forecast, not the invention of statistical screening.

Source: <http://www.aecouncil.com/AECDocuments.html>

NASA's EEE-INST-002 similarly establishes baseline selection, screening,
qualification and derating for spaceflight EEE parts.

Source: <https://nepp.nasa.gov/pages/EEE-INST-002.cfm>

### Layer B - stress and automated test equipment

- **Aehr Test Systems** publicly documents wafer-, die- and package-level test
  and burn-in for SiC, GaN, AI processors, memory, sensors, microcontrollers,
  silicon photonics and other optical devices. This is stress/application and
  measurement infrastructure.
- **Cohu** provides production test cells for SiC/GaN power devices and
  dedicated test systems for inertial, magnetic, microphone, optical and
  pressure MEMS sensors.
- **Teradyne** has mature memory, digital/mixed-signal, analog/power, system
  level and silicon-photonics test families.
- **Chroma** provides semiconductor IC and power-component automatic test
  systems, capacitor test systems, and electrolytic-capacitor test equipment.

These products prove that automated test data exists. They do not, on the
public pages reviewed, make the exact SIH claim of predicting each device's
168-hour parameter from its first 24 hours with a calibrated uncertainty range.

Sources:

- <https://www.aehr.com/>
- <https://www.cohu.com/wide-bandgap-test>
- <https://www.cohu.com/mems-sensor-test>
- <https://www.teradyne.com/application-pages/memory/>
- <https://www.chromaate.com/en/products_list/power_electronic_component_ats>
- <https://www.chromaate.com/en/product/capacitor_test_system_1820_256>

### Layer C - semiconductor data analytics and predictive products

- **PDF Solutions Exensio Test Operations** performs automated collection,
  rules, PAT variants, clustering and test/yield monitoring, and states that it
  manages data from more than 4,000 testers.
- **PDF Solutions' ML platform** advertises multivariate and edge prediction
  across high-volume semiconductor manufacturing, including a specific
  compound-semiconductor/SiC analytics offer.
- **proteanTecs** combines ML with on-chip monitors for production and in-field
  health, test-escape reduction and predictive failure detection.
- **yieldWerx** provides predictive yield analytics, including photonics use
  cases.
- **Siemens Tessent** provides DFT, yield learning and in-life silicon
  analytics.

These are the closest commercial substitutes. They are broad enterprise
platforms, usually requiring tester integration, a manufacturing data estate,
or instrumented silicon. A lightweight, audit-oriented CSV add-on for a
specialist reliability lab remains a credible product gap, but it is an
**integration and workflow gap**, not an absolute absence of AI.

Sources:

- <https://www.pdf.com/products/exensio-analytics-platform/modules/test-operations/>
- <https://www.pdf.com/products/technology/machine-learning/>
- <https://www.pdf.com/analytics-for-compound-semiconductors-download/>
- <https://www.proteantecs.com/solutions/>
- <https://yieldwerx.com/>
- <https://eda.sw.siemens.com/en-US/ic/tessent/silicon-lifecycle-solutions/>

## 3. Component-by-component comparison

"Gap" below means the lack of a **publicly documented close solution**, not
proof that no proprietary system exists inside a manufacturer.

| Component family | Burn-in / degradation signals suitable for a CSV | Industries and importance | Existing solutions found | Gap and SIH verdict |
|---|---|---|---|---|
| Digital logic, MCU, SoC and AI ASIC | IDDQ/standby current, supply current, propagation delay, timing margin, functional errors | Space computers, automotive ECUs, telecom, data centres and AI infrastructure | AEC-Q100/Q001/Q002; mature ATE and PAT; Aehr AI-processor burn-in; PDF Solutions/proteanTecs/Siemens analytics; published automotive-SoC burn-in toolchain | Very important and exact SIH fit, but commercially crowded and often proprietary. Keep as generic compatibility profile, not the headline pilot. |
| DRAM, NAND and other memory | Standby/active current, bit errors, retention, timing and bad-block growth | Space computing, servers, phones, vehicles and storage | Dedicated Teradyne/Aehr platforms, BIST, pattern test, yield analytics; extensive NASA radiation and assurance work | Critical but one of the most mature and data-proprietary test domains. Weak novelty. |
| Silicon power MOSFET and IGBT | RDS(on), VTH, leakage, VCE(sat), thermal resistance and switching loss | Motor drives, converters, EVs, aerospace power and industrial automation | Mature static/dynamic test; extensive prognostics/RUL literature; public NASA run-to-failure MOSFET and IGBT data | Easiest real-data prototype but too familiar for the best novelty story. Useful baseline/backup. |
| SiC MOSFET and Schottky diode | Gate/drain leakage, VTH, RDS(on), dynamic RDS(on), body-diode VF and breakdown | EV traction, charging, renewable energy, industrial and aerospace high-voltage power | Aehr production wafer-level burn-in; Cohu high-voltage/high-current test; PDF Solutions explicitly markets SiC manufacturing analytics | High importance, but burn-in hardware and analytics competition is already visible. Strong runner-up, not the clearest gap. |
| Enhancement-mode GaN power FET / HEMT | VTH, gate leakage, drain leakage, RDS(on), dynamic RDS(on) and current collapse | Space power, data centres, industrial converters, solar, automotive auxiliaries and fast chargers | NASA is still building reliability evidence and influencing standards; Aehr moved from first GaN qualification system in 2023 to a production order in 2025; Cohu has GaN test cells; a 2025 simulation-plus-LSTM lifetime study exists | Excellent importance and emerging gap. However, the public NASA protocol is 48 h and datasets are small. **Runner-up.** |
| Quantum-cascade and semiconductor lasers | Drive current, voltage, optical output, threshold current, slope efficiency and differential resistance | Sensing, defence, spectroscopy and space optical payloads | A 2022 open study and codebase already demonstrate SVM early-failure prediction during accelerated QCL burn-in, up to 200 h before failure | This is almost the same core idea as SIH26170, so it is a valuable benchmark but a poor novelty claim. |
| Silicon-photonic / optical IC | Optical power, laser/photodiode current, insertion loss, wavelength drift and thermal tuning power | Data-centre interconnects, telecom and emerging chip-to-chip optical I/O | Aehr production wafer burn-in; Teradyne Photon platform; yieldWerx photonics analytics | Very important, but expensive to reproduce, limited public device-level ageing data, and visibly growing commercial coverage. |
| X7R multilayer ceramic capacitor (MLCC) | Leakage current, insulation resistance, capacitance, dissipation factor, breakdown voltage and temperature | Ubiquitous filtering/decoupling in space and automotive electronics; a cracked short can disable a power rail | AEC-Q200, conventional electrical tests, acoustic/X-ray inspection; NASA says present procedures can miss cracks and recommends monitored leakage; one physics-ML MTTF paper exists | Best documented screening gap and perfect 168 h fit. Electrical time-series are simple to explain and cheap to demonstrate. **Selected pilot.** |
| Polymer tantalum capacitor | Direct-current leakage, current spikes, ESR, capacitance, dissipation factor and moisture/temperature history | High-density power rails in automotive, medical, military and space systems | NASA has detailed screening guidance including 5-minute monitored current during 40 h burn-in and 1,000 h life tests | Strong, under-served niche with rich time-series behaviour. Protocol does not match 168 h as cleanly, and moisture preconditioning is a major confounder. **Third place.** |
| MEMS pressure/inertial/magnetic/optical sensor | Bias/offset, sensitivity, noise, scale factor, temperature coefficient and response time | Guidance, navigation, phones, vehicles, industrial control and medical devices | AEC-Q103; Cohu has production-proven, sensor-specific parallel test cells; vendor-specific calibration/test analytics | Important, but each sensor type needs different physical stimulus and labels. Too broad for one convincing one-day data story. |
| Optocoupler / optoisolator | Current-transfer ratio, LED forward voltage, output leakage, propagation delay and isolation leakage | Spacecraft isolation, power converters, industrial controls and medical isolation | Qualification and radiation testing are established; little close public ML burn-in prediction was located | High public-solution gap, but lower market breadth and scarce public ageing data make validation weaker than MLCC/GaN. |

## 4. Closest research precedents

These papers prevent an exaggerated novelty claim:

1. **Quantum cascade laser early-failure prediction (2022).** A simple RBF-SVM
   used conventional electrical/optical burn-in measurements. Nine devices were
   studied, and the authors released data/code. The result validates the
   general idea but is device-specific and has a very small cohort.
   <https://doi.org/10.1038/s41598-022-13303-0>
2. **MLCC MTTF prediction (2023).** XGBoost plus physics and transfer learning
   predicted mean time to failure across voltage/temperature conditions for
   X7R MLCCs. This is population/stress-condition prediction, not early
   per-component screening against lot peers.
   <https://doi.org/10.1063/5.0158360>
3. **Automotive SoC burn-in effectiveness (2023).** A published toolchain
   quantifies burn-in stress effectiveness for large automotive SoCs, showing
   that sophisticated digital-IC burn-in optimization is already an active
   field. <https://doi.org/10.1109/ACCESS.2023.3316511>
4. **GaN lifetime prediction (2025).** COMSOL-generated thermal/mechanical data
   feed an LSTM. It is a simulation-based service-life predictor rather than a
   per-device production burn-in predictor using actual early electrical
   readings. <https://doi.org/10.3390/electronics14193883>

## 5. Weighted decision matrix

Weights reflect this particular hackathon, not a market valuation:

- industrial/space criticality: 25%;
- public solution gap: 25%;
- fit to SIH 0/24/96/168 h protocol: 20%;
- obtainable evidence/data: 15%;
- clarity and feasibility of the nomination demo: 15%.

Each raw score is 1-5. The total is normalized to 100. Scores are reasoned
decision aids based on the sources above; they are not measured market facts.

| Rank | Component | Criticality | Public gap | Protocol fit | Evidence/data | Demo clarity | Weighted total |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | X7R MLCC | 5.0 | 4.5 | 5.0 | 3.0 | 5.0 | **91.5** |
| 2 | Polymer tantalum capacitor | 4.5 | 4.5 | 3.0 | 3.0 | 5.0 | **81.0** |
| 3 | GaN power FET | 5.0 | 4.0 | 3.0 | 2.5 | 5.0 | **79.5** |
| 4 | Silicon MOSFET / IGBT | 5.0 | 2.0 | 4.0 | 5.0 | 4.0 | **78.0** |
| 5 | SiC MOSFET | 5.0 | 2.5 | 4.0 | 3.0 | 5.0 | **77.5** |
| 6 | Digital logic / AI ASIC | 5.0 | 2.0 | 5.0 | 3.0 | 4.0 | **76.0** |
| 7 | Quantum-cascade laser | 4.0 | 1.0 | 5.0 | 5.0 | 5.0 | **75.0** |
| 8 | Optocoupler | 4.0 | 4.0 | 4.0 | 2.0 | 4.0 | **74.0** |
| 9 | DRAM / NAND | 5.0 | 1.5 | 4.0 | 4.0 | 3.0 | **69.5** |
| 10 | Silicon photonic IC | 5.0 | 2.0 | 4.0 | 2.0 | 4.0 | **69.0** |
| 11 | MEMS sensor | 4.5 | 2.5 | 3.0 | 2.5 | 4.0 | **66.5** |

## 6. Why MLCC wins

### Importance is real

MLCCs are foundational passive parts. In high-reliability electronics, one
shorted decoupling/filter capacitor can collapse a shared rail. The AIP study
calls their reliability critical to electronic systems, AEC-Q200 covers their
automotive qualification class, and NASA continues to revise how they should be
screened for space.

### The gap is documented rather than invented

NASA's 2024 MLCC analysis reports:

- most MLCC application failures involve cracking;
- capacitance is the least sensitive electrical characteristic to cracking;
- cracks may not become a short during burn-in;
- longer leakage-current observations are more effective than a quick
  insulation-resistance reading; and
- monitoring leakage during burn-in and life tests helps reveal defective
  samples.

This is almost a requirements document for the proposed analytics layer.

Source: <https://nepp.nasa.gov/docs/tasks/007-Capacitors-Evaluation/NEPP-CP-2024-Teverovsky-JEDEC-May-Presentation-MLCCs-20240003605.pdf>

### It fits the exact SIH data shape

For one part number and one manufacturing lot:

- **0 h:** baseline leakage/IR, capacitance and dissipation factor;
- **24 h:** early movement and lot-relative anomaly score;
- **96 h:** updated trajectory and uncertainty;
- **168 h:** hidden/final outcome for training and evaluation.

No camera, oscilloscope waveform or proprietary processor test vector is
required for the dashboard demonstration.

### Existing ML does not erase the opportunity

The 2023 MLCC study predicts MTTF for stress conditions. Our proposed unit of
decision is different: **one physical capacitor inside one lot**, compared with
its true peers, with a forecast of its measured 168-hour leakage and a QA
recommendation. We should cite the paper as precedent and make this distinction
explicit.

## 7. Exact pilot definition

### Device scope

Start with one tightly controlled family:

> X7R MLCCs of one capacitance, voltage rating, package size and manufacturer
> part number, grouped by manufacturing lot.

Do not mix 10 nF and 10 uF parts, different voltage ratings, different package
sizes, or different dielectric families in one reference population.

### Primary endpoint

**Primary prediction target:** leakage current at 168 hours under the specified
burn-in voltage and temperature.

If source data supplies insulation resistance rather than leakage, retain the
original measurement and transform consistently; do not silently mix the two.

### Secondary measurements

- capacitance;
- dissipation factor / tan delta;
- insulation resistance;
- applied voltage;
- chamber temperature and humidity;
- lot, board position and measurement channel;
- pre/post-soldering flag; and
- optional acoustic/X-ray/DPA result for verified cause labels.

### Minimum CSV identity

```text
component_id
batch_id
manufacturer_part_number
dielectric_class
capacitance_nominal
voltage_rating
package_size
hours
measurement_name
measurement_value
upper_limit
lower_limit
temperature_c
stress_voltage_v
humidity_pct
board_position
tester_channel
data_source
```

The existing generic SIH input contract can remain. The extra columns enrich
the MLCC pilot and help prevent false lot comparisons.

## 8. Failure mechanisms: what the dashboard may and may not say

Electrical trajectories can support **mechanism hypotheses**, not ground-truth
root-cause claims.

| Pattern | Safe dashboard wording | Verification required before assigning a cause label |
|---|---|---|
| Leakage rises gradually under bias | "Progressive insulation degradation pattern" | Failure analysis or controlled experiment |
| Intermittent current spikes | "Unstable conduction / intermittent leakage pattern" | High-rate current trace and physical analysis |
| Leakage changes with humidity history | "Moisture-correlated leakage behaviour" | Controlled humidity exposure and package inspection |
| Sudden step after soldering | "Post-assembly step change" | Acoustic microscopy, X-ray or cross-section for crack/delamination |
| Isolated board/channel shift across many parts | "Probable tester/fixture anomaly" | Retest on a different channel |

Do not let the model state "water seepage caused this failure" from leakage
alone. If synthetic data includes moisture ingress, store it only in a hidden
ground-truth table and label the user-visible output as a hypothesis.

## 9. The novelty statement to use

> Existing systems mostly apply the burn-in stress, inspect parts, or run
> static/yield-level analytics. Our system is a vendor-neutral decision-support
> layer for high-reliability MLCC screening: it compares each capacitor with its
> own lot, detects subtle leakage drift while the part is still within its
> absolute limit, forecasts its 168-hour value from early readings, quantifies
> uncertainty, and gives an auditable reason to a QA engineer.

Do not say "the first AI burn-in system" or "no existing solutions." Both are
contradicted by commercial analytics platforms and the published QCL/MLCC work.

## 10. What this changes in our implementation

1. Keep the shared backend and API generic for ISRO evaluation.
2. Replace the current headline synthetic families with an **MLCC-X7R pilot
   profile**; retain digital-IC and MOSFET profiles only as compatibility tests.
3. Make leakage current the hero trajectory and 168-hour regression target.
4. Add capacitance, dissipation factor, temperature, stress voltage, humidity,
   board position and tester channel as optional covariates.
5. Use the optional board/channel fields to distinguish a component anomaly
   from a tester/fixture shift.
6. Evaluate on complete held-out lots, not randomly split rows or capacitors.
7. Report normalized MAE, future-limit-crossing recall, false-negative rate,
   false-positive rate, prediction-interval coverage and warning lead time.
8. Present recommendations as `ACCEPT`, `MONITOR`, `RETEST`, or
   `ENGINEER REVIEW`; never auto-certify a spaceflight part.

## 11. Evidence and data strategy

### Real evidence we can use now

- NASA's MLCC analysis establishes the failure/screening problem and realistic
  measurements/test durations.
- The published MLCC physics-ML work establishes that voltage, temperature and
  material-aware ML can improve failure-time prediction.
- NASA's Prognostics Data Repository provides real IGBT, silicon MOSFET and
  capacitor ageing datasets. Those are useful for testing the generic pipeline,
  but must not be relabelled as MLCC burn-in evidence.

Source: <https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/>

### Synthetic evidence we still need

Generate an explicitly labelled MLCC dataset that contains healthy settling,
gradual leakage growth, accelerating leakage, intermittent spikes,
soldering-associated steps and tester-channel faults. Parameters must be tied
to ranges from cited sources where possible. The generator is for software and
sensitivity testing, not proof of real-world detection performance.

### Best validation request to ISRO/industry

Ask for de-identified historical rows containing:

- at least 20-30 production lots;
- preferably hundreds of capacitors per part-number/lot family;
- 0/24/96/168-hour measurements under consistent stress;
- absolute limits and retest outcomes;
- board and tester-channel identifiers; and
- failure-analysis labels for a subset.

The final sample-size requirement must be determined from observed defect
prevalence and desired confidence. It should not be invented before real data
arrives.

## 12. Research limitations

- Public product pages do not reveal proprietary algorithms used inside
  semiconductor or capacitor manufacturers.
- A lack of a close Crossref/OpenAlex result is evidence of limited public
  documentation, not proof of non-existence.
- Vendor press releases demonstrate adoption and market direction but are not
  independent performance validation.
- NASA presentations and technical memoranda are authoritative for the stated
  experiments, but some reviewed cohorts are small and should not be treated as
  population-level proof.
- No official SIH26170 dataset was linked on the problem page as of the research
  date, so the pilot choice must not hard-code assumptions into the generic API.

## Primary source list

1. ISRO/SIH26170 official problem statement: <https://www.sih.gov.in/sih2026PS>
2. Automotive Electronics Council document index: <http://www.aecouncil.com/AECDocuments.html>
3. NASA EEE-INST-002: <https://nepp.nasa.gov/pages/EEE-INST-002.cfm>
4. NASA, *Cracking Failures in MLCCs and Military Specifications* (2024): <https://nepp.nasa.gov/docs/tasks/007-Capacitors-Evaluation/NEPP-CP-2024-Teverovsky-JEDEC-May-Presentation-MLCCs-20240003605.pdf>
5. NASA, *Guidelines for Screening, Lot Acceptance, and Derating for Polymer Tantalum Capacitors* (2023): <https://nepp.nasa.gov/docs/tasks/003a-Guidelines-Polymer-Tantalum-Capacitors/NEPP-NASA-TP-2023-Teverovsky-Guidelines-Screening-PTC-20220019033.pdf>
6. NASA, *Collaborative Evaluation of GaN FET Reliability* (2024): <https://nepp.nasa.gov/docs/etw/2024/05-JUN-WED/1130-Tiu-GaN-FET-20240006694.pdf>
7. NASA Prognostics Center of Excellence datasets: <https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/>
8. Yousefian et al., MLCC physics-based ML: <https://doi.org/10.1063/5.0158360>
9. Aydinkarahaliloglu et al., QCL early failure prediction: <https://doi.org/10.1038/s41598-022-13303-0>
10. Bernardi et al., automotive SoC burn-in stress toolchain: <https://doi.org/10.1109/ACCESS.2023.3316511>
11. Xu et al., simulation/LSTM GaN lifetime prediction: <https://doi.org/10.3390/electronics14193883>
12. Aehr, first GaN qualification-system order (2023): <https://www.aehr.com/2023/12/aehr-receives-first-order-for-fox-wafer-level-test-and-burn-in-system-to-be-used-for-gallium-nitride-semiconductor-engineering-and-qualification/>
13. Aehr, GaN production-system order (2025): <https://www.aehr.com/2025/01/aehr-announces-initial-fox-xp-multi-wafer-test-and-burn-in-production-system-order-from-major-gallium-nitride-power-semiconductor-supplier/>
14. Aehr, AI-processor wafer burn-in (2025): <https://www.aehr.com/2025/02/aehr-announces-shipment-of-initial-fox-xp-wafer-level-burn-in-system-for-advanced-ai-processors/>
15. Aehr, silicon-photonics production burn-in (2024): <https://www.aehr.com/2024/03/aehr-announces-shipment-of-new-high-power-configured-fox-xp-system-for-wafer-level-burn-in-and-stabilization-of-next-generation-silicon-photonics-integrated-circuits/>
16. Cohu SiC/GaN test solutions: <https://www.cohu.com/wide-bandgap-test>
17. Cohu MEMS/sensor test solutions: <https://www.cohu.com/mems-sensor-test>
18. PDF Solutions Exensio Test Operations: <https://www.pdf.com/products/exensio-analytics-platform/modules/test-operations/>
19. PDF Solutions machine learning: <https://www.pdf.com/products/technology/machine-learning/>
20. proteanTecs production/in-field analytics: <https://www.proteantecs.com/solutions/>
21. Siemens Tessent silicon-lifecycle analytics: <https://eda.sw.siemens.com/en-US/ic/tessent/silicon-lifecycle-solutions/>

