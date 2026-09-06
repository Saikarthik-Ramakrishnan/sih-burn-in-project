import React, { useState } from 'react';
import {
  LayoutDashboard,
  Grid3X3,
  LineChart,
  ThermometerSnowflake,
  FileSpreadsheet,
  Cpu,
  UploadCloud,
  ChevronRight,
  Network
} from 'lucide-react';

export default function Navigation({
  activeTab,
  setActiveTab,
  counts = {},
  onOpenUpload,
  backendReady
}) {
  const [isExpanded, setIsExpanded] = useState(false);

  const tabs = [
    {
      id: 'overview',
      label: 'Screening Overview',
      icon: LayoutDashboard,
      badge: null
    },
    {
      id: 'components',
      label: 'Component Matrix',
      icon: Grid3X3,
      badge: counts.total ? `${counts.total}` : null
    },
    {
      id: 'topology',
      label: 'Fault Topology',
      icon: Network,
      badge: 'CLUSTERS'
    },
    {
      id: 'inspector',
      label: 'Telemetry Inspector',
      icon: LineChart,
      badge: counts.anomalies > 0 ? `${counts.anomalies}` : null
    },
    {
      id: 'chamber',
      label: 'Chamber & Stress',
      icon: ThermometerSnowflake,
      badge: '125°C'
    },
    {
      id: 'export',
      label: 'Audit & Export',
      icon: FileSpreadsheet,
      badge: null
    }
  ];

  return (
    <aside
      onMouseEnter={() => setIsExpanded(true)}
      onMouseLeave={() => setIsExpanded(false)}
      className={`
        fixed left-0 top-0 bottom-0 z-50 flex flex-col justify-between
        bg-[#07080d]/90 backdrop-blur-2xl border-r border-white/[0.06]
        transition-all duration-300 ease-[cubic-bezier(0.16,1,0.3,1)]
        ${isExpanded ? 'w-64 shadow-[12px_0_32px_rgba(0,0,0,0.5)]' : 'w-16 shadow-[4px_0_16px_rgba(0,0,0,0.25)]'}
      `}
    >
      {/* Top: Brand & Logo */}
      <div className="p-3.5 border-b border-white/[0.05]">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-orange-500/10 border border-orange-500/20 text-orange-400 flex items-center justify-center shrink-0">
            <Cpu className="w-4 h-4" strokeWidth={1.5} />
          </div>

          <div
            className={`
              flex flex-col transition-opacity duration-200 overflow-hidden whitespace-nowrap
              ${isExpanded ? 'opacity-100 max-w-full' : 'opacity-0 max-w-0 pointer-events-none'}
            `}
          >
            <div className="flex items-center gap-1.5">
              <span className="text-xs font-semibold tracking-tight text-white">
                Burn-In Sentinel
              </span>
              <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-orange-500/15 text-orange-300 border border-orange-500/25">
                SIH26170
              </span>
            </div>
            <span className="text-[10px] text-slate-400 tracking-normal">
              Reliability Console
            </span>
          </div>
        </div>
      </div>

      {/* Middle: Navigation Items */}
      <nav className="flex-1 py-3 px-2 space-y-1 overflow-y-auto overflow-x-hidden">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;

          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`
                relative w-full flex items-center h-10 px-3 rounded-lg text-xs transition-all duration-150 cursor-pointer group
                ${
                  isActive
                    ? 'bg-orange-500/10 text-orange-400 border border-orange-500/20 font-medium'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-white/[0.03] border border-transparent'
                }
              `}
              title={!isExpanded ? tab.label : undefined}
            >
              {/* Active Indicator Bar */}
              {isActive && (
                <span className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 rounded-r bg-orange-400" />
              )}

              {/* Icon */}
              <div className="w-5 flex items-center justify-center shrink-0">
                <Icon
                  className={`w-4 h-4 transition-colors ${
                    isActive ? 'text-orange-400' : 'text-slate-400 group-hover:text-slate-200'
                  }`}
                  strokeWidth={1.5}
                />
              </div>

              {/* Label & Badge (shown when expanded) */}
              <div
                className={`
                  flex-1 flex items-center justify-between ml-3 transition-opacity duration-200 overflow-hidden whitespace-nowrap
                  ${isExpanded ? 'opacity-100 max-w-full' : 'opacity-0 max-w-0 pointer-events-none'}
                `}
              >
                <span className="truncate tracking-tight">{tab.label}</span>

                {tab.badge && (
                  <span
                    className={`
                      ml-2 px-1.5 py-0.2 rounded text-[10px] font-mono shrink-0
                      ${
                        isActive
                          ? 'bg-orange-500/20 text-orange-300 border border-orange-500/30'
                          : 'bg-white/[0.04] text-slate-500 border border-white/[0.06]'
                      }
                    `}
                  >
                    {tab.badge}
                  </span>
                )}
              </div>
            </button>
          );
        })}
      </nav>

      {/* Bottom: Status & Quick Action */}
      <div className="p-2.5 border-t border-white/[0.05] space-y-2">
        {onOpenUpload && (
          <button
            onClick={onOpenUpload}
            className={`
              w-full flex items-center justify-center gap-2 h-9 rounded-lg text-xs font-mono transition-all cursor-pointer
              ${
                isExpanded
                  ? 'btn-primary px-3'
                  : 'p-2 text-orange-400 hover:bg-orange-500/10 border border-transparent hover:border-orange-500/20'
              }
            `}
            title={!isExpanded ? 'Screen CSV' : undefined}
          >
            <UploadCloud className="w-4 h-4 shrink-0" strokeWidth={1.5} />
            <span
              className={`
                transition-opacity duration-200 overflow-hidden whitespace-nowrap
                ${isExpanded ? 'opacity-100 max-w-full' : 'opacity-0 max-w-0 hidden'}
              `}
            >
              Screen CSV
            </span>
          </button>
        )}

        {/* Minimal Status Dot */}
        <div className="flex items-center justify-center sm:justify-start gap-2.5 px-2 py-1.5 rounded-lg text-[11px] font-mono text-slate-400">
          <span
            className={`w-1.5 h-1.5 rounded-full shrink-0 ${
              backendReady ? 'bg-orange-400' : 'bg-slate-500'
            }`}
          />
          <span
            className={`
              transition-opacity duration-200 overflow-hidden whitespace-nowrap text-[10px]
              ${isExpanded ? 'opacity-100 max-w-full' : 'opacity-0 max-w-0 hidden'}
            `}
          >
            {backendReady ? 'SYSTEM ONLINE' : 'LOCAL DEMO'}
          </span>
        </div>
      </div>
    </aside>
  );
}
