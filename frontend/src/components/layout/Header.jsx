import React, { useState, useEffect } from 'react';
import { Cpu, UploadCloud, RefreshCcw, ShieldCheck, Database, Volume2, VolumeX, Activity } from 'lucide-react';
import { isAudioEnabled, setAudioEnabled, playMechanicalClick } from '../../lib/audioEffects';

export default function Header({
  backendReady,
  dataset,
  onOpenUpload,
  onReloadDemo,
  isSubmitting
}) {
  const [audioOn, setAudioOn] = useState(isAudioEnabled());
  const [busCycle, setBusCycle] = useState(2481);

  // Live industrial bus clock cycle heartbeat (Design Spell)
  useEffect(() => {
    const timer = setInterval(() => {
      setBusCycle(c => c + 1);
    }, 2800);
    return () => clearInterval(timer);
  }, []);

  const toggleAudio = () => {
    const next = !audioOn;
    setAudioOn(next);
    setAudioEnabled(next);
  };

  const modelName = dataset?.model_info?.selected_model || 'xgboost_v2';
  const prototypeVersion = dataset?.model_info?.prototype_version || 'mlcc-pilot-1.1';
  const provenance = dataset?.provenance || 'synthetic';

  return (
    <header className="sticky top-0 z-40 w-full bg-[#08090d]/85 backdrop-blur-xl border-b border-white/[0.06] px-6 py-2.5">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-start md:items-center justify-between gap-3">
        {/* Context Identification & Live Bus HUD */}
        <div className="flex items-center gap-4">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-sm font-semibold tracking-tight text-white flex items-center gap-2">
                Burn-In Sentinel
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

          {/* Live Industrial Bus Heartbeat (Design Spell) */}
          <div className="hidden xl:flex items-center gap-2 px-2.5 py-1 rounded bg-white/[0.02] border border-white/[0.05] text-[10px] font-mono text-slate-400 select-none">
            <span className="w-1.5 h-1.5 rounded-full bg-orange-400/80 animate-pulse" />
            <span>BUS CLK 10.0MHz</span>
            <span className="text-slate-600">•</span>
            <span>CYCLE #{String(busCycle).padStart(5, '0')}</span>
            <span className="text-slate-600">•</span>
            <span className="text-orange-400/90">ACQ 64/64 CH</span>
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
          <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-white/[0.02] border border-white/[0.06] text-[11px] font-mono text-slate-400">
            <Database className="w-3 h-3 text-slate-500" strokeWidth={1.5} />
            <span>{provenance.toUpperCase()}</span>
          </div>

          {/* Audio Feedback Toggle (Design Spell) */}
          <button
            onClick={toggleAudio}
            title={audioOn ? 'Hardware Sound Effects: ON (Click to Mute)' : 'Hardware Sound Effects: OFF (Click to Enable Tactile Relays)'}
            className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-mono transition-all cursor-pointer ${
              audioOn
                ? 'bg-orange-500/15 text-orange-300 border border-orange-500/30'
                : 'bg-white/[0.02] text-slate-400 border border-white/[0.06] hover:text-white'
            }`}
          >
            {audioOn ? <Volume2 className="w-3.5 h-3.5 text-orange-400" strokeWidth={1.5} /> : <VolumeX className="w-3.5 h-3.5 text-slate-500" strokeWidth={1.5} />}
            <span className="hidden sm:inline text-[10px] uppercase tracking-wider">{audioOn ? 'AUDIO ON' : 'MUTED'}</span>
          </button>

          {/* Quick Reload Sample */}
          <button
            onClick={() => {
              playMechanicalClick();
              onReloadDemo();
            }}
            disabled={isSubmitting}
            title="Reload verified sample demonstration dataset"
            className="btn-secondary flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono disabled:opacity-50"
          >
            <RefreshCcw className="w-3.5 h-3.5 text-slate-400" strokeWidth={1.5} />
            <span>Sample Data</span>
          </button>

          {/* Upload CSV Action Button */}
          <button
            onClick={() => {
              playMechanicalClick();
              onOpenUpload();
            }}
            disabled={isSubmitting}
            className="btn-primary flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-mono"
          >
            <UploadCloud className="w-3.5 h-3.5" strokeWidth={1.5} />
            <span>Screen CSV</span>
          </button>
        </div>
      </div>
    </header>
  );
}
