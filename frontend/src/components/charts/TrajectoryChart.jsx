import React from 'react';

export default function TrajectoryChart({
  record,
  showOutcome = false,
  height = 280
}) {
  if (!record) return null;

  const limit = record.limits?.applicable_limit || 0.25;
  const earlyTraj = record.early_trajectory || [
    { hour: 0, value: record.initial_value || 0.02 },
    { hour: 24, value: record.latest_value || 0.03 }
  ];
  const outcomeTraj = record.outcome_trajectory || [];
  const forecast = record.forecast || {};
  const predVal = forecast.predicted_final_value || (record.latest_value * 1.2);
  const predLower = forecast.prediction_lower ?? (predVal * 0.85);
  const predUpper = forecast.prediction_upper ?? (predVal * 1.25);

  // Compute scale boundaries
  const allValues = [
    limit,
    ...earlyTraj.map(p => p.value),
    predVal,
    predLower,
    predUpper,
    ...(showOutcome ? outcomeTraj.map(p => p.value) : [])
  ].filter(v => v !== null && !isNaN(v));

  const maxVal = Math.max(...allValues, limit * 1.15) * 1.1;
  const minVal = 0;

  // Chart dimensions
  const width = 640;
  const padding = { top: 30, right: 60, bottom: 40, left: 55 };
  const innerW = width - padding.left - padding.right;
  const innerH = height - padding.top - padding.bottom;

  // Coordinate mappers
  const getX = (hour) => padding.left + (hour / 168) * innerW;
  const getY = (val) => padding.top + innerH - ((val - minVal) / (maxVal - minVal)) * innerH;

  // Early path
  const earlyPath = earlyTraj.map((p, i) => `${i === 0 ? 'M' : 'L'} ${getX(p.hour)} ${getY(p.value)}`).join(' ');

  // Outcome path
  const fullObserved = showOutcome ? [
    ...earlyTraj,
    ...outcomeTraj
  ].sort((a, b) => a.hour - b.hour) : [];
  const outcomePath = fullObserved.map((p, i) => `${i === 0 ? 'M' : 'L'} ${getX(p.hour)} ${getY(p.value)}`).join(' ');

  return (
    <div className="w-full relative overflow-hidden select-none">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="w-full h-auto overflow-visible font-mono"
      >
        <defs>
          {/* Subtle grid pattern */}
          <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(255, 255, 255, 0.04)" strokeWidth="1" />
          </pattern>
          {/* Forecast uncertainty gradient */}
          <linearGradient id="forecastGlow" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#f97316" stopOpacity="0.3" />
            <stop offset="100%" stopColor="#f97316" stopOpacity="0.05" />
          </linearGradient>
        </defs>

        <rect x={padding.left} y={padding.top} width={innerW} height={innerH} fill="url(#grid)" rx="6" />

        {/* Observation Cutoff Shaded Zone (0 to 24h) */}
        <rect
          x={padding.left}
          y={padding.top}
          width={getX(24) - padding.left}
          height={innerH}
          fill="rgba(255, 255, 255, 0.02)"
        />

        {/* 24h Cutoff Vertical Marker */}
        <line
          x1={getX(24)}
          y1={padding.top - 10}
          x2={getX(24)}
          y2={height - padding.bottom}
          stroke="#f97316"
          strokeWidth="1.5"
          strokeDasharray="4 4"
          strokeOpacity="0.7"
        />
        <text
          x={getX(24)}
          y={padding.top - 14}
          fill="#f97316"
          fontSize="9"
          textAnchor="middle"
          fontWeight="bold"
        >
          24h CUTOFF
        </text>

        {/* Specification Upper Limit Line */}
        <line
          x1={padding.left}
          y1={getY(limit)}
          x2={width - padding.right}
          y2={getY(limit)}
          stroke="#f97316"
          strokeWidth="1.5"
          strokeDasharray="4 4"
          strokeOpacity="0.85"
        />
        <text
          x={width - padding.right + 5}
          y={getY(limit) + 3}
          fill="#f97316"
          fontSize="9"
          fontWeight="bold"
        >
          LIMIT ({limit} µA)
        </text>

        {/* Horizontal Axis Ticks */}
        {[0, 24, 48, 72, 96, 120, 144, 168].map(h => (
          <g key={h} transform={`translate(${getX(h)}, ${height - padding.bottom})`}>
            <line y2="5" stroke="rgba(255,255,255,0.12)" />
            <text y="18" fill="#64748b" fontSize="9" textAnchor="middle">
              {h}h
            </text>
          </g>
        ))}

        {/* Vertical Axis Ticks */}
        {[0, maxVal * 0.33, maxVal * 0.66, maxVal].map((val, idx) => (
          <g key={idx} transform={`translate(${padding.left}, ${getY(val)})`}>
            <line x2="-5" stroke="rgba(255,255,255,0.12)" />
            <text x="-8" y="3" fill="#64748b" fontSize="9" textAnchor="end">
              {val.toFixed(2)}
            </text>
          </g>
        ))}

        {/* Early Observed Trajectory (0 to 24h) */}
        <path
          d={earlyPath}
          fill="none"
          stroke="#f8fafc"
          strokeWidth="2.5"
          strokeLinecap="round"
        />
        {earlyTraj.map(p => (
          <circle
            key={p.hour}
            cx={getX(p.hour)}
            cy={getY(p.value)}
            r="4"
            fill="#f8fafc"
            stroke="#08090d"
            strokeWidth="2"
          />
        ))}

        {/* 168h Forecast Uncertainty Whisker Band */}
        <line
          x1={getX(168)}
          y1={getY(predLower)}
          x2={getX(168)}
          y2={getY(predUpper)}
          stroke="#f97316"
          strokeWidth="2"
        />
        {/* Whisker caps */}
        <line
          x1={getX(168) - 5}
          y1={getY(predLower)}
          x2={getX(168) + 5}
          y2={getY(predLower)}
          stroke="#f97316"
          strokeWidth="2"
        />
        <line
          x1={getX(168) - 5}
          y1={getY(predUpper)}
          x2={getX(168) + 5}
          y2={getY(predUpper)}
          stroke="#f97316"
          strokeWidth="2"
        />

        {/* 168h Forecast Point Marker */}
        <circle
          cx={getX(168)}
          cy={getY(predVal)}
          r="5.5"
          fill="#f97316"
          stroke="#fff"
          strokeWidth="2"
        />
        <text
          x={getX(168) - 10}
          y={getY(predVal) - 10}
          fill="#f97316"
          fontSize="10"
          fontWeight="bold"
          textAnchor="end"
        >
          Forecast: {predVal} µA
        </text>

        {/* Outcome Reveal Overlay */}
        {showOutcome && outcomeTraj.length > 0 && (
          <>
            <path
              d={outcomePath}
              fill="none"
              stroke="#94a3b8"
              strokeWidth="2"
              strokeDasharray="3 3"
              strokeLinecap="round"
            />
            {outcomeTraj.map(p => (
              <circle
                key={p.hour}
                cx={getX(p.hour)}
                cy={getY(p.value)}
                r="3.5"
                fill="#cbd5e1"
                stroke="#08090d"
                strokeWidth="1.5"
              />
            ))}
            <text
              x={getX(168) + 10}
              y={getY(record.observed_168h || outcomeTraj[outcomeTraj.length - 1].value) + 4}
              fill="#cbd5e1"
              fontSize="10"
              fontWeight="bold"
            >
              Actual 168h: {record.observed_168h} µA
            </text>
          </>
        )}
      </svg>
    </div>
  );
}
