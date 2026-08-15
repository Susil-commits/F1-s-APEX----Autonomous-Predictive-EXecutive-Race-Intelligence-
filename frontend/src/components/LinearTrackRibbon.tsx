import React from 'react';
import { useRaceStore } from '../store/raceStore';
import { CarState } from '../types/race';

export const LinearTrackRibbon: React.FC = () => {
  const { raceState, setSelectedCarId, setInspectedCar } = useRaceStore();

  if (!raceState) return null;

  const { cars, track } = raceState;
  const playerCar = cars.find((c) => c.is_player) || cars[0];

  return (
    <div className="flex flex-col gap-2 w-full p-3 bg-slate-950/70 rounded-xl border border-slate-800 font-mono text-xs">
      <div className="flex items-center justify-between text-[10px] text-slate-400 uppercase font-sans font-bold">
        <span>Linear Circuit Progression Ribbon</span>
        <span>Length: {track.lap_distance_km} km</span>
      </div>

      {/* Ribbon Track Bar */}
      <div className="relative w-full h-10 bg-slate-900 rounded-lg border border-slate-800 flex items-center px-4 overflow-hidden select-none">
        {/* Sector Background Segments */}
        <div className="absolute inset-y-0 left-0 w-[33%] bg-cyan-950/20 border-r border-cyan-500/20 flex items-center justify-center pointer-events-none">
          <span className="text-[9px] text-cyan-400/40 font-black">SECTOR 1</span>
        </div>
        <div className="absolute inset-y-0 left-[33%] w-[34%] bg-amber-950/20 border-r border-amber-500/20 flex items-center justify-center pointer-events-none">
          <span className="text-[9px] text-amber-400/40 font-black">SECTOR 2</span>
        </div>
        <div className="absolute inset-y-0 right-0 w-[33%] bg-purple-950/20 flex items-center justify-center pointer-events-none">
          <span className="text-[9px] text-purple-400/40 font-black">SECTOR 3</span>
        </div>

        {/* DRS Zone Strips */}
        <div className="absolute top-0 bottom-0 left-[18%] w-[12%] bg-emerald-500/10 border-t-2 border-emerald-400 pointer-events-none" />
        <div className="absolute top-0 bottom-0 left-[68%] w-[14%] bg-emerald-500/10 border-t-2 border-emerald-400 pointer-events-none" />

        {/* Start / Finish Line */}
        <div className="absolute top-0 bottom-0 left-2 w-0.5 bg-white shadow-sm shadow-white pointer-events-none" />

        {/* Cars on Ribbon */}
        {cars.map((car: CarState) => {
          const isPlayer = car.is_player;
          // Calculate proportional percentage based on position & gap
          const pct = Math.min(95, Math.max(3, 100 - (car.position - 1) * 9.5));

          return (
            <div
              key={car.car_id}
              onClick={() => {
                setSelectedCarId(car.car_id);
                setInspectedCar(car);
              }}
              style={{ left: `${pct}%` }}
              className={`absolute -translate-x-1/2 flex flex-col items-center cursor-pointer transition-all duration-500 group z-10`}
            >
              {/* Position Pill */}
              <div
                className={`px-1.5 py-0.2 rounded text-[9px] font-black tracking-tight border transition-transform group-hover:scale-110 ${
                  isPlayer
                    ? 'bg-cyan-500 text-black border-white shadow-md shadow-cyan-500/50'
                    : car.position === 1
                    ? 'bg-yellow-500 text-black border-yellow-300'
                    : 'bg-slate-800 text-slate-200 border-slate-700'
                }`}
              >
                P{car.position}
              </div>

              {/* Marker Dot */}
              <div
                className={`w-2 h-2 rounded-full mt-0.5 ${
                  isPlayer
                    ? 'bg-cyan-400 ring-2 ring-cyan-400/50 animate-ping'
                    : car.position === 1
                    ? 'bg-yellow-400'
                    : 'bg-slate-400'
                }`}
              />
            </div>
          );
        })}
      </div>

      {/* Ribbon Legend */}
      <div className="flex items-center justify-between text-[9.5px] text-slate-500 px-1">
        <span className="flex items-center gap-1">
          <span className="w-2 h-0.5 bg-white inline-block" /> Start/Finish
        </span>
        <span className="flex items-center gap-1 text-emerald-400 font-bold">
          <span className="w-2 h-0.5 bg-emerald-400 inline-block" /> DRS Activation
        </span>
        <span className="flex items-center gap-1 text-cyan-400">
          <span className="w-2 h-2 rounded-full bg-cyan-400 inline-block" /> APEX
        </span>
        <span className="flex items-center gap-1 text-yellow-400">
          <span className="w-2 h-2 rounded-full bg-yellow-400 inline-block" /> Leader
        </span>
      </div>
    </div>
  );
};
