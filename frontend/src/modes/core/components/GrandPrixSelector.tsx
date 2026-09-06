import React from 'react';
import { Flag, Compass } from 'lucide-react';
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
      {/* Section Header */}
      <div className="flex items-center justify-between">
        <span className="text-xs uppercase tracking-widest text-slate-500 dark:text-slate-400 font-bold flex items-center gap-2">
          <Flag className="w-3.5 h-3.5 text-[#E10600]" />
          <span>Select Grand Prix Circuit</span>
        </span>
        {activeGP && (
          <span className="text-xs font-mono text-slate-600 dark:text-slate-400">
            Venue:{' '}
            <strong className="text-slate-900 dark:text-white font-bold">
              {activeGP.circuit}
            </strong>{' '}
            ({activeGP.distanceKm} km · {activeGP.laps} Laps · {activeGP.downforce} Downforce)
          </span>
        )}
      </div>

      {/* Grid of Grand Prix Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
        {races.map((gp) => {
          const isSelected = selectedRace === gp.id;

          return (
            <button
              key={gp.id}
              type="button"
              onClick={() => onSelect(gp.id)}
              className={`matte-card-interactive p-3.5 flex flex-col justify-between h-28 text-left cursor-pointer transition-all ${
                isSelected
                  ? 'ring-2 ring-[#E10600] border-transparent shadow-lg shadow-red-600/20 bg-red-500/[0.04]'
                  : ''
              }`}
            >
              <div className="flex items-center justify-between text-xs">
                <span className="font-mono font-bold text-[10px] text-slate-500 dark:text-slate-400 uppercase">
                  RD {gp.round}
                </span>
                <span className="text-lg">{gp.flag}</span>
              </div>

              <div>
                <h3 className="font-bold text-xs uppercase text-slate-900 dark:text-white truncate font-['Outfit']">
                  {gp.name}
                </h3>
                <div className="flex items-center justify-between mt-1 text-[10px] font-mono text-slate-500 dark:text-slate-400">
                  <span className="truncate">{gp.city}</span>
                  <span className="font-bold px-1.5 py-0.2 rounded bg-slate-200/60 dark:bg-white/10 text-[9px]">
                    {gp.downforce}
                  </span>
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default GrandPrixSelector;
