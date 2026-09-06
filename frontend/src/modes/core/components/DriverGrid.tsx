import React from 'react';
import { Check } from 'lucide-react';
import { DriverItem } from '../data/constants';

export interface DriverGridProps {
  drivers: DriverItem[];
  selectedDriver: string;
  onSelect: (driverCode: string, defaultGrid: number) => void;
}

export const DriverGrid: React.FC<DriverGridProps> = ({
  drivers,
  selectedDriver,
  onSelect,
}) => {
  const activeDriver = drivers.find((d) => d.code === selectedDriver) || drivers[0];

  return (
    <div className="w-full flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-f1 uppercase tracking-widest text-slate-300 font-bold flex items-center gap-2">
          <span className="text-[#E10600] font-black">#</span>
          <span>Select Driver</span>
        </span>
        {activeDriver && (
          <span className="text-[11px] font-mono text-slate-400">
            Selected:{' '}
            <strong className="text-white font-f1">
              {activeDriver.firstName} {activeDriver.lastName} ({activeDriver.team})
            </strong>
          </span>
        )}
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {drivers.map((driver) => {
          const isSelected = selectedDriver === driver.code;

          return (
            <button
              key={driver.code}
              type="button"
              onClick={() => onSelect(driver.code, driver.defaultGrid)}
              className={`relative rounded-xl border p-3.5 text-left transition-all cursor-pointer overflow-hidden flex flex-col justify-between h-36 ${
                isSelected
                  ? 'f1-card-active ring-2 ring-[#E10600]'
                  : 'bg-[#13151F] border-[#242738] hover:border-slate-500 hover:bg-[#181B26]'
              }`}
            >
              {/* Team color accent line */}
              <div
                className="absolute top-0 left-0 right-0 h-1"
                style={{ backgroundColor: driver.color }}
              />

              {/* Big italic racing number in background */}
              <div className="absolute right-2 bottom-1 text-5xl font-black italic font-f1 text-white opacity-10 pointer-events-none select-none">
                {driver.number}
              </div>

              {/* Top: Flag & Number */}
              <div className="flex items-center justify-between z-10">
                <div className="flex items-center gap-1.5">
                  <span className="text-sm">{driver.country}</span>
                  <span className="text-xs font-mono font-black text-white">#{driver.number}</span>
                </div>
                {isSelected && (
                  <div className="w-4 h-4 rounded-full bg-[#E10600] flex items-center justify-center">
                    <Check className="w-2.5 h-2.5 text-white" />
                  </div>
                )}
              </div>

              {/* Driver cutout photo or fallback avatar */}
              <div className="relative h-16 w-full flex items-center justify-center my-1 z-10">
                {driver.photo ? (
                  <img
                    src={driver.photo}
                    alt={driver.lastName}
                    className="h-full object-contain drop-shadow-lg"
                  />
                ) : (
                  <div className="w-12 h-12 rounded-full bg-[#1C1F2D] border border-[#2F3447] flex items-center justify-center font-f1 font-black text-white text-lg">
                    {driver.code}
                  </div>
                )}
              </div>

              {/* Bottom: Driver Name & Team */}
              <div className="z-10">
                <div className="text-[10px] text-slate-400 font-f1 uppercase tracking-wider">
                  {driver.firstName}
                </div>
                <div className="font-black text-xs font-f1 uppercase text-white tracking-wide truncate">
                  {driver.lastName}
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};
