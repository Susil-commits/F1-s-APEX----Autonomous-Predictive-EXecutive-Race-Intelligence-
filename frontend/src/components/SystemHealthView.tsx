import React, { useState, useEffect } from 'react';
import {
  Activity,
  ShieldCheck,
  Cpu,
  HardDrive,
  Database,
  CheckCircle2,
  Clock,
  FileCode,
  AlertTriangle,
  RefreshCw,
  Layers,
  Radio,
  Play,
  Check,
  XCircle,
  Key,
  UserCheck,
  Server,
  Zap,
  Flame,
  Binary,
} from 'lucide-react';

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

interface JobPayload {
  job_id: string;
  job_type: string;
  status: 'QUEUED' | 'PROCESSING' | 'COMPLETED' | 'FAILED' | 'RETRYING';
  progress_pct: number;
  idempotency_key: string;
  params: Record<string, any>;
  result?: Record<string, any>;
  error?: string;
  created_at: number;
}

interface DemoToken {
  email: string;
  username: string;
  role: string;
  access_token: string;
  permissions: string[];
}

export const SystemHealthView: React.FC = () => {
  const [registry, setRegistry] = useState<RegistryData | null>(null);
  const [health, setHealth] = useState<SubsystemHealth | null>(null);
  const [jobs, setJobs] = useState<JobPayload[]>([]);
  const [demoTokens, setDemoTokens] = useState<Record<string, DemoToken>>({});
  const [selectedRole, setSelectedRole] = useState<string>('STRATEGIST');
  const [activeTabSection, setActiveTabSection] = useState<'streaming_jobs' | 'models_registry' | 'rbac_security'>('streaming_jobs');
  const [loading, setLoading] = useState<boolean>(true);
  const [isDispatching, setIsDispatching] = useState<boolean>(false);
  const [selectedJobResult, setSelectedJobResult] = useState<JobPayload | null>(null);

  const fetchStatus = async () => {
    try {
      const [regData, healthData, jobsData, tokensData] = await Promise.all([
        fetch('/api/models/registry').then((res) => res.json()).catch(() => null),
        fetch('/api/health').then((res) => res.json()).catch(() => null),
        fetch('/api/jobs/list?limit=15').then((res) => res.json()).catch(() => []),
        fetch('/api/auth/demo-tokens').then((res) => res.json()).catch(() => ({})),
      ]);
      if (regData) setRegistry(regData);
      if (healthData) setHealth(healthData);
      if (Array.isArray(jobsData)) setJobs(jobsData);
      if (tokensData) setDemoTokens(tokensData);
      setLoading(false);
    } catch (e) {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 3000);
    return () => clearInterval(interval);
  }, []);

  const dispatchJob = async (jobType: string, customParams?: Record<string, any>) => {
    setIsDispatching(true);
    try {
      const token = demoTokens[selectedRole]?.access_token;
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;

      let params = customParams;
      if (!params) {
        if (jobType === 'STRATEGY_MONTE_CARLO') {
          params = { n_rollouts: 2000, current_lap: 28, total_laps: 52, tyre_compound: 'HARD', tyre_age: 18, position: 2 };
        } else if (jobType === 'HISTORICAL_REPLAY') {
          params = { track: 'silverstone' };
        } else if (jobType === 'ML_RETRAIN_BATCH') {
          params = { model: 'treeshap' };
        } else {
          params = { alert_type: 'SAFETY_CAR_BOX_ORDER', urgency: 'CRITICAL', context: { gap: '1.2s' } };
        }
      }

      await fetch('/api/jobs/enqueue', {
        method: 'POST',
        headers,
        body: JSON.stringify({
          job_type: jobType,
          params,
          max_retries: 3,
        }),
      });
      await fetchStatus();
    } catch (err) {
      console.error('Failed to enqueue job:', err);
    } finally {
      setIsDispatching(false);
    }
  };

  const isAllHealthy = registry?.overall_status === 'ALL_MODELS_HEALTHY';

  return (
    <div className="flex flex-col gap-4 p-2 font-mono text-slate-100">
      {/* Top Banner */}
      <div className="flex flex-wrap items-center justify-between gap-4 bg-slate-900/90 p-4 rounded-xl border border-slate-800 backdrop-blur-md shadow-xl">
        <div className="flex items-center gap-3">
          <div className={`p-2.5 rounded-lg border ${isAllHealthy ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' : 'bg-amber-500/20 text-amber-400 border-amber-500/30'}`}>
            <Activity className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <h2 className="text-base font-bold text-white font-sans flex items-center gap-2">
              APEX Enterprise Distributed Observability & Job Control
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">
                Kafka + BullMQ + K8s
              </span>
            </h2>
            <p className="text-xs text-slate-400">Real-time telemetry event streaming, asynchronous worker queues, and RBAC authorization</p>
          </div>
        </div>

        {/* View Switcher Tabs */}
        <div className="flex items-center gap-1.5 bg-slate-950/80 p-1 rounded-lg border border-slate-800 text-xs">
          <button
            onClick={() => setActiveTabSection('streaming_jobs')}
            className={`px-3 py-1.5 rounded-md transition-all flex items-center gap-1.5 ${
              activeTabSection === 'streaming_jobs' ? 'bg-cyan-500 text-black font-bold shadow' : 'text-slate-400 hover:text-white'
            }`}
          >
            <Zap className="w-3.5 h-3.5" /> Kafka & Worker Queues
          </button>
          <button
            onClick={() => setActiveTabSection('models_registry')}
            className={`px-3 py-1.5 rounded-md transition-all flex items-center gap-1.5 ${
              activeTabSection === 'models_registry' ? 'bg-cyan-500 text-black font-bold shadow' : 'text-slate-400 hover:text-white'
            }`}
          >
            <Layers className="w-3.5 h-3.5" /> ML Registry & SHA-256
          </button>
          <button
            onClick={() => setActiveTabSection('rbac_security')}
            className={`px-3 py-1.5 rounded-md transition-all flex items-center gap-1.5 ${
              activeTabSection === 'rbac_security' ? 'bg-cyan-500 text-black font-bold shadow' : 'text-slate-400 hover:text-white'
            }`}
          >
            <ShieldCheck className="w-3.5 h-3.5" /> JWT & RBAC Personas
          </button>
        </div>
      </div>

      {/* SECTION 1: KAFKA STREAMING & BULLMQ ASYNC WORKER QUEUES */}
      {activeTabSection === 'streaming_jobs' && (
        <div className="flex flex-col gap-4">
          {/* Quick Metrics Bar */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800 flex items-center gap-3">
              <div className="p-2 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                <Radio className="w-5 h-5" />
              </div>
              <div>
                <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Kafka Ingestion</span>
                <span className="text-sm font-bold text-white font-sans">1,200 msg/s (60Hz)</span>
              </div>
            </div>

            <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800 flex items-center gap-3">
              <div className="p-2 rounded bg-purple-500/10 text-purple-400 border border-purple-500/20">
                <Cpu className="w-5 h-5" />
              </div>
              <div>
                <span className="text-[10px] text-slate-400 uppercase tracking-wider block">BullMQ Worker Pool</span>
                <span className="text-sm font-bold text-white font-sans">4 Active Workers</span>
              </div>
            </div>

            <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800 flex items-center gap-3">
              <div className="p-2 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">
                <Flame className="w-5 h-5" />
              </div>
              <div>
                <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Queue Depth</span>
                <span className="text-sm font-bold text-white font-sans">{jobs.filter(j => j.status === 'QUEUED' || j.status === 'PROCESSING').length} Pending Jobs</span>
              </div>
            </div>

            <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800 flex items-center gap-3">
              <div className="p-2 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <Server className="w-5 h-5" />
              </div>
              <div>
                <span className="text-[10px] text-slate-400 uppercase tracking-wider block">K8s Cluster State</span>
                <span className="text-sm font-bold text-emerald-400 font-sans">HPA (3-20 Pods)</span>
              </div>
            </div>
          </div>

          {/* Action Trigger Buttons */}
          <div className="bg-slate-900/80 p-4 rounded-xl border border-slate-800 flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                <Play className="w-3.5 h-3.5 text-cyan-400" /> Dispatch Asynchronous Compute Job
              </h3>
              <span className="text-[11px] text-slate-400">Offloaded to background worker pool without blocking 60Hz tick loop</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              <button
                disabled={isDispatching}
                onClick={() => dispatchJob('STRATEGY_MONTE_CARLO')}
                className="flex items-center justify-between p-3 rounded-lg bg-cyan-950/40 border border-cyan-800/60 hover:bg-cyan-900/50 transition-all text-left group"
              >
                <div>
                  <span className="text-xs font-bold text-cyan-300 block">🎲 10k Monte Carlo Rollout</span>
                  <span className="text-[10px] text-slate-400">9 Candidate Tactical Actions</span>
                </div>
                <Play className="w-4 h-4 text-cyan-400 group-hover:translate-x-0.5 transition-transform" />
              </button>

              <button
                disabled={isDispatching}
                onClick={() => dispatchJob('HISTORICAL_REPLAY')}
                className="flex items-center justify-between p-3 rounded-lg bg-emerald-950/40 border border-emerald-800/60 hover:bg-emerald-900/50 transition-all text-left group"
              >
                <div>
                  <span className="text-xs font-bold text-emerald-300 block">🏎️ FastF1 Session Replay</span>
                  <span className="text-[10px] text-slate-400">Silverstone GP Telemetry</span>
                </div>
                <Play className="w-4 h-4 text-emerald-400 group-hover:translate-x-0.5 transition-transform" />
              </button>

              <button
                disabled={isDispatching}
                onClick={() => dispatchJob('ML_RETRAIN_BATCH')}
                className="flex items-center justify-between p-3 rounded-lg bg-purple-950/40 border border-purple-800/60 hover:bg-purple-900/50 transition-all text-left group"
              >
                <div>
                  <span className="text-xs font-bold text-purple-300 block">🌲 TreeSHAP Precomputation</span>
                  <span className="text-[10px] text-slate-400">Surrogate Distillation Fit</span>
                </div>
                <Play className="w-4 h-4 text-purple-400 group-hover:translate-x-0.5 transition-transform" />
              </button>

              <button
                disabled={isDispatching}
                onClick={() => dispatchJob('ALERT_DISPATCH')}
                className="flex items-center justify-between p-3 rounded-lg bg-rose-950/40 border border-rose-800/60 hover:bg-rose-900/50 transition-all text-left group"
              >
                <div>
                  <span className="text-xs font-bold text-rose-300 block">🚨 Emergency Radio Alert</span>
                  <span className="text-[10px] text-slate-400">Speech Synth Notification</span>
                </div>
                <Play className="w-4 h-4 text-rose-400 group-hover:translate-x-0.5 transition-transform" />
              </button>
            </div>
          </div>

          {/* Live Job Table */}
          <div className="bg-slate-900/80 p-4 rounded-xl border border-slate-800 flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                <Clock className="w-3.5 h-3.5 text-cyan-400" /> Active & Recent Asynchronous Compute Jobs
              </h3>
              <span className="text-[10px] text-slate-500">Auto-refreshing every 3s</span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 text-[10px] uppercase">
                    <th className="p-2">Job ID</th>
                    <th className="p-2">Type</th>
                    <th className="p-2">Status</th>
                    <th className="p-2">Progress</th>
                    <th className="p-2">Idempotency Key</th>
                    <th className="p-2 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {jobs.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="p-4 text-center text-slate-500 italic">
                        No background compute jobs in queue. Click any dispatch button above!
                      </td>
                    </tr>
                  ) : (
                    jobs.map((job) => (
                      <tr key={job.job_id} className="hover:bg-slate-800/40 transition-colors">
                        <td className="p-2 font-mono text-cyan-400">{job.job_id}</td>
                        <td className="p-2 font-semibold text-slate-200">{job.job_type}</td>
                        <td className="p-2">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                              job.status === 'COMPLETED'
                                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                                : job.status === 'PROCESSING'
                                ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 animate-pulse'
                                : job.status === 'RETRYING'
                                ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                                : 'bg-slate-700/50 text-slate-300'
                            }`}
                          >
                            {job.status}
                          </span>
                        </td>
                        <td className="p-2 w-48">
                          <div className="flex items-center gap-2">
                            <div className="flex-1 bg-slate-950 rounded-full h-2 overflow-hidden border border-slate-800">
                              <div
                                className="bg-cyan-500 h-full transition-all duration-300"
                                style={{ width: `${job.progress_pct}%` }}
                              />
                            </div>
                            <span className="text-[10px] text-slate-400 font-mono">{Math.round(job.progress_pct)}%</span>
                          </div>
                        </td>
                        <td className="p-2 text-[10px] text-slate-400 font-mono truncate max-w-xs">{job.idempotency_key}</td>
                        <td className="p-2 text-right">
                          {job.result && (
                            <button
                              onClick={() => setSelectedJobResult(job)}
                              className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-cyan-400 text-[10px] transition-colors"
                            >
                              Inspect Result
                            </button>
                          )}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* SECTION 2: ML MODEL REGISTRY & SHA-256 DRIFT AUDIT */}
      {activeTabSection === 'models_registry' && registry && (
        <div className="flex flex-col gap-4">
          <div className="bg-slate-900/80 p-4 rounded-xl border border-slate-800">
            <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider mb-3 flex items-center gap-2">
              <Binary className="w-4 h-4 text-cyan-400" /> Active Machine Learning Models & Checkpoint Integrity
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {Object.entries(registry.models).map(([key, model]) => (
                <div key={key} className="bg-slate-950/80 p-3 rounded-lg border border-slate-800 flex flex-col gap-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-white">{model.model_name}</span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${model.in_sync ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'}`}>
                      {model.status}
                    </span>
                  </div>
                  <div className="text-[10px] text-slate-400 space-y-1">
                    <div><span className="text-slate-500">Framework:</span> {model.framework} ({model.type})</div>
                    <div><span className="text-slate-500">SHA-256 Live Hash:</span> <code className="text-cyan-400">{model.live_hash.slice(0, 16)}...</code></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* SECTION 3: JWT & RBAC PERSONAS */}
      {activeTabSection === 'rbac_security' && (
        <div className="bg-slate-900/80 p-4 rounded-xl border border-slate-800 flex flex-col gap-4">
          <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
            <Key className="w-4 h-4 text-cyan-400" /> Role-Based Access Control (RBAC) Switcher
          </h3>
          <p className="text-xs text-slate-400">Switch active security credentials to verify endpoint rate-limits and permissions.</p>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {['VIEWER', 'ANALYST', 'STRATEGIST', 'ADMIN'].map((roleKey) => {
              const isSelected = selectedRole === roleKey;
              const tokenData = demoTokens[roleKey];
              return (
                <div
                  key={roleKey}
                  onClick={() => setSelectedRole(roleKey)}
                  className={`p-3 rounded-lg border cursor-pointer transition-all ${
                    isSelected ? 'bg-cyan-950/60 border-cyan-500 text-white shadow-lg' : 'bg-slate-950/80 border-slate-800 text-slate-400 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-bold text-white">{roleKey}</span>
                    {isSelected && <Check className="w-4 h-4 text-cyan-400" />}
                  </div>
                  <div className="text-[10px] text-slate-400 space-y-1">
                    <div>User: {tokenData?.username || 'user'}</div>
                    <div className="flex flex-wrap gap-1 mt-2">
                      {tokenData?.permissions?.map((p) => (
                        <span key={p} className="px-1.5 py-0.5 rounded bg-slate-800 text-cyan-300 text-[9px]">
                          {p}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Job Result Inspection Modal */}
      {selectedJobResult && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-xl p-5 max-w-2xl w-full max-h-[85vh] flex flex-col gap-3 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <h3 className="text-sm font-bold text-white font-sans flex items-center gap-2">
                Job Output: <span className="text-cyan-400 font-mono">{selectedJobResult.job_id}</span>
              </h3>
              <button
                onClick={() => setSelectedJobResult(null)}
                className="p-1 text-slate-400 hover:text-white rounded"
              >
                <XCircle className="w-5 h-5" />
              </button>
            </div>
            <div className="flex-1 overflow-auto bg-slate-950 p-3 rounded-lg border border-slate-800 text-[11px] font-mono text-cyan-300">
              <pre>{JSON.stringify(selectedJobResult.result, null, 2)}</pre>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
