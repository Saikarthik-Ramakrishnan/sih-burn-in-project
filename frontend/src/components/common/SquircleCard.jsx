import React, { useRef, useState } from 'react';
import { playMechanicalClick } from '../../lib/audioEffects';

export default function SquircleCard({
  children,
  className = '',
  elevated = false,
  highlight = false,
  fiducials = false,
  spotlight = true,
  onClick,
  ...props
}) {
  const cardRef = useRef(null);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0, opacity: 0 });

  const handleMouseMove = (e) => {
    if (!spotlight || !cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    setMousePos({
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
      opacity: 1
    });
  };

  const handleMouseLeave = () => {
    setMousePos((prev) => ({ ...prev, opacity: 0 }));
  };

  const handleClick = (e) => {
    if (onClick) {
      playMechanicalClick();
      onClick(e);
    }
  };

  return (
    <div
      ref={cardRef}
      onClick={handleClick}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      className={`
        relative rounded-xl transition-all duration-200 backdrop-blur-md overflow-hidden group
        ${
          elevated
            ? 'bg-[#0c0e17]/75 border border-white/[0.09] shadow-[0_4px_24px_rgba(0,0,0,0.4)]'
            : 'bg-[#080a10]/60 border border-white/[0.06] hover:border-white/[0.12]'
        }
        ${highlight ? 'border-orange-500/40 bg-[#0e101c]/80 shadow-[0_0_20px_rgba(249,115,22,0.1)]' : ''}
        ${onClick ? 'cursor-pointer active:scale-[0.992]' : ''}
        ${className}
      `}
      {...props}
    >
      {/* 1. Dynamic Cursor Spotlight (Design Spell) */}
      {spotlight && (
        <div
          className="pointer-events-none absolute inset-0 transition-opacity duration-300 z-0"
          style={{
            opacity: mousePos.opacity,
            background: `radial-gradient(400px circle at ${mousePos.x}px ${mousePos.y}px, rgba(249, 115, 22, 0.06), transparent 75%)`
          }}
        />
      )}

      {/* 2. Authentic Corner Laser Alignment Fiducials (Semiconductor Test Fixture Marks) */}
      {(fiducials || elevated) && (
        <>
          <span className="pointer-events-none absolute top-1.5 left-1.5 text-[8px] font-mono text-white/20 select-none leading-none z-10">
            +
          </span>
          <span className="pointer-events-none absolute top-1.5 right-1.5 text-[8px] font-mono text-white/20 select-none leading-none z-10">
            +
          </span>
          <span className="pointer-events-none absolute bottom-1.5 left-1.5 text-[8px] font-mono text-white/20 select-none leading-none z-10">
            +
          </span>
          <span className="pointer-events-none absolute bottom-1.5 right-1.5 text-[8px] font-mono text-white/20 select-none leading-none z-10">
            +
          </span>
        </>
      )}

      {/* 3. Card Content */}
      <div className="relative z-10">
        {children}
      </div>
    </div>
  );
}
