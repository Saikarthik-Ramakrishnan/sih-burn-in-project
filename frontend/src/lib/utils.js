/**
 * Utility functions for formatting, styling, and data export.
 */

export function formatUnit(value, unit = 'µA', precision = 4) {
  if (value === null || value === undefined || isNaN(value)) {
    return 'N/A';
  }
  return `${Number(value).toFixed(precision)} ${unit}`;
}

export function formatPercent(fraction, precision = 1) {
  if (fraction === null || fraction === undefined || isNaN(fraction)) {
    return 'N/A';
  }
  return `${(Number(fraction) * 100).toFixed(precision)}%`;
}

export function formatZ(zScore, precision = 2) {
  if (zScore === null || zScore === undefined || isNaN(zScore)) {
    return 'N/A';
  }
  const num = Number(zScore);
  const sign = num > 0 ? '+' : '';
  return `${sign}${num.toFixed(precision)}σ`;
}

export const DECISION_CONFIG = {
  ACCEPT: {
    label: 'ACCEPT',
    badgeClass: 'bg-white/[0.04] text-slate-300 border-white/[0.1] backdrop-blur-md',
    dotClass: 'bg-slate-400',
    cardBorder: 'hover:border-white/20',
    gradientText: 'from-slate-200 to-slate-400',
    description: 'Nominal drift trajectory; within verified statistical bounds.'
  },
  MONITOR: {
    label: 'MONITOR',
    badgeClass: 'bg-orange-500/[0.08] text-orange-200 border-orange-500/25 backdrop-blur-md',
    dotClass: 'bg-orange-400',
    cardBorder: 'hover:border-orange-500/30',
    gradientText: 'from-orange-200 to-amber-300',
    description: 'Elevated rate of drift or forecast interval approaches threshold.'
  },
  RETEST: {
    label: 'RETEST',
    badgeClass: 'bg-orange-500/[0.15] text-orange-300 border-orange-500/35 backdrop-blur-md font-medium',
    dotClass: 'bg-orange-400',
    cardBorder: 'hover:border-orange-500/40',
    gradientText: 'from-orange-300 to-amber-400',
    description: 'Significant peer anomaly (score ≥ 0.8) or projected limit breach.'
  },
  ENGINEER_REVIEW: {
    label: 'ENGINEER REVIEW',
    badgeClass: 'bg-orange-500/25 text-orange-400 border-orange-500/50 backdrop-blur-md font-bold',
    dotClass: 'bg-orange-500 shadow-[0_0_8px_rgba(249,115,22,0.8)]',
    cardBorder: 'hover:border-orange-500/60',
    gradientText: 'from-orange-400 to-amber-400',
    description: 'Immediate inspection needed: active limit breach or confirmed anomaly.'
  }
};

export function getThermalColor(limitFraction) {
  if (limitFraction >= 1.0) {
    return {
      bg: 'bg-orange-500 text-black font-bold',
      border: 'border-orange-400',
      text: 'text-black font-bold',
      shadow: 'shadow-[0_0_12px_rgba(249,115,22,0.5)]',
      dot: 'bg-black'
    };
  }
  if (limitFraction >= 0.75) {
    return {
      bg: 'bg-orange-600/75 text-white',
      border: 'border-orange-500/60',
      text: 'text-white font-semibold',
      shadow: 'shadow-[0_0_8px_rgba(249,115,22,0.25)]',
      dot: 'bg-orange-200'
    };
  }
  if (limitFraction >= 0.45) {
    return {
      bg: 'bg-orange-950/60 text-orange-200',
      border: 'border-orange-500/30',
      text: 'text-orange-200',
      shadow: '',
      dot: 'bg-orange-400'
    };
  }
  if (limitFraction >= 0.2) {
    return {
      bg: 'bg-[#121522] text-slate-300',
      border: 'border-white/[0.08]',
      text: 'text-slate-300',
      shadow: '',
      dot: 'bg-slate-500'
    };
  }
  return {
    bg: 'bg-[#0b0d14] text-slate-500',
    border: 'border-white/[0.04]',
    text: 'text-slate-500',
    shadow: '',
    dot: 'bg-slate-700'
  };
}

export function exportToCsv(filename, rows) {
  if (!rows || !rows.length) return;
  const headers = Object.keys(rows[0]);
  const csvRows = [headers.join(',')];

  for (const row of rows) {
    const values = headers.map(header => {
      const escaped = ('' + (row[header] ?? '')).replace(/"/g, '""');
      return `"${escaped}"`;
    });
    csvRows.push(values.join(','));
  }

  const blob = new Blob([csvRows.join('\n')], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.setAttribute('href', url);
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

export function downloadJson(filename, data) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.setAttribute('href', url);
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}
