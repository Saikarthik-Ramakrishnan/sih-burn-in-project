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

  const padding = 6;
  const x = Math.max(0, targetRect.left - padding);
  const y = Math.max(0, targetRect.top - padding);
  const width = Math.min(windowSize.width - x, targetRect.width + padding * 2);
  const height = Math.min(windowSize.height - y, targetRect.height + padding * 2);
  const radius = 12;

  return (
    <div className="fixed inset-0 z-[70]" aria-hidden="true">
      {/* 4 Shaded quadrants preventing accidental clicks outside the highlighted area */}
      {/* Top quadrant */}
      <div
        style={{ top: 0, left: 0, width: '100%', height: `${y}px` }}
        className="fixed bg-black/70 backdrop-blur-[1.5px]"
        onClick={(e) => e.stopPropagation()}
      />
      {/* Bottom quadrant */}
      <div
        style={{ top: `${y + height}px`, left: 0, width: '100%', bottom: 0 }}
        className="fixed bg-black/70 backdrop-blur-[1.5px]"
        onClick={(e) => e.stopPropagation()}
      />
      {/* Left quadrant */}
      <div
        style={{ top: `${y}px`, left: 0, width: `${x}px`, height: `${height}px` }}
        className="fixed bg-black/70 backdrop-blur-[1.5px]"
        onClick={(e) => e.stopPropagation()}
      />
      {/* Right quadrant */}
      <div
        style={{
          top: `${y}px`,
          left: `${x + width}px`,
          right: 0,
          height: `${height}px`
        }}
        className="fixed bg-black/70 backdrop-blur-[1.5px]"
        onClick={(e) => e.stopPropagation()}
      />

      {/* Target element highlight border and glow (non-blocking) */}
      <div
        style={{
          position: 'fixed',
          left: `${x}px`,
          top: `${y}px`,
          width: `${width}px`,
          height: `${height}px`,
          borderRadius: `${radius}px`,
          pointerEvents: 'none'
        }}
        className={`
          border-2 border-orange-500/60 shadow-[0_0_28px_rgba(249,115,22,0.35)]
          bg-orange-500/[0.04]
          ${prefersReducedMotion ? '' : 'transition-all duration-200 ease-out'}
        `}
      />
    </div>
  );
}
