import React, { useState } from 'react';
import { useRaceStore } from '../store/raceStore';
import { DollarSign, UserCheck, Award, ShieldCheck, ArrowRightLeft, Sparkles, CheckCircle2 } from 'lucide-react';
import confetti from 'canvas-confetti';

interface DriverMarketProfile {
  id: string;
  name: string;
  country: string;
  flag: string;
  currentTeam: string;
  marketValueMillions: number;
  salaryMillions: number;
  superlicensePoints: number;
  paceRating: number;
  experienceYears: number;
  contractUntil: number;
}

const DRIVER_ROSTER: DriverMarketProfile[] = [
  {
    id: 'verstappen',
    name: 'Max Verstappen',
    country: 'Netherlands',
    flag: '🇳🇱',
    currentTeam: 'Red Bull Racing',
    marketValueMillions: 65,
    salaryMillions: 55,
    superlicensePoints: 85,
    paceRating: 99,
    experienceYears: 10,
    contractUntil: 2028,
  },
  {
    id: 'leclerc',
    name: 'Charles Leclerc',
    country: 'Monaco',
    flag: '🇲🇨',
    currentTeam: 'Scuderia Ferrari',
    marketValueMillions: 45,
    salaryMillions: 34,
    superlicensePoints: 72,
    paceRating: 97,
    experienceYears: 7,
    contractUntil: 2029,
  },
  {
    id: 'norris',
    name: 'Lando Norris',
    country: 'Great Britain',
    flag: '🇬🇧',
    currentTeam: 'McLaren',
    marketValueMillions: 40,
    salaryMillions: 28,
    superlicensePoints: 68,
    paceRating: 96,
    experienceYears: 6,
    contractUntil: 2027,
  },
  {
    id: 'hamilton',
    name: 'Lewis Hamilton',
    country: 'Great Britain',
    flag: '🇬🇧',
    currentTeam: 'Scuderia Ferrari',
    marketValueMillions: 50,
    salaryMillions: 50,
    superlicensePoints: 95,
    paceRating: 97,
    experienceYears: 18,
    contractUntil: 2026,
  },
  {
    id: 'piastri',
    name: 'Oscar Piastri',
    country: 'Australia',
    flag: '🇦🇺',
    currentTeam: 'McLaren',
    marketValueMillions: 30,
    salaryMillions: 12,
    superlicensePoints: 58,
    paceRating: 93,
    experienceYears: 2,
    contractUntil: 2026,
  },
  {
    id: 'bearman',
    name: 'Oliver Bearman',
    country: 'Great Britain',
    flag: '🇬🇧',
    currentTeam: 'Haas F1',
    marketValueMillions: 12,
    salaryMillions: 3,
    superlicensePoints: 48,
    paceRating: 88,
    experienceYears: 1,
    contractUntil: 2026,
  },
];

