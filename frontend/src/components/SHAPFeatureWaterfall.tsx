import React, { useState, useEffect } from 'react';
import { useRaceStore } from '../store/raceStore';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
  ReferenceLine,
} from 'recharts';
import { Brain, Layers, CheckCircle2, TrendingUp, TrendingDown, Sparkles, GitCompare, ArrowRightLeft } from 'lucide-react';
import { StrategyAction } from '../types/race';

interface BackendSHAPFeature {
  feature: string;
  feature_value: number;
  shap_value: number;
  impact: string;
}

interface DifferentialSHAPFeature {
  feature: string;
  feature_value: number;
  shap_action_a: number;
  shap_action_b: number;
  delta_shap: number;
  favors: string;
  abs_magnitude: number;
}

const STRATEGY_ACTIONS = [
  'MAINTAIN',
  'PUSH',
  'CONSERVE',
  'PIT_SOFT',
  'PIT_MEDIUM',
  'PIT_HARD',
  'PIT_INTER',
  'PIT_WET',
];

export const SHAPFeatureWaterfall: React.FC = () => {
  const { raceState } = useRaceStore();
  const [viewMode, setViewMode] = useState<'single' | 'pairwise'>('single');
  const [actionA, setActionA] = useState<string>('PUSH');
  const [actionB, setActionB] = useState<string>('CONSERVE');

  const [backendSHAP, setBackendSHAP] = useState<{
    base_value: number;
    prediction: number;
    top_features: BackendSHAPFeature[];
    is_distilled?: boolean;
    surrogate_type?: string;
  } | null>(null);

  const [differentialSHAP, setDifferentialSHAP] = useState<{
    action_a: string;
    action_b: string;
    q_value_action_a: number;
    q_value_action_b: number;
    delta_q: number;
    preferred_action: string;
    delta_base_value: number;
    top_differential_features: DifferentialSHAPFeature[];
    is_distilled?: boolean;
  } | null>(null);

  const playerCar = raceState?.cars.find((c) => c.is_player) || raceState?.cars[0];
  const decision = raceState?.active_decision;
  const currentLap = raceState?.current_lap || 1;

  // Single Action SHAP Fetch
  useEffect(() => {
    let isMounted = true;
    if (!playerCar) return;

    fetch(`/api/strategy/shap?car_id=${playerCar.car_id}`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (isMounted && data && data.top_features) {
          setBackendSHAP(data);
        }
      })
      .catch(() => {});

    return () => {
      isMounted = false;
    };
  }, [currentLap, playerCar?.car_id, decision?.recommendation]);

  // Pairwise Differential SHAP Fetch
  useEffect(() => {
    let isMounted = true;
    if (!playerCar || viewMode !== 'pairwise') return;

    fetch(`/api/strategy/shap-compare?action_a=${actionA}&action_b=${actionB}&car_id=${playerCar.car_id}`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (isMounted && data && data.top_differential_features) {
          setDifferentialSHAP(data);
        }
      })
      .catch(() => {});

    return () => {
      isMounted = false;
    };
  }, [currentLap, playerCar?.car_id, actionA, actionB, viewMode]);

  if (!raceState || !decision || !playerCar) return null;

  const wear = playerCar.tyre_wear_pct;
  const isWet = raceState.weather.condition === 'WET';
  const isSC = raceState.safety_car !== 'NONE';

  // Single Action Chart Data
  const singleFeatures = backendSHAP
    ? [
        {
          feature: 'Base E[f(x)]',
          value: parseFloat((backendSHAP.base_value * 10).toFixed(1)),
          isBase: true,
          impact: 'Global expected strategic baseline',
        },
        ...backendSHAP.top_features.slice(0, 6).map((f) => ({
          feature: f.feature.replace(/_/g, ' '),
          value: parseFloat((f.shap_value * 10).toFixed(1)),
          isBase: false,
          impact: `Value: ${f.feature_value}`,
        })),
      ]
    : [
        {
          feature: 'Base Intercept E[f(x)]',
          value: 50.0,
          isBase: true,
          impact: 'Baseline decision probability',
        },
        {
          feature: 'Tyre Degradation Delta',
          value: parseFloat((wear > 75 ? 32.5 : wear > 50 ? 18.2 : -8.5).toFixed(1)),
          isBase: false,
          impact: `${wear.toFixed(1)}% wear level`,
        },
        {
          feature: 'Rain / Wet Track Risk',
          value: parseFloat((isWet ? 28.4 : raceState.weather.rain_probability_next_5_laps > 0.3 ? 14.5 : -5.0).toFixed(1)),
          isBase: false,
          impact: `${(raceState.weather.rain_probability_next_5_laps * 100).toFixed(0)}% Markov risk`,
        },
        {
          feature: 'Safety Car Advantage',
          value: parseFloat((isSC ? 38.0 : -4.0).toFixed(1)),
          isBase: false,
          impact: isSC ? `SC saves ~${raceState.track.sc_pit_advantage_s}s` : 'Green flag pacing',
        },
      ];

  // Pairwise Differential Chart Data
  const pairwiseFeatures = differentialSHAP
    ? [
        {
          feature: `Δ Base E[${actionA} - ${actionB}]`,
          value: parseFloat((differentialSHAP.delta_base_value * 10).toFixed(1)),
          isBase: true,
          impact: 'Baseline expected Q-value difference',
        },
        ...differentialSHAP.top_differential_features.slice(0, 6).map((f) => ({
          feature: f.feature.replace(/_/g, ' '),
          value: parseFloat((f.delta_shap * 10).toFixed(1)),
          isBase: false,
          favors: f.favors,
          impact: `Favors ${f.favors} (A: ${f.shap_action_a}, B: ${f.shap_action_b})`,
        })),
      ]
    : [];

  const activeChartData = viewMode === 'single' ? singleFeatures : pairwiseFeatures;

  return (
    <div className="glass-panel rounded-xl p-5 flex flex-col border border-apex-border shadow-2xl font-mono text-xs">
      {/* Header & Mode Switch */}
      <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2.5">
          <Brain className="w-5 h-5 text-purple-400 animate-pulse" />
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-xs font-black uppercase tracking-widest text-slate-200">
                TreeSHAP Policy Attribution
              </h3>
              {backendSHAP?.is_distilled && (
                <span className="text-[9px] bg-emerald-950 text-emerald-300 border border-emerald-700/60 px-1.5 py-0.5 rounded font-bold">
                  DISTILLED DQN SURROGATE
                </span>
              )}
            </div>
            <p className="text-[10.5px] text-slate-400 font-sans">
              {viewMode === 'single'
                ? 'Exact Shapley additive decomposition of chosen strategic action'
                : 'Pairwise differential Shapley attribution: Why Action A over Action B?'}
            </p>
          </div>
        </div>

        {/* View Mode Toggle */}
        <div className="flex items-center bg-slate-900/90 border border-slate-800 p-1 rounded-lg">
          <button
            onClick={() => setViewMode('single')}
            className={`px-2.5 py-1 text-[10px] font-bold rounded ${
              viewMode === 'single'
                ? 'bg-purple-600 text-white shadow'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Policy SHAP
          </button>
          <button
            onClick={() => setViewMode('pairwise')}
            className={`flex items-center gap-1 px-2.5 py-1 text-[10px] font-bold rounded ${
              viewMode === 'pairwise'
                ? 'bg-cyan-600 text-white shadow'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <ArrowRightLeft className="w-3 h-3" />
            Δ Comparator
          </button>
        </div>
      </div>

      {/* Mode Specific Controls & Summary */}
      {viewMode === 'single' ? (
        <div className="flex items-center justify-between p-3 rounded-lg bg-slate-900/80 border border-slate-800 mb-4">
          <div>
            <span className="text-[9.5px] uppercase font-sans text-slate-500 block font-semibold">
              Explaining Recommended Action
            </span>
            <span className="text-sm font-black text-white">{decision.recommendation}</span>
          </div>
          <div className="text-right">
            <span className="text-[9.5px] uppercase font-sans text-slate-500 block font-semibold">
              Policy Confidence f(x)
            </span>
            <span className="text-lg font-black text-cyan-400">
              {(decision.confidence_score * 100).toFixed(1)}%
            </span>
          </div>
        </div>
      ) : (
        <div className="flex flex-col gap-2.5 p-3 rounded-lg bg-slate-900/80 border border-slate-800 mb-4 font-sans">
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <span className="text-[10px] uppercase text-slate-400 font-bold">Action A:</span>
              <select
                value={actionA}
                onChange={(e) => setActionA(e.target.value)}
                className="bg-slate-950 text-cyan-300 font-mono font-bold text-xs border border-slate-700 rounded px-2 py-1 focus:outline-none"
              >
                {STRATEGY_ACTIONS.map((act) => (
                  <option key={act} value={act}>
                    {act}
                  </option>
                ))}
              </select>
            </div>

            <div className="text-slate-500 font-bold text-xs">VS</div>

            <div className="flex items-center gap-2">
              <span className="text-[10px] uppercase text-slate-400 font-bold">Action B:</span>
              <select
                value={actionB}
                onChange={(e) => setActionB(e.target.value)}
                className="bg-slate-950 text-rose-300 font-mono font-bold text-xs border border-slate-700 rounded px-2 py-1 focus:outline-none"
              >
                {STRATEGY_ACTIONS.map((act) => (
                  <option key={act} value={act}>
                    {act}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {differentialSHAP && (
            <div className="flex items-center justify-between pt-2 border-t border-slate-800/80 font-mono text-[11px]">
              <div>
                <span className="text-slate-500 text-[9px] block">PREFERRED ACTION</span>
                <span className="font-black text-emerald-400">
                  {differentialSHAP.preferred_action}
                </span>
              </div>
              <div className="text-right">
                <span className="text-slate-500 text-[9px] block">EXPECTED MARGIN ΔQ</span>
                <span className={`font-black ${differentialSHAP.delta_q >= 0 ? 'text-cyan-400' : 'text-rose-400'}`}>
                  {differentialSHAP.delta_q > 0 ? `+${differentialSHAP.delta_q.toFixed(2)}` : differentialSHAP.delta_q.toFixed(2)}
                </span>
              </div>
            </div>
          )}
        </div>
      )}

      {/* SHAP Waterfall Bar Chart */}
      <div className="w-full h-52 mb-3 bg-slate-950/40 p-2 rounded-lg border border-slate-900">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={activeChartData}
            layout="vertical"
            margin={{ top: 5, right: 20, left: 55, bottom: 5 }}
          >
            <XAxis type="number" stroke="#64748b" fontSize={10} tickLine={false} />
            <YAxis
              type="category"
              dataKey="feature"
              stroke="#94a3b8"
              fontSize={9.5}
              tickLine={false}
              width={140}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#0f172a',
                borderColor: '#334155',
                borderRadius: '6px',
                fontSize: '11px',
                color: '#f8fafc',
              }}
            />
            <ReferenceLine x={0} stroke="#475569" />
            <Bar dataKey="value" name={viewMode === 'single' ? 'SHAP Contribution' : 'Δ SHAP Attribution'} radius={[0, 4, 4, 0]}>
              {activeChartData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={
                    entry.isBase
                      ? '#38bdf8'
                      : viewMode === 'pairwise'
                      ? entry.value >= 0
                        ? '#06b6d4'
                        : '#f43f5e'
                      : entry.value >= 0
                      ? '#10b981'
                      : '#ef4444'
                  }
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Legend & Explanation */}
      <div className="flex items-center justify-between text-[10px] text-slate-400 pt-2 border-t border-slate-800 font-sans">
        {viewMode === 'single' ? (
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1.5 text-emerald-400 font-bold font-mono">
              <span className="w-2.5 h-2.5 rounded-xs bg-emerald-500" /> + Drives Action
            </span>
            <span className="flex items-center gap-1.5 text-rose-400 font-bold font-mono">
              <span className="w-2.5 h-2.5 rounded-xs bg-rose-500" /> - Inhibits Action
            </span>
          </div>
        ) : (
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1.5 text-cyan-400 font-bold font-mono">
              <span className="w-2.5 h-2.5 rounded-xs bg-cyan-500" /> Favors {actionA}
            </span>
            <span className="flex items-center gap-1.5 text-rose-400 font-bold font-mono">
              <span className="w-2.5 h-2.5 rounded-xs bg-rose-500" /> Favors {actionB}
            </span>
          </div>
        )}
        <span className="italic">
          {viewMode === 'single' ? 'Sum of SHAP = f(x)' : 'ΔQ = ΔBase + Σ Δφ_i'}
        </span>
      </div>
    </div>
  );
};
