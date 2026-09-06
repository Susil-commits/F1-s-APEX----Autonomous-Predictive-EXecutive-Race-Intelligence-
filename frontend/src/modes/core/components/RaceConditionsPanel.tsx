import React from 'react';
import { CloudRain, Sun, Play, Sliders, Shield } from 'lucide-react';

export interface RaceConditionsPanelProps {
  gridPosition: number | '';
  rainForecast: number;
  activeDriverDefaultGrid: number;
  isAnalyzing: boolean;
  onGridChange: (grid: number) => void;
  onRainChange: (rain: number) => void;
  onAnalyze: () => void;
}

export const RaceConditionsPanel: React.FC<RaceConditionsPanelProps> = ({
  gridPosition,
  rainForecast,
  activeDriverDefaultGrid,
  isAnalyzing,
  onGridChange,
  onRainChange,
  onAnalyze,
}) => {
  const currentGrid = gridPosition === '' ? activeDriverDefaultGrid : gridPosition;

  return (
    <div className="w-full matte-panel p-6 flex flex-col gap-6">
      {/* Top Header */}
      <div className="flex items-center justify-between pb-2 border-b border-slate-200 dark:border-white/10">
        <span className="text-xs uppercase tracking-widest text-slate-500 dark:text-slate-400 font-bold flex items-center gap-2">
          <Sliders className="w-3.5 h-3.5 text-[#E10600]" />
          <span>Pre-Race Strategy Overrides</span>
        </span>
        <span className="text-[11px] font-mono text-slate-500 dark:text-slate-400">
          Tune starting grid & track meteorological conditions
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Starting Grid Position Selector */}
        <div className="flex flex-col gap-3">
          <div className="flex items-center justify-between text-xs font-bold uppercase">
            <span className="text-slate-700 dark:text-slate-300">Starting Grid Slot</span>
            <span className="text-red-600 dark:text-red-400 font-mono text-sm font-black">
              P{currentGrid} {gridPosition === '' && '(Qualifying)'}
            </span>
          </div>

          {/* Visual start-grid slot buttons P1 to P20 */}
          <div className="grid grid-cols-10 gap-1.5">
            {Array.from({ length: 20 }, (_, i) => i + 1).map((pos) => {
              const isCurrent = currentGrid === pos;
              return (
                <button
                  key={pos}
                  type="button"
                  onClick={() => onGridChange(pos)}
                  className={`py-2 rounded-lg font-mono text-xs font-bold transition-all cursor-pointer ${
                    isCurrent
                      ? 'bg-[#E10600] text-white shadow-md shadow-red-600/30 scale-105'
                      : 'bg-slate-100 hover:bg-slate-200 dark:bg-white/[0.04] dark:hover:bg-white/[0.08] text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-white/[0.08]'
                  }`}
                >
                  P{pos}
                </button>
              );
            })}
          </div>
          <p className="text-[11px] text-slate-500 dark:text-slate-400">
            Starting position on the grid strongly dictates initial race track position and clean air advantage.
          </p>
        </div>

        {/* Track Weather & Rain Probability */}
        <div className="flex flex-col gap-3">
          <div className="flex items-center justify-between text-xs font-bold uppercase">
            <span className="text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
              {rainForecast > 30 ? (
                <CloudRain className="w-4 h-4 text-cyan-600 dark:text-cyan-400" />
              ) : (
                <Sun className="w-4 h-4 text-amber-500 dark:text-amber-400" />
              )}
              <span>Forecast Track Weather</span>
            </span>
            <span className="text-cyan-600 dark:text-cyan-400 font-mono text-sm font-black">
              {rainForecast}% Rain Probability
            </span>
          </div>

          <div className="py-2">
            <input
              type="range"
              min="0"
              max="100"
              step="5"
              value={rainForecast}
              onChange={(e) => onRainChange(Number(e.target.value))}
              className="w-full accent-[#E10600] cursor-pointer h-2 bg-slate-200 dark:bg-slate-800 rounded-lg"
            />
          </div>

          <div className="flex items-center justify-between text-[11px] font-mono text-slate-500 dark:text-slate-400">
            <span className={rainForecast < 25 ? 'text-emerald-600 dark:text-emerald-400 font-bold' : ''}>
              DRY (0-20%)
            </span>
            <span
              className={
                rainForecast >= 25 && rainForecast < 60
                  ? 'text-amber-600 dark:text-amber-400 font-bold'
                  : ''
              }
            >
              MIXED CONDITIONS (25-55%)
            </span>
            <span className={rainForecast >= 60 ? 'text-cyan-600 dark:text-cyan-400 font-bold' : ''}>
              WET / INTERMEDIATES (&gt;55%)
            </span>
          </div>
        </div>
      </div>

      {/* Calculate Prediction Button */}
      <button
        type="button"
        onClick={onAnalyze}
        disabled={isAnalyzing}
        className="w-full py-4 rounded-xl btn-f1-primary flex items-center justify-center gap-3 cursor-pointer text-sm font-bold tracking-widest uppercase transition-all"
      >
        {isAnalyzing ? (
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            <span>SIMULATING RACE TELEMETRY & STRATEGY...</span>
          </div>
        ) : (
          <div className="flex items-center gap-2">
            <Play className="w-4 h-4 fill-current" />
            <span>CALCULATE RACE FINISH PREDICTION</span>
          </div>
        )}
      </button>
    </div>
  );
};

export default RaceConditionsPanel;
