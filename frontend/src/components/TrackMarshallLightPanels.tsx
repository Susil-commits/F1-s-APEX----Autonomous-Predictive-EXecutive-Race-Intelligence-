import React, { useState } from 'react';
import { useRaceStore } from '../store/raceStore';
import { Flag, AlertTriangle, ShieldAlert, Sparkles, CheckCircle2 } from 'lucide-react';
import confetti from 'canvas-confetti';

type PanelFlagType = 'GREEN' | 'YELLOW' | 'DOUBLE_YELLOW' | 'BLUE' | 'SLIPPERY' | 'RED' | 'MEATBALL';

interface MarshallPanel {
  id: number;
  sector: 1 | 2 | 3;
  location: string;
  flag: PanelFlagType;
}

const INITIAL_PANELS: MarshallPanel[] = [
  { id: 1, sector: 1, location: 'Turn 1 Apex Entry', flag: 'GREEN' },
  { id: 2, sector: 1, location: 'Turn 2 Exit Runoff', flag: 'GREEN' },
  { id: 3, sector: 1, location: 'Sector 1 Straight', flag: 'GREEN' },
  { id: 4, sector: 1, location: 'Turn 4 Complex', flag: 'YELLOW' },
  { id: 5, sector: 1, location: 'Sector 1 Split Line', flag: 'GREEN' },
  { id: 6, sector: 2, location: 'Turn 6 High-Speed Sweeper', flag: 'GREEN' },
  { id: 7, sector: 2, location: 'Turn 7 Hairpin Infield', flag: 'GREEN' },
  { id: 8, sector: 2, location: 'Back Straight Entry', flag: 'GREEN' },
  { id: 9, sector: 2, location: 'DRS Zone 2 Detection', flag: 'GREEN' },
  { id: 10, sector: 2, location: 'Turn 10 Heavy Braking', flag: 'GREEN' },
  { id: 11, sector: 2, location: 'Turn 11 Apex Kerb', flag: 'GREEN' },
  { id: 12, sector: 2, location: 'Sector 2 Split Line', flag: 'GREEN' },
  { id: 13, sector: 3, location: 'Turn 13 Fast Chicane', flag: 'GREEN' },
  { id: 14, sector: 3, location: 'Turn 14 Chicane Exit', flag: 'GREEN' },
  { id: 15, sector: 3, location: 'Turn 15 Technical Hairpin', flag: 'GREEN' },
  { id: 16, sector: 3, location: 'Pit Entry Commitment Line', flag: 'GREEN' },
  { id: 17, sector: 3, location: 'Final Corner Turn 17', flag: 'GREEN' },
  { id: 18, sector: 3, location: 'Main Straight Start/Finish', flag: 'GREEN' },
];

