import React, { useState } from 'react';
import { ChevronDown, ChevronUp, HelpCircle } from 'lucide-react';

export default function SchemaGuide() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="border border-white/10 rounded-xl overflow-hidden bg-black/30 font-mono text-xs">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full p-3 flex items-center justify-between text-slate-300 hover:text-white transition-colors cursor-pointer"
      >
        <span className="flex items-center gap-2">
          <HelpCircle className="w-4 h-4 text-orange-400" strokeWidth={1.5} />
          <span>CSV Column &amp; Format Specifications</span>
        </span>
        {isOpen ? <ChevronUp className="w-4 h-4" strokeWidth={1.5} /> : <ChevronDown className="w-4 h-4" strokeWidth={1.5} />}
      </button>

      {isOpen && (
        <div className="p-4 pt-0 border-t border-white/5 space-y-3 text-slate-400">
          <div>
            <strong className="text-white block mb-1">Required Columns (Early CSV):</strong>
            <p className="text-[11px] leading-relaxed bg-black/50 p-2 rounded border border-white/5 text-orange-300">
              component_id, batch_id, component_family, hours, measurement_name, measurement_value, upper_limit, profile_id
            </p>
          </div>

          <div>
            <strong className="text-white block mb-1">Rules &amp; Boundaries:</strong>
            <ul className="list-disc list-inside space-y-1 text-[11px] text-slate-300">
              <li><code className="text-orange-300">component_family</code> must be <code className="text-orange-300">MLCC_X7R</code>.</li>
              <li><code className="text-orange-300">measurement_name</code> must be <code className="text-orange-300">leakage_ua</code> in µA.</li>
              <li>Exactly one 0 h and one 24 h checkpoint row per component.</li>
              <li><code className="text-orange-300">upper_limit</code> must be positive. Lower limits are not supported for this pilot.</li>
              <li>All components in a single upload must share the same <code className="text-orange-300">profile_id</code>.</li>
            </ul>
          </div>

          <div>
            <strong className="text-white block mb-1">Optional Outcome CSV:</strong>
            <p className="text-[11px] text-slate-300">
              Contains readings strictly after 24 h (e.g. 48, 96, 168 h) for blind reveal and validation. It never alters the early prediction or recommendation.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
