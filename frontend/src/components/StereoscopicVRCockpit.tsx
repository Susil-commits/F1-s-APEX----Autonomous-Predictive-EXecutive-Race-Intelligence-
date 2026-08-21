import React, { useState, useEffect, useRef } from 'react';
import { useRaceStore } from '../store/raceStore';
import { Glasses, Headset, Compass, Gauge, Zap, Eye, Move } from 'lucide-react';

export const StereoscopicVRCockpit: React.FC = () => {
  const { raceState } = useRaceStore();
  const player = raceState?.cars.find((c) => c.is_player) || raceState?.cars[0];

  const [headPitchDeg, setHeadPitchDeg] = useState<number>(0);
  const [headYawDeg, setHeadYawDeg] = useState<number>(0);
  const [ipdMm, setIpdMm] = useState<number>(64); // Interpupillary distance in mm

  const speedKmh = player?.speed_kmh ?? 295;
  const gear = speedKmh > 270 ? 8 : speedKmh > 220 ? 7 : speedKmh > 175 ? 6 : 5;

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const xRatio = (e.clientX - rect.left) / rect.width - 0.5;
    const yRatio = (e.clientY - rect.top) / rect.height - 0.5;

    setHeadYawDeg(Math.round(xRatio * 50));
    setHeadPitchDeg(Math.round(-yRatio * 35));
  };

  const renderEyeViewport = (isLeft: boolean) => {
    const parallaxOffset = isLeft ? -ipdMm * 0.15 : ipdMm * 0.15;

    return (
      <div className="relative flex-1 h-full overflow-hidden bg-slate-950 rounded-2xl border-2 border-slate-800 flex items-center justify-center">
        {/* Cockpit Horizon & 3D Parallax Transform */}
        <div
          style={{
            transform: `perspective(600px) rotateX(${headPitchDeg}deg) rotateY(${headYawDeg}deg) translateX(${parallaxOffset}px)`,
          }}
          className="relative w-full h-full flex items-center justify-center transition-transform duration-75"
        >
          {/* Simulated 3D Track Apex & Horizon */}
          <div className="absolute inset-0 bg-gradient-to-b from-sky-950 via-slate-950 to-neutral-950 opacity-90" />

          {/* Halo Center Pillar */}
          <div className="w-6 h-64 bg-slate-800 rounded-b-md shadow-2xl border-x border-slate-700 z-10" />

          {/* Floating Spatial Micro-OLED Reticle HUD */}
          <div className="absolute top-12 flex flex-col items-center bg-black/70 backdrop-blur-md px-4 py-2 rounded-xl border border-cyan-500/40 font-mono z-20 shadow-lg shadow-cyan-500/10">
            <span className="text-[9px] text-slate-400 font-bold uppercase">
              {isLeft ? 'LEFT EYE 3D VIEW' : 'RIGHT EYE 3D VIEW'}
            </span>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-black text-white">{Math.round(speedKmh)}</span>
              <span className="text-[10px] text-slate-400">KM/H</span>
              <span className="text-xl font-black text-amber-400">G{gear}</span>
            </div>
            <span className="text-[10px] text-emerald-400 font-bold">DELTA: -0.184s</span>
          </div>

          {/* Steering Wheel Display Arc */}
          <div className="absolute -bottom-16 w-80 h-44 rounded-t-[120px] bg-slate-900 border-4 border-slate-800 shadow-2xl flex flex-col items-center pt-4 z-15">
            <div className="flex gap-1">
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
              ))}
              {[6, 7, 8, 9, 10].map((i) => (
                <div key={i} className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-pulse" />
              ))}
            </div>
          </div>
        </div>

        {/* Circular Vignette Overlay for VR Lenses */}
        <div className="absolute inset-0 rounded-2xl pointer-events-none shadow-[inset_0_0_60px_rgba(0,0,0,0.9)]" />
      </div>
    );
  };

  return (
    <div className="w-full rounded-2xl bg-slate-950 border border-slate-800 p-4 flex flex-col gap-4 shadow-2xl">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Headset className="w-5 h-5 text-indigo-400 animate-pulse" />
          <div className="flex flex-col">
            <span className="font-bold text-white text-sm">
              WEBXR STEREOSCOPIC 3D VR COCKPIT SIMULATION MODE
            </span>
            <span className="text-[11px] font-mono text-slate-400">
              Dual-eye stereoscopic ocular rendering, 6DoF head-tracking emulation & spatial floating HUD
            </span>
          </div>
        </div>

        {/* IPD Slider */}
        <div className="flex items-center gap-3 bg-slate-900 px-3 py-1.5 rounded-xl border border-slate-800 text-xs font-mono">
          <span className="text-slate-400">Interpupillary Distance (IPD):</span>
          <span className="font-bold text-apex-cyan">{ipdMm} mm</span>
          <input
            type="range"
            min={58}
            max={72}
            value={ipdMm}
            onChange={(e) => setIpdMm(Number(e.target.value))}
            className="w-24 accent-indigo-500 cursor-pointer"
          />
        </div>
      </div>

      {/* Dual Eye Stereoscopic Viewport */}
      <div
        onMouseMove={handleMouseMove}
        className="w-full h-[450px] rounded-2xl bg-black p-3 flex gap-3 cursor-move select-none"
      >
        {renderEyeViewport(true)}
        {renderEyeViewport(false)}
      </div>

      {/* Head Orientation Metrics */}
      <div className="flex flex-wrap items-center justify-between gap-2 p-3 rounded-xl bg-slate-900/80 border border-slate-800 text-xs font-mono">
        <div className="flex items-center gap-2">
          <Move className="w-4 h-4 text-indigo-400" />
          <span className="text-slate-400">6DoF Head Tracking: </span>
          <span className="text-white font-bold">Yaw: {headYawDeg}°</span>
          <span className="text-white font-bold">Pitch: {headPitchDeg}°</span>
        </div>
        <span className="text-slate-500">Move cursor over cockpit to rotate spatial field of view</span>
      </div>
    </div>
  );
};
