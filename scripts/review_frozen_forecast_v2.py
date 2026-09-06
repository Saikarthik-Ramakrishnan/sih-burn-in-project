"""Independent, non-training review of Claude's frozen candidate snapshot."""
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
SNAP = ROOT / 'work/ml_v2_review'
sys.path.insert(0, str(SNAP / 'src'))

import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits
from sih26170 import forecast_v2 as v2
from sih26170.mlcc_prototype import FORECAST_COLUMNS, GROUP_COLUMNS, prepare_early_features, load_bundle
from sih26170.mlcc_synthetic import generate_mlcc_dataset


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, data):
    path.write_text(json.dumps(v2._json_safe(data), indent=2, allow_nan=False) + '\n')


def interval_metrics(y, pred, features, labels, bounds):
    strata = v2.stratum_index(features)
    margins = np.array([bounds[int(s)] for s in strata])
    lo = np.maximum(0, pred + margins[:, 0])
    hi = np.maximum(0, pred + margins[:, 1])
    upper = np.maximum(0, pred + margins[:, 2])
    if np.any(lo > hi):
        raise ValueError('Invalid calibrated interval ordering')
    covered = (y >= lo) & (y <= hi)
    def metrics(mask):
        return {'components': int(mask.sum()), 'coverage': float(covered[mask].mean()),
                'mean_width_normalized': float((hi-lo)[mask].mean()),
                'one_sided_upper_coverage': float((y <= upper)[mask].mean())}
    result = metrics(np.ones(len(y), bool))
    result['by_batch'] = {str(k): metrics(features.batch_id.eq(k).to_numpy()) for k in sorted(features.batch_id.unique())}
    result['by_profile'] = {str(k): metrics(features.profile_id.eq(k).to_numpy()) for k in sorted(features.profile_id.unique())}
    result['by_stratum'] = {str(k): metrics(strata == k) for k in np.unique(strata)}
    for name, mask in [('healthy', labels.is_healthy.to_numpy(bool)), ('nonhealthy', ~labels.is_healthy.to_numpy(bool))]:
        if mask.any(): result[name] = metrics(mask)
    return result, lo, hi, upper


