import React, { useState, useRef } from 'react';
import { useRaceStore } from '../store/raceStore';
import { Timer, Zap, Trophy, AlertTriangle, RotateCcw, Play, CheckCircle } from 'lucide-react';
import { audioEngine } from '../utils/audioEngine';

export const PitStopReactionSim: React.FC = () => {
  const [gameState, setGameState] = useState<'idle' | 'waiting' | 'ready' | 'finished'>('idle');
  const [reactionTimeMs, setReactionTimeMs] = useState<number | null>(null);
  const [lightCount, setLightCount] = useState<number>(0);
  const startTimeRef = useRef<number>(0);
  const timeoutRef = useRef<number | null>(null);

  const startPitSequence = () => {
    setGameState('waiting');
    setReactionTimeMs(null);
    setLightCount(0);

    // Sequence 5 red lights over 2 seconds
    let count = 0;
    const interval = window.setInterval(() => {
      count += 1;
      setLightCount(count);
      audioEngine.playRadioBleep();

      if (count === 5) {
        clearInterval(interval);
        // Random green delay between 1.0s and 2.5s
        const greenDelay = 1000 + Math.random() * 1500;
        timeoutRef.current = window.setTimeout(() => {
          setGameState('ready');
          setLightCount(0);
          startTimeRef.current = Date.now();
        }, greenDelay);
      }
    }, 400);
  };

  const handleRelease = () => {
    if (gameState === 'waiting') {
      // Jump start!
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      setGameState('finished');
      setReactionTimeMs(-1); // False start
      return;
    }

    if (gameState === 'ready') {
      const elapsed = Date.now() - startTimeRef.current;
      const totalPitTime = 1800 + elapsed; // Base 1.8s mechanical change + reaction time
      setReactionTimeMs(totalPitTime);
      setGameState('finished');
      audioEngine.playWheelGunSound();
    }
  };

  const getGrade = (ms: number) => {
    if (ms === -1) return { grade: 'FALSE START', color: 'text-rose-400', desc: '5-second time penalty!' };
    const seconds = ms / 1000;
    if (seconds < 2.2) return { grade: 'WORLD RECORD STOP!', color: 'text-cyan-400 glow-cyan', desc: 'Red Bull speed perfection! (-0.6s advantage)' };
    if (seconds < 2.7) return { grade: 'EXCELLENT STOP', color: 'text-emerald-400', desc: 'Clean wheel swap and green light release.' };
    if (seconds < 3.4) return { grade: 'MEDIOCRE STOP', color: 'text-amber-400', desc: 'Slight wheel nut hesitation (+0.5s loss).' };
    return { grade: 'SLOW PIT STOP', color: 'text-rose-400', desc: 'Cross-threaded wheel nut delay (+1.8s loss).' };
  };

  return (
    <div className="glass-panel rounded-xl p-5 flex flex-col border border-apex-border shadow-2xl font-mono text-xs">
      {/* Header */}
      <div className="flex items-center justify-between mb-3 border-b border-slate-800 pb-2">
        <div className="flex items-center gap-2">
          <Timer className="w-4 h-4 text-apex-cyan animate-pulse" />
          <h3 className="text-xs font-black uppercase tracking-widest text-slate-200">
            Interactive Pit Crew Reaction Stopwatch
          </h3>
        </div>
        <span className="text-[10px] text-cyan-300 bg-cyan-950/40 px-2 py-0.5 rounded border border-cyan-800/50 font-bold">
          Pit Box Release Test
        </span>
      </div>

      {/* Light Board (5 F1 Gantry Lights) */}
      <div className="flex items-center justify-center gap-3 p-4 rounded-xl bg-slate-950/90 border border-slate-800 mb-4">
        {[1, 2, 3, 4, 5].map((idx) => {
          const isRed = gameState === 'waiting' && idx <= lightCount;
          const isGreen = gameState === 'ready';

          return (
            <div
              key={idx}
              className={`w-7 h-7 rounded-full border-2 transition-all flex items-center justify-center ${
                isGreen
                  ? 'bg-emerald-500 border-emerald-300 shadow-lg shadow-emerald-500/80 animate-ping'
                  : isRed
                  ? 'bg-rose-600 border-rose-400 shadow-lg shadow-rose-600/80'
                  : 'bg-slate-900 border-slate-700'
              }`}
            />
          );
        })}
      </div>

      {/* Main Trigger Action Button */}
      {gameState === 'idle' || gameState === 'finished' ? (
        <button
          onClick={startPitSequence}
          className="w-full py-3 px-4 rounded-xl font-black text-xs uppercase tracking-wider flex items-center justify-center gap-2 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-black shadow-lg shadow-cyan-500/25 transition-all active:scale-95 mb-2"
        >
          <Play className="w-4 h-4 fill-current" />
          <span>Start Pit Stop Reaction Drill</span>
        </button>
      ) : (
        <button
          onClick={handleRelease}
          className={`w-full py-4 px-4 rounded-xl font-black text-sm uppercase tracking-wider flex items-center justify-center gap-2 transition-all active:scale-95 shadow-2xl mb-2 ${
            gameState === 'ready'
              ? 'bg-emerald-500 hover:bg-emerald-400 text-black shadow-emerald-500/50 animate-bounce'
              : 'bg-rose-950/80 text-rose-300 border border-rose-700/60 hover:bg-rose-900'
          }`}
        >
          <Zap className="w-5 h-5 fill-current" />
          <span>{gameState === 'ready' ? 'RELEASE CAR NOW (GO!)' : 'HOLD... (WAIT FOR GREEN)'}</span>
        </button>
      )}

      {/* Results Box */}
      {gameState === 'finished' && reactionTimeMs !== null && (
        <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 text-center animate-fadeIn">
          {reactionTimeMs === -1 ? (
            <div className="text-rose-400 font-bold">
              <span className="text-base block">FALSE START / JUMPED LIGHTS</span>
              <span className="text-[11px] text-slate-400">Triggered release before green gantry light.</span>
            </div>
          ) : (
            <div>
              <span className="text-[10px] text-slate-500 uppercase block font-sans">Stationary Pit Duration</span>
              <span className="text-2xl font-black text-white font-mono my-0.5 block">
                {(reactionTimeMs / 1000).toFixed(3)}s
              </span>
              <span className={`text-xs font-black uppercase block ${getGrade(reactionTimeMs).color}`}>
                {getGrade(reactionTimeMs).grade}
              </span>
              <p className="text-[11px] text-slate-400 font-sans mt-1">
                {getGrade(reactionTimeMs).desc}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
