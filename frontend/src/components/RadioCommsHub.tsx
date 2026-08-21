import React, { useState, useEffect } from 'react';
import { useRaceStore } from '../store/raceStore';
import { neuralPitRadio, RadioTransmission } from '../utils/neuralRadioSynth';
import { RadioWaveformVisualizer } from './RadioWaveformVisualizer';
import {
  Radio,
  Volume2,
  VolumeX,
  Send,
  Sparkles,
  AlertTriangle,
  Flame,
  CloudRain,
  ShieldAlert,
  Zap,
} from 'lucide-react';

export const RadioCommsHub: React.FC = () => {
  const { raceState } = useRaceStore();
  const [transmissions, setTransmissions] = useState<RadioTransmission[]>([]);
  const [customMsg, setCustomMsg] = useState<string>('');
  const [selectedSpeaker, setSelectedSpeaker] = useState<string>('Race Engineer');
  const [isMuted, setIsMuted] = useState<boolean>(false);

  useEffect(() => {
    const unsubscribe = neuralPitRadio.subscribe((list) => {
      setTransmissions(list);
    });
    return () => unsubscribe();
  }, []);

  const handleBroadcast = (
    msg: string,
    speaker: string = 'Race Engineer',
    priority: 'ROUTINE' | 'TACTICAL' | 'URGENT' | 'SAFETY_CAR' = 'TACTICAL'
  ) => {
    if (!msg.trim()) return;
    neuralPitRadio.broadcastTransmission(
      msg,
      speaker,
      priority,
      raceState?.current_lap || 1
    );
  };

  const handleCustomSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!customMsg.trim()) return;
    handleBroadcast(customMsg, selectedSpeaker, 'TACTICAL');
    setCustomMsg('');
  };

  const toggleMute = () => {
    const muted = neuralPitRadio.toggleMute();
    setIsMuted(muted);
  };

  return (
    <div className="w-full rounded-2xl bg-slate-950 border border-slate-800 p-4 flex flex-col gap-4 shadow-2xl">
      {/* Header & Controls */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Radio className="w-5 h-5 text-rose-500 animate-pulse" />
          <div className="flex flex-col">
            <span className="font-bold text-white text-sm">NEURAL PIT WALL VOICE RADIO COMMS</span>
            <span className="text-[11px] font-mono text-slate-400">
              Web Audio DSP transceiver & speech synthesis radio channel
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <RadioWaveformVisualizer />
          <button
            onClick={toggleMute}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-mono font-bold transition-all active:scale-95 ${
              isMuted
                ? 'bg-slate-900 text-slate-500 border-slate-800'
                : 'bg-rose-500/20 text-rose-300 border-rose-500/40 shadow-sm shadow-rose-500/20'
            }`}
          >
            {isMuted ? <VolumeX className="w-3.5 h-3.5" /> : <Volume2 className="w-3.5 h-3.5 text-rose-400" />}
            <span>{isMuted ? 'RADIO MUTED' : 'RADIO LIVE'}</span>
          </button>
        </div>
      </div>

      {/* Quick Tactical Preset Transceiver Buttons */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs font-mono">
        <button
          onClick={() =>
            handleBroadcast(
              'Box box, box box, confirm hard compound this lap.',
              'Race Engineer',
              'URGENT'
            )
          }
          className="flex items-center gap-2 p-2.5 rounded-xl bg-amber-950/50 hover:bg-amber-900/70 border border-amber-600/50 text-amber-300 text-left transition-all active:scale-95"
        >
          <Flame className="w-4 h-4 text-amber-400 shrink-0" />
          <div className="flex flex-col">
            <span className="font-bold">BOX THIS LAP</span>
            <span className="text-[10px] text-amber-400/80">Trigger pit sequence</span>
          </div>
        </button>

        <button
          onClick={() =>
            handleBroadcast(
              'Safety Car deployed, maintain positive delta, watch tyre temperatures.',
              'Pit Wall Chief',
              'SAFETY_CAR'
            )
          }
          className="flex items-center gap-2 p-2.5 rounded-xl bg-amber-950/60 hover:bg-amber-900/80 border border-yellow-500/60 text-yellow-300 text-left transition-all active:scale-95"
        >
          <ShieldAlert className="w-4 h-4 text-yellow-400 shrink-0" />
          <div className="flex flex-col">
            <span className="font-bold">SAFETY CAR CALL</span>
            <span className="text-[10px] text-yellow-400/80">Delta management</span>
          </div>
        </button>

        <button
          onClick={() =>
            handleBroadcast(
              'Mode Push available, gap ahead is 0.7 seconds, deploy ERS overtake.',
              'Race Engineer',
              'TACTICAL'
            )
          }
          className="flex items-center gap-2 p-2.5 rounded-xl bg-purple-950/50 hover:bg-purple-900/70 border border-purple-600/50 text-purple-300 text-left transition-all active:scale-95"
        >
          <Zap className="w-4 h-4 text-purple-400 shrink-0" />
          <div className="flex flex-col">
            <span className="font-bold">OVERTAKE / ERS</span>
            <span className="text-[10px] text-purple-400/80">Full deployment</span>
          </div>
        </button>

        <button
          onClick={() =>
            handleBroadcast(
              'Rain intensifying in Sector 2, crossover window opening in two laps.',
              'Tyre Specialist',
              'TACTICAL'
            )
          }
          className="flex items-center gap-2 p-2.5 rounded-xl bg-cyan-950/50 hover:bg-cyan-900/70 border border-cyan-600/50 text-cyan-300 text-left transition-all active:scale-95"
        >
          <CloudRain className="w-4 h-4 text-cyan-400 shrink-0" />
          <div className="flex flex-col">
            <span className="font-bold">WEATHER ALERT</span>
            <span className="text-[10px] text-cyan-400/80">Rain crossover alert</span>
          </div>
        </button>
      </div>

      {/* Live Radio Transmissions Log */}
      <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800/80 max-h-[320px] overflow-y-auto flex flex-col gap-2">
        <span className="text-xs font-mono text-slate-400 font-bold uppercase mb-1">
          RADIO TRANSCRIPT FEED
        </span>

        {transmissions.length > 0 ? (
          transmissions.map((t) => (
            <div
              key={t.id}
              className={`p-3 rounded-xl border flex flex-col gap-1 text-xs font-mono transition-all ${
                t.priority === 'SAFETY_CAR'
                  ? 'bg-amber-950/40 border-amber-600/60 text-amber-200'
                  : t.priority === 'URGENT'
                  ? 'bg-rose-950/40 border-rose-600/60 text-rose-200'
                  : 'bg-slate-900/90 border-slate-800 text-slate-300'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-white uppercase">{t.speaker}</span>
                  <span className="px-1.5 py-0.2 rounded text-[10px] bg-slate-800 text-slate-400">
                    LAP {t.lap}
                  </span>
                </div>
                <span className="text-[10px] text-slate-500">{t.timestamp}</span>
              </div>
              <p className="text-slate-200 mt-0.5 text-[13px]">{t.message}</p>
            </div>
          ))
        ) : (
          <div className="text-center py-8 text-slate-500 font-mono text-xs">
            Radio channel quiet. Transmissions will be broadcast automatically during key events.
          </div>
        )}
      </div>

      {/* Custom Transmit Bar */}
      <form onSubmit={handleCustomSubmit} className="flex gap-2 text-xs font-mono">
        <select
          value={selectedSpeaker}
          onChange={(e) => setSelectedSpeaker(e.target.value)}
          className="bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-rose-500"
        >
          <option value="Race Engineer">Race Engineer</option>
          <option value="Pit Wall Chief">Pit Wall Chief</option>
          <option value="Driver (APEX AI)">Driver (APEX AI)</option>
          <option value="Tyre Specialist">Tyre Specialist</option>
        </select>

        <input
          type="text"
          value={customMsg}
          onChange={(e) => setCustomMsg(e.target.value)}
          placeholder="Transmit custom radio instruction to driver..."
          className="flex-1 bg-slate-900 border border-slate-700 rounded-xl px-4 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-rose-500"
        />

        <button
          type="submit"
          disabled={!customMsg.trim()}
          className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 disabled:opacity-50 text-white font-bold transition-all active:scale-95 shadow-sm shadow-rose-600/30"
        >
          <Send className="w-3.5 h-3.5" />
          <span>TRANSMIT</span>
        </button>
      </form>
    </div>
  );
};
