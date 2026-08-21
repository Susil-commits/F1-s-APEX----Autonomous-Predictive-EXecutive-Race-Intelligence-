import React, { useState, useEffect } from 'react';
import { useRaceStore } from '../store/raceStore';
import { AerodynamicsCarData } from '../types/race';
import { Wind, Zap, Gauge, Flame, ShieldAlert, CheckCircle, ChevronRight } from 'lucide-react';

export const AerodynamicWakeRadar: React.FC = () => {
  const { raceState } = useRaceStore();
  const [aeroList, setAeroList] = useState<AerodynamicsCarData[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [selectedErsMode, setSelectedErsMode] = useState<string>('BALANCED');

  const fetchAerodynamics = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/strategy/aerodynamics');
      if (res.ok) {
        const data = await res.json();
        setAeroList(data.cars || []);
      }
    } catch (err) {
      console.warn('[APEX Aero] Could not fetch aerodynamics telemetry:', err);
    }
  };

  useEffect(() => {
    fetchAerodynamics();
    const interval = setInterval(fetchAerodynamics, 2000);
    return () => clearInterval(interval);
  }, [raceState?.current_lap]);

  const playerAero = aeroList.find((c) => c.driver_name.includes('APEX') || c.car_id === 'car_04') || aeroList[0];

  return (
    <div className="w-full rounded-2xl bg-slate-950 border border-slate-800 p-4 flex flex-col gap-4 shadow-2xl">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Wind className="w-5 h-5 text-apex-cyan animate-pulse" />
          <div className="flex flex-col">
            <span className="font-bold text-white text-sm">AERODYNAMIC WAKE & HYBRID ERS TELEMETRY</span>
            <span className="text-[11px] font-mono text-slate-400">
              Dirty air downforce loss, slipstream tow dynamics & 4MJ battery management
            </span>
          </div>
        </div>

        {/* ERS Deploy Mode Selector */}
        <div className="flex items-center gap-1.5 bg-slate-900 p-1 rounded-xl border border-slate-800 text-xs font-mono">
          <span className="text-slate-400 pl-1">ERS Mode:</span>
          {(['BALANCED', 'OVERTAKE', 'DEFEND', 'HOTLAP', 'HARVEST'] as const).map((mode) => (
            <button
              key={mode}
              onClick={() => setSelectedErsMode(mode)}
              className={`px-2 py-0.5 rounded-lg text-[10px] font-bold transition-all ${
                selectedErsMode === mode
                  ? mode === 'OVERTAKE' || mode === 'HOTLAP'
                    ? 'bg-rose-500 text-black shadow-sm shadow-rose-500/30'
                    : mode === 'HARVEST'
                    ? 'bg-emerald-500 text-black shadow-sm shadow-emerald-500/30'
                    : 'bg-apex-cyan text-black font-bold'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              {mode}
            </button>
          ))}
        </div>
      </div>

      {/* Top Telemetry Row: Wake Diagram & Battery HUD */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Downforce Retention Gauge */}
        <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-slate-400 uppercase font-bold">DOWNFORCE RETENTION</span>
            <Wind className="w-4 h-4 text-apex-cyan" />
          </div>
          <div className="flex items-baseline gap-2 my-2">
            <span className="text-4xl font-black font-mono text-white">
              {playerAero?.downforce_retention_pct || 100}%
            </span>
            <span
              className={`text-xs font-mono font-bold ${
                (playerAero?.downforce_retention_pct || 100) < 80 ? 'text-rose-400' : 'text-emerald-400'
              }`}
            >
              {(playerAero?.downforce_retention_pct || 100) < 80 ? '-24% CORNER GRIP' : 'OPTIMAL AERO'}
            </span>
          </div>
          <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
            <div
              className={`h-full transition-all duration-500 ${
                (playerAero?.downforce_retention_pct || 100) < 75
                  ? 'bg-rose-500'
                  : (playerAero?.downforce_retention_pct || 100) < 90
                  ? 'bg-amber-400'
                  : 'bg-emerald-400'
              }`}
              style={{ width: `${playerAero?.downforce_retention_pct || 100}%` }}
            />
          </div>
        </div>

        {/* ERS Battery State of Charge */}
        <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-slate-400 uppercase font-bold">ERS BATTERY (SoC)</span>
            <Zap className="w-4 h-4 text-purple-400" />
          </div>
          <div className="flex items-baseline gap-2 my-2">
            <span className="text-4xl font-black font-mono text-purple-300">
              {playerAero?.ers_battery_soc_pct || 85}%
            </span>
            <span className="text-xs font-mono text-slate-400">3.4 MJ / 4.0 MJ</span>
          </div>
          <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-purple-600 via-pink-500 to-apex-cyan transition-all duration-500"
              style={{ width: `${playerAero?.ers_battery_soc_pct || 85}%` }}
            />
          </div>
        </div>

        {/* Slipstream & DRS Status */}
        <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-slate-400 uppercase font-bold">SLIPSTREAM & TOW</span>
            <Flame className="w-4 h-4 text-amber-400" />
          </div>
          <div className="flex flex-col gap-1 my-1 text-xs font-mono">
            <div className="flex justify-between">
              <span className="text-slate-400">Slipstream Tow:</span>
              <span className={`font-bold ${playerAero?.slipstream_active ? 'text-emerald-400' : 'text-slate-500'}`}>
                {playerAero?.slipstream_active ? 'ACTIVE (+14 KM/H)' : 'INACTIVE'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Wake Intensity:</span>
              <span className="font-bold text-amber-400">
                {playerAero?.dirty_air_intensity ? `${Math.round(playerAero.dirty_air_intensity * 100)}%` : '0%'}
              </span>
            </div>
          </div>
          <span className="text-[10px] font-mono text-slate-400">
            {playerAero?.in_dirty_air
              ? 'Warning: Sliding in wake increases tyre graining.'
              : 'Clean air: Maximum downforce & cooling efficiency.'}
          </span>
        </div>
      </div>

      {/* Grid Multi-Car Aerodynamics Status Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs font-mono">
          <thead className="bg-slate-900 text-slate-400 border-b border-slate-800 uppercase text-[10px]">
            <tr>
              <th className="p-2.5">POS</th>
              <th className="p-2.5">DRIVER</th>
              <th className="p-2.5">GAP AHEAD</th>
              <th className="p-2.5">WAKE STATUS</th>
              <th className="p-2.5">DOWNFORCE</th>
              <th className="p-2.5">ERS BATTERY</th>
              <th className="p-2.5">SPEED</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {aeroList.map((car) => (
              <tr
                key={car.car_id}
                className={`hover:bg-slate-900/60 transition-all ${
                  car.driver_name.includes('APEX') ? 'bg-apex-cyan/10 text-white font-bold' : 'text-slate-300'
                }`}
              >
                <td className="p-2.5 font-bold text-white">P{car.position}</td>
                <td className="p-2.5">{car.driver_name}</td>
                <td className="p-2.5 text-slate-400">
                  {car.position === 1 ? 'LEADER' : `+${car.gap_to_car_ahead_s}s`}
                </td>
                <td className="p-2.5">
                  {car.in_dirty_air ? (
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40">
                      DIRTY AIR ({Math.round(car.dirty_air_intensity * 100)}%)
                    </span>
                  ) : (
                    <span className="px-2 py-0.5 rounded text-[10px] bg-slate-800 text-slate-400">
                      CLEAN AIR
                    </span>
                  )}
                </td>
                <td className="p-2.5 font-bold text-apex-cyan">{car.downforce_retention_pct}%</td>
                <td className="p-2.5">
                  <div className="flex items-center gap-2">
                    <div className="w-16 bg-slate-800 rounded-full h-1.5 overflow-hidden">
                      <div
                        className="h-full bg-purple-500"
                        style={{ width: `${car.ers_battery_soc_pct}%` }}
                      />
                    </div>
                    <span className="text-[10px] text-purple-300 font-bold">{car.ers_battery_soc_pct}%</span>
                  </div>
                </td>
                <td className="p-2.5 font-bold text-white">{car.speed_kmh} km/h</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
