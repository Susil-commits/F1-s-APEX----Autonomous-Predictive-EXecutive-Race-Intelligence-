import React, { useState, useEffect, useRef } from 'react';
import { useRaceStore, WorkspaceTab } from '../store/raceStore';
import { neuralPitRadio } from '../utils/neuralRadioSynth';
import {
  Search,
  Command,
  Play,
  Pause,
  Layers,
  Flame,
  ShieldAlert,
  CloudRain,
  Zap,
  RotateCcw,
  Users,
  Brain,
  X,
  ChevronRight,
  Compass,
} from 'lucide-react';

interface PaletteAction {
  id: string;
  category: 'RACE CONTROL' | 'TACTICS' | 'NAVIGATION' | 'CIRCUITS';
  label: string;
  sublabel: string;
  icon: React.ReactNode;
  handler: () => void;
}

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  onOpenConsensus?: () => void;
  onOpenQA?: () => void;
}

export const CommandPalette: React.FC<CommandPaletteProps> = ({
  isOpen,
  onClose,
  onOpenConsensus,
  onOpenQA,
}) => {
  const [query, setQuery] = useState<string>('');
  const [selectedIndex, setSelectedIndex] = useState<number>(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const { isRunning, setRunning, setActiveTab, raceState } = useRaceStore();

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 50);
    } else {
      setQuery('');
      setSelectedIndex(0);
    }
  }, [isOpen]);

  const sendBackendEvent = async (endpoint: string, body?: any) => {
    try {
      await fetch(`http://localhost:8000/api/${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: body ? JSON.stringify(body) : undefined,
      });
    } catch (e) {
      console.warn('[APEX Command] Backend action error:', e);
    }
  };

  const actions: PaletteAction[] = [
    // Race Control
    {
      id: 'sim_toggle',
      category: 'RACE CONTROL',
      label: isRunning ? 'Pause Race Simulation' : 'Play / Resume Race Simulation',
      sublabel: 'Toggle WebSocket engine tick loop',
      icon: isRunning ? <Pause className="w-4 h-4 text-amber-400" /> : <Play className="w-4 h-4 text-emerald-400" />,
      handler: () => {
        sendBackendEvent(isRunning ? 'control/pause' : 'control/play');
        setRunning(!isRunning);
        onClose();
      },
    },
    {
      id: 'sc_full',
      category: 'RACE CONTROL',
      label: 'Deploy Full Safety Car (SC)',
      sublabel: 'Reduce pace by 60%, compress field delta',
      icon: <ShieldAlert className="w-4 h-4 text-yellow-400" />,
      handler: () => {
        sendBackendEvent('scenarios/safety-car', { type: 'SAFETY_CAR' });
        neuralPitRadio.broadcastTransmission('Safety Car deployed. Maintain positive delta.', 'Pit Wall Chief', 'SAFETY_CAR');
        onClose();
      },
    },
    {
      id: 'sc_vsc',
      category: 'RACE CONTROL',
      label: 'Deploy Virtual Safety Car (VSC)',
      sublabel: 'Maintain delta time, 10s pit advantage window',
      icon: <ShieldAlert className="w-4 h-4 text-amber-400" />,
      handler: () => {
        sendBackendEvent('scenarios/safety-car', { type: 'VSC' });
        neuralPitRadio.broadcastTransmission('Virtual Safety Car deployed. Target delta positive.', 'Race Engineer', 'TACTICAL');
        onClose();
      },
    },
    {
      id: 'rain_front',
      category: 'RACE CONTROL',
      label: 'Inject Rain Front (Heavy Rainstorm)',
      sublabel: 'Triggers wet track conditions and crossover window',
      icon: <CloudRain className="w-4 h-4 text-cyan-400" />,
      handler: () => {
        sendBackendEvent('scenarios/weather', { rain_intensity: 0.75 });
        neuralPitRadio.broadcastTransmission('Heavy rain incoming across sector 2 and 3.', 'Tyre Specialist', 'URGENT');
        onClose();
      },
    },

    // Tactical Actions
    {
      id: 'box_soft',
      category: 'TACTICS',
      label: 'Box APEX Car for Soft Tyres',
      sublabel: 'Queue pit stop for red Soft compound',
      icon: <Flame className="w-4 h-4 text-rose-400" />,
      handler: () => {
        sendBackendEvent('strategy/override', { action: 'PIT_SOFT' });
        neuralPitRadio.broadcastTransmission('Box this lap for Soft tyres. Confirm pit lane in.', 'Race Engineer', 'URGENT');
        onClose();
      },
    },
    {
      id: 'box_hard',
      category: 'TACTICS',
      label: 'Box APEX Car for Hard Tyres',
      sublabel: 'Queue pit stop for white Hard compound',
      icon: <Flame className="w-4 h-4 text-slate-300" />,
      handler: () => {
        sendBackendEvent('strategy/override', { action: 'PIT_HARD' });
        neuralPitRadio.broadcastTransmission('Box this lap for Hard tyres.', 'Race Engineer', 'URGENT');
        onClose();
      },
    },
    {
      id: 'mode_push',
      category: 'TACTICS',
      label: 'Switch Driving Mode to PUSH (+0.8s pace)',
      sublabel: 'Aggressive pace, elevated tyre degradation',
      icon: <Zap className="w-4 h-4 text-rose-500" />,
      handler: () => {
        sendBackendEvent('strategy/override', { action: 'PUSH' });
        neuralPitRadio.broadcastTransmission('Strat 3, switch to push mode now.', 'Race Engineer', 'TACTICAL');
        onClose();
      },
    },
    {
      id: 'mode_conserve',
      category: 'TACTICS',
      label: 'Switch Driving Mode to CONSERVE',
      sublabel: 'Tyre & fuel saving mode (-40% wear)',
      icon: <Zap className="w-4 h-4 text-emerald-400" />,
      handler: () => {
        sendBackendEvent('strategy/override', { action: 'CONSERVE' });
        neuralPitRadio.broadcastTransmission('Tyre management phase, switch to conserve.', 'Race Engineer', 'TACTICAL');
        onClose();
      },
    },

    // Navigation
    {
      id: 'nav_tactical',
      category: 'NAVIGATION',
      label: 'Go to Tactical Pit Wall Command Center',
      sublabel: 'Timing tower, circuit GPS, live telemetry',
      icon: <Layers className="w-4 h-4 text-apex-cyan" />,
      handler: () => {
        setActiveTab('tactical');
        onClose();
      },
    },
    {
      id: 'nav_strategy',
      category: 'NAVIGATION',
      label: 'Go to Strategy Center & Stint Planner',
      sublabel: 'Monte Carlo, Isochrone matrix, stint timeline',
      icon: <Layers className="w-4 h-4 text-purple-400" />,
      handler: () => {
        setActiveTab('strategy_center');
        onClose();
      },
    },
    {
      id: 'nav_telemetry',
      category: 'NAVIGATION',
      label: 'Go to Deep Telemetry & Aero Lab',
      sublabel: 'Multi-driver overlays, Delta-T decomposition',
      icon: <Layers className="w-4 h-4 text-blue-400" />,
      handler: () => {
        setActiveTab('telemetry');
        onClose();
      },
    },
    {
      id: 'open_consensus',
      category: 'NAVIGATION',
      label: 'Open Pit Wall 5-Agent Consensus Modal',
      sublabel: 'Multi-agent vote: Strategist, Tyre, Weather, Engineer',
      icon: <Users className="w-4 h-4 text-emerald-400" />,
      handler: () => {
        onClose();
        if (onOpenConsensus) onOpenConsensus();
      },
    },
    {
      id: 'open_rag_qa',
      category: 'NAVIGATION',
      label: 'Open RAG Race Debrief QA Modal',
      sublabel: 'Ask AI questions about current and historical race decisions',
      icon: <Brain className="w-4 h-4 text-cyan-400" />,
      handler: () => {
        onClose();
        if (onOpenQA) onOpenQA();
      },
    },

    // Circuit Selectors
    {
      id: 'track_suzuka',
      category: 'CIRCUITS',
      label: 'Load Suzuka Circuit (Japan 🇯🇵)',
      sublabel: 'Figure-8 crossover, 130R, Degner curves',
      icon: <Compass className="w-4 h-4 text-rose-400" />,
      handler: () => {
        sendBackendEvent('session/init', { track_name: 'suzuka', seed: 42 });
        onClose();
      },
    },
    {
      id: 'track_cota',
      category: 'CIRCUITS',
      label: 'Load Circuit of the Americas (COTA 🇺🇸)',
      sublabel: 'Steep hill Turn 1, multi-apex carousel',
      icon: <Compass className="w-4 h-4 text-blue-400" />,
      handler: () => {
        sendBackendEvent('session/init', { track_name: 'cota', seed: 42 });
        onClose();
      },
    },
    {
      id: 'track_singapore',
      category: 'CIRCUITS',
      label: 'Load Marina Bay Street Circuit (Singapore 🇸🇬)',
      sublabel: 'High-downforce night street circuit',
      icon: <Compass className="w-4 h-4 text-amber-400" />,
      handler: () => {
        sendBackendEvent('session/init', { track_name: 'singapore', seed: 42 });
        onClose();
      },
    },
    {
      id: 'track_redbullring',
      category: 'CIRCUITS',
      label: 'Load Red Bull Ring (Austria 🇦🇹)',
      sublabel: 'Short high-speed layout with 3 DRS zones',
      icon: <Compass className="w-4 h-4 text-red-500" />,
      handler: () => {
        sendBackendEvent('session/init', { track_name: 'redbullring', seed: 42 });
        onClose();
      },
    },
  ];

  const filtered = actions.filter(
    (a) =>
      a.label.toLowerCase().includes(query.toLowerCase()) ||
      a.sublabel.toLowerCase().includes(query.toLowerCase()) ||
      a.category.toLowerCase().includes(query.toLowerCase())
  );

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev + 1) % filtered.length);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev - 1 + filtered.length) % filtered.length);
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (filtered[selectedIndex]) {
        filtered[selectedIndex].handler();
      }
    } else if (e.key === 'Escape') {
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-24 p-4 bg-black/80 backdrop-blur-md animate-fadeIn">
      <div
        className="w-full max-w-2xl bg-slate-950 border border-slate-700/80 rounded-2xl shadow-2xl overflow-hidden flex flex-col"
        onKeyDown={handleKeyDown}
      >
        {/* Search Input Header */}
        <div className="flex items-center gap-3 px-4 py-3.5 border-b border-slate-800 bg-slate-900/90">
          <Search className="w-5 h-5 text-slate-400" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setSelectedIndex(0);
            }}
            placeholder="Type a command or search action (e.g., 'Safety Car', 'Box Soft', 'Suzuka')..."
            className="flex-1 bg-transparent text-white placeholder-slate-500 text-sm font-mono focus:outline-none"
          />
          <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-slate-800 text-[11px] font-mono text-slate-400 border border-slate-700">
            <span>ESC</span>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white p-1 rounded-lg">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Results List */}
        <div className="max-h-96 overflow-y-auto p-2 flex flex-col gap-1">
          {filtered.length > 0 ? (
            filtered.map((action, idx) => (
              <div
                key={action.id}
                onClick={action.handler}
                onMouseEnter={() => setSelectedIndex(idx)}
                className={`flex items-center justify-between p-3 rounded-xl cursor-pointer transition-all ${
                  selectedIndex === idx
                    ? 'bg-slate-800 text-white shadow-sm'
                    : 'text-slate-300 hover:bg-slate-900'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-slate-950/80 border border-slate-800">
                    {action.icon}
                  </div>
                  <div className="flex flex-col">
                    <span className="text-xs font-mono font-bold">{action.label}</span>
                    <span className="text-[11px] font-mono text-slate-400">{action.sublabel}</span>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-800">
                    {action.category}
                  </span>
                  <ChevronRight className="w-4 h-4 text-slate-500" />
                </div>
              </div>
            ))
          ) : (
            <div className="text-center py-12 text-slate-500 font-mono text-xs">
              No matching commands found for "{query}".
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-4 py-2 bg-slate-900/60 border-t border-slate-800/80 text-[11px] font-mono text-slate-400">
          <div className="flex items-center gap-3">
            <span>↑↓ Navigate</span>
            <span>↵ Execute</span>
            <span>ESC Dismiss</span>
          </div>
          <div className="flex items-center gap-1 text-apex-cyan">
            <Command className="w-3.5 h-3.5" />
            <span>APEX MISSION CONTROL</span>
          </div>
        </div>
      </div>
    </div>
  );
};