def main():
    out = ROOT / 'outputs/codex_ml_v2_review'
    out.mkdir(exist_ok=False)
    data = ROOT / 'outputs/mlcc_v1'
    candidate = v2.load_forecast_candidate(SNAP / 'candidate')
    old = load_bundle(data / 'model_bundle')
    tracked = list((SNAP / 'src').glob('sih26170/*.py')) + list((SNAP / 'candidate').iterdir())
    hashes = {str(p.relative_to(ROOT)): digest(p) for p in tracked if p.is_file()}
    claude_root = ROOT.parent / 'claude_forecast_v2_pack'
    source_hashes = {str(p): digest(p) for p in [claude_root / 'src/sih26170/forecast_v2.py', claude_root / 'tests/test_forecast_v2.py', *list((claude_root / 'outputs/claude_forecast_v2/candidate/xgb_abs_resid_leak').glob('model.*'))]}
    for name, expected in candidate.manifest['training']['input_sha256'].items():
        if digest(data / name) != expected: raise ValueError(f'Training hash mismatch: {name}')
    train_ids = pd.read_csv(data / 'train_labels.csv', usecols=['batch_id', 'component_id'])
    baseline_hashes = {str(p.relative_to(ROOT)): digest(p) for p in (data / 'model_bundle').iterdir() if p.is_file()}
    audit = {'candidate': candidate.manifest['config']['name'], 'snapshot_sha256': hashes,
             'claude_source_sha256': source_hashes, 'production_bundle_sha256': baseline_hashes,
             'protocol_sha256': digest(SNAP / 'OWNERSHIP_AND_PLAN.md'), 'models_refitted': False,
             'full_snapshot_tests': '114 passed', 'source_training_hashes_verified': True}
    dump(out / 'provenance.json', audit)
    seen_batches, seen_devices = set(train_ids.batch_id), set(train_ids.component_id)
    def prepare(name, readings, labels):
        nonlocal seen_batches, seen_devices
        if set(readings.batch_id) & seen_batches or set(readings.component_id) & seen_devices:
            raise ValueError(f'Overlapping identities in {name}')
        seen_batches |= set(readings.batch_id)
        seen_devices |= set(readings.component_id)
        f, early, invalid = prepare_early_features(readings)
        if invalid: raise ValueError(f'{name}: invalid components')
        f = f.sort_values(GROUP_COLUMNS).reset_index(drop=True)
        profiles = early.drop_duplicates('component_id').set_index('component_id').profile_id
        f['profile_id'] = f.component_id.map(profiles)
        if not f.profile_id.isin(candidate.manifest['supported_profiles']).all(): raise ValueError('Unsupported profile')
        y = f[GROUP_COLUMNS].merge(labels, on=GROUP_COLUMNS, how='left', validate='one_to_one')
        if len(y) != len(labels) or not np.isfinite(y.final_value).all(): raise ValueError('Invalid label join')
        y['y_normalized'] = y.final_value / f.upper_limit.to_numpy()
        # Use the exact saved preprocessing/predict implementation once per dataset.
        with threadpool_limits(limits=1):
            pred = candidate._fitted().predict_normalized(f)
            old_pred = np.maximum(0, old.models['xgboost'].predict(old.imputer.transform(f[FORECAST_COLUMNS])))
        return f, y, pred, old_pred
    def read_set(name):
        return (pd.read_csv(data / f'{name}_early.csv', dtype={'package_code': str}),
                pd.read_csv(data / f'{name}_labels.csv'))
    print('Calibrating frozen candidate on calibration batches only...', flush=True)
    cal_r, cal_l = read_set('calibration')
    cf, cy, cp, _ = prepare('calibration', cal_r, cal_l)
    bounds = v2.stratified_signed_bounds(cy.y_normalized.to_numpy()-cp, v2.stratum_index(cf), 0.1)
    dump(out / 'candidate_calibration.json', {
        'candidate_model_sha256': digest(SNAP / 'candidate/model.ubj'),
        'calibration_input_sha256': {n: digest(data / n) for n in ['calibration_early.csv','calibration_labels.csv']},
        'batch_ids': sorted(cf.batch_id.unique()), 'components': len(cf), 'alpha': 0.1,
        'signed_slope_z_edges': [2,5], 'stratum_counts': pd.Series(v2.stratum_index(cf)).value_counts().to_dict(),
        'margins_normalized_lower_upper_one_sided': bounds,
        'warning': 'Empirical synthetic coverage only; dependent batch observations limit guarantees.'})
    # One complete calibration batch checks public inference and private evaluation path agree.
    probe = cal_r.loc[cal_r.batch_id.eq(cal_r.batch_id.iloc[0])]
    public = candidate.predict(probe).sort_values(GROUP_COLUMNS).reset_index(drop=True)
    fp, _, bad = prepare_early_features(probe)
    fp = fp.sort_values(GROUP_COLUMNS).reset_index(drop=True)
    if bad or not public.status.eq('forecast').all(): raise ValueError('Public inference unavailable')
    np.testing.assert_allclose(public.predicted_normalized, candidate._fitted().predict_normalized(fp), rtol=1e-7)
    print('Public inference equivalence passed. Generating one fresh 4,000-component evaluation set...', flush=True)
    fresh = generate_mlcc_dataset(seed=20260906, n_batches=20, components_per_batch=200, identity_prefix='V2AUDIT20260906')
    fresh_r = fresh.readings.loc[fresh.readings.hours.isin([0,24])].copy()
    fresh_r.to_csv(out / 'fresh_early.csv', index=False)
    fresh.labels.to_csv(out / 'fresh_labels.csv', index=False)
    dump(out / 'fresh_generation.json', {'seed':20260906,'batches':20,'components':4000,
        'generator_sha256':digest(SNAP / 'src/sih26170/mlcc_synthetic.py'),
        'use':'All generated batches evaluation-only; generator split annotations not used for fitting.',
        'files':{n:digest(out/n) for n in ['fresh_early.csv','fresh_labels.csv']}})
    summaries = []
    for name in ['test','stress_low_prevalence','stress_unseen_condition','fresh']:
        print(f'Evaluating {name} (no training)...', flush=True)
        readings, labels = (fresh_r, fresh.labels) if name == 'fresh' else read_set(name)
        f, y, pred, old_pred = prepare(name, readings, labels)
        actual = y.y_normalized.to_numpy()
        forecasts = {'persistence':f.limit_fraction.to_numpy(), 'v1_xgboost':old_pred, 'v2_candidate':pred}
        result = {'data_role':'fresh synthetic evaluation' if name == 'fresh' else 'previously available synthetic diagnostic set',
                  'input_sha256': {f'{name}_{kind}.csv':digest(data/f'{name}_{kind}.csv') for kind in ['early','labels']} if name != 'fresh' else {},
                  'models': {k:v2.forecast_metrics(p,f,y) for k,p in forecasts.items()}}
        result['v2_calibrated_intervals'], lo, hi, upper = interval_metrics(actual,pred,f,y,bounds)
        row = f[GROUP_COLUMNS+['profile_id','upper_limit']].copy()
        row['observed_final_ua'] = y.final_value
        for k,p in forecasts.items(): row[k+'_ua'] = p*f.upper_limit.to_numpy()
        row['v2_lower_ua'], row['v2_upper_ua'], row['v2_one_sided_upper_ua'] = [a*f.upper_limit.to_numpy() for a in [lo,hi,upper]]
        row['paired_abs_error_delta_normalized'] = np.abs(pred-actual)-np.abs(f.limit_fraction.to_numpy()-actual)
        per_batch = row.groupby('batch_id').paired_abs_error_delta_normalized.mean()
        result['v2_vs_persistence_batch_delta'] = {'mean':float(per_batch.mean()), 'se':float(per_batch.std(ddof=1)/np.sqrt(len(per_batch))), 'batches_improved':int((per_batch<0).sum()), 'batches':len(per_batch)}
        with threadpool_limits(limits=1):
            anomaly = old.detector.score(f)
        # Future crossing is only one retrospective target for anomaly warnings, not their definition.
        result['unchanged_anomaly_detector'] = {'observed_final_crossing':v2._confusion(actual>=1,anomaly.is_anomaly.to_numpy(bool)),
            'healthy_alerts':int((anomaly.is_anomaly.to_numpy(bool)&y.is_healthy.to_numpy(bool)).sum()),
            'healthy_components':int(y.is_healthy.sum())}
        row.to_csv(out / f'{name}_predictions.csv', index=False)
        dump(out / f'{name}_evaluation.json', result)
        for k,m in result['models'].items():
            summaries.append({'dataset':name,'model':k,'mae_normalized':m['mae_normalized'],
                'healthy_mae':m['healthy_mae_normalized'], 'recall':m['observed_final_crossing']['recall'],
                'false_positives':m['observed_final_crossing']['fp'],
                'new_crossing_recall':m['new_observed_crossing_below_limit_at_24h']['recall']})
        print(json.dumps(summaries[-3:]), flush=True)
    for name,h in {**hashes,**baseline_hashes}.items():
        if digest(ROOT/name)!=h: raise ValueError(f'Snapshot or production changed during review: {name}')
    changed = [p for p,h in source_hashes.items() if digest(Path(p))!=h]
    dump(out / 'completion.json', {'completed':True,'production_unchanged':True,'claude_source_changes_during_run':changed,
        'candidate_public_inference_equivalence':'passed','training_runs':0,'production_promoted':False})
    pd.DataFrame(summaries).to_csv(out / 'comparison.csv', index=False)
    print(f'Completed: {out}', flush=True)


if __name__ == '__main__':
    main()
