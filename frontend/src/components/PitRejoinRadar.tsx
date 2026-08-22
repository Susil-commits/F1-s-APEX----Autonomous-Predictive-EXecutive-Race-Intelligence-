import React, { useMemo } from 'react';
import { useRaceStore } from '../store/raceStore';
import { ShieldCheck, AlertTriangle, Wind } from 'lucide-react';
import { CarState } from '../types/race';

export const PitRejoinRadar: React.FC = () => {
  const { raceState } = useRaceStore();

  const playerCar = raceState?.cars?.find((c) => c.is_player) || raceState?.cars?.[0];
  const track = raceState?.track;
  const safety_car = raceState?.safety_car;
  const cars = raceState?.cars || [];

  const rejoinAnalysis = useMemo(() => {
    if (!raceState || !playerCar || !track) return null;

    // Calculate dynamic pit delta
    let effectivePitDelta = track.pit_lane_delta_s;
    if (safety_car === 'SAFETY_CAR') {
      effectivePitDelta -= track.sc_pit_advantage_s;
    } else if (safety_car === 'VSC') {
      effectivePitDelta -= track.vsc_pit_advantage_s;
    }

    const projectedPlayerTotalTime = playerCar.total_race_time_s + effectivePitDelta;
    
    // Sort all other cars by their current total race time
    const otherCars = cars.filter((c) => c.car_id !== playerCar.car_id);
    
    let projectedPos = 1;
    let carAhead: CarState | null = null;
    let carBehind: CarState | null = null;
    let gapAhead = 999;
    let gapBehind = 999;

    // Determine projected position
    for (const car of otherCars) {
      if (car.total_race_time_s < projectedPlayerTotalTime) {
        projectedPos += 1;
        carAhead = car;
        gapAhead = projectedPlayerTotalTime - car.total_race_time_s;
      } else {
        if (!carBehind) {
          carBehind = car;
          gapBehind = car.total_race_time_s - projectedPlayerTotalTime;
        }
      }
    }

    const inDirtyAir = (gapAhead > 0 && gapAhead < 1.8) || (gapBehind > 0 && gapBehind < 1.2);

    return {
      projectedPos,
      effectivePitDelta,
      carAhead,
      carBehind,
      gapAhead: gapAhead === 999 ? 0 : gapAhead,
      gapBehind: gapBehind === 999 ? 0 : gapBehind,
      inDirtyAir,
    };
  }, [raceState, playerCar, track, safety_car, cars]);

  if (!raceState || !playerCar || !rejoinAnalysis) return null;

  return (
    <div className="glass-panel rounded-xl p-4 flex flex-col border border-apex-border shadow-2xl">
      {/* Title */}
      <div className="flex items-center justify-between mb-3 border-b border-slate-800 pb-2">
        <div className="flex items-center gap-2">
          <Wind className="w-4 h-4 text-apex-cyan" />
          <h3 className="text-xs font-black uppercase tracking-widest text-slate-200">
            Pit Rejoin & Traffic Radar
          </h3>
        </div>
        <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
          Delta: ~{rejoinAnalysis.effectivePitDelta.toFixed(1)}s
        </span>
      </div>

      {/* Main Rejoin Position Callout */}
      <div className="flex items-center justify-between p-3 rounded-lg bg-slate-900/90 border border-slate-800 mb-3">
        <div>
          <span className="text-[10px] text-slate-400 font-sans font-semibold uppercase block">
            Projected Re-emergence
          </span>
          <div className="flex items-center gap-2 mt-0.5">
            <span className="text-xl font-black font-mono text-apex-cyan">
              Position P{rejoinAnalysis.projectedPos}
            </span>
            <span className="text-xs text-slate-400 font-mono">
              (Current: P{playerCar.position})
            </span>
          </div>
        </div>

        {/* Traffic status badge */}
        <div>
          {rejoinAnalysis.inDirtyAir ? (
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40 text-[10px] font-mono font-bold">
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>TRAFFIC RISK</span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 text-[10px] font-mono font-bold">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>CLEAN AIR WINDOW</span>
            </div>
          )}
        </div>
      </div>

      {/* Traffic Slot Details */}
      <div className="grid grid-cols-2 gap-2 text-xs font-mono">
        <div className="p-2.5 rounded bg-slate-900/60 border border-slate-800/80">
          <span className="text-[9.5px] uppercase text-slate-500 font-sans block font-semibold">
            Rejoin Behind
          </span>
          {rejoinAnalysis.carAhead ? (
            <div className="mt-1">
              <span className="font-bold text-slate-200 block truncate">
                {rejoinAnalysis.carAhead.driver_name} (P{rejoinAnalysis.carAhead.position})
              </span>
              <span className="text-[11px] text-cyan-400">
                Gap Ahead: +{rejoinAnalysis.gapAhead.toFixed(1)}s
              </span>
            </div>
          ) : (
            <span className="font-bold text-yellow-400 text-[11px] mt-1 block">LEADER (P1 Rejoin)</span>
          )}
        </div>

        <div className="p-2.5 rounded bg-slate-900/60 border border-slate-800/80">
          <span className="text-[9.5px] uppercase text-slate-500 font-sans block font-semibold">
            Buffer to Car Behind
          </span>
          {rejoinAnalysis.carBehind ? (
            <div className="mt-1">
              <span className="font-bold text-slate-200 block truncate">
                {rejoinAnalysis.carBehind.driver_name} (P{rejoinAnalysis.carBehind.position})
              </span>
              <span className="text-[11px] text-emerald-400">
                Buffer: +{rejoinAnalysis.gapBehind.toFixed(1)}s
              </span>
            </div>
          ) : (
            <span className="font-bold text-slate-400 text-[11px] mt-1 block">Clear Track Behind</span>
          )}
        </div>
      </div>

      {/* Rejoin Window Strip */}
      <div className="mt-3 pt-2.5 border-t border-slate-800">
        <div className="flex items-center justify-between text-[9px] font-mono text-slate-500 mb-1">
          <span>LEADER (0s)</span>
          <span>REJOIN SLOT</span>
          <span>BACKMARKERS (+40s)</span>
        </div>
        <div className="relative w-full h-3 bg-slate-950 rounded-full border border-slate-800 overflow-hidden">
          {/* Competitor Dots */}
          {cars.map((c) => {
            const pct = Math.min(95, (c.gap_to_leader_s / 40) * 100);
            return (
              <div
                key={c.car_id}
                className="absolute top-0 bottom-0 w-1 bg-slate-600 rounded-full"
                style={{ left: `${pct}%` }}
                title={`P${c.position} ${c.driver_name}`}
              />
            );
          })}
          {/* Projected Rejoin Slot Marker */}
          <div
            className="absolute top-0 bottom-0 w-2.5 bg-apex-cyan rounded-full animate-ping opacity-75"
            style={{
              left: `${Math.min(95, ((playerCar.gap_to_leader_s + rejoinAnalysis.effectivePitDelta) / 40) * 100)}%`,
            }}
          />
          <div
            className="absolute top-0 bottom-0 w-2 bg-apex-cyan rounded-full"
            style={{
              left: `${Math.min(95, ((playerCar.gap_to_leader_s + rejoinAnalysis.effectivePitDelta) / 40) * 100)}%`,
            }}
          />
        </div>
      </div>
    </div>
  );
};
