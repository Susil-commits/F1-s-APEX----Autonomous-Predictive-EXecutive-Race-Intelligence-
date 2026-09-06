import React from 'react';
import { ChevronRight } from 'lucide-react';
import { DRIVERS_LIST, F1_CDN_FALLBACK } from '../../modes/core/data/constants';

interface DriverLineupProps {
  onEnterApp: () => void;
}

export const DriverLineup: React.FC<DriverLineupProps> = ({ onEnterApp }) => {
  return (
    <section className="py-20 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div className="text-center max-w-2xl mx-auto mb-12 flex flex-col items-center gap-2">
        <span className="text-xs font-bold uppercase tracking-widest text-[#E10600]">Championship Contenders</span>
        <h2 className="text-3xl sm:text-5xl font-extrabold uppercase tracking-tight text-slate-900 dark:text-white font-['Outfit']">
          2026 DRIVER LINEUP
        </h2>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Official driver lineup with current form ratings and constructor race pace.
        </p>
      </div>

      {/* Driver Cards with 3D Tilt Effect and Face Lighting */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
        {DRIVERS_LIST.map((driver) => (
          <div
            key={driver.code}
            className="matte-card-interactive card-3d p-4 flex flex-col justify-between h-56 relative overflow-hidden group"
          >
            {/* Livery Accent Bar */}
            <div
              className="absolute top-0 left-0 right-0 h-1"
              style={{ backgroundColor: driver.color }}
            />

            {/* Ambient face backlight halo */}
            <div
              className="absolute top-6 left-1/2 -translate-x-1/2 w-28 h-28 rounded-full blur-2xl opacity-20 group-hover:opacity-40 transition-opacity pointer-events-none"
              style={{ backgroundColor: driver.color }}
            />

            {/* Top: Country Flag & Number */}
            <div className="flex items-center justify-between text-xs z-10">
              <span className="text-base">{driver.country}</span>
              <span className="font-mono font-black text-slate-400 group-hover:text-slate-900 dark:group-hover:text-white transition-colors">
                #{driver.number}
              </span>
            </div>

            {/* Driver Face Photo: High Resolution, Centered, Illuminated */}
            <div className="relative h-28 w-full flex items-center justify-center my-1 z-10 overflow-hidden">
              <img
                src={driver.photo}
                alt={`${driver.firstName} ${driver.lastName}`}
                className="h-full w-auto object-contain transition-transform duration-300 group-hover:scale-110 drop-shadow-md"
                onError={(e) => {
                  const target = e.currentTarget;
                  const cdn = F1_CDN_FALLBACK[driver.code];
                  if (cdn && target.src !== cdn) {
                    target.src = cdn;
                    return;
                  }
                  target.style.display = 'none';
                  if (target.nextElementSibling) {
                    (target.nextElementSibling as HTMLElement).style.display = 'flex';
                  }
                }}
              />
              <div
                style={{ display: 'none' }}
                className="w-16 h-16 rounded-full bg-slate-200 dark:bg-slate-800 items-center justify-center font-bold text-lg text-slate-700 dark:text-white"
              >
                {driver.code}
              </div>
            </div>

            {/* Bottom: Names & Constructor */}
            <div className="z-10 text-left">
              <div className="text-[10px] uppercase tracking-wider text-slate-500 dark:text-slate-400 font-medium">
                {driver.firstName}
              </div>
              <div className="text-sm font-extrabold uppercase tracking-tight text-slate-900 dark:text-white font-['Outfit'] truncate">
                {driver.lastName}
              </div>
              <div className="text-[10px] font-semibold tracking-wide truncate" style={{ color: driver.color }}>
                {driver.team}
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="text-center mt-8">
        <button
          type="button"
          onClick={onEnterApp}
          className="btn-f1-primary px-8 py-3 text-xs font-bold tracking-wider inline-flex items-center gap-2 cursor-pointer"
        >
          <span>Select Driver in Predictor</span>
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    </section>
  );
};

export default DriverLineup;