export const TrackMarshallLightPanels: React.FC = () => {
  const [panels, setPanels] = useState<MarshallPanel[]>(INITIAL_PANELS);
  const [selectedPanelId, setSelectedPanelId] = useState<number>(4);

  const activePanel = panels.find((p) => p.id === selectedPanelId) || panels[0];

  const setPanelFlag = (panelId: number, flag: PanelFlagType) => {
    setPanels((prev) =>
      prev.map((p) => (p.id === panelId ? { ...p, flag } : p))
    );
    confetti({ particleCount: 30, spread: 45 });
  };

  const getFlagVisual = (flag: PanelFlagType) => {
    switch (flag) {
      case 'GREEN':
        return 'bg-emerald-500 text-black border-emerald-400';
      case 'YELLOW':
        return 'bg-amber-400 text-black border-amber-300 animate-pulse';
      case 'DOUBLE_YELLOW':
        return 'bg-amber-500 text-black border-amber-300 animate-bounce';
      case 'BLUE':
        return 'bg-blue-600 text-white border-blue-400 animate-pulse';
      case 'SLIPPERY':
        return 'bg-gradient-to-r from-amber-400 via-rose-500 to-amber-400 text-black border-rose-400';
      case 'RED':
        return 'bg-rose-600 text-white border-rose-400 animate-pulse';
      case 'MEATBALL':
        return 'bg-black text-amber-500 border-amber-500';
      default:
        return 'bg-slate-800 text-white border-slate-700';
    }
  };

  return (
    <div className="w-full rounded-2xl bg-slate-950 border border-slate-800 p-4 flex flex-col gap-4 shadow-2xl">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Flag className="w-5 h-5 text-amber-400 animate-pulse" />
          <div className="flex flex-col">
            <span className="font-bold text-white text-sm">
              TRACK MARSHALL ELECTRONIC LED LIGHT PANELS MATRIX
            </span>
            <span className="text-[11px] font-mono text-slate-400">
              20 FIA high-intensity trackside digital flag boards, sector hazard management & blue flag triggers
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2 bg-slate-900 px-3 py-1.5 rounded-xl border border-slate-800 text-xs font-mono">
          <span className="text-slate-400">Track Circuit Status: </span>
          <strong className="text-amber-400">HAZARD IN SECTOR 1 (PANEL #4)</strong>
        </div>
      </div>

      {/* Main Grid: 18 Track Panels Grid (Left 8 cols) & Panel Controller (Right 4 cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Panel Matrix */}
        <div className="lg:col-span-8 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2.5">
          {panels.map((panel) => (
            <div
              key={panel.id}
              onClick={() => setSelectedPanelId(panel.id)}
              className={`p-3 rounded-xl border cursor-pointer transition-all flex flex-col items-center justify-between gap-2 ${
                selectedPanelId === panel.id
                  ? 'bg-slate-900 border-cyan-400 shadow-md shadow-cyan-500/20'
                  : 'bg-slate-900/50 border-slate-800 hover:border-slate-700'
              }`}
            >
              <div className="flex justify-between w-full text-[10px] font-mono text-slate-400">
                <span>P#{panel.id}</span>
                <span>S{panel.sector}</span>
              </div>

              {/* Digital LED Flag Board Emulation */}
              <div
                className={`w-full h-12 rounded-lg border-2 flex items-center justify-center font-mono font-black text-xs shadow-md ${getFlagVisual(
                  panel.flag
                )}`}
              >
                {panel.flag === 'MEATBALL' ? '🟠' : panel.flag}
              </div>

              <span className="text-[9px] font-mono text-slate-400 line-clamp-1 text-center">
                {panel.location}
              </span>
            </div>
          ))}
        </div>

        {/* Selected Panel Flag Controller */}
        <div className="lg:col-span-4 p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col justify-between gap-3 font-mono text-xs">
          <div className="flex flex-col gap-2">
            <span className="font-bold text-slate-300 uppercase border-b border-slate-800 pb-2">
              PANEL #{activePanel.id} FLAG OVERRIDE
            </span>
            <span className="text-[11px] text-slate-400">
              Location: <strong className="text-white">{activePanel.location}</strong> (Sector {activePanel.sector})
            </span>

            {/* Flag Trigger Buttons */}
            <div className="grid grid-cols-2 gap-2 mt-2">
              {(['GREEN', 'YELLOW', 'DOUBLE_YELLOW', 'BLUE', 'SLIPPERY', 'RED', 'MEATBALL'] as const).map((flag) => (
                <button
                  key={flag}
                  onClick={() => setPanelFlag(activePanel.id, flag)}
                  className={`p-2 rounded-lg border text-center transition-all ${
                    activePanel.flag === flag
                      ? 'bg-cyan-500 text-black font-black border-cyan-400 shadow-md'
                      : 'bg-slate-950 text-slate-300 border-slate-800 hover:border-slate-700'
                  }`}
                >
                  {flag}
                </button>
              ))}
            </div>
          </div>

          <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-[11px] text-slate-400 leading-relaxed">
            Directly synchronizes light board signals into oncoming drivers' steering wheel cockpit marshaling LEDs.
          </div>
        </div>
      </div>
    </div>
  );
};
