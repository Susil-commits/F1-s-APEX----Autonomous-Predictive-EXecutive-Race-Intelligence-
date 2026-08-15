import React, { useState } from 'react';
import { useRaceStore } from '../store/raceStore';
import { History, Play, Pause, RotateCcw, FastForward, Rewind, Clock, Radio } from 'lucide-react';

interface RaceTimeTravelDVRProps {
  onSelectHistoricalLap?: (lap: number) => void;
}

export const RaceTimeTravelDVR: React.FC<RaceTimeTravelDVRProps> = () => {
  const { raceState, telemetryHistory } = useRaceStore();
  const [selectedLap, setSelectedLap] = useState<number | null>(null);
  const [isReplaying, setIsReplaying] = useState<boolean>(false);

  if (!raceState || telemetryHistory.length === 0) return null;

  const currentLap = raceState.current_lap;
  const minLap = telemetryHistory[0].lap;
  const maxLap = currentLap;
  const activeLap = selectedLap ?? currentLap;
  const isLive = activeLap === currentLap;

  const historicalPoint =
    telemetryHistory.find((p) => p.lap === activeLap) ||
    telemetryHistory[telemetryHistory.length - 1];

  const handleSliderChange = (lap: number) => {
    setSelectedLap(lap);
  };

  const handleJumpToLive = () => {
    setSelectedLap(null);
    setIsReplaying(false);
  };

  return (
    <div className="glass-panel rounded-xl p-3.5 flex flex-col gap-2.5 border border-apex-border shadow-2xl font-mono text-xs">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <History className="w-4 h-4 text-apex-cyan animate-pulse" />
          <h3 className="text-xs font-black uppercase tracking-widest text-slate-200">
            Telemetry DVR & Time-Travel Scrubber
          </h3>
        </div>

        <div className="flex items-center gap-2">
          {isLive ? (
            <span className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-rose-500/20 text-rose-400 border border-rose-500/40 text-[9.5px] font-black uppercase">
              <span className="w-1.5 h-1.5 rounded-full bg-rose-500 animate-ping" />
              LIVE EDGE
            </span>
          ) : (
            <button
              onClick={handleJumpToLive}
              className="flex items-center gap-1 px-2.5 py-0.5 rounded bg-cyan-500 hover:bg-cyan-400 text-black text-[10px] font-black uppercase transition-all shadow-sm shadow-cyan-500/30"
            >
              <span>Return to Live</span>
              <FastForward className="w-3 h-3" />
            </button>
          )}
        </div>
      </div>

      {/* Scrubbing Bar */}
      <div className="flex items-center gap-3 bg-slate-950/80 p-2 rounded-lg border border-slate-800">
        <span className="text-[10px] text-slate-500 font-bold shrink-0">Lap {minLap}</span>

        <input
          type="range"
          min={minLap}
          max={maxLap}
          value={activeLap}
          onChange={(e) => handleSliderChange(Number(e.target.value))}
          className="flex-1 h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-400"
        />

        <span className="text-[10px] font-bold text-apex-cyan shrink-0">
          Lap {activeLap} / {raceState.total_laps}
        </span>
      </div>

      {/* Historical Telemetry Snapshot Card */}
      {!isLive && historicalPoint && (
        <div className="p-2.5 rounded-lg bg-cyan-950/30 border border-cyan-500/40 flex items-center justify-between text-[11px] animate-fadeIn">
          <div>
            <span className="text-[9.5px] text-cyan-400 uppercase font-sans font-bold block">
              Snapshot @ Lap {historicalPoint.lap}
            </span>
            <span className="text-slate-200">
              Pace: <strong className="text-white">{historicalPoint.playerLapTime.toFixed(2)}s</strong> • Gap to P1: +{historicalPoint.gapToLeader.toFixed(2)}s
            </span>
          </div>

          <div className="text-right">
            <span className="text-[9.5px] text-slate-400 font-sans block">Historical Tyre Wear</span>
            <span
              className={`font-black ${
                historicalPoint.playerTyreWear > 75 ? 'text-rose-400' : 'text-amber-400'
              }`}
            >
              {historicalPoint.playerTyreWear}% Wear
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
