import React, { useState } from 'react';
import { Trophy, Award, Medal, Flame, Star, Sparkles, CheckCircle2 } from 'lucide-react';
import confetti from 'canvas-confetti';

interface TrophyItem {
  id: string;
  name: string;
  category: string;
  year: number;
  circuit: string;
  description: string;
  tier: 'GOLD' | 'SILVER' | 'BRONZE' | 'DIAMOND';
  unlocked: boolean;
}

const TROPHY_CABINET: TrophyItem[] = [
  {
    id: 'monaco_cup',
    name: 'Grand Prix de Monaco 1st Place Golden Trophy',
    category: 'Race Winner',
    year: 2024,
    circuit: 'Circuit de Monaco 🇲🇨',
    description: 'Awarded for precision masterclass victory navigating 78 laps between the Monte Carlo barriers.',
    tier: 'GOLD',
    unlocked: true,
  },
  {
    id: 'silverstone_trophy',
    name: 'Royal Automobile Club Tourist Trophy',
    category: 'Race Winner',
    year: 2024,
    circuit: 'Silverstone Circuit 🇬🇧',
    description: 'The oldest perpetual trophy in motorsport, awarded to the British Grand Prix winner.',
    tier: 'GOLD',
    unlocked: true,
  },
  {
    id: 'monza_trophy',
    name: 'Coppa d’Oro Autodromo Nazionale Monza',
    category: 'Race Winner',
    year: 2024,
    circuit: 'Monza 🇮🇹',
    description: 'Temple of Speed victory plate awarded for high-speed low-downforce masterclass.',
    tier: 'GOLD',
    unlocked: true,
  },
  {
    id: 'wdc_trophy',
    name: "FIA Formula 1 World Drivers' Championship Cup",
    category: 'World Champion',
    year: 2024,
    circuit: 'Global Championship Season 🏆',
    description: 'The ultimate pinnacle prize in global motorsport awarded to the World Champion.',
    tier: 'DIAMOND',
    unlocked: true,
  },
  {
    id: 'dhl_pitstop',
    name: 'DHL World Fastest Pit Stop Award (1.80s)',
    category: 'Pit Crew Masterclass',
    year: 2024,
    circuit: 'APEX Pit Box ⏱️',
    description: 'World record sub-2.0s 4-wheel tire exchange synchronization award.',
    tier: 'SILVER',
    unlocked: true,
  },
  {
    id: 'pirelli_pole',
    name: 'Pirelli Pole Position Wind Tunnel Scale Tire',
    category: 'Qualifying Dominance',
    year: 2024,
    circuit: 'Q3 Shootout 🏎️',
    description: 'Engraved scale wind-tunnel tire awarded to the fastest single-lap qualifier.',
    tier: 'BRONZE',
    unlocked: true,
  },
];

