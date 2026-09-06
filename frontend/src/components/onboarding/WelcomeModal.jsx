import React, { useEffect, useRef } from 'react';
import { BookOpen, ArrowRight, X, ShieldAlert, Layers } from 'lucide-react';
import LeakageLensLogo from '../common/LeakageLensLogo';

export default function WelcomeModal({
  onStart,
  onDismiss,
  onOpenGlossary,
  prefersReducedMotion
}) {
  const modalRef = useRef(null);
  const startButtonRef = useRef(null);

  useEffect(() => {
    startButtonRef.current?.focus();
  }, []);

  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      e.stopPropagation();
      onDismiss();
      return;
    }
    if (e.key === 'Tab') {
      const focusable = modalRef.current?.querySelectorAll(
        'button:not([disabled]), [tabindex]:not([tabindex="-1"])'
      );
      if (!focusable || focusable.length === 0) return;

      const first = focusable[0];
      const last = focusable[focusable.length - 1];

      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    }
  };

  return (
    <div
      className="fixed inset-0 z-[80] flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="welcome-modal-title"
      aria-describedby="welcome-modal-desc"
      onKeyDown={handleKeyDown}
    >
      <div
        ref={modalRef}
        className={`
          w-full max-w-xl p-6 sm:p-7 rounded-2xl bg-[#0e0f17] border border-white/[0.08]
          shadow-[0_24px_64px_rgba(0,0,0,0.8),0_0_32px_rgba(249,115,22,0.12)]
          ${prefersReducedMotion ? '' : 'transition-all duration-300 ease-out'}
        `}
      >
        {/* Header */}
        <div className="flex items-start justify-between pb-4 border-b border-white/[0.06] mb-5">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-orange-500/10 border border-orange-500/20 text-orange-400 flex items-center justify-center shrink-0 shadow-[0_0_12px_rgba(249,115,22,0.15)]">
              <LeakageLensLogo className="w-6 h-6" showGlow />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2
                  id="welcome-modal-title"
                  className="text-base font-semibold tracking-tight text-white"
                >
                  Leakage Lens
                </h2>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-orange-500/15 text-orange-300 border border-orange-500/25">
                  ONBOARDING
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Industrial Component Reliability &amp; Drift Screening
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onDismiss}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 transition-colors cursor-pointer"
            title="Skip onboarding"
            aria-label="Skip onboarding"
          >
            <X className="w-4 h-4" strokeWidth={1.5} />
          </button>
        </div>

        {/* Body Content */}
        <div id="welcome-modal-desc" className="space-y-4 text-xs text-slate-300 leading-relaxed mb-6">
          <div className="p-3.5 rounded-xl bg-white/[0.02] border border-white/[0.04]">
            <span className="text-[11px] font-mono uppercase tracking-wider text-orange-400 font-semibold block mb-1">
              Function &amp; Scope
            </span>
            <p>
              Leakage Lens analyzes 0 h and 24 h leakage readings across every part in a burn-in batch,
              identifies parts drifting differently from their batch peers, forecasts leakage at 168 h with a calibrated
              conformal interval, and assigns one of four screening recommendations per part.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-[11px] font-mono">
            <div className="p-3 rounded-xl bg-white/[0.02] border border-white/[0.04] space-y-1">
              <div className="flex items-center gap-1.5 text-slate-400">
                <Layers className="w-3.5 h-3.5 text-orange-400" strokeWidth={1.5} />
                <span className="text-white font-medium">Input Data</span>
              </div>
              <p className="text-slate-400 text-[10px] leading-normal">
                Long-format CSV with 0 h and 24 h rows. 8 required columns including profile_id.
              </p>
            </div>

            <div className="p-3 rounded-xl bg-white/[0.02] border border-white/[0.04] space-y-1">
              <div className="flex items-center gap-1.5 text-slate-400">
                <ShieldAlert className="w-3.5 h-3.5 text-orange-400" strokeWidth={1.5} />
                <span className="text-white font-medium">Decision Support</span>
              </div>
              <p className="text-slate-400 text-[10px] leading-normal">
                Calibrated on synthetic MLCC data. Use recommendations to guide site retest and inspection procedures.
              </p>
            </div>
          </div>
        </div>

        {/* Action Footer */}
        <div className="flex items-center justify-between pt-4 border-t border-white/[0.06]">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={onOpenGlossary}
              className="flex items-center gap-1.5 text-xs font-mono text-slate-400 hover:text-orange-300 transition-colors cursor-pointer"
            >
              <BookOpen className="w-3.5 h-3.5 text-orange-400" strokeWidth={1.5} />
              <span>Technical Glossary</span>
            </button>
            <span className="text-white/10">•</span>
            <button
              type="button"
              onClick={onDismiss}
              className="text-xs font-mono text-slate-500 hover:text-slate-300 transition-colors cursor-pointer"
            >
              Skip to Dashboard
            </button>
          </div>

          <button
            ref={startButtonRef}
            type="button"
            onClick={onStart}
            className="btn-primary flex items-center gap-2 px-4 py-2 text-xs font-mono tracking-wide"
          >
            <span>Begin Walkthrough</span>
            <ArrowRight className="w-3.5 h-3.5" strokeWidth={1.5} />
          </button>
        </div>
      </div>
    </div>
  );
}
