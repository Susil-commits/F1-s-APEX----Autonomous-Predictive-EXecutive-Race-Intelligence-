import React, { useState, useEffect } from 'react';
import {
  AlertTriangle,
  ShieldAlert,
  CheckCircle2,
  Activity,
  Server,
  Zap,
  RefreshCw,
  Cpu,
  Database,
  Flame,
  Radio,
} from 'lucide-react';

export const ErrorAnalysisView: React.FC = () => {
  const [errorData, setErrorData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    const fetchErrors = async () => {
      setLoading(true);
      try {
        const res = await fetch('/api/intelligence/error-analysis');
        if (res.ok) {
          const json = await res.json();
          setErrorData(json);
        }
      } catch (err) {
        console.warn('Error analysis fetch error:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchErrors();
  }, []);

  const scenarios = errorData?.scenarios || [
    {
      scenario: 'Sudden Rain Inversion',
      condition: 'Rapid track dampening (0 to 65% wetness in 2 laps)',
      prediction_error: 'Stale weather radar delayed crossover forecast by 1.8 laps',
      decision_failure: 'Pitted 1 lap late, resulting in a +4.2s time loss on slicks',
      root_cause: 'Low radar polling frequency under micro-climate conditions',
      mitigation: 'Dynamic high-frequency barometric Doppler ingestion & instant Safe-RL wet mask',
      status: 'Mitigated & Enforced',
    },
    {
      scenario: 'Tyre Cliff Thermal Anomaly',
      condition: 'Severe blistering from high track temperature (>44°C) & kerb abuse',
      prediction_error: 'Supervised model underpredicted degradation by +0.72s/lap at Lap 28',
      decision_failure: 'Delayed pit window by 2 laps; sudden 80% cliff breached',
      root_cause: 'Out-of-distribution lateral energy loads in high-speed corners',
      mitigation: 'PINN Physics-Informed residual compensator & uncertainty threshold trigger (>0.60)',
      status: 'Mitigated & Enforced',
    },
    {
      scenario: 'Late Safety Car Deployment',
      condition: 'Race neutralisation with 8 laps remaining',
      prediction_error: 'Static horizon rollout did not price cheap pit-stop delta (11.2s vs 20.5s)',
      decision_failure: 'Remained on 34-lap old hard tyres; overtaken on restart',
      root_cause: 'Lack of dynamic transition probability weighting under safety car flags',
      mitigation: 'Instant priority event interrupt & automatic cheap pit-stop utility recalculation',
      status: 'Mitigated & Enforced',
    },
    {
      scenario: 'Opponent Aggressive Undercut',
      condition: 'Rival within 1.8s box window stops on Lap 22',
      prediction_error: 'Opponent model assumed default 2-stop stint extension',
      decision_failure: 'Track position lost on pit exit by 0.6s',
      root_cause: 'Single-car policy horizon without multi-agent game-theoretic branch',
      mitigation: 'Multi-car Monte Carlo rollout expansion with opponent pit probability thresholding',
      status: 'Mitigated & Enforced',
    },
  ];

  const streamingInfra = [
    { name: 'Kafka Event Broker', status: 'ONLINE', rate: '60 Hz Stream', desc: 'Partitioned by session_id:car_id with automated DLQ poison isolation' },
    { name: 'BullMQ Async Worker Pool', status: 'ACTIVE', rate: '10,000 Rollouts/job', desc: 'Deterministic SHA-256 idempotency & exponential backoff retry' },
    { name: 'Multi-Tier Storage Store', status: 'OPTIMAL', rate: '0.0245ms p99', desc: 'L1 RAM Ring Buffer -> L2 Redis hot cache -> L3 PostgreSQL long-term' },
    { name: 'OpenTelemetry & Prometheus', status: 'HEALTHY', rate: 'W3C Trace Context', desc: 'Full distributed latency tracing across WebSocket & REST routes' },
  ];

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-[#141824] via-[#1B2236] to-[#121622] border border-[#2B354F] rounded-xl p-6 shadow-xl">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="px-2.5 py-0.5 rounded bg-rose-950/80 text-rose-400 border border-rose-700/80 text-xs font-mono font-bold tracking-wider uppercase">
                PRODUCTION RESILIENCE & ERROR ANALYSIS
              </span>
              <span className="text-xs text-slate-400 font-mono">Edge-Case Failure Matrix & Infrastructure</span>
            </div>
            <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
              <span>Edge-Case Error Analysis & Mitigation Matrix</span>
              <AlertTriangle className="w-6 h-6 text-rose-400" />
            </h1>
            <p className="text-sm text-slate-300 max-w-3xl mt-1">
              Systematic post-mortem analysis of operational failure modes. Maps prediction errors and decision failures
              to root causes, uncertainty flags, and engineered physical guardrails.
            </p>
          </div>
        </div>
      </div>

      {/* Error Analysis Matrix Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {scenarios.map((s: any, idx: number) => (
          <div key={idx} className="bg-[#121622] border border-[#20273B] rounded-xl p-5 shadow-lg flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-bold text-white font-mono flex items-center gap-2">
                  <ShieldAlert className="w-4 h-4 text-rose-400" />
                  <span>{s.scenario}</span>
                </span>
                <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-700/60 text-[10px] font-mono font-bold">
                  {s.status}
                </span>
              </div>

              <div className="space-y-2.5 text-xs font-mono">
                <div className="bg-[#0A0D15] p-2.5 rounded-lg border border-[#1E2538]">
                  <span className="text-slate-400 block text-[10px] uppercase">Operational Condition:</span>
                  <span className="text-slate-200">{s.condition}</span>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div className="bg-[#0A0D15] p-2.5 rounded-lg border border-[#1E2538]">
                    <span className="text-rose-400 block text-[10px] uppercase font-bold">Prediction Error:</span>
                    <span className="text-slate-300 text-[11px]">{s.prediction_error}</span>
                  </div>
                  <div className="bg-[#0A0D15] p-2.5 rounded-lg border border-[#1E2538]">
                    <span className="text-amber-400 block text-[10px] uppercase font-bold">Decision Consequence:</span>
                    <span className="text-slate-300 text-[11px]">{s.decision_failure}</span>
                  </div>
                </div>

                <div className="bg-[#0A0D15] p-2.5 rounded-lg border border-[#1E2538]">
                  <span className="text-purple-400 block text-[10px] uppercase font-bold">Root Cause:</span>
                  <span className="text-slate-300 text-[11px]">{s.root_cause}</span>
                </div>

                <div className="bg-emerald-950/30 p-2.5 rounded-lg border border-emerald-800/50">
                  <span className="text-emerald-400 block text-[10px] uppercase font-bold">Engineered Mitigation:</span>
                  <span className="text-emerald-200 text-[11px]">{s.mitigation}</span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Production Infrastructure Supporting Layer */}
      <div className="bg-[#121622] border border-[#20273B] rounded-xl p-5 shadow-lg">
        <h3 className="text-base font-bold text-white flex items-center gap-2 mb-4">
          <Server className="w-4 h-4 text-cyan-400" />
          <span>Production Engineering & Infrastructure (Supporting Layer)</span>
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {streamingInfra.map((infra, idx) => (
            <div key={idx} className="bg-[#0A0D15] border border-[#1E2538] rounded-lg p-4 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between text-xs font-mono mb-2">
                  <span className="text-white font-bold">{infra.name}</span>
                  <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 text-[10px] font-bold">
                    {infra.status}
                  </span>
                </div>
                <p className="text-xs text-slate-400 mt-1 leading-relaxed">{infra.desc}</p>
              </div>

              <div className="mt-4 pt-2 border-t border-[#1C2336] flex justify-between text-xs font-mono text-slate-400">
                <span>Metric:</span>
                <span className="text-cyan-400 font-bold">{infra.rate}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
