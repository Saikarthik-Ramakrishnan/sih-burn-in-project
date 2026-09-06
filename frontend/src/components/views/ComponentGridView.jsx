import React, { useState, useMemo, useEffect } from 'react';
import SquircleCard from '../common/SquircleCard';
import DecisionBadge from '../common/DecisionBadge';
import {
  Search,
  Filter,
  Grid,
  List,
  Sparkles,
  ArrowUpDown,
  ExternalLink,
  Flame,
  ShieldAlert,
  SlidersHorizontal,
  ChevronRight,
  Crosshair
} from 'lucide-react';
import { formatUnit, formatPercent, formatZ, getThermalColor } from '../../lib/utils';
import { playMechanicalClick, playTick } from '../../lib/audioEffects';

export default function ComponentGridView({
  dataset,
  selectedComponentId,
  setSelectedComponentId,
  onInspectComponent,
  activeFilter,
  setActiveFilter
}) {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortField, setSortField] = useState('board_position');
  const [sortAsc, setSortAsc] = useState(true);
  const [hoveredRecord, setHoveredRecord] = useState(null);

  const records = dataset?.records || [];

  // Arrow Key navigation for 8x8 physical socket board (Design Spell)
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (['INPUT', 'TEXTAREA'].includes(document.activeElement?.tagName)) return;
      if (!['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) return;

      const idx = records.findIndex(r => r.component_id === selectedComponentId);
      if (idx === -1) return;

      let nextIdx = idx;
      if (e.key === 'ArrowLeft' && idx > 0) nextIdx = idx - 1;
      else if (e.key === 'ArrowRight' && idx < records.length - 1) nextIdx = idx + 1;
      else if (e.key === 'ArrowUp' && idx >= 8) nextIdx = idx - 8;
      else if (e.key === 'ArrowDown' && idx + 8 < records.length) nextIdx = idx + 8;

      if (nextIdx !== idx && records[nextIdx]) {
        e.preventDefault();
        playTick();
        setSelectedComponentId(records[nextIdx].component_id);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [records, selectedComponentId, setSelectedComponentId]);

  // Filter records
  const filteredRecords = useMemo(() => {
    return records.filter((r) => {
      // Search term
      if (searchTerm) {
        const term = searchTerm.toLowerCase();
        const matchesId = r.component_id.toLowerCase().includes(term);
        const matchesBatch = r.batch_id.toLowerCase().includes(term);
        const matchesProfile = (r.profile_id || '').toLowerCase().includes(term);
        if (!matchesId && !matchesBatch && !matchesProfile) return false;
      }

      // Quick filter
      if (activeFilter === 'ALL') return true;
      if (activeFilter === 'UNUSUAL') return r.within_limit_but_unusual;
      if (activeFilter === 'ANOMALY') return r.anomaly?.is_anomaly;
      if (activeFilter === 'CROSSING') return r.forecast?.predicted_to_cross_limit;
      if (activeFilter === 'ACCEPT') return r.recommendation === 'ACCEPT';
      if (activeFilter === 'MONITOR') return r.recommendation === 'MONITOR';
      if (activeFilter === 'RETEST') return r.recommendation === 'RETEST';
      if (activeFilter === 'ENGINEER_REVIEW') return r.recommendation === 'ENGINEER_REVIEW';

      return true;
    });
  }, [records, searchTerm, activeFilter]);

  // Sort records
  const sortedRecords = useMemo(() => {
    return [...filteredRecords].sort((a, b) => {
      let valA, valB;
      if (sortField === 'board_position') {
        valA = a.context?.board_position || 0;
        valB = b.context?.board_position || 0;
      } else if (sortField === 'latest_value') {
        valA = a.latest_value || 0;
        valB = b.latest_value || 0;
      } else if (sortField === 'forecast') {
        valA = a.forecast?.predicted_final_value || 0;
        valB = b.forecast?.predicted_final_value || 0;
      } else if (sortField === 'robust_z') {
        valA = a.peers?.current_batch_robust_z || 0;
        valB = b.peers?.current_batch_robust_z || 0;
      } else {
        valA = a.component_id;
        valB = b.component_id;
      }

      if (valA < valB) return sortAsc ? -1 : 1;
      if (valA > valB) return sortAsc ? 1 : -1;
      return 0;
    });
  }, [filteredRecords, sortField, sortAsc]);

  const handleSort = (field) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(true);
    }
  };

  const selectedRecord = records.find(r => r.component_id === selectedComponentId) || records[0];

  return (
    <div className="space-y-6 pb-12">
      {/* Search & Quick Filter Pills */}
      <SquircleCard className="p-3.5 flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
        {/* Search Bar */}
        <div className="relative flex-1 max-w-md">
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" strokeWidth={1.5} />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search Component ID (e.g. MLCC_C000062), Batch, Profile..."
            className="w-full pl-9 pr-3.5 py-1.5 rounded-lg bg-black/20 border border-white/[0.08] text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-orange-500/60 transition-all font-mono"
          />
        </div>

        {/* Filter Tabs */}
        <div className="flex flex-wrap items-center gap-1.5">
          <button
            onClick={() => setActiveFilter('ALL')}
            className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-all cursor-pointer ${
              activeFilter === 'ALL'
                ? 'bg-orange-500/15 text-orange-400 border border-orange-500/30 font-medium'
                : 'text-slate-400 hover:text-slate-200 bg-white/[0.03] border border-transparent'
            }`}
          >
            All ({records.length})
          </button>

          <button
            onClick={() => setActiveFilter('UNUSUAL')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono transition-all cursor-pointer ${
              activeFilter === 'UNUSUAL'
                ? 'bg-orange-500/15 text-orange-400 border border-orange-500/30 font-medium'
                : 'text-slate-400 hover:text-slate-200 bg-white/[0.03] border border-transparent'
            }`}
          >
            <Sparkles className="w-3 h-3 text-orange-400" strokeWidth={1.5} />
            <span>Within Limit, Still Unusual ({records.filter(r => r.within_limit_but_unusual).length})</span>
          </button>

          <button
            onClick={() => setActiveFilter('CROSSING')}
            className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-all cursor-pointer ${
              activeFilter === 'CROSSING'
                ? 'bg-orange-500/15 text-orange-400 border border-orange-500/30 font-medium'
                : 'text-slate-400 hover:text-slate-200 bg-white/[0.03] border border-transparent'
            }`}
          >
            Limit Crossing ({records.filter(r => r.forecast?.predicted_to_cross_limit).length})
          </button>
        </div>
      </SquircleCard>

      {/* Main Dual Workspace: Component Table (Left) + Spatial Fixture Matrix (Right) */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
        {/* Left Column: Result Table (7 cols) */}
        <div className="xl:col-span-7 space-y-3">
          <div className="flex items-center justify-between text-xs text-slate-400 px-1 font-mono">
            <span>SHOWING {sortedRecords.length} OF {records.length} COMPONENTS</span>
            <span>CLICK ROW TO HIGHLIGHT ON BOARD MAP</span>
          </div>

          <SquircleCard className="overflow-hidden p-0 border-white/10">
            <div className="overflow-x-auto max-h-[640px]">
              <table className="w-full text-left text-xs font-mono border-collapse">
                <thead className="bg-[#10111a] text-slate-400 sticky top-0 z-20 border-b border-white/10">
                  <tr>
                    <th
                      onClick={() => handleSort('board_position')}
                      className="py-3 px-3.5 cursor-pointer hover:text-white"
                    >
                      <div className="flex items-center gap-1">
                        <span>POS</span>
                        <ArrowUpDown className="w-3 h-3 text-slate-500" strokeWidth={1.5} />
                      </div>
                    </th>
                    <th
                      onClick={() => handleSort('component_id')}
                      className="py-3 px-3.5 cursor-pointer hover:text-white"
                    >
                      <div className="flex items-center gap-1">
                        <span>COMPONENT</span>
                        <ArrowUpDown className="w-3 h-3 text-slate-500" strokeWidth={1.5} />
                      </div>
                    </th>
                    <th
                      onClick={() => handleSort('latest_value')}
                      className="py-3 px-3 cursor-pointer hover:text-white"
                    >
                      <div className="flex items-center gap-1">
                        <span>24h VALUE</span>
                        <ArrowUpDown className="w-3 h-3 text-slate-500" strokeWidth={1.5} />
                      </div>
                    </th>
                    <th
                      onClick={() => handleSort('robust_z')}
                      className="py-3 px-3 cursor-pointer hover:text-white"
                    >
                      <div className="flex items-center gap-1">
                        <span>PEER Z</span>
                        <ArrowUpDown className="w-3 h-3 text-slate-500" strokeWidth={1.5} />
                      </div>
                    </th>
                    <th
                      onClick={() => handleSort('forecast')}
                      className="py-3 px-3 cursor-pointer hover:text-white"
                    >
                      <div className="flex items-center gap-1">
                        <span>168h FORECAST</span>
                        <ArrowUpDown className="w-3 h-3 text-slate-500" strokeWidth={1.5} />
                      </div>
                    </th>
                    <th className="py-3 px-3.5">DECISION</th>
                    <th className="py-3 px-3 text-right">ACTION</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {sortedRecords.map((record) => {
                    const isSelected = record.component_id === selectedComponentId;
                    const limitFraction = record.limits?.limit_fraction || 0;
                    const isUnusual = record.within_limit_but_unusual;

                    return (
                      <tr
                        key={record.component_id}
                        onClick={() => setSelectedComponentId(record.component_id)}
                        className={`
                          transition-colors cursor-pointer group
                          ${
                            isSelected
                              ? 'bg-orange-500/[0.1] text-white font-medium'
                              : 'hover:bg-white/[0.03] text-slate-300'
                          }
                          ${isUnusual ? 'border-l-2 border-l-orange-400' : ''}
                        `}
                      >
                        {/* Position */}
                        <td className="py-2.5 px-3.5 text-slate-500">
                          #{String(record.context?.board_position || '00').padStart(2, '0')}
                        </td>

                        {/* ID & Batch */}
                        <td className="py-2.5 px-3.5">
                          <div className="flex flex-col">
                            <span className="font-medium text-white group-hover:text-orange-300 transition-colors">
                              {record.component_id}
                            </span>
                            <span className="text-[10px] text-slate-500">
                              {record.batch_id} • Ch.{record.context?.tester_channel}
                            </span>
                          </div>
                        </td>

                        {/* Current 24h Leakage */}
                        <td className="py-2.5 px-3">
                          <div className="flex flex-col">
                            <span className={limitFraction >= 1 ? 'text-orange-400 font-bold' : 'text-slate-200'}>
                              {record.latest_value} µA
                            </span>
                            <span className="text-[10px] text-slate-500">
                              Δ {record.absolute_change > 0 ? '+' : ''}{record.absolute_change} µA
                            </span>
                          </div>
                        </td>

                        {/* Peer Robust Z */}
                        <td className="py-2.5 px-3">
                          <span
                            className={`
                              inline-block px-1.5 py-0.5 rounded text-[11px]
                              ${
                                Math.abs(record.peers?.current_batch_robust_z || 0) >= 2
                                  ? 'bg-orange-500/20 text-orange-300 font-medium'
                                  : 'text-slate-400'
                              }
                            `}
                          >
                            {formatZ(record.peers?.current_batch_robust_z)}
                          </span>
                        </td>

                        {/* 168h Forecast & Interval */}
                        <td className="py-2.5 px-3">
                          <div className="flex flex-col">
                            <span
                              className={`
                                ${record.forecast?.predicted_to_cross_limit ? 'text-orange-400 font-medium' : 'text-slate-300'}
                              `}
                            >
                              {record.forecast?.predicted_final_value} µA
                            </span>
                            <span className="text-[10px] text-slate-500">
                              [{record.forecast?.prediction_lower} - {record.forecast?.prediction_upper}]
                            </span>
                          </div>
                        </td>

                        {/* Recommendation Badge */}
                        <td className="py-2.5 px-3.5">
                          <DecisionBadge decision={record.recommendation} size="sm" />
                        </td>

                        {/* Inspect action */}
                        <td className="py-2.5 px-3 text-right">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedComponentId(record.component_id);
                              onInspectComponent(record.component_id);
                            }}
                            title="Inspect Trajectory & Evidence"
                            className="p-1 rounded text-slate-500 hover:text-orange-400 transition-colors cursor-pointer inline-flex items-center"
                          >
                            <ChevronRight className="w-4 h-4" strokeWidth={1.5} />
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </SquircleCard>
        </div>

        {/* Right Column: Physical Semiconductor Fixture Map (5 cols) */}
        <div className="xl:col-span-5 space-y-4">
          <SquircleCard elevated fiducials className="p-4 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-orange-400" />
                  <h3 className="text-xs font-mono uppercase tracking-wider text-slate-300">
                    Chamber Rack Fixture // 64 Sockets
                  </h3>
                </div>
                <span className="text-[10px] font-mono text-orange-400 bg-orange-500/10 px-2 py-0.5 rounded border border-orange-500/20">
                  HTOL 8×8 RACK
                </span>
              </div>
              <p className="text-[11px] text-slate-400 mb-2.5 leading-relaxed">
                Physical test board socket layout. Use <kbd className="px-1 py-0.2 rounded bg-white/10 text-white font-mono text-[9px]">Arrow Keys</kbd> to step between active sockets.
              </p>

              {/* Floating Real-Time Micro-HUD (Design Spell) */}
              {hoveredRecord ? (
                <div className="mb-2.5 p-2 rounded-lg bg-[#141624] border border-orange-500/30 text-xs font-mono text-white flex items-center justify-between shadow-lg animate-in fade-in duration-100">
                  <div className="flex items-center gap-2">
                    <Crosshair className="w-3.5 h-3.5 text-orange-400 animate-spin-slow" strokeWidth={1.5} />
                    <div>
                      <span className="text-orange-400 font-bold">{hoveredRecord.component_id}</span>
                      <span className="text-[10px] text-slate-400 block">
                        Socket #{hoveredRecord.context?.board_position} · {hoveredRecord.latest_value} µA
                      </span>
                    </div>
                  </div>

                  {/* Micro Sparkline */}
                  <div className="flex items-center gap-2">
                    <svg width="44" height="20" className="overflow-visible">
                      <path
                        d={`M 2 16 L 22 ${16 - Math.min((hoveredRecord.latest_value / 0.25) * 14, 14)} L 42 ${16 - Math.min((hoveredRecord.forecast?.predicted_final_value / 0.25) * 14, 14)}`}
                        fill="none"
                        stroke="#f97316"
                        strokeWidth="1.5"
                      />
                      <circle cx="2" cy="16" r="2" fill="#fff" />
                      <circle cx="22" cy={16 - Math.min((hoveredRecord.latest_value / 0.25) * 14, 14)} r="2" fill="#f97316" />
                      <circle cx="42" cy={16 - Math.min((hoveredRecord.forecast?.predicted_final_value / 0.25) * 14, 14)} r="2" fill="#f97316" />
                    </svg>
                    <span className="text-[10px] text-slate-400">
                      Z: {formatZ(hoveredRecord.peers?.current_batch_robust_z)}
                    </span>
                  </div>
                </div>
              ) : (
                <div className="mb-2.5 px-2.5 py-1.5 rounded-lg bg-white/[0.015] border border-white/[0.04] text-[10px] font-mono text-slate-500 flex items-center justify-between">
                  <span>HOVER SOCKET FOR MICRO-HUD</span>
                  <span>KEYS [← ↑ → ↓]</span>
                </div>
              )}

              {/* Physical HTOL Socket Fixture with Coordinate Rails */}
              <div className="p-2.5 rounded-lg bg-black/40 border border-white/[0.06] relative">
                {/* Top Column Rail: 01 to 08 */}
                <div className="flex items-center mb-1 text-center text-[9px] font-mono text-slate-500 pl-4">
                  {['01', '02', '03', '04', '05', '06', '07', '08'].map(c => (
                    <span key={c} className="flex-1 text-center">{c}</span>
                  ))}
                </div>

                {/* Grid Rows with Left Row Rail (A to H) */}
                <div className="space-y-1">
                  {['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'].map((rowLetter, rowIdx) => {
                    const rowRecords = records.slice(rowIdx * 8, (rowIdx + 1) * 8);

                    return (
                      <div key={rowLetter} className="flex items-center gap-1">
                        {/* Row Coordinate Letter */}
                        <span className="w-3 text-center text-[9px] font-mono text-slate-500 shrink-0">
                          {rowLetter}
                        </span>

                        {/* 8 Sockets for this Row */}
                        <div className="grid grid-cols-8 gap-1 flex-1">
                          {rowRecords.map((r, colIdx) => {
                            const i = rowIdx * 8 + colIdx;
                            const isSelected = r.component_id === selectedComponentId;
                            const limitFraction = r.limits?.limit_fraction || 0;
                            const style = getThermalColor(limitFraction);

                            return (
                              <button
                                key={r.component_id}
                                onClick={() => {
                                  playMechanicalClick();
                                  setSelectedComponentId(r.component_id);
                                }}
                                onMouseEnter={() => {
                                  playTick();
                                  setHoveredRecord(r);
                                }}
                                onMouseLeave={() => setHoveredRecord(null)}
                                title={`Socket ${rowLetter}${colIdx+1} (Pos #${r.context?.board_position || i+1}): ${r.component_id} (${r.latest_value} µA)`}
                                className={`
                                  relative aspect-square rounded flex flex-col items-center justify-center p-0.5 cursor-pointer
                                  transition-all duration-100 select-none group/socket
                                  ${style.bg}
                                  ${
                                    isSelected
                                      ? 'ring-2 ring-orange-400 scale-110 z-20 shadow-[0_0_12px_rgba(249,115,22,0.5)]'
                                      : 'hover:scale-105 active:scale-95'
                                  }
                                  border ${isSelected ? 'border-orange-400' : style.border}
                                `}
                              >
                                {/* Gold Corner Pin Accents (Semiconductor DIP Socket Detail) */}
                                <span className="absolute top-0.5 left-0.5 w-0.5 h-0.5 rounded-full bg-amber-400/40 opacity-50" />
                                <span className="absolute top-0.5 right-0.5 w-0.5 h-0.5 rounded-full bg-amber-400/40 opacity-50" />

                                <span className={`text-[8px] font-mono ${style.text}`}>
                                  {String(r.context?.board_position || (i + 1)).padStart(2, '0')}
                                </span>
                                <span className={`w-1 h-1 rounded-full mt-0.5 ${style.dot}`} />
                              </button>
                            );
                          })}
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Thermal Scale Legend */}
                <div className="mt-3 pt-2 border-t border-white/[0.04] flex flex-wrap items-center justify-between text-[9px] font-mono text-slate-400 gap-1.5 pl-3">
                  <div className="flex items-center gap-1">
                    <span className="w-2 h-2 rounded bg-white/[0.03] border border-white/[0.06]" />
                    <span>&lt;0.05 µA</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <span className="w-2 h-2 rounded bg-white/[0.06] border border-white/[0.08]" />
                    <span>0.10 µA</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <span className="w-2 h-2 rounded bg-orange-950/60 border border-orange-500/30" />
                    <span>0.15 µA</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <span className="w-2 h-2 rounded bg-orange-600/75" />
                    <span>0.20 µA</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <span className="w-2 h-2 rounded bg-orange-500 shadow-[0_0_6px_rgba(249,115,22,0.8)]" />
                    <span className="text-orange-300">≥0.25 µA</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Selected Socket Telemetry Card */}
            {selectedRecord && (
              <div className="mt-3 p-3 rounded-lg bg-white/[0.02] border border-white/[0.04] space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5 font-mono text-xs">
                    <span className="text-slate-500">LOCKED:</span>
                    <strong className="text-orange-400 font-medium">{selectedRecord.component_id}</strong>
                    <span className="text-[10px] text-slate-500">(Pos #{selectedRecord.context?.board_position})</span>
                  </div>
                  <DecisionBadge decision={selectedRecord.recommendation} size="sm" />
                </div>

                <div className="grid grid-cols-2 gap-1.5 text-xs font-mono">
                  <div className="p-2 rounded bg-white/[0.02]">
                    <span className="text-[10px] text-slate-400 block">24h Current</span>
                    <span className="text-white font-medium">{selectedRecord.latest_value} µA</span>
                  </div>
                  <div className="p-2 rounded bg-white/[0.02]">
                    <span className="text-[10px] text-slate-400 block">168h Forecast</span>
                    <span className="text-orange-400 font-medium">{selectedRecord.forecast.predicted_final_value} µA</span>
                  </div>
                  <div className="p-2 rounded bg-white/[0.02]">
                    <span className="text-[10px] text-slate-400 block">Robust Z</span>
                    <span className="text-slate-300 font-medium">+{selectedRecord.peers.current_batch_robust_z}σ</span>
                  </div>
                  <div className="p-2 rounded bg-white/[0.02]">
                    <span className="text-[10px] text-slate-400 block">Channel</span>
                    <span className="text-slate-300 font-medium">CH-{selectedRecord.context?.tester_channel}</span>
                  </div>
                </div>

                <button
                  onClick={() => onInspectComponent(selectedRecord.component_id)}
                  className="btn-primary w-full py-2 flex items-center justify-center gap-1.5 text-xs font-mono"
                >
                  <ExternalLink className="w-3.5 h-3.5" strokeWidth={1.5} />
                  <span>Inspect Telemetry</span>
                </button>
              </div>
            )}
          </SquircleCard>
        </div>
      </div>
    </div>
  );
}
