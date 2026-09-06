import React from 'react';

export default function SquircleCard({
  children,
  className = '',
  elevated = false,
  highlight = false,
  onClick,
  ...props
}) {
  return (
    <div
      onClick={onClick}
      className={`
        relative rounded-2xl transition-all duration-200 backdrop-blur-xl
        ${
          elevated
            ? 'bg-[#121420]/85 border border-white/[0.12] shadow-[0_10px_30px_rgba(0,0,0,0.5)]'
            : 'bg-[#0d0f18]/75 border border-white/[0.08] shadow-[0_4px_20px_rgba(0,0,0,0.4)]'
        }
        ${highlight ? 'border-orange-500/35 bg-[#141724]/90 shadow-[0_0_20px_rgba(249,115,22,0.1)]' : 'hover:border-white/[0.16]'}
        ${onClick ? 'cursor-pointer active:scale-[0.995]' : ''}
        ${className}
      `}
      {...props}
    >
      {children}
    </div>
  );
}
