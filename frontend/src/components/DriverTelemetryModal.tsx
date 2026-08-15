import React from 'react';
import { useRaceStore } from '../store/raceStore';
import {
  X,
  Gauge,
  Zap,
  Flame,
  Fuel,
  Shield,
  Activity,
  Radio,
  TrendingUp,
  Disc,
} from 'lucide-react';
import { CarState } from '../types/race';

export const DriverTelemetryModal: React.FC = () => {
  const { inspectedCar, setInspectedCar, raceState } = useRaceStore();

  if (!inspectedCar || !raceState) return null;

  const car: CarState = inspectedCar;
  const wear = car.tyre_wear_pct;
  const isPush = car.driving_mode === 'PUSH';
  const isConserve = car.driving_mode === 'CONSERVE';

  // Derived high-fidelity telemetry metrics
  const speedKmh = isPush ? 318 : isConserve ? 295 : 308;
  const rpm = isPush ? 12450 : isConserve ? 10800 : 11600;
  const gear = isPush ? 7 : 7;
  const throttlePct = isPush ? 98 : isConserve ? 84 : 92;
  const brakePct = 0;
  const ersBatteryPct = isPush ? 62 : isConserve ? 94 : 81;

  // 4-corner tyre thermal simulation (°C)
  const tempFL = parseFloat((84 + wear * 0.45 + (isPush ? 8 : 0)).toFixed(1));
  const tempFR = parseFloat((86 + wear * 0.48 + (isPush ? 9 : 0)).toFixed(1));
  const tempRL = parseFloat((91 + wear * 0.52 + (isPush ? 10 : 0)).toFixed(1));
  const tempRR = parseFloat((93 + wear * 0.55 + (isPush ? 11 : 0)).toFixed(1));

  const getTempColor = (t: number) => {
    if (t > 115) return 'text-rose-400 bg-rose-950/40 border-rose-600/50';
    if (t > 100) return 'text-amber-400 bg-amber-950/40 border-amber-600/50';
    return 'text-emerald-400 bg-emerald-950/40 border-emerald-600/50';
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-md animate-fadeIn">
      <div className="glass-panel-glow w-full max-w-2xl rounded-2xl p-6 border border-cyan-500/40 shadow-2xl relative flex flex-col gap-4 text-slate-100">
        {/* Top Header Bar */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center font-black text-black text-lg shadow-lg shadow-cyan-500/30">
              #{car.car_number}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-black tracking-wide text-white">{car.driver_name}</h2>
                <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 font-bold">
                  {car.team_name}
                </span>
                {car.is_player && (
                  <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-cyan-500/20 text-apex-cyan border border-cyan-500/40 font-black">
                    APEX CHASSIS
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-400 font-mono">
                Position: <span className="text-amber-400 font-bold">P{car.position}</span> • Lap: {car.current_lap} / {raceState.total_laps} • Gap to P1: +{car.gap_to_leader_s.toFixed(2)}s
              </p>
            </div>
          </div>

          <button
            onClick={() => setInspectedCar(null)}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white border border-slate-700 transition-all"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Live Gauges Row */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono text-center">
          {/* Speed */}
          <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800">
            <span className="text-[10px] text-slate-400 uppercase block font-sans font-semibold">Speed</span>
            <span className="text-2xl font-black text-apex-cyan glow-cyan">{speedKmh}</span>
            <span className="text-[10px] text-slate-500 block">km/h</span>
          </div>

          {/* RPM & Gear */}
          <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800">
            <span className="text-[10px] text-slate-400 uppercase block font-sans font-semibold">Gear / Engine</span>
            <div className="flex items-center justify-center gap-1.5">
              <span className="text-2xl font-black text-amber-400">{gear}</span>
              <span className="text-xs text-slate-400">({rpm} RPM)</span>
            </div>
            <span className="text-[10px] text-slate-500 block">V6 Turbo Hybrid</span>
          </div>

          {/* Throttle */}
          <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800">
            <span className="text-[10px] text-slate-400 uppercase block font-sans font-semibold">Throttle / ERS</span>
            <span className="text-2xl font-black text-emerald-400">{throttlePct}%</span>
            <div className="w-full h-1.5 bg-slate-800 rounded-full mt-1 overflow-hidden">
              <div className="h-full bg-emerald-400 rounded-full" style={{ width: `${throttlePct}%` }} />
            </div>
          </div>

          {/* Mode */}
          <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800">
            <span className="text-[10px] text-slate-400 uppercase block font-sans font-semibold">Engine Mode</span>
            <span className={`text-base font-black uppercase mt-1 block ${
              isPush ? 'text-rose-400' : isConserve ? 'text-cyan-400' : 'text-slate-200'
            }`}>
              {car.driving_mode}
            </span>
            <span className="text-[10px] text-slate-500">ERS: {ersBatteryPct}% SOC</span>
          </div>
        </div>

        {/* 4-Corner Tyre Thermal & Degradation Heatmap */}
        <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Flame className="w-4 h-4 text-amber-400" />
              <h3 className="text-xs font-black uppercase tracking-wider text-slate-200">
                4-Corner Tyre Thermals & Wear Matrix
              </h3>
            </div>
            <div className="text-[11px] font-mono">
              Compound: <span className="font-bold text-amber-400">{car.tyre_compound}</span> ({car.tyre_age_laps} Laps old)
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            {/* Front Left */}
            <div className={`p-3 rounded-lg border ${getTempColor(tempFL)} flex items-center justify-between`}>
              <div>
                <span className="text-[10px] uppercase font-sans font-bold block text-slate-400">Front Left (FL)</span>
                <span className="text-lg font-black font-mono">{tempFL}°C</span>
              </div>
              <div className="text-right font-mono text-xs">
                <span className="text-slate-400 text-[10px] block">Wear</span>
                <span className="font-bold">{wear.toFixed(1)}%</span>
              </div>
            </div>

            {/* Front Right */}
            <div className={`p-3 rounded-lg border ${getTempColor(tempFR)} flex items-center justify-between`}>
              <div>
                <span className="text-[10px] uppercase font-sans font-bold block text-slate-400">Front Right (FR)</span>
                <span className="text-lg font-black font-mono">{tempFR}°C</span>
              </div>
              <div className="text-right font-mono text-xs">
                <span className="text-slate-400 text-[10px] block">Wear</span>
                <span className="font-bold">{wear.toFixed(1)}%</span>
              </div>
            </div>

            {/* Rear Left */}
            <div className={`p-3 rounded-lg border ${getTempColor(tempRL)} flex items-center justify-between`}>
              <div>
                <span className="text-[10px] uppercase font-sans font-bold block text-slate-400">Rear Left (RL)</span>
                <span className="text-lg font-black font-mono">{tempRL}°C</span>
              </div>
              <div className="text-right font-mono text-xs">
                <span className="text-slate-400 text-[10px] block">Wear</span>
                <span className="font-bold">{(wear * 1.05).toFixed(1)}%</span>
              </div>
            </div>

            {/* Rear Right */}
            <div className={`p-3 rounded-lg border ${getTempColor(tempRR)} flex items-center justify-between`}>
              <div>
                <span className="text-[10px] uppercase font-sans font-bold block text-slate-400">Rear Right (RR)</span>
                <span className="text-lg font-black font-mono">{tempRR}°C</span>
              </div>
              <div className="text-right font-mono text-xs">
                <span className="text-slate-400 text-[10px] block">Wear</span>
                <span className="font-bold">{(wear * 1.08).toFixed(1)}%</span>
              </div>
            </div>
          </div>
        </div>

        {/* Fuel & Stint Summary */}
        <div className="grid grid-cols-3 gap-3 font-mono text-xs text-center">
          <div className="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800">
            <span className="text-[10px] text-slate-400 uppercase font-sans block">Fuel Mass</span>
            <span className="font-bold text-slate-200">{car.fuel_kg.toFixed(1)} kg</span>
          </div>
          <div className="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800">
            <span className="text-[10px] text-slate-400 uppercase font-sans block">Pit Stops</span>
            <span className="font-bold text-slate-200">{car.pit_count} Stops</span>
          </div>
          <div className="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800">
            <span className="text-[10px] text-slate-400 uppercase font-sans block">Best Lap</span>
            <span className="font-bold text-purple-400">
              {car.best_lap_time_s ? `${car.best_lap_time_s.toFixed(2)}s` : '--.--'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
