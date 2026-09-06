import React from 'react';
import { DECISION_CONFIG } from '../../lib/utils';
import { CheckCircle2, AlertTriangle, RefreshCw, AlertOctagon } from 'lucide-react';

const ICONS = {
  ACCEPT: CheckCircle2,
  MONITOR: AlertTriangle,
  RETEST: RefreshCw,
  ENGINEER_REVIEW: AlertOctagon
};

export default function DecisionBadge({ decision, size = 'md', showDescription = false }) {
  const config = DECISION_CONFIG[decision] || {
    label: decision || 'UNSCORED',
    badgeClass: 'bg-slate-500/15 text-slate-400 border-slate-500/30',
    dotClass: 'bg-slate-400',
    description: 'No recommendation available.'
  };

  const IconComponent = ICONS[decision];

  const sizeClasses = {
    sm: 'text-[10px] px-2 py-0.5 gap-1 tracking-wider',
    md: 'text-xs px-2.5 py-1 gap-1.5 tracking-wider',
    lg: 'text-sm px-3.5 py-1.5 gap-2 font-semibold tracking-wide'
  };

  const STAMPS = {
    ACCEPT: 'QA:PASS',
    MONITOR: 'QA:FLAG',
    RETEST: 'QA:RETEST',
    ENGINEER_REVIEW: 'QA:CRIT'
  };

  return (
    <div className="inline-flex flex-col gap-1 select-none">
      <span
        className={`
          inline-flex items-center rounded-lg border font-mono uppercase tracking-wider
          transition-all duration-150 relative overflow-hidden
          ${config.badgeClass}
          ${sizeClasses[size]}
        `}
      >
        {/* Subtle physical stamp background corner ticks */}
        <span className="absolute left-0 top-0 bottom-0 w-0.5 bg-current opacity-30" />
        
        <span className={`w-1.5 h-1.5 rounded-full ${config.dotClass} shadow-[0_0_6px_currentColor]`} />
        {IconComponent && <IconComponent className={size === 'sm' ? 'w-3 h-3' : 'w-3.5 h-3.5'} strokeWidth={1.5} />}
        <span className="font-semibold">{config.label}</span>

        {size === 'lg' && (
          <span className="ml-1 text-[9px] opacity-60 font-mono tracking-widest pl-1 border-l border-current">
            [{STAMPS[decision] || 'UNSET'}]
          </span>
        )}
      </span>
      {showDescription && (
        <p className="text-[11px] text-slate-400 leading-tight font-sans">
          {config.description}
        </p>
      )}
    </div>
  );
}
