import React, { useState, useEffect } from 'react';
import { useRaceStore } from '../store/raceStore';
import {
  CloudRain,
  Sun,
  ShieldAlert,
  Zap,
  MapPin,
  Clock,
  Gauge,
  SlidersHorizontal,
} from 'lucide-react';
import { CIRCUIT_DATABASE } from '../data/trackGeometries';

export type AppMode = 'simple' | 'pitwall';

interface HeaderProps {
  appMode: AppMode;
  onSelectMode: (mode: AppMode) => void;
}

const AVAILABLE_CIRCUITS = [
  { id: 'silverstone', name: 'Silverstone Circuit', flag: '🇬🇧' },
  { id: 'monza', name: 'Autodromo Nazionale Monza', flag: '🇮🇹' },
  { id: 'spa', name: 'Circuit de Spa-Francorchamps', flag: '🇧🇪' },
  { id: 'monaco', name: 'Circuit de Monaco', flag: '🇲🇨' },
  { id: 'interlagos', name: 'Autódromo de Interlagos', flag: '🇧🇷' },
  { id: 'suzuka', name: 'Suzuka Racing Course', flag: '🇯🇵' },
  { id: 'cota', name: 'Circuit of the Americas', flag: '🇺🇸' },
  { id: 'singapore', name: 'Marina Bay Circuit', flag: '🇸🇬' },
  { id: 'redbullring', name: 'Red Bull Ring (Spielberg)', flag: '🇦🇹' },
];

