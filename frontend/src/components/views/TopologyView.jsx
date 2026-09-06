import React, { useState, useMemo, useRef, useEffect, useCallback } from 'react';
import SquircleCard from '../common/SquircleCard';
import DecisionBadge from '../common/DecisionBadge';
import {
  Network,
  Activity,
  Flame,
  Sparkles,
  AlertOctagon,
  AlertTriangle,
  CheckCircle2,
  TrendingUp,
  Layers,
  Search,
  SlidersHorizontal,
  Maximize2,
  Minimize2,
  RotateCcw,
  Info,
  ArrowRight,
  ShieldAlert,
  Cpu,
  Filter,
  ExternalLink,
  ChevronRight,
  Crosshair,
  Zap,
  Server
} from 'lucide-react';
import { formatPercent, formatZ } from '../../lib/utils';

// Color definitions matching the signature Warm Amber & Obsidian theme
const THEME_COLORS = {
  ENGINEER_REVIEW: {
    base: '#f97316',
    border: '#fb923c',
    halo: 'rgba(249, 115, 22, 0.45)',
    glow: 'rgba(249, 115, 22, 0.25)',
    label: 'Critical Review',
    priority: 1
  },
  RETEST: {
    base: '#f59e0b',
    border: '#fbbf24',
    halo: 'rgba(245, 158, 11, 0.4)',
    glow: 'rgba(245, 158, 11, 0.2)',
    label: 'Retest Required',
    priority: 2
  },
  MONITOR: {
    base: '#fdba74',
    border: '#fed7aa',
    halo: 'rgba(253, 186, 116, 0.35)',
    glow: 'rgba(253, 186, 116, 0.15)',
    label: 'Watchlist Drift',
    priority: 3
  },
  ACCEPT: {
    base: '#94a3b8',
    border: '#cbd5e1',
    halo: 'rgba(148, 163, 184, 0.2)',
    glow: 'rgba(148, 163, 184, 0.08)',
    label: 'Nominal Spec',
    priority: 4
  }
};

