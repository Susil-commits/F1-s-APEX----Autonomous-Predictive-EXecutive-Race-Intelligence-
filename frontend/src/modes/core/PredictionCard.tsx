import React, { useState } from 'react';
import { Trophy, ChevronDown, ChevronUp, Activity, Gauge, Flag, Zap, Compass, CheckCircle2 } from 'lucide-react';
import { FeatureContributionItem } from './FeatureImportanceBar';

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
  feature_contributions?: FeatureContributionItem[];
  summary_explanation: string;
}

interface PredictionCardProps {
  data: PredictionData;
}

const DRIVER_METADATA: Record<
  string,
  { number: number; color: string; country: string }
> = {
  VER: { number: 1, color: '#3671C6', country: '🇳🇱' },
  NOR: { number: 4, color: '#FF8000', country: '🇬🇧' },
  LEC: { number: 16, color: '#E80020', country: '🇲🇨' },
  HAM: { number: 44, color: '#E80020', country: '🇬🇧' },
  RUS: { number: 63, color: '#00A19B', country: '🇬🇧' },
  ANT: { number: 12, color: '#00A19B', country: '🇮🇹' },
  PIA: { number: 81, color: '#FF8000', country: '🇦🇺' },
  SAI: { number: 55, color: '#64C4FF', country: '🇪🇸' },
  ALO: { number: 14, color: '#229971', country: '🇪🇸' },
  ALB: { number: 23, color: '#64C4FF', country: '🇹🇭' },
  TSU: { number: 22, color: '#6692FF', country: '🇯🇵' },
  HUL: { number: 27, color: '#52E252', country: '🇩🇪' },
};

