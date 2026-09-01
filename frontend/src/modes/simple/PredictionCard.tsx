import React, { useState } from 'react';
import { ChevronDown, ChevronUp, ShieldCheck, Gauge, Trophy, ArrowRight, Clock, Cpu } from 'lucide-react';
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
  onSwitchToPitWall: () => void;
}

export const PredictionCard: React.FC<PredictionCardProps> = ({ data, onSwitchToPitWall }) => {
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

      {/* Driver Header & Metadata */}
      <div className="flex flex-wrap items-start justify-between gap-4 border-b border-[#1F2432]/80 pb-5">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-lg bg-[#151822] border border-[#2A3042] flex items-center justify-center font-mono font-black text-2xl text-white shadow-inner">
            {data.driver_id}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-2xl font-black tracking-wide text-white uppercase">{data.driver_name}</h2>
              {isPodium && (
                <span className="flex items-center gap-1 text-[11px] px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40 font-bold">
                  <Trophy className="w-3 h-3 text-amber-400" />
                  Podium Contender
                </span>
              )}
            </div>
            <p className="text-xs text-slate-400 font-medium">
              {data.team_name} · Starting Grid:{' '}
              <span className="text-white font-bold font-mono">P{data.grid_position}</span>
            </p>
          </div>
        </div>

        {/* Snapshot & Model Stamp */}
        <div className="flex flex-col items-end text-right text-[11px] text-slate-400 font-mono">
          <div className="flex items-center gap-1.5 text-slate-300">
            <Cpu className="w-3.5 h-3.5 text-[#00F0FF]" />
            <span>Model: <strong className="text-white">{data.model_version}</strong></span>
          </div>
          <div className="flex items-center gap-1.5 mt-0.5">
            <Clock className="w-3 h-3 text-slate-500" />
            <span>Snapshot: {new Date(data.data_snapshot_utc).toLocaleTimeString()} UTC</span>
          </div>
        </div>
      </div>

      {/* Main Prediction Readout */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-center">
        {/* Big P# Card */}
        <div className="md:col-span-5 flex flex-col items-center justify-center p-6 rounded-xl bg-[#0B0D14] border border-[#1F2432] relative shadow-inner text-center">
          <span className="text-[11px] uppercase tracking-widest text-slate-400 font-bold">
            Projected Finish
          </span>
          <div className="flex items-baseline justify-center gap-1 mt-1">
            <span className="text-6xl font-black tracking-tight text-white font-mono">
              P{data.predicted_position}
            </span>
          </div>

          <div className="mt-3 px-3 py-1 rounded bg-[#151924] border border-[#242A3C] text-xs font-mono text-slate-300">
            90% Range:{' '}
            <strong className="text-white font-bold">
              P{data.confidence_interval[0]} – P{data.confidence_interval[1]}
            </strong>
          </div>
        </div>

        {/* Probabilities & Confidence Metrics */}
        <div className="md:col-span-7 flex flex-col gap-3">
          <div className="grid grid-cols-2 gap-3">
            <div className="p-3.5 rounded-lg bg-[#0F121A] border border-[#1F2432]">
              <div className="text-[10px] uppercase tracking-wider text-slate-400 font-mono font-bold">
                Win Probability
              </div>
              <div className="text-2xl font-black font-mono text-white mt-1">
                {data.win_probability_pct.toFixed(1)}%
              </div>
              <div className="w-full bg-[#1A1F2C] h-1.5 rounded-full mt-2 overflow-hidden">
                <div
                  className="h-full bg-amber-400 rounded-full"
                  style={{ width: `${Math.min(100, data.win_probability_pct)}%` }}
                />
              </div>
            </div>

            <div className="p-3.5 rounded-lg bg-[#0F121A] border border-[#1F2432]">
              <div className="text-[10px] uppercase tracking-wider text-slate-400 font-mono font-bold">
                Podium Probability
              </div>
              <div className="text-2xl font-black font-mono text-white mt-1">
                {data.podium_probability_pct.toFixed(1)}%
              </div>
              <div className="w-full bg-[#1A1F2C] h-1.5 rounded-full mt-2 overflow-hidden">
                <div
                  className="h-full bg-[#00E676] rounded-full"
                  style={{ width: `${Math.min(100, data.podium_probability_pct)}%` }}
                />
              </div>
            </div>
          </div>

          {/* Model Summary Quote */}
          <div className="p-3 rounded-lg bg-[#12151E] border border-[#1F2432] text-xs text-slate-300 leading-relaxed font-sans">
            <span className="text-[#E10600] font-bold mr-1">EXECUTIVE SUMMARY:</span>
            {data.summary_explanation}
          </div>
        </div>
      </div>

      {/* Accordion: How was this calculated? */}
      <div className="border border-[#1F2432] rounded-lg overflow-hidden bg-[#0A0C12]">
        <button
          onClick={() => setShowExplanation(!showExplanation)}
          className="w-full flex items-center justify-between px-4 py-3 bg-[#11141E] hover:bg-[#161B28] text-xs font-bold tracking-wide uppercase text-slate-200 transition-colors"
        >
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-[#00F0FF]" />
            <span>How was this calculated? (Point-in-Time Factor Weights)</span>
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
      <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-[#1F2432]/60">
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <Gauge className="w-4 h-4 text-emerald-400" />
          <span>Need live tyre degradation, pit windows & counterfactuals?</span>
        </div>

        <button
          onClick={onSwitchToPitWall}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[#161A26] hover:bg-[#E10600] hover:text-white text-slate-200 border border-[#2A3042] text-xs font-bold transition-all shadow-md active:scale-95 group"
        >
          <span>Launch Pit-Wall Live Strategy</span>
          <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
        </button>
      </div>
    </div>
  );
};
