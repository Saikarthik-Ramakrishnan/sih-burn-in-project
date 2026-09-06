import React, { useState, useEffect, useMemo, useRef } from 'react';
import {
  Search,
  LayoutDashboard,
  Grid3X3,
  LineChart,
  Network,
  ThermometerSnowflake,
  FileSpreadsheet,
  UploadCloud,
  RefreshCcw,
  BookOpen,
  Sparkles,
  X,
  CornerDownLeft,
  Maximize2,
  AlertOctagon,
  AlertTriangle,
  CheckCircle2,
  Filter,
  Layers
} from 'lucide-react';
import LeakageLensLogo from './LeakageLensLogo';
import DecisionBadge from './DecisionBadge';
import { formatUnit } from '../../lib/utils';

export default function CommandPalette({
  isOpen,
  onClose,
  dataset,
  activeTab,
  setActiveTab,
  onInspectComponent,
  onFilterByDecision,
  onOpenUpload,
  onReloadDemo
}) {
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef(null);
  const listRef = useRef(null);

  // Auto-focus on open and reset state
  useEffect(() => {
    if (isOpen) {
      setQuery('');
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isOpen]);

  // Base navigation commands
  const navigationCommands = useMemo(() => [
    {
      id: 'nav-overview',
      category: 'NAVIGATION',
      title: 'Overview Dashboard',
      subtitle: 'Early screening yield, drift anomalies & KPIs',
      icon: LayoutDashboard,
      badge: 'TAB',
      action: () => {
        setActiveTab('overview');
        onClose();
      }
    },
    {
      id: 'nav-components',
      category: 'NAVIGATION',
      title: 'Component Matrix',
      subtitle: 'Complete batch tabular list and search',
      icon: Grid3X3,
      badge: 'TAB',
      action: () => {
        setActiveTab('components');
        onClose();
      }
    },
    {
      id: 'nav-topology',
      category: 'NAVIGATION',
      title: 'Neural Fault Topology',
      subtitle: 'Obsidian fluid physics cluster network',
      icon: Network,
      badge: 'TAB',
      action: () => {
        setActiveTab('topology');
        onClose();
      }
    },
    {
      id: 'nav-inspector',
      category: 'NAVIGATION',
      title: 'Telemetry Inspector',
      subtitle: 'Detailed trajectory curves & 168h forecast',
      icon: LineChart,
      badge: 'TAB',
      action: () => {
        setActiveTab('inspector');
        onClose();
      }
    },
    {
      id: 'nav-chamber',
      category: 'NAVIGATION',
      title: 'Chamber Environment',
      subtitle: 'Thermal stress & hardware socket distribution',
      icon: ThermometerSnowflake,
      badge: 'TAB',
      action: () => {
        setActiveTab('chamber');
        onClose();
      }
    },
    {
      id: 'nav-export',
      category: 'NAVIGATION',
      title: 'Audit & Compliance Export',
      subtitle: 'Download CSV and audit-traceable summaries',
      icon: FileSpreadsheet,
      badge: 'TAB',
      action: () => {
        setActiveTab('export');
        onClose();
      }
    }
  ], [setActiveTab, onClose]);

  // Operational actions
  const actionCommands = useMemo(() => [
    {
      id: 'action-upload',
      category: 'ACTIONS',
      title: 'Upload Burn-In CSV',
      subtitle: 'Screen new 0h & 24h checkpoint dataset',
      icon: UploadCloud,
      badge: 'INGEST',
      action: () => {
        onClose();
        onOpenUpload();
      }
    },
    {
      id: 'action-sample',
      category: 'ACTIONS',
      title: 'Load Verified Sample Demo',
      subtitle: 'Run live screening on 64 MLCC parts',
      icon: RefreshCcw,
      badge: 'DEMO',
      action: () => {
        onClose();
        onReloadDemo();
      }
    },
    {
      id: 'action-glossary',
      category: 'ACTIONS',
      title: 'Open Technical Glossary',
      subtitle: 'Definitions, Z-scores, conformal bounds & rules',
      icon: BookOpen,
      badge: 'DOCS',
      action: () => {
        onClose();
        window.dispatchEvent(new CustomEvent('open-glossary'));
      }
    },
    {
      id: 'action-tour',
      category: 'ACTIONS',
      title: 'Restart Onboarding Walkthrough',
      subtitle: 'First-run visual tour and step-by-step guide',
      icon: Sparkles,
      badge: 'TOUR',
      action: () => {
        onClose();
        window.dispatchEvent(new CustomEvent('open-onboarding'));
      }
    },
    {
      id: 'action-fullscreen',
      category: 'ACTIONS',
      title: 'Toggle Fullscreen Mode',
      subtitle: 'Expand dashboard view for lab wall displays',
      icon: Maximize2,
      badge: 'VIEW',
      action: () => {
        onClose();
        if (!document.fullscreenElement) {
          document.documentElement.requestFullscreen().catch(() => {});
        } else {
          document.exitFullscreen().catch(() => {});
        }
      }
    }
  ], [onClose, onOpenUpload, onReloadDemo]);

  // Filter commands
  const filterCommands = useMemo(() => [
    {
      id: 'filter-review',
      category: 'DISPOSITION FILTERS',
      title: 'Filter: REVIEW (ERROR)',
      subtitle: 'Show parts with limit breach or high drift',
      icon: AlertOctagon,
      badge: 'ERROR',
      color: 'text-rose-400',
      action: () => {
        onFilterByDecision('ENGINEER_REVIEW');
        onClose();
      }
    },
    {
      id: 'filter-retest',
      category: 'DISPOSITION FILTERS',
      title: 'Filter: RETEST',
      subtitle: 'Show parts with severe peer anomaly or suspect drift',
      icon: AlertTriangle,
      badge: 'RETEST',
      color: 'text-amber-400',
      action: () => {
        onFilterByDecision('RETEST');
        onClose();
      }
    },
    {
      id: 'filter-monitor',
      category: 'DISPOSITION FILTERS',
      title: 'Filter: MONITOR',
      subtitle: 'Show parts where interval upper bound reaches limit',
      icon: CheckCircle2,
      badge: 'MONITOR',
      color: 'text-yellow-400',
      action: () => {
        onFilterByDecision('MONITOR');
        onClose();
      }
    },
    {
      id: 'filter-accept',
      category: 'DISPOSITION FILTERS',
      title: 'Filter: ACCEPT (GOOD)',
      subtitle: 'Show parts meeting nominal burn-in criteria',
      icon: CheckCircle2,
      badge: 'GOOD',
      color: 'text-emerald-400',
      action: () => {
        onFilterByDecision('ACCEPT');
        onClose();
      }
    },
    {
      id: 'filter-all',
      category: 'DISPOSITION FILTERS',
      title: 'Show All Components',
      subtitle: 'Clear all active disposition filters',
      icon: Filter,
      badge: 'ALL',
      action: () => {
        onFilterByDecision('ALL');
        onClose();
      }
    }
  ], [onFilterByDecision, onClose]);

  // Dynamic component records matching
  const matchedComponents = useMemo(() => {
    const records = dataset?.records || [];
    if (!query.trim()) return [];

    const q = query.toLowerCase().trim();
    return records
      .filter(r => {
        const idMatch = r.component_id?.toLowerCase().includes(q);
        const batchMatch = r.batch_id?.toLowerCase().includes(q);
        const recMatch = r.recommendation?.toLowerCase().includes(q);
        const socketMatch = r.context?.board_position != null && String(r.context.board_position).includes(q);
        return idMatch || batchMatch || recMatch || socketMatch;
      })
      .slice(0, 10)
      .map(r => ({
        id: `comp-${r.component_id}`,
        category: 'COMPONENTS',
        title: r.component_id,
        subtitle: `${r.batch_id || 'Batch'} · Socket #${r.context?.board_position ?? 'N/A'} · 24h: ${formatUnit(r.early_features?.leakage_24h, 'µA', 3)}`,
        record: r,
        action: () => {
          onInspectComponent(r.component_id);
          onClose();
        }
      }));
  }, [dataset?.records, query, onInspectComponent, onClose]);

  // Combined and filtered command list
  const filteredCommands = useMemo(() => {
    const q = query.toLowerCase().trim();
    if (!q) {
      // Default initial view: top navigation + key actions + quick filters
      return [...navigationCommands, ...actionCommands, ...filterCommands];
    }

    const staticMatches = [
      ...navigationCommands,
      ...actionCommands,
      ...filterCommands
    ].filter(cmd => 
      cmd.title.toLowerCase().includes(q) ||
      cmd.subtitle.toLowerCase().includes(q) ||
      cmd.category.toLowerCase().includes(q) ||
      (cmd.badge && cmd.badge.toLowerCase().includes(q))
    );

    return [...matchedComponents, ...staticMatches];
  }, [query, navigationCommands, actionCommands, filterCommands, matchedComponents]);

  // Reset selectedIndex if it goes out of range
  useEffect(() => {
    if (selectedIndex >= filteredCommands.length) {
      setSelectedIndex(0);
    }
  }, [filteredCommands.length, selectedIndex]);

  // Scroll active item into view
  useEffect(() => {
    if (listRef.current) {
      const activeEl = listRef.current.querySelector('[data-active="true"]');
      if (activeEl) {
        activeEl.scrollIntoView({ block: 'nearest' });
      }
    }
  }, [selectedIndex]);

  // Handle keyboard events inside modal
  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      e.preventDefault();
      onClose();
      return;
    }

    if (filteredCommands.length === 0) return;

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex(prev => (prev + 1) % filteredCommands.length);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex(prev => (prev - 1 + filteredCommands.length) % filteredCommands.length);
    } else if (e.key === 'Enter') {
      e.preventDefault();
      const current = filteredCommands[selectedIndex];
      if (current && current.action) {
        current.action();
      }
    }
  };

  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Command Palette"
      className="fixed inset-0 z-50 flex items-start justify-center pt-16 sm:pt-24 px-4 bg-black/75 backdrop-blur-md animate-in fade-in duration-150"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        className="w-full max-w-2xl rounded-2xl bg-[#08090e] border border-white/10 shadow-[0_25px_60px_rgba(0,0,0,0.85),0_0_30px_rgba(249,115,22,0.12)] overflow-hidden flex flex-col max-h-[80vh] animate-in zoom-in-95 duration-150"
        onKeyDown={handleKeyDown}
      >
        {/* Top Header Bar */}
        <div className="flex items-center justify-between px-4 py-2.5 border-b border-white/[0.06] bg-white/[0.02]">
          <div className="flex items-center gap-2">
            <LeakageLensLogo className="w-4 h-4" showGlow />
            <span className="text-[11px] font-mono font-semibold tracking-wider text-orange-400 uppercase">
              LEAKAGE LENS // COMMAND CENTER
            </span>
          </div>
          <button
            onClick={onClose}
            className="w-6 h-6 rounded-md hover:bg-white/10 text-slate-400 hover:text-white flex items-center justify-center transition-colors cursor-pointer"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Search Input */}
        <div className="relative flex items-center px-4 py-3 border-b border-white/[0.06] bg-black/30">
          <Search className="w-4 h-4 text-orange-400 shrink-0 mr-3" strokeWidth={1.5} />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setSelectedIndex(0);
            }}
            placeholder="Type a command or search parts (e.g. C000147, B018, topology, review)..."
            className="w-full bg-transparent text-sm text-white placeholder-slate-500 focus:outline-none font-mono"
          />
          {query && (
            <button
              onClick={() => {
                setQuery('');
                setSelectedIndex(0);
                inputRef.current?.focus();
              }}
              className="p-1 text-slate-500 hover:text-slate-300 rounded cursor-pointer"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
          <span className="ml-2 px-1.5 py-0.5 rounded bg-white/[0.05] border border-white/10 text-[10px] font-mono text-slate-400 shrink-0">
            ESC
          </span>
        </div>

        {/* Results List */}
        <div
          ref={listRef}
          className="flex-1 overflow-y-auto p-2 divide-y divide-white/[0.02] space-y-1 font-mono"
        >
          {filteredCommands.length === 0 ? (
            <div className="py-12 px-6 text-center text-slate-500">
              <Search className="w-8 h-8 mx-auto mb-2 opacity-30 text-orange-400" />
              <p className="text-xs text-slate-400 font-medium">No commands or components found for &ldquo;{query}&rdquo;</p>
              <p className="text-[11px] text-slate-600 mt-1">
                Try searching for a component ID like &ldquo;C000&rdquo;, a batch like &ldquo;B018&rdquo;, or &ldquo;overview&rdquo;
              </p>
            </div>
          ) : (
            filteredCommands.map((item, index) => {
              const isSelected = index === selectedIndex;
              const Icon = item.icon || Layers;
              const isComponent = item.category === 'COMPONENTS';

              return (
                <div
                  key={item.id}
                  data-active={isSelected}
                  onClick={() => item.action && item.action()}
                  onMouseEnter={() => setSelectedIndex(index)}
                  className={`flex items-center justify-between p-2.5 rounded-xl transition-all cursor-pointer ${
                    isSelected
                      ? 'bg-orange-500/15 border border-orange-500/30 text-white shadow-[0_0_15px_rgba(249,115,22,0.1)]'
                      : 'hover:bg-white/[0.04] border border-transparent text-slate-300'
                  }`}
                >
                  <div className="flex items-center gap-3 min-w-0 pr-3">
                    <div
                      className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 border transition-colors ${
                        isSelected
                          ? 'bg-orange-500 text-black border-orange-400 shadow-sm'
                          : 'bg-white/[0.03] border-white/[0.06] text-slate-400'
                      }`}
                    >
                      {isComponent ? (
                        <LeakageLensLogo className={`w-4 h-4 ${isSelected ? 'text-black' : ''}`} showGlow={isSelected} />
                      ) : (
                        <Icon className={`w-4 h-4 ${item.color && !isSelected ? item.color : ''}`} strokeWidth={1.5} />
                      )}
                    </div>

                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-semibold tracking-tight truncate text-white">
                          {item.title}
                        </span>
                        {item.badge && (
                          <span
                            className={`px-1.5 py-0.2 rounded text-[9.5px] uppercase border ${
                              item.badge === 'ERROR'
                                ? 'bg-rose-500/20 text-rose-300 border-rose-500/40'
                                : item.badge === 'GOOD'
                                ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                                : item.badge === 'RETEST'
                                ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                                : 'bg-white/[0.05] text-slate-400 border-white/10'
                            }`}
                          >
                            {item.badge}
                          </span>
                        )}
                      </div>
                      <p className="text-[11px] text-slate-400 truncate mt-0.5">
                        {item.subtitle}
                      </p>
                    </div>
                  </div>

                  {/* Right side details / action indicator */}
                  <div className="flex items-center gap-2 shrink-0">
                    {isComponent && item.record && (
                      <div className="hidden sm:flex items-center gap-1.5">
                        <DecisionBadge decision={item.record.recommendation} size="sm" />
                      </div>
                    )}
                    {isSelected && (
                      <div className="flex items-center gap-1 text-[11px] text-orange-400 animate-pulse font-mono">
                        <span>Run</span>
                        <CornerDownLeft className="w-3 h-3" />
                      </div>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Footer Shortcut Helper */}
        <div className="flex flex-wrap items-center justify-between px-4 py-2 border-t border-white/[0.06] bg-black/40 text-[11px] font-mono text-slate-500">
          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1">
              <kbd className="px-1.5 py-0.5 rounded bg-white/[0.06] border border-white/10 text-[10px] text-slate-400">↑↓</kbd>
              <span>Navigate</span>
            </span>
            <span className="flex items-center gap-1">
              <kbd className="px-1.5 py-0.5 rounded bg-white/[0.06] border border-white/10 text-[10px] text-slate-400">↵</kbd>
              <span>Select</span>
            </span>
            <span className="flex items-center gap-1">
              <kbd className="px-1.5 py-0.5 rounded bg-white/[0.06] border border-white/10 text-[10px] text-slate-400">ESC</kbd>
              <span>Dismiss</span>
            </span>
          </div>

          <div className="hidden sm:flex items-center gap-1.5 text-slate-400">
            <span className="w-1.5 h-1.5 rounded-full bg-orange-400 animate-pulse" />
            <span>Leakage Lens v1.1</span>
          </div>
        </div>
      </div>
    </div>
  );
}
