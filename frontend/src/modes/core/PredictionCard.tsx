import React, { useState } from 'react';
import { ChevronDown, ChevronUp, ShieldCheck, Trophy, Clock, Cpu } from 'lucide-react';
import { FeatureImportanceBar, FeatureContributionItem } from './FeatureImportanceBar';

export interface PredictionData {
  race_id: string;
  driver_id: string;
  driver_name: string;
  team_name: string;
  grid_position: number;
  predicted_position: number;
  confidence_interval: [number, number];
  win_probability_pct: number;
  podium_probability_pct: number;
  model_version: string;
  data_snapshot_utc: string;
  feature_contributions: FeatureContributionItem[];
  summary_explanation: string;
}

interface PredictionCardProps {
  data: PredictionData;
}

export const PredictionCard: React.FC<PredictionCardProps> = ({ data }) => {
  const [showExplanation, setShowExplanation] = useState<boolean>(true);

  const isPodium = data.predicted_position <= 3;
  const isP1 = data.predicted_position === 1;

  return (
    <div className="w-full max-w-3xl glass-panel rounded-xl border border-[#1F2432] p-6 flex flex-col gap-6 shadow-2xl relative overflow-hidden">
      {/* Top Accent Stripe */}
      <div
        className={`absolute top-0 left-0 right-0 h-1.5 ${
          isP1 ? 'bg-gradient-to-r from-amber-400 via-rose-500 to-amber-400' : 'bg-gradient-to-r from-[#E10600] to-[#00F0FF]'
        }`}
      />

      {/* Header Info Banner */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-[#161A26] border border-[#2A3042] flex items-center justify-center text-xl font-black font-mono text-white shadow-inner">
            {data.driver_id}
          </div>
          <div>
            <h2 className="text-xl font-black text-white tracking-tight flex items-center gap-2">
              <span>{data.driver_name}</span>
              {isP1 && <Trophy className="w-5 h-5 text-amber-400" />}
            </h2>
            <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
              <span className="text-[#00F0FF]">{data.team_name}</span>
              <span>•</span>
              <span>Qualifying Grid: P{data.grid_position}</span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className="px-3 py-1 rounded bg-[#10131B] border border-[#242938] text-[11px] font-mono text-slate-300 flex items-center gap-1.5">
            <Clock className="w-3 h-3 text-[#00F0FF]" />
            <span>{new Date(data.data_snapshot_utc).toLocaleTimeString()} UTC</span>
          </div>
          <div className="px-2.5 py-1 rounded bg-emerald-950 border border-emerald-800 text-[10px] font-mono font-bold text-emerald-400 uppercase">
            CALIBRATED
          </div>
        </div>
      </div>

      {/* Centerpiece Prediction Banner */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Metric 1: Projected Finish Position */}
        <div className="bg-[#0C0E15] border border-[#202534] rounded-xl p-4 flex flex-col items-center justify-center text-center shadow-md">
          <span className="text-[10px] font-mono uppercase tracking-widest text-slate-400 font-bold">
            Projected Finish
          </span>
          <div className="flex items-baseline gap-1 my-1">
            <span className="text-4xl font-black font-mono text-white tracking-tight">
              P{data.predicted_position}
            </span>
          </div>
          <span
            className={`text-xs font-mono font-bold px-2 py-0.5 rounded ${
              isP1
                ? 'bg-amber-950 text-amber-300 border border-amber-800'
                : isPodium
                ? 'bg-purple-950 text-purple-300 border border-purple-800'
                : 'bg-slate-850 text-slate-300'
            }`}
          >
            {isP1 ? 'P1 FAVOURITE' : isPodium ? 'PODIUM CONTENDER' : 'POINTS SCORER'}
          </span>
        </div>

        {/* Metric 2: Split Conformal 90% Confidence Window */}
        <div className="bg-[#0C0E15] border border-[#202534] rounded-xl p-4 flex flex-col items-center justify-center text-center shadow-md">
          <span className="text-[10px] font-mono uppercase tracking-widest text-slate-400 font-bold">
            90% Conformal Band
          </span>
          <div className="flex items-baseline gap-1.5 my-1">
            <span className="text-2xl font-black font-mono text-white">
              P{data.confidence_interval[0]}
            </span>
            <span className="text-sm font-mono text-slate-500">to</span>
            <span className="text-2xl font-black font-mono text-white">
              P{data.confidence_interval[1]}
            </span>
          </div>
          <span className="text-[10px] font-mono text-slate-400">
            Guaranteed empirical coverage
          </span>
        </div>

        {/* Metric 3: Win & Podium Probabilities */}
        <div className="bg-[#0C0E15] border border-[#202534] rounded-xl p-4 flex flex-col items-center justify-center text-center shadow-md">
          <span className="text-[10px] font-mono uppercase tracking-widest text-slate-400 font-bold">
            Win / Podium Odds
          </span>
          <div className="flex items-baseline gap-3 my-1">
            <div className="flex flex-col">
              <span className="text-2xl font-black font-mono text-[#00F0FF]">
                {data.win_probability_pct.toFixed(1)}%
              </span>
              <span className="text-[9px] font-mono text-slate-400 uppercase">Win</span>
            </div>
            <div className="h-8 w-px bg-[#202534]" />
            <div className="flex flex-col">
              <span className="text-2xl font-black font-mono text-emerald-400">
                {data.podium_probability_pct.toFixed(1)}%
              </span>
              <span className="text-[9px] font-mono text-slate-400 uppercase">Podium</span>
            </div>
          </div>
        </div>
      </div>

      {/* Narrative Explanation */}
      <div className="bg-[#0E1119] border-l-4 border-[#E10600] rounded-r-lg p-3 text-xs text-slate-300 font-sans leading-relaxed">
        {data.summary_explanation}
      </div>

      {/* Accordion: How was this calculated? */}
      <div className="border border-[#1F2432] rounded-lg overflow-hidden bg-[#0A0C12]">
        <button
          onClick={() => setShowExplanation(!showExplanation)}
          className="w-full flex items-center justify-between px-4 py-3 bg-[#11141E] hover:bg-[#161B28] text-xs font-bold tracking-wide uppercase text-slate-200 transition-colors cursor-pointer"
        >
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-[#00F0FF]" />
            <span>How was this calculated? (Point-in-Time Feature Importances)</span>
          </div>
          {showExplanation ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>

        {showExplanation && (
          <div className="p-4 border-t border-[#1F2432] flex flex-col gap-4">
            <p className="text-xs text-slate-400">
              Computed strictly from verified pre-race inputs (Qualifying grid, 5-race rolling form, constructor points share) without race-outcome leakage.
            </p>
            <FeatureImportanceBar contributions={data.feature_contributions} />
          </div>
        )}
      </div>

      {/* Action Footer */}
      <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-[#1F2432]/60 text-xs font-mono text-slate-400">
        <div className="flex items-center gap-2">
          <Cpu className="w-4 h-4 text-[#00F0FF]" />
          <span>Model Architecture: <strong className="text-slate-200">{data.model_version}</strong></span>
        </div>
        <div className="flex items-center gap-2 text-[11px] text-slate-500">
          <span>R²=0.479 on 2024 temporal holdout</span>
        </div>
      </div>
    </div>
  );
};

export default PredictionCard;
