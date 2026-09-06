import React, { useEffect, useState, useCallback } from 'react';

export default function SpotlightOverlay({ targetRect, isVisible, prefersReducedMotion }) {
  const [windowSize, setWindowSize] = useState({
    width: typeof window !== 'undefined' ? window.innerWidth : 1280,
    height: typeof window !== 'undefined' ? window.innerHeight : 800
  });

  const handleResize = useCallback(() => {
    setWindowSize({
      width: window.innerWidth,
      height: window.innerHeight
    });
  }, []);

  useEffect(() => {
    window.addEventListener('resize', handleResize);
    window.addEventListener('scroll', handleResize, true);
    return () => {
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('scroll', handleResize, true);
    };
  }, [handleResize]);

  if (!isVisible || !targetRect) return null;

  const padding = 8;
  const x = Math.max(0, targetRect.left - padding);
  const y = Math.max(0, targetRect.top - padding);
  const width = Math.min(windowSize.width - x, targetRect.width + padding * 2);
  const height = Math.min(windowSize.height - y, targetRect.height + padding * 2);
  const radius = 12;

  return (
    <div
      className="fixed inset-0 z-[70] pointer-events-none"
      aria-hidden="true"
    >
      <svg
        className={`w-full h-full ${prefersReducedMotion ? '' : 'transition-opacity duration-300'}`}
        viewBox={`0 0 ${windowSize.width} ${windowSize.height}`}
      >
        <defs>
          <mask id="spotlight-mask">
            {/* White background covers everything */}
            <rect x="0" y="0" width={windowSize.width} height={windowSize.height} fill="#fff" />
            {/* Black cutout reveals the target element */}
            <rect
              x={x}
              y={y}
              width={width}
              height={height}
              rx={radius}
              ry={radius}
              fill="#000"
            />
          </mask>
        </defs>

        {/* Shaded backdrop with cutout mask */}
        <rect
          x="0"
          y="0"
          width={windowSize.width}
          height={windowSize.height}
          fill="rgba(5, 6, 10, 0.72)"
          mask="url(#spotlight-mask)"
        />
      </svg>

      {/* Target element highlight border */}
      <div
        style={{
          position: 'absolute',
          left: `${x}px`,
          top: `${y}px`,
          width: `${width}px`,
          height: `${height}px`,
          borderRadius: `${radius}px`
        }}
        className={`
          border-2 border-orange-500/60 shadow-[0_0_24px_rgba(249,115,22,0.3)]
          bg-orange-500/[0.03]
          ${prefersReducedMotion ? '' : 'transition-all duration-300 ease-out'}
        `}
      />
    </div>
  );
}
