import React, { useState, useMemo } from 'react';
import { useRaceStore } from '../store/raceStore';
import { Navigation, Flag, CloudRain, ShieldAlert, Sparkles, Activity, Layers, Box } from 'lucide-react';
import { CIRCUIT_DATABASE, CircuitData } from '../data/trackGeometries';
import { CarState } from '../types/race';
import { LinearTrackRibbon } from './LinearTrackRibbon';
import { Track3DDigitalTwin } from './Track3DDigitalTwin';

export type TrackViewMode = 'circuit' | '3d_twin' | 'heatmap' | 'ribbon';

export const TrackMap: React.FC = () => {
  const { raceState, selectedCarId, setSelectedCarId, setInspectedCar } = useRaceStore();
  const [viewMode, setViewMode] = useState<TrackViewMode>('3d_twin');

  if (!raceState) return null;

  const { cars, track, weather, safety_car } = raceState;

  // Resolve circuit geometry based on track name
  const circuitKey =
    Object.keys(CIRCUIT_DATABASE).find(
      (k) =>
        track.name.toLowerCase().includes(k) ||
        CIRCUIT_DATABASE[k].name.toLowerCase().includes(track.name.toLowerCase())
    ) || 'silverstone';

  const circuit: CircuitData = CIRCUIT_DATABASE[circuitKey] || CIRCUIT_DATABASE.silverstone;

  // Interpolate car positions along circuit waypoints
  const carCoordinates = useMemo(() => {
    const waypoints = circuit.waypoints;
    const nWaypoints = waypoints.length;

    return cars.map((car: CarState) => {
      const wpIndex = (car.position - 1) % nWaypoints;
      const wp = waypoints[wpIndex];
      const laneOffset = ((car.car_number % 3) - 1) * 4;

      return {
        ...car,
        x: wp.x + laneOffset,
        y: wp.y + laneOffset,
        sector: wp.sector,
        speedKmh: wp.speedKmh || 290,
      };
    });
  }, [cars, circuit]);

  const isRaining = weather.condition === 'WET' || weather.condition === 'DAMP';

  const handleCarClick = (car: CarState) => {
    setSelectedCarId(car.car_id);
    setInspectedCar(car);
  };

  if (viewMode === '3d_twin') {
    return (
      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between px-1">
          <span className="text-xs font-bold text-slate-400 font-mono flex items-center gap-1.5">
            <Box className="w-3.5 h-3.5 text-apex-cyan" />
            3D SPATIAL DIGITAL TWIN ACTIVE
          </span>
          <div className="flex items-center bg-slate-950 p-0.5 rounded-lg border border-slate-800 text-[10px] font-mono">
            <button
              onClick={() => setViewMode('3d_twin')}
              className="px-2 py-1 rounded bg-apex-cyan text-black font-bold shadow"
            >
              3D WebGL
            </button>
            <button
              onClick={() => setViewMode('circuit')}
              className="px-2 py-1 rounded text-slate-400 hover:text-slate-200"
            >
              2D Vector
            </button>
            <button
              onClick={() => setViewMode('heatmap')}
              className="px-2 py-1 rounded text-slate-400 hover:text-slate-200"
            >
              Heatmap
            </button>
            <button
              onClick={() => setViewMode('ribbon')}
              className="px-2 py-1 rounded text-slate-400 hover:text-slate-200"
            >
              Ribbon
            </button>
          </div>
        </div>
        <Track3DDigitalTwin />
      </div>
    );
  }

  return (
    <div className="glass-panel rounded-xl p-4 flex flex-col h-full border border-apex-border relative overflow-hidden shadow-2xl">
      {/* Title Bar & Mode Switcher */}
      <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
        <div className="flex items-center gap-2">
          <Navigation className="w-4 h-4 text-apex-cyan animate-pulse" />
          <h3 className="text-xs font-black uppercase tracking-widest text-slate-200">
            Live Circuit Tracker — {circuit.name}
          </h3>
        </div>

        {/* View Mode Buttons */}
        <div className="flex items-center bg-slate-950/90 p-0.5 rounded-lg border border-slate-800 text-[10px] font-mono">
          <button
            onClick={() => setViewMode('3d_twin')}
            className="px-2 py-1 rounded text-slate-400 hover:text-slate-200 flex items-center gap-1"
          >
            <Box className="w-3 h-3 text-apex-cyan" />
            <span>3D WebGL</span>
          </button>
          <button
            onClick={() => setViewMode('circuit')}
            className={`px-2 py-1 rounded transition-all ${
              viewMode === 'circuit'
                ? 'bg-cyan-500 text-black font-bold shadow'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            2D Circuit
          </button>
          <button
            onClick={() => setViewMode('heatmap')}
            className={`px-2 py-1 rounded transition-all ${
              viewMode === 'heatmap'
                ? 'bg-cyan-500 text-black font-bold shadow'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Speed Heatmap
          </button>
          <button
            onClick={() => setViewMode('ribbon')}
            className={`px-2 py-1 rounded transition-all ${
              viewMode === 'ribbon'
                ? 'bg-cyan-500 text-black font-bold shadow'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Linear Gap Ribbon
          </button>
        </div>
      </div>

      {/* Mode 1 & 2: SVG Circuit Canvas */}
      {viewMode !== 'ribbon' ? (
        <div className="relative flex-1 flex items-center justify-center min-h-[250px] bg-slate-950/40 rounded-lg p-2 border border-slate-900 radar-sweep">
          {/* Dynamic Weather Sheen */}
          {isRaining && (
            <div className="absolute inset-0 bg-cyan-950/20 backdrop-blur-[0.5px] pointer-events-none flex items-center justify-center z-10 border border-cyan-500/20 rounded-lg">
              <div className="text-[11px] font-mono text-cyan-300 font-bold uppercase tracking-widest flex items-center gap-2 bg-slate-900/90 px-3 py-1 rounded-full border border-cyan-500/40 shadow-lg shadow-cyan-500/20">
                <CloudRain className="w-4 h-4 text-cyan-400 animate-bounce" />
                <span>WET TRACK CONDITIONS ({(weather.rain_intensity * 100).toFixed(0)}% RAIN)</span>
              </div>
            </div>
          )}

          {/* Safety Car Banner Overlay */}
          {safety_car !== 'NONE' && (
            <div className="absolute top-2 left-2 z-20 flex items-center gap-1.5 px-2.5 py-1 rounded bg-yellow-500/20 border border-yellow-500/60 text-yellow-300 text-[10px] font-mono font-bold animate-pulse">
              <ShieldAlert className="w-3.5 h-3.5" />
              <span>{safety_car === 'SAFETY_CAR' ? 'SAFETY CAR ON TRACK' : 'VIRTUAL SAFETY CAR'}</span>
            </div>
          )}

          <svg
            viewBox={circuit.viewBox}
            className="w-full h-full max-h-[300px] drop-shadow-[0_0_20px_rgba(0,240,255,0.12)]"
          >
            {/* Base Asphalt */}
            <path
              d={circuit.fullPath}
              fill="none"
              stroke="#0b111e"
              strokeWidth="26"
              strokeLinecap="round"
              strokeLinejoin="round"
            />

            {/* Track Outer Kerb */}
            <path
              d={circuit.fullPath}
              fill="none"
              stroke="#1e293b"
              strokeWidth="18"
              strokeLinecap="round"
              strokeLinejoin="round"
            />

            {/* View Mode: Normal Sectors vs Speed Heatmap */}
            {viewMode === 'circuit' ? (
              <>
                {circuit.sectors[0] && (
                  <path
                    d={circuit.sectors[0].path}
                    fill="none"
                    stroke="#00f0ff"
                    strokeWidth="4"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    opacity="0.85"
                  />
                )}
                {circuit.sectors[1] && (
                  <path
                    d={circuit.sectors[1].path}
                    fill="none"
                    stroke="#f59e0b"
                    strokeWidth="4"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    opacity="0.85"
                  />
                )}
                {circuit.sectors[2] && (
                  <path
                    d={circuit.sectors[2].path}
                    fill="none"
                    stroke="#c084fc"
                    strokeWidth="4"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    opacity="0.85"
                  />
                )}
              </>
            ) : (
              // Heatmap Stroke: Red (Slow corner) ➔ Yellow ➔ Green ➔ Cyan (Full Throttle)
              <path
                d={circuit.fullPath}
                fill="none"
                stroke="url(#speedHeatmapGrad)"
                strokeWidth="6"
                strokeLinecap="round"
                strokeLinejoin="round"
                opacity="0.95"
              />
            )}

            {/* Speed Gradient Definition */}
            <defs>
              <linearGradient id="speedHeatmapGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#ef4444" />
                <stop offset="30%" stopColor="#eab308" />
                <stop offset="70%" stopColor="#10b981" />
                <stop offset="100%" stopColor="#00f0ff" />
              </linearGradient>
            </defs>

            {/* DRS Zones */}
            {circuit.drsZones.map((drs, idx) => (
              <path
                key={idx}
                d={drs.path}
                fill="none"
                stroke="#10b981"
                strokeWidth="5"
                strokeDasharray="4 4"
                className="animate-pulse"
                opacity="0.95"
              />
            ))}

            {/* Start / Finish Line */}
            <line
              x1={circuit.startFinishLine.x1}
              y1={circuit.startFinishLine.y1}
              x2={circuit.startFinishLine.x2}
              y2={circuit.startFinishLine.y2}
              stroke="#ffffff"
              strokeWidth="3.5"
              strokeDasharray="3 3"
            />

            {/* Corner Labels */}
            {circuit.corners.map((c) => (
              <g key={c.number} transform={`translate(${c.x}, ${c.y})`} className="select-none opacity-40 hover:opacity-100 transition-opacity">
                <circle r="4" fill="#0f172a" stroke="#475569" strokeWidth="1" />
                <text
                  x="0"
                  y="2.5"
                  textAnchor="middle"
                  fontSize="6"
                  fill="#94a3b8"
                  fontFamily="monospace"
                  fontWeight="bold"
                >
                  {c.number}
                </text>
              </g>
            ))}

            {/* Moving Cars */}
            {carCoordinates.map((car) => {
              const isPlayer = car.is_player;
              const isSelected = selectedCarId === car.car_id;

              return (
                <g
                  key={car.car_id}
                  className="transition-all duration-500 ease-out cursor-pointer group"
                  transform={`translate(${car.x}, ${car.y})`}
                  onClick={() => handleCarClick(car)}
                >
                  {isPlayer && (
                    <circle
                      r="15"
                      fill="none"
                      stroke="#00f0ff"
                      strokeWidth="2"
                      className="animate-ping opacity-75"
                    />
                  )}

                  {isSelected && !isPlayer && (
                    <circle
                      r="12"
                      fill="none"
                      stroke="#f59e0b"
                      strokeWidth="2"
                      className="animate-pulse"
                    />
                  )}

                  <circle
                    r={isPlayer ? '8' : '6'}
                    fill={isPlayer ? '#00f0ff' : '#64748b'}
                    stroke={isPlayer ? '#ffffff' : '#0f172a'}
                    strokeWidth="2"
                    className={isPlayer ? 'filter drop-shadow-[0_0_10px_#00f0ff]' : 'group-hover:fill-slate-300'}
                  />

                  <rect
                    x="-12"
                    y="-20"
                    width="24"
                    height="13"
                    rx="3"
                    fill={isPlayer ? '#083344' : '#0f172a'}
                    stroke={isPlayer ? '#00f0ff' : isSelected ? '#f59e0b' : '#334155'}
                    strokeWidth="1.2"
                  />
                  <text
                    x="0"
                    y="-10.5"
                    textAnchor="middle"
                    fill={isPlayer ? '#00f0ff' : '#f1f5f9'}
                    fontSize="8.5"
                    fontWeight="900"
                    fontFamily="monospace"
                  >
                    P{car.position}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>
      ) : (
        // Mode 3: Linear Track Ribbon
        <div className="flex-1 flex flex-col justify-center">
          <LinearTrackRibbon />
        </div>
      )}

      {/* Track Stats Footer */}
      <div className="grid grid-cols-4 gap-2 pt-2.5 border-t border-slate-800 text-center font-mono text-[11px] mt-2">
        <div className="bg-slate-900/70 p-1.5 rounded border border-slate-800/60">
          <span className="text-[9px] text-slate-500 font-sans block font-semibold">Distance</span>
          <span className="text-slate-200 font-bold">{circuit.lengthKm} km</span>
        </div>
        <div className="bg-slate-900/70 p-1.5 rounded border border-slate-800/60">
          <span className="text-[9px] text-slate-500 font-sans block font-semibold">Base Lap</span>
          <span className="text-slate-200 font-bold">{circuit.baseLapS}s</span>
        </div>
        <div className="bg-slate-900/70 p-1.5 rounded border border-slate-800/60">
          <span className="text-[9px] text-slate-500 font-sans block font-semibold">Pit Delta</span>
          <span className="text-slate-200 font-bold">~{track.pit_lane_delta_s}s</span>
        </div>
        <div className="bg-slate-900/70 p-1.5 rounded border border-slate-800/60">
          <span className="text-[9px] text-slate-500 font-sans block font-semibold">Track Temp</span>
          <span className="text-amber-300 font-bold">{weather.track_temp_c.toFixed(1)}°C</span>
        </div>
      </div>
    </div>
  );
};
