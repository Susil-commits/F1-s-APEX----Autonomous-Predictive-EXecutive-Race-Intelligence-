import React from 'react';
import { Timer, Layers, Zap, ShieldCheck, Radio } from 'lucide-react';

export type PitWallZone = 'timing' | 'strategy' | 'intelligence' | 'explainability' | 'race_ops';

interface LeftRailProps {
  activeZone: PitWallZone;
  onSelectZone: (zone: PitWallZone) => void;
}

interface ZoneMeta {
  id: PitWallZone;
  label: string;
  sublabel: string;
  icon: React.FC<{ className?: string }>;
  hotkey: string;
  badge?: string;
}

const ZONES: ZoneMeta[] = [
  {
    id: 'timing',
    label: 'Timing Tower',
    sublabel: 'Gaps, Sectors & Track Map',
    icon: Timer,
    hotkey: '1',
  },
  {
    id: 'strategy',
    label: 'Strategy Room',
    sublabel: 'Monte Carlo, Isochrones & RL',
    icon: Layers,
    hotkey: '2',
    badge: 'DQN',
  },
  {
    id: 'intelligence',
    label: 'Intelligence',
    sublabel: 'Tyres, Weather & Opponents',
    icon: Zap,
    hotkey: '3',
    badge: 'PINN',
  },
  {
    id: 'explainability',
    label: 'Trust & SHAP',
    sublabel: 'Feature Waterfall & Ablation',
    icon: ShieldCheck,
    hotkey: '4',
  },
  {
    id: 'race_ops',
    label: 'Race Ops',
    sublabel: 'Radio Comms & Debrief QA',
    icon: Radio,
    hotkey: '5',
  },
];

export const LeftRail: React.FC<LeftRailProps> = ({ activeZone, onSelectZone }) => {
  return (
    <aside className="w-64 bg-[#0A0C11] border-r border-[#1F2432] flex flex-col justify-between py-3 select-none flex-shrink-0">
      {/* Top Zone Switcher */}
      <div className="flex flex-col gap-1 px-2">
        <div className="px-3 py-1 text-[10px] font-mono uppercase tracking-widest text-slate-500 font-bold">
          Pit-Wall Workspaces
        </div>

        {ZONES.map((zone) => {
          const isActive = activeZone === zone.id;
          const Icon = zone.icon;

          return (
            <button
              key={zone.id}
              onClick={() => onSelectZone(zone.id)}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-left transition-all relative group cursor-pointer ${
                isActive
                  ? 'bg-[#151924] text-white border border-[#2D354A] shadow-md'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-[#10131B] border border-transparent'
              }`}
            >
              {/* Active Indicator Strip */}
              {isActive && (
                <div className="absolute left-0 top-1.5 bottom-1.5 w-1 rounded-r bg-[#E10600] shadow-[0_0_8px_#E10600]" />
              )}

              <div
                className={`p-1.5 rounded-md ${
                  isActive
                    ? 'bg-[#E10600]/20 text-[#E10600] border border-[#E10600]/40'
                    : 'bg-[#12151E] text-slate-400 group-hover:text-slate-200'
                }`}
              >
                <Icon className="w-4 h-4" />
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold font-sans tracking-wide truncate">
                    {zone.label}
                  </span>
                  {zone.badge && (
                    <span className="text-[9px] px-1 py-0.2 rounded bg-red-950/60 text-red-400 border border-red-800/40 font-mono font-bold">
                      {zone.badge}
                    </span>
                  )}
                </div>
                <div className="text-[10px] text-slate-500 truncate mt-0.5 font-mono">
                  {zone.sublabel}
                </div>
              </div>
            </button>
          );
        })}
      </div>

      {/* Bottom Status / Telemetry Lower Third */}
      <div className="p-3 border-t border-[#1F2432]/60 mx-2 flex flex-col gap-2">
        <div className="flex items-center justify-between text-[10px] font-mono text-slate-400">
          <span>STREAM STATUS</span>
          <span className="text-[#00E676] flex items-center gap-1 font-bold">
            <span className="w-1.5 h-1.5 rounded-full bg-[#00E676] animate-pulse" />
            SYNCHRONIZED
          </span>
        </div>
        <div className="flex items-center justify-between text-[10px] font-mono text-slate-400">
          <span>LATENCY</span>
          <span className="text-white font-bold">12ms</span>
        </div>
      </div>
    </aside>
  );
};
