import React, { useState } from 'react';
import SquircleCard from '../common/SquircleCard';
import SchemaGuide from './SchemaGuide';
import LeakageLensLogo from '../common/LeakageLensLogo';
import {
  X,
  UploadCloud,
  FileSpreadsheet,
  AlertCircle,
  CheckCircle2,
  Loader2,
  RefreshCcw
} from 'lucide-react';
import { screenUpload } from '../../lib/api';

export default function UploadModal({
  isOpen,
  onClose,
  onUploadSuccess,
  onLoadSample
}) {
  const [earlyFile, setEarlyFile] = useState(null);
  const [outcomeFile, setOutcomeFile] = useState(null);
  const [forecastModel, setForecastModel] = useState('xgboost_v2');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!earlyFile) {
      setError({ message: 'Please select an Early CSV file with 0 h and 24 h readings.' });
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const result = await screenUpload(earlyFile, outcomeFile, forecastModel);
      onUploadSuccess(result);
      onClose();
    } catch (err) {
      setError(err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md overflow-y-auto">
      <SquircleCard
        elevated
        className="w-full max-w-2xl p-6 sm:p-8 bg-[#12131b] border-white/15 max-h-[90vh] overflow-y-auto space-y-6"
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-white/10 pb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-orange-500/10 border border-orange-500/20 flex items-center justify-center shrink-0 shadow-[0_0_12px_rgba(249,115,22,0.15)]">
              <LeakageLensLogo className="w-6 h-6" showGlow />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-display font-bold text-white">
                  Screen Electronic Components
                </h2>
                <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-orange-500/15 text-orange-300 border border-orange-500/25">
                  LEAKAGE LENS
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Upload 0 h and 24 h burn-in readings for inference and final 168 h forecasting.
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            disabled={isSubmitting}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" strokeWidth={1.5} />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Quick Demo Loader Option */}
          <div className="p-4 rounded-xl bg-orange-500/[0.05] border border-orange-500/20 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
            <div>
              <span className="text-xs font-mono font-bold text-white block">
                Instant Verification Mode:
              </span>
              <span className="text-[11px] text-slate-400">
                Load the pre-verified 64-component MLCC synthetic test sample with 168 h outcomes.
              </span>
            </div>

            <button
              type="button"
              onClick={() => {
                onLoadSample();
                onClose();
              }}
              disabled={isSubmitting}
              className="btn-secondary px-4 py-2 text-xs font-mono font-semibold whitespace-nowrap"
            >
              Load Verified Sample
            </button>
          </div>

          {/* 1. Early CSV Input */}
          <div className="space-y-1.5">
            <label className="text-xs font-mono font-bold text-white block uppercase tracking-wider">
              Early Readings CSV (Required)
            </label>
            <div className="relative border-2 border-dashed border-white/15 hover:border-orange-500/50 rounded-xl p-5 bg-black/20 text-center transition-colors">
              <input
                type="file"
                accept=".csv,text/csv"
                onChange={(e) => setEarlyFile(e.target.files[0])}
                disabled={isSubmitting}
                className="absolute inset-0 opacity-0 cursor-pointer w-full h-full"
              />
              <FileSpreadsheet className="w-8 h-8 mx-auto text-orange-400 mb-2 opacity-80" strokeWidth={1.5} />
              {earlyFile ? (
                <span className="text-xs font-mono text-orange-300 font-semibold block truncate">
                  Selected: {earlyFile.name} ({(earlyFile.size / 1024).toFixed(1)} KB)
                </span>
              ) : (
                <span className="text-xs text-slate-400 block font-mono">
                  Drag &amp; drop or click to choose <strong className="text-slate-200">Early CSV</strong> (0 h &amp; 24 h)
                </span>
              )}
            </div>
          </div>

          {/* 2. Optional Outcome CSV Input */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <label className="text-xs font-mono font-bold text-white block uppercase tracking-wider">
                Recorded Outcome CSV (Optional)
              </label>
              <span className="text-[10px] font-mono text-slate-500">For 168h Reveal</span>
            </div>
            <div className="relative border-2 border-dashed border-white/15 hover:border-orange-500/50 rounded-xl p-4 bg-black/20 text-center transition-colors">
              <input
                type="file"
                accept=".csv,text/csv"
                onChange={(e) => setOutcomeFile(e.target.files[0])}
                disabled={isSubmitting}
                className="absolute inset-0 opacity-0 cursor-pointer w-full h-full"
              />
              {outcomeFile ? (
                <span className="text-xs font-mono text-orange-300 font-semibold block truncate">
                  Selected: {outcomeFile.name} ({(outcomeFile.size / 1024).toFixed(1)} KB)
                </span>
              ) : (
                <span className="text-xs text-slate-400 block font-mono">
                  Optional later observations (48h - 168h) for blind validation
                </span>
              )}
            </div>
          </div>

          {/* 3. Model Selector */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-mono">
            <div>
              <label className="text-slate-400 block mb-1">Forecast Model</label>
              <select
                value={forecastModel}
                onChange={(e) => setForecastModel(e.target.value)}
                disabled={isSubmitting}
                className="w-full px-3 py-2 rounded-xl bg-[#0e0f16] border border-white/10 text-white focus:outline-none focus:border-orange-500"
              >
                <option value="xgboost_v2">xgboost_v2 (Internal Winner)</option>
                <option value="persistence">persistence (Naive Baseline)</option>
                <option value="linear_extrapolation">linear_extrapolation</option>
                <option value="ridge">ridge</option>
                <option value="hist_gradient_boosting">hist_gradient_boosting</option>
                <option value="xgboost">xgboost (v1 Candidate)</option>
              </select>
            </div>

            <div>
              <label className="text-slate-400 block mb-1">Measurement Profile</label>
              <input
                type="text"
                disabled
                value="MLCC X7R Leakage (µA)"
                className="w-full px-3 py-2 rounded-xl bg-[#0e0f16] border border-white/10 text-slate-400 cursor-not-allowed"
              />
            </div>
          </div>

          {/* 4. Collapsible Schema Guide */}
          <SchemaGuide />

          {/* Error Display Panel */}
          {error && (
            <div className="p-4 rounded-xl bg-orange-500/10 border border-orange-500/30 text-xs font-mono text-orange-200 space-y-2">
              <div className="flex items-center gap-2 font-bold text-orange-300">
                <AlertCircle className="w-4 h-4 flex-shrink-0" strokeWidth={1.5} />
                <span>Validation Error: {error.error || 'UPLOAD_REJECTED'}</span>
              </div>
              <p className="leading-relaxed">{error.message}</p>
              {error.details && error.details.length > 0 && (
                <div className="mt-2 pt-2 border-t border-orange-500/20 space-y-1">
                  {error.details.slice(0, 3).map((d, i) => (
                    <div key={i} className="text-[11px] text-orange-300">
                      Row {d.row || 'N/A'}, Col {d.column || 'N/A'}: {d.message}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="px-4 py-2 rounded-xl text-xs font-mono text-slate-400 hover:text-white transition-colors cursor-pointer"
            >
              Cancel
            </button>

            <button
              type="submit"
              disabled={isSubmitting || !earlyFile}
              className="btn-primary px-6 py-2.5 flex items-center gap-2 text-xs font-mono tracking-wide"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" strokeWidth={1.5} />
                  <span>Validating &amp; Scoring Components...</span>
                </>
              ) : (
                <>
                  <UploadCloud className="w-4 h-4" strokeWidth={1.5} />
                  <span>Submit for Screening</span>
                </>
              )}
            </button>
          </div>
        </form>
      </SquircleCard>
    </div>
  );
}