export const DriverMarketHub: React.FC = () => {
  const { raceState } = useRaceStore();

  const [activeDriverId, setActiveDriverId] = useState<string>('verstappen');
  const [teamBudgetRemainingM, setTeamBudgetRemainingM] = useState<number>(38.5);
  const [signedDriverName, setSignedDriverName] = useState<string | null>(null);

  const selectedDriver = DRIVER_ROSTER.find((d) => d.id === activeDriverId) || DRIVER_ROSTER[0];

  const handleSignContract = () => {
    setSignedDriverName(selectedDriver.name);
    setTeamBudgetRemainingM((prev) => Math.max(0, prev - selectedDriver.salaryMillions * 0.2));
    confetti({ particleCount: 50, spread: 60 });
  };

  return (
    <div className="w-full rounded-2xl bg-slate-950 border border-slate-800 p-4 flex flex-col gap-4 shadow-2xl">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <ArrowRightLeft className="w-5 h-5 text-indigo-400 animate-pulse" />
          <div className="flex flex-col">
            <span className="font-bold text-white text-sm">
              PADDOCK LIVE DRIVER MARKET & SUPERLICENSE CONTRACT HUB
            </span>
            <span className="text-[11px] font-mono text-slate-400">
              Driver market valuations, FIA Superlicense points (40 pts req) & $135M cost cap allocations
            </span>
          </div>
        </div>

        {/* Cost Cap KPI */}
        <div className="flex items-center gap-2 bg-slate-900 px-3 py-1.5 rounded-xl border border-slate-800 text-xs font-mono">
          <DollarSign className="w-4 h-4 text-emerald-400" />
          <span className="text-slate-400">Cap Headroom: </span>
          <strong className="text-emerald-400">${teamBudgetRemainingM.toFixed(1)}M / $135M</strong>
        </div>
      </div>

      {/* Main Grid: Roster & Contract Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Roster List (Left 5 cols) */}
        <div className="lg:col-span-5 flex flex-col gap-2.5">
          <span className="text-xs font-mono text-slate-400 uppercase font-bold">
            AVAILABLE DRIVER MARKET ROSTER
          </span>

          {DRIVER_ROSTER.map((driver) => (
            <div
              key={driver.id}
              onClick={() => setActiveDriverId(driver.id)}
              className={`p-3 rounded-xl border cursor-pointer transition-all flex items-center justify-between ${
                activeDriverId === driver.id
                  ? 'bg-slate-900 border-indigo-500 shadow-md shadow-indigo-500/10'
                  : 'bg-slate-900/50 border-slate-800 hover:border-slate-700'
              }`}
            >
              <div className="flex items-center gap-2.5">
                <span className="text-xl">{driver.flag}</span>
                <div className="flex flex-col">
                  <span className="font-mono text-xs font-bold text-white">{driver.name}</span>
                  <span className="text-[10px] font-mono text-slate-400">{driver.currentTeam}</span>
                </div>
              </div>

              <div className="text-right font-mono">
                <div className="text-xs font-bold text-apex-cyan">${driver.marketValueMillions}M</div>
                <div className="text-[10px] text-emerald-400">Pace: {driver.paceRating}</div>
              </div>
            </div>
          ))}
        </div>

        {/* Driver Contract Dossier & Sign Panel (Right 7 cols) */}
        <div className="lg:col-span-7 p-5 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col justify-between gap-4">
          <div className="flex flex-col gap-3">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-3">
                <span className="text-3xl">{selectedDriver.flag}</span>
                <div className="flex flex-col">
                  <span className="text-lg font-black text-white font-mono">{selectedDriver.name}</span>
                  <span className="text-xs font-mono text-slate-400">
                    Current Team: <strong className="text-slate-200">{selectedDriver.currentTeam}</strong> • Contract Until {selectedDriver.contractUntil}
                  </span>
                </div>
              </div>

              <div className="flex items-center gap-1 bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 px-2.5 py-1 rounded-lg text-xs font-mono font-bold">
                <ShieldCheck className="w-4 h-4" />
                <span>SUPERLICENSE OK ({selectedDriver.superlicensePoints} PTS)</span>
              </div>
            </div>

            {/* Metrics Breakdown */}
            <div className="grid grid-cols-3 gap-2.5 font-mono">
              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 flex flex-col">
                <span className="text-[10px] text-slate-400 uppercase">ANNUAL SALARY</span>
                <span className="text-lg font-black text-white">${selectedDriver.salaryMillions}M / yr</span>
              </div>

              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 flex flex-col">
                <span className="text-[10px] text-slate-400 uppercase">PACE RATING</span>
                <span className="text-lg font-black text-apex-cyan">{selectedDriver.paceRating} / 100</span>
              </div>

              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 flex flex-col">
                <span className="text-[10px] text-slate-400 uppercase">EXPERIENCE</span>
                <span className="text-lg font-black text-amber-400">{selectedDriver.experienceYears} Years</span>
              </div>
            </div>
          </div>

          {/* Action Footer */}
          <div className="flex items-center justify-between pt-3 border-t border-slate-800">
            {signedDriverName === selectedDriver.name ? (
              <div className="flex items-center gap-2 text-emerald-400 font-mono text-xs font-bold">
                <CheckCircle2 className="w-5 h-5" />
                <span>CONTRACT SIGNED FOR 2026 CAMPAIGN</span>
              </div>
            ) : (
              <span className="text-xs font-mono text-slate-400">
                Buyout & Signing Bonus: ${Math.round(selectedDriver.salaryMillions * 0.2)}M
              </span>
            )}

            <button
              onClick={handleSignContract}
              disabled={signedDriverName === selectedDriver.name}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 text-white font-mono text-xs font-bold transition-all active:scale-95 shadow-md shadow-indigo-500/20"
            >
              <Sparkles className="w-4 h-4" />
              <span>Sign Driver to APEX Team</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