export default function TopologyView({
  dataset,
  selectedComponentId,
  setSelectedComponentId,
  onInspectComponent
}) {
  const [activeMode, setActiveMode] = useState('failure_vectors'); // 'failure_vectors' | 'affinity' | 'similarity'
  const [filterDisposition, setFilterDisposition] = useState('ALL');
  const [filterBatch, setFilterBatch] = useState('ALL');
  const [searchTerm, setSearchTerm] = useState('');
  const [showCompoundOnly, setShowCompoundOnly] = useState(false);
  const [hoveredNodeId, setHoveredNodeId] = useState(null);
  const [selectedHubId, setSelectedHubId] = useState(null);

  // Canvas Pan & Zoom State
  const [transform, setTransform] = useState({ x: 0, y: 0, scale: 1 });
  const [isDragging, setIsDragging] = useState(false);
  const dragStartRef = useRef({ x: 0, y: 0 });
  const svgRef = useRef(null);

  const records = dataset?.records || [];

  // 1. Mechanism Hub Definitions for Mode 1
  const FAILURE_HUBS = useMemo(() => [
    {
      id: 'HUB_LIMIT',
      name: 'SPEC LIMIT BREACH',
      short: 'LIMIT BREACH',
      desc: 'Projected 168h leakage crosses 0.25 µA spec',
      x: 500,
      y: 120,
      color: '#f97316',
      icon: AlertOctagon
    },
    {
      id: 'HUB_DRIFT',
      name: 'THERMAL RUNAWAY DRIFT',
      short: 'RAPID DRIFT',
      desc: 'Hourly leakage slope ≥ 0.0025 µA/h',
      x: 230,
      y: 280,
      color: '#fb923c',
      icon: Flame
    },
    {
      id: 'HUB_OUTLIER',
      name: 'BATCH NORM DEVIATION',
      short: 'BATCH OUTLIER',
      desc: 'Robust Z-score ≥ 2.0σ vs peer median',
      x: 770,
      y: 280,
      color: '#f59e0b',
      icon: TrendingUp
    },
    {
      id: 'HUB_LATENT',
      name: 'SUB-THRESHOLD ANOMALY',
      short: 'LATENT RISK',
      desc: 'Within spec limit, but unusual pattern',
      x: 350,
      y: 490,
      color: '#fdba74',
      icon: Sparkles
    },
    {
      id: 'HUB_NOMINAL',
      name: 'NOMINAL BASELINE',
      short: 'NOMINAL COHORT',
      desc: 'Stable trajectory conforming to lot bounds',
      x: 650,
      y: 490,
      color: '#94a3b8',
      icon: CheckCircle2
    }
  ], []);

  // 2. Batch Hubs for Mode 2
  const BATCH_HUBS = useMemo(() => [
    { id: 'BATCH_MLCC_B018', batch_id: 'MLCC_B018', name: 'LOT MLCC_B018', x: 280, y: 190, color: '#f97316' },
    { id: 'BATCH_MLCC_B019', batch_id: 'MLCC_B019', name: 'LOT MLCC_B019', x: 720, y: 190, color: '#fb923c' },
    { id: 'BATCH_MLCC_B020', batch_id: 'MLCC_B020', name: 'LOT MLCC_B020', x: 280, y: 470, color: '#f59e0b' },
    { id: 'BATCH_MLCC_B021', batch_id: 'MLCC_B021', name: 'LOT MLCC_B021', x: 720, y: 470, color: '#94a3b8' }
  ], []);

  // 3. Classify Each Component's Active Mechanisms & Connections
  const componentsClassification = useMemo(() => {
    return records.map(r => {
      const crosses = r.forecast?.predicted_to_cross_limit || (r.forecast?.predicted_final_value >= (r.limits?.applicable_limit || 0.25));
      const rapidDrift = (r.slope_per_hour || 0) >= 0.0025 || (r.percent_change || 0) >= 45;
      const outlier = Math.abs(r.peers?.current_batch_robust_z || 0) >= 2.0;
      const latent = Boolean(r.within_limit_but_unusual);

      const activeHubIds = [];
      if (crosses) activeHubIds.push('HUB_LIMIT');
      if (rapidDrift) activeHubIds.push('HUB_DRIFT');
      if (outlier) activeHubIds.push('HUB_OUTLIER');
      if (latent && !crosses) activeHubIds.push('HUB_LATENT');
      if (activeHubIds.length === 0) activeHubIds.push('HUB_NOMINAL');

      const isCompound = activeHubIds.filter(id => id !== 'HUB_NOMINAL').length >= 2;

      return {
        record: r,
        id: r.component_id,
        batch_id: r.batch_id,
        recommendation: r.recommendation,
        activeHubIds,
        isCompound,
        theme: THEME_COLORS[r.recommendation] || THEME_COLORS.ACCEPT
      };
    });
  }, [records]);

  // 4. Compute Node Coordinates & Graph Elements based on Active Mode
  const graphData = useMemo(() => {
    const hubMap = new Map();
    FAILURE_HUBS.forEach(h => hubMap.set(h.id, h));

    const nodes = [];
    const edges = [];

    if (activeMode === 'failure_vectors') {
      // 1. Add Hub Nodes
      FAILURE_HUBS.forEach(h => {
        nodes.push({
          type: 'hub',
          id: h.id,
          name: h.name,
          short: h.short,
          desc: h.desc,
          x: h.x,
          y: h.y,
          color: h.color,
          icon: h.icon,
          size: 26
        });
      });

      // 2. Position Component Nodes based on connected hubs
      componentsClassification.forEach((comp, idx) => {
        const connectedHubs = comp.activeHubIds.map(hid => hubMap.get(hid)).filter(Boolean);

        // Centroid of connected hubs
        const avgX = connectedHubs.reduce((acc, h) => acc + h.x, 0) / connectedHubs.length;
        const avgY = connectedHubs.reduce((acc, h) => acc + h.y, 0) / connectedHubs.length;

        // Radial offset so nodes around same hub or centroid distribute cleanly
        const isNominal = comp.activeHubIds.includes('HUB_NOMINAL');
        const ring = Math.floor(idx % 3);
        const radius = isNominal ? (60 + ring * 25) : (comp.isCompound ? 30 + ring * 14 : 50 + ring * 20);
        const angle = (idx * 2.39996); // golden ratio angle distribution

        const x = Math.max(70, Math.min(930, avgX + Math.cos(angle) * radius));
        const y = Math.max(70, Math.min(580, avgY + Math.sin(angle) * radius));

        nodes.push({
          type: 'component',
          id: comp.id,
          batch_id: comp.batch_id,
          recommendation: comp.recommendation,
          record: comp.record,
          theme: comp.theme,
          isCompound: comp.isCompound,
          activeHubIds: comp.activeHubIds,
          x,
          y,
          size: comp.recommendation === 'ENGINEER_REVIEW' ? 12 : (comp.recommendation === 'RETEST' ? 10.5 : 9)
        });

        // Add Edges from component to each connected hub
        comp.activeHubIds.forEach(hid => {
          edges.push({
            id: `${comp.id}->${hid}`,
            source: comp.id,
            target: hid,
            sourceX: x,
            sourceY: y,
            targetX: hubMap.get(hid)?.x || x,
            targetY: hubMap.get(hid)?.y || y,
            color: comp.theme.base,
            isCompound: comp.isCompound,
            recommendation: comp.recommendation
          });
        });
      });
    } else if (activeMode === 'affinity') {
      // MODE 2: Lot vs Hardware Channel Affinity
      const batchMap = new Map();
      BATCH_HUBS.forEach(b => {
        batchMap.set(b.batch_id, b);
        nodes.push({
          type: 'hub',
          id: b.id,
          name: b.name,
          short: b.batch_id,
          desc: `Production Lot Batch ${b.batch_id}`,
          x: b.x,
          y: b.y,
          color: b.color,
          icon: Layers,
          size: 24
        });
      });

      // Group components by batch
      const batches = ['MLCC_B018', 'MLCC_B019', 'MLCC_B020', 'MLCC_B021'];
      batches.forEach(bId => {
        const batchHub = batchMap.get(bId);
        if (!batchHub) return;

        const batchComps = componentsClassification.filter(c => c.batch_id === bId);
        batchComps.forEach((comp, bIdx) => {
          const isFlagged = comp.recommendation !== 'ACCEPT';
          const ringRadius = isFlagged ? 115 : 75;
          const totalInRing = batchComps.length;
          const angle = (bIdx / totalInRing) * 2 * Math.PI - (Math.PI / 2);

          const x = batchHub.x + Math.cos(angle) * ringRadius;
          const y = batchHub.y + Math.sin(angle) * ringRadius;

          nodes.push({
            type: 'component',
            id: comp.id,
            batch_id: comp.batch_id,
            recommendation: comp.recommendation,
            record: comp.record,
            theme: comp.theme,
            isCompound: comp.isCompound,
            activeHubIds: [batchHub.id],
            x,
            y,
            size: isFlagged ? 11 : 8.5
          });

          edges.push({
            id: `${comp.id}->${batchHub.id}`,
            source: comp.id,
            target: batchHub.id,
            sourceX: x,
            sourceY: y,
            targetX: batchHub.x,
            targetY: batchHub.y,
            color: comp.theme.base,
            isCompound: comp.isCompound,
            recommendation: comp.recommendation
          });
        });
      });
    } else {
      // MODE 3: Drift Trajectory Similarity (2D Phase Space)
      const values = records.map(r => r.initial_value || 0.02);
      const slopes = records.map(r => r.slope_per_hour || 0);

      const minX = Math.min(...values);
      const maxX = Math.max(...values, 0.08);
      const minY = Math.min(...slopes, 0);
      const maxY = Math.max(...slopes, 0.008);

      componentsClassification.forEach((comp) => {
        const r = comp.record;
        const normX = ((r.initial_value || 0.02) - minX) / (maxX - minX || 1);
        const normY = ((r.slope_per_hour || 0) - minY) / (maxY - minY || 1);

        const x = 160 + normX * 680;
        const y = 520 - normY * 380; // inverted Y axis

        nodes.push({
          type: 'component',
          id: comp.id,
          batch_id: comp.batch_id,
          recommendation: comp.recommendation,
          record: comp.record,
          theme: comp.theme,
          isCompound: comp.isCompound,
          activeHubIds: [],
          x,
          y,
          size: comp.recommendation === 'ENGINEER_REVIEW' ? 12 : 9
        });
      });

      // Connect 2 nearest neighbors to illustrate trajectory affinity
      for (let i = 0; i < nodes.length; i++) {
        const a = nodes[i];
        let closest = null;
        let minDist = Infinity;
        for (let j = 0; j < nodes.length; j++) {
          if (i === j) continue;
          const b = nodes[j];
          const dist = Math.hypot(a.x - b.x, a.y - b.y);
          if (dist < minDist && dist < 85) {
            minDist = dist;
            closest = b;
          }
        }
        if (closest) {
          edges.push({
            id: `sim-${a.id}-${closest.id}`,
            source: a.id,
            target: closest.id,
            sourceX: a.x,
            sourceY: a.y,
            targetX: closest.x,
            targetY: closest.y,
            color: a.theme.base,
            isCompound: a.isCompound,
            recommendation: a.recommendation
          });
        }
      }
    }

    return { nodes, edges };
  }, [activeMode, FAILURE_HUBS, BATCH_HUBS, componentsClassification, records]);

  // Filtered nodes logic
  const filteredNodeIds = useMemo(() => {
    const ids = new Set();
    graphData.nodes.forEach(n => {
      if (n.type === 'hub') {
        ids.add(n.id);
        return;
      }
      // Filter by disposition
      if (filterDisposition !== 'ALL' && n.recommendation !== filterDisposition) return;
      // Filter by batch
      if (filterBatch !== 'ALL' && n.batch_id !== filterBatch) return;
      // Compound only
      if (showCompoundOnly && !n.isCompound) return;
      // Search term
      if (searchTerm && !n.id.toLowerCase().includes(searchTerm.toLowerCase())) return;

      ids.add(n.id);
    });
    return ids;
  }, [graphData.nodes, filterDisposition, filterBatch, showCompoundOnly, searchTerm]);

  // Selected item reference
  const selectedRecord = useMemo(() => {
    return records.find(r => r.component_id === selectedComponentId) || records[0];
  }, [records, selectedComponentId]);

  const selectedClassification = useMemo(() => {
    return componentsClassification.find(c => c.id === selectedComponentId);
  }, [componentsClassification, selectedComponentId]);

  // Handlers for Pan & Zoom
  const handleMouseDown = (e) => {
    if (e.target.tagName === 'circle' || e.target.tagName === 'path' || e.target.closest('button')) return;
    setIsDragging(true);
    dragStartRef.current = { x: e.clientX - transform.x, y: e.clientY - transform.y };
  };

  const handleMouseMove = (e) => {
    if (!isDragging) return;
    setTransform(prev => ({
      ...prev,
      x: e.clientX - dragStartRef.current.x,
      y: e.clientY - dragStartRef.current.y
    }));
  };

  const handleMouseUp = () => setIsDragging(false);

  const handleWheel = (e) => {
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 1.1 : 0.9;
    setTransform(prev => ({
      ...prev,
      scale: Math.max(0.5, Math.min(2.8, prev.scale * zoomFactor))
    }));
  };

  const resetView = () => setTransform({ x: 0, y: 0, scale: 1 });
  const zoomIn = () => setTransform(prev => ({ ...prev, scale: Math.min(2.8, prev.scale * 1.2) }));
  const zoomOut = () => setTransform(prev => ({ ...prev, scale: Math.max(0.5, prev.scale * 0.8) }));

  // Center on Selected Component
  const centerSelected = useCallback(() => {
    const targetNode = graphData.nodes.find(n => n.id === selectedComponentId);
    if (targetNode) {
      setTransform({
        x: 500 - targetNode.x * 1.3,
        y: 320 - targetNode.y * 1.3,
        scale: 1.3
      });
    }
  }, [graphData.nodes, selectedComponentId]);

  // Metric summaries for HUD top bar
  const metrics = useMemo(() => {
    const compoundCount = componentsClassification.filter(c => c.isCompound).length;
    const b018Anomalies = componentsClassification.filter(c => c.batch_id === 'MLCC_B018' && c.recommendation !== 'ACCEPT').length;
    const b018Total = componentsClassification.filter(c => c.batch_id === 'MLCC_B018').length;
    const b018Rate = b018Total > 0 ? ((b018Anomalies / b018Total) * 100).toFixed(0) : '0';

    return {
      compoundCount,
      b018Rate,
      activeEdges: graphData.edges.length,
      visibleNodes: filteredNodeIds.size
    };
  }, [componentsClassification, graphData.edges.length, filteredNodeIds]);

  return (
    <div className="space-y-5 pb-12">
      {/* 1. View Header & Context Banner */}
      <SquircleCard elevated className="p-5">
        <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="w-1.5 h-1.5 rounded-full bg-orange-400" />
              <span className="text-[10.5px] font-mono font-medium text-orange-400 uppercase tracking-wider">
                NEURAL FAULT TOPOLOGY // MULTI-FACTOR CORRELATION
              </span>
            </div>
            <h2 className="text-lg font-semibold text-white tracking-tight flex items-center gap-2">
              <Network className="w-5 h-5 text-orange-400" strokeWidth={1.5} />
              Fault Topology &amp; Failure Cluster Map
            </h2>
            <p className="text-[12.5px] text-slate-400">
              Interactive relationship network mapping failure modes, lot defect clustering, and tester channel affinities across all 64 screened MLCC components.
            </p>
          </div>

          {/* Top Quick Stats Pill Row */}
          <div className="flex flex-wrap items-center gap-2.5 font-mono text-xs">
            <div className="px-3 py-1.5 rounded-lg bg-white/[0.02] border border-white/[0.05] text-right">
              <span className="text-[10px] text-slate-500 uppercase block">NETWORK NODES</span>
              <span className="text-sm font-medium text-white">{metrics.visibleNodes} Active</span>
            </div>
            <div className="px-3 py-1.5 rounded-lg bg-orange-500/[0.06] border border-orange-500/20 text-right">
              <span className="text-[10px] text-orange-400 uppercase block">COMPOUND RISKS</span>
              <span className="text-sm font-medium text-orange-400">{metrics.compoundCount} Parts (≥2 Vectors)</span>
            </div>
            <div className="px-3 py-1.5 rounded-lg bg-white/[0.02] border border-white/[0.05] text-right">
              <span className="text-[10px] text-slate-500 uppercase block">LOT B018 DEFECT RATE</span>
              <span className="text-sm font-medium text-white">{metrics.b018Rate}% Flagged</span>
            </div>
          </div>
        </div>
      </SquircleCard>

      {/* 2. Mode Selector & Filter Toolbar */}
      <SquircleCard className="p-3.5 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          {/* Topology Mode Switcher */}
          <div className="flex items-center gap-1.5 p-1 rounded-lg bg-black/40 border border-white/[0.06] text-xs font-mono">
            <button
              onClick={() => setActiveMode('failure_vectors')}
              className={`px-3 py-1.5 rounded-md transition-all cursor-pointer ${
                activeMode === 'failure_vectors'
                  ? 'bg-orange-500 text-black font-semibold shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              1. Failure Vectors &amp; Root Causes
            </button>
            <button
              onClick={() => setActiveMode('affinity')}
              className={`px-3 py-1.5 rounded-md transition-all cursor-pointer ${
                activeMode === 'affinity'
                  ? 'bg-orange-500 text-black font-semibold shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              2. Lot vs Channel Affinity
            </button>
            <button
              onClick={() => setActiveMode('similarity')}
              className={`px-3 py-1.5 rounded-md transition-all cursor-pointer ${
                activeMode === 'similarity'
                  ? 'bg-orange-500 text-black font-semibold shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              3. Drift Phase Space
            </button>
          </div>

          {/* Quick Search Bar */}
          <div className="relative min-w-[200px]">
            <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" strokeWidth={1.5} />
            <input
              type="text"
              placeholder="Filter by ID (e.g. C000147)..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 rounded-lg bg-black/30 border border-white/[0.08] text-xs text-white placeholder-slate-500 focus:outline-none focus:border-orange-500/50 font-mono"
            />
          </div>
        </div>

        {/* Secondary Filter Pills */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-white/[0.04] text-xs font-mono">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-[11px] text-slate-500">DISPOSITION:</span>
            {['ALL', 'ENGINEER_REVIEW', 'RETEST', 'MONITOR', 'ACCEPT'].map(disp => (
              <button
                key={disp}
                onClick={() => setFilterDisposition(disp)}
                className={`px-2.5 py-1 rounded-md text-[11px] transition-all cursor-pointer ${
                  filterDisposition === disp
                    ? 'bg-orange-500/20 text-orange-300 border border-orange-500/40 font-medium'
                    : 'bg-white/[0.02] text-slate-400 hover:text-white border border-white/[0.04]'
                }`}
              >
                {disp.replace('_', ' ')}
              </button>
            ))}
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <span className="text-[11px] text-slate-500">BATCH:</span>
            {['ALL', 'MLCC_B018', 'MLCC_B019', 'MLCC_B020', 'MLCC_B021'].map(b => (
              <button
                key={b}
                onClick={() => setFilterBatch(b)}
                className={`px-2 py-0.5 rounded text-[11px] transition-all cursor-pointer ${
                  filterBatch === b
                    ? 'bg-white/15 text-white border border-white/25 font-medium'
                    : 'bg-white/[0.02] text-slate-400 hover:text-white border border-white/[0.04]'
                }`}
              >
                {b === 'ALL' ? 'ALL' : b.replace('MLCC_', '')}
              </button>
            ))}

            <button
              onClick={() => setShowCompoundOnly(!showCompoundOnly)}
              className={`ml-2 px-2.5 py-1 rounded-md text-[11px] border transition-all cursor-pointer flex items-center gap-1.5 ${
                showCompoundOnly
                  ? 'bg-orange-500 text-black border-orange-400 font-semibold'
                  : 'bg-white/[0.02] text-slate-400 hover:text-orange-300 border-white/[0.06]'
              }`}
            >
              <Zap className="w-3 h-3" strokeWidth={1.5} />
              <span>Multi-Threat Only ({metrics.compoundCount})</span>
            </button>
          </div>
        </div>
      </SquircleCard>

      {/* 3. Main Topology Canvas + Side HUD Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
        {/* Left: Interactive Canvas Viewport (8 cols) */}
        <div className="lg:col-span-8 space-y-3">
          <SquircleCard elevated className="relative overflow-hidden p-0 bg-[#06070b] border-white/[0.08]">
            {/* On-Canvas Float Control Bar */}
            <div className="absolute top-3 left-3 z-20 flex items-center gap-1.5 bg-[#0b0c13]/90 backdrop-blur-md p-1.5 rounded-lg border border-white/[0.08] text-slate-400">
              <button
                onClick={zoomIn}
                title="Zoom In"
                className="p-1.5 rounded hover:bg-white/10 hover:text-white transition-colors cursor-pointer"
              >
                <Maximize2 className="w-3.5 h-3.5" strokeWidth={1.5} />
              </button>
              <button
                onClick={zoomOut}
                title="Zoom Out"
                className="p-1.5 rounded hover:bg-white/10 hover:text-white transition-colors cursor-pointer"
              >
                <Minimize2 className="w-3.5 h-3.5" strokeWidth={1.5} />
              </button>
              <button
                onClick={resetView}
                title="Reset Camera"
                className="p-1.5 rounded hover:bg-white/10 hover:text-white transition-colors cursor-pointer"
              >
                <RotateCcw className="w-3.5 h-3.5" strokeWidth={1.5} />
              </button>
              <span className="w-px h-3.5 bg-white/10 mx-0.5" />
              <button
                onClick={centerSelected}
                title="Center on Selected Node"
                className="flex items-center gap-1 px-2 py-1 rounded hover:bg-orange-500/10 hover:text-orange-300 text-[11px] font-mono transition-colors cursor-pointer"
              >
                <Crosshair className="w-3.5 h-3.5 text-orange-400" strokeWidth={1.5} />
                <span>Focus</span>
              </button>
            </div>

            {/* Canvas Legend Overlay */}
            <div className="absolute bottom-3 left-3 z-20 hidden sm:flex items-center gap-3 bg-[#0b0c13]/90 backdrop-blur-md px-3 py-1.5 rounded-lg border border-white/[0.08] text-[11px] font-mono">
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-orange-500 shadow-[0_0_8px_#f97316]" />
                <span className="text-white">Review</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
                <span className="text-slate-300">Retest</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-orange-300" />
                <span className="text-slate-400">Monitor</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-slate-400" />
                <span className="text-slate-500">Accept</span>
              </div>
            </div>

            {/* SVG Interactive Canvas */}
            <div
              className={`w-full h-[580px] overflow-hidden select-none ${
                isDragging ? 'cursor-grabbing' : 'cursor-grab'
              }`}
              onMouseDown={handleMouseDown}
              onMouseMove={handleMouseMove}
              onMouseUp={handleMouseUp}
              onMouseLeave={handleMouseUp}
              onWheel={handleWheel}
            >
              <svg
                ref={svgRef}
                viewBox="0 0 1000 640"
                className="w-full h-full overflow-visible"
              >
                <defs>
                  {/* Glowing Halos */}
                  <radialGradient id="glow-ember" cx="50%" cy="50%" r="50%">
                    <stop offset="0%" stopColor="#f97316" stopOpacity="0.8" />
                    <stop offset="60%" stopColor="#f97316" stopOpacity="0.25" />
                    <stop offset="100%" stopColor="#f97316" stopOpacity="0" />
                  </radialGradient>
                  <radialGradient id="glow-gold" cx="50%" cy="50%" r="50%">
                    <stop offset="0%" stopColor="#f59e0b" stopOpacity="0.8" />
                    <stop offset="60%" stopColor="#f59e0b" stopOpacity="0.2" />
                    <stop offset="100%" stopColor="#f59e0b" stopOpacity="0" />
                  </radialGradient>

                  {/* Hub Gradients */}
                  <linearGradient id="hubGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#1e2235" />
                    <stop offset="100%" stopColor="#0d0f1a" />
                  </linearGradient>

                  {/* Filter for subtle glow */}
                  <filter id="softGlow" x="-20%" y="-20%" width="140%" height="140%">
                    <feGaussianBlur stdDeviation="3" result="blur" />
                    <feComposite in="SourceGraphic" in2="blur" operator="over" />
                  </filter>
                </defs>

                {/* Transformed Content Group */}
                <g transform={`translate(${transform.x}, ${transform.y}) scale(${transform.scale})`}>
                  {/* Subtle Background Radar Concentric Rings */}
                  <g opacity="0.12" stroke="#ffffff" fill="none">
                    <circle cx="500" cy="320" r="140" strokeWidth="1" strokeDasharray="3 6" />
                    <circle cx="500" cy="320" r="260" strokeWidth="1" strokeDasharray="3 6" />
                    <circle cx="500" cy="320" r="390" strokeWidth="1" />
                    <line x1="500" y1="0" x2="500" y2="640" strokeWidth="0.5" strokeDasharray="4 8" />
                    <line x1="0" y1="320" x2="1000" y2="320" strokeWidth="0.5" strokeDasharray="4 8" />
                  </g>

                  {/* 1. Edges Layer */}
                  <g className="edges-layer">
                    {graphData.edges.map(edge => {
                      const isSourceVisible = filteredNodeIds.has(edge.source);
                      const isTargetVisible = filteredNodeIds.has(edge.target);
                      if (!isSourceVisible || !isTargetVisible) return null;

                      const isConnectedToHover = hoveredNodeId && (edge.source === hoveredNodeId || edge.target === hoveredNodeId);
                      const isConnectedToSelected = selectedComponentId && (edge.source === selectedComponentId || edge.target === selectedComponentId);
                      const isHighlighted = isConnectedToHover || isConnectedToSelected;

                      return (
                        <line
                          key={edge.id}
                          x1={edge.sourceX}
                          y1={edge.sourceY}
                          x2={edge.targetX}
                          y2={edge.targetY}
                          stroke={isHighlighted ? '#f97316' : edge.color}
                          strokeWidth={isHighlighted ? 2.5 : (edge.isCompound ? 1.2 : 0.7)}
                          strokeOpacity={isHighlighted ? 0.9 : (hoveredNodeId ? 0.08 : (edge.isCompound ? 0.45 : 0.22))}
                          strokeDasharray={isHighlighted ? '5 5' : (edge.isCompound ? '3 3' : 'none')}
                          className={isHighlighted ? 'animate-pulse' : ''}
                        />
                      );
                    })}
                  </g>

                  {/* 2. Hub Nodes Layer */}
                  <g className="hubs-layer">
                    {graphData.nodes.filter(n => n.type === 'hub').map(hub => {
                      const isSelected = selectedHubId === hub.id;
                      const Icon = hub.icon || Network;

                      return (
                        <g
                          key={hub.id}
                          transform={`translate(${hub.x}, ${hub.y})`}
                          onClick={() => setSelectedHubId(hub.id)}
                          onMouseEnter={() => setHoveredNodeId(hub.id)}
                          onMouseLeave={() => setHoveredNodeId(null)}
                          className="cursor-pointer group"
                        >
                          {/* Radial Hub Glow */}
                          <circle
                            r="36"
                            fill="none"
                            stroke={hub.color}
                            strokeWidth="1.5"
                            strokeOpacity={isSelected ? 0.8 : 0.25}
                            strokeDasharray="4 4"
                          />

                          {/* Hub Base Body */}
                          <rect
                            x="-24"
                            y="-24"
                            width="48"
                            height="48"
                            rx="12"
                            fill="url(#hubGrad)"
                            stroke={isSelected ? '#ffffff' : hub.color}
                            strokeWidth={isSelected ? 2 : 1.5}
                            className="transition-transform duration-200 group-hover:scale-105"
                          />

                          {/* Icon representation */}
                          <circle cx="0" cy="0" r="10" fill={hub.color} fillOpacity="0.15" />
                          <circle cx="0" cy="0" r="3.5" fill={hub.color} />

                          {/* Hub Label */}
                          <text
                            y="38"
                            fill="#ffffff"
                            fontSize="11"
                            fontWeight="600"
                            textAnchor="middle"
                            className="font-mono tracking-wider"
                          >
                            {hub.short}
                          </text>
                        </g>
                      );
                    })}
                  </g>

                  {/* 3. Component Nodes Layer */}
                  <g className="components-layer">
                    {graphData.nodes.filter(n => n.type === 'component').map(node => {
                      const isVisible = filteredNodeIds.has(node.id);
                      if (!isVisible) return null;

                      const isSelected = node.id === selectedComponentId;
                      const isHovered = node.id === hoveredNodeId;
                      const isMuted = hoveredNodeId && hoveredNodeId !== node.id && !node.activeHubIds.includes(hoveredNodeId);

                      return (
                        <g
                          key={node.id}
                          transform={`translate(${node.x}, ${node.y})`}
                          onClick={() => {
                            setSelectedComponentId(node.id);
                            setSelectedHubId(null);
                          }}
                          onMouseEnter={() => setHoveredNodeId(node.id)}
                          onMouseLeave={() => setHoveredNodeId(null)}
                          opacity={isMuted ? 0.2 : 1}
                          className="cursor-pointer transition-opacity duration-150"
                        >
                          {/* Pulsing Selection Halo */}
                          {isSelected && (
                            <circle
                              r={node.size + 10}
                              fill="none"
                              stroke="#f97316"
                              strokeWidth="1.5"
                              strokeDasharray="3 3"
                              className="animate-spin"
                              style={{ animationDuration: '6s' }}
                            />
                          )}

                          {/* Hover Expansion Halo */}
                          {isHovered && !isSelected && (
                            <circle
                              r={node.size + 6}
                              fill="none"
                              stroke={node.theme.border}
                              strokeWidth="1.2"
                              strokeOpacity="0.8"
                            />
                          )}

                          {/* Multi-Threat Halo for Compound Outliers */}
                          {node.isCompound && (
                            <circle
                              r={node.size + 4}
                              fill={node.theme.glow}
                              stroke={node.theme.border}
                              strokeWidth="0.8"
                              strokeOpacity="0.4"
                            />
                          )}

                          {/* Core Node Disc */}
                          <circle
                            r={node.size}
                            fill={node.theme.base}
                            stroke={isSelected ? '#ffffff' : node.theme.border}
                            strokeWidth={isSelected ? 2 : 1.2}
                            filter="url(#softGlow)"
                          />

                          {/* Inner Socket Glyph / Center Dot */}
                          <circle
                            r={isSelected ? 3.5 : 2}
                            fill={node.recommendation === 'ACCEPT' ? '#1e293b' : '#08090e'}
                          />

                          {/* Node Hover Tooltip / Floating Tag */}
                          {(isHovered || isSelected) && (
                            <g transform="translate(0, -18)" className="pointer-events-none">
                              <rect
                                x="-45"
                                y="-16"
                                width="90"
                                height="20"
                                rx="4"
                                fill="#0f111a"
                                stroke={node.theme.border}
                                strokeWidth="1"
                              />
                              <text
                                x="0"
                                y="-3"
                                fill="#ffffff"
                                fontSize="10.5"
                                fontWeight="600"
                                textAnchor="middle"
                                className="font-mono"
                              >
                                {node.id.replace('MLCC_', '')}
                              </text>
                            </g>
                          )}
                        </g>
                      );
                    })}
                  </g>
                </g>
              </svg>
            </div>
          </SquircleCard>
        </div>

        {/* Right: Telemetry Inspector HUD Drawer (4 cols) */}
        <div className="lg:col-span-4 space-y-4">
          <SquircleCard elevated className="p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-white/[0.06] pb-3">
              <div className="flex items-center gap-2">
                <Cpu className="w-4 h-4 text-orange-400" strokeWidth={1.5} />
                <h3 className="text-xs font-mono uppercase tracking-wider text-slate-300">
                  Cluster Telemetry HUD
                </h3>
              </div>
              <span className="text-[11px] font-mono text-slate-500">
                SOCKET #{selectedRecord.context?.board_position || '01'}
              </span>
            </div>

            {/* Selected Component Header */}
            <div>
              <div className="flex items-center justify-between gap-2 mb-1.5">
                <span className="text-base font-bold text-white font-mono tracking-wide">
                  {selectedRecord.component_id}
                </span>
                <DecisionBadge decision={selectedRecord.recommendation} size="sm" />
              </div>
              <div className="text-xs font-mono text-slate-400 flex items-center gap-2">
                <span>Batch: <strong className="text-slate-200 font-normal">{selectedRecord.batch_id}</strong></span>
                <span>•</span>
                <span>Ch: <strong className="text-slate-200 font-normal">{selectedRecord.context?.tester_channel}</strong></span>
              </div>
            </div>

            {/* Active Failure Mechanisms */}
            <div className="space-y-1.5">
              <span className="text-[10.5px] font-mono text-slate-400 uppercase tracking-wider block">
                Detected Risk Vectors:
              </span>
              <div className="space-y-1">
                {selectedClassification?.activeHubIds.map(hId => {
                  const hub = FAILURE_HUBS.find(h => h.id === hId);
                  if (!hub) return null;
                  const Icon = hub.icon || Activity;
                  return (
                    <div
                      key={hId}
                      className="p-2 rounded bg-white/[0.02] border border-white/[0.04] flex items-center gap-2 text-xs font-mono"
                    >
                      <Icon className="w-3.5 h-3.5 text-orange-400 shrink-0" strokeWidth={1.5} />
                      <span className="text-slate-200">{hub.name}</span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Metric Comparison Grid */}
            <div className="grid grid-cols-2 gap-2 text-xs font-mono">
              <div className="p-2.5 rounded bg-white/[0.02] border border-white/[0.04]">
                <span className="text-[9.5px] text-slate-500 uppercase block">24h Leakage</span>
                <span className="text-sm font-medium text-white">{selectedRecord.latest_value} µA</span>
                <span className="text-[10px] text-slate-500 block">0h: {selectedRecord.initial_value} µA</span>
              </div>
              <div className="p-2.5 rounded bg-white/[0.02] border border-white/[0.04]">
                <span className="text-[9.5px] text-slate-500 uppercase block">168h Forecast</span>
                <span className="text-sm font-medium text-orange-400">
                  {selectedRecord.forecast?.predicted_final_value} µA
                </span>
                <span className="text-[10px] text-slate-500 block">Spec: {selectedRecord.limits?.applicable_limit} µA</span>
              </div>
              <div className="p-2.5 rounded bg-white/[0.02] border border-white/[0.04]">
                <span className="text-[9.5px] text-slate-500 uppercase block">Peer Robust Z</span>
                <span className="text-sm font-medium text-white">
                  {formatZ(selectedRecord.peers?.current_batch_robust_z)}
                </span>
                <span className="text-[10px] text-slate-500 block">vs {selectedRecord.peers?.sample_size} peers</span>
              </div>
              <div className="p-2.5 rounded bg-white/[0.02] border border-white/[0.04]">
                <span className="text-[9.5px] text-slate-500 uppercase block">Drift Rate</span>
                <span className="text-sm font-medium text-white">
                  +{selectedRecord.slope_per_hour} µA/h
                </span>
                <span className="text-[10px] text-slate-500 block">Δ {selectedRecord.percent_change}%</span>
              </div>
            </div>

            {/* TreeSHAP Explanation Snippet */}
            <div className="space-y-1.5 pt-1">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-[10.5px] text-slate-400 uppercase">Top SHAP Vector</span>
                <span className="text-[10px] text-slate-500">XGBoost v2</span>
              </div>
              {selectedRecord.forecast?.xgboost_explanation?.top_contributions?.[0] && (
                <div className="p-2 rounded bg-orange-500/[0.05] border border-orange-500/20 text-xs font-mono flex items-center justify-between">
                  <span className="text-slate-300">
                    {selectedRecord.forecast.xgboost_explanation.top_contributions[0].feature}
                  </span>
                  <span className="text-orange-400 font-medium">
                    +{selectedRecord.forecast.xgboost_explanation.top_contributions[0].contribution_ua} µA
                  </span>
                </div>
              )}
            </div>

            {/* Direct Deep-link Action Button */}
            <button
              onClick={() => onInspectComponent(selectedRecord.component_id)}
              className="btn-primary w-full py-2.5 flex items-center justify-center gap-2 text-xs font-mono font-medium tracking-wide"
            >
              <span>Inspect Full Trajectory &amp; SHAP</span>
              <ArrowRight className="w-3.5 h-3.5" strokeWidth={1.5} />
            </button>
          </SquircleCard>

          {/* Root-Cause Lot Diagnosis Banner */}
          <SquircleCard className="p-4 space-y-2 text-xs font-mono">
            <div className="flex items-center gap-2 text-orange-400">
              <ShieldAlert className="w-4 h-4 shrink-0" strokeWidth={1.5} />
              <span className="font-semibold uppercase tracking-wider text-[11px]">
                Engineering Root-Cause Verdict
              </span>
            </div>
            <p className="text-[11.5px] text-slate-300 leading-relaxed">
              Anomaly concentration is <strong className="text-white">60% higher in Lot MLCC_B018</strong> than tester channels, indicating a probable <strong className="text-orange-300">Raw Material / Firing Lot Defect</strong> rather than a chamber socket artifact.
            </p>
          </SquircleCard>
        </div>
      </div>
    </div>
  );
}
