# Dashboard brief for the UX and frontend designer

Copy the prompt below into your design or coding assistant.

---

Design a dashboard for SIH26170: early anomaly detection and final-measurement prediction during electronic component burn-in testing. Burn-in means testing components under controlled heat and electrical stress over time.

You have full freedom over branding, colours, typography, layout, navigation and your design signature. Choose a single page or several views. The information and behaviour below are requirements; their visual arrangement is yours. This freedom supersedes the older handoff's prescribed visual palette and styling restrictions.

Our pilot is X7R multilayer ceramic capacitors (MLCCs). The interface should later support other electronic components through configurable measurement profiles. A general interface does not mean one model can predict every component family.

The primary user is a test/QA engineer. Help them answer: Which components need attention? What evidence supports that? What may happen by 168 hours? What should I inspect next?

## 1. Essential workflow

Upload CSV → validate data → analyse measurements available through 24 hours → display anomalies and 168-hour predictions → inspect a component → export findings.

The live demo performs real inference using an already trained model. Show actual loading and errors. The interface must work with local assets and the local Python backend during the demonstration.

## 2. Shared dashboard information

| Area | Information to include |
|---|---|
| Dataset context | Filename, real/synthetic source label, component family, batch/lot IDs, unique component count, reading count, selected measurement, analysis cutoff (normally 24 h), forecast target (normally 168 h) |
| Readiness | Backend/model readiness, model version, supported profile, missing-data warnings; keep secondary technical details expandable |
| Summary | Counts for Accept, Monitor, Retest and Engineer Review; separate count for unscored components; components currently outside limits; components within limits but flagged as unusual |
| Results table | Component ID, batch, measurement and unit, latest reading, change since baseline, applicable limit, anomaly flag, predicted 168 h value, prediction interval, recommendation, short reason |
| Filters | Batch, measurement, recommendation, anomaly flag, data-quality issue; search by component ID |
| Selected component | Reading history, peer comparison, forecast, reasons, test conditions and next action |
| Export | Analysis cutoff, source, model version, measurements, predictions, uncertainty, recommendations and supporting reasons in a downloadable report/CSV |

Counts must refer to unique components or explicitly say they count measurement records. If multiple measurements produce conflicting recommendations, the backend must define the component-level aggregation rule.

## 3. MLCC measurements and context

Essential for the leakage pilot:

| Parameter | How to show it / why it matters |
|---|---|
| Component ID and batch/lot ID | Trace the part and identify its comparison group |
| Part number / X7R profile | Identify comparable capacitor specifications; show Unknown when absent |
| Elapsed test time, h | Distinguish 0 h and 24 h observations from the future 168 h target |
| Leakage current, nA or µA | Main pilot signal: current leaking through the capacitor; always show units |
| Approved leakage upper limit | Show the limit and its source/test conditions when supplied; never invent a universal threshold |
| Baseline-to-current change | Absolute change and, when baseline is valid and nonzero, percentage change |
| Average early drift | Change per hour between available readings; two points do not establish acceleration |
| Batch comparison | Similar parts' median and reference range, reference sample size and the selected part's position |
| 168 h leakage forecast | Predicted value and prediction interval, clearly separated from measurements |
| Recommendation and reasons | Accept / Monitor / Retest / Engineer Review, with concise measurement-based evidence |

Show the following only when supplied or validly derived; these are useful context, not mandatory invented CSV fields:

| Optional parameter | Display |
|---|---|
| Insulation resistance, MΩ or GΩ | Resistance to leakage; use its approved LOWER limit, where specified |
| Capacitance, nF or µF | Nominal value, measured value and deviation from nominal; tolerance if supplied |
| Dissipation factor, % or tan δ | Electrical loss measurement, with a consistent unit convention |
| Rated voltage and applied stress voltage, V | Keep the rating distinct from the actual test voltage |
| Stress temperature and measurement temperature, °C | Keep separate if readings were taken outside the burn-in chamber |
| Humidity, %RH | Environmental context when measured |
| Measurement voltage and settling time | Context for comparable leakage/insulation readings |
| Tester channel, fixture/board position, test run | Help investigate whether multiple anomalies share test equipment |

Insulation resistance and leakage are related by I = V/R under the relevant measurement conditions. Label converted values as derived; do not treat them as independent evidence or silently convert a manufacturer guarantee into a different guarantee.

## 4. General component version

Keep the workflow and common result fields. Replace MLCC-specific labels with a measurement profile containing:

- Component family, part number, component ID, batch and test protocol.
- Measurement name, unit, baseline, latest value, observation time and change.
- Lower limit, upper limit or permitted range, plus the source of that rule.
- Test conditions and the definition/sample size of a comparable peer group.
- Anomaly result, forecast target/value/interval, supporting reasons and recommendation.
- Data availability and whether the loaded model supports this family and measurement.

