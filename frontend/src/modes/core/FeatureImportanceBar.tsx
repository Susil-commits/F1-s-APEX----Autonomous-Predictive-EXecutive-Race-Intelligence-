import React from 'react';

export interface FeatureContributionItem {
  feature: string;
  label: string;
  value: number;
  importance_pct: number;
  direction: 'improves_finish' | 'hurts_finish' | 'neutral' | string;
}

interface FeatureImportanceBarProps {
  contributions: FeatureContributionItem[];
}

export const FeatureImportanceBar: React.FC<FeatureImportanceBarProps> = ({ contributions }) => {
  return (
    <div className="flex flex-col gap-3 w-full">
      {contributions.map((item, idx) => {
        const isPositive = item.direction === 'improves_finish';
        const isNegative = item.direction === 'hurts_finish';

        return (
          <div key={item.feature || idx} className="flex flex-col gap-1 text-xs">
            <div className="flex items-center justify-between font-mono">
              <span className="text-slate-200 font-medium">{item.label}</span>
              <div className="flex items-center gap-2">
                <span
                  className={`text-[10px] px-1.5 py-0.5 rounded font-bold uppercase ${
                    isPositive
                      ? 'bg-emerald-950/80 text-emerald-400 border border-emerald-800/60'
                      : isNegative
                      ? 'bg-rose-950/80 text-rose-400 border border-rose-800/60'
                      : 'bg-slate-800 text-slate-400'
                  }`}
                >
                  {isPositive ? '+ Pace Advantage' : isNegative ? '- Grid / Track Penalty' : 'Neutral'}
                </span>
                <span className="text-slate-400 w-12 text-right">{item.importance_pct.toFixed(1)}%</span>
              </div>
            </div>

            {/* Progress bar */}
            <div className="w-full bg-[#12151E] h-2 rounded-full overflow-hidden border border-[#1F2432]">
              <div
                className={`h-full rounded-full transition-all duration-700 ease-out ${
                  isPositive ? 'bg-[#00E676]' : isNegative ? 'bg-[#E10600]' : 'bg-[#00F0FF]'
                }`}
                style={{ width: `${Math.min(100, Math.max(8, item.importance_pct * 2.2))}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
};
