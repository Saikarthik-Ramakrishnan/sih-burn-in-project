import React from 'react';
import SquircleCard from '../common/SquircleCard';
import LeakageLensLogo from '../common/LeakageLensLogo';
import {
  FileSpreadsheet,
  FileCode,
  Download,
  CheckCircle2,
  Share2,
  FileText,
  Database
} from 'lucide-react';
import { exportToCsv, downloadJson } from '../../lib/utils';

export default function ExportView({ dataset }) {
  const records = dataset?.records || [];

  const handleExportFullCsv = () => {
    const rows = records.map(r => ({
      Component_ID: r.component_id,
      Batch_ID: r.batch_id,
      Family: r.component_family,
      Profile: r.profile_id,
      Initial_0h_uA: r.initial_value,
      Latest_24h_uA: r.latest_value,
      Delta_uA: r.absolute_change,
      Percent_Change: r.percent_change,
      Slope_Per_Hour: r.slope_per_hour,
      Applicable_Limit_uA: r.limits.applicable_limit,
      Anomaly_Flag: r.anomaly.is_anomaly ? 'TRUE' : 'FALSE',
      Anomaly_Score: r.anomaly.score,
      Robust_Deviation_Score: r.anomaly.robust_deviation_score,
      Peer_Robust_Z: r.peers.current_batch_robust_z,
      Peer_Sample_Size: r.peers.sample_size,
      Predicted_168h_uA: r.forecast.predicted_final_value,
      Interval_Lower_uA: r.forecast.prediction_lower,
      Interval_Upper_uA: r.forecast.prediction_upper,
      Interval_Nominal_Coverage: r.forecast.interval_nominal_coverage,
      Predicted_Limit_Cross: r.forecast.predicted_to_cross_limit ? 'TRUE' : 'FALSE',
      Recommendation: r.recommendation,
      Recommendation_Reasons: r.recommendation_reasons.join('; '),
      Observed_168h_uA: r.observed_168h || '',
      Crossed_Limit_At_168h: r.crossed_applicable_limit ? 'TRUE' : 'FALSE',
      Board_Position: r.context.board_position,
      Tester_Channel: r.context.tester_channel,
      Tester_ID: r.context.tester_id
    }));
    exportToCsv(`SIH26170_Screening_Summary_${new Date().toISOString().slice(0,10)}.csv`, rows);
  };

  const handleExportJson = () => {
    downloadJson(`SIH26170_Complete_Response_${new Date().toISOString().slice(0,10)}.json`, dataset);
  };

  const handleExportFlaggedOnly = () => {
    const flagged = records.filter(r => r.recommendation !== 'ACCEPT');
    const rows = flagged.map(r => ({
      Component_ID: r.component_id,
      Batch_ID: r.batch_id,
      Recommendation: r.recommendation,
      Reasons: r.recommendation_reasons.join('; '),
      Latest_24h_uA: r.latest_value,
      Limit_uA: r.limits.applicable_limit,
      Peer_Robust_Z: r.peers.current_batch_robust_z,
      Predicted_168h_uA: r.forecast.predicted_final_value,
      Interval_Upper_uA: r.forecast.prediction_upper,
      Board_Position: r.context.board_position
    }));
    exportToCsv(`Flagged_Components_Audit_${new Date().toISOString().slice(0,10)}.csv`, rows);
  };

  return (
    <div className="space-y-6 pb-12 max-w-5xl mx-auto">
      <div className="mb-2">
        <h2 className="text-xl font-display font-bold text-white tracking-tight flex items-center gap-2">
          <FileSpreadsheet className="w-5 h-5 text-orange-400" strokeWidth={1.5} />
          Audit &amp; Data Export Hub
        </h2>
        <p className="text-xs text-slate-400">
          Generate production audit logs, compliance evidence reports, and raw prediction JSON envelopes.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* Full CSV Report */}
        <SquircleCard elevated className="p-5 flex flex-col justify-between space-y-4">
          <div>
            <div className="w-9 h-9 rounded-lg bg-orange-500/10 border border-orange-500/20 flex items-center justify-center mb-3">
              <FileSpreadsheet className="w-4 h-4 text-orange-400" strokeWidth={1.5} />
            </div>
            <h3 className="text-sm font-display font-semibold text-white mb-1">
              Full Screening CSV Report
            </h3>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Contains all 64 screened components with baseline 0h, cutoff 24h, robust z-scores, 168h forecasts, and recommendations.
            </p>
          </div>

          <button
            onClick={handleExportFullCsv}
            className="btn-primary w-full py-2 flex items-center justify-center gap-2 text-xs font-mono tracking-wide"
          >
            <Download className="w-3.5 h-3.5" strokeWidth={1.5} />
            <span>Download Full CSV</span>
          </button>
        </SquircleCard>

        {/* Flagged Parts Audit Card */}
        <SquircleCard elevated className="p-5 flex flex-col justify-between space-y-4">
          <div>
            <div className="w-9 h-9 rounded-lg bg-orange-500/10 border border-orange-500/20 flex items-center justify-center mb-3">
              <FileText className="w-4 h-4 text-orange-400" strokeWidth={1.5} />
            </div>
            <h3 className="text-sm font-display font-semibold text-white mb-1">
              Flagged Items Audit Report
            </h3>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Filtered extract containing only components requiring MONITOR, RETEST, or ENGINEER REVIEW for QA technician disposition.
            </p>
          </div>

          <button
            onClick={handleExportFlaggedOnly}
            className="btn-secondary w-full py-2 flex items-center justify-center gap-2 text-xs font-mono tracking-wide"
          >
            <Download className="w-3.5 h-3.5" strokeWidth={1.5} />
            <span>Download Flagged Only</span>
          </button>
        </SquircleCard>

        {/* Raw JSON Envelope */}
        <SquircleCard elevated className="p-5 flex flex-col justify-between space-y-4">
          <div>
            <div className="w-9 h-9 rounded-lg bg-orange-500/10 border border-orange-500/20 flex items-center justify-center mb-3">
              <FileCode className="w-4 h-4 text-orange-400" strokeWidth={1.5} />
            </div>
            <h3 className="text-sm font-display font-semibold text-white mb-1">
              Full API JSON Envelope
            </h3>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Complete raw JSON matching the backend contract with metadata, TreeSHAP explanation vectors, and model verification details.
            </p>
          </div>

          <button
            onClick={handleExportJson}
            className="btn-secondary w-full py-2 flex items-center justify-center gap-2 text-xs font-mono tracking-wide"
          >
            <Download className="w-3.5 h-3.5" strokeWidth={1.5} />
            <span>Download Raw JSON</span>
          </button>
        </SquircleCard>
      </div>

      {/* Compliance Note with Leakage Lens Official Seal */}
      <SquircleCard className="p-4 font-mono text-xs text-slate-400">
        <div className="flex items-start gap-3.5">
          <div className="w-10 h-10 rounded-xl bg-orange-500/10 border border-orange-500/25 flex items-center justify-center shrink-0 shadow-[0_0_12px_rgba(249,115,22,0.15)] mt-0.5">
            <LeakageLensLogo className="w-6 h-6" showGlow />
          </div>
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-slate-200 font-semibold uppercase text-[11px]">
                Leakage Lens Verified Audit &amp; Traceability
              </span>
              <span className="text-[9px] px-1.5 py-0.2 rounded bg-orange-500/15 text-orange-300 border border-orange-500/25">
                SIH26170
              </span>
            </div>
            <p className="leading-relaxed text-[11px] text-slate-400">
              Exported records adhere to SIH26170 standard field definitions. Every forecast includes its model version identifier (<strong className="text-white">xgboost_v2</strong>) and bundle id (<strong className="text-white">b5553f6f7032092e-s26170</strong>). All reported prediction intervals represent nominal coverage calibrated offline on held-out whole-batch splits.
            </p>
          </div>
        </div>
      </SquircleCard>
    </div>
  );
}
