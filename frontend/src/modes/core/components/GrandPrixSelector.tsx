import React from 'react';
import { Flag } from 'lucide-react';
import { GrandPrix } from '../data/constants';

export interface GrandPrixSelectorProps {
  races: GrandPrix[];
  selectedRace: string;
  onSelect: (raceId: string) => void;
}

export const GrandPrixSelector: React.FC<GrandPrixSelectorProps> = ({
  races,
  selectedRace,
  onSelect,
}) => {
  const activeGP = races.find((g) => g.id === selectedRace) || races[0];

  return (
    <div className="w-full flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-f1 uppercase tracking-widest text-slate-300 font-bold flex items-center gap-2">
          <Flag className="w-4 h-4 text-[#E10600]" />
          <span>Select 2026 Grand Prix Venue</span>
        </span>
        {activeGP && (
          <span className="text-[11px] font-mono text-[#00F0FF] uppercase">
            {activeGP.circuit} ({activeGP.distanceKm} km · {activeGP.downforce} DF)
          </span>
        )}
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2.5">
        {races.map((gp) => {
          const isSelected = selectedRace === gp.id;
          return (
            <button
              key={gp.id}
              type="button"
              onClick={() => onSelect(gp.id)}
              className={`p-3 rounded-xl border text-left transition-all cursor-pointer flex flex-col justify-between ${
                isSelected
                  ? 'bg-[#22181C] border-[#E10600] shadow-lg shadow-red-950/40 ring-1 ring-[#E10600]'
                  : 'bg-[#12141D] border-[#222533] hover:border-slate-600 hover:bg-[#181B26]'
              }`}
            >
              <div className="flex items-center justify-between text-xs mb-1.5">
                <span className="font-mono text-[10px] text-slate-400 font-bold uppercase">
                  RD {gp.round}
                </span>
                <span className="text-base">{gp.flag}</span>
              </div>
              <div>
                <h3 className="font-black text-xs font-f1 uppercase text-white truncate">{gp.name}</h3>
                <span className="text-[10px] font-mono text-slate-400 block truncate">{gp.downforce} DF</span>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};