export const Header: React.FC<HeaderProps> = ({ appMode, onSelectMode }) => {
  const { raceState, setRaceState, connected } = useRaceStore();
  const [isChangingTrack, setIsChangingTrack] = useState<boolean>(false);
  const [currentTimeUTC, setCurrentTimeUTC] = useState<string>('');

  useEffect(() => {
    const updateTime = () => {
      const d = new Date();
      setCurrentTimeUTC(
        `${d.getUTCHours().toString().padStart(2, '0')}:${d
          .getUTCMinutes()
          .toString()
          .padStart(2, '0')}:${d.getUTCSeconds().toString().padStart(2, '0')} UTC`
      );
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const current_lap = raceState?.current_lap || 1;
  const total_laps = raceState?.total_laps || 52;
  const race_time_s = raceState?.race_time_s || 0;
  const weather = raceState?.weather || { condition: 'DRY', track_temp_c: 32, air_temp_c: 24, rain_intensity: 0 };
  const safety_car = raceState?.safety_car || 'NONE';
  const trackName = raceState?.track?.name || 'Silverstone Circuit';
  const trackDistance = raceState?.track?.lap_distance_km || 5.89;

  // Format race session time
  const minutes = Math.floor(race_time_s / 60);
  const seconds = (race_time_s % 60).toFixed(1);
  const formattedTime = `${minutes.toString().padStart(2, '0')}:${seconds.padStart(4, '0')}`;

  const isRain = weather.condition === 'WET' || weather.condition === 'DAMP';

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
      trackName.toLowerCase().includes(c.id) || trackName.toLowerCase().includes(c.name.toLowerCase())
    )?.id || 'silverstone';

  return (
    <header className="w-full bg-[#090B10]/95 backdrop-blur-xl border-b border-[#1F2432] px-4 lg:px-6 py-2.5 flex flex-wrap items-center justify-between gap-3 sticky top-0 z-50 shadow-2xl shadow-black/80 relative">
      {/* Red underline accent */}
      <div className="absolute bottom-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-[#E10600] to-transparent opacity-80" />

      {/* Brand & Track Info */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-3">
          {/* Official F1 Red Angle Box */}
          <div className="h-9 px-3 rounded bg-gradient-to-r from-[#E10600] to-[#B30000] flex items-center justify-center shadow-lg shadow-red-600/30 border-t border-white/20 -skew-x-12">
            <span className="font-black text-sm tracking-tighter text-white uppercase skew-x-12 flex items-center gap-1.5 font-sans">
              <Zap className="w-3.5 h-3.5 fill-white" />
              APEX
            </span>
          </div>

          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-black text-sm tracking-wider text-white font-sans">RACE INTELLIGENCE</span>
              <span className="text-[9px] font-mono font-black uppercase px-1.5 py-0.5 rounded bg-red-950 text-red-400 border border-red-800">
                F1 OPS
              </span>
            </div>
            <p className="text-[10px] text-slate-400 font-mono tracking-tight">Formula 1 Predictive & Executive Engine</p>
          </div>
        </div>

        <div className="h-6 w-px bg-[#232736] hidden md:block" />

        {/* Interactive Circuit Switcher */}
        <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#131722] border border-[#232736] text-xs font-mono">
          <MapPin className="w-3.5 h-3.5 text-[#E10600]" />
          <select
            value={currentTrackKey}
            onChange={(e) => handleTrackChange(e.target.value)}
            disabled={isChangingTrack}
            className="bg-transparent text-white font-bold focus:outline-none cursor-pointer text-xs"
            title="Switch Active Grand Prix Circuit"
          >
            {AVAILABLE_CIRCUITS.map((c) => (
              <option key={c.id} value={c.id} className="bg-[#0B0D13] text-white">
                {c.flag} {c.name}
              </option>
            ))}
          </select>
          <span className="text-slate-400 text-[10px]">({trackDistance} km)</span>
        </div>
      </div>

      {/* CENTER STAGE: DRS-STYLE DUAL-MODE TOGGLE */}
      <div className="flex items-center bg-[#07090E] p-1 rounded-xl border border-[#232736] shadow-inner font-mono text-xs order-3 lg:order-2">
        <button
          onClick={() => onSelectMode('simple')}
          className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg transition-all cursor-pointer ${
            appMode === 'simple'
              ? 'bg-[#E10600] text-white font-black shadow-md shadow-red-600/40'
              : 'text-slate-400 hover:text-slate-200 hover:bg-[#121520]'
          }`}
        >
          <Zap className="w-3.5 h-3.5" />
          <span className="font-bold uppercase tracking-wider">Simple Mode (V1)</span>
        </button>

        <button
          onClick={() => onSelectMode('pitwall')}
          className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg transition-all cursor-pointer ${
            appMode === 'pitwall'
              ? 'bg-[#E10600] text-white font-black shadow-md shadow-red-600/40'
              : 'text-slate-400 hover:text-slate-200 hover:bg-[#121520]'
          }`}
        >
          <Gauge className="w-3.5 h-3.5" />
          <span className="font-bold uppercase tracking-wider">Pit-Wall Mode (V2)</span>
        </button>
      </div>

      {/* RIGHT: BROADCAST LOWER-THIRD CLOCK & TELEMETRY */}
      <div className="flex items-center gap-2 lg:gap-3 order-2 lg:order-3">
        {/* Broadcast Live Session Clock */}
        <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#10131B] border border-[#232736] text-xs font-mono text-slate-300">
          <Clock className="w-3.5 h-3.5 text-[#00F0FF]" />
          <span className="font-bold text-white tracking-widest">{currentTimeUTC}</span>
        </div>

        {/* Weather Badge */}
        <div className="flex items-center gap-1.5 px-2 py-1 rounded bg-[#131722] border border-[#232736] text-xs font-mono">
          {isRain ? (
            <CloudRain className="w-3.5 h-3.5 text-cyan-400 animate-bounce" />
          ) : (
            <Sun className="w-3.5 h-3.5 text-amber-400" />
          )}
          <span className="font-bold text-white text-[11px]">{weather.track_temp_c}°C</span>
        </div>

        {/* Safety Car Badge */}
        {safety_car !== 'NONE' && (
          <div className="flex items-center gap-1 px-2 py-0.5 rounded bg-yellow-950 border border-yellow-700 text-[10px] font-mono font-bold text-yellow-300 animate-pulse">
            <ShieldAlert className="w-3.5 h-3.5 text-yellow-400" />
            <span>{safety_car}</span>
          </div>
        )}

        {/* Lap Counter */}
        <div className="px-2.5 py-1 rounded bg-[#131722] border border-[#232736] text-xs font-mono font-bold text-slate-200">
          <span className="text-[#E10600]">L{current_lap}</span>/{total_laps}
        </div>

        {/* Live WS Status Indicator */}
        <div className="flex items-center gap-1.5 px-2 py-1 rounded bg-[#131722] border border-[#232736] text-[11px] font-mono">
          <div
            className={`w-2 h-2 rounded-full ${
              connected ? 'bg-emerald-500 shadow-sm shadow-emerald-500/50' : 'bg-red-500 animate-ping'
            }`}
          />
          <span className="text-slate-300 text-[10px] hidden sm:inline">{connected ? 'LIVE' : 'OFFLINE'}</span>
        </div>
      </div>
    </header>
  );
};
