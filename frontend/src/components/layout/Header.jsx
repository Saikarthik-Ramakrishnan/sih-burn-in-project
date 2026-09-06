import React from 'react';
import { UploadCloud, RefreshCcw, ShieldCheck, Database, Search } from 'lucide-react';
import LeakageLensLogo from '../common/LeakageLensLogo';

export default function Header({
  backendReady,
  dataset,
  onOpenUpload,
  onReloadDemo,
  onOpenCommandPalette,
  isSubmitting
}) {
  const modelName = dataset?.model_info?.selected_model || 'xgboost_v2';
  const prototypeVersion = dataset?.model_info?.prototype_version || 'mlcc-pilot-1.1';
  const provenance = dataset?.provenance || 'synthetic';

  return (
    <header className="sticky top-0 z-40 w-full bg-[#08090d]/80 backdrop-blur-xl border-b border-white/[0.06] px-6 py-2.5">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-start md:items-center justify-between gap-3">
        {/* Context Identification */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-orange-500/10 border border-orange-500/25 flex items-center justify-center shrink-0 shadow-[0_0_12px_rgba(249,115,22,0.15)]">
            <LeakageLensLogo className="w-5 h-5" showGlow animated />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-sm font-semibold tracking-tight text-white flex items-center gap-2">
                Leakage Lens
                <span className="text-[10px] font-mono font-medium px-1.5 py-0.2 rounded bg-orange-500/10 text-orange-300 border border-orange-500/20">
                  SIH26170
                </span>
              </h1>
            </div>
            <p className="text-[11px] text-slate-400 flex items-center gap-1.5">
              <span>Early Anomaly &amp; 168h Forecast</span>
              <span className="text-slate-600">•</span>
              <span className="text-slate-300 font-mono">MLCC X7R</span>
            </p>
          </div>
        </div>

        {/* Telemetry Status Badges & Controls */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Backend Health Badge */}
          <div className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-white/[0.02] border border-white/[0.06] text-xs">
            <span className={`w-1.5 h-1.5 rounded-full ${backendReady ? 'bg-orange-400' : 'bg-slate-500'}`} />
            <span className="text-slate-400 font-mono text-[11px]">
              {backendReady ? 'API CONNECTED' : 'LOCAL DEMO'}
            </span>
          </div>

          {/* Model Identification */}
          <div className="hidden lg:flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-white/[0.02] border border-white/[0.06] text-xs text-slate-400">
            <ShieldCheck className="w-3.5 h-3.5 text-orange-400/80" strokeWidth={1.5} />
            <span className="font-mono text-[11px]">
              <strong className="text-slate-200 font-normal">{modelName}</strong> ({prototypeVersion})
            </span>
          </div>

          {/* Synthetic Provenance Pill */}
          <div className="hidden sm:flex items-center gap-1.5 px-2 py-1.5 rounded-lg bg-white/[0.02] border border-white/[0.06] text-[11px] font-mono text-slate-400">
            <Database className="w-3 h-3 text-slate-500" strokeWidth={1.5} />
            <span>{provenance.toUpperCase()}</span>
          </div>

          {/* Quick Command Palette Button */}
          <button
            onClick={onOpenCommandPalette}
            title="Open Command Palette (Ctrl+K or ⌘K)"
            className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-white/[0.03] hover:bg-white/[0.08] border border-white/[0.08] hover:border-orange-500/30 text-xs text-slate-400 hover:text-white transition-all cursor-pointer font-mono group"
          >
            <Search className="w-3.5 h-3.5 text-slate-400 group-hover:text-orange-400 transition-colors" strokeWidth={1.5} />
            <span className="hidden md:inline text-[11px] text-slate-300">Search</span>
            <kbd className="px-1.5 py-0.5 rounded bg-black/40 border border-white/10 text-[9.5px] text-slate-400 group-hover:text-orange-300">
              Ctrl+K
            </kbd>
          </button>

          {/* Quick Reload Sample */}
          <button
            onClick={onReloadDemo}
            disabled={isSubmitting}
            title="Reload verified sample demonstration dataset"
            className="btn-secondary flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono disabled:opacity-50"
          >
            <RefreshCcw className="w-3.5 h-3.5 text-slate-400" strokeWidth={1.5} />
            <span>Sample Data</span>
          </button>

          {/* Upload CSV Action Button */}
          <button
            onClick={onOpenUpload}
            disabled={isSubmitting}
            className="btn-primary flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-mono"
          >
            <UploadCloud className="w-3.5 h-3.5" strokeWidth={1.5} />
            <span>Upload CSV</span>
          </button>
        </div>
      </div>
    </header>
  );
}
