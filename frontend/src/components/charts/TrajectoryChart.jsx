import React, { useState, useMemo, useRef } from 'react';

export default function TrajectoryChart({
  record,
  showOutcome = false,
  height = 280
}) {
  if (!record) return null;

  const [hoverPoint, setHoverPoint] = useState(null);
  const [cursorPos, setCursorPos] = useState(null);
  const svgRef = useRef(null);

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

  // Collect all milestone points with threshold-relative color coordinates
  const points = useMemo(() => {
    const pts = [];

    // 1. Initial Baseline Point
    if (earlyTraj.length > 0) {
      const p0 = earlyTraj[0];
      pts.push({
        id: 'pt-0h',
        hour: p0.hour,
        value: p0.value,
        title: '0.0h Baseline Reading',
        stage: 'Initial Burn-In Checkpoint',
        kind: 'baseline'
      });
    }

    // 2. Cutoff Reading Point
    if (earlyTraj.length > 1) {
      const p24 = earlyTraj[1];
      pts.push({
        id: 'pt-24h',
        hour: p24.hour,
        value: p24.value,
        title: '24.0h Cutoff Reading',
        stage: 'Decision Screening Checkpoint',
        kind: 'cutoff'
      });
    }

    // 3. Interim checkpoints (if outcome shown)
    if (showOutcome && outcomeTraj.length > 0) {
      outcomeTraj.forEach(p => {
        if (p.hour !== 168) {
          pts.push({
            id: `pt-${p.hour}h`,
            hour: p.hour,
            value: p.value,
            title: `${p.hour}.0h Intermediate Telemetry`,
            stage: 'Interim Observation',
            kind: 'interim'
          });
        }
      });
    }

    // 4. 168h Forecast Point
    pts.push({
      id: 'pt-168h-forecast',
      hour: 168,
      value: predVal,
      lower: predLower,
      upper: predUpper,
      title: '168.0h Predicted Forecast',
      stage: 'XGBoost v2 Conformal Horizon',
      kind: 'forecast',
      nominalCoverage: forecast.interval_nominal_coverage || 0.9
    });

    // 5. Observed 168h Outcome (if revealed)
    if (showOutcome && record.observed_168h !== undefined) {
      pts.push({
        id: 'pt-168h-actual',
        hour: 168,
        value: record.observed_168h,
        title: '168.0h Observed Outcome',
        stage: 'Measured Verification',
        kind: 'actual'
      });
    }

    return pts.map(pt => {
      const x = getX(pt.hour);
      const y = getY(pt.value);
      const fraction = limit > 0 ? (pt.value / limit) : 0;
      const headroom = limit - pt.value;

      // Color coordination with respect to threshold limit value
      let color, border, glow, statusLabel, statusBadge;
      if (pt.value >= limit) {
        // Limit breach -> ERROR -> RED
        color = '#ef4444'; // glowing crimson red
        border = '#f87171';
        glow = 'rgba(239, 68, 68, 0.45)';
        statusLabel = 'THRESHOLD BREACH // ERROR';
        statusBadge = 'bg-rose-500/20 text-rose-300 border-rose-500/40 font-bold';
      } else if (fraction >= 0.7) {
        // Approaching threshold limit -> CAUTION -> AMBER
        color = '#f59e0b'; // warm amber
        border = '#fbbf24';
        glow = 'rgba(245, 158, 11, 0.35)';
        statusLabel = 'ELEVATED // NEAR LIMIT';
        statusBadge = 'bg-amber-500/15 text-amber-300 border-amber-500/30';
      } else {
        // Safe nominal -> GOING GOOD -> GREEN
        color = '#10b981'; // vibrant emerald green
        border = '#34d399';
        glow = 'rgba(16, 185, 129, 0.35)';
        statusLabel = 'NOMINAL // GOING GOOD';
        statusBadge = 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30 font-semibold';
      }

      return {
        ...pt,
        x,
        y,
        fraction,
        headroom,
        color,
        border,
        glow,
        statusLabel,
        statusBadge
      };
    });
  }, [earlyTraj, outcomeTraj, showOutcome, predVal, predLower, predUpper, record.observed_168h, limit, maxVal, minVal]);

  // Handle interactive mouse proximity
  const handleMouseMove = (e) => {
    if (!svgRef.current) return;
    const rect = svgRef.current.getBoundingClientRect();
    const mouseX = ((e.clientX - rect.left) / rect.width) * width;
    const mouseY = ((e.clientY - rect.top) / rect.height) * height;

    if (
      mouseX < padding.left - 10 ||
      mouseX > width - padding.right + 10 ||
      mouseY < padding.top - 15 ||
      mouseY > height - padding.bottom + 15
    ) {
      setHoverPoint(null);
      setCursorPos(null);
      return;
    }

    setCursorPos({ x: mouseX, y: mouseY });

    // Snap to nearest data point within 45px
    let nearest = null;
    let minDist = 45;

    points.forEach(pt => {
      const dist = Math.hypot(pt.x - mouseX, pt.y - mouseY);
      if (dist < minDist) {
        minDist = dist;
        nearest = pt;
      }
    });

    setHoverPoint(nearest);
  };

  const handleMouseLeave = () => {
    setHoverPoint(null);
    setCursorPos(null);
  };

  return (
    <div className="w-full relative overflow-hidden select-none">
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
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(255, 255, 255, 0.04)" strokeWidth="1" />
          </pattern>

          {/* Forecast uncertainty gradient */}
          <linearGradient id="forecastGlow" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#f97316" stopOpacity="0.3" />
            <stop offset="100%" stopColor="#f97316" stopOpacity="0.05" />
          </linearGradient>

          {/* Soft blur filter */}
          <filter id="pointGlow" x="-30%" y="-30%" width="160%" height="160%">
            <feGaussianBlur stdDeviation="2.5" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
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

        {/* Specification Upper Limit Line (Red Error Threshold) */}
        <line
          x1={padding.left}
          y1={getY(limit)}
          x2={width - padding.right}
          y2={getY(limit)}
          stroke="#ef4444"
          strokeWidth="1.5"
          strokeDasharray="4 4"
          strokeOpacity="0.85"
        />
        <text
          x={width - padding.right + 5}
          y={getY(limit) + 3.5}
          fill="#ef4444"
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

        {/* Early Observed Trajectory (0 to 24h) */}
        <path
          d={earlyPath}
          fill="none"
          stroke="#f8fafc"
          strokeWidth="2.5"
          strokeLinecap="round"
        />

        {/* 168h Forecast Uncertainty Whisker Band (Red if error/crosses, Green if good, Amber if elevated) */}
        {(() => {
          const isCross = predVal >= limit;
          const isElev = !isCross && (predVal >= limit * 0.7);
          const fColor = isCross ? '#ef4444' : (isElev ? '#f59e0b' : '#10b981');
          return (
            <g>
              <line
                x1={getX(168)}
                y1={getY(predLower)}
                x2={getX(168)}
                y2={getY(predUpper)}
                stroke={fColor}
                strokeWidth="2"
              />
              <line
                x1={getX(168) - 5}
                y1={getY(predLower)}
                x2={getX(168) + 5}
                y2={getY(predLower)}
                stroke={fColor}
                strokeWidth="2"
              />
              <line
                x1={getX(168) - 5}
                y1={getY(predUpper)}
                x2={getX(168) + 5}
                y2={getY(predUpper)}
                stroke={fColor}
                strokeWidth="2"
              />

              {/* Static Forecast Point Text */}
              {!hoverPoint && (
                <text
                  x={getX(168) - 10}
                  y={getY(predVal) - 10}
                  fill={fColor}
                  fontSize="11.5"
                  fontWeight="600"
                  textAnchor="end"
                >
                  Forecast: {predVal.toFixed(3)} µA
                </text>
              )}
            </g>
          );
        })()}

        {/* Outcome Reveal Overlay Path (if enabled) */}
        {showOutcome && outcomeTraj.length > 0 && (
          <path
            d={outcomePath}
            fill="none"
            stroke="#94a3b8"
            strokeWidth="2"
            strokeDasharray="3 3"
            strokeLinecap="round"
          />
        )}

        {/* Render Milestone Nodes (Base circles) */}
        {points.map(pt => {
          const isHovered = hoverPoint?.id === pt.id;

          return (
            <g key={pt.id} className="transition-transform duration-150">
              {/* Outer halo when hovered */}
              {isHovered && (
                <circle
                  cx={pt.x}
                  cy={pt.y}
                  r="12"
                  fill="none"
                  stroke={pt.color}
                  strokeWidth="1.5"
                  strokeDasharray="3 3"
                  className="animate-spin"
                  style={{ animationDuration: '4s' }}
                />
              )}

              {/* Core Node circle */}
              <circle
                cx={pt.x}
                cy={pt.y}
                r={isHovered ? 6 : (pt.kind === 'forecast' ? 5.5 : 4)}
                fill={pt.color}
                stroke="#ffffff"
                strokeWidth={isHovered ? 2 : 1.5}
                filter="url(#pointGlow)"
              />
            </g>
          );
        })}

        {/* Static Actual Label when outcome revealed and not hovered */}
        {showOutcome && !hoverPoint && record.observed_168h !== undefined && (
          <text
            x={getX(168) + 10}
            y={getY(record.observed_168h) + 4}
            fill="#cbd5e1"
            fontSize="11.5"
            fontWeight="600"
          >
            Actual 168h: {record.observed_168h} µA
          </text>
        )}

        {/* ========================================================= */}
        {/* INTERACTIVE CROSSHAIR & COORDINATE HUD OVERLAY           */}
        {/* ========================================================= */}
        {hoverPoint && (
          <g className="interactive-hud pointer-events-none">
            {/* Vertical Coordinate Hairline */}
            <line
              x1={hoverPoint.x}
              y1={padding.top}
              x2={hoverPoint.x}
              y2={height - padding.bottom}
              stroke={hoverPoint.color}
              strokeWidth="1.2"
              strokeDasharray="3 3"
              strokeOpacity="0.8"
            />

            {/* Horizontal Coordinate Hairline */}
            <line
              x1={padding.left}
              y1={hoverPoint.y}
              x2={width - padding.right}
              y2={hoverPoint.y}
              stroke={hoverPoint.color}
              strokeWidth="1.2"
              strokeDasharray="3 3"
              strokeOpacity="0.8"
            />

            {/* X-Axis Highlight Pill */}
            <g transform={`translate(${hoverPoint.x}, ${height - padding.bottom + 1})`}>
              <rect
                x="-24"
                y="0"
                width="48"
                height="16"
                rx="4"
                fill="#0f111a"
                stroke={hoverPoint.color}
                strokeWidth="1"
              />
              <text
                x="0"
                y="11"
                fill="#ffffff"
                fontSize="10"
                fontWeight="600"
                textAnchor="middle"
              >
                {hoverPoint.hour.toFixed(1)}h
              </text>
            </g>

            {/* Y-Axis Highlight Pill */}
            <g transform={`translate(${padding.left - 50}, ${hoverPoint.y - 8})`}>
              <rect
                x="0"
                y="0"
                width="46"
                height="16"
                rx="4"
                fill="#0f111a"
                stroke={hoverPoint.color}
                strokeWidth="1"
              />
              <text
                x="23"
                y="11"
                fill={hoverPoint.color}
                fontSize="9.5"
                fontWeight="600"
                textAnchor="middle"
              >
                {hoverPoint.value.toFixed(3)}
              </text>
            </g>

            {/* Floating Coordinate & Threshold HUD Box */}
            {(() => {
              // Smart positioning so HUD never overflows SVG bounds
              const tooltipW = 195;
              const tooltipH = hoverPoint.kind === 'forecast' ? 82 : 70;
              const boxX = hoverPoint.x > width - 210 ? hoverPoint.x - tooltipW - 14 : hoverPoint.x + 14;
              const boxY = hoverPoint.y < 85 ? hoverPoint.y + 12 : hoverPoint.y - tooltipH - 10;

              return (
                <g transform={`translate(${boxX}, ${boxY})`}>
                  {/* Tooltip Background Card */}
                  <rect
                    x="0"
                    y="0"
                    width={tooltipW}
                    height={tooltipH}
                    rx="8"
                    fill="#0a0c14"
                    fillOpacity="0.95"
                    stroke={hoverPoint.border}
                    strokeWidth="1.2"
                    filter="url(#pointGlow)"
                  />

                  {/* Top Bar Indicator in Threshold Color */}
                  <rect
                    x="0"
                    y="0"
                    width={tooltipW}
                    height="3"
                    rx="1.5"
                    fill={hoverPoint.color}
                  />

                  {/* Title & Stage */}
                  <text
                    x="10"
                    y="17"
                    fill="#ffffff"
                    fontSize="10.5"
                    fontWeight="600"
                  >
                    {hoverPoint.title}
                  </text>

                  {/* Coordinates: Time & Value */}
                  <text
                    x="10"
                    y="32"
                    fill="#cbd5e1"
                    fontSize="10"
                  >
                    Time: <tspan fill="#ffffff" fontWeight="600">{hoverPoint.hour.toFixed(1)} h</tspan> • Val: <tspan fill={hoverPoint.color} fontWeight="600">{hoverPoint.value.toFixed(4)} µA</tspan>
                  </text>

                  {/* Threshold Status & Relationship */}
                  <text
                    x="10"
                    y="47"
                    fill={hoverPoint.color}
                    fontSize="9.5"
                    fontWeight="600"
                  >
                    {hoverPoint.statusLabel} ({((hoverPoint.fraction) * 100).toFixed(1)}% of Spec)
                  </text>

                  {/* Headroom / Interval line */}
                  <text
                    x="10"
                    y="60"
                    fill="#94a3b8"
                    fontSize="9"
                  >
                    {hoverPoint.value >= limit
                      ? `Spec breach by ${(hoverPoint.value - limit).toFixed(4)} µA`
                      : `Headroom: +${hoverPoint.headroom.toFixed(4)} µA to 0.25 µA limit`}
                  </text>

                  {hoverPoint.kind === 'forecast' && (
                    <text
                      x="10"
                      y="73"
                      fill="#f59e0b"
                      fontSize="8.5"
                    >
                      90% Interval: [{hoverPoint.lower.toFixed(3)} - {hoverPoint.upper.toFixed(3)}] µA
                    </text>
                  )}
                </g>
              );
            })()}
          </g>
        )}
      </svg>
    </div>
  );
}
