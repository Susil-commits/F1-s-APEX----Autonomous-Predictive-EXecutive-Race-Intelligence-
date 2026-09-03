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
          <div key={item.feature || idx} className="flex flex-col gap-1.5 text-xs font-f1">
            <div className="flex items-center justify-between">
              <span className="text-slate-200 font-bold uppercase tracking-wider">{item.label}</span>
              <div className="flex items-center gap-2">
                <span
                  className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold uppercase tracking-wider ${
                    isPositive
                      ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                      : isNegative
                      ? 'bg-rose-950 text-rose-400 border border-rose-800'
                      : 'bg-slate-800 text-slate-300 border border-slate-700'
                  }`}
                >
                  {isPositive ? '▲ PACE GAIN' : isNegative ? '▼ POSITION RISK' : 'NEUTRAL'}
                </span>
                <span className="font-mono text-white font-bold w-12 text-right">
                  {item.importance_pct.toFixed(1)}%
                </span>
              </div>
            </div>

            {/* F1 High-Tech Segmented Telemetry Bar */}
            <div className="w-full bg-[#11131B] h-2.5 rounded overflow-hidden border border-[#2B2E3D] relative shadow-inner">
              <div
                className={`h-full rounded transition-all duration-700 ease-out relative ${
                  isPositive
                    ? 'bg-gradient-to-r from-emerald-500 to-[#00E676]'
                    : isNegative
                    ? 'bg-gradient-to-r from-[#B30000] via-[#E10600] to-[#FF1801]'
                    : 'bg-gradient-to-r from-cyan-600 to-[#00F0FF]'
                }`}
                style={{ width: `${Math.min(100, Math.max(10, item.importance_pct * 2.0))}%` }}
              >
                {/* Slanted inner glint */}
                <div className="absolute inset-0 bg-white/20 f1-angle" />
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default FeatureImportanceBar;
