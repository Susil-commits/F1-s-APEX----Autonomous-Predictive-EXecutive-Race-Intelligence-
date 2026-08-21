import React, { useState, useEffect, useRef } from 'react';
import { useRaceStore } from '../store/raceStore';
import { CloudRain, Wind, Compass, Droplets, Thermometer, Clock, ShieldAlert } from 'lucide-react';

export const SatelliteDopplerRadar: React.FC = () => {
  const { raceState } = useRaceStore();
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  const [stormHeadingDeg, setStormHeadingDeg] = useState<number>(68);
  const [stormSpeedKmh, setStormSpeedKmh] = useState<number>(34);
  const [sector1ArrivalSec, setSector1ArrivalSec] = useState<number>(254);
  const [waterDepthMm, setWaterDepthMm] = useState<number>(0.8);

  const weather = raceState?.weather;

  // Animated 360-degree Doppler radar sweep
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let angle = 0;
    let animId: number;
    const width = canvas.width;
    const height = canvas.height;
    const centerX = width / 2;
    const centerY = height / 2;
    const maxRadius = Math.min(centerX, centerY) - 20;

    const renderRadar = () => {
      angle = (angle + 0.035) % (Math.PI * 2);

      // Fading background for phosphor trail
      ctx.fillStyle = 'rgba(6, 9, 17, 0.15)';
      ctx.fillRect(0, 0, width, height);

      // Concentric Range Rings (5km, 10km, 15km)
      ctx.strokeStyle = '#1e293b';
      ctx.lineWidth = 1;
      for (let r = 1; r <= 3; r++) {
        ctx.beginPath();
        ctx.arc(centerX, centerY, (maxRadius / 3) * r, 0, Math.PI * 2);
        ctx.stroke();
      }

      // Crosshairs
      ctx.beginPath();
      ctx.moveTo(centerX, 10);
      ctx.lineTo(centerX, height - 10);
      ctx.moveTo(10, centerY);
      ctx.lineTo(width - 10, centerY);
      ctx.stroke();

      // Simulated Advancing Weather Rain Cells (Blobs)
      const cell1X = centerX - 60 + Math.sin(angle * 0.2) * 5;
      const cell1Y = centerY - 50 + Math.cos(angle * 0.2) * 5;

      const grad = ctx.createRadialGradient(cell1X, cell1Y, 10, cell1X, cell1Y, 70);
      grad.addColorStop(0, 'rgba(239, 68, 68, 0.7)'); // 50 dBZ Heavy core
      grad.addColorStop(0.4, 'rgba(245, 158, 11, 0.5)'); // 35 dBZ Moderate
      grad.addColorStop(0.8, 'rgba(34, 197, 94, 0.3)'); // 20 dBZ Light
      grad.addColorStop(1, 'transparent');

      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.arc(cell1X, cell1Y, 70, 0, Math.PI * 2);
      ctx.fill();

      // Rotating Radar Beam Sweep
      const beamX = centerX + Math.cos(angle) * maxRadius;
      const beamY = centerY + Math.sin(angle) * maxRadius;

      const beamGrad = ctx.createLinearGradient(centerX, centerY, beamX, beamY);
      beamGrad.addColorStop(0, '#00f0ff');
      beamGrad.addColorStop(1, 'transparent');

      ctx.strokeStyle = '#00f0ff';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(centerX, centerY);
      ctx.lineTo(beamX, beamY);
      ctx.stroke();

      // Circuit Center Marker
      ctx.fillStyle = '#f59e0b';
      ctx.beginPath();
      ctx.arc(centerX, centerY, 4, 0, Math.PI * 2);
      ctx.fill();

      animId = requestAnimationFrame(renderRadar);
    };

    renderRadar();
    return () => cancelAnimationFrame(animId);
  }, []);

  // Sector Arrival Countdown ticker
  useEffect(() => {
    const interval = setInterval(() => {
      setSector1ArrivalSec((prev) => Math.max(0, prev - 1));
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const formatCountdown = (s: number) => {
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return `${m.toString().padStart(2, '0')}m : ${sec.toString().padStart(2, '0')}s`;
  };

  return (
    <div className="w-full rounded-2xl bg-slate-950 border border-slate-800 p-4 flex flex-col gap-4 shadow-2xl">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <CloudRain className="w-5 h-5 text-cyan-400 animate-pulse" />
          <div className="flex flex-col">
            <span className="font-bold text-white text-sm">
              PADDOCK HIGH-RESOLUTION SATELLITE DOPPLER RAIN RADAR
            </span>
            <span className="text-[11px] font-mono text-slate-400">
              360° precipitation reflectivity (dBZ), storm velocity vectors & micro-climate sector arrival timers
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2 bg-slate-900 px-3 py-1.5 rounded-xl border border-slate-800 text-xs font-mono">
          <Wind className="w-4 h-4 text-apex-cyan" />
          <span className="text-slate-400">Heading: </span>
          <strong className="text-white">{stormHeadingDeg}° ENE</strong>
          <span className="text-slate-400">@</span>
          <strong className="text-apex-cyan">{stormSpeedKmh} km/h</strong>
        </div>
      </div>

      {/* Main Grid: Radar Screen & Sector Timers */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Radar Canvas (Left 7 cols) */}
        <div className="lg:col-span-7 p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col items-center gap-3">
          <div className="flex justify-between w-full text-xs font-mono">
            <span className="text-slate-300 font-bold uppercase">15 KM DOPPLER RADAR SWEEP</span>
            <span className="text-emerald-400 font-bold">SWEEP ACTIVE</span>
          </div>

          <div className="relative w-[340px] h-[340px] rounded-full overflow-hidden border-2 border-slate-800 bg-[#060911] shadow-inner shadow-cyan-500/10">
            <canvas ref={canvasRef} width={340} height={340} className="w-full h-full" />
            <div className="absolute top-2 left-1/2 -translate-x-1/2 text-[9px] font-mono text-slate-400 font-bold">
              N
            </div>
            <div className="absolute bottom-2 left-1/2 -translate-x-1/2 text-[9px] font-mono text-slate-400 font-bold">
              S
            </div>
            <div className="absolute left-2 top-1/2 -translate-y-1/2 text-[9px] font-mono text-slate-400 font-bold">
              W
            </div>
            <div className="absolute right-2 top-1/2 -translate-y-1/2 text-[9px] font-mono text-slate-400 font-bold">
              E
            </div>
          </div>
        </div>

        {/* Sector Arrival Times & Track Grip Impact (Right 5 cols) */}
        <div className="lg:col-span-5 flex flex-col gap-3 font-mono text-xs">
          <span className="font-bold text-amber-400 uppercase border-b border-slate-800 pb-2">
            MICRO-CLIMATE SECTOR PRECIPITATION FORECAST
          </span>

          {/* Sector 1 Timer */}
          <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 flex justify-between items-center">
            <div className="flex flex-col">
              <span className="font-bold text-white">SECTOR 1 (TURNS 1-5)</span>
              <span className="text-[10px] text-rose-400 font-bold">HEAVY RAIN INBOUND</span>
            </div>
            <div className="text-right">
              <span className="text-lg font-black text-amber-400">{formatCountdown(sector1ArrivalSec)}</span>
              <div className="text-[10px] text-slate-400">Est. Intensity: 45 dBZ</div>
            </div>
          </div>

          {/* Sector 2 Timer */}
          <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 flex justify-between items-center">
            <div className="flex flex-col">
              <span className="font-bold text-white">SECTOR 2 (HIGH-SPEED)</span>
              <span className="text-[10px] text-amber-400 font-bold">MODERATE RAIN</span>
            </div>
            <div className="text-right">
              <span className="text-lg font-black text-slate-200">
                {formatCountdown(sector1ArrivalSec + 140)}
              </span>
              <div className="text-[10px] text-slate-400">Est. Intensity: 30 dBZ</div>
            </div>
          </div>

          {/* Sector 3 Timer */}
          <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 flex justify-between items-center">
            <div className="flex flex-col">
              <span className="font-bold text-white">SECTOR 3 (PIT STRAIGHT)</span>
              <span className="text-[10px] text-emerald-400 font-bold">LIGHT SPRAY</span>
            </div>
            <div className="text-right">
              <span className="text-lg font-black text-slate-400">
                {formatCountdown(sector1ArrivalSec + 280)}
              </span>
              <div className="text-[10px] text-slate-400">Est. Intensity: 18 dBZ</div>
            </div>
          </div>

          {/* Grip Crossover Strategy Alert */}
          <div className="p-3.5 rounded-xl bg-slate-950 border border-cyan-500/30 flex flex-col gap-1.5">
            <div className="flex items-center gap-1.5 text-cyan-300 font-bold text-xs">
              <Droplets className="w-4 h-4 text-cyan-400" />
              <span>TYRE CROSSOVER WINDOW: INTERMEDIATES</span>
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Track surface water depth rising to <strong>{waterDepthMm} mm</strong>. Crossover threshold reached in <strong>{formatCountdown(sector1ArrivalSec)}</strong>. Recommend staging Intermediate green compound in pit box.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
