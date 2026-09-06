import React, { useEffect, useRef, useState } from 'react';
import { ChevronRight, ChevronLeft, X, BookOpen, ArrowRight, Loader2 } from 'lucide-react';

export default function CalloutCard({
  stepNumber,
  totalSteps,
  heading,
  sentence1,
  sentence2,
  actionLabel,
  onAction,
  onPrev,
  onDismiss,
  onOpenGlossary,
  targetRect,
  isLoading = false,
  prefersReducedMotion = false
}) {
  const cardRef = useRef(null);
  const actionButtonRef = useRef(null);
  const [position, setPosition] = useState({ top: 120, left: 120 });

  // Autofocus the primary action button for keyboard accessibility
  useEffect(() => {
    const timer = setTimeout(() => {
      actionButtonRef.current?.focus();
    }, 50);
    return () => clearTimeout(timer);
  }, [stepNumber]);

  // Compute anchored placement relative to the target element
  useEffect(() => {
    if (!targetRect || !cardRef.current) return;

    const cardWidth = 440;
    const cardHeight = cardRef.current.offsetHeight || 220;
    const padding = 16;
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;

    let top = targetRect.bottom + padding;
    let left = targetRect.left;

    // If bottom doesn't have enough space, position above target
    if (top + cardHeight > viewportHeight - padding) {
      top = targetRect.top - cardHeight - padding;
    }

    // Strict clamping vertically within viewport
    top = Math.max(padding, Math.min(viewportHeight - cardHeight - padding, top));

    // Clamp horizontally within viewport
    if (left + cardWidth > viewportWidth - padding) {
      left = viewportWidth - cardWidth - padding;
    }
    if (left < padding) {
      left = padding;
    }

    setPosition({ top, left });
  }, [targetRect, stepNumber]);

  // Trap focus and keyboard shortcuts within the card
  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      e.stopPropagation();
      onDismiss();
      return;
    }

    // Keyboard navigation: Enter or ArrowRight advances, ArrowLeft goes back
    if (e.key === 'ArrowRight') {
      if (!isLoading) {
        e.preventDefault();
        onAction();
      }
      return;
    }

    if (e.key === 'ArrowLeft' && onPrev && stepNumber > 1) {
      if (!isLoading) {
        e.preventDefault();
        onPrev();
      }
      return;
    }

    if (e.key === 'Tab') {
      const focusable = cardRef.current?.querySelectorAll(
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
      ref={cardRef}
      role="dialog"
      aria-modal="true"
      aria-labelledby="callout-heading"
      aria-describedby="callout-description"
      onKeyDown={handleKeyDown}
      tabIndex={-1}
      style={{
        position: 'fixed',
        top: `${position.top}px`,
        left: `${position.left}px`,
        width: '440px'
      }}
      className={`
        z-[80] p-5 rounded-2xl bg-[#0e0f17] border border-orange-500/30
        shadow-[0_16px_48px_rgba(0,0,0,0.7),0_0_24px_rgba(249,115,22,0.15)]
        outline-none
        ${prefersReducedMotion ? '' : 'transition-all duration-300 ease-out'}
      `}
    >
      {/* Top Header: Step Counter & Dismiss */}
      <div className="flex items-center justify-between pb-3 border-b border-white/[0.06] mb-3">
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-orange-500/15 text-orange-300 border border-orange-500/30 font-semibold tracking-wide">
            STEP {stepNumber} OF {totalSteps}
          </span>
          <button
            type="button"
            onClick={onOpenGlossary}
            className="flex items-center gap-1 text-[11px] font-mono text-slate-400 hover:text-orange-300 transition-colors cursor-pointer ml-1"
            title="View technical definitions and API field rules"
          >
            <BookOpen className="w-3.5 h-3.5 text-orange-400" strokeWidth={1.5} />
            <span>Glossary</span>
          </button>
        </div>

        <button
          type="button"
          onClick={onDismiss}
          className="p-1 rounded-md text-slate-400 hover:text-white hover:bg-white/10 transition-colors cursor-pointer"
          title="Exit walkthrough (reopen anytime from sidebar)"
          aria-label="Exit walkthrough"
        >
          <X className="w-4 h-4" strokeWidth={1.5} />
        </button>
      </div>

      {/* Exactly One Heading */}
      <h3
        id="callout-heading"
        className="text-sm font-semibold tracking-tight text-white mb-2"
      >
        {heading}
      </h3>

      {/* At Most Two Sentences */}
      <div id="callout-description" className="text-xs text-slate-300 leading-relaxed space-y-1 mb-5">
        <p>{sentence1}</p>
        {sentence2 && <p className="text-slate-400">{sentence2}</p>}
      </div>

      {/* Action Bar: Exactly One Action Button + Nav Controls */}
      <div className="flex items-center justify-between pt-3 border-t border-white/[0.06]">
        <div>
          {onPrev && stepNumber > 1 && (
            <button
              type="button"
              onClick={onPrev}
              disabled={isLoading}
              className="flex items-center gap-1 text-xs font-mono text-slate-400 hover:text-slate-200 transition-colors cursor-pointer px-2 py-1 rounded hover:bg-white/5 disabled:opacity-40"
            >
              <ChevronLeft className="w-3.5 h-3.5" strokeWidth={1.5} />
              <span>Back</span>
            </button>
          )}
        </div>

        {/* Exactly One Primary Action */}
        <button
          ref={actionButtonRef}
          type="button"
          onClick={onAction}
          disabled={isLoading}
          className="btn-primary flex items-center gap-1.5 px-4 py-2 text-xs font-mono tracking-wide shadow-md disabled:opacity-60"
        >
          {isLoading ? (
            <>
              <Loader2 className="w-3.5 h-3.5 animate-spin" strokeWidth={1.5} />
              <span>Processing Sample...</span>
            </>
          ) : (
            <>
              <span>{actionLabel}</span>
              <ArrowRight className="w-3.5 h-3.5" strokeWidth={1.5} />
            </>
          )}
        </button>
      </div>
    </div>
  );
}
