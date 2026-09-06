import React from 'react';
import { CloudRain, Sun, Play } from 'lucide-react';

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
  return (
    <div className="w-full f1-card p-6 flex flex-col gap-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Starting Grid Position Selector */}
        <div className="flex flex-col gap-2.5">
          <div className="flex items-center justify-between text-xs font-f1 font-bold uppercase">
            <span className="text-slate-300">Starting Grid Slot</span>
            <span className="text-[#00F0FF] font-mono text-sm">
              {gridPosition !== '' ? `P${gridPosition}` : `P${activeDriverDefaultGrid} (Qualifying Slot)`}
            </span>
          </div>

          {/* Visual start-grid slot buttons P1 to P20 */}
          <div className="grid grid-cols-10 gap-1.5">
            {Array.from({ length: 20 }, (_, i) => i + 1).map((pos) => {
              const isCurrent = (gridPosition === '' ? activeDriverDefaultGrid : gridPosition) === pos;
              return (
                <button
                  key={pos}
                  type="button"
                  onClick={() => onGridChange(pos)}
                  className={`py-2 rounded font-mono text-xs font-black transition-all cursor-pointer ${
                    isCurrent
                      ? 'bg-[#E10600] text-white shadow-md shadow-red-600/40 scale-105'
                      : 'bg-[#151722] text-slate-300 hover:bg-[#1E2232] border border-[#262A3B]'
                  }`}
                >
                  P{pos}
                </button>
              );
            })}
          </div>
          <p className="text-[11px] font-f1 text-slate-400">
            Qualifying grid position accounts for 22.4% of total finish variance on historical holdout data.
          </p>
        </div>

        {/* Track Weather & Rain Probability */}
        <div className="flex flex-col gap-2.5">
          <div className="flex items-center justify-between text-xs font-f1 font-bold uppercase">
            <span className="text-slate-300 flex items-center gap-1.5">
              {rainForecast > 30 ? (
                <CloudRain className="w-4 h-4 text-cyan-400" />
              ) : (
                <Sun className="w-4 h-4 text-amber-400" />
              )}
              <span>Forecast Rain Probability</span>
            </span>
            <span className="text-[#00F0FF] font-mono text-sm">{rainForecast}% Rain</span>
          </div>

          <input
            type="range"
            min="0"
            max="100"
            step="5"
            value={rainForecast}
            onChange={(e) => onRainChange(Number(e.target.value))}
            className="w-full accent-[#E10600] cursor-pointer h-2 bg-[#171926] rounded-lg"
          />

          <div className="flex items-center justify-between text-[10px] font-mono text-slate-400 pt-1">
            <span className={rainForecast < 25 ? 'text-emerald-400 font-bold' : ''}>DRY (0-20%)</span>
            <span className={rainForecast >= 25 && rainForecast < 60 ? 'text-amber-400 font-bold' : ''}>
              MIXED (25-50%)
            </span>
            <span className={rainForecast >= 60 ? 'text-cyan-400 font-bold' : ''}>WET / RAIN (&gt;55%)</span>
          </div>
        </div>
      </div>

      {/* Big Official F1 Release Button */}
      <button
        type="button"
        onClick={onAnalyze}
        disabled={isAnalyzing}
        className="w-full py-4 rounded-xl f1-racing-bar hover:brightness-110 active:scale-[0.99] text-white font-black uppercase tracking-widest text-base shadow-xl shadow-red-950/70 border border-red-400/40 flex items-center justify-center gap-3 transition-all cursor-pointer font-f1"
      >
        {isAnalyzing ? (
          <div className="flex items-center gap-2">
            <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
            <span>EVALUATING CATBOOST PREDICTION MATRIX...</span>
          </div>
        ) : (
          <div className="flex items-center gap-2.5">
            <Play className="w-5 h-5 fill-current" />
            <span>CALCULATE RACE FINISH PREDICTION</span>
          </div>
        )}
      </button>
    </div>
  );
};
