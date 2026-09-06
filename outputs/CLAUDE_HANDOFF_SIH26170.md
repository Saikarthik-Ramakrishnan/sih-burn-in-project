# Claude handoff — SIH26170 parallel technical-lead task

Paste the prompt below into Claude Code with a copy of this project. If using
Git, ask Claude to work on a separate branch named `claude/anomaly-audit`.

---

You are collaborating on SIH26170: AI-driven anomaly detection in electronic
component burn-in and screening.

The current repository contains the anomaly core and its evaluation harness. Read
these files before acting:

- `README.md`
- `docs/technical_lead_plan.md`
- `src/sih26170/contracts.py`
- `src/sih26170/validation.py`
- `src/sih26170/features.py`
- `src/sih26170/anomaly.py`
- `src/sih26170/decision.py`
- `src/sih26170/synthetic.py`
- `src/sih26170/evaluation.py`
- `docs/evaluation_notes.md`
- all files under `tests/`

Current verified state: the local test command is `.venv/bin/pytest`, and 17
tests pass. The code uses Python, pandas, NumPy, and scikit-learn.

Your assignment is an independent correctness audit and sensitivity study. Do
not create a replacement detector, synthetic generator, or evaluation module.
Do not change public contracts unless a failing test demonstrates a genuine
defect.

Deliver the following:

1. Review feature calculations, label definitions, batch splitting, score
   calibration, and every metric for semantic or mathematical errors.
2. Verify independently that changing readings after `as_of_hour` cannot change
   fitted features, anomaly scores, or flags.
3. Run sensitivity experiments across at least three generator seeds, several
   Isolation Forest contamination values, and several robust thresholds.
4. Check whether one component family performs materially worse than the other
   and whether any raw-unit information accidentally enters the ML feature set.
5. Inspect false negatives and false positives by scenario and explain whether
   each failure is plausible, impossible to observe at that time, or a genuine
   model weakness.
6. Add focused regression tests for any real bug you find.
7. Produce `docs/claude_independent_audit.md` containing findings, experiment
   tables, recommended settings, and unresolved risks. Clearly state that all
   figures come from synthetic data.

Use simple deterministic parameter sweeps if sensitivity analysis is useful.
Bayesian optimisation is not required. Preserve the engineer-review model: the
software recommends actions but does not automatically certify or reject a
real component.

Prefer new audit scripts, tests, and documentation. If you believe an existing
module is incorrect, first add a failing regression test, then make the smallest
fix. Run the complete suite before handing the work back. Report changed files,
test results, exact commands, and any interface issue the main implementation
must resolve.

---

## Merge rule

Bring back Claude's audit notes, new experiments, and regression tests. Review
any proposed edits to existing source modules manually so the dashboard and
prediction interfaces do not drift.
