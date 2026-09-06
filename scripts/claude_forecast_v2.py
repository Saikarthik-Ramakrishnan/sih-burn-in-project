"""Claude v2 forecasting experiment runner (training batches only).

Usage (from the extracted pack root, with the pack's virtual environment):

    python scripts/claude_forecast_v2.py validate
    python scripts/claude_forecast_v2.py predeclare
    python scripts/claude_forecast_v2.py experiment
    python scripts/claude_forecast_v2.py intervals --config <name>
    python scripts/claude_forecast_v2.py fit-final --config <name>
    python scripts/claude_forecast_v2.py all --final-config <name>

``experiment`` refuses to run unless ``predeclare`` has recorded the exact
configuration list first (digest check), so the comparison cannot be edited
after results are seen without leaving a trace.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd  # noqa: E402

from sih26170 import forecast_v2 as fv2  # noqa: E402


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _log(message: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {message}", flush=True)


def _load(args: argparse.Namespace) -> fv2.TrainingData:
    _log(f"loading training pack from {args.data_dir}")
    training = fv2.load_training_data(args.data_dir)
    _log(f"{training.validation['components']} components in {training.validation['batches']} batches")
    return training


def cmd_validate(args: argparse.Namespace) -> None:
    training = _load(args)
    payload = {"recorded_at": _stamp(), "input_sha256": training.input_hashes, "environment": fv2.environment_record(), **training.validation}
    fv2.write_json(args.output_dir / "data_validation.json", payload)
    folds = fv2.assign_batch_folds(training.features, n_splits=args.folds)
    fv2.assert_folds_disjoint(training.features, folds)
    folds.to_csv(args.output_dir / "fold_assignment.csv", index=False)
    _log(f"wrote data_validation.json and fold_assignment.csv to {args.output_dir}")
    print(json.dumps({k: payload[k] for k in ("components", "batches", "observed_final_crossing_count", "already_at_or_above_limit_at_24h")}, indent=2))


def cmd_predeclare(args: argparse.Namespace) -> None:
    path = args.output_dir / "PREDECLARED_COMPARISON.json"
    if path.exists() and not args.force:
        raise SystemExit(f"{path} already exists; the comparison is frozen (use --force only to restart the experiment from scratch and say so in STATUS.md)")
    configs = fv2.PREDECLARED_CONFIGS
    payload = {
        "recorded_at": _stamp(),
        "rule": "This list was fixed before scripts/claude_forecast_v2.py experiment was run. Any later change requires a new predeclaration and must be disclosed.",
        "selection_rule": fv2.SELECTION_RULE,
        "folds": args.folds,
        "seed": args.seed,
        "config_digest": fv2.config_digest(configs),
        "configs": [c.to_dict() for c in configs],
        "feature_sets": fv2.FEATURE_SETS,
        "provenance": fv2.provenance_record(),
        "provenance_digest": fv2.provenance_digest(),
    }
    fv2.write_json(path, payload)
    lines = ["# Predeclared forecasting comparison", "", f"Recorded {payload['recorded_at']}. Digest `{payload['config_digest'][:16]}`. {len(configs)} configurations including baselines.", "", payload["rule"], "", "## Selection rule", "", fv2.SELECTION_RULE, "", "| # | name | model | objective | target | feature set | note |", "|---|---|---|---|---|---|---|"]
    for i, c in enumerate(configs, 1):
        lines.append(f"| {i} | `{c.name}` | {c.model} | {c.objective or '-'} | {c.target} | {c.feature_set} | {c.description} |")
    lines += ["", "## Feature sets", ""]
    for name, columns in fv2.FEATURE_SETS.items():
        lines.append(f"- `{name}` ({len(columns)}): {', '.join(columns)}")
    lines += ["", "XGBoost hyperparameters are v1's, unchanged for every configuration: " + json.dumps(fv2.V1_XGB_PARAMS) + ". No tuning is part of this comparison."]
    (args.output_dir / "PREDECLARED_COMPARISON.md").write_text("\n".join(lines) + "\n")
    _log(f"predeclared {len(configs)} configurations, digest {payload['config_digest'][:16]}")


def _check_predeclared(args: argparse.Namespace) -> dict:
    path = args.output_dir / "PREDECLARED_COMPARISON.json"
    if not path.exists():
        raise SystemExit("run `predeclare` first: the comparison must be recorded before it is executed")
    recorded = json.loads(path.read_text())
    if recorded["config_digest"] != fv2.config_digest(fv2.PREDECLARED_CONFIGS):
        raise SystemExit("PREDECLARED_CONFIGS changed after predeclaration; re-run predeclare --force and disclose the change")
    if "provenance_digest" in recorded and recorded["provenance_digest"] != fv2.provenance_digest():
        raise SystemExit("Shared hyperparameters or feature/interval constants changed after predeclaration; re-run predeclare --force and disclose the change")
    current = fv2.provenance_record()["source_sha256"]
    drift = sorted(name for name, digest in recorded.get("provenance", {}).get("source_sha256", {}).items() if current.get(name) != digest)
    if drift:
        _log(f"WARNING: source files changed since predeclaration: {', '.join(drift)}; results must be reproduced and the change disclosed")
    recorded["source_changed_since_predeclaration"] = drift
    return recorded


def cmd_experiment(args: argparse.Namespace) -> None:
    recorded = _check_predeclared(args)
    training = _load(args)
    folds = fv2.assign_batch_folds(training.features, n_splits=args.folds)
    fv2.assert_folds_disjoint(training.features, folds)
    started = time.time()
    results, oof = fv2.run_cross_validation(training, fv2.PREDECLARED_CONFIGS, folds, seed=args.seed, n_jobs=args.n_jobs, log=_log)
    results.update({
        "recorded_at": _stamp(), "runtime_seconds": time.time() - started, "seed": args.seed, "folds": args.folds,
        "predeclaration": {"recorded_at": recorded["recorded_at"], "config_digest": recorded["config_digest"], "provenance_digest": recorded.get("provenance_digest"), "source_changed_since_predeclaration": recorded.get("source_changed_since_predeclaration", [])},
        "provenance": fv2.provenance_record(),
        "input_sha256": training.input_hashes, "environment": fv2.environment_record(),
        "selection_rule": fv2.SELECTION_RULE,
        "note": "Development results on training-batch folds; not final validation. Codex evaluates independently on untouched batches.",
    })
    fv2.write_json(args.output_dir / "cv_results.json", results)
    oof.to_csv(args.output_dir / "oof_predictions.csv", index=False)
    table = fv2.comparison_table(results)
    table.to_csv(args.output_dir / "comparison_table.csv", index=False)
    fv2.profile_table(results).to_csv(args.output_dir / "comparison_by_profile.csv", index=False)
    fv2.scenario_table(results).to_csv(args.output_dir / "comparison_by_scenario.csv", index=False)
    fv2.stratum_table(results).to_csv(args.output_dir / "comparison_by_stratum.csv", index=False)
    _write_comparison_markdown(args.output_dir, results, table)
    pd.set_option("display.width", 250)
    print(table[["config", "mae_norm_pooled", "mae_norm_fold_mean", "mae_norm_fold_std", "folds_beating_persistence", "batches_beating_persistence", "paired_batch_delta_mean", "paired_batch_delta_se", "train_mae_norm_fold_mean", "mae_ua_pooled", "healthy_mae_norm", "nonhealthy_mae_norm", "crossing_recall", "crossing_fpr", "crossing_tp", "crossing_fp", "new_crossing_tp", "share_clipped_at_zero"]].to_string(index=False))
    _log(f"experiment finished in {time.time() - started:.1f}s; outputs in {args.output_dir}")


def _write_comparison_markdown(output_dir: Path, results: dict, table: pd.DataFrame) -> None:
    lines = ["# Cross-validated comparison (training batches only)", "", f"Recorded {results['recorded_at']}; seed {results['seed']}; {results['folds']} profile-stratified whole-batch folds; predeclaration digest `{results['predeclaration']['config_digest'][:16]}`.", "", "Development results, not final validation. Lower MAE is better. Signed error is prediction minus observed. Recall/FPR use the point forecast >= limit against the observed 168 h crossing; 'new' restricts to parts below the limit at 24 h; 'latent' uses is_future_failure and excludes tester-fault parts. 'batches' counts the 36 whole batches where the configuration's MAE is below persistence's; the paired delta is the per-batch MAE difference to persistence (negative is better) with its standard error.", "", "| config | MAE norm (pooled) | fold mean ± std | folds < pers | batches < pers | paired Δ vs pers (SE) | train MAE | MAE µA | healthy MAE | non-healthy MAE | mean signed err | crossing recall | crossing FPR | tp/fn/fp/tn | new recall (tp/fp) | latent recall (no tester) | clipped at 0 |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for _, r in table.iterrows():
        lines.append(f"| `{r['config']}` | {r['mae_norm_pooled']:.4f} | {r['mae_norm_fold_mean']:.4f} ± {r['mae_norm_fold_std']:.4f} | {r['folds_beating_persistence']}/{results['folds']} | {r['batches_beating_persistence']}/{r['batches_total']} | {r['paired_batch_delta_mean']:+.4f} ({r['paired_batch_delta_se']:.4f}) | {r['train_mae_norm_fold_mean']:.4f} | {r['mae_ua_pooled']:.4f} | {r['healthy_mae_norm']:.4f} | {r['nonhealthy_mae_norm']:.4f} | {r['mean_signed_error']:+.4f} | {r['crossing_recall']:.3f} | {r['crossing_fpr']:.4f} | {r['crossing_tp']}/{r['crossing_fn']}/{r['crossing_fp']}/{r['crossing_tn']} | {r['new_crossing_recall']:.3f} ({r['new_crossing_tp']}/{r['new_crossing_fp']}) | {'n/a' if r['latent_recall_no_tester'] is None else f"{r['latent_recall_no_tester']:.3f}"} | {r['share_clipped_at_zero']:.4f} |")
    lines += ["", "## Per-fold normalized MAE", "", "| config | " + " | ".join(f"fold {k}" for k in range(results['folds'])) + " |", "|---|" + "---|" * results["folds"]]
    for name, entry in results["configs"].items():
        lines.append(f"| `{name}` | " + " | ".join(f"{v:.4f}" for v in entry["fold_summary"]["mae_normalized"]["per_fold"]) + " |")
    lines += ["", "## MAE in µA by profile (pooled out-of-fold)", ""]
    profiles = sorted(next(iter(results["configs"].values()))["pooled"].get("by_profile", {}).keys())
    lines += ["| config | " + " | ".join(profiles) + " |", "|---|" + "---|" * len(profiles)]
    for name, entry in results["configs"].items():
        lines.append(f"| `{name}` | " + " | ".join(f"{entry['pooled']['by_profile'][p]['mae_ua']:.4f}" for p in profiles) + " |")
    strata = fv2.stratum_table(results)
    if not strata.empty:
        names = [s_ for s_ in fv2.STRATA_ORDER if s_ in set(strata["stratum"])]
        lines += ["", "## Normalized MAE by retrospective stratum (labels used only to explain errors)", "", "Counts: " + ", ".join(f"{n} = {int(strata.loc[strata['stratum'] == n, 'components'].iloc[0])}" for n in names), "", "| config | " + " | ".join(names) + " |", "|---|" + "---|" * len(names)]
        for name in results["configs"]:
            sub = strata.loc[strata["config"] == name].set_index("stratum")
            lines.append(f"| `{name}` | " + " | ".join(f"{sub.loc[n, 'mae_normalized']:.4f} ({sub.loc[n, 'mean_signed_error']:+.3f})" for n in names) + " |")
        lines += ["", "Cell format: MAE (mean signed error). Strata are mutually exclusive with tester-fault priority: the 45 parts flagged both defect and tester fault are counted as tester faults (so the two defect strata sum to 1,386 of 1,431 is_defect parts) and are excluded from the latent-crossing metric."]
    lines += ["", "## Normalized MAE by simulated scenario (retrospective explanation only)", ""]
    scenarios = sorted(next(iter(results["configs"].values()))["pooled"].get("by_scenario_mae_normalized", {}).keys())
    lines += ["| config | " + " | ".join(scenarios) + " |", "|---|" + "---|" * len(scenarios)]
    for name, entry in results["configs"].items():
        lines.append(f"| `{name}` | " + " | ".join(f"{entry['pooled']['by_scenario_mae_normalized'][s]['mae_normalized']:.4f}" for s in scenarios) + " |")
    (output_dir / "COMPARISON.md").write_text("\n".join(lines) + "\n")


def _config_by_name(name: str) -> fv2.CandidateConfig:
    for config in fv2.PREDECLARED_CONFIGS:
        if config.name == name:
            return config
    raise SystemExit(f"unknown configuration {name}; choose one of {[c.name for c in fv2.PREDECLARED_CONFIGS]}")


def cmd_intervals(args: argparse.Namespace) -> None:
    training = _load(args)
    folds = fv2.assign_batch_folds(training.features, n_splits=args.folds)
    for name in args.config:
        config = _config_by_name(name)
        _log(f"interval experiment for {name} (alpha={args.alpha}, {args.calibration_batches_per_profile} calibration batches per profile)")
        report = fv2.run_interval_experiment(training, config, folds, alpha=args.alpha, calibration_batches_per_profile=args.calibration_batches_per_profile, seed=args.seed, n_jobs=args.n_jobs, log=_log)
        report.update({"recorded_at": _stamp(), "input_sha256": training.input_hashes, "environment": fv2.environment_record()})
        fv2.write_json(args.output_dir / f"interval_experiment__{name}.json", report)
        for method, summary in report["methods"].items():
            print(f"{name:28s} {method:24s} coverage {summary['coverage_mean']:.3f} ± {summary['coverage_std']:.3f} (min {summary['coverage_min']:.3f}) | healthy {summary['coverage_healthy_mean']:.3f} non-healthy {summary['coverage_nonhealthy_mean']:.3f} | median width {summary['median_width_normalized_mean']:.3f} | upper<limit share {summary['share_upper_below_limit_mean']:.3f}")


def cmd_fit_final(args: argparse.Namespace) -> None:
    recorded = _check_predeclared(args)
    results_path = args.output_dir / "cv_results.json"
    if not results_path.exists():
        raise SystemExit("run `experiment` before fitting a final candidate")
    results = json.loads(results_path.read_text())
    config = _config_by_name(args.config)
    training = _load(args)
    entry = results["configs"][config.name]
    reference = {"cv_results": str(results_path.name), "predeclaration_digest": recorded["config_digest"], "pooled_mae_normalized": entry["pooled"]["mae_normalized"], "fold_mae_normalized": entry["fold_summary"]["mae_normalized"], "persistence_pooled_mae_normalized": results["configs"].get("persistence", {}).get("pooled", {}).get("mae_normalized")}
    candidate = fv2.fit_final_candidate(training, config, seed=args.seed, n_jobs=args.n_jobs, experiment_reference=reference)
    target_dir = args.output_dir / "candidate" / config.name
    if (target_dir / "manifest.json").exists() and not args.force:
        raise SystemExit(f"{target_dir} already holds a candidate; use --force to overwrite")
    fv2.save_forecast_candidate(candidate, target_dir)
    reloaded = fv2.load_forecast_candidate(target_dir)
    early = fv2.read_identity_csv(Path(args.data_dir) / "train_early.csv")
    first_batch = early.loc[early["batch_id"].eq(sorted(early["batch_id"].unique())[0])]
    preview = reloaded.predict(first_batch)
    preview.head(20).to_csv(args.output_dir / f"predict_preview__{config.name}.csv", index=False)
    stale = target_dir / "predict_preview_first_training_batch.csv"
    if stale.exists():
        stale.unlink()
    _log(f"saved candidate {config.name} to {target_dir}; preview of {len(preview)} forecasts written ({preview['status'].value_counts().to_dict()})")


def cmd_seed_check(args: argparse.Namespace) -> None:
    training = _load(args)
    folds = fv2.assign_batch_folds(training.features, n_splits=args.folds)
    config = _config_by_name(args.config)
    report = fv2.run_seed_check(training, config, folds, seeds=args.seeds, n_jobs=args.n_jobs)
    report.update({"recorded_at": _stamp(), "note": "post-selection stochastic-spread read-out; not used for selection"})
    fv2.write_json(args.output_dir / f"seed_check__{config.name}.json", report)
    print(json.dumps(report["pooled_mae_normalized_spread"], indent=2))


def cmd_prevalence_check(args: argparse.Namespace) -> None:
    training = _load(args)
    folds = fv2.assign_batch_folds(training.features, n_splits=args.folds)
    configs = [_config_by_name(name) for name in args.config]
    report = fv2.run_prevalence_readout(training, configs, folds, keep_fraction=args.keep_fraction, seed=args.seed, n_jobs=args.n_jobs)
    report.update({"recorded_at": _stamp(), "note": "robustness read-out with defect prevalence reduced in the training portion only; labels used to subsample training rows for this diagnostic, never as features; not a selection criterion"})
    fv2.write_json(args.output_dir / "prevalence_readout.json", report)
    for name, m in report["configs"].items():
        print(f"{name:28s} MAE {m['mae_normalized']:.4f} healthy MAE {m['healthy_mae_normalized']:.4f} healthy signed {m['healthy_mean_signed_error_normalized']:+.4f} recall {m['crossing_recall']:.3f} fp {m['crossing_fp']}")


def cmd_all(args: argparse.Namespace) -> None:
    cmd_validate(args)
    if not (args.output_dir / "PREDECLARED_COMPARISON.json").exists():
        cmd_predeclare(args)
    cmd_experiment(args)
    args.config = [args.final_config] + [c for c in args.interval_configs if c != args.final_config]
    cmd_intervals(args)
    args.config = args.final_config
    cmd_fit_final(args)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/claude_forecast_v2"))
    parser.add_argument("--folds", type=int, default=fv2.DEFAULT_FOLDS)
    parser.add_argument("--seed", type=int, default=fv2.DEFAULT_SEED)
    parser.add_argument("--n-jobs", type=int, default=4)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate").set_defaults(func=cmd_validate)
    p = sub.add_parser("predeclare"); p.add_argument("--force", action="store_true"); p.set_defaults(func=cmd_predeclare)
    sub.add_parser("experiment").set_defaults(func=cmd_experiment)
    p = sub.add_parser("intervals"); p.add_argument("--config", nargs="+", required=True); p.add_argument("--alpha", type=float, default=0.1); p.add_argument("--calibration-batches-per-profile", type=int, default=2); p.set_defaults(func=cmd_intervals)
    p = sub.add_parser("fit-final"); p.add_argument("--config", required=True); p.add_argument("--force", action="store_true"); p.set_defaults(func=cmd_fit_final)
    p = sub.add_parser("seed-check"); p.add_argument("--config", required=True); p.add_argument("--seeds", nargs="+", type=int, default=[1, 2, 3]); p.set_defaults(func=cmd_seed_check)
    p = sub.add_parser("prevalence-check"); p.add_argument("--config", nargs="+", required=True); p.add_argument("--keep-fraction", type=float, default=0.5); p.set_defaults(func=cmd_prevalence_check)
    p = sub.add_parser("all"); p.add_argument("--final-config", required=True); p.add_argument("--interval-configs", nargs="*", default=["persistence"]); p.add_argument("--alpha", type=float, default=0.1); p.add_argument("--calibration-batches-per-profile", type=int, default=2); p.add_argument("--force", action="store_true"); p.set_defaults(func=cmd_all)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.func(args)


if __name__ == "__main__":
    main()
