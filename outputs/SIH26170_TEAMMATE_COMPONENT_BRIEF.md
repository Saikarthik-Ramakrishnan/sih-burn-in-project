# SIH26170 - Simple Team Brief

## What is the problem?

Electronic components are tested under heat for many hours before being used in
spacecraft. This is called **burn-in testing**.

Today, a component usually passes if its final value stays below a fixed limit.
But a defective component may still be below the limit while changing much
faster than the other components in its manufacturing batch.

Our system must:

1. find these unusual components early; and
2. use the 0-hour and 24-hour readings to predict the 168-hour value.

## Which component are we focusing on?

**X7R multilayer ceramic capacitors (MLCCs).**

These small capacitors are used for filtering and stabilising power in
spacecraft, vehicles and other electronic systems.

## Why did we choose MLCCs?

- One cracked capacitor can short or disturb an important power line.
- NASA reports that ordinary final measurements can miss some cracked MLCCs.
- NASA recommends monitoring leakage current throughout burn-in.
- MLCC burn-in can last about **168 hours**, which matches the SIH problem.
- Existing equipment performs testing and inspection, but there is still room
  for a simple tool that predicts each capacitor's final result from early data.

## What will our solution do?

A QA engineer uploads a burn-in CSV file. The system then:

1. checks whether the file and measurements are valid;
2. compares every capacitor only with similar capacitors from its own batch;
3. detects unusual leakage behaviour;
4. predicts the leakage current at 168 hours;
5. shows a prediction range to communicate uncertainty;
6. explains why a capacitor was flagged; and
7. recommends **Accept, Monitor, Retest, or Engineer Review**.

## What data will we use?

The main measurement is **leakage current**.

Important CSV fields:

- capacitor ID and manufacturing batch;
- time: 0, 24, 96 and 168 hours;
- leakage current or insulation resistance;
- capacitance and dissipation factor;
- temperature and applied voltage;
- humidity; and
- tester channel or board position.

## What makes our solution different?

Existing systems mostly apply the heat/electrical stress, inspect components,
or check fixed limits.

Our system adds a vendor-neutral intelligence layer that:

- works with an ordinary CSV export;
- finds abnormal drift before the fixed limit is crossed;
- predicts the final 168-hour measurement;
- compares components fairly within their own batch; and
- gives a clear explanation instead of only a black-box score.

## Important limitation

The system helps a QA engineer make a decision. It does **not** automatically
certify a component for spaceflight.

Electrical data can suggest patterns such as moisture-related leakage or
possible cracking, but the physical cause must be confirmed using inspection,
retesting or failure analysis.

## One-line project pitch

> We detect abnormal leakage in MLCC capacitors after only 24 hours and predict
> their 168-hour burn-in result, helping engineers identify risky components
> earlier without replacing existing test equipment.

## Sources

- SIH26170 problem statement: <https://www.sih.gov.in/sih2026PS>
- NASA MLCC screening analysis: <https://nepp.nasa.gov/docs/tasks/007-Capacitors-Evaluation/NEPP-CP-2024-Teverovsky-JEDEC-May-Presentation-MLCCs-20240003605.pdf>
- MLCC failure-time prediction study: <https://doi.org/10.1063/5.0158360>

