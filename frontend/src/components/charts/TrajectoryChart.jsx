import React, { useState, useRef } from 'react';
import { playTick } from '../../lib/audioEffects';

export default function TrajectoryChart({
  record,
  showOutcome = false,
  height = 280
}) {
  const svgRef = useRef(null);
  const [crosshair, setCrosshair] = useState(null);

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

  // Handle interactive crosshair movement (Design Spell)
  const handleMouseMove = (e) => {
    if (!svgRef.current) return;
    const rect = svgRef.current.getBoundingClientRect();
    const clientX = e.clientX - rect.left;
    const clientY = e.clientY - rect.top;

    // Convert clientX to SVG viewBox coordinates
    const scaleX = width / rect.width;
    const scaleY = height / rect.height;
    const svgX = clientX * scaleX;
    const svgY = clientY * scaleY;

    if (svgX < padding.left || svgX > width - padding.right) {
      setCrosshair(null);
      return;
    }

    // Calculate time hour
    let hour = Math.round(((svgX - padding.left) / innerW) * 168);
    hour = Math.max(0, Math.min(168, hour));

    // Calculate approximate value
    let approxVal;
    let label = `${hour}h`;
    let snapX = svgX;
    let snapY = svgY;

    if (Math.abs(hour - 0) <= 6) {
      hour = 0;
      snapX = getX(0);
      snapY = getY(record.initial_value);
      approxVal = record.initial_value;
      label = `T0 BASELINE (${approxVal} µA)`;
    } else if (Math.abs(hour - 24) <= 6) {
      hour = 24;
      snapX = getX(24);
      snapY = getY(record.latest_value);
      approxVal = record.latest_value;
      label = `T24 CUTOFF (${approxVal} µA)`;
    } else if (Math.abs(hour - 168) <= 6) {
      hour = 168;
      snapX = getX(168);
      snapY = getY(predVal);
      approxVal = predVal;
      label = `T168 FORECAST (${approxVal} µA)`;
    } else {
      // Linear interpolation between known points
      if (hour <= 24) {
        approxVal = (record.initial_value + (hour / 24) * (record.latest_value - record.initial_value)).toFixed(4);
      } else {
        approxVal = (record.latest_value + ((hour - 24) / (168 - 24)) * (predVal - record.latest_value)).toFixed(4);
      }
      snapY = getY(approxVal);
      label = `T+${hour}h: ${approxVal} µA`;
    }

    setCrosshair({
      x: snapX,
      y: snapY,
      hour,
      value: approxVal,
      label
    });
  };

  const handleMouseLeave = () => {
    setCrosshair(null);
  };

  return (
    <div className="w-full relative overflow-hidden select-none">
      {/* Precision Oscilloscope Live Telemetry Ribbon */}
      <div className="absolute top-2 right-3 z-10 flex items-center gap-2 font-mono text-[10px] bg-black/80 px-2.5 py-1 rounded-md border border-white/[0.08] backdrop-blur-md">
        <span className="w-1.5 h-1.5 rounded-full bg-orange-400 animate-pulse" />
        <span className="text-slate-400">OSCILLOSCOPE CH-01:</span>
        <span className="text-white font-bold tracking-wider">
          {crosshair ? crosshair.label : `T24 ACTIVE // ${record.latest_value} µA`}
        </span>
      </div>

      <svg
        ref={svgRef}
        viewBox={`0 0 ${width} ${height}`}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        className="w-full h-auto overflow-visible font-mono cursor-crosshair"
      >
        <defs>
          {/* Subtle grid pattern */}
          <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(255, 255, 255, 0.03)" strokeWidth="1" />
          </pattern>
          {/* Phosphor Beam CRT Glow Filter */}
          <filter id="phosphorGlow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="2.5" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
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
          fontSize="10.5"
          textAnchor="middle"
          fontWeight="600"
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
          fontSize="10"
          fontWeight="600"
        >
          LIMIT ({limit} µA)
        </text>

        {/* Horizontal Axis Ticks */}
        {[0, 24, 48, 72, 96, 120, 144, 168].map(h => (
          <g key={h} transform={`translate(${getX(h)}, ${height - padding.bottom})`}>
            <line y2="5" stroke="rgba(255,255,255,0.12)" />
            <text y="18" fill="#94a3b8" fontSize="10" textAnchor="middle">
              {h}h
            </text>
          </g>
        ))}

        {/* Vertical Axis Ticks */}
        {[0, maxVal * 0.33, maxVal * 0.66, maxVal].map((val, idx) => (
          <g key={idx} transform={`translate(${padding.left}, ${getY(val)})`}>
            <line x2="-5" stroke="rgba(255,255,255,0.12)" />
            <text x="-8" y="3.5" fill="#94a3b8" fontSize="10" textAnchor="end">
              {val.toFixed(2)}
            </text>
          </g>
        ))}

        {/* Phosphor Cathode Glow Underlayer (Design Spell) */}
        <path
          d={earlyPath}
          fill="none"
          stroke="#f97316"
          strokeWidth="6"
          strokeLinecap="round"
          opacity="0.3"
          filter="url(#phosphorGlow)"
        />

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
          filter="url(#phosphorGlow)"
        />
        <text
          x={getX(168) - 10}
          y={getY(predVal) - 10}
          fill="#f97316"
          fontSize="11.5"
          fontWeight="600"
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
              fontSize="11.5"
              fontWeight="600"
            >
              Actual 168h: {record.observed_168h} µA
            </text>
          </>
        )}

        {/* Laser Inspection Crosshairs & Reticle (Design Spell) */}
        {crosshair && (
          <g className="pointer-events-none transition-all duration-75">
            {/* Vertical Hairline */}
            <line
              x1={crosshair.x}
              y1={padding.top}
              x2={crosshair.x}
              y2={height - padding.bottom}
              stroke="#f97316"
              strokeWidth="1"
              strokeDasharray="2 2"
              opacity="0.8"
            />
            {/* Horizontal Hairline */}
            <line
              x1={padding.left}
              y1={crosshair.y}
              x2={width - padding.right}
              y2={crosshair.y}
              stroke="#f97316"
              strokeWidth="1"
              strokeDasharray="2 2"
              opacity="0.8"
            />
            {/* Reticle Target Ring */}
            <circle
              cx={crosshair.x}
              cy={crosshair.y}
              r="6"
              fill="none"
              stroke="#f97316"
              strokeWidth="1.5"
            />
            <circle
              cx={crosshair.x}
              cy={crosshair.y}
              r="2.5"
              fill="#fff"
              stroke="#f97316"
              strokeWidth="1"
            />
          </g>
        )}
      </svg>
    </div>
  );
}
