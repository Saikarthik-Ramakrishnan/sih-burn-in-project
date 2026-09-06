import React, { useState, useMemo, useEffect, useRef } from 'react';
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
  ChevronRight,
  Search,
  X,
  Filter
} from 'lucide-react';
import { formatPercent, formatZ, exportToCsv } from '../../lib/utils';

export default function ComponentDetailView({
  dataset,
  selectedComponentId,
  setSelectedComponentId
}) {
  const [showOutcome, setShowOutcome] = useState(false);
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterRisk, setFilterRisk] = useState('ALL');
  const searchInputRef = useRef(null);

  const records = dataset?.records || [];
  const currentIndex = records.findIndex(r => r.component_id === selectedComponentId);
  const record = records[currentIndex !== -1 ? currentIndex : 0] || records[0];

  // Hotkey listener: / or Ctrl+K / Cmd+K to open, ESC to close
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.key === 'k' && (e.ctrlKey || e.metaKey)) || (e.key === '/' && !['INPUT', 'TEXTAREA'].includes(document.activeElement?.tagName))) {
        e.preventDefault();
        setIsSearchOpen(prev => !prev);
      } else if (e.key === 'Escape' && isSearchOpen) {
        setIsSearchOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isSearchOpen]);

  // Autofocus search input upon opening
  useEffect(() => {
    if (isSearchOpen) {
      setTimeout(() => searchInputRef.current?.focus(), 50);
    }
  }, [isSearchOpen]);

  // Filtered search list
  const filteredRecords = useMemo(() => {
    return records.filter(r => {
      const matchesFilter = filterRisk === 'ALL' || r.recommendation === filterRisk;
      if (!matchesFilter) return false;
      if (!searchQuery.trim()) return true;
      const q = searchQuery.toLowerCase().trim();
      const compMatch = r.component_id?.toLowerCase().includes(q);
      const batchMatch = r.batch_id?.toLowerCase().includes(q);
      const recMatch = r.recommendation?.toLowerCase().includes(q);
      const socketMatch = r.context?.board_position != null && String(r.context.board_position).includes(q);
      return compMatch || batchMatch || recMatch || socketMatch;
    });
  }, [records, searchQuery, filterRisk]);

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
              title="Previous Component"
            >
              <ChevronLeft className="w-4 h-4" strokeWidth={1.5} />
            </button>
            <button
              onClick={handleNext}
              disabled={currentIndex >= records.length - 1}
              className="btn-secondary p-2 disabled:opacity-30 flex items-center justify-center cursor-pointer"
              title="Next Component"
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
          {/* Quick Search Button in Inspector */}
          <button
            onClick={() => setIsSearchOpen(true)}
            className="btn-secondary flex items-center gap-2 px-3 py-1.5 text-xs font-mono text-slate-300 hover:text-white border-white/10 hover:border-orange-500/30 transition-all cursor-pointer group"
            title="Search components (Press '/' or Ctrl+K)"
          >
            <Search className="w-3.5 h-3.5 text-orange-400 group-hover:scale-110 transition-transform" strokeWidth={1.5} />
            <span>Search Parts</span>
            <kbd className="hidden sm:inline-block text-[10px] px-1.5 py-0.5 rounded bg-white/5 border border-white/10 text-slate-400">
              /
            </kbd>
          </button>

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
                  Hover near checkpoints to highlight coordinates &amp; threshold clearance.
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

            {/* Outcome Verification Banner (Red if limit crossed, Green if within spec) */}
            {showOutcome && (
              <div className={`mt-4 p-3 rounded-lg text-xs font-mono flex flex-wrap items-center justify-between gap-3 border ${
                record.crossed_applicable_limit
                  ? 'bg-rose-500/[0.08] border-rose-500/30 text-rose-200'
                  : 'bg-emerald-500/[0.08] border-emerald-500/30 text-emerald-200'
              }`}>
                <div className="flex items-center gap-2">
                  <CheckCircle className={`w-4 h-4 flex-shrink-0 ${record.crossed_applicable_limit ? 'text-rose-400' : 'text-emerald-400'}`} strokeWidth={1.5} />
                  <span>
                    Observed 168h leakage: <strong className="text-white">{record.observed_168h} µA</strong> (Forecast: {record.forecast.predicted_final_value} µA, Δ: {Math.abs(record.observed_168h - record.forecast.predicted_final_value).toFixed(4)} µA).
                  </span>
                </div>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                  record.crossed_applicable_limit
                    ? 'bg-rose-500/20 text-rose-300 border-rose-500/40'
                    : 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                }`}>
                  {record.crossed_applicable_limit ? 'DEFECT // CROSSED LIMIT' : 'HEALTHY // WITHIN SPEC'}
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
                <span className="text-white font-medium">{record.context?.board_position != null ? `#${record.context.board_position}` : 'N/A'}</span>
              </div>
              <div className="p-2 rounded bg-white/[0.02]">
                <span className="text-slate-500 block text-[9px]">CHANNEL</span>
                <span className="text-white font-medium">{record.context?.tester_channel != null ? `CH-${record.context.tester_channel}` : 'N/A'}</span>
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

      {/* 3. Component Search Modal */}
      {isSearchOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-md animate-in fade-in duration-150"
          onClick={() => setIsSearchOpen(false)}
        >
          <div
            className="relative w-full max-w-2xl max-h-[85vh] flex flex-col rounded-2xl bg-[#0c0d12]/95 border border-white/15 shadow-2xl shadow-black/80 overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header & Search Bar */}
            <div className="p-4 border-b border-white/10 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-xs font-mono tracking-wider text-slate-300 uppercase">
                  <Search className="w-4 h-4 text-orange-400" strokeWidth={1.5} />
                  <span>Telemetry Inspector • Component Directory</span>
                </div>
                <button
                  onClick={() => setIsSearchOpen(false)}
                  className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition-colors cursor-pointer"
                  title="Close (ESC)"
                >
                  <X className="w-4 h-4" strokeWidth={1.5} />
                </button>
              </div>

              {/* Input field */}
              <div className="relative">
                <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" strokeWidth={1.5} />
                <input
                  ref={searchInputRef}
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search by Component ID (e.g. CMP-001), Batch, Socket, or status..."
                  className="w-full bg-white/[0.04] border border-white/10 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white placeholder:text-slate-500 font-mono focus:outline-none focus:border-orange-500/50 focus:ring-1 focus:ring-orange-500/50 transition-all"
                />
              </div>

              {/* Filter Pills */}
              <div className="flex items-center gap-1.5 overflow-x-auto text-xs font-mono pb-1 scrollbar-none">
                <span className="text-[11px] text-slate-500 uppercase flex items-center gap-1 pr-1">
                  <Filter className="w-3 h-3 text-slate-500" strokeWidth={1.5} />
                  Filter:
                </span>
                {[
                  { id: 'ALL', label: 'All Parts' },
                  { id: 'ENGINEER_REVIEW', label: 'Review (Error)' },
                  { id: 'RETEST', label: 'Retest' },
                  { id: 'MONITOR', label: 'Monitor' },
                  { id: 'ACCEPT', label: 'Accept (Good)' }
                ].map(filter => {
                  let activeClass = 'bg-orange-500/20 text-orange-300 border-orange-500/40 font-semibold';
                  if (filter.id === 'ENGINEER_REVIEW') activeClass = 'bg-rose-500/20 text-rose-300 border-rose-500/50 font-bold';
                  else if (filter.id === 'ACCEPT') activeClass = 'bg-emerald-500/20 text-emerald-300 border-emerald-500/50 font-bold';
                  else if (filter.id === 'RETEST') activeClass = 'bg-amber-500/20 text-amber-300 border-amber-500/40 font-medium';
                  else if (filter.id === 'MONITOR') activeClass = 'bg-yellow-500/20 text-yellow-300 border-yellow-500/40 font-medium';

                  return (
                    <button
                      key={filter.id}
                      onClick={() => setFilterRisk(filter.id)}
                      className={`px-2.5 py-1 rounded-lg transition-all cursor-pointer whitespace-nowrap ${
                        filterRisk === filter.id
                          ? activeClass
                          : 'bg-white/[0.03] text-slate-400 border border-white/5 hover:text-white hover:bg-white/[0.06]'
                      }`}
                    >
                      {filter.label}
                    </button>
                  );
                })}
                <span className="ml-auto text-[11px] text-slate-500 whitespace-nowrap pl-2">
                  {filteredRecords.length} found
                </span>
              </div>
            </div>

            {/* Results List */}
            <div className="flex-1 overflow-y-auto p-2 divide-y divide-white/[0.03] max-h-[55vh]">
              {filteredRecords.length === 0 ? (
                <div className="py-12 text-center text-slate-500 font-mono text-xs">
                  No components match the search query "{searchQuery}".
                </div>
              ) : (
                filteredRecords.map((item) => {
                  const isSelected = item.component_id === selectedComponentId;
                  const isError = item.recommendation === 'ENGINEER_REVIEW';
                  const isGood = item.recommendation === 'ACCEPT';
                  const isRetest = item.recommendation === 'RETEST';

                  let badgeColor = 'bg-white/5 text-slate-400 border border-white/10';
                  if (isError) badgeColor = 'bg-rose-500/20 text-rose-300 border border-rose-500/40';
                  else if (isGood) badgeColor = 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40';
                  else if (isRetest) badgeColor = 'bg-amber-500/20 text-amber-300 border border-amber-500/40';
                  else badgeColor = 'bg-yellow-500/20 text-yellow-300 border border-yellow-500/40';

                  return (
                    <div
                      key={item.component_id}
                      onClick={() => {
                        setSelectedComponentId(item.component_id);
                        setIsSearchOpen(false);
                      }}
                      className={`p-3 rounded-xl flex items-center justify-between gap-3 cursor-pointer transition-all ${
                        isSelected
                          ? (isError ? 'bg-rose-500/10 border border-rose-500/30' : (isGood ? 'bg-emerald-500/10 border border-emerald-500/30' : 'bg-orange-500/10 border border-orange-500/30'))
                          : 'hover:bg-white/[0.04] text-slate-300 border border-transparent'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <div className={`w-8 h-8 rounded-lg flex items-center justify-center font-mono text-xs font-bold ${badgeColor}`}>
                          #{item.component_id.replace('CMP-', '')}
                        </div>
                        <div>
                          <div className="flex items-center gap-2 font-mono text-sm font-semibold text-white">
                            <span className={isError ? 'text-rose-300' : (isGood ? 'text-emerald-300' : 'text-white')}>
                              {item.component_id}
                            </span>
                            <span className="text-xs text-slate-400 font-normal">({item.batch_id})</span>
                            {isSelected && (
                              <span className="text-[10px] uppercase px-1.5 py-0.5 rounded bg-white/10 text-white border border-white/20">
                                Current
                              </span>
                            )}
                          </div>
                          <div className="text-[11px] font-mono text-slate-400 flex items-center gap-3 mt-0.5">
                            <span>Socket #{item.context?.board_position ?? 'N/A'}</span>
                            <span>•</span>
                            <span>24h: {item.latest_value?.toFixed(4)} µA</span>
                            <span>•</span>
                            <span className={item.forecast?.predicted_to_cross_limit ? 'text-rose-400 font-medium' : ''}>
                              168h Pred: {item.forecast?.predicted_final_value?.toFixed(4)} µA
                            </span>
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        <DecisionBadge decision={item.recommendation} size="sm" />
                      </div>
                    </div>
                  );
                })
              )}
            </div>

            {/* Modal Footer with shortcut help */}
            <div className="p-3 bg-white/[0.02] border-t border-white/10 flex items-center justify-between text-[11px] font-mono text-slate-400">
              <div className="flex items-center gap-2">
                <span>Press <kbd className="px-1 py-0.5 rounded bg-white/5 border border-white/10 text-slate-300">ESC</kbd> to close</span>
                <span>•</span>
                <span>Click component to inspect</span>
              </div>
              <div className="text-slate-500">
                Total Parts: {records.length}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
