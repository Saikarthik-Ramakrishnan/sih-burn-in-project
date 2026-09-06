import React from 'react';
import { Cpu, UploadCloud, RefreshCcw, ShieldCheck, Database } from 'lucide-react';

export default function Header({
  backendReady,
  dataset,
  onOpenUpload,
  onReloadDemo,
  isSubmitting
}) {
  const modelName = dataset?.model_info?.selected_model || 'xgboost_v2';
  const prototypeVersion = dataset?.model_info?.prototype_version || 'mlcc-pilot-1.1';
  const provenance = dataset?.provenance || 'synthetic';

  return (
    <header className="sticky top-0 z-40 w-full bg-[#08090d]/80 backdrop-blur-xl border-b border-white/[0.07] px-6 py-3">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        {/* Logo & Product Identification */}
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-orange-500/10 border border-orange-500/30 flex items-center justify-center">
            <Cpu className="w-4 h-4 text-orange-400" />
          </div>

          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-sm font-display font-semibold tracking-tight text-white flex items-center gap-2">
                Burn-In Sentinel
                <span className="text-[10px] font-mono font-medium px-2 py-0.5 rounded-md bg-orange-500/10 text-orange-300 border border-orange-500/20">
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
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/[0.03] border border-white/[0.08] text-xs">
            <span className={`w-1.5 h-1.5 rounded-full ${backendReady ? 'bg-orange-400' : 'bg-slate-500'}`} />
            <span className="text-slate-400 font-mono text-[11px]">
              {backendReady ? 'API CONNECTED' : 'LOCAL DEMO'}
            </span>
          </div>

          {/* Model Identification */}
          <div className="hidden lg:flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/[0.03] border border-white/[0.08] text-xs text-slate-400">
            <ShieldCheck className="w-3.5 h-3.5 text-orange-400/80" />
            <span className="font-mono text-[11px]">
              <strong className="text-slate-200 font-normal">{modelName}</strong> ({prototypeVersion})
            </span>
          </div>

          {/* Synthetic Provenance Pill */}
          <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-white/[0.03] border border-white/[0.08] text-[11px] font-mono text-slate-400">
            <Database className="w-3 h-3 text-slate-500" />
            <span>{provenance.toUpperCase()}</span>
          </div>

          {/* Quick Reload Sample */}
          <button
            onClick={onReloadDemo}
            disabled={isSubmitting}
            title="Reload verified sample demonstration dataset"
            className="btn-secondary flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono disabled:opacity-50"
          >
            <RefreshCcw className="w-3.5 h-3.5 text-slate-400" />
            <span>Sample Data</span>
          </button>

          {/* Upload CSV Action Button */}
          <button
            onClick={onOpenUpload}
            disabled={isSubmitting}
            className="btn-primary flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-mono"
          >
            <UploadCloud className="w-3.5 h-3.5" />
            <span>Screen CSV</span>
          </button>
        </div>
      </div>
    </header>
  );
}
