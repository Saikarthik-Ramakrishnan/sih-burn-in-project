import React, { useEffect, useRef, useState } from 'react';
import {
  X,
  BookOpen,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  AlertOctagon,
  HelpCircle,
  FileSpreadsheet,
  AlertCircle,
  ShieldCheck,
  Search,
  Database
} from 'lucide-react';

export default function GlossaryDrawer({ isOpen, onClose, prefersReducedMotion }) {
  const [activeCategory, setActiveCategory] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const drawerRef = useRef(null);
  const closeButtonRef = useRef(null);

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => closeButtonRef.current?.focus(), 50);
    }
  }, [isOpen]);

  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      e.stopPropagation();
      onClose();
      return;
    }
    if (e.key === 'Tab') {
      const focusable = drawerRef.current?.querySelectorAll(
        'button:not([disabled]), [tabindex]:not([tabindex="-1"]), input:not([disabled])'
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

  if (!isOpen) return null;

  const glossaryItems = [
    {
      id: 'accept',
      category: 'recommendations',
      term: 'ACCEPT',
      badge: 'NOMINAL',
      color: 'text-emerald-400',
      definition:
        'The component exhibits nominal drift trajectory and stays within verified statistical batch bounds. Neither anomalous peer divergence nor projected threshold breaches are detected.',
      apiField: 'recommendation: "ACCEPT"'
    },
    {
      id: 'monitor',
      category: 'recommendations',
      term: 'MONITOR',
      badge: 'WATCHLIST',
      color: 'text-yellow-400',
      definition:
        'Elevated rate of drift or the forecast interval upper bound reaches the specification limit (prediction_upper >= upper_limit). The component sits within spec but warrants extended observation.',
      apiField: 'recommendation: "MONITOR"'
    },
    {
      id: 'retest',
      category: 'recommendations',
      term: 'RETEST',
      badge: 'ANOMALY / CROSSING',
      color: 'text-amber-400',
      definition:
        'A strong peer anomaly (score >= 0.8 or current_batch_robust_z >= 3.5) or a forecast limit crossing (predicted_to_cross_limit: true). Re-measurement or chamber re-seating is indicated.',
      apiField: 'recommendation: "RETEST"'
    },
    {
      id: 'engineer_review',
      category: 'recommendations',
      term: 'ENGINEER_REVIEW',
      badge: 'DEFECT / BREACH',
      color: 'text-rose-400',
      definition:
        'The component is anomalous and forecast to cross its limit (recommendation_basis: "anomaly_and_forecast"), or has already breached the 24 h limit. Requires immediate engineering review.',
      apiField: 'recommendation: "ENGINEER_REVIEW"'
    },
    {
      id: 'anomaly_score',
      category: 'statistics',
      term: 'Anomaly Score (anomaly.score)',
      badge: 'PEER RANKING',
      color: 'text-orange-400',
      definition:
        'A relative ranking metric (score_kind: "ranking score, not failure probability") combining robust median/MAD deviation and an Isolation Forest model. It measures how differently a part drifts compared to its uploaded batch peers, never an absolute physical failure probability.',
      apiField: 'anomaly.score · anomaly.score_kind'
    },
    {
      id: 'robust_z',
      category: 'statistics',
      term: 'Robust Z-Score (current_batch_robust_z)',
      badge: 'BATCH DEVIATION',
      color: 'text-orange-400',
      definition:
        'Calculated as (value - batch_median) / (1.4826 * batch_MAD). Unlike conventional standard deviation, it is resilient to extreme outliers. Batches with fewer than 8 parts (sample_size < 8) receive a warning that peer comparisons are statistically weak.',
      apiField: 'peers.current_batch_robust_z · peers.sample_size'
    },
    {
      id: 'interval',
      category: 'statistics',
      term: 'Forecast Interval (prediction_lower .. prediction_upper)',
      badge: '80% INTERVAL / 90% BOUND',
      color: 'text-orange-400',
      definition:
        'For the default xgboost_v2 model, prediction_lower to prediction_upper represents an 80 % nominal conformal interval whose upper bound is a one-sided 90 % bound. Roughly one part in ten ends above the upper bound. Intervals are nominal and calibrated on synthetic batches; field coverage is not claimed.',
      apiField: 'forecast.interval_nominal_coverage: 0.8 · forecast.upper_bound_nominal_level: 0.9'
    },
    {
      id: 'unscored',
      category: 'pipeline',
      term: 'Unscored Records (unscored_records)',
      badge: 'NOT ASSESSED',
      color: 'text-slate-400',
      definition:
        'Records excluded from screening due to missing checkpoints (e.g. missing 0 h or 24 h row), unsupported profile_id, or invalid limits. Unscored parts were not assessed and must never be interpreted as passes.',
      apiField: 'unscored_records[] · unscored_record_count'
    },
    {
      id: 'synthetic',
      category: 'pipeline',
      term: 'Synthetic Calibration (SYNTHETIC)',
      badge: 'PROVENANCE',
      color: 'text-slate-400',
      definition:
        'All models and baseline datasets are trained and evaluated on synthetic MLCC physics simulations. The SYNTHETIC badge indicates that no field deployment accuracy is claimed. Recommendations are intended for decision support only.',
      apiField: 'model_info.model_training_data: "synthetic"'
    },
    {
      id: 'empty_state',
      category: 'pipeline',
      term: 'Empty & Pre-Upload State',
      badge: 'SYSTEM STATUS',
      color: 'text-slate-300',
      definition:
        'Prior to uploading batch telemetry, the dashboard displays an empty ingestion prompt ("Upload CSV" or "Load Verified Sample"). Socket maps and topology clusters remain unpopulated until batch data is provided. API connectivity reflects "API CONNECTED" when /api/v1/health/ready passes.',
      apiField: 'GET /api/v1/health/ready'
    },
    {
      id: 'input_spec',
      category: 'schema',
      term: 'Input CSV Specification',
      badge: 'POST /api/v1/screen',
      color: 'text-orange-400',
      definition:
        'Requires a long-format CSV with exactly one 0 h row and one 24 h row per component. Required columns: component_id, batch_id, component_family, hours, measurement_name, measurement_value, upper_limit, and profile_id (must match GET /api/v1/profiles). Rows beyond 24 h are preserved for outcome verification.',
      apiField: 'file: multipart/form-data CSV'
    },
    {
      id: 'error_schema',
      category: 'errors',
      term: 'Backend Rejection & Error Structure',
      badge: 'HTTP 413 / 415 / 422',
      color: 'text-rose-400',
      definition:
        'The API rejects malformed CSVs with structured JSON containing a root error code, descriptive message, request_id, and verbatim details array pointing to the 1-based CSV row and column.',
      apiField: '{ error, message, request_id, details: [{ code, message, row, column, value }] }'
    }
  ];

  const filteredItems = glossaryItems.filter((item) => {
    const matchesCat = activeCategory === 'all' || item.category === activeCategory;
    if (!matchesCat) return false;
    if (!searchTerm.trim()) return true;
    const q = searchTerm.toLowerCase().trim();
    return (
      item.term.toLowerCase().includes(q) ||
      item.definition.toLowerCase().includes(q) ||
      item.apiField.toLowerCase().includes(q)
    );
  });

  return (
    <div
      className="fixed inset-0 z-[90] flex justify-end bg-black/60 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="glossary-title"
      onKeyDown={handleKeyDown}
    >
      <div
        ref={drawerRef}
        className={`
          w-full max-w-xl h-full bg-[#0a0b10] border-l border-white/[0.08] flex flex-col
          shadow-[-16px_0_48px_rgba(0,0,0,0.8)]
          ${prefersReducedMotion ? '' : 'transition-transform duration-300 ease-out'}
        `}
      >
        {/* Drawer Header */}
        <div className="p-5 border-b border-white/[0.06] flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-orange-500/10 border border-orange-500/20 text-orange-400 flex items-center justify-center shrink-0">
              <BookOpen className="w-4 h-4" strokeWidth={1.5} />
            </div>
            <div>
              <h2 id="glossary-title" className="text-sm font-semibold text-white tracking-tight">
                Technical Glossary &amp; API Contract
              </h2>
              <p className="text-[11px] text-slate-400">
                Definitions, statistical conventions, and error models
              </p>
            </div>
          </div>

          <button
            ref={closeButtonRef}
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 transition-colors cursor-pointer"
            title="Close glossary"
            aria-label="Close glossary"
          >
            <X className="w-5 h-5" strokeWidth={1.5} />
          </button>
        </div>

        {/* Search & Filter Bar */}
        <div className="p-4 border-b border-white/[0.04] space-y-3 bg-[#0e0f16]">
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" strokeWidth={1.5} />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search terms, metrics, or error codes..."
              className="w-full pl-9 pr-3 py-1.5 rounded-lg bg-black/40 border border-white/10 text-xs font-mono text-white placeholder-slate-500 focus:outline-none focus:border-orange-500/50"
            />
          </div>

          <div className="flex flex-wrap gap-1.5 text-[11px] font-mono">
            {['all', 'recommendations', 'statistics', 'pipeline', 'schema', 'errors'].map((cat) => (
              <button
                key={cat}
                onClick={() => setActiveCategory(cat)}
                className={`px-2.5 py-1 rounded-md transition-colors uppercase ${
                  activeCategory === cat
                    ? 'bg-orange-500/20 text-orange-300 border border-orange-500/30 font-semibold'
                    : 'bg-white/[0.02] text-slate-400 hover:text-slate-200 border border-white/[0.04]'
                }`}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>

        {/* Item List */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          {filteredItems.map((item) => (
            <div
              key={item.id}
              className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.04] space-y-2 hover:border-white/10 transition-colors"
            >
              <div className="flex items-center justify-between gap-2">
                <span className={`text-xs font-mono font-bold ${item.color}`}>
                  {item.term}
                </span>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-white/[0.04] text-slate-400 border border-white/[0.06]">
                  {item.badge}
                </span>
              </div>

              <p className="text-xs text-slate-300 leading-relaxed">
                {item.definition}
              </p>

              <div className="pt-2 border-t border-white/[0.03] text-[10px] font-mono text-slate-500">
                API Reference: <code className="text-slate-400">{item.apiField}</code>
              </div>
            </div>
          ))}

          {/* Verbatim Backend Error Representation */}
          {(activeCategory === 'all' || activeCategory === 'errors') && (
            <div className="p-4 rounded-xl bg-rose-500/[0.04] border border-rose-500/20 space-y-2.5">
              <div className="flex items-center gap-2 text-rose-300 font-mono text-xs font-bold">
                <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" strokeWidth={1.5} />
                <span>Verbatim Rejection JSON Example (422)</span>
              </div>
              <p className="text-xs text-slate-400 leading-normal">
                When a CSV is rejected, the API returns structured error details without stack traces:
              </p>
              <pre className="p-3 rounded-lg bg-black/50 border border-rose-500/20 font-mono text-[11px] text-rose-200 overflow-x-auto">
{`{
  "error": "INCOMPATIBLE_UNITS",
  "message": "Declared unit 'mA' is incompatible with profile unit 'uA'",
  "request_id": "cada3c5176f24c45bf79a9178e3edc32",
  "details": [
    {
      "code": "UNIT_MISMATCH",
      "message": "Expected measurement_name 'leakage_ua' in 'uA'",
      "row": 4,
      "column": "measurement_name",
      "value": "leakage_ma"
    }
  ]
}`}
              </pre>
            </div>
          )}
        </div>

        {/* Drawer Footer */}
        <div className="p-4 border-t border-white/[0.06] bg-[#08090e] flex items-center justify-between text-xs font-mono text-slate-500">
          <span>Schema Version: 1.0.0</span>
          <button
            type="button"
            onClick={onClose}
            className="btn-secondary px-3 py-1.5 text-xs text-slate-300"
          >
            Close Glossary
          </button>
        </div>
      </div>
    </div>
  );
}
