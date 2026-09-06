import React from 'react';

/**
 * LeakageLensLogo
 * 
 * Monogram logo component featuring the two stylized cascading "L" letterforms (Leakage Lens)
 * calibrated from the official concept SVG specification.
 * 
 * Variants:
 * - 'brand': Radiant obsidian-amber gradient with glowing accents (matches dashboard theme)
 * - 'concept': Exact dark charcoal fill with titanium border from the original design spec
 * - 'glow': Obsidian fill with vibrant electric amber neon stroke and radial backlight
 * - 'duotone': Left L in bright amber, Right L in deep ember/rose
 * - 'white': Clean white / silver metallic finish
 * - 'amber': Solid amber styling
 */
export default function LeakageLensLogo({
  className = '',
  size = 'md',
  variant = 'brand',
  showGlow = false,
  animated = false,
  ...props
}) {
  // Size presets
  const sizeMap = {
    xs: 'w-3.5 h-3.5',
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
    xl: 'w-10 h-10',
    '2xl': 'w-12 h-12',
    '3xl': 'w-16 h-16'
  };

  const dimensionClass = className.includes('w-') || className.includes('h-') 
    ? className 
    : `${sizeMap[size] || sizeMap.md} ${className}`;

  // Unique IDs for SVG gradients to prevent DOM collision across instances
  const idSuffix = React.useId().replace(/:/g, '');
  const gradLeftId = `ll-grad-left-${idSuffix}`;
  const gradRightId = `ll-grad-right-${idSuffix}`;
  const glowFilterId = `ll-glow-${idSuffix}`;

  // Color & styling profiles
  let leftFill = `url(#${gradLeftId})`;
  let leftStroke = '#fb923c';
  let leftStrokeWidth = '3';
  let rightFill = `url(#${gradRightId})`;
  let rightStroke = '#f97316';
  let rightStrokeWidth = '3';

  if (variant === 'concept') {
    leftFill = '#111216';
    leftStroke = '#888894';
    leftStrokeWidth = '3.5';
    rightFill = '#111216';
    rightStroke = '#888894';
    rightStrokeWidth = '3.5';
  } else if (variant === 'glow') {
    leftFill = '#0f111a';
    leftStroke = '#fb923c';
    leftStrokeWidth = '4';
    rightFill = '#0f111a';
    rightStroke = '#f97316';
    rightStrokeWidth = '4';
  } else if (variant === 'duotone') {
    leftFill = '#f97316';
    leftStroke = '#fed7aa';
    leftStrokeWidth = '2';
    rightFill = '#ef4444';
    rightStroke = '#fca5a5';
    rightStrokeWidth = '2';
  } else if (variant === 'white') {
    leftFill = '#ffffff';
    leftStroke = '#cbd5e1';
    leftStrokeWidth = '2';
    rightFill = '#e2e8f0';
    rightStroke = '#94a3b8';
    rightStrokeWidth = '2';
  } else if (variant === 'amber') {
    leftFill = '#f97316';
    leftStroke = '#fb923c';
    leftStrokeWidth = '2';
    rightFill = '#ea580c';
    rightStroke = '#f97316';
    rightStrokeWidth = '2';
  }

  // Left L SVG path
  const leftPath = `
    M 315 590
    L 445 150
    Q 455 115 495 115
    L 620 115
    L 620 118
    Q 570 145 558 190
    L 475 545
    Q 468 575 500 575
    L 570 575
    Q 565 605 525 610
    Z
  `;

  // Right L SVG path
  const rightPath = `
    M 510 670
    L 645 280
    Q 657 245 697 245
    L 835 245
    L 835 248
    Q 785 275 773 320
    L 690 655
    Q 683 690 720 690
    L 950 690
    Q 940 720 900 720
    L 525 720
    Z
  `;

  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="250 35 765 765"
      fill="none"
      className={`shrink-0 transition-transform ${animated ? 'hover:scale-110 duration-200' : ''} ${dimensionClass}`}
      {...props}
    >
      <defs>
        {/* Left L Gradient: Radiant Amber Horizon */}
        <linearGradient id={gradLeftId} x1="315" y1="115" x2="620" y2="610" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#fb923c" />
          <stop offset="60%" stopColor="#f97316" />
          <stop offset="100%" stopColor="#ea580c" />
        </linearGradient>

        {/* Right L Gradient: Deep Ember Resonance */}
        <linearGradient id={gradRightId} x1="510" y1="245" x2="950" y2="720" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#f97316" />
          <stop offset="65%" stopColor="#ea580c" />
          <stop offset="100%" stopColor="#c2410c" />
        </linearGradient>

        {/* Glow filter */}
        <filter id={glowFilterId} x="-20%" y="-20%" width="140%" height="140%">
          <feGaussianBlur stdDeviation="16" result="blur" />
          <feComposite in="SourceGraphic" in2="blur" operator="over" />
        </filter>
      </defs>

      <g filter={showGlow ? `url(#${glowFilterId})` : undefined}>
        {/* Left Monogram L */}
        <path
          d={leftPath}
          fill={leftFill}
          stroke={leftStroke}
          strokeWidth={leftStrokeWidth}
          strokeLinejoin="round"
          strokeLinecap="round"
          className="transition-all duration-200"
        />

        {/* Right Monogram L */}
        <path
          d={rightPath}
          fill={rightFill}
          stroke={rightStroke}
          strokeWidth={rightStrokeWidth}
          strokeLinejoin="round"
          strokeLinecap="round"
          className="transition-all duration-200"
        />
      </g>
    </svg>
  );
}
