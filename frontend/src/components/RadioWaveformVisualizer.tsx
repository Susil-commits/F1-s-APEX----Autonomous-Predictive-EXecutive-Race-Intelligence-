import React from 'react';
import { useRaceStore } from '../store/raceStore';
import { Radio, Mic, Activity, Volume2 } from 'lucide-react';

export const RadioWaveformVisualizer: React.FC = () => {
  const { voiceRadioEnabled, audioMuted } = useRaceStore();

  return (
    <div className="flex items-center gap-3 px-3 py-1.5 rounded-xl bg-slate-950/80 border border-slate-800 font-mono text-xs">
      <div className="flex items-center gap-1.5 text-cyan-400 font-bold text-[10px] shrink-0">
        <Radio className="w-3.5 h-3.5 animate-pulse text-cyan-400" />
        <span className="hidden sm:inline">142.850 MHz [PIT-WALL]</span>
      </div>

      {/* Animated Frequency Bars */}
      <div className="flex items-center gap-0.5 h-4 px-1">
        {[4, 10, 16, 8, 14, 20, 12, 6, 18, 14, 8, 16, 22, 10, 6, 12].map((h, idx) => (
          <div
            key={idx}
            style={{
              height: `${voiceRadioEnabled && !audioMuted ? h : 3}px`,
              animationDelay: `${idx * 0.08}s`,
            }}
            className={`w-0.5 rounded-full transition-all duration-300 ${
              voiceRadioEnabled && !audioMuted
                ? 'bg-gradient-to-t from-cyan-500 to-purple-400'
                : 'bg-slate-700'
            }`}
          />
        ))}
      </div>

      <div className="flex items-center gap-1 text-[9px] text-slate-500 font-sans hidden md:flex">
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping" />
        <span>RX ACTIVE</span>
      </div>
    </div>
  );
};
