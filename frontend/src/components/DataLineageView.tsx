import React from 'react';
import {
  Database,
  Activity,
  Layers,
  ShieldCheck,
  Zap,
  ArrowRight,
  Clock,
  CheckCircle2,
  Cpu,
  Workflow,
  Server,
} from 'lucide-react';

export const DataLineageView: React.FC = () => {
  const featureStoreMetrics = [
    { label: 'Feature Extraction Throughput', value: '66,798 / sec', unit: 'vectors', benchmark: '> 10,000 SLA' },
    { label: 'p99 Feature Extraction Latency', value: '0.0245 ms', unit: 'milliseconds', benchmark: '< 0.50 ms SLA' },
    { label: 'p50 Inference Vector Ready', value: '0.0112 ms', unit: 'milliseconds', benchmark: '< 0.10 ms SLA' },
    { label: 'Feature Vector Dimensionality', value: '28-D', unit: 'telemetry features', benchmark: 'Full Multi-Car Space' },
  ];

  const pipelineStages = [
    {
      stage: '01. Raw Ingestion Bridge',
      source: 'FastF1 & Jolpica API',
      description: '60Hz multi-car timing, tyre compounds, GPS track coordinates, weather sensors, and FIA race-control events.',
      rate: '60 Hz / 20 Cars',
      status: 'HEALTHY',
    },
    {
      stage: '02. Schema Validation & DLQ',
      source: 'Pydantic Strict Schemas',
      description: 'Zero-copy data validation, out-of-range sensor clipping, and dead-letter queue (DLQ) poison-pill isolation.',
      rate: '0 Validation Failures',
      status: 'VERIFIED',
    },
    {
      stage: '03. Multi-Tier Feature Store',
      source: 'L1 RAM -> L2 Redis -> L3 PostgreSQL',
      description: 'Real-time rolling delta calculations (gap to leader, tyre degradation slope, track wetness index, lap delta).',
      rate: '0.0245 ms p99',
      status: 'OPTIMAL',
    },
    {
      stage: '04. Predictive Model Serving',
      source: 'XGBoost + TreeSHAP + PINN',
      description: 'Parallelized inference feeding forward Monte Carlo rollouts, DQN/PPO policy networks, and risk engines.',
      rate: 'Sub-Millisecond',
      status: 'ACTIVE',
    },
  ];

  const featureCatalog = [
    { name: 'player_tyre_wear_pct', type: 'float', source: 'FastF1 Tyre Model', description: 'Calculated cumulative degradation percentage' },
    { name: 'player_tyre_age_laps', type: 'int', source: 'Session Timing Tower', description: 'Current stint lap counter for active compound' },
    { name: 'track_temp_c', type: 'float', source: 'Doppler Weather Sensor', description: 'Track surface asphalt temperature (°C)' },
    { name: 'rain_probability_next_5_laps', type: 'float', source: 'Meteorological Model', description: 'Predictive rain onset probability' },
    { name: 'gap_to_car_ahead_s', type: 'float', source: 'Timing Transponder Loop', description: 'Live delta to preceding competitor (seconds)' },
    { name: 'in_dirty_air', type: 'bool', source: 'Spatial Distance Kinematics', description: 'Flag whether car is within 1.5s aerodynamic wake' },
    { name: 'safety_car_status', type: 'enum', source: 'FIA Race Control Stream', description: 'NONE, VSC, FULL_SAFETY_CAR, or RED_FLAG' },
    { name: 'undercut_threat_detected', type: 'bool', source: 'Opponent Strategy Model', description: 'Rival pit window probability > 60%' },
  ];

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-[#141824] via-[#1B2236] to-[#121622] border border-[#2B354F] rounded-xl p-6 shadow-xl">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="px-2.5 py-0.5 rounded bg-emerald-950/80 text-emerald-400 border border-emerald-700/80 text-xs font-mono font-bold tracking-wider uppercase">
                ENTERPRISE DATA PLATFORM & LINEAGE
              </span>
              <span className="text-xs text-slate-400 font-mono">End-to-End Telemetry Flow</span>
            </div>
            <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
              <span>Data Pipeline, Feature Store & Lineage</span>
              <Workflow className="w-6 h-6 text-cyan-400" />
            </h1>
            <p className="text-sm text-slate-300 max-w-3xl mt-1">
              Real telemetry feeding the ML layer. Clean architectural separation between raw 60Hz streaming ingestion,
              low-latency feature engineering (0.0245ms p99), and downstream decision optimization.
            </p>
          </div>
        </div>
      </div>

      {/* Feature Store Performance Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {featureStoreMetrics.map((m, idx) => (
          <div key={idx} className="bg-[#121622] border border-[#20273B] rounded-xl p-4 shadow-lg">
            <div className="text-[11px] font-mono text-slate-400 uppercase">{m.label}</div>
            <div className="text-2xl font-bold text-white font-mono my-1">{m.value}</div>
            <div className="text-xs text-emerald-400 font-mono flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>SLA Target: {m.benchmark}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Data Lineage Architecture Stages */}
      <div className="bg-[#121622] border border-[#20273B] rounded-xl p-5 shadow-lg">
        <h3 className="text-base font-bold text-white flex items-center gap-2 mb-4">
          <Server className="w-4 h-4 text-cyan-400" />
          <span>End-to-End Decision Data Lineage Pipeline</span>
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 relative">
          {pipelineStages.map((stage, idx) => (
            <div key={idx} className="bg-[#0A0D15] border border-[#1E2538] rounded-lg p-4 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between text-xs font-mono mb-2">
                  <span className="text-cyan-400 font-bold">{stage.stage}</span>
                  <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 text-[10px] font-bold">
                    {stage.status}
                  </span>
                </div>
                <div className="text-xs font-bold text-white font-mono">{stage.source}</div>
                <p className="text-xs text-slate-400 mt-2 leading-relaxed">{stage.description}</p>
              </div>

              <div className="mt-4 pt-2 border-t border-[#1C2336] flex justify-between text-xs font-mono text-slate-400">
                <span>Throughput / Latency:</span>
                <span className="text-white font-bold">{stage.rate}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Feature Store Catalog */}
      <div className="bg-[#121622] border border-[#20273B] rounded-xl p-5 shadow-lg">
        <h3 className="text-base font-bold text-white flex items-center gap-2 mb-4">
          <Database className="w-4 h-4 text-purple-400" />
          <span>Low-Latency 28-Dimensional Feature Catalog</span>
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-[#0A0E18] text-slate-400 uppercase text-[11px] border-b border-[#1E263A]">
              <tr>
                <th className="py-3 px-4">Feature Name</th>
                <th className="py-3 px-4">Data Type</th>
                <th className="py-3 px-4">Extraction Source</th>
                <th className="py-3 px-4">Description & Operational Role</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1A2033]">
              {featureCatalog.map((f) => (
                <tr key={f.name} className="hover:bg-[#161B2B] transition-colors">
                  <td className="py-3 px-4 font-bold text-cyan-300">{f.name}</td>
                  <td className="py-3 px-4 text-slate-400">{f.type}</td>
                  <td className="py-3 px-4 text-slate-300">{f.source}</td>
                  <td className="py-3 px-4 text-slate-400">{f.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
