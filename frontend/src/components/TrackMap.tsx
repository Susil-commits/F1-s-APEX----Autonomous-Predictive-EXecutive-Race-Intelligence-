import React, { useMemo } from 'react';
import { useRaceStore } from '../store/raceStore';
import { Navigation, Flag } from 'lucide-react';

export const TrackMap: React.FC = () => {
  const { raceState } = useRaceStore();

  if (!raceState) return null;

  const { cars, track, weather } = raceState;

  // Silverstone-inspired geometric SVG path coordinates
  // Width: 600, Height: 320
  const trackPath = "M 90 220 C 60 160 80 80 160 70 C 230 60 270 120 340 100 C 400 80 480 50 540 110 C 570 150 530 220 460 210 C 410 200 390 260 320 260 C 250 260 230 180 180 180 C 140 180 120 250 90 220 Z";

  // Compute normalized point along path for each car based on position
  const totalCars = Math.max(1, cars.length);

  // Path points approximation for smooth 2D placement
  const carCoordinates = useMemo(() => {
    // 10 reference waypoints around the track loop
    const waypoints = [
      { x: 120, y: 70 },  // Turn 1
      { x: 230, y: 75 },  // Maggotts
      { x: 340, y: 100 }, // Becketts
      { x: 440, y: 70 },  // Chapel
      { x: 535, y: 120 }, // Stowe
      { x: 480, y: 205 }, // Vale
      { x: 380, y: 220 }, // Club
      { x: 310, y: 260 }, // Abbey
      { x: 200, y: 200 }, // Farm
      { x: 100, y: 225 }, // Luffield / Pit Straight
    ];

    return cars.map((car) => {
      // Map car's relative lap position to a coordinate
      const index = (car.position - 1) % waypoints.length;
      const wp = waypoints[index];
      // Micro offset for realism
      const offset = (car.car_number % 5) * 3 - 6;
      return {
        ...car,
        x: wp.x + offset,
        y: wp.y + offset,
      };
    });
  }, [cars]);

  const isRaining = weather.condition === 'WET' || weather.condition === 'DAMP';

  return (
    <div className="glass-panel rounded-xl p-4 flex flex-col h-full border border-apex-border relative overflow-hidden shadow-2xl">
      {/* Title Bar */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <Navigation className="w-4 h-4 text-apex-cyan" />
          <h3 className="text-xs font-extrabold uppercase tracking-widest text-slate-200">
            Live Circuit Tracker — {track.name}
          </h3>
        </div>
        <div className="flex items-center gap-3 text-[11px] font-mono text-slate-400">
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-cyan-400" /> APEX (You)
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-slate-400" /> Competitors
          </span>
        </div>
      </div>

      {/* SVG Circuit Canvas */}
      <div className="relative flex-1 flex items-center justify-center min-h-[220px]">
        {/* Dynamic Rain Overlay */}
        {isRaining && (
          <div className="absolute inset-0 bg-blue-950/20 backdrop-blur-[0.5px] pointer-events-none flex items-center justify-center z-0">
            <div className="text-[11px] font-mono text-cyan-300/60 font-semibold uppercase tracking-widest animate-pulse">
              TRACK: {weather.condition} ({(weather.rain_intensity * 100).toFixed(0)}% RAIN)
            </div>
          </div>
        )}

        <svg
          viewBox="0 0 620 330"
          className="w-full h-full max-h-[280px] drop-shadow-[0_0_15px_rgba(0,240,255,0.15)]"
        >
          {/* Circuit Outline Base */}
          <path
            d={trackPath}
            fill="none"
            stroke="#1e293b"
            strokeWidth="24"
            strokeLinecap="round"
            strokeLinejoin="round"
          />

          {/* Circuit Racing Line */}
          <path
            d={trackPath}
            fill="none"
            stroke="#334155"
            strokeWidth="14"
            strokeLinecap="round"
            strokeLinejoin="round"
          />

          {/* DRS Zone 1 (Green Accent) */}
          <path
            d="M 230 60 C 270 120 340 100 400 80"
            fill="none"
            stroke="#10b981"
            strokeWidth="5"
            strokeDasharray="4,4"
            opacity="0.8"
          />

          {/* Start / Finish Line */}
          <line
            x1="90"
            y1="205"
            x2="90"
            y2="235"
            stroke="#ffffff"
            strokeWidth="4"
            strokeDasharray="2,2"
          />

          {/* Render Moving Cars */}
          {carCoordinates.map((car) => {
            const isPlayer = car.is_player;
            return (
              <g
                key={car.car_id}
                className="transition-all duration-700 ease-out cursor-pointer"
                transform={`translate(${car.x}, ${car.y})`}
              >
                {/* Glow Ring for Player */}
                {isPlayer && (
                  <circle
                    r="14"
                    fill="none"
                    stroke="#00f0ff"
                    strokeWidth="2"
                    className="animate-ping opacity-60"
                  />
                )}

                {/* Car Marker Body */}
                <circle
                  r={isPlayer ? '8' : '6'}
                  fill={isPlayer ? '#00f0ff' : '#94a3b8'}
                  stroke={isPlayer ? '#ffffff' : '#0f172a'}
                  strokeWidth="2"
                  className={isPlayer ? 'filter drop-shadow-[0_0_8px_#00f0ff]' : ''}
                />

                {/* Position Badge Label */}
                <rect
                  x="-10"
                  y="-18"
                  width="20"
                  height="12"
                  rx="3"
                  fill={isPlayer ? '#083344' : '#1e293b'}
                  stroke={isPlayer ? '#00f0ff' : '#475569'}
                  strokeWidth="1"
                />
                <text
                  x="0"
                  y="-9"
                  textAnchor="middle"
                  fill={isPlayer ? '#00f0ff' : '#f1f5f9'}
                  fontSize="8"
                  fontWeight="bold"
                  fontFamily="monospace"
                >
                  P{car.position}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      {/* Track Stats Footer */}
      <div className="grid grid-cols-4 gap-2 pt-2 border-t border-slate-800 text-center font-mono text-[11px]">
        <div className="bg-slate-900/60 p-1.5 rounded">
          <span className="text-[10px] text-slate-500 font-sans block">Distance</span>
          <span className="text-slate-200 font-bold">{track.lap_distance_km} km</span>
        </div>
        <div className="bg-slate-900/60 p-1.5 rounded">
          <span className="text-[10px] text-slate-500 font-sans block">Base Lap</span>
          <span className="text-slate-200 font-bold">{track.base_lap_time_s}s</span>
        </div>
        <div className="bg-slate-900/60 p-1.5 rounded">
          <span className="text-[10px] text-slate-500 font-sans block">Pit Delta</span>
          <span className="text-slate-200 font-bold">~{track.pit_lane_delta_s}s</span>
        </div>
        <div className="bg-slate-900/60 p-1.5 rounded">
          <span className="text-[10px] text-slate-500 font-sans block">Track Temp</span>
          <span className="text-amber-300 font-bold">{weather.track_temp_c.toFixed(1)}°C</span>
        </div>
      </div>
    </div>
  );
};
