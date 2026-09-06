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
      {/* Header */}
      <div className="flex items-center justify-between">
        <span className="text-xs uppercase tracking-widest text-slate-500 dark:text-slate-400 font-bold flex items-center gap-2">
          <span className="text-[#E10600] font-black">#</span>
          <span>Official 2026 Drivers</span>
        </span>
        {activeDriver && (
          <span className="text-xs font-mono text-slate-600 dark:text-slate-400">
            Selected:{' '}
            <strong className="text-slate-900 dark:text-white font-bold">
              {activeDriver.firstName} {activeDriver.lastName} ({activeDriver.team})
            </strong>
          </span>
        )}
      </div>

      {/* Grid of Drivers */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
        {drivers.map((driver) => {
          const isSelected = selectedDriver === driver.code;

          return (
            <button
              key={driver.code}
              type="button"
              onClick={() => onSelect(driver.code, driver.defaultGrid)}
              className={`matte-card-interactive card-3d p-3.5 flex flex-col justify-between h-44 relative overflow-hidden text-left cursor-pointer transition-all ${
                isSelected
                  ? 'ring-2 ring-[#E10600] border-transparent shadow-lg shadow-red-600/20'
                  : ''
              }`}
            >
              {/* Livery Top Accent Line */}
              <div
                className="absolute top-0 left-0 right-0 h-1"
                style={{ backgroundColor: driver.color }}
              />

              {/* Face Illumination Ambient Glow */}
              <div
                className="absolute top-3 left-1/2 -translate-x-1/2 w-24 h-24 rounded-full blur-xl opacity-20 pointer-events-none transition-opacity"
                style={{
                  backgroundColor: driver.color,
                  opacity: isSelected ? 0.45 : 0.2,
                }}
              />

              {/* Background Car Number */}
              <div className="absolute right-2 bottom-0 text-5xl font-black italic font-mono text-slate-900/5 dark:text-white/5 pointer-events-none select-none">
                {driver.number}
              </div>

              {/* Top Row: Flag, Number & Active Check */}
              <div className="flex items-center justify-between text-xs z-10">
                <div className="flex items-center gap-1.5">
                  <span className="text-sm">{driver.country}</span>
                  <span className="font-mono font-bold text-slate-600 dark:text-slate-300">
                    #{driver.number}
                  </span>
                </div>
                {isSelected && (
                  <div className="w-4 h-4 rounded-full bg-[#E10600] flex items-center justify-center text-white shadow-sm">
                    <Check className="w-2.5 h-2.5" />
                  </div>
                )}
              </div>

              {/* Driver Face Photo (Illuminated & Properly Scaled) */}
              <div className="relative h-20 w-full flex items-center justify-center my-1 z-10 overflow-hidden">
                <img
                  src={driver.photo || `/f1/drivers/${driver.code}.png`}
                  alt={`${driver.firstName} ${driver.lastName}`}
                  className="h-full w-auto object-contain transition-transform duration-300 group-hover:scale-105 drop-shadow-sm"
                  onError={(e) => {
                    const target = e.currentTarget;
                    target.style.display = 'none';
                    if (target.nextElementSibling) {
                      (target.nextElementSibling as HTMLElement).style.display = 'flex';
                    }
                  }}
                />
                <div
                  style={{ display: 'none' }}
                  className="w-12 h-12 rounded-full bg-slate-200 dark:bg-slate-800 items-center justify-center font-bold text-sm text-slate-700 dark:text-white"
                >
                  {driver.code}
                </div>
              </div>

              {/* Driver Name & Constructor */}
              <div className="z-10">
                <div className="text-[10px] text-slate-500 dark:text-slate-400 font-medium uppercase tracking-wider">
                  {driver.firstName}
                </div>
                <div className="font-extrabold text-xs text-slate-900 dark:text-white uppercase tracking-tight truncate font-['Outfit']">
                  {driver.lastName}
                </div>
                <div className="text-[10px] font-semibold truncate" style={{ color: driver.color }}>
                  {driver.team}
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default DriverGrid;
