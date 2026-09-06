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
    label: 'ACCEPT (GOOD)',
    badgeClass: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/35 backdrop-blur-md font-semibold',
    dotClass: 'bg-emerald-400 shadow-[0_0_8px_rgba(16,185,129,0.7)]',
    cardBorder: 'hover:border-emerald-500/40',
    gradientText: 'from-emerald-400 to-teal-300',
    textColor: 'text-emerald-400',
    colorHex: '#10b981',
    description: 'Nominal drift trajectory; within verified statistical bounds.'
  },
  MONITOR: {
    label: 'MONITOR',
    badgeClass: 'bg-yellow-500/15 text-yellow-300 border-yellow-500/30 backdrop-blur-md font-medium',
    dotClass: 'bg-yellow-400 shadow-[0_0_6px_rgba(234,179,8,0.5)]',
    cardBorder: 'hover:border-yellow-500/35',
    gradientText: 'from-yellow-200 to-amber-300',
    textColor: 'text-yellow-400',
    colorHex: '#eab308',
    description: 'Elevated rate of drift or forecast interval approaches threshold.'
  },
  RETEST: {
    label: 'RETEST',
    badgeClass: 'bg-amber-500/15 text-amber-300 border-amber-500/35 backdrop-blur-md font-medium',
    dotClass: 'bg-amber-400 shadow-[0_0_8px_rgba(245,158,11,0.6)]',
    cardBorder: 'hover:border-amber-500/40',
    gradientText: 'from-amber-300 to-orange-400',
    textColor: 'text-amber-400',
    colorHex: '#f59e0b',
    description: 'Significant peer anomaly (score ≥ 0.8) or projected limit breach.'
  },
  ENGINEER_REVIEW: {
    label: 'REVIEW (ERROR)',
    badgeClass: 'bg-rose-500/20 text-rose-300 border-rose-500/50 backdrop-blur-md font-bold',
    dotClass: 'bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.8)]',
    cardBorder: 'hover:border-rose-500/60',
    gradientText: 'from-rose-400 to-red-500',
    textColor: 'text-rose-400',
    colorHex: '#ef4444',
    description: 'Critical defect / error: active limit breach or confirmed anomaly.'
  }
};

export function getThermalColor(limitFraction) {
  if (limitFraction >= 1.0) {
    // Error / Limit Breach -> RED
    return {
      bg: 'bg-rose-500 text-white font-bold',
      border: 'border-rose-400',
      text: 'text-white font-bold',
      shadow: 'shadow-[0_0_12px_rgba(239,68,68,0.7)]',
      dot: 'bg-white'
    };
  }
  if (limitFraction >= 0.75) {
    // High / Near Limit -> AMBER
    return {
      bg: 'bg-amber-500/25 text-amber-300',
      border: 'border-amber-500/50',
      text: 'text-amber-300 font-semibold',
      shadow: 'shadow-[0_0_8px_rgba(245,158,11,0.3)]',
      dot: 'bg-amber-400'
    };
  }
  if (limitFraction >= 0.45) {
    // Elevated -> YELLOW
    return {
      bg: 'bg-yellow-500/15 text-yellow-300',
      border: 'border-yellow-500/30',
      text: 'text-yellow-300',
      shadow: '',
      dot: 'bg-yellow-400'
    };
  }
  if (limitFraction >= 0.2) {
    // Healthy -> LIGHT GREEN
    return {
      bg: 'bg-emerald-500/15 text-emerald-300',
      border: 'border-emerald-500/30',
      text: 'text-emerald-300',
      shadow: '',
      dot: 'bg-emerald-400'
    };
  }
  // Optimal / Going Good -> VIBRANT EMERALD GREEN
  return {
    bg: 'bg-emerald-500/10 text-emerald-400',
    border: 'border-emerald-500/20',
    text: 'text-emerald-400',
    shadow: '',
    dot: 'bg-emerald-500'
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
