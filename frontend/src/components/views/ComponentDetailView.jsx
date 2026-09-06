import React, { useState } from 'react';
import SquircleCard from '../common/SquircleCard';
import DecisionBadge from '../common/DecisionBadge';
import TrajectoryChart from '../charts/TrajectoryChart';
import {
  Eye,
  EyeOff,
  Download,
  Activity,
  Layers,
  Sparkles,
  Info,
  Cpu,
  Thermometer,
  Zap,
  CheckCircle,
  AlertOctagon,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';
import { formatPercent, formatZ, exportToCsv } from '../../lib/utils';

export default function ComponentDetailView({
  dataset,
  selectedComponentId,
  setSelectedComponentId
}) {
  const [showOutcome, setShowOutcome] = useState(false);
  const records = dataset?.records || [];
  const currentIndex = records.findIndex(r => r.component_id === selectedComponentId);
  const record = records[currentIndex !== -1 ? currentIndex : 0] || records[0];

  if (!record) {
    return (
      <SquircleCard className="p-8 text-center text-slate-400">
        No component data available.
      </SquircleCard>
    );
  }

  const handlePrev = () => {
    if (currentIndex > 0) {
      setSelectedComponentId(records[currentIndex - 1].component_id);
    }
  };

  const handleNext = () => {
    if (currentIndex < records.length - 1) {
      setSelectedComponentId(records[currentIndex + 1].component_id);
    }
  };

  const exportEvidenceCard = () => {
    const cardData = [{
      Component_ID: record.component_id,
      Batch_ID: record.batch_id,
      Recommendation: record.recommendation,
      Reasons: record.recommendation_reasons.join('; '),
      Initial_0h_uA: record.initial_value,
      Current_24h_uA: record.latest_value,
      Limit_uA: record.limits.applicable_limit,
      Forecast_168h_uA: record.forecast.predicted_final_value,
      Interval_Lower_uA: record.forecast.prediction_lower,
      Interval_Upper_uA: record.forecast.prediction_upper,
      Peer_Robust_Z: record.peers.current_batch_robust_z,
      Peer_Sample_Size: record.peers.sample_size,
      Anomaly_Score: record.anomaly.score,
      Model_Version: record.forecast.model_version,
      Chamber_Temp_C: record.context.temperature_c,
      Stress_Voltage_V: record.context.applied_voltage_v,
      Board_Position: record.context.board_position,
      Tester_Channel: record.context.tester_channel
    }];
    exportToCsv(`Evidence_Card_${record.component_id}.csv`, cardData);
  };

  const contributions = record.forecast?.xgboost_explanation?.top_contributions || [];

  return (
    <div className="space-y-6 pb-12">
      {/* 1. Component Switcher Bar */}
      <SquircleCard className="p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <button
              onClick={handlePrev}
              disabled={currentIndex <= 0}
              className="btn-secondary p-2 disabled:opacity-30 flex items-center justify-center cursor-pointer"
            >
              <ChevronLeft className="w-4 h-4" strokeWidth={1.5} />
            </button>
            <button
              onClick={handleNext}
              disabled={currentIndex >= records.length - 1}
              className="btn-secondary p-2 disabled:opacity-30 flex items-center justify-center cursor-pointer"
            >
              <ChevronRight className="w-4 h-4" strokeWidth={1.5} />
            </button>
          </div>

          <div>
            <div className="flex items-center gap-2 font-mono">
              <span className="text-xs text-slate-400">INSPECTING:</span>
              <span className="text-base font-bold text-white tracking-wide">{record.component_id}</span>
              <span className="text-slate-500">•</span>
              <span className="text-xs text-slate-400">Batch {record.batch_id}</span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <DecisionBadge decision={record.recommendation} size="md" />

          <button
            onClick={exportEvidenceCard}
            className="btn-secondary flex items-center gap-2 px-3.5 py-2 text-xs font-mono font-medium"
          >
            <Download className="w-3.5 h-3.5 text-orange-400" strokeWidth={1.5} />
            <span>Export Evidence</span>
          </button>
        </div>
      </SquircleCard>

      {/* 2. Main Trajectory & Outcome Reveal Section */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Interactive Trajectory Chart (8 cols) */}
        <div className="lg:col-span-8 space-y-4">
          <SquircleCard elevated className="p-5">
            <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
              <div>
                <h3 className="text-xs font-mono uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
                  <Activity className="w-3.5 h-3.5 text-orange-400" strokeWidth={1.5} />
                  Burn-In Trajectory &amp; 168h Forecast
                </h3>
                <p className="text-[11px] text-slate-400">
                  0/24h measurements with calibrated split-conformal 168h forecast interval.
                </p>
              </div>

              {/* Reveal Outcome Action Toggle */}
              <button
                onClick={() => setShowOutcome(!showOutcome)}
                className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-mono transition-all cursor-pointer ${
                  showOutcome
                    ? 'btn-secondary text-orange-300 border-orange-500/30'
                    : 'btn-primary'
                }`}
              >
                {showOutcome ? <EyeOff className="w-3.5 h-3.5" strokeWidth={1.5} /> : <Eye className="w-3.5 h-3.5" strokeWidth={1.5} />}
                <span>{showOutcome ? 'Hide Recorded 168h' : 'Reveal 168h Outcome'}</span>
              </button>
            </div>

            {/* Trajectory SVG Chart */}
            <TrajectoryChart record={record} showOutcome={showOutcome} height={280} />

            {/* Outcome Verification Banner */}
            {showOutcome && (
              <div className="mt-4 p-3 rounded-lg bg-orange-500/[0.04] border border-orange-500/20 text-xs font-mono text-slate-300 flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-orange-400 flex-shrink-0" strokeWidth={1.5} />
                  <span>
                    Observed 168h leakage: <strong className="text-white">{record.observed_168h} µA</strong> (Forecast: {record.forecast.predicted_final_value} µA, Δ: {Math.abs(record.observed_168h - record.forecast.predicted_final_value).toFixed(4)} µA).
                  </span>
                </div>
                <span className="px-2 py-0.5 rounded text-[10px] bg-white/[0.04] border border-white/[0.08] text-slate-300">
                  {record.crossed_applicable_limit ? 'CROSSED LIMIT' : 'WITHIN SPEC'}
                </span>
              </div>
            )}
          </SquircleCard>

          {/* Peer Deviation & Baseline Comparison */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <SquircleCard className="p-3 text-xs font-mono">
              <span className="text-[10px] text-slate-400 uppercase block mb-1">Peer Robust Z</span>
              <span className="text-lg font-medium text-orange-400">
                {formatZ(record.peers.current_batch_robust_z)}
              </span>
              <span className="text-[10px] text-slate-500 block mt-0.5">
                vs {record.peers.sample_size} peers
              </span>
            </SquircleCard>

            <SquircleCard className="p-3 text-xs font-mono">
              <span className="text-[10px] text-slate-400 uppercase block mb-1">Drift Rate</span>
              <span className="text-lg font-medium text-white">
                +{record.slope_per_hour} µA/h
              </span>
              <span className="text-[10px] text-slate-500 block mt-0.5">
                Δ {record.absolute_change > 0 ? '+' : ''}{record.absolute_change} µA ({formatPercent(record.percent_change)})
              </span>
            </SquircleCard>

            <SquircleCard className="p-3 text-xs font-mono">
              <span className="text-[10px] text-slate-400 uppercase block mb-1">Headroom to Spec</span>
              <span className="text-lg font-medium text-white">
                {record.limits.headroom} µA
              </span>
              <span className="text-[10px] text-slate-500 block mt-0.5">
                {formatPercent(record.limits.headroom_fraction)} remaining
              </span>
            </SquircleCard>
          </div>
        </div>

        {/* Right: Technical Evidence & SHAP Explanation (4 cols) */}
        <div className="lg:col-span-4 space-y-3.5">
          {/* Recommendation Reasons Card */}
          <SquircleCard className="p-4 space-y-2">
            <h4 className="text-xs font-mono uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <Info className="w-3.5 h-3.5 text-orange-400" strokeWidth={1.5} />
              Recommendation Rationale
            </h4>
            <div className="space-y-1.5 text-xs">
              {record.recommendation_reasons.map((reason, idx) => (
                <div key={idx} className="p-2 rounded bg-white/[0.02] border border-white/[0.03] text-slate-300 flex items-start gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-orange-400 mt-1.5 flex-shrink-0" />
                  <span>{reason}</span>
                </div>
              ))}
            </div>
          </SquircleCard>

          {/* TreeSHAP Feature Attribution */}
          <SquircleCard className="p-4 space-y-2">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-mono uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-orange-400" strokeWidth={1.5} />
                TreeSHAP Vectors
              </h4>
              <span className="text-[10px] font-mono text-slate-500">
                {record.forecast.xgboost_explanation?.explained_model}
              </span>
            </div>

            <p className="text-[11px] text-slate-400 leading-normal">
              Corrections over base leakage ({record.forecast.xgboost_explanation?.base_value_ua} µA):
            </p>

            <div className="space-y-1.5 font-mono text-xs">
              {contributions.map((c, i) => (
                <div key={i} className="p-2 rounded bg-white/[0.02] border border-white/[0.03] space-y-0.5">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-300 text-[11px]">{c.feature}</span>
                    <span className="text-xs font-medium text-orange-400">
                      {c.contribution_ua >= 0 ? '+' : ''}{c.contribution_ua} µA
                    </span>
                  </div>
                  <div className="text-[9px] text-slate-500">
                    Val: {c.feature_value}
                  </div>
                </div>
              ))}
            </div>
          </SquircleCard>

          {/* Test Context & Hardware Location */}
          <SquircleCard className="p-4 space-y-2 font-mono text-xs">
            <h4 className="text-xs uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <Cpu className="w-3.5 h-3.5 text-orange-400" strokeWidth={1.5} />
              Hardware Context
            </h4>

            <div className="grid grid-cols-2 gap-1.5 text-[11px]">
              <div className="p-2 rounded bg-white/[0.02]">
                <span className="text-slate-500 block text-[9px]">SOCKET</span>
                <span className="text-white font-medium">#{record.context?.board_position}</span>
              </div>
              <div className="p-2 rounded bg-white/[0.02]">
                <span className="text-slate-500 block text-[9px]">CHANNEL</span>
                <span className="text-white font-medium">CH-{record.context?.tester_channel}</span>
              </div>
              <div className="p-2 rounded bg-white/[0.02]">
                <span className="text-slate-500 block text-[9px]">TEMP</span>
                <span className="text-white font-medium">{record.context?.temperature_c}°C</span>
              </div>
              <div className="p-2 rounded bg-white/[0.02]">
                <span className="text-slate-500 block text-[9px]">VOLTAGE</span>
                <span className="text-white font-medium">{record.context?.applied_voltage_v} V</span>
              </div>
            </div>
          </SquircleCard>
        </div>
      </div>
    </div>
  );
}
