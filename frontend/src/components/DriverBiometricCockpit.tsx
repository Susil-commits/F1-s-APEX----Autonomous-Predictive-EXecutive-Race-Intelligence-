import React, { useState, useEffect, useRef } from 'react';
import { useRaceStore } from '../store/raceStore';
import { Heart, Activity, Brain, Droplets, Thermometer, Zap, AlertTriangle, ShieldCheck } from 'lucide-react';

export const DriverBiometricCockpit: React.FC = () => {
  const { raceState } = useRaceStore();
  const player = raceState?.cars.find((c) => c.is_player) || raceState?.cars[0];

  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  // Biometric States
  const [heartRateBpm, setHeartRateBpm] = useState<number>(168);
  const [cognitiveLoadPct, setCognitiveLoadPct] = useState<number>(78);
  const [reactionTimeMs, setReactionTimeMs] = useState<number>(195);
  const [bodyTempC, setBodyTempC] = useState<number>(38.1);
  const [hydrationLitersLost, setHydrationLitersLost] = useState<number>(1.4);

  const isPushing = player?.driving_mode === 'PUSH';
  const isDefending = player?.gap_to_car_behind_s != null && player.gap_to_car_behind_s < 1.0;

  // Dynamic Heart Rate calculation based on race intensity
  useEffect(() => {
    let targetHr = 158;
    if (isPushing) targetHr += 18;
    if (isDefending) targetHr += 12;

    const interval = setInterval(() => {
      setHeartRateBpm((prev) => {
        const jitter = (Math.random() - 0.5) * 4;
        return Math.round(targetHr + jitter);
      });

      setCognitiveLoadPct(Math.min(98, Math.round((isPushing ? 86 : 72) + Math.random() * 6)));
      setReactionTimeMs(Math.round((isPushing ? 180 : 210) + Math.random() * 15));
    }, 1000);

    return () => clearInterval(interval);
  }, [isPushing, isDefending]);

  // Animated ECG Heartbeat Canvas Loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animId: number;
    let offset = 0;
    const width = canvas.width;
    const height = canvas.height;

    const renderEcg = () => {
      offset += 2;
      ctx.fillStyle = '#060911';
      ctx.fillRect(0, 0, width, height);

      // Grid Lines
      ctx.strokeStyle = '#1e293b';
      ctx.lineWidth = 1;
      for (let x = 0; x < width; x += 30) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
        ctx.stroke();
      }
      for (let y = 0; y < height; y += 20) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
      }

      // ECG Waveform
      ctx.strokeStyle = heartRateBpm > 175 ? '#f43f5e' : '#22c55e';
      ctx.lineWidth = 2.5;
      ctx.beginPath();

      const midY = height / 2;

      for (let x = 0; x < width; x++) {
        const t = (x + offset) % 180;
        let y = midY;

        // P wave
        if (t > 30 && t < 45) {
          y -= Math.sin(((t - 30) / 15) * Math.PI) * 8;
        }
        // QRS complex
        else if (t >= 55 && t < 60) {
          y += 6; // Q
        } else if (t >= 60 && t < 68) {
          y -= 45; // R spike
        } else if (t >= 68 && t < 74) {
          y += 18; // S dip
        }
        // T wave
        else if (t > 90 && t < 120) {
          y -= Math.sin(((t - 90) / 30) * Math.PI) * 14;
        }

        if (x === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }

      ctx.stroke();
      animId = requestAnimationFrame(renderEcg);
    };

    renderEcg();

    return () => cancelAnimationFrame(animId);
  }, [heartRateBpm]);

  const errorRiskPct = Math.min(85, Math.round((cognitiveLoadPct * 0.4) + ((heartRateBpm - 140) * 0.6)));

  return (
    <div className="w-full rounded-2xl bg-slate-950 border border-slate-800 p-4 flex flex-col gap-4 shadow-2xl">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Heart className="w-5 h-5 text-rose-500 animate-pulse" />
          <div className="flex flex-col">
            <span className="font-bold text-white text-sm">
              DRIVER BIOMETRIC & COGNITIVE STRESS TELEMETRY COCKPIT
            </span>
            <span className="text-[11px] font-mono text-slate-400">
              Live biometric glove ECG, cognitive workload index, reaction latency & error probability
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono">
          <span className="text-slate-400">Driver:</span>
          <span className="font-bold text-white px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800">
            {player?.driver_name || 'Driver #1'}
          </span>
        </div>
      </div>

      {/* Primary Biometric KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {/* Heart Rate */}
        <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] font-mono text-slate-400 uppercase flex items-center gap-1">
            <Heart className="w-3 h-3 text-rose-500" /> HEART RATE
          </span>
          <div className="flex items-baseline gap-1">
            <span className={`text-3xl font-black font-mono ${heartRateBpm > 175 ? 'text-rose-400 animate-pulse' : 'text-emerald-400'}`}>
              {heartRateBpm}
            </span>
            <span className="text-xs font-mono text-slate-400">BPM</span>
          </div>
          <span className="text-[10px] font-mono text-slate-400">
            {heartRateBpm > 175 ? 'High cardiac stress' : 'Optimal threshold'}
          </span>
        </div>

        {/* Cognitive Workload */}
        <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] font-mono text-slate-400 uppercase flex items-center gap-1">
            <Brain className="w-3 h-3 text-purple-400" /> COGNITIVE LOAD
          </span>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-black font-mono text-purple-400">
              {cognitiveLoadPct}%
            </span>
          </div>
          <span className="text-[10px] font-mono text-slate-400">Traffic & tactical focus</span>
        </div>

        {/* Reaction Latency */}
        <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] font-mono text-slate-400 uppercase flex items-center gap-1">
            <Zap className="w-3 h-3 text-apex-cyan" /> REACTION LATENCY
          </span>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-black font-mono text-apex-cyan">
              {reactionTimeMs}
            </span>
            <span className="text-xs font-mono text-slate-400">MS</span>
          </div>
          <span className="text-[10px] font-mono text-slate-400">Brake trigger latency</span>
        </div>

        {/* Core Body Temperature */}
        <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] font-mono text-slate-400 uppercase flex items-center gap-1">
            <Thermometer className="w-3 h-3 text-amber-400" /> CORE TEMP
          </span>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-black font-mono text-amber-400">
              {bodyTempC.toFixed(1)}
            </span>
            <span className="text-xs font-mono text-slate-400">°C</span>
          </div>
          <span className="text-[10px] font-mono text-slate-400">Cockpit thermal load</span>
        </div>

        {/* Mistake Probability */}
        <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] font-mono text-slate-400 uppercase flex items-center gap-1">
            <AlertTriangle className="w-3 h-3 text-rose-400" /> ERROR RISK
          </span>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-black font-mono text-rose-400">
              {errorRiskPct}%
            </span>
          </div>
          <span className="text-[10px] font-mono text-slate-400">Lockup / wide apex risk</span>
        </div>
      </div>

      {/* Live ECG Waveform Monitor & Stress Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Animated ECG Monitor */}
        <div className="lg:col-span-8 p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col gap-2">
          <div className="flex justify-between items-center">
            <span className="text-xs font-mono text-slate-300 font-bold uppercase flex items-center gap-2">
              <Activity className="w-4 h-4 text-emerald-400" />
              LIVE BIOMETRIC GLOVE ECG TRACE (CHEST HARNESS & OPTICAL PULSE)
            </span>
            <span className="text-[11px] font-mono text-emerald-400 font-bold">250 HZ SYNC</span>
          </div>

          <div className="w-full h-44 rounded-lg overflow-hidden border border-slate-800 bg-[#060911]">
            <canvas ref={canvasRef} width={800} height={176} className="w-full h-full" />
          </div>
        </div>

        {/* Fatigue & Hydration Sidebar */}
        <div className="lg:col-span-4 p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col justify-between gap-3 font-mono text-xs">
          <span className="text-xs font-bold text-amber-400 uppercase border-b border-slate-800 pb-2">
            PHYSIOLOGICAL STRESS PROFILE
          </span>

          <div className="flex flex-col gap-1">
            <div className="flex justify-between text-slate-300">
              <span>Hydration Depletion:</span>
              <span className="font-bold text-apex-cyan">{hydrationLitersLost.toFixed(1)} Liters</span>
            </div>
            <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
              <div className="h-full bg-cyan-400" style={{ width: `${(hydrationLitersLost / 3.0) * 100}%` }} />
            </div>
          </div>

          <div className="flex flex-col gap-1">
            <div className="flex justify-between text-slate-300">
              <span>Cumulative G-Force Stress:</span>
              <span className="font-bold text-purple-400">4.8G Lateral Peak</span>
            </div>
            <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
              <div className="h-full bg-purple-500" style={{ width: '75%' }} />
            </div>
          </div>

          <div className="p-2.5 rounded-lg bg-slate-950/80 border border-slate-800 text-[11px] text-slate-400">
            <strong>Medical Note:</strong> Driver physiological parameters within FIA superlicense safety limits. Recommend in-helmet hydration intake.
          </div>
        </div>
      </div>
    </div>
  );
};
