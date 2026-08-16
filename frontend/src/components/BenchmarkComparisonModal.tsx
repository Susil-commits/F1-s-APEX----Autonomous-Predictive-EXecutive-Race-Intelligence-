import React, { useState, useEffect } from 'react';
import { X, Trophy, Award, Gauge, Activity, RefreshCw, BarChart2, ShieldCheck, Zap } from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  Cell,
} from 'recharts';

interface PolicyMetrics {
  avg_position: number;
  win_rate_pct: number;
  podium_rate_pct: number;
  avg_gap_to_winner_s: number;
  avg_blown_tyre_laps: number;
  avg_pit_stops: number;
}

interface BenchmarkPayload {
  timestamp: string;
  total_tracks: number;
  races_per_track: number;
  total_races_evaluated: number;
  overall_summary: {
    random: PolicyMetrics;
    rule_based: PolicyMetrics;
    dqn: PolicyMetrics;
  };
  circuit_breakdown: Array<{
    track_name: string;
    num_races: number;
    policies: {
      random: PolicyMetrics;
      rule_based: PolicyMetrics;
      dqn: PolicyMetrics;
    };
  }>;
}

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export const BenchmarkComparisonModal: React.FC<Props> = ({ isOpen, onClose }) => {
  const [data, setData] = useState<BenchmarkPayload | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  const fetchBenchmarks = () => {
    setLoading(true);
    fetch('/api/benchmarks/latest')
      .then((res) => (res.ok ? res.json() : null))
      .then((payload) => {
        if (payload) setData(payload);
      })
      .catch((err) => console.error('Failed to fetch benchmarks:', err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    if (isOpen) {
      fetchBenchmarks();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const chartData = data
    ? [
        {
          name: 'Win Rate (%)',
          Random: data.overall_summary.random.win_rate_pct,
          'Rule Engine': data.overall_summary.rule_based.win_rate_pct,
          'DQN Policy': data.overall_summary.dqn.win_rate_pct,
        },
        {
          name: 'Podium Rate (%)',
          Random: data.overall_summary.random.podium_rate_pct,
          'Rule Engine': data.overall_summary.rule_based.podium_rate_pct,
          'DQN Policy': data.overall_summary.dqn.podium_rate_pct,
        },
        {
          name: 'Blown Tyre Laps (lower is better)',
          Random: data.overall_summary.random.avg_blown_tyre_laps,
          'Rule Engine': data.overall_summary.rule_based.avg_blown_tyre_laps,
          'DQN Policy': data.overall_summary.dqn.avg_blown_tyre_laps,
        },
      ]
    : [];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in font-sans">
      <div className="relative w-full max-w-4xl max-h-[90vh] overflow-y-auto bg-slate-950 border border-slate-800 rounded-2xl p-6 shadow-2xl flex flex-col gap-5 text-slate-200 font-mono text-xs">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-purple-950/60 border border-purple-800/80 text-purple-400">
              <Trophy className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-base font-black text-white tracking-wide">
                APEX STRATEGY EVALUATION BENCHMARK
              </h2>
              <p className="text-xs text-slate-400 font-sans">
                Head-to-head empirical validation: Random Baseline vs Rule Engine vs Deep Q-Network
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={fetchBenchmarks}
              disabled={loading}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-300 text-xs font-bold transition-all disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              <span>Refresh</span>
            </button>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-all"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Policy Summary Cards */}
        {data && (
          <div className="grid grid-cols-3 gap-3">
            {/* Random */}
            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col gap-2">
              <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">
                Baseline 1
              </span>
              <h4 className="text-sm font-black text-slate-300">RANDOM ACTION</h4>
              <div className="space-y-1 pt-2 border-t border-slate-800 text-[11px] font-sans">
                <div className="flex justify-between">
                  <span className="text-slate-400">Avg Finish:</span>
                  <span className="font-bold font-mono text-slate-300">P{data.overall_summary.random.avg_position}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Win Rate:</span>
                  <span className="font-bold font-mono text-rose-400">{data.overall_summary.random.win_rate_pct}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Blown Tyre Laps:</span>
                  <span className="font-bold font-mono text-rose-400">{data.overall_summary.random.avg_blown_tyre_laps}</span>
                </div>
              </div>
            </div>

            {/* Rule Engine */}
            <div className="p-4 rounded-xl bg-blue-950/30 border border-blue-800/60 flex flex-col gap-2">
              <span className="text-[10px] text-blue-400 font-bold uppercase tracking-wider">
                Baseline 2
              </span>
              <h4 className="text-sm font-black text-blue-300">RULE-BASED ENGINE</h4>
              <div className="space-y-1 pt-2 border-t border-blue-900/60 text-[11px] font-sans">
                <div className="flex justify-between">
                  <span className="text-slate-400">Avg Finish:</span>
                  <span className="font-bold font-mono text-blue-300">P{data.overall_summary.rule_based.avg_position}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Win Rate:</span>
                  <span className="font-bold font-mono text-emerald-400">{data.overall_summary.rule_based.win_rate_pct}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Blown Tyre Laps:</span>
                  <span className="font-bold font-mono text-emerald-400">{data.overall_summary.rule_based.avg_blown_tyre_laps}</span>
                </div>
              </div>
            </div>

            {/* DQN */}
            <div className="p-4 rounded-xl bg-purple-950/40 border border-purple-700/80 flex flex-col gap-2 shadow-lg shadow-purple-950/50">
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-purple-400 font-bold uppercase tracking-wider">
                  Learned Policy
                </span>
                <span className="text-[9px] bg-purple-600 text-white font-black px-1.5 py-0.5 rounded">
                  TOP POLICY
                </span>
              </div>
              <h4 className="text-sm font-black text-white">DEEP Q-NETWORK (DQN)</h4>
              <div className="space-y-1 pt-2 border-t border-purple-900/60 text-[11px] font-sans">
                <div className="flex justify-between">
                  <span className="text-slate-400">Avg Finish:</span>
                  <span className="font-bold font-mono text-cyan-300">P{data.overall_summary.dqn.avg_position}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Win Rate:</span>
                  <span className="font-bold font-mono text-emerald-400">{data.overall_summary.dqn.win_rate_pct}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Gap to Leader:</span>
                  <span className="font-bold font-mono text-emerald-400">+{data.overall_summary.dqn.avg_gap_to_winner_s}s</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Comparative Chart */}
        <div className="w-full h-56 bg-slate-900/50 p-4 rounded-xl border border-slate-800">
          <h4 className="text-[11px] font-bold text-slate-300 uppercase mb-2">
            Policy Performance Comparison
          </h4>
          <ResponsiveContainer width="100%" height="85%">
            <BarChart data={chartData}>
              <XAxis dataKey="name" stroke="#64748b" fontSize={11} />
              <YAxis stroke="#64748b" fontSize={11} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0f172a',
                  borderColor: '#334155',
                  borderRadius: '8px',
                  fontSize: '11px',
                }}
              />
              <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
              <Bar dataKey="Random" fill="#64748b" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Rule Engine" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              <Bar dataKey="DQN Policy" fill="#a855f7" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Circuit Breakdown Table */}
        {data && data.circuit_breakdown && data.circuit_breakdown.length > 0 && (
          <div>
            <h4 className="text-[11px] font-bold text-slate-300 uppercase mb-2">
              Circuit Breakdown Matrix
            </h4>
            <div className="overflow-x-auto rounded-xl border border-slate-800">
              <table className="w-full text-left text-[11px]">
                <thead className="bg-slate-900/90 text-slate-400 font-sans uppercase text-[9.5px]">
                  <tr>
                    <th className="py-2.5 px-3">Circuit</th>
                    <th className="py-2.5 px-3">Random Avg Pos</th>
                    <th className="py-2.5 px-3">Rule Engine Avg Pos</th>
                    <th className="py-2.5 px-3">DQN Avg Pos</th>
                    <th className="py-2.5 px-3">DQN Win Rate</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono">
                  {data.circuit_breakdown.map((c) => (
                    <tr key={c.track_name} className="hover:bg-slate-900/40">
                      <td className="py-2.5 px-3 font-bold text-white uppercase">{c.track_name}</td>
                      <td className="py-2.5 px-3 text-slate-400">P{c.policies.random.avg_position}</td>
                      <td className="py-2.5 px-3 text-blue-400 font-bold">P{c.policies.rule_based.avg_position}</td>
                      <td className="py-2.5 px-3 text-purple-400 font-bold">P{c.policies.dqn.avg_position}</td>
                      <td className="py-2.5 px-3 text-emerald-400 font-bold">{c.policies.dqn.win_rate_pct}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
