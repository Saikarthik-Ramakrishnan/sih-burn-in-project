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
  Play,
  Pause,
  ZoomIn,
  ZoomOut,
  Move,
  Compass,
  Eye,
  EyeOff,
  Sliders,
  RefreshCw,
  Wind
} from 'lucide-react';
import { formatPercent, formatZ } from '../../lib/utils';

// Color definitions: Red for error/review, Amber/Yellow for caution, Green for good/accept
const THEME_COLORS = {
  ENGINEER_REVIEW: {
    base: '#ef4444',
    border: '#f87171',
    halo: 'rgba(239, 68, 68, 0.45)',
    glow: 'rgba(239, 68, 68, 0.25)',
    label: 'REVIEW (ERROR)',
    badgeClass: 'bg-rose-500/20 text-rose-300 border-rose-500/50 backdrop-blur-md font-bold',
    dotClass: 'bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.8)]',
    priority: 1
  },
  RETEST: {
    base: '#f97316',
    border: '#fb923c',
    halo: 'rgba(249, 115, 22, 0.4)',
    glow: 'rgba(249, 115, 22, 0.2)',
    label: 'RETEST',
    badgeClass: 'bg-amber-500/15 text-amber-300 border-amber-500/35 backdrop-blur-md font-medium',
    dotClass: 'bg-amber-400 shadow-[0_0_8px_rgba(245,158,11,0.6)]',
    priority: 2
  },
  MONITOR: {
    base: '#eab308',
    border: '#fde047',
    halo: 'rgba(234, 179, 8, 0.35)',
    glow: 'rgba(234, 179, 8, 0.15)',
    label: 'MONITOR',
    badgeClass: 'bg-yellow-500/15 text-yellow-300 border-yellow-500/30 backdrop-blur-md font-medium',
    dotClass: 'bg-yellow-400 shadow-[0_0_6px_rgba(234,179,8,0.5)]',
    priority: 3
  },
  ACCEPT: {
    base: '#10b981',
    border: '#34d399',
    halo: 'rgba(16, 185, 129, 0.45)',
    glow: 'rgba(16, 185, 129, 0.25)',
    label: 'ACCEPT (GOOD)',
    badgeClass: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/35 backdrop-blur-md font-semibold',
    dotClass: 'bg-emerald-400 shadow-[0_0_8px_rgba(16,185,129,0.7)]',
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

  // Display toggles
  const [edgeMode, setEdgeMode] = useState('all'); // 'all' | 'threats_only' | 'selected' | 'hidden'
  const [nodeSizing, setNodeSizing] = useState('risk'); // 'risk' | 'uniform'
  const [showLabels, setShowLabels] = useState('hover'); // 'hover' | 'all'
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Obsidian-style Fluid Physics Configuration & State
  const [isPhysicsActive, setIsPhysicsActive] = useState(true);
  const [showForcesDrawer, setShowForcesDrawer] = useState(false);
  const [physicsParams, setPhysicsParams] = useState({
    repelStrength: 480,       // Obsidian repel force (n-body anti-gravity)
    linkDistance: 82,          // Resting length of springs
    linkStrength: 0.085,       // Elastic spring tension
    centerGravity: 0.007,      // Center pull
    viscousFriction: 0.895,    // Fluid damping / viscosity
    ambientDrift: true,        // Obsidian-style gentle cosmic breathing motion
    maxVelocity: 12
  });

  // Canvas Pan & Zoom State
  const [transform, setTransform] = useState({ x: 0, y: 0, scale: 1 });
  const [isDraggingCanvas, setIsDraggingCanvas] = useState(false);
  const [draggedNodeId, setDraggedNodeId] = useState(null);
  const [isSmoothTransition, setIsSmoothTransition] = useState(true);

  // Drag coordinates ref
  const dragStartRef = useRef({ clientX: 0, clientY: 0, origX: 0, origY: 0, panX: 0, panY: 0 });
  const svgRef = useRef(null);
  const canvasContainerRef = useRef(null);

  // Physics Simulation Buffers in Refs
  const simNodesRef = useRef([]);
  const simLinksRef = useRef([]);
  const alphaRef = useRef(1.0);
  const animFrameRef = useRef(null);
  const [simPositions, setSimPositions] = useState({});

  const records = dataset?.records || [];

  // 1. Mechanism Hub Definitions for Mode 1
  const FAILURE_HUBS = useMemo(() => [
    {
      id: 'HUB_LIMIT',
      name: 'SPEC LIMIT BREACH',
      short: 'LIMIT BREACH',
      desc: 'Projected 168h leakage crosses 0.25 µA spec',
      x: 500,
      y: 110,
      color: '#ef4444',
      icon: AlertOctagon
    },
    {
      id: 'HUB_DRIFT',
      name: 'THERMAL RUNAWAY DRIFT',
      short: 'RAPID DRIFT',
      desc: 'Hourly leakage slope ≥ 0.0025 µA/h',
      x: 230,
      y: 270,
      color: '#f97316',
      icon: Flame
    },
    {
      id: 'HUB_OUTLIER',
      name: 'BATCH NORM DEVIATION',
      short: 'BATCH OUTLIER',
      desc: 'Robust Z-score ≥ 2.0σ vs peer median',
      x: 770,
      y: 270,
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
      color: '#eab308',
      icon: Sparkles
    },
    {
      id: 'HUB_NOMINAL',
      name: 'NOMINAL BASELINE',
      short: 'NOMINAL COHORT',
      desc: 'Stable trajectory conforming to lot bounds',
      x: 650,
      y: 490,
      color: '#10b981',
      icon: CheckCircle2
    }
  ], []);

  // 2. Batch Hubs for Mode 2
  const BATCH_HUBS = useMemo(() => [
    { id: 'BATCH_MLCC_B018', batch_id: 'MLCC_B018', name: 'LOT MLCC_B018', x: 280, y: 190, color: '#f97316' },
    { id: 'BATCH_MLCC_B019', batch_id: 'MLCC_B019', name: 'LOT MLCC_B019', x: 720, y: 190, color: '#fb923c' },
    { id: 'BATCH_MLCC_B020', batch_id: 'MLCC_B020', name: 'LOT MLCC_B020', x: 280, y: 470, color: '#f59e0b' },
    { id: 'BATCH_MLCC_B021', batch_id: 'MLCC_B021', name: 'LOT MLCC_B021', x: 720, y: 470, color: '#10b981' }
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

  // 4. Compute Base Graph Data
  const baseGraphData = useMemo(() => {
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
          baseX: h.x,
          baseY: h.y,
          color: h.color,
          icon: h.icon,
          size: 26,
          mass: 5.5
        });
      });

      // 2. Position Component Nodes based on connected hubs
      componentsClassification.forEach((comp, idx) => {
        const connectedHubs = comp.activeHubIds.map(hid => hubMap.get(hid)).filter(Boolean);
        const avgX = connectedHubs.reduce((acc, h) => acc + h.x, 0) / (connectedHubs.length || 1);
        const avgY = connectedHubs.reduce((acc, h) => acc + h.y, 0) / (connectedHubs.length || 1);

        const isNominal = comp.activeHubIds.includes('HUB_NOMINAL');
        const ring = Math.floor(idx % 3);
        const radius = isNominal ? (65 + ring * 26) : (comp.isCompound ? 34 + ring * 15 : 54 + ring * 22);
        const angle = (idx * 2.39996);

        const x = Math.max(70, Math.min(930, avgX + Math.cos(angle) * radius));
        const y = Math.max(70, Math.min(570, avgY + Math.sin(angle) * radius));

        const baseSize = nodeSizing === 'risk'
          ? (comp.recommendation === 'ENGINEER_REVIEW' ? 13.5 : (comp.recommendation === 'RETEST' ? 11 : 9))
          : 9.5;

        nodes.push({
          type: 'component',
          id: comp.id,
          batch_id: comp.batch_id,
          recommendation: comp.recommendation,
          record: comp.record,
          theme: comp.theme,
          isCompound: comp.isCompound,
          activeHubIds: comp.activeHubIds,
          baseX: x,
          baseY: y,
          size: baseSize,
          mass: 1.0
        });

        comp.activeHubIds.forEach(hid => {
          edges.push({
            id: `${comp.id}->${hid}`,
            source: comp.id,
            target: hid,
            baseSourceX: x,
            baseSourceY: y,
            baseTargetX: hubMap.get(hid)?.x || x,
            baseTargetY: hubMap.get(hid)?.y || y,
            color: comp.theme.base,
            isCompound: comp.isCompound,
            recommendation: comp.recommendation,
            isThreat: hid === 'HUB_LIMIT' || hid === 'HUB_DRIFT' || hid === 'HUB_OUTLIER'
          });
        });
      });
    } else if (activeMode === 'affinity') {
      const batchMap = new Map();
      BATCH_HUBS.forEach(b => {
        batchMap.set(b.batch_id, b);
        nodes.push({
          type: 'hub',
          id: b.id,
          name: b.name,
          short: b.batch_id,
          desc: `Production Lot Batch ${b.batch_id}`,
          baseX: b.x,
          baseY: b.y,
          color: b.color,
          icon: Layers,
          size: 24,
          mass: 5.5
        });
      });

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

          const baseSize = nodeSizing === 'risk'
            ? (isFlagged ? 12 : 8.5)
            : 9.5;

          nodes.push({
            type: 'component',
            id: comp.id,
            batch_id: comp.batch_id,
            recommendation: comp.recommendation,
            record: comp.record,
            theme: comp.theme,
            isCompound: comp.isCompound,
            activeHubIds: [batchHub.id],
            baseX: x,
            baseY: y,
            size: baseSize,
            mass: 1.0
          });

          edges.push({
            id: `${comp.id}->${batchHub.id}`,
            source: comp.id,
            target: batchHub.id,
            baseSourceX: x,
            baseSourceY: y,
            baseTargetX: batchHub.x,
            baseTargetY: batchHub.y,
            color: comp.theme.base,
            isCompound: comp.isCompound,
            recommendation: comp.recommendation,
            isThreat: isFlagged
          });
        });
      });
    } else {
      // MODE 3: Drift Trajectory Phase Space
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
        const y = 520 - normY * 380;

        const baseSize = nodeSizing === 'risk'
          ? (comp.recommendation === 'ENGINEER_REVIEW' ? 13.5 : 9)
          : 9.5;

        nodes.push({
          type: 'component',
          id: comp.id,
          batch_id: comp.batch_id,
          recommendation: comp.recommendation,
          record: comp.record,
          theme: comp.theme,
          isCompound: comp.isCompound,
          activeHubIds: [],
          baseX: x,
          baseY: y,
          size: baseSize,
          mass: 1.0
        });
      });

      for (let i = 0; i < nodes.length; i++) {
        const a = nodes[i];
        let closest = null;
        let minDist = Infinity;
        for (let j = 0; j < nodes.length; j++) {
          if (i === j) continue;
          const b = nodes[j];
          const dist = Math.hypot(a.baseX - b.baseX, a.baseY - b.baseY);
          if (dist < minDist && dist < 90) {
            minDist = dist;
            closest = b;
          }
        }
        if (closest) {
          edges.push({
            id: `sim-${a.id}-${closest.id}`,
            source: a.id,
            target: closest.id,
            baseSourceX: a.baseX,
            baseSourceY: a.baseY,
            baseTargetX: closest.baseX,
            baseTargetY: closest.baseY,
            color: a.theme.base,
            isCompound: a.isCompound,
            recommendation: a.recommendation,
            isThreat: a.recommendation !== 'ACCEPT' || closest.recommendation !== 'ACCEPT'
          });
        }
      }
    }

    return { nodes, edges };
  }, [activeMode, FAILURE_HUBS, BATCH_HUBS, componentsClassification, records, nodeSizing]);

  // Initialize simulation buffers whenever baseGraphData changes
  useEffect(() => {
    simNodesRef.current = baseGraphData.nodes.map(n => ({
      id: n.id,
      type: n.type,
      x: n.baseX,
      y: n.baseY,
      baseX: n.baseX,
      baseY: n.baseY,
      vx: (Math.random() - 0.5) * 2,
      vy: (Math.random() - 0.5) * 2,
      mass: n.mass || 1.0,
      hash: Math.random() * 50,
      fx: null,
      fy: null,
      prevX: n.baseX,
      prevY: n.baseY
    }));

    simLinksRef.current = baseGraphData.edges.map(e => ({
      source: e.source,
      target: e.target,
      isCompound: e.isCompound
    }));

    alphaRef.current = 1.0; // Heat up simulation
  }, [baseGraphData]);

  // Obsidian-Grade Fluid Physics Simulation Engine Loop
  useEffect(() => {
    let running = true;
    let lastTime = performance.now();

    const tickSimulation = (now) => {
      if (!running) return;

      const dt = Math.min((now - lastTime) / 1000, 0.05);
      lastTime = now;

      if (isPhysicsActive) {
        const nodes = simNodesRef.current;
        const links = simLinksRef.current;
        const nodeMap = new Map();
        nodes.forEach(n => nodeMap.set(n.id, n));

        const {
          repelStrength,
          linkDistance,
          linkStrength,
          centerGravity,
          viscousFriction,
          ambientDrift,
          maxVelocity
        } = physicsParams;

        const currentAlpha = alphaRef.current;

        if (currentAlpha > 0.001 || ambientDrift) {
          const t = now * 0.0015;

          // 1. Elastic Hooke's Law Spring Attraction along Edges
          for (let i = 0; i < links.length; i++) {
            const link = links[i];
            const u = nodeMap.get(link.source);
            const v = nodeMap.get(link.target);
            if (!u || !v) continue;

            const dx = v.x - u.x;
            const dy = v.y - u.y;
            const dist = Math.hypot(dx, dy) || 1;
            const targetDist = link.isCompound ? linkDistance * 0.75 : linkDistance;
            const displacement = dist - targetDist;
            const springForce = displacement * linkStrength;

            const fx = (dx / dist) * springForce;
            const fy = (dy / dist) * springForce;

            if (u.fx === null) {
              u.vx += fx / u.mass;
              u.vy += fy / u.mass;
            }
            if (v.fx === null) {
              v.vx -= fx / v.mass;
              v.vy -= fy / v.mass;
            }
          }

          // 2. N-Body Coulomb Repulsion (Pushes close nodes smoothly apart)
          const nLen = nodes.length;
          for (let i = 0; i < nLen; i++) {
            const u = nodes[i];
            for (let j = i + 1; j < nLen; j++) {
              const v = nodes[j];
              const dx = v.x - u.x;
              const dy = v.y - u.y;
              const distSq = dx * dx + dy * dy + 36;

              if (distSq < 90000) { // Interaction radius ~300px
                const dist = Math.sqrt(distSq);
                const repForce = repelStrength / distSq;
                const rx = (dx / dist) * repForce;
                const ry = (dy / dist) * repForce;

                if (u.fx === null) {
                  u.vx -= rx / u.mass;
                  u.vy -= ry / u.mass;
                }
                if (v.fx === null) {
                  v.vx += rx / v.mass;
                  v.vy += ry / v.mass;
                }
              }
            }
          }

          // 3. Center Gravity & Boundary Attraction (Pull to 500, 320)
          for (let i = 0; i < nLen; i++) {
            const u = nodes[i];
            if (u.fx !== null) continue;

            const cx = 500 - u.x;
            const cy = 320 - u.y;
            u.vx += cx * centerGravity;
            u.vy += cy * centerGravity;

            // Ambient gentle cosmic drift (Obsidian-style living graph)
            if (ambientDrift) {
              const waveX = Math.sin(t + u.hash) * 0.16;
              const waveY = Math.cos(t * 0.8 + u.hash * 1.4) * 0.16;
              u.vx += waveX;
              u.vy += waveY;
            }

            // Damping & Friction
            u.vx *= viscousFriction;
            u.vy *= viscousFriction;

            // Velocity Clamping
            const speed = Math.hypot(u.vx, u.vy);
            if (speed > maxVelocity) {
              u.vx = (u.vx / speed) * maxVelocity;
              u.vy = (u.vy / speed) * maxVelocity;
            }

            // Position Integration
            u.x += u.vx * Math.max(currentAlpha, 0.15);
            u.y += u.vy * Math.max(currentAlpha, 0.15);

            // Bounding box soft cushion
            u.x = Math.max(35, Math.min(965, u.x));
            u.y = Math.max(35, Math.min(605, u.y));
          }

          // Alpha Cooling
          alphaRef.current = Math.max(ambientDrift ? 0.07 : 0.0005, currentAlpha * 0.99);

          // Update position map for SVG elements
          const posMap = {};
          nodes.forEach(n => {
            posMap[n.id] = { x: n.x, y: n.y };
          });
          setSimPositions(posMap);
        }
      }

      animFrameRef.current = requestAnimationFrame(tickSimulation);
    };

    animFrameRef.current = requestAnimationFrame(tickSimulation);

    return () => {
      running = false;
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    };
  }, [isPhysicsActive, physicsParams]);

  // Re-heat simulation function (Obsidian Jolt)
  const reheatSimulation = useCallback(() => {
    alphaRef.current = 1.0;
    simNodesRef.current.forEach(n => {
      n.vx += (Math.random() - 0.5) * 8;
      n.vy += (Math.random() - 0.5) * 8;
    });
  }, []);

  // Helper to get active position of a node
  const getNodePos = useCallback((node) => {
    if (!node) return { x: 500, y: 320 };
    return simPositions[node.id] || { x: node.baseX, y: node.baseY };
  }, [simPositions]);

  // Dynamic Graph Nodes & Edges synced with physics positions
  const currentNodes = useMemo(() => {
    return baseGraphData.nodes.map(n => {
      const pos = getNodePos(n);
      return {
        ...n,
        x: pos.x,
        y: pos.y
      };
    });
  }, [baseGraphData.nodes, getNodePos]);

  const nodeMap = useMemo(() => {
    const map = new Map();
    currentNodes.forEach(n => map.set(n.id, n));
    return map;
  }, [currentNodes]);

  const currentEdges = useMemo(() => {
    return baseGraphData.edges.map(e => {
      const srcNode = nodeMap.get(e.source);
      const tgtNode = nodeMap.get(e.target);
      return {
        ...e,
        sourceX: srcNode ? srcNode.x : e.baseSourceX,
        sourceY: srcNode ? srcNode.y : e.baseSourceY,
        targetX: tgtNode ? tgtNode.x : e.baseTargetX,
        targetY: tgtNode ? tgtNode.y : e.baseTargetY
      };
    });
  }, [baseGraphData.edges, nodeMap]);

  // Filtered nodes logic
  const filteredNodeIds = useMemo(() => {
    const ids = new Set();
    currentNodes.forEach(n => {
      if (n.type === 'hub') {
        ids.add(n.id);
        return;
      }
      if (selectedHubId && !n.activeHubIds.includes(selectedHubId)) return;
      if (filterDisposition !== 'ALL' && n.recommendation !== filterDisposition) return;
      if (filterBatch !== 'ALL' && n.batch_id !== filterBatch) return;
      if (showCompoundOnly && !n.isCompound) return;
      if (searchTerm && !n.id.toLowerCase().includes(searchTerm.toLowerCase())) return;

      ids.add(n.id);
    });
    return ids;
  }, [currentNodes, selectedHubId, filterDisposition, filterBatch, showCompoundOnly, searchTerm]);

  // Selected item reference
  const selectedRecord = useMemo(() => {
    return records.find(r => r.component_id === selectedComponentId) || records[0];
  }, [records, selectedComponentId]);

  const selectedClassification = useMemo(() => {
    return componentsClassification.find(c => c.id === selectedComponentId);
  }, [componentsClassification, selectedComponentId]);

  // Canvas Mouse & Drag Handlers with Obsidian-style elastic fling
  const handleCanvasMouseDown = (e) => {
    if (e.target.closest('.interactive-node') || e.target.closest('button') || e.target.closest('input')) return;
    setIsSmoothTransition(false);
    setIsDraggingCanvas(true);
    dragStartRef.current = {
      clientX: e.clientX,
      clientY: e.clientY,
      panX: transform.x,
      panY: transform.y
    };
  };

  const handleNodeMouseDown = (e, node) => {
    e.stopPropagation();
    setIsSmoothTransition(false);
    setDraggedNodeId(node.id);
    setSelectedComponentId(node.id);
    if (node.type === 'hub') {
      setSelectedHubId(node.id);
    }

    const simNode = simNodesRef.current.find(n => n.id === node.id);
    if (simNode) {
      simNode.fx = simNode.x;
      simNode.fy = simNode.y;
      simNode.prevX = simNode.x;
      simNode.prevY = simNode.y;
    }
    alphaRef.current = 0.9; // Re-heat physics during drag

    const currentPos = getNodePos(node);
    dragStartRef.current = {
      clientX: e.clientX,
      clientY: e.clientY,
      nodeId: node.id,
      origX: currentPos.x,
      origY: currentPos.y
    };
  };

  const handleMouseMove = (e) => {
    if (draggedNodeId) {
      const dx = (e.clientX - dragStartRef.current.clientX) / transform.scale;
      const dy = (e.clientY - dragStartRef.current.clientY) / transform.scale;
      const simNode = simNodesRef.current.find(n => n.id === draggedNodeId);
      if (simNode) {
        const nextX = Math.max(30, Math.min(970, dragStartRef.current.origX + dx));
        const nextY = Math.max(30, Math.min(610, dragStartRef.current.origY + dy));
        simNode.fx = nextX;
        simNode.fy = nextY;
        simNode.vx = (nextX - (simNode.prevX || nextX)) * 0.45;
        simNode.vy = (nextY - (simNode.prevY || nextY)) * 0.45;
        simNode.prevX = nextX;
        simNode.prevY = nextY;
        simNode.x = nextX;
        simNode.y = nextY;
        alphaRef.current = 0.85; // Continuous fluid response
      }
      return;
    }

    if (isDraggingCanvas) {
      const dx = e.clientX - dragStartRef.current.clientX;
      const dy = e.clientY - dragStartRef.current.clientY;
      setTransform(prev => ({
        ...prev,
        x: dragStartRef.current.panX + dx,
        y: dragStartRef.current.panY + dy
      }));
    }
  };

  const handleMouseUp = () => {
    if (draggedNodeId) {
      const simNode = simNodesRef.current.find(n => n.id === draggedNodeId);
      if (simNode) {
        simNode.fx = null;
        simNode.fy = null;
        alphaRef.current = 0.75; // Fling inertia into surrounding springs!
      }
      setDraggedNodeId(null);
    }
    setIsDraggingCanvas(false);
    setIsSmoothTransition(true);
  };

  const handleWheel = (e) => {
    e.preventDefault();
    setIsSmoothTransition(false);
    const zoomFactor = e.deltaY < 0 ? 1.08 : 0.92;
    setTransform(prev => ({
      ...prev,
      scale: Math.max(0.4, Math.min(3.2, prev.scale * zoomFactor))
    }));
  };

  // Smooth Camera Operations
  const resetView = () => {
    setIsSmoothTransition(true);
    setTransform({ x: 0, y: 0, scale: 1 });
  };

  const zoomIn = () => {
    setIsSmoothTransition(true);
    setTransform(prev => ({ ...prev, scale: Math.min(3.2, prev.scale * 1.25) }));
  };

  const zoomOut = () => {
    setIsSmoothTransition(true);
    setTransform(prev => ({ ...prev, scale: Math.max(0.4, prev.scale * 0.8) }));
  };

  // Center on Selected Component
  const centerSelected = useCallback(() => {
    const targetNode = currentNodes.find(n => n.id === selectedComponentId);
    if (targetNode) {
      setIsSmoothTransition(true);
      setTransform({
        x: 500 - targetNode.x * 1.4,
        y: 320 - targetNode.y * 1.4,
        scale: 1.4
      });
    }
  }, [currentNodes, selectedComponentId]);

  // Search input auto-jump
  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (!searchTerm.trim()) return;
    const match = currentNodes.find(n => n.id.toLowerCase().includes(searchTerm.toLowerCase()));
    if (match) {
      setSelectedComponentId(match.id);
      centerSelected();
    }
  };

  // Minimap Navigation
  const handleMinimapClick = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const clickX = (e.clientX - rect.left) / rect.width * 1000;
    const clickY = (e.clientY - rect.top) / rect.height * 640;
    setIsSmoothTransition(true);
    setTransform(prev => ({
      ...prev,
      x: 500 - clickX * prev.scale,
      y: 320 - clickY * prev.scale
    }));
  };

  // Metric summaries for HUD
  const metrics = useMemo(() => {
    const compoundCount = componentsClassification.filter(c => c.isCompound).length;
    const b018Anomalies = componentsClassification.filter(c => c.batch_id === 'MLCC_B018' && c.recommendation !== 'ACCEPT').length;
    const b018Total = componentsClassification.filter(c => c.batch_id === 'MLCC_B018').length;
    const b018Rate = b018Total > 0 ? ((b018Anomalies / b018Total) * 100).toFixed(0) : '0';

    const reviewCount = componentsClassification.filter(c => c.recommendation === 'ENGINEER_REVIEW').length;
    const retestCount = componentsClassification.filter(c => c.recommendation === 'RETEST').length;
    const monitorCount = componentsClassification.filter(c => c.recommendation === 'MONITOR').length;
    const acceptCount = componentsClassification.filter(c => c.recommendation === 'ACCEPT').length;

    return {
      compoundCount,
      b018Rate,
      reviewCount,
      retestCount,
      monitorCount,
      acceptCount,
      activeEdges: currentEdges.length,
      visibleNodes: filteredNodeIds.size
    };
  }, [componentsClassification, currentEdges.length, filteredNodeIds]);

  return (
    <div className={`space-y-5 pb-12 ${isFullscreen ? 'fixed inset-0 z-50 bg-[#08090e] p-6 overflow-y-auto' : ''}`}>
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
              Interactive relationship network with Obsidian-grade fluid physics simulation. Nodes float in living suspension and react elastically to dragging, tension, and repulsion.
            </p>
          </div>

          {/* Top Quick Stats Pill Row */}
          <div className="flex flex-wrap items-center gap-2.5 font-mono text-xs">
            <button
              onClick={() => setFilterDisposition('ALL')}
              className={`px-3 py-1.5 rounded-lg border text-right transition-all cursor-pointer ${
                filterDisposition === 'ALL'
                  ? 'bg-white/10 border-white/25 text-white shadow-sm'
                  : 'bg-white/[0.02] border-white/[0.05] text-slate-400 hover:text-white'
              }`}
            >
              <span className="text-[10px] text-slate-500 uppercase block">ACTIVE NODES</span>
              <span className="text-sm font-medium text-white">{metrics.visibleNodes} Active</span>
            </button>
            <button
              onClick={() => setFilterDisposition(filterDisposition === 'ENGINEER_REVIEW' ? 'ALL' : 'ENGINEER_REVIEW')}
              className={`px-3 py-1.5 rounded-lg border text-right transition-all cursor-pointer ${
                filterDisposition === 'ENGINEER_REVIEW'
                  ? 'bg-rose-500/25 border-rose-500/60 ring-1 ring-rose-500/40 text-rose-300 shadow-[0_0_12px_rgba(244,63,94,0.3)]'
                  : 'bg-rose-500/[0.08] border-rose-500/25 text-rose-400 hover:bg-rose-500/15'
              }`}
            >
              <div className="flex items-center justify-end gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-rose-500 shadow-[0_0_6px_rgba(244,63,94,0.8)] animate-pulse" />
                <span className="text-[10px] text-rose-400 uppercase font-semibold">REVIEW (ERROR)</span>
              </div>
              <span className="text-sm font-bold text-rose-300">
                {metrics.reviewCount} Parts
              </span>
            </button>
            <button
              onClick={() => setFilterDisposition(filterDisposition === 'RETEST' ? 'ALL' : 'RETEST')}
              className={`px-3 py-1.5 rounded-lg border text-right transition-all cursor-pointer ${
                filterDisposition === 'RETEST'
                  ? 'bg-amber-500/25 border-amber-500/60 ring-1 ring-amber-500/40 text-amber-300 shadow-[0_0_10px_rgba(245,158,11,0.25)]'
                  : 'bg-amber-500/[0.08] border-amber-500/25 text-amber-400 hover:bg-amber-500/15'
              }`}
            >
              <div className="flex items-center justify-end gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-400 shadow-[0_0_6px_rgba(245,158,11,0.6)]" />
                <span className="text-[10px] text-amber-400 uppercase font-semibold">RETEST</span>
              </div>
              <span className="text-sm font-medium text-amber-300">
                {metrics.retestCount} Parts
              </span>
            </button>
            <button
              onClick={() => setFilterDisposition(filterDisposition === 'MONITOR' ? 'ALL' : 'MONITOR')}
              className={`px-3 py-1.5 rounded-lg border text-right transition-all cursor-pointer ${
                filterDisposition === 'MONITOR'
                  ? 'bg-yellow-500/25 border-yellow-500/60 ring-1 ring-yellow-500/40 text-yellow-300 shadow-[0_0_10px_rgba(234,179,8,0.2)]'
                  : 'bg-yellow-500/[0.08] border-yellow-500/25 text-yellow-400 hover:bg-yellow-500/15'
              }`}
            >
              <div className="flex items-center justify-end gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-yellow-400 shadow-[0_0_6px_rgba(234,179,8,0.5)]" />
                <span className="text-[10px] text-yellow-400 uppercase font-semibold">MONITOR</span>
              </div>
              <span className="text-sm font-medium text-yellow-300">
                {metrics.monitorCount} Parts
              </span>
            </button>
            <button
              onClick={() => setFilterDisposition(filterDisposition === 'ACCEPT' ? 'ALL' : 'ACCEPT')}
              className={`px-3 py-1.5 rounded-lg border text-right transition-all cursor-pointer ${
                filterDisposition === 'ACCEPT'
                  ? 'bg-emerald-500/25 border-emerald-500/60 ring-1 ring-emerald-500/40 text-emerald-300 shadow-[0_0_12px_rgba(16,185,129,0.3)]'
                  : 'bg-emerald-500/[0.08] border-emerald-500/25 text-emerald-400 hover:bg-emerald-500/15'
              }`}
            >
              <div className="flex items-center justify-end gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-[0_0_6px_rgba(16,185,129,0.7)]" />
                <span className="text-[10px] text-emerald-400 uppercase font-semibold">ACCEPT (GOOD)</span>
              </div>
              <span className="text-sm font-bold text-emerald-300">
                {metrics.acceptCount} Parts
              </span>
            </button>
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

          {/* Search Form */}
          <form onSubmit={handleSearchSubmit} className="relative min-w-[220px]">
            <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" strokeWidth={1.5} />
            <input
              type="text"
              placeholder="Search & Center (e.g. C000147)..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 rounded-lg bg-black/30 border border-white/[0.08] text-xs text-white placeholder-slate-500 focus:outline-none focus:border-orange-500/50 font-mono"
            />
          </form>
        </div>

        {/* Secondary Filter Pills */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-white/[0.04] text-xs font-mono">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-[11px] text-slate-500 uppercase flex items-center gap-1">
              <Filter className="w-3 h-3 text-slate-500" strokeWidth={1.5} />
              DISPOSITION:
            </span>
            {[
              { id: 'ALL', label: 'ALL', count: records.length, dotClass: 'bg-slate-400' },
              { id: 'ENGINEER_REVIEW', label: 'REVIEW (ERROR)', count: metrics.reviewCount, dotClass: 'bg-rose-500 shadow-[0_0_6px_#ef4444]' },
              { id: 'RETEST', label: 'RETEST', count: metrics.retestCount, dotClass: 'bg-amber-400' },
              { id: 'MONITOR', label: 'MONITOR', count: metrics.monitorCount, dotClass: 'bg-yellow-400' },
              { id: 'ACCEPT', label: 'ACCEPT (GOOD)', count: metrics.acceptCount, dotClass: 'bg-emerald-400 shadow-[0_0_6px_#10b981]' }
            ].map(disp => {
              let activeStyle = 'bg-orange-500/20 text-orange-300 border-orange-500/40 font-medium';
              if (disp.id === 'ENGINEER_REVIEW') activeStyle = 'bg-rose-500/20 text-rose-300 border-rose-500/50 font-bold shadow-[0_0_10px_rgba(244,63,94,0.25)]';
              else if (disp.id === 'ACCEPT') activeStyle = 'bg-emerald-500/20 text-emerald-300 border-emerald-500/50 font-bold shadow-[0_0_10px_rgba(16,185,129,0.25)]';
              else if (disp.id === 'RETEST') activeStyle = 'bg-amber-500/20 text-amber-300 border-amber-500/40 font-medium shadow-[0_0_8px_rgba(245,158,11,0.2)]';
              else if (disp.id === 'MONITOR') activeStyle = 'bg-yellow-500/20 text-yellow-300 border-yellow-500/40 font-medium shadow-[0_0_8px_rgba(234,179,8,0.15)]';

              return (
                <button
                  key={disp.id}
                  onClick={() => setFilterDisposition(disp.id)}
                  className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] transition-all cursor-pointer ${
                    filterDisposition === disp.id
                      ? activeStyle
                      : 'bg-white/[0.02] text-slate-400 hover:text-white border border-white/[0.04]'
                  }`}
                >
                  <span className={`w-1.5 h-1.5 rounded-full ${disp.dotClass}`} />
                  <span>{disp.label}</span>
                  <span className="opacity-70 text-[10px]">({disp.count})</span>
                </button>
              );
            })}
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

        {/* Extended Visual Controls Strip */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-white/[0.04] text-xs font-mono">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-[11px] text-slate-500 flex items-center gap-1">
              <SlidersHorizontal className="w-3 h-3 text-slate-500" strokeWidth={1.5} />
              EDGES:
            </span>
            {[
              { id: 'all', label: 'All Links' },
              { id: 'threats_only', label: 'Threats Only' },
              { id: 'selected', label: 'Focus Selection' },
              { id: 'hidden', label: 'Hide' }
            ].map(em => (
              <button
                key={em.id}
                onClick={() => setEdgeMode(em.id)}
                className={`px-2 py-0.5 rounded text-[10.5px] transition-all cursor-pointer ${
                  edgeMode === em.id
                    ? 'bg-white/15 text-orange-300 border border-orange-500/30 font-medium'
                    : 'bg-white/[0.02] text-slate-400 hover:text-white border border-white/[0.04]'
                }`}
              >
                {em.label}
              </button>
            ))}
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <span className="text-[11px] text-slate-500">NODE SIZE:</span>
            <button
              onClick={() => setNodeSizing(nodeSizing === 'risk' ? 'uniform' : 'risk')}
              className="px-2 py-0.5 rounded text-[10.5px] bg-white/[0.03] hover:bg-white/[0.07] border border-white/10 text-slate-300 cursor-pointer"
            >
              {nodeSizing === 'risk' ? 'Weighted by Risk' : 'Uniform 9px'}
            </button>

            <span className="text-slate-600">•</span>

            <span className="text-[11px] text-slate-500">LABELS:</span>
            <button
              onClick={() => setShowLabels(showLabels === 'hover' ? 'all' : 'hover')}
              className="px-2 py-0.5 rounded text-[10.5px] bg-white/[0.03] hover:bg-white/[0.07] border border-white/10 text-slate-300 cursor-pointer"
            >
              {showLabels === 'hover' ? 'Hover / Focus Only' : 'Show All IDs'}
            </button>

            {selectedHubId && (
              <button
                onClick={() => setSelectedHubId(null)}
                className="ml-2 px-2 py-0.5 rounded text-[10.5px] bg-orange-500/20 text-orange-300 border border-orange-500/30 flex items-center gap-1 cursor-pointer"
              >
                <span>Clear Hub Filter</span>
                <span className="text-orange-400">✕</span>
              </button>
            )}
          </div>
        </div>
      </SquircleCard>

      {/* 3. Main Topology Canvas + Side HUD Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
        {/* Left: Interactive Canvas Viewport (8 cols) */}
        <div className="lg:col-span-8 space-y-3">
          <SquircleCard elevated className="relative overflow-hidden p-0 bg-[#06070b] border-white/[0.08]">
            {/* On-Canvas Multi-Control Floating Island */}
            <div className="absolute top-3 left-3 z-30 flex items-center gap-1.5 bg-[#0b0c13]/90 backdrop-blur-md p-1.5 rounded-xl border border-white/[0.1] text-slate-300 shadow-xl shadow-black/40">
              <button
                onClick={zoomIn}
                title="Zoom In (+)"
                className="p-1.5 rounded-lg hover:bg-white/10 hover:text-white transition-colors cursor-pointer"
              >
                <ZoomIn className="w-4 h-4" strokeWidth={1.5} />
              </button>
              <button
                onClick={zoomOut}
                title="Zoom Out (-)"
                className="p-1.5 rounded-lg hover:bg-white/10 hover:text-white transition-colors cursor-pointer"
              >
                <ZoomOut className="w-4 h-4" strokeWidth={1.5} />
              </button>
              <span className="px-1.5 text-[11px] font-mono text-slate-400 font-medium">
                {Math.round(transform.scale * 100)}%
              </span>
              <span className="w-px h-4 bg-white/10 mx-0.5" />
              <button
                onClick={resetView}
                title="Reset Camera View"
                className="p-1.5 rounded-lg hover:bg-white/10 hover:text-white transition-colors cursor-pointer"
              >
                <RotateCcw className="w-3.5 h-3.5" strokeWidth={1.5} />
              </button>
              <button
                onClick={centerSelected}
                title="Center on Selected Node"
                className="flex items-center gap-1 px-2 py-1 rounded-lg hover:bg-orange-500/15 hover:text-orange-300 text-[11px] font-mono transition-colors cursor-pointer text-orange-400"
              >
                <Crosshair className="w-3.5 h-3.5" strokeWidth={1.5} />
                <span>Focus</span>
              </button>
              <span className="w-px h-4 bg-white/10 mx-0.5" />

              {/* Obsidian-Style Forces Toggle Button */}
              <button
                onClick={() => setShowForcesDrawer(!showForcesDrawer)}
                title="Obsidian Graph Forces Settings"
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-mono transition-all cursor-pointer ${
                  showForcesDrawer
                    ? 'bg-orange-500 text-black font-semibold shadow-[0_0_12px_rgba(249,115,22,0.4)]'
                    : 'hover:bg-white/10 text-slate-300'
                }`}
              >
                <Sliders className="w-3.5 h-3.5" strokeWidth={1.5} />
                <span>Forces</span>
              </button>

              {/* Reheat / Jolt Button */}
              <button
                onClick={reheatSimulation}
                title="Jolt / Shake Graph (Obsidian Reheat)"
                className="p-1.5 rounded-lg hover:bg-white/10 text-slate-300 hover:text-orange-400 transition-colors cursor-pointer"
              >
                <RefreshCw className="w-3.5 h-3.5" strokeWidth={1.5} />
              </button>

              <span className="w-px h-4 bg-white/10 mx-0.5" />
              {/* Fullscreen Theater Mode */}
              <button
                onClick={() => setIsFullscreen(!isFullscreen)}
                title={isFullscreen ? "Exit Fullscreen" : "Fullscreen Theater View"}
                className="p-1.5 rounded-lg hover:bg-white/10 hover:text-white transition-colors cursor-pointer"
              >
                {isFullscreen ? <Minimize2 className="w-4 h-4 text-orange-400" strokeWidth={1.5} /> : <Maximize2 className="w-4 h-4" strokeWidth={1.5} />}
              </button>
            </div>

            {/* Obsidian-Style Forces Floating Drawer */}
            {showForcesDrawer && (
              <div
                className="absolute top-14 left-3 z-40 w-72 bg-[#0a0c13]/95 backdrop-blur-xl rounded-2xl border border-white/15 p-4 shadow-2xl shadow-black/80 space-y-3.5 text-xs font-mono animate-in fade-in zoom-in-95 duration-150"
                onClick={(e) => e.stopPropagation()}
              >
                <div className="flex items-center justify-between border-b border-white/10 pb-2">
                  <div className="flex items-center gap-1.5 text-slate-200 font-semibold tracking-wide">
                    <Sliders className="w-3.5 h-3.5 text-orange-400" strokeWidth={1.5} />
                    <span>GRAPH FORCES</span>
                  </div>
                  <span className="text-[10px] text-slate-500 uppercase">Fluid Physics</span>
                </div>

                {/* Force 1: Repulsion */}
                <div className="space-y-1">
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="text-slate-400">Repel Force</span>
                    <span className="text-white font-medium">{physicsParams.repelStrength}</span>
                  </div>
                  <input
                    type="range"
                    min="150"
                    max="1000"
                    step="10"
                    value={physicsParams.repelStrength}
                    onChange={(e) => {
                      setPhysicsParams(prev => ({ ...prev, repelStrength: Number(e.target.value) }));
                      alphaRef.current = 0.8;
                    }}
                    className="w-full h-1 bg-white/10 rounded-lg appearance-none cursor-pointer accent-orange-500"
                  />
                </div>

                {/* Force 2: Link Distance */}
                <div className="space-y-1">
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="text-slate-400">Link Distance</span>
                    <span className="text-white font-medium">{physicsParams.linkDistance}px</span>
                  </div>
                  <input
                    type="range"
                    min="40"
                    max="160"
                    step="2"
                    value={physicsParams.linkDistance}
                    onChange={(e) => {
                      setPhysicsParams(prev => ({ ...prev, linkDistance: Number(e.target.value) }));
                      alphaRef.current = 0.8;
                    }}
                    className="w-full h-1 bg-white/10 rounded-lg appearance-none cursor-pointer accent-orange-500"
                  />
                </div>

                {/* Force 3: Link Force (Spring Tension) */}
                <div className="space-y-1">
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="text-slate-400">Link Force</span>
                    <span className="text-white font-medium">{physicsParams.linkStrength.toFixed(3)}</span>
                  </div>
                  <input
                    type="range"
                    min="0.01"
                    max="0.25"
                    step="0.005"
                    value={physicsParams.linkStrength}
                    onChange={(e) => {
                      setPhysicsParams(prev => ({ ...prev, linkStrength: Number(e.target.value) }));
                      alphaRef.current = 0.8;
                    }}
                    className="w-full h-1 bg-white/10 rounded-lg appearance-none cursor-pointer accent-orange-500"
                  />
                </div>

                {/* Force 4: Center Gravity */}
                <div className="space-y-1">
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="text-slate-400">Center Force</span>
                    <span className="text-white font-medium">{physicsParams.centerGravity.toFixed(3)}</span>
                  </div>
                  <input
                    type="range"
                    min="0.001"
                    max="0.025"
                    step="0.001"
                    value={physicsParams.centerGravity}
                    onChange={(e) => {
                      setPhysicsParams(prev => ({ ...prev, centerGravity: Number(e.target.value) }));
                      alphaRef.current = 0.8;
                    }}
                    className="w-full h-1 bg-white/10 rounded-lg appearance-none cursor-pointer accent-orange-500"
                  />
                </div>

                {/* Force 5: Viscous Friction (Damping) */}
                <div className="space-y-1">
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="text-slate-400">Damping / Viscosity</span>
                    <span className="text-white font-medium">{physicsParams.viscousFriction.toFixed(3)}</span>
                  </div>
                  <input
                    type="range"
                    min="0.80"
                    max="0.96"
                    step="0.005"
                    value={physicsParams.viscousFriction}
                    onChange={(e) => {
                      setPhysicsParams(prev => ({ ...prev, viscousFriction: Number(e.target.value) }));
                      alphaRef.current = 0.8;
                    }}
                    className="w-full h-1 bg-white/10 rounded-lg appearance-none cursor-pointer accent-orange-500"
                  />
                </div>

                {/* Ambient Drift Toggle */}
                <div className="pt-2 border-t border-white/10 flex items-center justify-between">
                  <div className="flex items-center gap-1.5 text-slate-300">
                    <Wind className="w-3.5 h-3.5 text-orange-400" strokeWidth={1.5} />
                    <span>Ambient Breathing Float</span>
                  </div>
                  <button
                    onClick={() => {
                      setPhysicsParams(prev => ({ ...prev, ambientDrift: !prev.ambientDrift }));
                      alphaRef.current = 0.8;
                    }}
                    className={`w-8 h-4.5 rounded-full transition-colors relative cursor-pointer p-0.5 ${
                      physicsParams.ambientDrift ? 'bg-orange-500' : 'bg-white/10'
                    }`}
                  >
                    <div
                      className={`w-3.5 h-3.5 rounded-full bg-white transition-transform ${
                        physicsParams.ambientDrift ? 'translate-x-3.5' : 'translate-x-0'
                      }`}
                    />
                  </button>
                </div>

                {/* Footer Buttons */}
                <div className="pt-2 flex items-center justify-between gap-2">
                  <button
                    onClick={() => {
                      setPhysicsParams({
                        repelStrength: 480,
                        linkDistance: 82,
                        linkStrength: 0.085,
                        centerGravity: 0.007,
                        viscousFriction: 0.895,
                        ambientDrift: true,
                        maxVelocity: 12
                      });
                      reheatSimulation();
                    }}
                    className="px-2 py-1 rounded bg-white/5 hover:bg-white/10 text-slate-400 hover:text-white text-[10px] cursor-pointer"
                  >
                    Reset Defaults
                  </button>
                  <button
                    onClick={reheatSimulation}
                    className="px-3 py-1 rounded bg-orange-500/20 text-orange-300 border border-orange-500/30 text-[10.5px] font-semibold cursor-pointer"
                  >
                    Jolt / Shake
                  </button>
                </div>
              </div>
            )}

            {/* Interaction Hint Badge */}
            <div className="absolute top-3 right-3 z-20 hidden md:flex items-center gap-1.5 bg-[#0b0c13]/85 backdrop-blur-md px-2.5 py-1 rounded-lg border border-white/[0.08] text-[10.5px] font-mono text-slate-400">
              <Move className="w-3 h-3 text-orange-400" strokeWidth={1.5} />
              <span>Fluid rubber-band dragging • Drag canvas to pan</span>
            </div>

            {/* Quick Hover Inspection Badge Card */}
            {hoveredNodeId && componentsClassification.find(c => c.id === hoveredNodeId) && (
              <div className="absolute top-12 right-3 z-30 flex items-center gap-2.5 bg-[#0b0c13]/95 backdrop-blur-md px-3 py-2 rounded-xl border border-white/15 shadow-2xl font-mono text-xs animate-in fade-in zoom-in-95 duration-100 pointer-events-none">
                {(() => {
                  const comp = componentsClassification.find(c => c.id === hoveredNodeId);
                  const r = comp?.record;
                  return (
                    <>
                      <div className="flex flex-col">
                        <span className="font-bold text-white tracking-wide text-xs">{comp.id}</span>
                        <span className="text-[10px] text-slate-400">Batch {comp.batch_id} • 24h: {r?.latest_value} µA</span>
                      </div>
                      <DecisionBadge decision={comp.recommendation} size="sm" />
                    </>
                  );
                })()}
              </div>
            )}

            {/* Canvas Legend Overlay with standard dashboard tags */}
            <div className="absolute bottom-3 left-3 z-20 hidden sm:flex items-center gap-1.5 bg-[#0b0c13]/90 backdrop-blur-md p-1.5 rounded-xl border border-white/[0.08] text-[11px] font-mono">
              {[
                { id: 'ENGINEER_REVIEW', label: 'REVIEW (ERROR)', dotClass: 'bg-rose-500 shadow-[0_0_8px_#ef4444]', textClass: 'text-rose-300', activeClass: 'bg-rose-500/20 border-rose-500/50 text-rose-300 font-bold shadow-[0_0_10px_rgba(244,63,94,0.25)]' },
                { id: 'RETEST', label: 'RETEST', dotClass: 'bg-amber-400 shadow-[0_0_6px_rgba(245,158,11,0.6)]', textClass: 'text-amber-300', activeClass: 'bg-amber-500/20 border-amber-500/40 text-amber-300 font-medium shadow-[0_0_8px_rgba(245,158,11,0.2)]' },
                { id: 'MONITOR', label: 'MONITOR', dotClass: 'bg-yellow-400 shadow-[0_0_6px_rgba(234,179,8,0.5)]', textClass: 'text-yellow-300', activeClass: 'bg-yellow-500/20 border-yellow-500/40 text-yellow-300 font-medium shadow-[0_0_8px_rgba(234,179,8,0.15)]' },
                { id: 'ACCEPT', label: 'ACCEPT (GOOD)', dotClass: 'bg-emerald-400 shadow-[0_0_8px_#10b981]', textClass: 'text-emerald-300', activeClass: 'bg-emerald-500/20 border-emerald-500/50 text-emerald-300 font-bold shadow-[0_0_10px_rgba(16,185,129,0.25)]' }
              ].map(item => (
                <button
                  key={item.id}
                  onClick={() => setFilterDisposition(filterDisposition === item.id ? 'ALL' : item.id)}
                  title={`Filter graph by ${item.label}`}
                  className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg border transition-all cursor-pointer ${
                    filterDisposition === item.id
                      ? `${item.activeClass} ring-1 ring-white/10`
                      : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-white/[0.04]'
                  }`}
                >
                  <span className={`w-2 h-2 rounded-full ${item.dotClass}`} />
                  <span className={filterDisposition === item.id ? item.textClass : ''}>{item.label}</span>
                </button>
              ))}
            </div>

            {/* Interactive Mini-Radar Map (Bottom-Right) */}
            <div
              onClick={handleMinimapClick}
              title="Radar Minimap • Click to pan"
              className="absolute bottom-3 right-3 z-20 w-36 h-24 bg-[#090b10]/90 backdrop-blur-md rounded-xl border border-white/15 p-1 cursor-crosshair overflow-hidden shadow-2xl hidden md:block"
            >
              <svg viewBox="0 0 1000 640" className="w-full h-full">
                <rect width="1000" height="640" fill="transparent" />
                <circle cx="500" cy="320" r="280" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="4" />
                {currentNodes.map(n => (
                  <circle
                    key={`mini-${n.id}`}
                    cx={n.x}
                    cy={n.y}
                    r={n.type === 'hub' ? 14 : 7}
                    fill={n.type === 'hub' ? '#ffffff' : (THEME_COLORS[n.recommendation]?.base || '#10b981')}
                    opacity={n.id === selectedComponentId ? 1 : 0.6}
                  />
                ))}
                <rect
                  x={Math.max(0, -transform.x / transform.scale)}
                  y={Math.max(0, -transform.y / transform.scale)}
                  width={1000 / transform.scale}
                  height={640 / transform.scale}
                  fill="rgba(249, 115, 22, 0.08)"
                  stroke="#f97316"
                  strokeWidth="6"
                  rx="8"
                />
              </svg>
            </div>

            {/* SVG Interactive Canvas */}
            <div
              ref={canvasContainerRef}
              className={`w-full ${isFullscreen ? 'h-[75vh]' : 'h-[600px]'} overflow-hidden select-none ${
                isDraggingCanvas ? 'cursor-grabbing' : (draggedNodeId ? 'cursor-move' : 'cursor-grab')
              }`}
              onMouseDown={handleCanvasMouseDown}
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
                  <radialGradient id="glow-green" cx="50%" cy="50%" r="50%">
                    <stop offset="0%" stopColor="#10b981" stopOpacity="0.8" />
                    <stop offset="60%" stopColor="#10b981" stopOpacity="0.25" />
                    <stop offset="100%" stopColor="#10b981" stopOpacity="0" />
                  </radialGradient>
                  <radialGradient id="glow-red" cx="50%" cy="50%" r="50%">
                    <stop offset="0%" stopColor="#ef4444" stopOpacity="0.8" />
                    <stop offset="60%" stopColor="#ef4444" stopOpacity="0.25" />
                    <stop offset="100%" stopColor="#ef4444" stopOpacity="0" />
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

                {/* Transformed Content Group with Smooth Transition */}
                <g
                  transform={`translate(${transform.x}, ${transform.y}) scale(${transform.scale})`}
                  style={{
                    transition: isSmoothTransition ? 'transform 0.4s cubic-bezier(0.16, 1, 0.3, 1)' : 'none'
                  }}
                >
                  {/* Subtle Background Radar Concentric Rings */}
                  <g opacity="0.12" stroke="#ffffff" fill="none">
                    <circle cx="500" cy="320" r="140" strokeWidth="1" strokeDasharray="3 6" />
                    <circle cx="500" cy="320" r="260" strokeWidth="1" strokeDasharray="3 6" />
                    <circle cx="500" cy="320" r="390" strokeWidth="1" />
                    <line x1="500" y1="0" x2="500" y2="640" strokeWidth="0.5" strokeDasharray="4 8" />
                    <line x1="0" y1="320" x2="1000" y2="320" strokeWidth="0.5" strokeDasharray="4 8" />
                  </g>

                  {/* 1. Edges Layer */}
                  {edgeMode !== 'hidden' && (
                    <g className="edges-layer">
                      {currentEdges.map(edge => {
                        const isSourceVisible = filteredNodeIds.has(edge.source);
                        const isTargetVisible = filteredNodeIds.has(edge.target);
                        if (!isSourceVisible || !isTargetVisible) return null;

                        if (edgeMode === 'threats_only' && !edge.isThreat) return null;

                        const isConnectedToHover = hoveredNodeId && (edge.source === hoveredNodeId || edge.target === hoveredNodeId);
                        const isConnectedToSelected = selectedComponentId && (edge.source === selectedComponentId || edge.target === selectedComponentId);
                        const isConnectedToDrag = draggedNodeId && (edge.source === draggedNodeId || edge.target === draggedNodeId);
                        const isHighlighted = isConnectedToHover || isConnectedToSelected || isConnectedToDrag;

                        if (edgeMode === 'selected' && !isHighlighted) return null;

                        return (
                          <line
                            key={edge.id}
                            x1={edge.sourceX}
                            y1={edge.sourceY}
                            x2={edge.targetX}
                            y2={edge.targetY}
                            stroke={isHighlighted ? '#f97316' : edge.color}
                            strokeWidth={isHighlighted ? 2.5 : (edge.isCompound ? 1.2 : 0.75)}
                            strokeOpacity={isHighlighted ? 0.95 : (hoveredNodeId ? 0.08 : (edge.isCompound ? 0.45 : 0.25))}
                            strokeDasharray={isHighlighted ? '5 5' : (edge.isCompound ? '3 3' : 'none')}
                            className={isHighlighted ? 'animate-pulse' : ''}
                          />
                        );
                      })}
                    </g>
                  )}

                  {/* 2. Hub Nodes Layer */}
                  <g className="hubs-layer">
                    {currentNodes.filter(n => n.type === 'hub').map(hub => {
                      const isSelected = selectedHubId === hub.id;
                      const Icon = hub.icon || Network;
                      const isHovered = hoveredNodeId === hub.id;

                      return (
                        <g
                          key={hub.id}
                          transform={`translate(${hub.x}, ${hub.y})`}
                          onMouseDown={(e) => handleNodeMouseDown(e, hub)}
                          onClick={() => setSelectedHubId(selectedHubId === hub.id ? null : hub.id)}
                          onMouseEnter={() => setHoveredNodeId(hub.id)}
                          onMouseLeave={() => setHoveredNodeId(null)}
                          className="interactive-node cursor-move group"
                        >
                          {/* Radial Hub Glow */}
                          <circle
                            r="38"
                            fill="none"
                            stroke={hub.color}
                            strokeWidth="1.5"
                            strokeOpacity={isSelected || isHovered ? 0.9 : 0.25}
                            strokeDasharray="4 4"
                            className={isHovered ? 'animate-spin' : ''}
                            style={{ animationDuration: '8s' }}
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

                          <circle cx="0" cy="0" r="10" fill={hub.color} fillOpacity="0.15" />
                          <circle cx="0" cy="0" r="3.5" fill={hub.color} />

                          {/* Hub Label */}
                          <text
                            y="40"
                            fill="#ffffff"
                            fontSize="11"
                            fontWeight="600"
                            textAnchor="middle"
                            className="font-mono tracking-wider pointer-events-none"
                          >
                            {hub.short}
                          </text>
                        </g>
                      );
                    })}
                  </g>

                  {/* 3. Component Nodes Layer */}
                  <g className="components-layer">
                    {currentNodes.filter(n => n.type === 'component').map(node => {
                      const isVisible = filteredNodeIds.has(node.id);
                      if (!isVisible) return null;

                      const isSelected = node.id === selectedComponentId;
                      const isHovered = node.id === hoveredNodeId;
                      const isBeingDragged = node.id === draggedNodeId;
                      const isMuted = hoveredNodeId && hoveredNodeId !== node.id && !node.activeHubIds.includes(hoveredNodeId);

                      return (
                        <g
                          key={node.id}
                          transform={`translate(${node.x}, ${node.y})`}
                          onMouseDown={(e) => handleNodeMouseDown(e, node)}
                          onClick={() => {
                            setSelectedComponentId(node.id);
                            setSelectedHubId(null);
                          }}
                          onMouseEnter={() => setHoveredNodeId(node.id)}
                          onMouseLeave={() => setHoveredNodeId(null)}
                          opacity={isMuted ? 0.15 : 1}
                          className="interactive-node cursor-move transition-opacity duration-150"
                        >
                          {/* Pulsing Selection Halo */}
                          {isSelected && (
                            <circle
                              r={node.size + 11}
                              fill="none"
                              stroke="#f97316"
                              strokeWidth="1.8"
                              strokeDasharray="3 3"
                              className="animate-spin"
                              style={{ animationDuration: '6s' }}
                            />
                          )}

                          {/* Drag elevation halo */}
                          {isBeingDragged && (
                            <circle
                              r={node.size + 16}
                              fill="rgba(249, 115, 22, 0.25)"
                              stroke="#f97316"
                              strokeWidth="1.6"
                            />
                          )}

                          {/* Hover Expansion Halo */}
                          {isHovered && !isSelected && (
                            <circle
                              r={node.size + 7}
                              fill="none"
                              stroke={node.theme.border}
                              strokeWidth="1.5"
                              strokeOpacity="0.8"
                            />
                          )}

                          {/* Multi-Threat Halo for Compound Outliers */}
                          {node.isCompound && (
                            <circle
                              r={node.size + 4.5}
                              fill={node.theme.glow}
                              stroke={node.theme.border}
                              strokeWidth="0.8"
                              strokeOpacity="0.5"
                            />
                          )}

                          {/* Core Node Disc */}
                          <circle
                            r={node.size}
                            fill={node.theme.base}
                            stroke={isSelected ? '#ffffff' : node.theme.border}
                            strokeWidth={isSelected ? 2.2 : 1.2}
                            filter="url(#softGlow)"
                          />

                          {/* Inner Socket Glyph / Center Dot */}
                          <circle
                            r={isSelected ? 3.5 : 2}
                            fill={node.recommendation === 'ACCEPT' ? '#064e3b' : (node.recommendation === 'ENGINEER_REVIEW' ? '#450a0a' : '#08090e')}
                          />

                          {/* Node Hover Tooltip or Constant Label */}
                          {(showLabels === 'all' || isHovered || isSelected) && (
                            <g transform="translate(0, -22)" className="pointer-events-none select-none">
                              <rect
                                x="-54"
                                y="-17"
                                width="108"
                                height="22"
                                rx="6"
                                fill="#0c0e17"
                                stroke={node.theme.border}
                                strokeWidth={isSelected ? 1.6 : 1}
                                filter="url(#softGlow)"
                              />
                              <circle
                                cx="-42"
                                cy="-6"
                                r="2.8"
                                fill={node.theme.base}
                              />
                              <text
                                x="-33"
                                y="-2.5"
                                fill="#ffffff"
                                fontSize="9.5"
                                fontWeight="600"
                                textAnchor="start"
                                className="font-mono"
                              >
                                {node.id.replace('MLCC_', '')}
                              </text>
                              <text
                                x="46"
                                y="-2.5"
                                fill={node.theme.base}
                                fontSize="8"
                                fontWeight="700"
                                textAnchor="end"
                                className="font-mono uppercase"
                              >
                                {node.recommendation === 'ENGINEER_REVIEW' ? 'ERROR' : (node.recommendation === 'ACCEPT' ? 'GOOD' : node.recommendation)}
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
                {selectedRecord.context?.board_position != null ? `SOCKET #${selectedRecord.context.board_position}` : 'SOCKET N/A'}
              </span>
            </div>

            {/* Selected Component Header */}
            <div>
              <div className="flex items-center justify-between gap-2 mb-1.5">
                <span className={`text-base font-bold font-mono tracking-wide ${
                  selectedRecord.recommendation === 'ENGINEER_REVIEW' ? 'text-rose-300' : (selectedRecord.recommendation === 'ACCEPT' ? 'text-emerald-300' : 'text-white')
                }`}>
                  {selectedRecord.component_id}
                </span>
                <DecisionBadge decision={selectedRecord.recommendation} size="sm" />
              </div>
              <div className="text-xs font-mono text-slate-400 flex items-center gap-2">
                <span>Batch: <strong className="text-slate-200 font-normal">{selectedRecord.batch_id}</strong></span>
                <span>•</span>
                <span>Ch: <strong className="text-slate-200 font-normal">{selectedRecord.context?.tester_channel ?? 'N/A'}</strong></span>
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
                  const isNominal = hId === 'HUB_NOMINAL';
                  const isCritical = hId === 'HUB_LIMIT';

                  return (
                    <div
                      key={hId}
                      className={`p-2 rounded-lg border flex items-center justify-between gap-2 text-xs font-mono ${
                        isCritical
                          ? 'bg-rose-500/[0.08] border-rose-500/30 text-rose-300'
                          : isNominal
                          ? 'bg-emerald-500/[0.08] border-emerald-500/30 text-emerald-300'
                          : 'bg-white/[0.02] border-white/[0.06] text-slate-200'
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        <Icon className="w-3.5 h-3.5 shrink-0" style={{ color: hub.color }} strokeWidth={1.5} />
                        <span>{hub.name}</span>
                      </div>
                      <span
                        className="text-[10px] px-2 py-0.5 rounded border font-mono font-medium uppercase"
                        style={{
                          borderColor: `${hub.color}40`,
                          backgroundColor: `${hub.color}15`,
                          color: hub.color
                        }}
                      >
                        {hub.short}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Metric Comparison Grid */}
            <div className="grid grid-cols-2 gap-2 text-xs font-mono">
              <div className="p-2.5 rounded bg-white/[0.02] border border-white/[0.04]">
                <span className="text-[9.5px] text-slate-500 uppercase block">24h Leakage</span>
                <span className={`text-sm font-medium ${selectedRecord.latest_value >= (selectedRecord.limits?.applicable_limit || 0.25) ? 'text-rose-400 font-bold' : (selectedRecord.latest_value < 0.1 ? 'text-emerald-400' : 'text-white')}`}>
                  {selectedRecord.latest_value} µA
                </span>
                <span className="text-[10px] text-slate-500 block">0h: {selectedRecord.initial_value} µA</span>
              </div>
              <div className="p-2.5 rounded bg-white/[0.02] border border-white/[0.04]">
                <span className="text-[9.5px] text-slate-500 uppercase block">168h Forecast</span>
                <span className={`text-sm font-medium ${selectedRecord.forecast?.predicted_to_cross_limit ? 'text-rose-400 font-bold' : (selectedRecord.recommendation === 'ACCEPT' ? 'text-emerald-400' : 'text-orange-400')}`}>
                  {selectedRecord.forecast?.predicted_final_value} µA
                </span>
                <span className="text-[10px] text-slate-500 block">Spec: {selectedRecord.limits?.applicable_limit} µA</span>
              </div>
              <div className="p-2.5 rounded bg-white/[0.02] border border-white/[0.04]">
                <span className="text-[9.5px] text-slate-500 uppercase block">Peer Robust Z</span>
                <span className={`text-sm font-medium ${Math.abs(selectedRecord.peers?.current_batch_robust_z || 0) >= 2.0 ? 'text-rose-400 font-bold' : 'text-white'}`}>
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
              Anomaly concentration is <strong className="text-rose-400">60% higher in Lot MLCC_B018</strong> than tester channels, indicating a probable <strong className="text-rose-300">Raw Material / Firing Lot Defect</strong> rather than a chamber socket artifact.
            </p>
          </SquircleCard>
        </div>
      </div>
    </div>
  );
}
