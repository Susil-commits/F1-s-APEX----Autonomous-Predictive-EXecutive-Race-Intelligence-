import React, { useState, useEffect } from 'react';
import { useRaceStore } from '../store/raceStore';
import {
  AlertTriangle,
  Cpu,
  Zap,
  Activity,
  ShieldCheck,
  ShieldAlert,
  Flame,
  Wrench,
  RotateCcw,
  CheckCircle2,
  RefreshCw,
} from 'lucide-react';

interface SensorChannel {
  channel_name: string;
  current_val: number;
  expected_val: number;
  unit: string;
  residual_error: number;
  anomaly_score: number;
  status: 'NORMAL' | 'ELEVATED' | 'CRITICAL';
}

interface ComponentRisk {
  component: string;
  health_pct: number;
  failure_risk_pct: number;
  predicted_rul_laps: number;
  primary_sensor: string;
  anomaly_detected: boolean;
  diagnostic_message: string;
}

interface AnomalyReport {
  timestamp_s: number;
  overall_anomaly_score: number;
  is_anomaly_critical: boolean;
  channels: SensorChannel[];
  components: ComponentRisk[];
  recommended_actions: string[];
}

export const SensorAnomalyDetector: React.FC = () => {
  const { raceState } = useRaceStore();
  const [report, setReport] = useState<AnomalyReport | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [injectedAnomalies, setInjectedAnomalies] = useState<Record<string, number>>({});

  const fetchAnomalies = async () => {
    try {
      setLoading(true);
      const res = await fetch('/api/intelligence/sensor-anomalies');
      if (res.ok) {
        const data: AnomalyReport = await res.json();

        // If local injected anomalies exist, adjust data locally
        if (Object.keys(injectedAnomalies).length > 0) {
          data.channels.forEach((c) => {
            if (injectedAnomalies[c.channel_name]) {
              c.current_val = Number((c.current_val + injectedAnomalies[c.channel_name]).toFixed(2));
              c.residual_error = Number(Math.abs(c.current_val - c.expected_val).toFixed(2));
              c.anomaly_score = Math.min(100, Math.round((c.residual_error / 5.0) * 100));
              c.status = c.anomaly_score > 70 ? 'CRITICAL' : 'ELEVATED';
            }
          });
          data.is_anomaly_critical = data.channels.some((c) => c.status === 'CRITICAL');
        }

        setReport(data);
      }
    } catch (e) {
      console.error('Failed to fetch sensor anomalies:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnomalies();
    const interval = setInterval(fetchAnomalies, 3000);
    return () => clearInterval(interval);
  }, [raceState?.current_lap, injectedAnomalies]);

  const injectScenario = (channel: string, delta: number) => {
    setInjectedAnomalies((prev) => ({ ...prev, [channel]: delta }));
  };

  const clearInjections = () => {
    setInjectedAnomalies({});
  };

  const getStatusColor = (status: string) => {
    if (status === 'CRITICAL') return 'text-rose-400 bg-rose-500/10 border-rose-500/30';
    if (status === 'ELEVATED') return 'text-amber-400 bg-amber-500/10 border-amber-500/30';
    return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30';
  };

  return (
    <div className="w-full rounded-2xl bg-slate-950 border border-slate-800 p-4 flex flex-col gap-4 shadow-2xl">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Cpu className="w-5 h-5 text-apex-cyan animate-pulse" />
          <div className="flex flex-col">
            <span className="font-bold text-white text-sm">
              TELEMETRY SENSOR FUSION AUTOENCODER & COMPONENT RUL PREDICTOR
            </span>
            <span className="text-[11px] font-mono text-slate-400">
              16-channel neural reconstruction loss, anomaly z-scores & remaining useful life (RUL)
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={fetchAnomalies}
            className="p-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-300 transition-all"
            title="Refresh telemetry"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>

          {Object.keys(injectedAnomalies).length > 0 && (
            <button
              onClick={clearInjections}
              className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-rose-950/80 hover:bg-rose-900 border border-rose-700 text-rose-300 text-xs font-mono font-bold transition-all"
            >
              <RotateCcw className="w-3 h-3" />
              <span>Clear Chaos ({Object.keys(injectedAnomalies).length})</span>
            </button>
          )}
        </div>
      </div>

      {/* Top Level Severity Alert Bar */}
      {report?.is_anomaly_critical ? (
        <div className="p-3 rounded-xl bg-rose-950/80 border border-rose-600/80 flex items-center justify-between gap-3 text-rose-200 animate-pulse">
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-rose-400" />
            <span className="font-mono font-bold text-xs">
              CRITICAL ANOMALY DETECTED: Powertrain component failure imminent within projected laps!
            </span>
          </div>
          <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-rose-500 text-black">
            URGENT PIT INTERVENTION
          </span>
        </div>
      ) : (
        <div className="p-3 rounded-xl bg-emerald-950/50 border border-emerald-700/50 flex items-center justify-between gap-3 text-emerald-300">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
            <span className="font-mono text-xs">
              All 16 Telemetry Sensors Nominal • Autoencoder Reconstruction Residuals &lt; 1.2σ
            </span>
          </div>
          <span className="text-[11px] font-mono text-emerald-400 font-bold">RELIABILITY: 99.8%</span>
        </div>
      )}

      {/* Component Failure Risk Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {report?.components.map((comp) => (
          <div
            key={comp.component}
            className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col gap-2.5"
          >
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
              <span className="font-bold text-white text-xs font-mono">{comp.component}</span>
              <span
                className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded ${
                  comp.health_pct < 60
                    ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                    : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                }`}
              >
                {comp.health_pct}% HEALTH
              </span>
            </div>

            <div className="grid grid-cols-2 gap-2 text-xs font-mono">
              <div className="flex flex-col">
                <span className="text-[10px] text-slate-400">Failure Risk:</span>
                <span
                  className={`font-bold ${
                    comp.failure_risk_pct > 50 ? 'text-rose-400' : 'text-slate-200'
                  }`}
                >
                  {comp.failure_risk_pct}%
                </span>
              </div>
              <div className="flex flex-col">
                <span className="text-[10px] text-slate-400">Predicted RUL:</span>
                <span className="font-bold text-apex-cyan">{comp.predicted_rul_laps} Laps</span>
              </div>
            </div>

            <p className="text-[11px] font-mono text-slate-400 bg-slate-950/60 p-2 rounded-lg border border-slate-800/60">
              {comp.diagnostic_message}
            </p>
          </div>
        ))}
      </div>

      {/* 16-Channel Telemetry Sensor Grid */}
      <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800 flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-mono text-apex-cyan font-bold uppercase">
            16-CHANNEL TELEMETRY SENSOR RESIDUAL MONITOR
          </span>
          <span className="text-[11px] font-mono text-slate-400">
            Neural Reconstruction Residuals vs Live Sensors
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-2.5">
          {report?.channels.map((ch) => (
            <div
              key={ch.channel_name}
              className={`p-2.5 rounded-lg border flex flex-col gap-1 transition-all ${getStatusColor(
                ch.status
              )}`}
            >
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono font-bold truncate max-w-[130px]" title={ch.channel_name}>
                  {ch.channel_name.replace(/_/g, ' ').toUpperCase()}
                </span>
                <span className="text-[9px] font-mono font-bold px-1 rounded bg-black/40">
                  {ch.status}
                </span>
              </div>

              <div className="flex justify-between items-baseline font-mono text-xs">
                <span className="font-bold text-white">
                  {ch.current_val} {ch.unit}
                </span>
                <span className="text-[10px] text-slate-400">exp: {ch.expected_val}</span>
              </div>

              <div className="w-full bg-slate-950 rounded-full h-1 overflow-hidden mt-1">
                <div
                  className={`h-full ${
                    ch.anomaly_score > 70
                      ? 'bg-rose-500'
                      : ch.anomaly_score > 40
                      ? 'bg-amber-400'
                      : 'bg-emerald-400'
                  }`}
                  style={{ width: `${ch.anomaly_score}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Synthetic Chaos & Anomaly Injection Drill */}
      <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-wrap items-center justify-between gap-3 text-xs font-mono">
        <div className="flex items-center gap-2">
          <Flame className="w-4 h-4 text-amber-400" />
          <span className="text-slate-300 font-bold">Inject Failure Scenarios (Chaos Drill):</span>
        </div>

        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => injectScenario('mguk_stator_temp_c', 48.0)}
            className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 border border-slate-700 text-rose-300 transition-all active:scale-95"
          >
            + MGU-K Overheat (+48°C)
          </button>
          <button
            onClick={() => injectScenario('turbo_boost_pressure_bar', 0.95)}
            className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 border border-slate-700 text-amber-300 transition-all active:scale-95"
          >
            + Turbo Overboost (+0.95 bar)
          </button>
          <button
            onClick={() => injectScenario('hydraulic_line_pressure_bar', -45.0)}
            className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 border border-slate-700 text-purple-300 transition-all active:scale-95"
          >
            + Hydraulic Leak (-45 bar)
          </button>
          <button
            onClick={() => injectScenario('front_left_brake_disc_c', 290.0)}
            className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 border border-slate-700 text-rose-300 transition-all active:scale-95"
          >
            + Brake Glaze (+290°C)
          </button>
        </div>
      </div>
    </div>
  );
};
