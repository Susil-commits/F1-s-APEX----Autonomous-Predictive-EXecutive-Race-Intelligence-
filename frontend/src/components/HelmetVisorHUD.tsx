import React, { useState, useEffect, useRef } from 'react';
import { useRaceStore } from '../store/raceStore';
import { Eye, CloudRain, Sun, Zap, RotateCcw, Award, Gauge } from 'lucide-react';
import confetti from 'canvas-confetti';

interface Droplet {
  x: number;
  y: number;
  radius: number;
  speedX: number;
  speedY: number;
  streakLength: number;
}

export const HelmetVisorHUD: React.FC = () => {
  const { raceState } = useRaceStore();
  const player = raceState?.cars.find((c) => c.is_player) || raceState?.cars[0];

  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  const [tearOffsRemaining, setTearOffsRemaining] = useState<number>(4);
  const [visorTint, setVisorTint] = useState<'CLEAR' | 'DARK_SMOKE' | 'AMBER'>('DARK_SMOKE');
  const [isTearingOff, setIsTearingOff] = useState<boolean>(false);

  const speedKmh = player?.speed_kmh ?? 285;
  const isWet = raceState?.weather?.condition === 'WET' || raceState?.weather?.condition === 'DAMP';

  // Water droplets physics
  const dropletsRef = useRef<Droplet[]>([]);

  useEffect(() => {
    // Generate initial droplets
    const drops: Droplet[] = [];
    for (let i = 0; i < 45; i++) {
      drops.push({
        x: Math.random() * 800,
        y: Math.random() * 380,
        radius: 1.5 + Math.random() * 3,
        speedX: 0,
        speedY: 0.5 + Math.random() * 1.5,
        streakLength: 0,
      });
    }
    dropletsRef.current = drops;
  }, []);

  // Animation Loop for Aerodynamic Droplet Streaking
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animId: number;
    const width = canvas.width;
    const height = canvas.height;

    const renderVisor = () => {
      ctx.clearRect(0, 0, width, height);

      // Draw Visor Tint Overlay
      if (visorTint === 'DARK_SMOKE') {
        ctx.fillStyle = 'rgba(15, 23, 42, 0.45)';
      } else if (visorTint === 'AMBER') {
        ctx.fillStyle = 'rgba(245, 158, 11, 0.18)';
      } else {
        ctx.fillStyle = 'rgba(255, 255, 255, 0.05)';
      }
      ctx.fillRect(0, 0, width, height);

      // Speed-dependent aerodynamic streak factor
      const streakFactor = Math.max(0, (speedKmh - 100) / 180);

      // Render Droplets
      ctx.fillStyle = 'rgba(255, 255, 255, 0.75)';
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.6)';

      dropletsRef.current.forEach((d) => {
        // High speed blows droplets towards the edges laterally
        const dirX = d.x > width / 2 ? 1 : -1;
        d.x += dirX * streakFactor * 3.5;
        d.y += (1 - streakFactor * 0.5) * 1.2;

        if (streakFactor > 0.3) {
          // Draw streak tail
          ctx.lineWidth = d.radius * 0.8;
          ctx.beginPath();
          ctx.moveTo(d.x, d.y);
          ctx.lineTo(d.x - dirX * streakFactor * 25, d.y - 8);
          ctx.stroke();
        } else {
          // Draw spherical bead
          ctx.beginPath();
          ctx.arc(d.x, d.y, d.radius, 0, Math.PI * 2);
          ctx.fill();
        }

        // Respawn off-screen drops
        if (d.x < 0 || d.x > width || d.y > height) {
          d.x = Math.random() * width;
          d.y = 0;
        }
      });

      animId = requestAnimationFrame(renderVisor);
    };

    renderVisor();
    return () => cancelAnimationFrame(animId);
  }, [speedKmh, visorTint]);

  const handleTearOff = () => {
    if (tearOffsRemaining <= 0 || isTearingOff) return;

    setIsTearingOff(true);
    confetti({ particleCount: 35, spread: 45, origin: { x: 0.8, y: 0.5 } });

    // Clear droplets immediately
    dropletsRef.current = [];

    setTimeout(() => {
      // Regenerate fresh light droplets
      const newDrops: Droplet[] = [];
      for (let i = 0; i < 15; i++) {
        newDrops.push({
          x: Math.random() * 800,
          y: Math.random() * 100,
          radius: 1.5 + Math.random() * 2,
          speedX: 0,
          speedY: 1,
          streakLength: 0,
        });
      }
      dropletsRef.current = newDrops;
      setTearOffsRemaining((prev) => Math.max(0, prev - 1));
      setIsTearingOff(false);
    }, 450);
  };

  return (
    <div className="w-full rounded-2xl bg-slate-950 border border-slate-800 p-4 flex flex-col gap-4 shadow-2xl">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Eye className="w-5 h-5 text-apex-cyan animate-pulse" />
          <div className="flex flex-col">
            <span className="font-bold text-white text-sm">
              DRIVER IN-HELMET VISOR TEAR-OFF & AERODYNAMIC WATER BEADING HUD
            </span>
            <span className="text-[11px] font-mono text-slate-400">
              First-person helmet viewport with speed-dependent water streak physics & micro-OLED telemetry HUD
            </span>
          </div>
        </div>

        {/* Visor Tint Selector */}
        <div className="flex items-center gap-2">
          <div className="flex items-center bg-slate-900 p-1 rounded-xl border border-slate-800 text-xs font-mono">
            {(['CLEAR', 'DARK_SMOKE', 'AMBER'] as const).map((tint) => (
              <button
                key={tint}
                onClick={() => setVisorTint(tint)}
                className={`px-2.5 py-1 rounded-lg transition-all ${
                  visorTint === tint ? 'bg-apex-cyan text-black font-bold' : 'text-slate-400'
                }`}
              >
                {tint.replace(/_/g, ' ')}
              </button>
            ))}
          </div>

          {/* Tear-Off Action Button */}
          <button
            onClick={handleTearOff}
            disabled={tearOffsRemaining <= 0 || isTearingOff}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-amber-500 hover:bg-amber-400 disabled:opacity-40 text-black font-mono text-xs font-bold transition-all active:scale-95 shadow-md shadow-amber-500/20"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>PULL TEAR-OFF ({tearOffsRemaining})</span>
          </button>
        </div>
      </div>

      {/* Main Helmet Viewport Screen */}
      <div className="relative w-full h-[420px] rounded-2xl overflow-hidden bg-slate-950 border-4 border-slate-900 shadow-2xl flex items-center justify-center">
        {/* Cockpit Horizon Background Silhouette */}
        <div className="absolute inset-0 bg-gradient-to-t from-slate-900 via-slate-950 to-black pointer-events-none opacity-80" />

        {/* Canvas for Rain Streaking */}
        <canvas
          ref={canvasRef}
          width={900}
          height={420}
          className={`absolute inset-0 w-full h-full transition-transform duration-300 ${
            isTearingOff ? 'translate-x-full opacity-30' : 'translate-x-0 opacity-100'
          }`}
        />

        {/* In-Visor Micro-OLED Heads-Up Display */}
        <div className="absolute top-6 left-8 right-8 flex justify-between items-start pointer-events-none font-mono z-20">
          {/* Left HUD: Speed & Gear */}
          <div className="flex items-baseline gap-3 bg-black/60 backdrop-blur-md px-4 py-2 rounded-xl border border-cyan-500/40">
            <span className="text-3xl font-black text-white">{Math.round(speedKmh)}</span>
            <span className="text-xs text-slate-400 font-bold">KM/H</span>
            <div className="w-px h-6 bg-slate-700 mx-1" />
            <span className="text-2xl font-black text-amber-400">
              GEAR {speedKmh > 260 ? '7' : speedKmh > 200 ? '6' : '5'}
            </span>
          </div>

          {/* Center HUD: Live Delta Bar */}
          <div className="flex flex-col items-center bg-black/60 backdrop-blur-md px-4 py-2 rounded-xl border border-cyan-500/40">
            <span className="text-[10px] text-slate-400 font-bold uppercase">DELTA TO BEST LAP</span>
            <span className="text-xl font-black text-emerald-400">-0.142s</span>
          </div>

          {/* Right HUD: ERS & Engine Mode */}
          <div className="flex flex-col items-end bg-black/60 backdrop-blur-md px-4 py-2 rounded-xl border border-cyan-500/40">
            <span className="text-xs font-bold text-pink-400">
              ERS: {Math.round(player?.ers_battery_soc_pct ?? 84)}%
            </span>
            <span className="text-[10px] text-slate-300 font-bold uppercase">
              MODE: {player?.driving_mode || 'PUSH'}
            </span>
          </div>
        </div>

        {/* Halo Frame & Steering Arc Outline Overlay */}
        <div className="absolute bottom-0 inset-x-0 h-28 bg-gradient-to-t from-black via-black/80 to-transparent flex items-end justify-center pointer-events-none">
          <div className="w-80 h-14 rounded-t-full border-t-4 border-slate-700 bg-slate-900/90 shadow-2xl flex items-center justify-center font-mono text-[10px] text-slate-500">
            FIA CARBON HALO REINFORCEMENT
          </div>
        </div>
      </div>
    </div>
  );
};