export const PredictionCard: React.FC<PredictionCardProps> = ({ data }) => {
  const [showStrategicDrivers, setShowStrategicDrivers] = useState<boolean>(true);

  const meta = DRIVER_METADATA[data.driver_id] || {
    number: 99,
    color: '#E10600',
    country: '🏁',
  };

  const isPodium = data.predicted_position <= 3;
  const isP1 = data.predicted_position === 1;

  const nameParts = data.driver_name.split(' ');
  const firstName = nameParts.slice(0, -1).join(' ');
  const lastName = nameParts[nameParts.length - 1] || data.driver_name;

  return (
    <div className="w-full matte-panel-elevated overflow-hidden transition-all duration-300">
      {/* Team Color Top Accent Stripe */}
      <div
        className="h-1.5 w-full"
        style={{
          background: `linear-gradient(90deg, ${meta.color} 0%, #E10600 50%, ${meta.color} 100%)`,
        }}
      />

      <div className="p-6 sm:p-8 flex flex-col gap-6">
        {/* TOP ROW: Driver Profile & Grand Prix Banner */}
        <div className="flex flex-wrap items-center justify-between gap-4 pb-6 border-b border-slate-200 dark:border-white/10">
          <div className="flex items-center gap-4 sm:gap-6">
            {/* Driver Photo Frame with Team Color Halo */}
            <div className="relative w-20 h-20 sm:w-24 sm:h-24 rounded-2xl bg-slate-100 dark:bg-white/[0.04] border border-slate-200 dark:border-white/10 flex items-center justify-center overflow-hidden flex-shrink-0">
              <div
                className="absolute inset-0 opacity-25 dark:opacity-30 blur-md pointer-events-none"
                style={{ backgroundColor: meta.color }}
              />
              <img
                src={`/f1/drivers/${data.driver_id}.png`}
                alt={data.driver_name}
                className="w-full h-full object-contain drop-shadow-md z-10 hover:scale-105 transition-transform duration-300"
                onError={(e) => {
                  const target = e.currentTarget;
                  target.style.display = 'none';
                  if (target.nextElementSibling) {
                    (target.nextElementSibling as HTMLElement).style.display = 'flex';
                  }
                }}
              />
              <div
                style={{ display: 'none' }}
                className="w-full h-full flex-col items-center justify-center z-10 font-bold"
              >
                <span className="text-2xl font-black">{meta.number}</span>
                <span className="text-[10px] text-slate-500 uppercase font-mono">{data.driver_id}</span>
              </div>
            </div>

            {/* Driver Name & Team Identity */}
            <div className="flex flex-col">
              <div className="flex items-center gap-2">
                <span className="text-base sm:text-lg">{meta.country}</span>
                <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-widest">
                  {firstName}
                </span>
              </div>
              <h2 className="text-2xl sm:text-4xl font-extrabold tracking-tight text-slate-900 dark:text-white uppercase font-['Outfit'] flex items-center gap-3">
                <span>{lastName}</span>
                {isP1 && <Trophy className="w-6 h-6 text-amber-500 fill-amber-500" />}
              </h2>
              <div className="flex items-center gap-3 mt-1.5 text-xs">
                <span
                  className="px-2.5 py-0.5 rounded-md font-bold text-white text-[11px] uppercase tracking-wider"
                  style={{ backgroundColor: meta.color }}
                >
                  {data.team_name}
                </span>
                <span className="text-slate-500 dark:text-slate-400 font-mono">
                  Starting: <strong className="text-slate-900 dark:text-white">P{data.grid_position}</strong>
                </span>
              </div>
            </div>
          </div>

          {/* Grand Prix Badge */}
          <div className="flex flex-col items-end gap-1.5">
            <div className="flex items-center gap-2">
              <span className="px-3 py-1 rounded-lg bg-slate-100 dark:bg-white/[0.04] border border-slate-200 dark:border-white/10 text-xs font-mono font-semibold uppercase text-slate-700 dark:text-slate-300">
                {data.race_id.toUpperCase()} GP
              </span>
              <span className="px-2.5 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-[10px] font-bold text-emerald-600 dark:text-emerald-400 uppercase tracking-wider">
                READY
              </span>
            </div>
            <span className="text-[11px] font-mono text-slate-400">
              Snapshot: {new Date(data.data_snapshot_utc).toLocaleTimeString()} UTC
            </span>
          </div>
        </div>

        {/* 3 CORE METRIC CARDS (ZERO ML JARGON) */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* 1. Projected Finishing Position */}
          <div className="matte-panel p-6 flex flex-col items-center justify-center text-center relative overflow-hidden">
            <span className="text-xs uppercase tracking-widest text-slate-500 dark:text-slate-400 font-bold mb-2">
              Projected Finish
            </span>
            <div className="flex items-baseline gap-1 my-1">
              <span
                className={`text-5xl sm:text-6xl font-black tracking-tight font-['Outfit'] ${
                  isP1
                    ? 'text-amber-500'
                    : isPodium
                    ? 'text-purple-600 dark:text-purple-400'
                    : 'text-slate-900 dark:text-white'
                }`}
              >
                P{data.predicted_position}
              </span>
            </div>
            <span
              className={`text-[11px] font-bold px-3 py-1 rounded-full uppercase tracking-wider mt-2 ${
                isP1
                  ? 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20'
                  : isPodium
                  ? 'bg-purple-500/10 text-purple-600 dark:text-purple-400 border border-purple-500/20'
                  : 'bg-slate-100 dark:bg-white/[0.06] text-slate-700 dark:text-slate-300'
              }`}
            >
              {isP1 ? 'RACE WIN FAVOURITE' : isPodium ? 'PODIUM CONTENDER' : 'POINTS CONTENDER'}
            </span>
          </div>

          {/* 2. Projected Finish Window */}
          <div className="matte-panel p-6 flex flex-col items-center justify-center text-center">
            <span className="text-xs uppercase tracking-widest text-slate-500 dark:text-slate-400 font-bold mb-2 flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5 text-cyan-600 dark:text-cyan-400" />
              <span>Projected Race Window</span>
            </span>
            <div className="flex items-baseline gap-3 my-1">
              <span className="text-3xl sm:text-4xl font-extrabold font-['Outfit'] text-slate-900 dark:text-white">
                P{data.confidence_interval[0]}
              </span>
              <span className="text-base text-slate-400 font-bold">—</span>
              <span className="text-3xl sm:text-4xl font-extrabold font-['Outfit'] text-slate-900 dark:text-white">
                P{data.confidence_interval[1]}
              </span>
            </div>
            <span className="text-[11px] font-medium text-slate-500 dark:text-slate-400 mt-2">
              Expected variance window under normal race pacing
            </span>
          </div>

          {/* 3. Win & Podium Odds */}
          <div className="matte-panel p-6 flex flex-col items-center justify-center text-center">
            <span className="text-xs uppercase tracking-widest text-slate-500 dark:text-slate-400 font-bold mb-2">
              Podium & Victory Odds
            </span>
            <div className="flex items-center justify-center gap-6 my-1">
              <div className="flex flex-col items-center">
                <span className="text-2xl sm:text-3xl font-extrabold text-[#E10600] font-['Outfit']">
                  {data.win_probability_pct.toFixed(1)}%
                </span>
                <span className="text-[10px] uppercase font-bold text-slate-500 dark:text-slate-400">WIN</span>
              </div>
              <div className="h-8 w-px bg-slate-200 dark:border-white/10" />
              <div className="flex flex-col items-center">
                <span className="text-2xl sm:text-3xl font-extrabold text-emerald-600 dark:text-emerald-400 font-['Outfit']">
                  {data.podium_probability_pct.toFixed(1)}%
                </span>
                <span className="text-[10px] uppercase font-bold text-slate-500 dark:text-slate-400">PODIUM</span>
              </div>
            </div>
            <span className="text-[11px] font-medium text-slate-500 dark:text-slate-400 mt-2">
              Simulated across race lap deltas
            </span>
          </div>
        </div>

        {/* Strategic Briefing Narrative */}
        <div className="p-4 rounded-xl bg-slate-50 dark:bg-white/[0.02] border-l-4 border-[#E10600] text-xs text-slate-700 dark:text-slate-300 leading-relaxed font-medium">
          <p>{data.summary_explanation}</p>
        </div>

        {/* Strategic Performance Drivers Accordion */}
        <div className="matte-panel overflow-hidden">
          <button
            type="button"
            onClick={() => setShowStrategicDrivers(!showStrategicDrivers)}
            className="w-full flex items-center justify-between px-5 py-4 bg-slate-50/50 hover:bg-slate-100/60 dark:bg-white/[0.02] dark:hover:bg-white/[0.04] text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-200 transition-colors cursor-pointer"
          >
            <div className="flex items-center gap-2.5">
              <Gauge className="w-4 h-4 text-[#E10600]" />
              <span>Key Race Performance Drivers</span>
            </div>
            {showStrategicDrivers ? (
              <ChevronUp className="w-4 h-4 text-slate-400" />
            ) : (
              <ChevronDown className="w-4 h-4 text-slate-400" />
            )}
          </button>

          {showStrategicDrivers && (
            <div className="p-5 border-t border-slate-200 dark:border-white/10 flex flex-col gap-4">
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Strategic factors evaluated prior to race start: qualifying grid position, constructor aerodynamic balance, driver current form, and track downforce profile.
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="p-3 rounded-lg bg-slate-50 dark:bg-white/[0.02] border border-slate-200 dark:border-white/10 flex items-center justify-between text-xs">
                  <span className="text-slate-600 dark:text-slate-400">Starting Grid Advantage</span>
                  <span className="font-bold text-slate-900 dark:text-white font-mono">P{data.grid_position}</span>
                </div>
                <div className="p-3 rounded-lg bg-slate-50 dark:bg-white/[0.02] border border-slate-200 dark:border-white/10 flex items-center justify-between text-xs">
                  <span className="text-slate-600 dark:text-slate-400">Constructor Chassis Pace</span>
                  <span className="font-bold text-slate-900 dark:text-white truncate max-w-[120px]">{data.team_name}</span>
                </div>
                <div className="p-3 rounded-lg bg-slate-50 dark:bg-white/[0.02] border border-slate-200 dark:border-white/10 flex items-center justify-between text-xs">
                  <span className="text-slate-600 dark:text-slate-400">Circuit Downforce Demand</span>
                  <span className="font-bold text-slate-900 dark:text-white uppercase font-mono">{data.race_id}</span>
                </div>
                <div className="p-3 rounded-lg bg-slate-50 dark:bg-white/[0.02] border border-slate-200 dark:border-white/10 flex items-center justify-between text-xs">
                  <span className="text-slate-600 dark:text-slate-400">Driver Form Trajectory</span>
                  <span className="font-bold text-emerald-600 dark:text-emerald-400">Calibrated</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Bottom Status Bar */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-4 border-t border-slate-200 dark:border-white/10 text-xs text-slate-500 dark:text-slate-400 font-mono">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
            <span>2026 World Championship Pre-Race Simulation</span>
          </div>
          <span>Engine Status: Active</span>
        </div>
      </div>
    </div>
  );
};

export default PredictionCard;
