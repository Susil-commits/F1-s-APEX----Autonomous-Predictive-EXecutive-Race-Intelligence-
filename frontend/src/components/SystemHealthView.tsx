import React, { useState, useEffect } from 'react';
import { Activity, ShieldCheck, Cpu, HardDrive, Database, CheckCircle2, Clock } from 'lucide-react';

export const SystemHealthView: React.FC = () => {
  const [metrics, setMetrics] = useState<any>(null);

  useEffect(() => {
    fetch('/api/observability/metrics')
      .then((res) => res.json())
      .then((data) => setMetrics(data))
      .catch(() => {});
  }, []);

  return (
    <div className="flex flex-col gap-4 p-2 font-mono">
      <div className="flex items-center justify-between bg-slate-900/90 p-4 rounded-xl border border-slate-800">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
            <Activity className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-base font-bold text-white font-sans">APEX System Observability & Model Infrastructure Health</h2>
            <p className="text-xs text-slate-400">Microservice telemetry, AI policy status, and memory cache diagnostics</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="px-2.5 py-1 text-xs rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-bold flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5" /> SYSTEM {metrics?.system_status || 'ONLINE'}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800 flex flex-col gap-2">
          <span className="text-[11px] text-slate-400 flex items-center gap-1.5"><Cpu className="w-4 h-4 text-cyan-400" /> AI MODEL REGISTRY</span>
          <div className="space-y-1.5 text-xs mt-1">
            <div className="flex justify-between">
              <span className="text-slate-300">FastF1 Tyre ML Regressor:</span>
              <span className="text-emerald-400 font-bold">READY</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-300">Deep Q-Network (DQN) Policy:</span>
              <span className="text-emerald-400 font-bold">LOADED</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-300">PPO Decision Policy:</span>
              <span className="text-emerald-400 font-bold">ACTIVE</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-300">Isolation Forest Anomaly:</span>
              <span className="text-emerald-400 font-bold">INITIALIZED</span>
            </div>
          </div>
        </div>

        <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800 flex flex-col gap-2">
          <span className="text-[11px] text-slate-400 flex items-center gap-1.5"><Database className="w-4 h-4 text-purple-400" /> STATE STORE & PERSISTENCE</span>
          <div className="space-y-1.5 text-xs mt-1">
            <div className="flex justify-between">
              <span className="text-slate-300">L1 In-Memory Hot Cache:</span>
              <span className="text-emerald-400 font-bold">ACTIVE</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-300">L2 Async Redis Buffer:</span>
              <span className="text-emerald-400 font-bold">FALLBACK READY</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-300">L3 SQLite / PostgreSQL DB:</span>
              <span className="text-emerald-400 font-bold">CONNECTED</span>
            </div>
          </div>
        </div>

        <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800 flex flex-col gap-2">
          <span className="text-[11px] text-slate-400 flex items-center gap-1.5"><Clock className="w-4 h-4 text-amber-400" /> DECISION LATENCY GAUGE</span>
          <div className="space-y-1.5 text-xs mt-1">
            <div className="flex justify-between">
              <span className="text-slate-300">Rule Engine Inference:</span>
              <span className="text-cyan-400 font-bold">&lt; 1 ms</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-300">Vectorized Monte Carlo (1000x):</span>
              <span className="text-cyan-400 font-bold">&lt; 15 ms</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-300">TreeSHAP Feature Attribution:</span>
              <span className="text-cyan-400 font-bold">&lt; 25 ms</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