export const HallOfFameTrophyRoom: React.FC = () => {
  const [selectedTrophy, setSelectedTrophy] = useState<TrophyItem>(TROPHY_CABINET[0]);

  const triggerPolish = () => {
    confetti({ particleCount: 50, spread: 60 });
  };

  return (
    <div className="w-full rounded-2xl bg-slate-950 border border-slate-800 p-4 flex flex-col gap-4 shadow-2xl">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Trophy className="w-5 h-5 text-amber-400 animate-pulse" />
          <div className="flex flex-col">
            <span className="font-bold text-white text-sm">
              FORMULA 1 CHAMPIONSHIP SILVERWARE CABINET & HALL OF FAME
            </span>
            <span className="text-[11px] font-mono text-slate-400">
              Interactive 3D trophy gallery, Grand Prix winner silverware & career career milestones
            </span>
          </div>
        </div>

        <button
          onClick={triggerPolish}
          className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-black font-mono text-xs font-bold transition-all active:scale-95 shadow-md shadow-amber-500/20"
        >
          <Sparkles className="w-4 h-4" />
          <span>Polish Silverware</span>
        </button>
      </div>

      {/* Career Stats Summary Bar */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-2.5 font-mono text-xs">
        <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] text-slate-400 uppercase">GP WINS</span>
          <span className="text-2xl font-black text-amber-400">62</span>
        </div>
        <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] text-slate-400 uppercase">POLE POSITIONS</span>
          <span className="text-2xl font-black text-apex-cyan">40</span>
        </div>
        <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] text-slate-400 uppercase">PODIUM FINISHES</span>
          <span className="text-2xl font-black text-purple-400">108</span>
        </div>
        <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] text-slate-400 uppercase">WORLD TITLES</span>
          <span className="text-2xl font-black text-amber-300">4x WDC</span>
        </div>
        <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] text-slate-400 uppercase">FASTEST LAPS</span>
          <span className="text-2xl font-black text-emerald-400">33</span>
        </div>
        <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] text-slate-400 uppercase">WIN RATE</span>
          <span className="text-2xl font-black text-rose-400">29.8%</span>
        </div>
      </div>

      {/* Main Grid: Trophy Gallery (Left 7 cols) & Showcase Dossier (Right 5 cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Trophy Cards Grid */}
        <div className="lg:col-span-7 grid grid-cols-1 sm:grid-cols-2 gap-3">
          {TROPHY_CABINET.map((trophy) => (
            <div
              key={trophy.id}
              onClick={() => setSelectedTrophy(trophy)}
              className={`p-4 rounded-xl border cursor-pointer transition-all flex flex-col justify-between gap-3 ${
                selectedTrophy.id === trophy.id
                  ? 'bg-slate-900 border-amber-400 shadow-lg shadow-amber-500/10 scale-[1.02]'
                  : 'bg-slate-900/50 border-slate-800 hover:border-slate-700'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-2.5">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-400 to-amber-600 flex items-center justify-center text-black font-black text-lg shadow-md">
                    🏆
                  </div>
                  <div className="flex flex-col">
                    <span className="font-mono text-xs font-bold text-white line-clamp-1">{trophy.name}</span>
                    <span className="text-[10px] font-mono text-slate-400">{trophy.circuit}</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between text-[10px] font-mono border-t border-slate-800/80 pt-2">
                <span className="text-slate-400">{trophy.category}</span>
                <span className="text-amber-400 font-bold">{trophy.year} Season</span>
              </div>
            </div>
          ))}
        </div>

        {/* Selected Trophy Inspector Showcase */}
        <div className="lg:col-span-5 p-5 rounded-xl bg-gradient-to-b from-slate-900 to-slate-950 border border-slate-800 flex flex-col justify-between gap-4 font-mono text-xs">
          <div className="flex flex-col gap-3">
            <div className="flex items-center gap-3 border-b border-slate-800 pb-3">
              <div className="text-4xl">🏆</div>
              <div className="flex flex-col">
                <span className="text-sm font-bold text-white">{selectedTrophy.name}</span>
                <span className="text-xs text-amber-400 font-bold">{selectedTrophy.circuit}</span>
              </div>
            </div>

            <div className="p-3 rounded-lg bg-black/60 border border-slate-800 text-slate-300 leading-relaxed font-sans text-xs">
              "{selectedTrophy.description}"
            </div>

            <div className="flex flex-col gap-1.5 text-[11px]">
              <div className="flex justify-between text-slate-400">
                <span>Award Category:</span>
                <span className="font-bold text-white">{selectedTrophy.category}</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Prestige Tier:</span>
                <span className="font-bold text-amber-300">{selectedTrophy.tier} CLASS</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Cabinet Authentication:</span>
                <span className="font-bold text-emerald-400">FIA VERIFIED SILVERWARE</span>
              </div>
            </div>
          </div>

          <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-300 text-center font-bold text-[11px]">
            Permanent Silverware Inducted into APEX Hall of Fame
          </div>
        </div>
      </div>
    </div>
  );
};
