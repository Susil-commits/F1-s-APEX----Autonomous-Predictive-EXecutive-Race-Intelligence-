import React, { useState, useEffect } from 'react';
import { History, Play, CheckCircle2, XCircle, ArrowRight, Zap } from 'lucide-react';

export const HistoricalReplayView: React.FC = () => {
  const [replays, setReplays] = useState<any[]>([]);
  const [selectedKey, setSelectedKey] = useState<string>('monaco_2023');
  const [replayData, setReplayData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    fetch('/api/replays')
      .then((res) => res.json())
      .then((data) => {
        if (data.replays) setReplays(data.replays);
      })
      .catch(() => {});
  }, []);

  const handleRunReplay = (key: string) => {
    setSelectedKey(key);
    setLoading(true);
    fetch(`/api/replays/${key}`)
      .then((res) => res.json())
      .then((data) => {
        setReplayData(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  };

  useEffect(() => {
    handleRunReplay('monaco_2023');
  }, []);

  return (
    <div className="flex flex-col gap-4 p-2 font-mono">
      <div className="flex items-center justify-between bg-slate-900/90 p-4 rounded-xl border border-slate-800">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">
            <History className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-base font-bold text-white font-sans">Historical Race Replay & Counterfactual Decision Benchmarking</h2>
            <p className="text-xs text-slate-400">Reconstructing real F1 Grand Prix critical decision points vs APEX AI</p>
          </div>
        </div>
      </div>

      {/* Replay Selector Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {replays.map((r) => (
          <button
            key={r.id}
            onClick={() => handleRunReplay(r.id)}
            className={`p-3 rounded-xl border text-left flex flex-col gap-1 transition-all ${
              selectedKey === r.id
                ? 'bg-cyan-950/70 border-cyan-500/80 shadow-lg shadow-cyan-950/50'
                : 'bg-slate-950/70 border-slate-800 hover:border-slate-700'
            }`}
          >
            <span className="text-xs font-bold text-white font-sans">{r.title}</span>
            <span className="text-[11px] text-slate-400">Circuit: {r.track.toUpperCase()} | {r.total_laps} Laps</span>
            <span className="text-[10px] text-cyan-400 mt-1">{r.event_count} Critical Strategic Decision Points</span>
          </button>
        ))}
      </div>

      {loading && (
        <div className="p-12 text-center text-slate-400 text-xs flex items-center justify-center gap-2">
          <Play className="w-4 h-4 text-cyan-400 animate-spin" />
          <span>Reconstructing historical telemetry and simulating APEX decision trees...</span>
        </div>
      )}

      {replayData && !loading && (
        <div className="flex flex-col gap-4">
          <div className="bg-slate-950/90 p-4 rounded-xl border border-slate-800 flex items-center justify-between">
            <div>
              <span className="text-xs font-bold text-white font-sans">{replayData.title}</span>
              <p className="text-[11px] text-slate-400">Evaluated {replayData.total_decisions_evaluated} Critical Decision Points</p>
            </div>
            <div className="text-right">
              <span className="text-xs text-slate-400">Agreement with Real Pit Wall</span>
              <p className="text-xl font-bold text-cyan-400">{replayData.agreement_rate_pct}%</p>
            </div>
          </div>

          <div className="space-y-3">
            {replayData.decision_points?.map((dp: any, idx: number) => (
              <div key={idx} className="bg-slate-950/90 p-4 rounded-xl border border-slate-800 flex flex-col gap-3">
                <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
                  <span className="font-bold text-cyan-400 text-xs">LAP {dp.lap} EVENT TRIGGER</span>
                  <div className="flex items-center gap-2">
                    {dp.agreement_with_real_team ? (
                      <span className="flex items-center gap-1 text-emerald-400 text-xs font-bold bg-emerald-500/20 px-2 py-0.5 rounded border border-emerald-500/30">
                        <CheckCircle2 className="w-3.5 h-3.5" /> APEX Agreed with Team
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-amber-400 text-xs font-bold bg-amber-500/20 px-2 py-0.5 rounded border border-amber-500/30">
                        <Zap className="w-3.5 h-3.5" /> APEX Strategic Divergence
                      </span>
                    )}
                  </div>
                </div>

                <p className="text-xs text-slate-200">{dp.trigger_event}</p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                  <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                    <span className="text-[10px] text-slate-500 uppercase font-bold">Real F1 Team Execution</span>
                    <p className="font-bold text-slate-200 mt-1">{dp.real_team_decision}</p>
                    <p className="text-[11px] text-slate-400 mt-1">{dp.real_outcome_description}</p>
                  </div>

                  <div className="p-3 rounded-lg bg-cyan-950/40 border border-cyan-800/50">
                    <span className="text-[10px] text-cyan-400 uppercase font-bold">APEX Autonomous Recommendation</span>
                    <p className="font-bold text-cyan-300 mt-1">{dp.apex_recommended_action} (Confidence: {Math.round(dp.apex_confidence_score * 100)}%)</p>
                    <p className="text-[11px] text-emerald-400 mt-1">Counterfactual Delta: +{dp.counterfactual_advantage_s.toFixed(1)}s saved</p>
                  </div>
                </div>

                {dp.apex_rationale && (
                  <div className="text-[11px] text-slate-400 bg-slate-900/50 p-2.5 rounded-lg border border-slate-800/60">
                    <span className="font-bold text-slate-300">APEX Rationale:</span> {dp.apex_rationale.join(' ')}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
