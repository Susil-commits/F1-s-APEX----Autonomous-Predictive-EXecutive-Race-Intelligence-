import React, { useState } from 'react';
import { useRaceStore, WorkspaceTab } from '../store/raceStore';
import {
  Activity,
  CloudRain,
  Sun,
  ShieldAlert,
  Flag,
  Wifi,
  Radio,
  Volume2,
  VolumeX,
  Gauge,
  Brain,
  Sliders,
  Cpu,
  UserCheck,
  MapPin,
} from 'lucide-react';
import { CIRCUIT_DATABASE } from '../data/trackGeometries';
import { audioEngine, VoicePersona } from '../utils/audioEngine';

const AVAILABLE_CIRCUITS = [
  { id: 'silverstone', name: 'Silverstone Circuit', flag: '🇬🇧' },
  { id: 'monza', name: 'Autodromo Nazionale Monza', flag: '🇮🇹' },
  { id: 'spa', name: 'Circuit de Spa-Francorchamps', flag: '🇧🇪' },
  { id: 'monaco', name: 'Circuit de Monaco', flag: '🇲🇨' },
  { id: 'interlagos', name: 'Autódromo de Interlagos', flag: '🇧🇷' },
];

export const Header: React.FC = () => {
  const {
    raceState,
    setRaceState,
    connected,
    isLocalTwin,
    isRunning,
    activeTab,
    setActiveTab,
    audioMuted,
    toggleAudioMute,
    voiceRadioEnabled,
    toggleVoiceRadio,
  } = useRaceStore();

  const [activePersona, setActivePersona] = useState<VoicePersona>('apex_core');
  const [isChangingTrack, setIsChangingTrack] = useState<boolean>(false);

  if (!raceState) return null;

  const { track, current_lap, total_laps, race_time_s, weather, safety_car } = raceState;

  // Format race clock
  const minutes = Math.floor(race_time_s / 60);
  const seconds = (race_time_s % 60).toFixed(1);
  const formattedTime = `${minutes.toString().padStart(2, '0')}:${seconds.padStart(4, '0')}`;

  const isRain = weather.condition === 'WET' || weather.condition === 'DAMP';
  const circuitMeta =
    Object.values(CIRCUIT_DATABASE).find(
      (c) =>
        c.name.toLowerCase().includes(track.name.toLowerCase()) ||
        track.name.toLowerCase().includes(c.id)
    ) || CIRCUIT_DATABASE.silverstone;

  const handlePersonaChange = (p: VoicePersona) => {
    setActivePersona(p);
    audioEngine.setPersona(p);
    audioEngine.speakRadioMessage(
      `Radio check, ${p === 'bono' ? 'Bono' : p === 'gp' ? 'GP' : p === 'xavi' ? 'Xavi' : 'APEX'} online.`
    );
  };

  const handleTrackChange = async (newTrackId: string) => {
    setIsChangingTrack(true);
    try {
      const res = await fetch('/api/race/init', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ track_name: newTrackId, seed: 42 }),
      });
      if (res.ok) {
        const data = await res.json();
        if (data.state) {
          setRaceState(data.state);
          audioEngine.speakRadioMessage(`Track session initialized: ${data.state.track.name}`);
        }
      }
    } catch (err) {
      console.error('Failed to change track:', err);
    } finally {
      setIsChangingTrack(false);
    }
  };

  const currentTrackKey =
    AVAILABLE_CIRCUITS.find((c) =>
      track.name.toLowerCase().includes(c.id) || track.name.toLowerCase().includes(c.name.toLowerCase())
    )?.id || 'silverstone';

  const TABS: { id: WorkspaceTab; label: string; icon: React.ReactNode }[] = [
    { id: 'tactical', label: 'Tactical Pit Wall', icon: <Activity className="w-3.5 h-3.5" /> },
    { id: 'telemetry', label: 'Telemetry Lab', icon: <Gauge className="w-3.5 h-3.5" /> },
    { id: 'explainability', label: 'AI Reasoning & Policy', icon: <Brain className="w-3.5 h-3.5" /> },
    { id: 'sandbox', label: 'Strategy Sandbox', icon: <Sliders className="w-3.5 h-3.5" /> },
  ];

  return (
    <header className="w-full glass-panel border-b border-apex-border px-4 lg:px-6 py-2.5 flex flex-wrap items-center justify-between gap-3 sticky top-0 z-50">
      {/* Brand & Track Info */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-400 via-blue-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-cyan-500/25 border border-cyan-300/30">
            <Activity className="w-4 h-4 text-black stroke-[2.8]" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-black text-base tracking-wider text-white">APEX</span>
              <span className="text-[9px] font-mono font-bold uppercase px-1.5 py-0.2 rounded bg-cyan-500/20 text-apex-cyan border border-cyan-500/30">
                RACE INTEL
              </span>
            </div>
            <p className="text-[11px] text-slate-400 font-medium">Digital Twin & Strategy Engine</p>
          </div>
        </div>

        <div className="h-6 w-px bg-slate-800 hidden md:block" />

        {/* Interactive Circuit Switcher */}
        <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-900/80 border border-slate-800 text-xs font-mono">
          <MapPin className="w-3.5 h-3.5 text-cyan-400" />
          <select
            value={currentTrackKey}
            onChange={(e) => handleTrackChange(e.target.value)}
            disabled={isChangingTrack}
            className="bg-transparent text-slate-200 font-bold focus:outline-none cursor-pointer text-xs"
            title="Switch Active Grand Prix Circuit"
          >
            {AVAILABLE_CIRCUITS.map((c) => (
              <option key={c.id} value={c.id} className="bg-slate-950 text-slate-200">
                {c.flag} {c.name}
              </option>
            ))}
          </select>
          <span className="text-slate-500 text-[10px]">({track.lap_distance_km} km)</span>
        </div>
      </div>

      {/* Center Navigation Tabs */}
      <div className="flex items-center bg-slate-950/80 p-1 rounded-lg border border-slate-800/80 text-xs font-mono order-3 lg:order-2">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md transition-all ${
              activeTab === tab.id
                ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-black font-bold shadow-md shadow-cyan-500/20'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
            }`}
          >
            {tab.icon}
            <span className="hidden sm:inline font-sans font-semibold text-[11px]">{tab.label}</span>
          </button>
        ))}
      </div>

      {/* Right Session Status & Audio Controls */}
      <div className="flex items-center gap-3 order-2 lg:order-3">
        {/* Lap Progress */}
        <div className="flex flex-col items-center px-3 py-1 rounded bg-slate-900/90 border border-slate-800 text-xs font-mono">
          <span className="text-[9px] text-slate-500 uppercase font-sans font-bold">Lap</span>
          <span className="font-extrabold text-apex-cyan text-sm">
            {current_lap} <span className="text-[10px] text-slate-500">/ {total_laps}</span>
          </span>
        </div>

        {/* Race Time */}
        <div className="hidden sm:flex flex-col items-center px-3 py-1 rounded bg-slate-900/90 border border-slate-800 text-xs font-mono">
          <span className="text-[9px] text-slate-500 uppercase font-sans font-bold">Session</span>
          <span className="font-bold text-slate-200 text-sm">{formattedTime}</span>
        </div>

        {/* Safety Car Status */}
        {safety_car !== 'NONE' ? (
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-amber-500/20 border border-amber-500/50 text-amber-300 animate-pulse font-sans font-bold text-xs">
            <ShieldAlert className="w-3.5 h-3.5" />
            <span>{safety_car === 'SAFETY_CAR' ? 'SAFETY CAR' : 'VSC'}</span>
          </div>
        ) : (
          <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 font-sans font-medium text-[10px]">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
            <span>TRACK CLEAR</span>
          </div>
        )}

        {/* Weather Indicator */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-900/90 border border-slate-800 text-xs">
          {isRain ? (
            <CloudRain className="w-3.5 h-3.5 text-cyan-400 animate-bounce" />
          ) : (
            <Sun className="w-3.5 h-3.5 text-amber-400" />
          )}
          <span className="text-[10px] text-slate-300 font-mono font-semibold">
            {weather.track_temp_c.toFixed(0)}°C
          </span>
        </div>

        {/* Voice Persona Selector */}
        <select
          value={activePersona}
          onChange={(e) => handlePersonaChange(e.target.value as VoicePersona)}
          className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-[10.5px] font-mono text-cyan-300 font-bold focus:outline-none focus:border-cyan-500 cursor-pointer hidden xl:inline-block"
          title="Select Race Engineer Voice Persona"
        >
          <option value="apex_core">AI: APEX Core</option>
          <option value="bono">Voice: "Bono" (Mercedes)</option>
          <option value="gp">Voice: "GP" (Red Bull)</option>
          <option value="xavi">Voice: "Xavi" (Ferrari)</option>
          <option value="guenther">Voice: "Guenther" (Haas)</option>
          <option value="hugh_bird">Voice: "Hugh Bird" (Red Bull)</option>
          <option value="ricky">Voice: "Ricky" (Ferrari)</option>
        </select>

        {/* Audio & Voice Radio Toggle */}
        <div className="flex items-center bg-slate-900/80 p-0.5 rounded-md border border-slate-800">
          <button
            onClick={toggleAudioMute}
            title={audioMuted ? 'Unmute pit wall audio' : 'Mute pit wall audio'}
            className={`p-1.5 rounded transition-all ${
              audioMuted ? 'text-rose-400 bg-rose-500/10' : 'text-slate-300 hover:text-white'
            }`}
          >
            {audioMuted ? <VolumeX className="w-3.5 h-3.5" /> : <Volume2 className="w-3.5 h-3.5" />}
          </button>
          <button
            onClick={toggleVoiceRadio}
            title={voiceRadioEnabled ? 'Voice Radio Enabled' : 'Voice Radio Disabled'}
            className={`px-1.5 py-0.5 rounded text-[9px] font-mono font-bold flex items-center gap-1 transition-all ${
              voiceRadioEnabled ? 'text-apex-cyan bg-cyan-500/10' : 'text-slate-500'
            }`}
          >
            <Radio className="w-2.5 h-2.5" />
            <span>VOICE</span>
          </button>
        </div>

        {/* Connection Mode */}
        <div className="flex items-center gap-1.5 px-2 py-1 rounded bg-slate-900/60 border border-slate-800 text-[10px] font-mono">
          <Wifi className={`w-3 h-3 ${connected ? 'text-emerald-400' : 'text-cyan-400'}`} />
          <span className={connected ? 'text-emerald-400 font-bold' : 'text-cyan-400 font-medium'}>
            {connected ? 'LIVE' : 'DIGITAL TWIN'}
          </span>
        </div>

        {isRunning && (
          <div className="flex items-center gap-1 px-2 py-0.5 rounded bg-rose-500/20 text-rose-400 border border-rose-500/30 text-[9px] font-bold uppercase tracking-wider animate-pulse">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-500" />
            SIM
          </div>
        )}
      </div>
    </header>
  );
};