Example profiles to design for, subject to domain-approved test definitions:

| Family | Example measurements |
|---|---|
| MLCC | Leakage current, insulation resistance, capacitance, dissipation factor |
| Digital IC | Standby current/IDDQ, leakage current, propagation delay |
| Power transistor | Gate/drain leakage, threshold voltage, on-resistance |
| Sensor | Offset, sensitivity, noise |

Direction of concern belongs to the measurement profile. Increasing current, decreasing insulation resistance and deviation from an allowed threshold-voltage range need different rules. Do not pool raw values with different units or compare unrelated component families. An unsupported family should show available measurements and an explicit Prediction unavailable state.

## 5. Standout interactions, in priority order

1. **Within limits, still unusual.** A filter reveals components that pass the fixed threshold but are flagged relative to peers. Selecting one shows the measurement, threshold and peer distribution together. Describe this as early concern, not a confirmed defect.

2. **Freeze at 24 hours, reveal the outcome.** Mark the observation cutoff on the chart. Show 0/24 h measurements, a separate 168 h prediction marker and an interval whisker at 168 h. A separate Reveal recorded outcome action overlays actual 96/168 h readings, if the uploaded evaluation file contains them. Later readings must never enter the early prediction, peer reference or early explanation. Show prediction error after reveal. This demonstrates the claim directly.

3. **An evidence card for every flagged part.** Combine current condition, peer difference, forecast range, strongest available reasons and recommended follow-up. Make the card exportable. Engineers should understand it without knowing ML terminology.

4. **Uncertainty changes the action.** Visually distinguish a forecast interval entirely within limits, overlapping a limit, or entirely outside. Display the backend's recommendation. An anomaly score is not a percentage probability of failure. Label nominal interval coverage only when calibration metadata supports it.

Optional later feature: a board/fixture map showing whether anomalies cluster by channel or position. Only build this when real position metadata exists. Clustering suggests an investigation; it does not prove a tester fault or a physical defect.

## 6. Chart and explanation requirements

- Make measured and predicted values visibly different; label axes and units.
- Use a vertical 24 h cutoff and a labelled threshold/reference range.
- Two input points support a connecting segment, not an invented curved degradation history.
- A prediction interval for 168 h belongs at 168 h; do not draw a full future uncertainty band without time-specific forecasts.
- Peer bands describe the population; prediction intervals describe uncertainty. Give them different labels and styling.
- Do not claim water seepage, cracking or another physical cause from leakage alone. A cause investigation panel may show a hypothesis, supporting observations and the inspection needed to confirm it.
- Explanations of model inputs describe contribution, not proven physical causation.

## 7. UX and implementation boundaries

Design empty, upload-selected, processing, success, validation-error, backend-unavailable, missing-history and prediction-unavailable states. Preserve useful results for eligible components when the backend permits partial scoring, and identify unscored parts clearly. Never display missing values as zero or silently label an unscored part Accept.

Use readable units, keyboard access, visible focus, sufficient contrast and status labels alongside colours. Prioritise a laptop presentation view; disclose detailed diagnostics on demand. Avoid hard-coded results or fake processing percentages.

For implementation, retain React + TypeScript + Vite with the Python FastAPI backend. Existing UI/chart libraries are available; your visual signature is unrestricted. Frontend displays backend results and does not independently compute risk, predictions or recommendations.

The present result contract already exposes IDs, family, measurement, cutoff, current value, upper safety limit, anomaly scores/flag, reason codes, data-quality warning, recommendation and optional final prediction/lower/upper bounds. Several requested UI fields still require backend additions: raw trajectory, units, peer statistics, baseline/drift, test metadata, limit source/direction and export support. Confirm these against the actual API before wiring the design. Lower-limit and two-sided-limit decisions are planned extensions; the current decision code handles upper limits only.

Provide your proposed design, reusable components, interaction states and a clear list of missing API fields. Label any design-only sample data. Preserve synthetic-data labels in the working demo.

---

Implementation priority: complete upload → results table → selected-part evidence and forecast → outcome reveal. Add fixture mapping only after this path works reliably.

Research context: these are proposed product differentiators, not a claim that no industrial solution has them. Existing industrial platforms already offer statistical screening and test analytics.

Sources:
- [Murata: leakage current and insulation resistance](https://www.murata.com/en-global/support/faqs/capacitor/ceramiccapacitor/char/0039)
- [PDF Solutions: existing test analytics and statistical screening](https://www.pdf.com/products/exensio-analytics-platform/modules/test-operations/)
