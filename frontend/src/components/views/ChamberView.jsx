import React from 'react';
import SquircleCard from '../common/SquircleCard';
import {
  Thermometer,
  Zap,
  Droplets,
  Activity,
  Server,
  Wind,
  ShieldCheck,
  CheckCircle2,
  Clock,
  Download
} from 'lucide-react';
import { exportToCsv } from '../../lib/utils';

export default function ChamberView({ dataset }) {
  const records = dataset?.records || [];
  const sampleContext = records[0]?.context || {};

  const chamberLogs = [
    {
      timestamp: '00:00:00.000',
      event: 'Baseline T0 reading cycle initialized',
      channel: 'ALL (CH 01-16)',
      temperature: '125.0 °C',
      voltage: '45.7 V',
      status: 'NOMINAL',
      operator: 'SYSTEM_AUTOTEST'
    },
    {
      timestamp: '12:00:00.000',
      event: 'Intermediate checkpoint thermal stability verify',
      channel: 'CH 01-16',
      temperature: '125.2 °C',
      voltage: '45.7 V',
      status: 'NOMINAL',
      operator: 'WATCHDOG_DAEMON'
    },
    {
      timestamp: '24:00:00.000',
      event: 'Cutoff checkpoint T24 readings captured & validated',
      channel: 'ALL (CH 01-16)',
      temperature: '125.0 °C',
      voltage: '45.7 V',
      status: 'SCREENING_READY',
      operator: 'SYSTEM_AUTOTEST'
    },
    {
      timestamp: '24:05:12.450',
      event: 'Early Anomaly Inference Pipeline triggered (xgboost_v2)',
      channel: 'CORE INF',
      temperature: '125.1 °C',
      voltage: '45.7 V',
      status: 'SCORING_COMPLETE',
      operator: 'SIH26170_SENTINEL'
    }
  ];

  const handleExportLogs = () => {
    exportToCsv('Chamber_Telemetry_Log.csv', chamberLogs);
  };

  return (
    <div className="space-y-6 pb-12">
      {/* 1. Chamber Top Banner */}
      <SquircleCard elevated className="p-5">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="w-1.5 h-1.5 rounded-full bg-orange-400" />
              <span className="text-[10px] font-mono font-medium text-orange-400 uppercase tracking-wider">
                CHAMBER ZONE 01 // HTOL TEST RACK
              </span>
            </div>
            <h2 className="text-base font-display font-semibold text-white tracking-tight">
              Environmental &amp; Chamber Telemetry
            </h2>
            <p className="text-[11px] text-slate-400">
              High-temperature operational life rack monitoring 64 active MLCC test sockets.
            </p>
          </div>

          <div className="flex items-center gap-2.5">
            <div className="px-3 py-1.5 rounded-lg bg-white/[0.02] border border-white/[0.04] text-right font-mono">
              <span className="text-[9px] text-slate-500 uppercase block">THERMAL STRESS</span>
              <span className="text-sm font-medium text-white">125.0 °C</span>
            </div>
            <div className="px-3 py-1.5 rounded-lg bg-white/[0.02] border border-white/[0.04] text-right font-mono">
              <span className="text-[9px] text-slate-500 uppercase block">VOLTAGE STRESS</span>
              <span className="text-sm font-medium text-orange-400">45.7 V</span>
            </div>
          </div>
        </div>
      </SquircleCard>

      {/* 2. Sensor Instrumentation KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 font-mono">
        <SquircleCard className="p-4 space-y-1.5">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[10px] uppercase">Chamber Temp</span>
            <Thermometer className="w-3.5 h-3.5 text-orange-400" />
          </div>
          <div className="text-xl font-medium text-white">
            {sampleContext.temperature_c || 125.0} °C
          </div>
          <div className="text-[10px] text-slate-500">
            Setpoint: 125.0°C (±0.5°C)
          </div>
        </SquircleCard>

        <SquircleCard className="p-4 space-y-1.5">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[10px] uppercase">Stress Voltage</span>
            <Zap className="w-3.5 h-3.5 text-orange-400" />
          </div>
          <div className="text-xl font-medium text-white">
            {sampleContext.applied_voltage_v || 45.7} V
          </div>
          <div className="text-[10px] text-slate-500">
            Rated: {sampleContext.rated_voltage_v || 50.0} V (0.914x)
          </div>
        </SquircleCard>

        <SquircleCard className="p-4 space-y-1.5">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[10px] uppercase">Prior Storage RH</span>
            <Droplets className="w-3.5 h-3.5 text-orange-400" />
          </div>
          <div className="text-xl font-medium text-white">
            {sampleContext.prior_storage_humidity_pct || 55.4} %RH
          </div>
          <div className="text-[10px] text-slate-500">
            Pre-conditioning history
          </div>
        </SquircleCard>

        <SquircleCard className="p-4 space-y-1.5">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[10px] uppercase">Tester Hardware</span>
            <Server className="w-3.5 h-3.5 text-orange-400" />
          </div>
          <div className="text-xl font-medium text-white">
            {sampleContext.tester_id || 'TESTER_03'}
          </div>
          <div className="text-[10px] text-slate-500">
            16 Parallel Channels
          </div>
        </SquircleCard>
      </div>

      {/* 3. Event Log Table */}
      <SquircleCard className="p-5 space-y-3.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity className="w-3.5 h-3.5 text-orange-400" />
            <h3 className="text-xs font-mono uppercase tracking-wider text-slate-300">
              Chamber Event Log
            </h3>
          </div>

          <button
            onClick={handleExportLogs}
            className="btn-secondary flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono"
          >
            <Download className="w-3.5 h-3.5 text-slate-400" />
            <span>Export CSV</span>
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono border-collapse">
            <thead className="bg-[#0b0c12] text-slate-500 border-b border-white/[0.06]">
              <tr>
                <th className="py-2 px-3">TIMESTAMP</th>
                <th className="py-2 px-3">EVENT</th>
                <th className="py-2 px-3">CHANNELS</th>
                <th className="py-2 px-3">TEMP</th>
                <th className="py-2 px-3">VOLTAGE</th>
                <th className="py-2 px-3">STATUS</th>
                <th className="py-2 px-3">SOURCE</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.04]">
              {chamberLogs.map((log, idx) => (
                <tr key={idx} className="hover:bg-white/[0.02] text-slate-300 transition-colors">
                  <td className="py-2 px-3 text-slate-500">{log.timestamp}</td>
                  <td className="py-2 px-3 text-white">{log.event}</td>
                  <td className="py-2 px-3 text-slate-400">{log.channel}</td>
                  <td className="py-2 px-3">{log.temperature}</td>
                  <td className="py-2 px-3">{log.voltage}</td>
                  <td className="py-2 px-3">
                    <span className="px-1.5 py-0.5 rounded text-[10px] bg-white/[0.04] text-slate-300 border border-white/[0.08]">
                      {log.status}
                    </span>
                  </td>
                  <td className="py-2 px-3 text-slate-500">{log.operator}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </SquircleCard>
    </div>
  );
}
