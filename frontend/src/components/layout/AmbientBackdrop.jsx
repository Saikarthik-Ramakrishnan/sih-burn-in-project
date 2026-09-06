import React from 'react';

export default function AmbientBackdrop() {
  return (
    <div className="fixed inset-0 pointer-events-none -z-10 overflow-hidden select-none">
      {/* High-Fidelity Radiant Thermal Squircle Background */}
      <img
        src="/assets/squircle-bg.png"
        alt="Radiant Thermal Grid Background"
        className="w-full h-full object-cover object-center fixed inset-0 opacity-85 transition-opacity duration-700"
      />
      {/* Subtle atmospheric tint to maintain perfect contrast and readability */}
      <div className="absolute inset-0 bg-gradient-to-b from-[#0a0b10]/60 via-[#0c0e15]/40 to-[#090a0f]/75 mix-blend-multiply" />
      {/* Subtle edge vignette */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,transparent_30%,rgba(9,10,15,0.65)_100%)]" />
    </div>
  );
}
