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
    sm: 'text-[10px] px-2 py-0.5 gap-1 tracking-wider whitespace-nowrap',
    md: 'text-xs px-2.5 py-1 gap-1.5 tracking-wider whitespace-nowrap',
    lg: 'text-sm px-3.5 py-1.5 gap-2 font-semibold tracking-wide whitespace-nowrap'
  };

  return (
    <div className="inline-flex flex-col gap-1 shrink-0">
      <span
        className={`
          inline-flex items-center rounded-lg border font-mono font-medium uppercase
          ${config.badgeClass}
          ${sizeClasses[size]}
        `}
      >
        <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${config.dotClass}`} />
        {IconComponent && <IconComponent className={size === 'sm' ? 'w-3 h-3 shrink-0' : 'w-3.5 h-3.5 shrink-0'} strokeWidth={1.5} />}
        <span>{config.label}</span>
      </span>
      {showDescription && (
        <p className="text-[11px] text-slate-400 leading-tight">
          {config.description}
        </p>
      )}
    </div>
  );
}
