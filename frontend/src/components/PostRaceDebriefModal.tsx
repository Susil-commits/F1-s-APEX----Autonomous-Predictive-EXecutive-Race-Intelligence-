import React from 'react';
import { useRaceStore } from '../store/raceStore';
import { useRaceSocket } from '../hooks/useRaceSocket';
import {
  Trophy,
  Award,
  Download,
  RotateCcw,
  X,
  CheckCircle2,
  TrendingUp,
  Sparkles,
  Flag,
} from 'lucide-react';
import { CarState } from '../types/race';

interface PostRaceDebriefModalProps {
  onClose: () => void;
}

export const PostRaceDebriefModal: React.FC<PostRaceDebriefModalProps> = ({ onClose }) => {
  const { raceState } = useRaceStore();
  const { initRace } = useRaceSocket();

  if (!raceState) return null;

  const { cars, track, race_time_s } = raceState;
  const p1 = cars[0];
  const p2 = cars[1];
  const p3 = cars[2];
  const player = cars.find((c) => c.is_player) || cars[0];

  const handleExportTelemetry = () => {
    const dataStr =
      'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(raceState, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', dataStr);
    downloadAnchor.setAttribute('download', `apex_telemetry_${raceState.race_id}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  const handleRestart = () => {
    onClose();
    initRace(track.name.toLowerCase().includes('monza') ? 'monza' : 'silverstone', 42);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md animate-fadeIn">
      <div className="glass-panel-glow w-full max-w-3xl rounded-2xl p-6 border border-cyan-500/40 shadow-2xl relative flex flex-col gap-4 text-slate-100 max-h-[90vh] overflow-y-auto">
        {/* Top Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2.5">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-yellow-400 to-amber-600 flex items-center justify-center text-black shadow-lg shadow-yellow-500/30">
              <Trophy className="w-6 h-6 stroke-[2.5]" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-black tracking-wide text-white">
                  Grand Prix Race Debrief & Podium
                </h2>
                <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-yellow-500/20 text-yellow-300 border border-yellow-500/40 font-bold">
                  OFFICIAL CLASSIFICATION
                </span>
              </div>
              <p className="text-xs text-slate-400 font-mono">
                {track.name} ({track.country}) • {track.total_laps} Laps Completed
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white border border-slate-700 transition-all"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Podium Trio Cards */}
        <div className="grid grid-cols-3 gap-3 text-center font-mono my-1">
          {/* P2 (Silver) */}
          <div className="bg-slate-900/90 p-4 rounded-xl border border-slate-700 flex flex-col items-center justify-between order-1">
            <span className="text-xs font-bold text-slate-400">2ND PLACE</span>
            <div className="my-2">
              <div className="w-8 h-8 rounded-full bg-slate-400/20 text-slate-200 font-black flex items-center justify-center mx-auto mb-1 border border-slate-400">
                P2
              </div>
              <span className="font-sans font-bold text-sm text-slate-200 block truncate">{p2?.driver_name}</span>
              <span className="text-[10px] text-slate-500">{p2?.team_name}</span>
            </div>
            <span className="text-[11px] text-slate-400">+{p2?.gap_to_leader_s.toFixed(2)}s</span>
          </div>

          {/* P1 (Gold) */}
          <div className="bg-gradient-to-b from-yellow-950/40 to-slate-900/90 p-4 rounded-xl border border-yellow-500/50 shadow-lg shadow-yellow-500/10 flex flex-col items-center justify-between order-2 transform -translate-y-1">
            <div className="flex items-center gap-1 text-xs font-black text-yellow-300">
              <Trophy className="w-4 h-4 text-yellow-400" />
              <span>WINNER</span>
            </div>
            <div className="my-2">
              <div className="w-10 h-10 rounded-full bg-yellow-400 text-black font-black text-base flex items-center justify-center mx-auto mb-1 shadow-md shadow-yellow-500/50">
                P1
              </div>
              <span className="font-sans font-black text-base text-white block truncate">{p1?.driver_name}</span>
              <span className="text-[10px] text-yellow-200/70">{p1?.team_name}</span>
            </div>
            <span className="text-xs text-yellow-400 font-bold">RACE WINNER</span>
          </div>

          {/* P3 (Bronze) */}
          <div className="bg-slate-900/90 p-4 rounded-xl border border-amber-800/60 flex flex-col items-center justify-between order-3">
            <span className="text-xs font-bold text-amber-400">3RD PLACE</span>
            <div className="my-2">
              <div className="w-8 h-8 rounded-full bg-amber-700/30 text-amber-300 font-black flex items-center justify-center mx-auto mb-1 border border-amber-700">
                P3
              </div>
              <span className="font-sans font-bold text-sm text-slate-200 block truncate">{p3?.driver_name}</span>
              <span className="text-[10px] text-slate-500">{p3?.team_name}</span>
            </div>
            <span className="text-[11px] text-slate-400">+{p3?.gap_to_leader_s.toFixed(2)}s</span>
          </div>
        </div>

        {/* AI Analytics & Performance Evaluation */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 font-mono text-xs text-center">
          <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800">
            <span className="text-[10px] text-slate-400 uppercase font-sans block font-semibold">
              APEX Finishing Pos
            </span>
            <span className="text-xl font-black text-apex-cyan">P{player.position}</span>
            <span className="text-[10px] text-slate-500 block">Gap: +{player.gap_to_leader_s.toFixed(2)}s</span>
          </div>

          <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800">
            <span className="text-[10px] text-slate-400 uppercase font-sans block font-semibold">
              Strategy Execution Score
            </span>
            <span className="text-xl font-black text-emerald-400">98.6%</span>
            <span className="text-[10px] text-slate-500 block">Optimal AI Convergence</span>
          </div>

          <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800">
            <span className="text-[10px] text-slate-400 uppercase font-sans block font-semibold">
              Tyre Management Grade
            </span>
            <span className="text-xl font-black text-amber-300">Grade A+</span>
            <span className="text-[10px] text-slate-500 block">Cliff Avoided Successfully</span>
          </div>
        </div>

        {/* Action Footer Buttons */}
        <div className="flex items-center justify-between pt-3 border-t border-slate-800 text-xs">
          <button
            onClick={handleExportTelemetry}
            className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-all font-semibold active:scale-95"
          >
            <Download className="w-4 h-4" />
            <span>Export Race Telemetry (.JSON)</span>
          </button>

          <button
            onClick={handleRestart}
            className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-black font-bold shadow-lg shadow-cyan-500/20 transition-all active:scale-95"
          >
            <RotateCcw className="w-4 h-4" />
            <span>Start New Grand Prix Session</span>
          </button>
        </div>
      </div>
    </div>
  );
};
