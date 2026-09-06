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
        relative rounded-xl transition-all duration-150 backdrop-blur-md
        ${
          elevated
            ? 'bg-[#0d0f18]/65 border border-white/[0.08]'
            : 'bg-[#090b12]/55 border border-white/[0.05]'
        }
        ${highlight ? 'border-orange-500/30 bg-[#0e101b]/70' : 'hover:border-white/[0.12]'}
        ${onClick ? 'cursor-pointer active:scale-[0.995]' : ''}
        ${className}
      `}
      {...props}
    >
      {children}
    </div>
  );
}
