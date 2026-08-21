import React, { useState, useEffect, useRef } from 'react';
import { useRaceStore } from '../store/raceStore';
import { Disc, Zap, Activity, Gauge, Volume2, VolumeX, ShieldAlert, Radio, Maximize2, Minimize2 } from 'lucide-react';

export const SteeringWheelDDU: React.FC = () => {
  const { raceState } = useRaceStore();
  const player = raceState?.cars.find((c) => c.is_player) || raceState?.cars[0];

  // Dynamic DDU State
  const [rpm, setRpm] = useState<number>(11200);
  const [gear, setGear] = useState<number>(6);
  const [speedKmh, setSpeedKmh] = useState<number>(player?.speed_kmh || 295);
  const [brakeBiasPct, setBrakeBiasPct] = useState<number>(56.5);
  const [diffEntry, setDiffEntry] = useState<number>(65);
  const [ersMode, setErsMode] = useState<'BALANCED' | 'OVERTAKE' | 'HOTLAP' | 'HARVEST'>('BALANCED');
  const [audioBeepActive, setAudioBeepActive] = useState<boolean>(true);
  const [isFullScreen, setIsFullScreen] = useState<boolean>(false);

  const audioCtxRef = useRef<AudioContext | null>(null);

  // Play shift beep tone
  const playShiftBeep = () => {
    if (!audioBeepActive) return;
    try {
      if (!audioCtxRef.current) {
        audioCtxRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
      }
      const ctx = audioCtxRef.current;
      if (ctx.state === 'suspended') ctx.resume();

      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(1400, ctx.currentTime);
      gain.gain.setValueAtTime(0.08, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.08);

      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + 0.08);
    } catch (e) {
      // Audio context ignore
    }
  };

  // Simulate dynamic RPM oscillation and gear shifts
  useEffect(() => {
    const interval = setInterval(() => {
      const liveSpeed: number = player?.speed_kmh != null ? player.speed_kmh : 290;
      setSpeedKmh(Math.round(liveSpeed));

      // Calculate approximate gear based on speed
      let g = 1;
      if (liveSpeed > 300) g = 8;
      else if (liveSpeed > 260) g = 7;
      else if (liveSpeed > 215) g = 6;
      else if (liveSpeed > 175) g = 5;
      else if (liveSpeed > 135) g = 4;
      else if (liveSpeed > 95) g = 3;
      else if (liveSpeed > 55) g = 2;

      setGear(g);

      // RPM simulation (10,500 - 13,200 RPM)
      const simulatedRpm = Math.min(13200, Math.max(9800, Math.round(10200 + ((liveSpeed % 45) / 45.0) * 3000)));
      setRpm(simulatedRpm);

      if (simulatedRpm > 12600) {
        playShiftBeep();
      }
    }, 180);

    return () => clearInterval(interval);
  }, [player?.speed_kmh, audioBeepActive]);

  // 15-LED Shift Bar (5 Green, 5 Red, 5 Blue)
  const renderRevLeds = () => {
    const leds = [];
    const rpmRatio = Math.max(0, Math.min(1, (rpm - 10000) / 3000));
    const activeCount = Math.round(rpmRatio * 15);

    for (let i = 0; i < 15; i++) {
      const isActive = i < activeCount;
      let colorClass = 'bg-slate-800 border-slate-700';

      if (isActive) {
        if (i < 5) {
          colorClass = 'bg-emerald-400 border-emerald-300 shadow-sm shadow-emerald-400/80';
        } else if (i < 10) {
          colorClass = 'bg-rose-500 border-rose-400 shadow-sm shadow-rose-500/80';
        } else {
          colorClass = 'bg-cyan-400 border-cyan-300 shadow-sm shadow-cyan-400/80 animate-pulse';
        }
      }

      leds.push(
        <div
          key={i}
          className={`w-3.5 h-6 rounded-sm border transition-all ${colorClass}`}
        />
      );
    }
    return leds;
  };

  const deltaS = -0.218; // Live delta to reference lap
  const deltaColor = deltaS <= 0 ? 'text-emerald-400' : 'text-rose-400';

  return (
    <div
      className={`w-full rounded-2xl bg-slate-950 border border-slate-800 p-4 flex flex-col gap-4 shadow-2xl transition-all ${
        isFullScreen ? 'fixed inset-0 z-50 rounded-none p-6 bg-black overflow-y-auto' : ''
      }`}
    >
      {/* Top Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Gauge className="w-5 h-5 text-apex-cyan animate-pulse" />
          <div className="flex flex-col">
            <span className="font-bold text-white text-sm">
              FIA STEERING WHEEL DIGITAL DASH UNIT (DDU HUD)
            </span>
            <span className="text-[11px] font-mono text-slate-400">
              Cockpit LCD display, 15x Rev Shift LEDs, delta bar, brake bias & ERS rotary controls
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setAudioBeepActive(!audioBeepActive)}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-lg border text-xs font-mono font-bold transition-all ${
              audioBeepActive
                ? 'bg-rose-950/80 text-rose-300 border-rose-700/60 shadow-sm'
                : 'bg-slate-900 text-slate-500 border-slate-800'
            }`}
          >
            {audioBeepActive ? <Volume2 className="w-3.5 h-3.5" /> : <VolumeX className="w-3.5 h-3.5" />}
            <span>SHIFT BEEP</span>
          </button>

          <button
            onClick={() => setIsFullScreen(!isFullScreen)}
            className="p-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-300 transition-all"
            title="Toggle Fullscreen DDU"
          >
            {isFullScreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Main Steering Wheel Physical Frame & LCD Display */}
      <div className="max-w-4xl w-full mx-auto p-4 sm:p-6 rounded-3xl bg-gradient-to-b from-slate-900 via-black to-slate-950 border-4 border-slate-800 shadow-2xl flex flex-col gap-4">
        {/* Top 15-LED Sequential Rev Shift Bar */}
        <div className="flex items-center justify-center gap-1.5 p-2 rounded-xl bg-slate-950/90 border border-slate-800">
          {renderRevLeds()}
        </div>

        {/* Steering Wheel Main LCD Screen */}
        <div className="p-4 sm:p-6 rounded-2xl bg-black border-2 border-slate-700/80 grid grid-cols-1 md:grid-cols-12 gap-4 font-mono">
          {/* Left Column: Speed, Lap, Tyre Temps */}
          <div className="md:col-span-4 flex flex-col justify-between gap-3 border-r border-slate-800/80 pr-4">
            <div className="flex flex-col">
              <span className="text-[10px] text-slate-400 uppercase font-bold tracking-widest">SPEED</span>
              <div className="flex items-baseline gap-1">
                <span className="text-5xl font-black text-white">{speedKmh}</span>
                <span className="text-xs text-slate-400">KM/H</span>
              </div>
            </div>

            <div className="flex justify-between items-center bg-slate-900/60 p-2 rounded-lg border border-slate-800">
              <span className="text-[11px] text-slate-400">LAP:</span>
              <span className="font-bold text-white">
                {raceState?.current_lap || 1} / {raceState?.total_laps || 52}
              </span>
            </div>

            {/* 4 Tyre Temps */}
            <div className="flex flex-col gap-1">
              <span className="text-[9px] text-slate-400 uppercase">TYRE TEMPS (°C)</span>
              <div className="grid grid-cols-2 gap-1 text-[11px] font-bold text-center">
                <div className="p-1 rounded bg-emerald-950 text-emerald-300 border border-emerald-700/60">
                  FL 101°
                </div>
                <div className="p-1 rounded bg-emerald-950 text-emerald-300 border border-emerald-700/60">
                  FR 104°
                </div>
                <div className="p-1 rounded bg-emerald-950 text-emerald-300 border border-emerald-700/60">
                  RL 99°
                </div>
                <div className="p-1 rounded bg-emerald-950 text-emerald-300 border border-emerald-700/60">
                  RR 105°
                </div>
              </div>
            </div>
          </div>

          {/* Center Column: Massive Gear Indicator & Delta Bar */}
          <div className="md:col-span-4 flex flex-col items-center justify-between gap-2 text-center py-2">
            <span className="text-[10px] text-slate-400 uppercase font-bold tracking-widest">GEAR</span>
            <div className="w-28 h-32 rounded-2xl bg-gradient-to-b from-slate-900 to-black border-2 border-apex-cyan/50 flex items-center justify-center shadow-lg shadow-cyan-500/20">
              <span className="text-7xl font-black text-apex-cyan">{gear}</span>
            </div>

            {/* Delta-to-Reference Time Bar */}
            <div className="w-full flex flex-col items-center gap-1 mt-2">
              <span className="text-[10px] text-slate-400 uppercase">LAP DELTA (Δ)</span>
              <div className="px-3 py-1 rounded-lg bg-slate-900 border border-slate-800 text-lg font-black tracking-wider">
                <span className={deltaColor}>{deltaS <= 0 ? `${deltaS.toFixed(3)}s` : `+${deltaS.toFixed(3)}s`}</span>
              </div>
            </div>
          </div>

          {/* Right Column: RPM, ERS, Brake Bias */}
          <div className="md:col-span-4 flex flex-col justify-between gap-3 border-l border-slate-800/80 pl-4">
            <div className="flex flex-col text-right">
              <span className="text-[10px] text-slate-400 uppercase font-bold tracking-widest">ENGINE RPM</span>
              <span className="text-4xl font-black text-amber-400">{rpm}</span>
            </div>

            {/* ERS SoC & Mode */}
            <div className="flex flex-col gap-1 bg-slate-900/60 p-2.5 rounded-lg border border-slate-800">
              <div className="flex justify-between text-[11px]">
                <span className="text-slate-400">ERS BATTERY:</span>
                <span className="font-bold text-pink-400">
                  {Math.round(player?.ers_battery_soc_pct ?? 84)}%
                </span>
              </div>
              <div className="w-full bg-slate-950 rounded-full h-2 overflow-hidden">
                <div
                  className="h-full bg-pink-500"
                  style={{ width: `${player?.ers_battery_soc_pct ?? 84}%` }}
                />
              </div>
              <div className="flex justify-between text-[10px] text-slate-400 mt-1">
                <span>MODE:</span>
                <span className="font-bold text-white uppercase">{ersMode}</span>
              </div>
            </div>

            {/* Brake Bias & DRS */}
            <div className="flex justify-between items-center text-xs">
              <div className="flex flex-col">
                <span className="text-[9px] text-slate-400 uppercase">BRAKE BIAS</span>
                <span className="font-bold text-white text-sm">{brakeBiasPct.toFixed(1)}%</span>
              </div>
              <div className="flex flex-col text-right">
                <span className="text-[9px] text-slate-400 uppercase">DRS</span>
                <span className="font-bold text-emerald-400 text-sm">AVAILABLE</span>
              </div>
            </div>
          </div>
        </div>

        {/* Physical Rotary Dial Controls */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs font-mono">
          <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 flex flex-col gap-1">
            <span className="text-[10px] text-slate-400">ROTARY: BRAKE BIAS</span>
            <div className="flex items-center justify-between">
              <button
                onClick={() => setBrakeBiasPct((prev) => Math.max(52.0, Number((prev - 0.5).toFixed(1))))}
                className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-white font-bold"
              >
                -
              </button>
              <span className="font-bold text-white">{brakeBiasPct}%</span>
              <button
                onClick={() => setBrakeBiasPct((prev) => Math.min(62.0, Number((prev + 0.5).toFixed(1))))}
                className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-white font-bold"
              >
                +
              </button>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 flex flex-col gap-1">
            <span className="text-[10px] text-slate-400">ROTARY: DIFF ENTRY</span>
            <div className="flex items-center justify-between">
              <button
                onClick={() => setDiffEntry((prev) => Math.max(50, prev - 5))}
                className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-white font-bold"
              >
                -
              </button>
              <span className="font-bold text-white">{diffEntry}%</span>
              <button
                onClick={() => setDiffEntry((prev) => Math.min(90, prev + 5))}
                className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-white font-bold"
              >
                +
              </button>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 flex flex-col gap-1">
            <span className="text-[10px] text-slate-400">ERS DEPLOY MODE</span>
            <select
              value={ersMode}
              onChange={(e) => setErsMode(e.target.value as any)}
              className="bg-slate-900 border border-slate-700 rounded px-2 py-1 text-white font-bold text-xs"
            >
              <option value="BALANCED">BALANCED</option>
              <option value="OVERTAKE">OVERTAKE</option>
              <option value="HOTLAP">HOTLAP</option>
              <option value="HARVEST">HARVEST</option>
            </select>
          </div>

          <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 flex flex-col justify-center text-center">
            <span className="text-[10px] text-slate-400 uppercase">FIA STATUS</span>
            <span className="text-xs font-bold text-emerald-400">GREEN FLAG (TRACK CLEAR)</span>
          </div>
        </div>
      </div>
    </div>
  );
};
