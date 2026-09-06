import React from 'react';
import { LayoutDashboard, Grid3X3, LineChart, ThermometerSnowflake, FileSpreadsheet } from 'lucide-react';

export default function Navigation({ activeTab, setActiveTab, counts = {} }) {
  const tabs = [
    {
      id: 'overview',
      label: 'Screening Overview',
      icon: LayoutDashboard,
      badge: null
    },
    {
      id: 'components',
      label: 'Component Matrix & Spatial Grid',
      icon: Grid3X3,
      badge: counts.total || null
    },
    {
      id: 'inspector',
      label: 'Telemetry & Forecast Inspector',
      icon: LineChart,
      badge: (counts.anomalies > 0 ? `${counts.anomalies} flagged` : null)
    },
    {
      id: 'chamber',
      label: 'Chamber & Stress Telemetry',
      icon: ThermometerSnowflake,
      badge: '125°C'
    },
    {
      id: 'export',
      label: 'Audit & Reports',
      icon: FileSpreadsheet,
      badge: null
    }
  ];

  return (
    <nav className="w-full bg-[#08090d]/60 backdrop-blur-xl border-b border-white/[0.06] px-6 py-2">
      <div className="max-w-7xl mx-auto flex items-center gap-1.5 overflow-x-auto no-scrollbar">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;

          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`
                flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all duration-150 whitespace-nowrap cursor-pointer
                ${
                  isActive
                    ? 'bg-orange-500/10 text-orange-400 border border-orange-500/30 font-medium'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-white/[0.03] border border-transparent'
                }
              `}
            >
              <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-orange-400' : 'text-slate-500'}`} />
              <span>{tab.label}</span>
              {tab.badge && (
                <span
                  className={`
                    px-1.5 py-0.2 rounded text-[10px] font-mono
                    ${isActive ? 'bg-orange-500/20 text-orange-300 border border-orange-500/30' : 'bg-white/[0.05] text-slate-500'}
                  `}
                >
                  {tab.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>
    </nav>
  );
}
