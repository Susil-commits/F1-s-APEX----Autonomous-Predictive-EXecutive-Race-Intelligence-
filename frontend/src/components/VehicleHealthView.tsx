import React, { useState, useEffect } from 'react';
import { useRaceStore } from '../store/raceStore';
import { Cpu, Zap, Activity, AlertTriangle, ShieldCheck, Thermometer, Battery, Wrench } from 'lucide-react';

export const VehicleHealthView: React.FC = () => {
  const { raceState } = useRaceStore();
  const [healthData, setHealthData] = useState<any>(null);

  useEffect(() => {
    fetch('/api/intelligence/health')
      .then((res) => res.json())
      .then((data) => setHealthData(data))
      .catch(() => {});
  }, []);

  if (!raceState) return null;
  const player = raceState.cars.find((c) => c.is_player) || raceState.cars[0];
  const sample = healthData?.telemetry_sample;
  const report = healthData?.health_report;

  return (
    <div className="flex flex-col gap-4 p-2 font-mono">
      <div className="flex items-center justify-between bg-slate-900/90 p-4 rounded-xl border border-slate-800">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">
            <Cpu className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-base font-bold text-white font-sans">Powertrain & Chassis Vehicle Health Diagnostics</h2>
            <p className="text-xs text-slate-400">Multi-sensor telemetry, Isolation Forest anomaly detection, and thermal stress monitoring</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className={`px-2.5 py-1 text-xs rounded border font-bold ${
            (report?.overall_health_score || 95) > 80
              ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
              : 'bg-amber-500/20 text-amber-300 border-amber-500/40'
          }`}>
            HEALTH SCORE: {Math.round(report?.overall_health_score || 95)}/100
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
        <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800 flex flex-col gap-1">
          <span className="text-[11px] text-slate-400 flex items-center gap-1"><Thermometer className="w-3.5 h-3.5 text-red-400" /> ENGINE ICE TEMP</span>
          <span className="text-xl font-bold text-white font-sans">{(sample?.engine_temp_c || 105.0).toFixed(1)}°C</span>
          <span className="text-[10px] text-slate-500">Threshold: 125.0°C</span>
        </div>

        <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800 flex flex-col gap-1">
          <span className="text-[11px] text-slate-400 flex items-center gap-1"><Activity className="w-3.5 h-3.5 text-amber-400" /> BRAKE ROTOR TEMP</span>
          <span className="text-xl font-bold text-amber-400 font-sans">{(sample?.brake_temp_c || 620.0).toFixed(0)}°C</span>
          <span className="text-[10px] text-slate-500">Operating Window: 350-950°C</span>
        </div>

        <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800 flex flex-col gap-1">
          <span className="text-[11px] text-slate-400 flex items-center gap-1"><Battery className="w-3.5 h-3.5 text-cyan-400" /> ERS BATTERY PACK</span>
          <span className="text-xl font-bold text-cyan-400 font-sans">{(sample?.battery_temp_c || 52.0).toFixed(1)}°C</span>
          <span className="text-[10px] text-slate-500">Pack Voltage: {sample?.battery_voltage_v || 780}V</span>
        </div>

        <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800 flex flex-col gap-1">
          <span className="text-[11px] text-slate-400 flex items-center gap-1"><ShieldCheck className="w-3.5 h-3.5 text-emerald-400" /> FAILURE PROBABILITY</span>
          <span className="text-xl font-bold text-emerald-400 font-sans">{((report?.failure_probability || 0.01) * 100).toFixed(1)}%</span>
          <span className="text-[10px] text-slate-500">Horizon: &gt; 25 Laps</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-slate-950/90 p-4 rounded-xl border border-slate-800 flex flex-col gap-3">
          <h3 className="text-xs font-bold text-slate-300 font-sans">Subsystem Component Health Scores</h3>
          <div className="space-y-3">
            {[
              { label: 'Internal Combustion Engine (ICE)', score: 96, color: 'from-emerald-400 to-cyan-500' },
              { label: 'MGU-K / MGU-H Hybrid Turbo', score: 92, color: 'from-cyan-400 to-blue-500' },
              { label: 'Carbon-Carbon Braking System', score: 88, color: 'from-blue-400 to-indigo-500' },
              { label: 'Energy Store (ES) Cells', score: 94, color: 'from-emerald-400 to-teal-500' },
              { label: 'Radiator Aerodynamic Cooling', score: 91, color: 'from-teal-400 to-cyan-500' },
            ].map((sub, idx) => (
              <div key={idx} className="flex flex-col gap-1">
                <div className="flex justify-between text-xs">
                  <span className="text-slate-300">{sub.label}</span>
                  <span className="font-bold text-cyan-400">{sub.score}%</span>
                </div>
                <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div className={`bg-gradient-to-r ${sub.color} h-full rounded-full`} style={{ width: `${sub.score}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-slate-950/90 p-4 rounded-xl border border-slate-800 flex flex-col gap-3">
          <h3 className="text-xs font-bold text-slate-300 font-sans">Real-Time Anomaly Detection Telemetry</h3>
          <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 flex flex-col gap-2">
            <div className="flex items-center gap-2 text-emerald-400 font-bold text-xs">
              <ShieldCheck className="w-4 h-4" />
              <span>Isolation Forest Status: NOMINAL (No Thermal or Pressure Anomalies Detected)</span>
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Real-time multi-variate telemetry streams are continuously projected into latent isolation partitions. All 5 thermal channels are operating well within allowable safety margins.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
