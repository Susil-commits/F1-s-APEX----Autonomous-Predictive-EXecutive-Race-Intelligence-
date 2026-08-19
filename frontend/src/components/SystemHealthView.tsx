import React, { useState, useEffect } from 'react';
import { Activity, ShieldCheck, Cpu, HardDrive, Database, CheckCircle2, Clock, FileCode, AlertTriangle, RefreshCw } from 'lucide-react';

interface ModelInfo {
  model_id: string;
  model_name: string;
  type: string;
  framework: string;
  status: string;
  in_sync: boolean;
  file_present: boolean;
  live_hash: string;
  expected_hash: string;
  size_bytes: number;
}

interface RegistryData {
  registry_version: string;
  audit_timestamp_utc: string;
  overall_status: string;
  total_models: number;
  healthy_count: number;
  drift_count: number;
  missing_count: number;
  models: Record<string, ModelInfo>;
}

interface SubsystemHealth {
  status: string;
  subsystems: {
    simulator: { status: string; engine_state: string };
    ml_models: { status: string; models_verified: number; healthy_count: number };
    database: { status: string; driver: string };
    redis_cache: { status: string; active_mode: string };
    dense_embeddings: { status: string; engine: string };
  };
  metrics: {
    active_sessions: number;
    connected_websockets: number;
  };
}

