import React, { useState, useEffect, useCallback, useRef } from 'react';
import WelcomeModal from './WelcomeModal';
import CalloutCard from './CalloutCard';
import SpotlightOverlay from './SpotlightOverlay';
import GlossaryDrawer from './GlossaryDrawer';

const STORAGE_KEY = 'burn_in_sentinel_onboarding_dismissed';

export default function OnboardingFlow({
  activeTab,
  setActiveTab,
  onReloadDemo,
  onOpenUpload,
  dataset,
  backendReady
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [currentStep, setCurrentStep] = useState(0); // 0 = welcome, 1-5 = spotlight steps
  const [isGlossaryOpen, setIsGlossaryOpen] = useState(false);
  const [targetRect, setTargetRect] = useState(null);
  const [isLoadingSample, setIsLoadingSample] = useState(false);
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);

  // Check reduced motion preference
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
      setPrefersReducedMotion(mq.matches);
      const listener = (e) => setPrefersReducedMotion(e.matches);
      mq.addEventListener('change', listener);
      return () => mq.removeEventListener('change', listener);
    }
  }, []);

  // First-run automatic detection (1280px+ and not previously dismissed)
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const isDismissed = localStorage.getItem(STORAGE_KEY) === 'true';
      if (!isDismissed && window.innerWidth >= 1280) {
        setIsOpen(true);
        setCurrentStep(0);
      }
    }
  }, []);

  // Listen to custom global events from Sidebar / Navigation
  useEffect(() => {
    const handleOpenOnboarding = () => {
      setActiveTab('overview');
      setIsOpen(true);
      setCurrentStep(0);
    };

    const handleOpenGlossary = () => {
      setIsGlossaryOpen(true);
    };

    window.addEventListener('open-onboarding', handleOpenOnboarding);
    window.addEventListener('open-glossary', handleOpenGlossary);

    return () => {
      window.removeEventListener('open-onboarding', handleOpenOnboarding);
      window.removeEventListener('open-glossary', handleOpenGlossary);
    };
  }, [setActiveTab]);

  // Ensure active tab matches current step
  useEffect(() => {
    if (!isOpen) return;

    if (currentStep >= 1 && currentStep <= 4) {
      if (activeTab !== 'overview') {
        setActiveTab('overview');
      }
    } else if (currentStep === 5) {
      if (activeTab !== 'inspector') {
        setActiveTab('inspector');
      }
    }
  }, [isOpen, currentStep, activeTab, setActiveTab]);

  // Persist dismissal
  const handleDismiss = useCallback(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem(STORAGE_KEY, 'true');
    }
    setIsOpen(false);
    setTargetRect(null);
  }, []);

  // Helper to find DOM target for a step
  const findTargetElement = useCallback((step) => {
    if (step === 1) {
      // Step 1: Upload CSV button in Header or Sidebar
      return (
        document.querySelector('header button.btn-primary') ||
        Array.from(document.querySelectorAll('button')).find((b) =>
          b.textContent.includes('Upload CSV')
        )
      );
    }
    if (step === 2) {
      // Step 2: Sample Data button in Header
      return (
        document.querySelector('header button[title*="sample" i]') ||
        Array.from(document.querySelectorAll('button')).find((b) =>
          b.textContent.includes('Sample Data')
        )
      );
    }
    if (step === 3) {
      // Step 3: Decision Cards container on Overview
      return (
        document.querySelector('.grid.grid-cols-1.sm\\:grid-cols-2.lg\\:grid-cols-4') ||
        Array.from(document.querySelectorAll('span'))
          .find((s) => s.textContent.trim().startsWith('ACCEPT'))
          ?.closest('.squircle-card')?.parentElement
      );
    }
    if (step === 4) {
      // Step 4: Within Limits But Unusual card on Overview
      return Array.from(document.querySelectorAll('h3'))
        .find((h) => h.textContent.includes('Within Limits, Still Unusual'))
        ?.closest('.squircle-card');
    }
    if (step === 5) {
      // Step 5: Trajectory & Forecast Card on Inspector
      return (
        Array.from(document.querySelectorAll('h3'))
          .find((h) => h.textContent.includes('Burn-In Trajectory'))
          ?.closest('.squircle-card') ||
        document.querySelector('main .squircle-card')
      );
    }
    return null;
  }, []);

  // Measure target bounding rect without triggering scroll
  const measureTarget = useCallback(() => {
    if (!isOpen || currentStep === 0) {
      setTargetRect(null);
      return;
    }
    const el = findTargetElement(currentStep);
    if (el) {
      setTargetRect(el.getBoundingClientRect());
    } else {
      setTargetRect(null);
    }
  }, [isOpen, currentStep, findTargetElement]);

  // Scroll into view once when step transitions, with retries for mounted components
  useEffect(() => {
    if (!isOpen || currentStep === 0) {
      setTargetRect(null);
      return;
    }

    let attempts = 0;
    const maxAttempts = 5;

    const locateAndScroll = () => {
      const el = findTargetElement(currentStep);
      if (el) {
        el.scrollIntoView({
          behavior: prefersReducedMotion ? 'auto' : 'smooth',
          block: 'center'
        });
        // Measure after scroll animation settles
        setTimeout(() => {
          setTargetRect(el.getBoundingClientRect());
        }, prefersReducedMotion ? 20 : 180);
      } else if (attempts < maxAttempts) {
        attempts += 1;
        setTimeout(locateAndScroll, 80);
      }
    };

    locateAndScroll();
  }, [isOpen, currentStep, findTargetElement, prefersReducedMotion]);

  // Attach measure listener for user scroll or window resize
  useEffect(() => {
    if (!isOpen || currentStep === 0) return;

    window.addEventListener('resize', measureTarget);
    window.addEventListener('scroll', measureTarget, true);

    return () => {
      window.removeEventListener('resize', measureTarget);
      window.removeEventListener('scroll', measureTarget, true);
    };
  }, [isOpen, currentStep, measureTarget]);

  // Step definitions: strictly ONE heading, AT MOST TWO sentences, ONE action
  const steps = [
    null, // Step 0 is WelcomeModal
    {
      stepNumber: 1,
      heading: 'Input Data Format',
      sentence1:
        'Upload a long-format CSV with required columns component_id, batch_id, component_family, hours, measurement_name, measurement_value, upper_limit, and profile_id.',
      sentence2:
        'Exactly one 0 h and one 24 h row are required per part, while later checkpoint hours are reserved for optional outcome verification.',
      actionLabel: 'Next: Sample Data',
      onAction: () => {
        setCurrentStep(2);
      }
    },
    {
      stepNumber: 2,
      heading: 'Verified Sample Demonstration',
      sentence1:
        'Load the verified 64-component MLCC demonstration dataset to evaluate live inference and peer statistics within the first minute.',
      sentence2:
        'Selecting this action executes the sample screening pipeline directly through the backend model service.',
      actionLabel: 'Run Sample Screening',
      onAction: async () => {
        if (onReloadDemo) {
          try {
            setIsLoadingSample(true);
            await onReloadDemo();
          } catch (err) {
            console.warn('Sample reload encounter:', err);
          } finally {
            setIsLoadingSample(false);
          }
        }
        setActiveTab('overview');
        setCurrentStep(3);
      }
    },
    {
      stepNumber: 3,
      heading: 'Screening Recommendations',
      sentence1:
        'ENGINEER_REVIEW indicates an anomalous part forecast to cross its limit, RETEST flags a strong peer anomaly or forecast crossing, MONITOR indicates the interval upper bound reaches the limit, and ACCEPT meets nominal criteria.',
      sentence2:
        'Unscored records were excluded from screening and must never be interpreted as passed components.',
      actionLabel: 'Next: Drift Detection',
      onAction: () => {
        setCurrentStep(4);
      }
    },
    {
      stepNumber: 4,
      heading: 'Within Limit, Still Unusual',
      sentence1:
        'A component can remain safely within spec limits while drifting anomalously compared to other components in the same burn-in batch.',
      sentence2:
        'The anomaly score ranks deviation against batch peers rather than estimating failure probability, and batches with fewer than 8 parts provide weaker statistical comparisons.',
      actionLabel: 'Next: Telemetry Inspector',
      onAction: () => {
        setActiveTab('inspector');
        setCurrentStep(5);
      }
    },
    {
      stepNumber: 5,
      heading: 'Telemetry Inspector & Decision Support',
      sentence1:
        'Inspect individual component trajectories alongside nominal 80 % forecast intervals (with a one-sided 90 % upper bound) and TreeSHAP feature attributions.',
      sentence2:
        'All screening recommendations are intended for decision support to guide engineering retest, physical inspection, or lot disposition.',
      actionLabel: 'Complete Walkthrough',
      onAction: () => {
        handleDismiss();
        setActiveTab('overview');
      }
    }
  ];

  if (!isOpen && !isGlossaryOpen) return null;

  const currentStepData = steps[currentStep];

  return (
    <>
      {/* 1. Technical Glossary Drawer */}
      <GlossaryDrawer
        isOpen={isGlossaryOpen}
        onClose={() => setIsGlossaryOpen(false)}
        prefersReducedMotion={prefersReducedMotion}
      />

      {/* 2. Step 0: Welcome Modal */}
      {isOpen && currentStep === 0 && (
        <WelcomeModal
          onStart={() => setCurrentStep(1)}
          onDismiss={handleDismiss}
          onOpenGlossary={() => setIsGlossaryOpen(true)}
          prefersReducedMotion={prefersReducedMotion}
        />
      )}

      {/* 3. Steps 1-5: Spotlight Overlay & Anchored Callout Card */}
      {isOpen && currentStep >= 1 && currentStepData && (
        <>
          <SpotlightOverlay
            targetRect={targetRect}
            isVisible={isOpen}
            prefersReducedMotion={prefersReducedMotion}
          />
          <CalloutCard
            stepNumber={currentStepData.stepNumber}
            totalSteps={5}
            heading={currentStepData.heading}
            sentence1={currentStepData.sentence1}
            sentence2={currentStepData.sentence2}
            actionLabel={currentStepData.actionLabel}
            onAction={currentStepData.onAction}
            onPrev={() => {
              if (currentStep === 5) {
                setActiveTab('overview');
              }
              setCurrentStep((prev) => Math.max(1, prev - 1));
            }}
            onDismiss={handleDismiss}
            onOpenGlossary={() => setIsGlossaryOpen(true)}
            targetRect={targetRect}
            isLoading={isLoadingSample}
            prefersReducedMotion={prefersReducedMotion}
          />
        </>
      )}
    </>
  );
}
