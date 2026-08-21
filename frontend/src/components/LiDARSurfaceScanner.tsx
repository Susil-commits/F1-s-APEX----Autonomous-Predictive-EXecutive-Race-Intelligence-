import React, { useState, useMemo } from 'react';
import { useRaceStore } from '../store/raceStore';
import { Layers, Scan, Compass, ShieldAlert, Sparkles, Activity, CheckCircle2 } from 'lucide-react';

export const LiDARSurfaceScanner: React.FC = () => {
  const { raceState } = useRaceStore();

  const [selectedScanSector, setSelectedScanSector] = useState<'TURN_1_APEX' | 'HIGH_SPEED_EXIT_KERB' | 'PIT_STRAIGHT'>('TURN_1_APEX');
  const [laserBeamDensity, setLaserBeamDensity] = useState<number>(2500);

  // Micro-surface metrics
  const surfaceMetrics = useMemo(() => {
    if (selectedScanSector === 'TURN_1_APEX') {
      return {
        roughnessRaMicrons: 38.4,
        curbHeightMm: 25.0,
        camberAngleDeg: 2.8,
        frictionCoeff: 1.42,
        tarmacType: 'Aggressive High-Grip Granite Aggregate',
        curbType: 'Beveled 25mm Apex Steel-Reinforced',
      };
    } else if (selectedScanSector === 'HIGH_SPEED_EXIT_KERB') {
      return {
        roughnessRaMicrons: 52.1,
        curbHeightMm: 50.0,
        camberAngleDeg: 1.5,
        frictionCoeff: 1.15,
        tarmacType: 'Sawtooth Exit Vibration Kerb',
        curbType: 'Aggressive 50mm Ribbed Sawtooth',
      };
    } else {
      return {
        roughnessRaMicrons: 22.0,
        curbHeightMm: 0.0,
        camberAngleDeg: 1.2,
        frictionCoeff: 1.35,
        tarmacType: 'Smooth Polymer-Modified Asphalt',
        curbType: 'Flat White Line Border',
      };
    }
  }, [selectedScanSector]);

  return (
    <div className="w-full rounded-2xl bg-slate-950 border border-slate-800 p-4 flex flex-col gap-4 shadow-2xl">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Scan className="w-5 h-5 text-emerald-400 animate-pulse" />
          <div className="flex flex-col">
            <span className="font-bold text-white text-sm">
              LIDAR 3D TRACK SURFACE LASER SCAN & MICRO-ROUGHNESS PROFILER
            </span>
            <span className="text-[11px] font-mono text-slate-400">
              Sub-millimeter laser point cloud, kerb sawtooth cross-sections & tarmac macro-texture friction analysis
            </span>
          </div>
        </div>

        {/* Sector Selector */}
        <div className="flex items-center bg-slate-900 p-1 rounded-xl border border-slate-800 text-xs font-mono">
          <button
            onClick={() => setSelectedScanSector('TURN_1_APEX')}
            className={`px-3 py-1 rounded-lg transition-all ${
              selectedScanSector === 'TURN_1_APEX' ? 'bg-emerald-500 text-black font-bold' : 'text-slate-400'
            }`}
          >
            Turn 1 Apex Kerb
          </button>
          <button
            onClick={() => setSelectedScanSector('HIGH_SPEED_EXIT_KERB')}
            className={`px-3 py-1 rounded-lg transition-all ${
              selectedScanSector === 'HIGH_SPEED_EXIT_KERB' ? 'bg-emerald-500 text-black font-bold' : 'text-slate-400'
            }`}
          >
            Exit Sawtooth Kerb
          </button>
          <button
            onClick={() => setSelectedScanSector('PIT_STRAIGHT')}
            className={`px-3 py-1 rounded-lg transition-all ${
              selectedScanSector === 'PIT_STRAIGHT' ? 'bg-emerald-500 text-black font-bold' : 'text-slate-400'
            }`}
          >
            Pit Straight Asphalt
          </button>
        </div>
      </div>

      {/* Primary LiDAR KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] font-mono text-slate-400 uppercase">TARMAC MICRO-ROUGHNESS (RA)</span>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-black font-mono text-emerald-400">
              {surfaceMetrics.roughnessRaMicrons}
            </span>
            <span className="text-xs font-mono text-slate-400">µM</span>
          </div>
          <span className="text-[10px] font-mono text-slate-400">Aggregate Macro-Texture</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] font-mono text-slate-400 uppercase">KERB STEP HEIGHT</span>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-black font-mono text-amber-400">
              {surfaceMetrics.curbHeightMm}
            </span>
            <span className="text-xs font-mono text-slate-400">MM</span>
          </div>
          <span className="text-[10px] font-mono text-slate-400">{surfaceMetrics.curbType}</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] font-mono text-slate-400 uppercase">DRAINAGE CAMBER ANGLE</span>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-black font-mono text-apex-cyan">
              {surfaceMetrics.camberAngleDeg}°
            </span>
          </div>
          <span className="text-[10px] font-mono text-slate-400">Lateral Water Shed Slope</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] font-mono text-slate-400 uppercase">PEAK FRICTION (µ)</span>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-black font-mono text-purple-400">
              {surfaceMetrics.frictionCoeff}
            </span>
          </div>
          <span className="text-[10px] font-mono text-slate-400">Dry Rubbered Adhesion</span>
        </div>
      </div>

      {/* Interactive Laser Scan Point Cloud Elevation CAD Profile */}
      <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col gap-2">
        <div className="flex justify-between items-center text-xs font-mono">
          <span className="font-bold text-slate-300 uppercase">
            3D LIDAR ELEVATION POINT CLOUD & CROSS-SECTION PROFILE
          </span>
          <span className="text-emerald-400 font-bold">2.5M PTS/SEC LASER SCAN</span>
        </div>

        <div className="relative w-full h-56 rounded-lg overflow-hidden bg-black/90 border border-slate-800 p-4 flex items-center justify-center">
          <svg viewBox="0 0 600 200" className="w-full h-full">
            {/* Grid Lines */}
            <line x1="40" y1="160" x2="560" y2="160" stroke="#334155" strokeWidth="1" strokeDasharray="4 4" />
            <text x="50" y="180" fill="#64748b" fontSize="9" fontFamily="monospace">
              Datum Surface (0.0 mm)
            </text>

            {/* Laser Point Cloud Curve */}
            {selectedScanSector === 'HIGH_SPEED_EXIT_KERB' ? (
              <path
                d="M 50 160 L 220 160 L 230 110 L 260 160 L 270 110 L 300 160 L 310 110 L 340 160 L 550 160"
                fill="none"
                stroke="#22c55e"
                strokeWidth="3"
              />
            ) : selectedScanSector === 'TURN_1_APEX' ? (
              <path
                d="M 50 160 L 240 160 Q 300 125 360 145 L 550 160"
                fill="none"
                stroke="#00f0ff"
                strokeWidth="3"
              />
            ) : (
              <line x1="50" y1="160" x2="550" y2="160" stroke="#a855f7" strokeWidth="3" />
            )}

            {/* Laser Scan Sweep Line */}
            <line x1="300" y1="20" x2="300" y2="160" stroke="#ef4444" strokeWidth="1.5" strokeDasharray="2 2" />
            <text x="310" y="45" fill="#ef4444" fontSize="10" fontFamily="monospace" fontWeight="bold">
              Laser Target: {surfaceMetrics.curbHeightMm} mm
            </text>
          </svg>
        </div>
      </div>
    </div>
  );
};