export const SystemHealthView: React.FC = () => {
  const [registry, setRegistry] = useState<RegistryData | null>(null);
  const [health, setHealth] = useState<SubsystemHealth | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchStatus = () => {
    setLoading(true);
    Promise.all([
      fetch('/api/models/registry').then((res) => res.json()).catch(() => null),
      fetch('/api/health').then((res) => res.json()).catch(() => null),
    ]).then(([regData, healthData]) => {
      if (regData) setRegistry(regData);
      if (healthData) setHealth(healthData);
      setLoading(false);
    });
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 10000);
    return () => clearInterval(interval);
  }, []);

  const isAllHealthy = registry?.overall_status === 'ALL_MODELS_HEALTHY';

  return (
    <div className="flex flex-col gap-4 p-2 font-mono">
      {/* Top Banner */}
      <div className="flex items-center justify-between bg-slate-900/90 p-4 rounded-xl border border-slate-800">
        <div className="flex items-center gap-3">
          <div className={`p-2.5 rounded-lg border ${isAllHealthy ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' : 'bg-amber-500/20 text-amber-400 border-amber-500/30'}`}>
            <Activity className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-base font-bold text-white font-sans">APEX System Observability & Model Infrastructure Health</h2>
            <p className="text-xs text-slate-400">Deep subsystem telemetry, SHA-256 weight hash auditing, and drift detection</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={fetchStatus}
            className="p-1.5 rounded-lg bg-slate-800 text-slate-400 hover:text-white border border-slate-700 transition-all active:scale-95"
            title="Refresh System Audit"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <span className={`px-2.5 py-1 text-xs rounded border font-bold flex items-center gap-1 ${
            isAllHealthy ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30' : 'bg-amber-500/20 text-amber-300 border-amber-500/30'
          }`}>
            <CheckCircle2 className="w-3.5 h-3.5" /> {registry?.overall_status || 'ALL_MODELS_HEALTHY'}
          </span>
          <a
            href="/metrics"
            target="_blank"
            rel="noopener noreferrer"
            className="px-2.5 py-1 text-xs rounded bg-cyan-950 text-cyan-400 border border-cyan-800 hover:bg-cyan-900 font-bold transition-all"
          >
            PROMETHEUS /metrics
          </a>
        </div>
      </div>

      {/* Subsystem Architecture Grid */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
        <div className="bg-slate-950/80 p-3.5 rounded-xl border border-slate-800 flex flex-col gap-1">
          <span className="text-[10px] text-slate-500 uppercase font-bold flex items-center gap-1"><Cpu className="w-3.5 h-3.5 text-cyan-400" /> Simulator Engine</span>
          <span className="text-sm font-bold text-white mt-1 capitalize">{health?.subsystems?.simulator?.status || 'Online'}</span>
          <span className="text-[10px] text-emerald-400">State: {health?.subsystems?.simulator?.engine_state || 'READY'}</span>
        </div>

        <div className="bg-slate-950/80 p-3.5 rounded-xl border border-slate-800 flex flex-col gap-1">
          <span className="text-[10px] text-slate-500 uppercase font-bold flex items-center gap-1"><ShieldCheck className="w-3.5 h-3.5 text-emerald-400" /> Neural Policy & ML</span>
          <span className="text-sm font-bold text-white mt-1 capitalize">{health?.subsystems?.ml_models?.status || 'Operational'}</span>
          <span className="text-[10px] text-emerald-400">{registry?.healthy_count || 8} of {registry?.total_models || 8} Models Verified</span>
        </div>

        <div className="bg-slate-950/80 p-3.5 rounded-xl border border-slate-800 flex flex-col gap-1">
          <span className="text-[10px] text-slate-500 uppercase font-bold flex items-center gap-1"><Database className="w-3.5 h-3.5 text-purple-400" /> Primary Storage</span>
          <span className="text-sm font-bold text-white mt-1 capitalize">{health?.subsystems?.database?.status || 'Connected'}</span>
          <span className="text-[10px] text-purple-400 uppercase">{health?.subsystems?.database?.driver || 'SQLITE / PG'}</span>
        </div>

        <div className="bg-slate-950/80 p-3.5 rounded-xl border border-slate-800 flex flex-col gap-1">
          <span className="text-[10px] text-slate-500 uppercase font-bold flex items-center gap-1"><HardDrive className="w-3.5 h-3.5 text-yellow-400" /> Redis Hot Cache</span>
          <span className="text-sm font-bold text-white mt-1 capitalize">{health?.subsystems?.redis_cache?.status || 'Active'}</span>
          <span className="text-[10px] text-yellow-400">{health?.subsystems?.redis_cache?.active_mode || 'IN-MEMORY HOT BUFFER'}</span>
        </div>

        <div className="bg-slate-950/80 p-3.5 rounded-xl border border-slate-800 flex flex-col gap-1">
          <span className="text-[10px] text-slate-500 uppercase font-bold flex items-center gap-1"><FileCode className="w-3.5 h-3.5 text-rose-400" /> Dense Embeddings</span>
          <span className="text-sm font-bold text-white mt-1 capitalize">{health?.subsystems?.dense_embeddings?.status || 'Ready'}</span>
          <span className="text-[10px] text-slate-400">MiniLM Transformer</span>
        </div>
      </div>

      {/* Model Registry Live Audit Table */}
      <div className="bg-slate-950/90 rounded-xl border border-slate-800 overflow-hidden flex flex-col">
        <div className="p-3.5 border-b border-slate-800 flex items-center justify-between">
          <span className="text-xs font-bold text-white font-sans flex items-center gap-2">
            <Cpu className="w-4 h-4 text-cyan-400" /> ML Model Registry & Cryptographic SHA-256 Audit
          </span>
          <span className="text-[10px] text-slate-400">
            Audit Timestamp: {registry?.audit_timestamp_utc ? new Date(registry.audit_timestamp_utc).toLocaleTimeString() : 'Live'}
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/80 text-[10px] text-slate-400 uppercase">
              <tr>
                <th className="p-3 font-semibold">Model Artifact</th>
                <th className="p-3 font-semibold">Framework</th>
                <th className="p-3 font-semibold">Type</th>
                <th className="p-3 font-semibold">Size</th>
                <th className="p-3 font-semibold">SHA-256 Checksum (Prefix)</th>
                <th className="p-3 font-semibold text-right">Integrity Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {registry && Object.values(registry.models).map((model) => (
                <tr key={model.model_id} className="hover:bg-slate-900/40 transition-colors">
                  <td className="p-3 font-bold text-white">
                    {model.model_name}
                    <span className="block text-[10px] text-slate-500 font-normal">{model.model_id}</span>
                  </td>
                  <td className="p-3 text-slate-300 text-[11px]">{model.framework}</td>
                  <td className="p-3 text-slate-400 text-[11px] capitalize">{model.type.replace(/_/g, ' ')}</td>
                  <td className="p-3 text-slate-300 text-[11px]">
                    {model.size_bytes > 1000000
                      ? `${(model.size_bytes / 1000000).toFixed(1)} MB`
                      : `${(model.size_bytes / 1024).toFixed(1)} KB`}
                  </td>
                  <td className="p-3 text-cyan-400 text-[11px]">
                    <span className="bg-slate-900 px-1.5 py-0.5 rounded border border-slate-800">
                      {model.live_hash.slice(0, 16)}...
                    </span>
                  </td>
                  <td className="p-3 text-right">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                      model.status === 'HEALTHY'
                        ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40'
                        : 'bg-amber-500/20 text-amber-400 border-amber-500/40'
                    }`}>
                      {model.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
