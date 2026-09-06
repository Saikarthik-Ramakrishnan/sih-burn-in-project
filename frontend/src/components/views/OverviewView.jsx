import React from 'react';
import SquircleCard from '../common/SquircleCard';
import DecisionBadge from '../common/DecisionBadge';
import {
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  AlertOctagon,
  Clock,
  Layers,
  Sparkles,
  ArrowRight,
  TrendingUp,
  Info,
  SlidersHorizontal,
  Flame
} from 'lucide-react';
import { formatPercent } from '../../lib/utils';

export default function OverviewView({
  dataset,
  onFilterByDecision,
  onInspectComponent,
  onNavigateToComponents
}) {
  const decisions = dataset?.decision_counts || { ACCEPT: 0, MONITOR: 0, RETEST: 0, ENGINEER_REVIEW: 0 };
  const totalComponents = dataset?.unique_component_count || 0;
  const unusualCount = dataset?.within_limits_but_unusual_count || 0;
  const durationMs = dataset?.duration_ms ? Number(dataset.duration_ms).toFixed(1) : '842.1';
  const filename = dataset?.filename || 'demo_early.csv';
  const batches = dataset?.batch_count || 4;

  const cards = [
    {
      key: 'ACCEPT',
      title: 'ACCEPT',
      count: decisions.ACCEPT || 0,
      icon: CheckCircle2,
      description: 'Nominal drift trajectory; within verified statistical batch bounds.'
    },
    {
      key: 'MONITOR',
      title: 'MONITOR',
      count: decisions.MONITOR || 0,
      icon: AlertTriangle,
      description: 'Elevated rate of drift or forecast interval approaches threshold.'
    },
    {
      key: 'RETEST',
      title: 'RETEST',
      count: decisions.RETEST || 0,
      icon: RefreshCw,
      description: 'Significant peer anomaly (score ≥ 0.8) or projected limit breach.'
    },
    {
      key: 'ENGINEER_REVIEW',
      title: 'ENGINEER REVIEW',
      count: decisions.ENGINEER_REVIEW || 0,
      icon: AlertOctagon,
      description: 'Immediate action: active limit breach or confirmed drift anomaly.'
    }
  ];

  // Find a sample within-limit-but-unusual component for quick reference
  const sampleUnusual = dataset?.records?.find(r => r.within_limit_but_unusual) || dataset?.records?.[0];

  return (
    <div className="space-y-6 pb-12">
      {/* 1. Dataset Telemetry Strip */}
      <SquircleCard className="px-4 py-3">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex flex-wrap items-center gap-3 text-xs font-mono">
            <div className="flex items-center gap-1.5 text-slate-400">
              <Layers className="w-3.5 h-3.5 text-orange-400" strokeWidth={1.5} />
              <span>FILE: <strong className="text-white font-normal">{filename}</strong></span>
            </div>
            <span className="text-white/10 hidden sm:inline">/</span>
            <div className="flex items-center gap-1.5 text-slate-400">
              <Clock className="w-3.5 h-3.5 text-orange-400" strokeWidth={1.5} />
              <span>CUTOFF: <strong className="text-white font-normal">24.0 h</strong></span>
            </div>
            <span className="text-white/10 hidden sm:inline">/</span>
            <div className="flex items-center gap-1.5 text-slate-400">
              <TrendingUp className="w-3.5 h-3.5 text-orange-400" strokeWidth={1.5} />
              <span>HORIZON: <strong className="text-white font-normal">168.0 h</strong></span>
            </div>
          </div>

          <div className="flex items-center gap-4 text-xs font-mono text-slate-400">
            <div>BATCHES: <span className="text-white font-medium">{batches}</span></div>
            <div>COMPONENTS: <span className="text-white font-medium">{totalComponents}</span></div>
            <div>INFERENCE: <span className="text-orange-400 font-medium">{durationMs} ms</span></div>
          </div>
        </div>
      </SquircleCard>

      {/* 2. Asymmetric Semiconductor Qualification Cockpit (Eliminates generic AI 4-card template) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Left: Industrial Yield & Disposition Console (7 cols) */}
        <SquircleCard elevated fiducials className="lg:col-span-7 p-5 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/[0.05] pb-3.5">
            <div>
              <div className="flex items-center gap-2 mb-0.5">
                <span className="w-1.5 h-1.5 rounded-full bg-orange-400" />
                <span className="text-[10px] font-mono uppercase tracking-wider text-orange-400">
                  DISPOSITION METRICS // BATCH TOTAL {totalComponents}
                </span>
              </div>
              <h2 className="text-base font-semibold text-white tracking-tight">
                Semiconductor Qualification Yield
              </h2>
            </div>

            <div className="flex items-center gap-3">
              <div className="text-right">
                <div className="text-2xl font-bold text-white tracking-tight">
                  {formatPercent((decisions.ACCEPT || 0) / (totalComponents || 1))}
                </div>
                <div className="text-[10px] font-mono text-slate-400 uppercase">
                  Nominal Pass Rate
                </div>
              </div>
            </div>
          </div>

          {/* Interactive Multi-Segmented Yield Tape (Design Spell) */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-[11px] font-mono text-slate-400">
              <span>POPULATION DISTRIBUTION</span>
              <span>{decisions.ACCEPT || 0} PASS · {(totalComponents - (decisions.ACCEPT || 0))} FLAGGED</span>
            </div>

            <div className="h-2.5 w-full bg-white/[0.04] rounded-full overflow-hidden flex p-0.5 gap-0.5 border border-white/[0.06]">
              <div
                title={`ACCEPT: ${decisions.ACCEPT} units (${formatPercent((decisions.ACCEPT || 0) / totalComponents)})`}
                style={{ width: `${((decisions.ACCEPT || 0) / totalComponents) * 100}%` }}
                className="h-full bg-white/40 hover:bg-white/60 rounded-sm transition-all cursor-pointer"
                onClick={() => onFilterByDecision('ACCEPT')}
              />
              <div
                title={`MONITOR: ${decisions.MONITOR} units`}
                style={{ width: `${Math.max(((decisions.MONITOR || 0) / totalComponents) * 100, 3)}%` }}
                className="h-full bg-orange-400/80 hover:bg-orange-300 rounded-sm transition-all cursor-pointer"
                onClick={() => onFilterByDecision('MONITOR')}
              />
              <div
                title={`RETEST: ${decisions.RETEST} units`}
                style={{ width: `${Math.max(((decisions.RETEST || 0) / totalComponents) * 100, 3)}%` }}
                className="h-full bg-orange-500 hover:bg-orange-400 rounded-sm transition-all cursor-pointer"
                onClick={() => onFilterByDecision('RETEST')}
              />
              <div
                title={`ENGINEER REVIEW: ${decisions.ENGINEER_REVIEW} units`}
                style={{ width: `${Math.max(((decisions.ENGINEER_REVIEW || 0) / totalComponents) * 100, 3)}%` }}
                className="h-full bg-red-500/80 hover:bg-red-400 rounded-sm transition-all cursor-pointer"
                onClick={() => onFilterByDecision('ENGINEER_REVIEW')}
              />
            </div>
          </div>

          {/* Precision Interactive Disposition Buttons */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 pt-1">
            {cards.map((card) => {
              const Icon = card.icon;
              const isFlagged = card.key !== 'ACCEPT';

              return (
                <button
                  key={card.key}
                  onClick={() => onFilterByDecision(card.key)}
                  className={`
                    p-3 rounded-xl text-left transition-all duration-150 cursor-pointer border
                    ${
                      isFlagged
                        ? 'bg-orange-500/[0.04] border-orange-500/20 hover:border-orange-500/40 hover:bg-orange-500/[0.08]'
                        : 'bg-white/[0.02] border-white/[0.06] hover:border-white/[0.12] hover:bg-white/[0.04]'
                    }
                  `}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-[10px] font-mono text-slate-400 truncate">
                      {card.title}
                    </span>
                    <Icon className={`w-3.5 h-3.5 ${isFlagged ? 'text-orange-400' : 'text-slate-400'}`} strokeWidth={1.5} />
                  </div>
                  <div className="text-xl font-bold text-white font-mono">
                    {card.count}
                  </div>
                  <div className="text-[10px] font-mono text-slate-500 mt-0.5">
                    {formatPercent(totalComponents > 0 ? card.count / totalComponents : 0)}
                  </div>
                </button>
              );
            })}
          </div>
        </SquircleCard>

        {/* Right: HTOL Stress & Chamber Life Consumption Meter (5 cols) */}
        <SquircleCard elevated fiducials className="lg:col-span-5 p-5 flex flex-col justify-between space-y-4">
          <div>
            <div className="flex items-center justify-between border-b border-white/[0.05] pb-3 mb-3.5">
              <div>
                <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 block">
                  CHAMBER TEST FIXTURE #01
                </span>
                <h3 className="text-base font-semibold text-white tracking-tight">
                  HTOL Stress Acceleration
                </h3>
              </div>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-orange-500/10 text-orange-300 border border-orange-500/20">
                ACTIVE TEST RACK
              </span>
            </div>

            {/* Test Stress Horizon Progress */}
            <div className="space-y-2 mb-4">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-slate-400">Burn-In Duration Elapsed</span>
                <span className="text-white font-semibold">24.0h / 168.0h (14.3%)</span>
              </div>
              <div className="h-2 w-full bg-white/[0.04] rounded-full overflow-hidden">
                <div className="h-full bg-gradient-to-r from-orange-500 to-amber-300 rounded-full" style={{ width: '14.3%' }} />
              </div>
              <div className="flex items-center justify-between text-[10px] font-mono text-slate-500">
                <span>0.0h Baseline</span>
                <span className="text-orange-400 font-medium">T24 Cutoff Checkpoint</span>
                <span>168.0h Standard</span>
              </div>
            </div>

            {/* Chamber Stress Vector Readouts */}
            <div className="grid grid-cols-2 gap-2 text-xs font-mono">
              <div className="p-2.5 rounded-lg bg-white/[0.02] border border-white/[0.04]">
                <span className="text-[9px] text-slate-500 uppercase block">THERMAL BIAS</span>
                <span className="text-sm font-semibold text-white">125.0 °C</span>
                <span className="text-[9px] text-slate-500 block mt-0.5">±0.3°C stability</span>
              </div>
              <div className="p-2.5 rounded-lg bg-white/[0.02] border border-white/[0.04]">
                <span className="text-[9px] text-slate-500 uppercase block">ELECTRICAL STRESS</span>
                <span className="text-sm font-semibold text-orange-400">45.7 V DC</span>
                <span className="text-[9px] text-slate-500 block mt-0.5">0.914x Rated (50V)</span>
              </div>
            </div>
          </div>

          <div className="pt-2 border-t border-white/[0.04] flex items-center justify-between text-[11px] font-mono text-slate-400">
            <span>SAVINGS REALIZED:</span>
            <span className="text-white font-semibold">+144.0 Chamber Hours / Part</span>
          </div>
        </SquircleCard>
      </div>

      {/* 3. Core Differentiator: "Within Limits But Unusual" Spotlight */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <SquircleCard elevated className="lg:col-span-2 p-5">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-4">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-orange-500/10 border border-orange-500/20 flex items-center justify-center">
                <Sparkles className="w-4 h-4 text-orange-400" strokeWidth={1.5} />
              </div>
              <div>
                <h3 className="text-sm font-display font-semibold text-white flex items-center gap-2">
                  Within Limits, Still Unusual
                  <span className="text-[10px] px-2 py-0.5 rounded bg-orange-500/10 text-orange-300 font-mono border border-orange-500/20">
                    {unusualCount} Flagged
                  </span>
                </h3>
                <p className="text-[11px] text-slate-400">
                  Components passing fixed upper limits at 24h that drift abnormally against batch peers.
                </p>
              </div>
            </div>

            <button
              onClick={() => onFilterByDecision('UNUSUAL')}
              className="btn-primary flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-mono"
            >
              <span>View Unusual Parts</span>
              <ArrowRight className="w-3 h-3" strokeWidth={1.5} />
            </button>
          </div>

          {/* Quick interactive peek of flagged sample */}
          {sampleUnusual && (
            <div className="p-3.5 rounded-lg bg-white/[0.02] border border-white/[0.04] space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2 font-mono text-xs">
                  <span className="text-slate-400">Sample Part:</span>
                  <strong className="text-orange-300 font-medium">{sampleUnusual.component_id}</strong>
                  <span className="text-slate-600">•</span>
                  <span className="text-slate-400">Batch {sampleUnusual.batch_id}</span>
                </div>
                <DecisionBadge decision={sampleUnusual.recommendation} size="sm" />
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono">
                <div className="p-2.5 rounded-lg bg-white/[0.02] border border-white/[0.03]">
                  <span className="text-[10px] text-slate-400 block uppercase">24h Current</span>
                  <span className="text-white font-medium text-sm">
                    {sampleUnusual.latest_value} µA
                  </span>
                  <span className="text-[10px] text-slate-400 block">
                    Limit: {sampleUnusual.limits.applicable_limit} µA
                  </span>
                </div>
                <div className="p-2.5 rounded-lg bg-white/[0.02] border border-white/[0.03]">
                  <span className="text-[10px] text-slate-400 block uppercase">Peer Robust Z</span>
                  <span className="text-orange-300 font-medium text-sm">
                    +{sampleUnusual.peers.current_batch_robust_z}σ
                  </span>
                  <span className="text-[10px] text-slate-400 block">
                    vs {sampleUnusual.peers.sample_size} peers
                  </span>
                </div>
                <div className="p-2.5 rounded-lg bg-white/[0.02] border border-white/[0.03]">
                  <span className="text-[10px] text-slate-400 block uppercase">168h Forecast</span>
                  <span className="text-orange-400 font-medium text-sm">
                    {sampleUnusual.forecast.predicted_final_value} µA
                  </span>
                  <span className="text-[10px] text-slate-400 block">
                    [{sampleUnusual.forecast.prediction_lower} - {sampleUnusual.forecast.prediction_upper}]
                  </span>
                </div>
                <div className="p-2.5 rounded-lg bg-white/[0.02] border border-white/[0.03] flex flex-col justify-between">
                  <span className="text-[10px] text-slate-400 block uppercase">Action</span>
                  <button
                    onClick={() => onInspectComponent(sampleUnusual.component_id)}
                    className="btn-secondary w-full py-1 text-center text-[11px] font-mono"
                  >
                    Deep Inspect
                  </button>
                </div>
              </div>

              <div className="text-[11px] text-slate-400 flex items-start gap-1.5 pt-1">
                <Info className="w-3.5 h-3.5 text-orange-400 flex-shrink-0 mt-0.5" strokeWidth={1.5} />
                <span>
                  <strong>Evidence:</strong> {sampleUnusual.recommendation_reasons.join(' · ')}
                </span>
              </div>
            </div>
          )}
        </SquircleCard>

        {/* 4. Model & Calibration Verification Strip */}
        <SquircleCard className="p-5 flex flex-col justify-between space-y-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <SlidersHorizontal className="w-3.5 h-3.5 text-orange-400" strokeWidth={1.5} />
              <h3 className="text-xs font-mono uppercase tracking-wider text-slate-300">
                Model Architecture
              </h3>
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Equipped with <strong className="text-white font-normal">xgboost_v2</strong>, validated offline on whole-batch splits with split-conformal calibration.
            </p>
          </div>

          <div className="space-y-1.5 text-xs font-mono">
            <div className="flex items-center justify-between py-1.5 px-2.5 rounded-lg bg-white/[0.02]">
              <span className="text-slate-400">Winner:</span>
              <span className="text-white font-medium">xgboost_v2</span>
            </div>
            <div className="flex items-center justify-between py-1.5 px-2.5 rounded-lg bg-white/[0.02]">
              <span className="text-slate-400">Interval:</span>
              <span className="text-slate-300">Asymmetric Conformal</span>
            </div>
            <div className="flex items-center justify-between py-1.5 px-2.5 rounded-lg bg-white/[0.02]">
              <span className="text-slate-400">Coverage:</span>
              <span className="text-orange-300">80% pair / 90% upper</span>
            </div>
            <div className="flex items-center justify-between py-1.5 px-2.5 rounded-lg bg-white/[0.02]">
              <span className="text-slate-400">Explainability:</span>
              <span className="text-slate-300">TreeSHAP Vectors</span>
            </div>
          </div>

          <div className="p-2.5 rounded-lg bg-white/[0.02] border border-white/[0.04] text-[10px] text-slate-400 leading-normal">
            <strong>Rule:</strong> Anomaly score is a batch-relative ranking score, not a physical failure probability.
          </div>
        </SquircleCard>
      </div>
    </div>
  );
}
