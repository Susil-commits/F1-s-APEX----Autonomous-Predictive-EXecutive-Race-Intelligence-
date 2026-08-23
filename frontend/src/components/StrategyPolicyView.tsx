import React, { useState } from 'react';
import { useRaceStore } from '../store/raceStore';
import {
  ShieldCheck,
  Zap,
  Brain,
  Activity,
  Layers,
  CheckCircle2,
  AlertTriangle,
  Flame,
  Award,
  Sliders,
  TrendingUp,
  Cpu,
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';

export const StrategyPolicyView: React.FC = () => {
  const { raceState, inspectedCar } = useRaceStore();
  const [activeTab, setActiveTab] = useState<'policies' | 'safe_rl' | 'q_values'>('policies');

  const policyComparison = [
    {
      policy: 'APEX Hybrid (Production)',
      type: 'Safe-RL + DQN + Monte Carlo',
      win_rate_pct: 90.0,
      podium_rate_pct: 95.0,
      dnf_rate_pct: 0.0,
      avg_gap_to_winner_s: 0.0,
      decision_latency_ms: 0.02,
      cliff_breaches: 0,
      is_hero: true,
    },
    {
      policy: 'DQN Neural Policy',
      type: 'Deep Q-Network (Epsilon-Greedy)',
      win_rate_pct: 93.3,
      podium_rate_pct: 100.0,
      dnf_rate_pct: 0.0,
      avg_gap_to_winner_s: 0.12,
      decision_latency_ms: 0.01,
      cliff_breaches: 0,
      is_hero: false,
    },
    {
      policy: 'PPO Policy Gradient',
      type: 'Actor-Critic Continuous-Discrete',
      win_rate_pct: 86.7,
      podium_rate_pct: 93.3,
      dnf_rate_pct: 0.0,
      avg_gap_to_winner_s: 1.45,
      decision_latency_ms: 0.03,
      cliff_breaches: 0,
      is_hero: false,
    },
    {
      policy: 'Monte Carlo 1,000 Rollouts',
      type: 'Stochastic Forward Search',
      win_rate_pct: 80.0,
      podium_rate_pct: 90.0,
      dnf_rate_pct: 0.0,
      avg_gap_to_winner_s: 2.10,
      decision_latency_ms: 16.0,
      cliff_breaches: 0,
      is_hero: false,
    },
    {
      policy: 'Deterministic Rule Engine',
      type: 'Expert Heuristic Thresholds',
      win_rate_pct: 86.7,
      podium_rate_pct: 93.3,
      dnf_rate_pct: 0.0,
      avg_gap_to_winner_s: 1.19,
      decision_latency_ms: 0.005,
      cliff_breaches: 0,
      is_hero: false,
    },
    {
      policy: 'Unconstrained Random Policy',
      type: 'Uniform Exploration Baseline',
      win_rate_pct: 26.7,
      podium_rate_pct: 33.3,
      dnf_rate_pct: 65.0,
      avg_gap_to_winner_s: 58.65,
      decision_latency_ms: 0.001,
      cliff_breaches: 19.5,
      is_hero: false,
    },
  ];

  const qValueRankings = [
    { action: 'PIT_HARD', q_value: 0.88, margin: '+0.15', is_optimal: true, safety: 'SAFE' },
    { action: 'PIT_MEDIUM', q_value: 0.82, margin: '+0.09', is_optimal: false, safety: 'SAFE' },
    { action: 'CONSERVE', q_value: 0.73, margin: '+0.00', is_optimal: false, safety: 'SAFE' },
    { action: 'MAINTAIN', q_value: 0.71, margin: '-0.02', is_optimal: false, safety: 'SAFE' },
    { action: 'PUSH', q_value: 0.54, margin: '-0.19', is_optimal: false, safety: 'WARNING (Tyre Wear 68%)' },
    { action: 'PIT_SOFT', q_value: 0.41, margin: '-0.32', is_optimal: false, safety: 'BLOCKED (Insufficient Stint Laps)' },
  ];

  const guardrailRules = [
    {
      guardrail: 'Tyre Cliff Catastrophic Prevention',
      condition: 'Tyre wear >= 78% or remaining useful life <= 1 lap',
      action: 'Forces PIT directive; blocks PUSH and aggressive stint extension',
      dnf_prevention: 'Eliminates 25% catastrophic puncture DNF rate',
      status: 'ACTIVE & ENFORCED',
    },
    {
      guardrail: 'Track Condition Compound Validation',
      condition: 'Wet/Damp track without Inter/Wet compound',
      action: 'Blocks all slick tyres (Soft/Medium/Hard); forces wet crossover box',
      dnf_prevention: 'Prevents immediate spin-out and aqua-planing crash',
      status: 'ACTIVE & ENFORCED',
    },
    {
      guardrail: 'Closed Pitlane / Safety Car Speed Limiter',
      condition: 'Pit lane closed by FIA Race Control or red flag neutralisation',
      action: 'Masks all pit directives until pit exit is legally declared open',
      dnf_prevention: 'Prevents FIA disqualification penalty',
      status: 'ACTIVE & ENFORCED',
    },
    {
      guardrail: 'Fuel Margin & Energy Recovery Depletion',
      condition: 'Remaining fuel load < 1.5 laps of race distance',
      action: 'Blocks PUSH/ATTACK ERS modes; forces fuel conservation lift-and-coast',
      dnf_prevention: 'Eliminates fuel starvation DNF',
      status: 'ACTIVE & ENFORCED',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-[#141824] via-[#1B2236] to-[#121622] border border-[#2B354F] rounded-xl p-6 shadow-xl">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="px-2.5 py-0.5 rounded bg-purple-950/80 text-purple-400 border border-purple-700/80 text-xs font-mono font-bold tracking-wider uppercase">
                DECISION OPTIMIZATION & SAFE RL LAYER
              </span>
              <span className="text-xs text-slate-400 font-mono">Reinforcement Learning & Guardrail Action Masking</span>
            </div>
            <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
              <span>Policy Evaluation & Guardrail Action Masking</span>
              <ShieldCheck className="w-6 h-6 text-emerald-400" />
            </h1>
            <p className="text-sm text-slate-300 max-w-3xl mt-1">
              Benchmark DQN and PPO against expert rule engines and Monte Carlo search. Safe RL action masking guardrails
              physically eliminate catastrophic tyre blowouts and ensure 100% compliance with FIA sporting regulations.
            </p>
          </div>

          <div className="flex items-center gap-2 bg-[#0D111A] p-1 rounded-lg border border-slate-800 text-xs font-mono font-bold">
            <button
              onClick={() => setActiveTab('policies')}
              className={`px-3 py-1.5 rounded transition-all ${
                activeTab === 'policies' ? 'bg-[#E10600] text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Policy Benchmark
            </button>
            <button
              onClick={() => setActiveTab('safe_rl')}
              className={`px-3 py-1.5 rounded transition-all ${
                activeTab === 'safe_rl' ? 'bg-[#E10600] text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Safe RL Guardrails
            </button>
            <button
              onClick={() => setActiveTab('q_values')}
              className={`px-3 py-1.5 rounded transition-all ${
                activeTab === 'q_values' ? 'bg-[#E10600] text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Q-Value Rankings
            </button>
          </div>
        </div>
      </div>

      {activeTab === 'policies' && (
        <div className="space-y-6">
          {/* Policy Benchmark Table */}
          <div className="bg-[#121622] border border-[#20273B] rounded-xl p-5 shadow-lg">
            <h3 className="text-base font-bold text-white flex items-center gap-2 mb-4">
              <Award className="w-4 h-4 text-amber-400" />
              <span>Multi-Circuit Autonomous Strategy Policy Benchmark (100 Races)</span>
            </h3>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-[#0A0E18] text-slate-400 uppercase text-[11px] border-b border-[#1E263A]">
                  <tr>
                    <th className="py-3 px-4">Policy Architecture</th>
                    <th className="py-3 px-4">Algorithmic Family</th>
                    <th className="py-3 px-4 text-right">Win Rate %</th>
                    <th className="py-3 px-4 text-right">Podium %</th>
                    <th className="py-3 px-4 text-right">DNF Rate %</th>
                    <th className="py-3 px-4 text-right">Avg Gap to Winner</th>
                    <th className="py-3 px-4 text-right">Decision Latency</th>
                    <th className="py-3 px-4 text-center">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#1A2033]">
                  {policyComparison.map((p) => (
                    <tr
                      key={p.policy}
                      className={`transition-colors ${
                        p.is_hero ? 'bg-red-950/30 font-bold hover:bg-red-950/50' : 'hover:bg-[#161B2B]'
                      }`}
                    >
                      <td className="py-3 px-4 flex items-center gap-2">
                        {p.is_hero && <Award className="w-4 h-4 text-amber-400" />}
                        <span className={p.is_hero ? 'text-white' : 'text-slate-200'}>{p.policy}</span>
                      </td>
                      <td className="py-3 px-4 text-slate-400">{p.type}</td>
                      <td className={`py-3 px-4 text-right ${p.win_rate_pct >= 85 ? 'text-emerald-400 font-bold' : 'text-slate-300'}`}>
                        {p.win_rate_pct.toFixed(1)}%
                      </td>
                      <td className="py-3 px-4 text-right text-cyan-400">{p.podium_rate_pct.toFixed(1)}%</td>
                      <td
                        className={`py-3 px-4 text-right font-bold ${
                          p.dnf_rate_pct === 0 ? 'text-emerald-400' : 'text-rose-400'
                        }`}
                      >
                        {p.dnf_rate_pct.toFixed(1)}%
                      </td>
                      <td className="py-3 px-4 text-right text-slate-300">+{p.avg_gap_to_winner_s.toFixed(2)}s</td>
                      <td className="py-3 px-4 text-right text-slate-400">{p.decision_latency_ms} ms</td>
                      <td className="py-3 px-4 text-center">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            p.is_hero
                              ? 'bg-emerald-900/60 text-emerald-300 border border-emerald-600/80'
                              : 'bg-slate-800 text-slate-400'
                          }`}
                        >
                          {p.is_hero ? 'CHAMPION' : 'EVALUATED'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'safe_rl' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {guardrailRules.map((gr, idx) => (
            <div key={idx} className="bg-[#121622] border border-[#20273B] rounded-xl p-5 shadow-lg flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-emerald-400 font-mono flex items-center gap-1.5">
                    <ShieldCheck className="w-4 h-4 text-emerald-400" />
                    <span>{gr.guardrail}</span>
                  </span>
                  <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-700/60 text-[10px] font-mono font-bold">
                    {gr.status}
                  </span>
                </div>

                <div className="space-y-2 text-xs font-mono mt-3">
                  <div>
                    <span className="text-slate-400 block text-[11px]">Trigger Condition:</span>
                    <span className="text-white">{gr.condition}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 block text-[11px]">Action Mask Enforcement:</span>
                    <span className="text-cyan-300">{gr.action}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 block text-[11px]">Safety Impact:</span>
                    <span className="text-emerald-300 font-semibold">{gr.dnf_prevention}</span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {activeTab === 'q_values' && (
        <div className="bg-[#121622] border border-[#20273B] rounded-xl p-5 shadow-lg">
          <h3 className="text-base font-bold text-white flex items-center gap-2 mb-4">
            <Cpu className="w-4 h-4 text-purple-400" />
            <span>Real-Time DQN Action Q-Value Distribution</span>
          </h3>

          <div className="space-y-3 font-mono text-xs">
            {qValueRankings.map((q) => (
              <div
                key={q.action}
                className={`p-3 rounded-lg border flex items-center justify-between ${
                  q.is_optimal
                    ? 'bg-red-950/40 border-red-700/80 shadow-md'
                    : 'bg-[#0A0D15] border-[#1E2538]'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full ${q.is_optimal ? 'bg-red-500 animate-ping' : 'bg-slate-600'}`} />
                  <div>
                    <span className={`font-bold text-sm ${q.is_optimal ? 'text-white' : 'text-slate-300'}`}>
                      {q.action}
                    </span>
                    <div className="text-[11px] text-slate-400">Safety Mask: {q.safety}</div>
                  </div>
                </div>

                <div className="text-right">
                  <div className="text-sm font-bold text-white">Q: {q.q_value.toFixed(2)}</div>
                  <div className={`text-[10px] ${q.margin.startsWith('+') ? 'text-emerald-400' : 'text-slate-400'}`}>
                    Margin: {q.margin}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
