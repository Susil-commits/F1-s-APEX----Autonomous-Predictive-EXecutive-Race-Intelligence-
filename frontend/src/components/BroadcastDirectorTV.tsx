import React, { useState, useEffect } from 'react';
import { useRaceStore } from '../store/raceStore';
import { Tv, Video, Zap, Activity, Eye, Play, Sparkles, Volume2, ShieldAlert } from 'lucide-react';

export const BroadcastDirectorTV: React.FC = () => {
  const { raceState } = useRaceStore();
  const [selectedCam, setSelectedCam] = useState<'AUTO' | 'HELICOPTER' | 'ONBOARD' | 'APEX_CURB' | 'PIT_EXIT'>('AUTO');
  const [activeDirectorCut, setActiveDirectorCut] = useState<string>('CAM 1: HELICOPTER GYRO CAM');

  const player = raceState?.cars.find((c) => c.is_player) || raceState?.cars[0];
  const leader = raceState?.cars[0];
  const p2 = raceState?.cars[1];

  // Auto-Director AI logic
  useEffect(() => {
    if (selectedCam !== 'AUTO') {
      setActiveDirectorCut(`CAM: ${selectedCam}`);
      return;
    }

    const interval = setInterval(() => {
      // Pick dynamic camera based on current race scenario
      const gap = p2 ? p2.gap_to_leader_s : 1.5;
      if (gap < 0.8) {
        setActiveDirectorCut('CAM 3: ONBOARD CHASE BATTLE (GAP < 0.8s)');
      } else if (raceState?.safety_car !== 'NONE') {
        setActiveDirectorCut('CAM 1: HELICOPTER OVERVIEW (SAFETY CAR REGIME)');
      } else {
        const cuts = [
          'CAM 1: HELICOPTER HIGH-WIRE GYRO',
          'CAM 2: TURN 1 HIGH-SPEED APEX',
          'CAM 3: LEADER ONBOARD NOSE-CAM',
          'CAM 4: PIT LANE REJOIN RADAR',
        ];
        const nextCut = cuts[Math.floor(Math.random() * cuts.length)];
        setActiveDirectorCut(nextCut);
      }
    }, 4000);

    return () => clearInterval(interval);
  }, [selectedCam, raceState?.current_lap, p2?.gap_to_leader_s]);

  const overtakeProbability = player ? Math.min(95, Math.max(15, Math.round(100 - (player.gap_to_car_ahead_s * 45)))) : 76;

  return (
    <div className="w-full rounded-2xl bg-slate-950 border border-slate-800 p-4 flex flex-col gap-4 shadow-2xl">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Tv className="w-5 h-5 text-rose-400 animate-pulse" />
          <div className="flex flex-col">
            <span className="font-bold text-white text-sm">AI BROADCAST TV DIRECTOR & CINEMATIC GRAPHICS</span>
            <span className="text-[11px] font-mono text-slate-400">
              Autonomous multi-camera action switching with live AWS-style TV overlay graphics
            </span>
          </div>
        </div>

        {/* Camera Selector */}
        <div className="flex items-center bg-slate-900 p-1 rounded-xl border border-slate-800 text-xs font-mono">
          <span className="text-slate-400 pl-2 pr-1">Director:</span>
          {(['AUTO', 'HELICOPTER', 'ONBOARD', 'APEX_CURB', 'PIT_EXIT'] as const).map((cam) => (
            <button
              key={cam}
              onClick={() => setSelectedCam(cam)}
              className={`px-2.5 py-1 rounded-lg transition-all ${
                selectedCam === cam
                  ? 'bg-rose-600 text-white font-bold shadow-sm shadow-rose-600/30'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              {cam}
            </button>
          ))}
        </div>
      </div>

      {/* Main Broadcast Screen with TV Overlays */}
      <div className="relative w-full h-[460px] rounded-xl overflow-hidden bg-slate-900 border border-slate-800 flex items-center justify-center">
        {/* Background Visualizer Simulation */}
        <div className="absolute inset-0 bg-gradient-to-t from-black via-slate-950/80 to-transparent flex items-center justify-center">
          <div className="text-center flex flex-col items-center gap-2 text-slate-500">
            <Video className="w-12 h-12 text-slate-600 animate-pulse" />
            <span className="font-mono text-xs uppercase tracking-widest text-slate-400 font-bold">
              {activeDirectorCut}
            </span>
            <span className="text-[11px] font-mono text-slate-500">
              4K HDR 60FPS LOW-LATENCY WEBRTC BROADCAST STREAM
            </span>
          </div>
        </div>

        {/* Top-Left Live TV Bug */}
        <div className="absolute top-4 left-4 flex items-center gap-2 bg-black/80 backdrop-blur-md px-3 py-1.5 rounded-lg border border-slate-700">
          <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping" />
          <span className="font-black text-white text-xs tracking-wider">LIVE</span>
          <span className="text-slate-500">|</span>
          <span className="font-mono text-xs text-slate-300">
            LAP {raceState?.current_lap || 1} / {raceState?.total_laps || 52}
          </span>
        </div>

        {/* Top-Right Speed Trap Radar Bug */}
        <div className="absolute top-4 right-4 bg-black/80 backdrop-blur-md px-3 py-1.5 rounded-lg border border-slate-700 font-mono text-xs text-right">
          <span className="text-[10px] text-slate-400 uppercase block">SPEED TRAP</span>
          <span className="font-bold text-apex-cyan text-sm">{player ? player.speed_kmh : 328} KM/H</span>
        </div>

        {/* Bottom Broadcast Graphics Overlay (AWS-Style Insights) */}
        <div className="absolute bottom-4 left-4 right-4 flex flex-col gap-2">
          {/* AWS Insight: Overtake Probability */}
          <div className="bg-black/85 backdrop-blur-lg p-3 rounded-xl border border-slate-700 flex flex-wrap items-center justify-between gap-3 shadow-2xl">
            <div className="flex items-center gap-3">
              <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-amber-400 to-rose-500 flex items-center justify-center font-bold text-black text-xs">
                ⚡
              </div>
              <div className="flex flex-col">
                <span className="text-[10px] font-mono text-slate-400 uppercase font-bold tracking-wider">
                  AWS RACE INSIGHT • OVERTAKE PROBABILITY
                </span>
                <span className="font-bold text-white text-xs font-mono">
                  {player?.driver_name} attempting move into Turn 4 Chicane
                </span>
              </div>
            </div>

            {/* Probability Progress Bar */}
            <div className="flex items-center gap-3 min-w-[200px]">
              <div className="flex-1 bg-slate-800 rounded-full h-2 overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-amber-400 via-rose-500 to-pink-500 transition-all duration-500"
                  style={{ width: `${overtakeProbability}%` }}
                />
              </div>
              <span className="font-mono font-bold text-sm text-pink-400">
                {overtakeProbability}%
              </span>
            </div>
          </div>

          {/* Pit Rejoin Predictor Graphic */}
          <div className="bg-slate-950/90 backdrop-blur-md px-3 py-2 rounded-lg border border-slate-800 flex items-center justify-between text-xs font-mono text-slate-300">
            <div className="flex items-center gap-2">
              <Sparkles className="w-3.5 h-3.5 text-apex-cyan" />
              <span>
                Pit Window Forecast: Box Lap {raceState?.current_lap ? raceState.current_lap + 2 : 18} → Rejoin in <strong>P3</strong> (Clear Air)
              </span>
            </div>
            <span className="text-[11px] text-emerald-400 font-bold">+2.4s Undercut Advantage</span>
          </div>
        </div>
      </div>
    </div>
  );
};
