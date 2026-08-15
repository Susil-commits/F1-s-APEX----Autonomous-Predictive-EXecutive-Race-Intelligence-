import React, { useState, useRef, useEffect } from 'react';
import { useRaceStore } from '../store/raceStore';
import {
  Bot,
  Send,
  Sparkles,
  Volume2,
  VolumeX,
  MessageSquare,
  HelpCircle,
  TrendingDown,
  Wind,
  ShieldAlert,
} from 'lucide-react';
import { audioEngine } from '../utils/audioEngine';

interface CopilotMessage {
  id: string;
  sender: 'user' | 'apex_ai';
  text: string;
  timestamp: string;
}

const QUICK_PROMPTS = [
  { id: 'p1', label: 'Undercut Window', query: 'What is our undercut window against the car ahead?' },
  { id: 'p2', label: 'Rain Arrival Risk', query: 'Analyze rain arrival probability in the next 5 laps.' },
  { id: 'p3', label: 'Tyre Cliff Horizon', query: 'When will we hit the tyre degradation cliff on this stint?' },
  { id: 'p4', label: '1-Stop vs 2-Stop', query: 'Should we extend to a 1-stop or switch to an aggressive 2-stop?' },
  { id: 'p5', label: 'Race Briefing', query: 'Summarize our current race situation, pace, and key threats.' },
];

export const AIPitWallCopilot: React.FC = () => {
  const { raceState } = useRaceStore();
  const [messages, setMessages] = useState<CopilotMessage[]>([
    {
      id: 'm1',
      sender: 'apex_ai',
      text: 'APEX AI Pit Wall Strategist online. Telemetry feeds synchronized. Ask any tactical query or select a quick briefing.',
      timestamp: '00:00',
    },
  ]);
  const [inputQuery, setInputQuery] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const chatBottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  const generateContextualResponse = (query: string): string => {
    if (!raceState) return 'Digital twin synchronizing...';

    const player = raceState.cars.find((c) => c.is_player) || raceState.cars[0];
    const leader = raceState.cars[0];
    const wear = player.tyre_wear_pct;
    const track = raceState.track;
    const qLower = query.toLowerCase();

    if (qLower.includes('undercut')) {
      const gapAhead = player.gap_to_car_ahead_s;
      const pitDelta = track.pit_lane_delta_s;
      return `Target undercut analysis: You are currently P${player.position} with a ${gapAhead.toFixed(1)}s gap to the car ahead. Fresh tyre delta will yield approximately +1.8s/lap advantage on out-lap. Pitting 1 lap earlier provides a 78% probability of jumping the car ahead upon their pit exit.`;
    }

    if (qLower.includes('rain') || qLower.includes('weather')) {
      const rainProb = (raceState.weather.rain_probability_next_5_laps * 100).toFixed(0);
      return `Meteorological radar report: Track is currently ${raceState.weather.condition} with ${rainProb}% rain probability over next 5 laps. Intermediate crossover is 35% rain intensity. If precipitation spikes above 0.35, immediate box for Intermediate tyres saves ~14 seconds over staying out on slicks.`;
    }

    if (qLower.includes('cliff') || qLower.includes('tyre') || qLower.includes('wear')) {
      const lapsToCliff = Math.max(0, Math.ceil((78 - wear) / 2.6));
      return `Tyre Degradation telemetry: Current tyre wear on ${player.tyre_compound} is ${wear.toFixed(1)}% (${player.tyre_age_laps} laps old). Cliff threshold (78%) is estimated in approximately ${lapsToCliff} laps. Beyond this point, lap time degradation increases by +2.8s per lap.`;
    }

    if (qLower.includes('1-stop') || qLower.includes('2-stop') || qLower.includes('strategy')) {
      return `Strategy model comparison: Plan A (1-Stop Medium ➔ Hard) remains optimal with lowest total race time delta (0.0s). Plan B (2-Stop Soft ➔ Medium ➔ Soft) is +3.8s slower over race distance unless an opportune Safety Car creates a cheap 12.5s pit window.`;
    }

    // Default race briefing
    return `Race status briefing [Lap ${raceState.current_lap}/${raceState.total_laps}]: Running P${player.position} (+${player.gap_to_leader_s.toFixed(2)}s to P1 ${leader.driver_name}). Tyre wear is at ${wear.toFixed(0)}% on ${player.tyre_compound}s. AI recommendation is ${raceState.active_decision?.recommendation || 'MAINTAIN'} with ${( (raceState.active_decision?.confidence_score || 0.9) * 100).toFixed(0)}% confidence.`;
  };

  const handleSend = (textToSend?: string) => {
    const query = textToSend || inputQuery.trim();
    if (!query) return;

    const userMsg: CopilotMessage = {
      id: `user_${Date.now()}`,
      sender: 'user',
      text: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputQuery('');
    setIsTyping(true);

    setTimeout(() => {
      const responseText = generateContextualResponse(query);
      const aiMsg: CopilotMessage = {
        id: `ai_${Date.now()}`,
        sender: 'apex_ai',
        text: responseText,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, aiMsg]);
      setIsTyping(false);
      audioEngine.playRadioBleep();
      audioEngine.speakRadioMessage(responseText.split('.')[0] + '.');
    }, 600);
  };

  return (
    <div className="glass-panel rounded-xl p-4 flex flex-col h-full border border-apex-border shadow-2xl font-mono text-xs min-h-[380px]">
      {/* Header */}
      <div className="flex items-center justify-between mb-3 border-b border-slate-800 pb-2">
        <div className="flex items-center gap-2">
          <Bot className="w-4 h-4 text-apex-cyan animate-pulse" />
          <h3 className="text-xs font-black uppercase tracking-widest text-slate-200">
            APEX Pit Wall AI Strategist Copilot
          </h3>
        </div>
        <span className="text-[10px] text-cyan-300 bg-cyan-950/40 px-2 py-0.5 rounded border border-cyan-800/50 font-bold flex items-center gap-1">
          <Sparkles className="w-3 h-3 text-cyan-400" /> Real-Time Decision LLM
        </span>
      </div>

      {/* Quick Tactical Action Buttons */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-2 mb-2 select-none">
        {QUICK_PROMPTS.map((p) => (
          <button
            key={p.id}
            onClick={() => handleSend(p.query)}
            className="px-2.5 py-1 rounded-lg bg-slate-900/90 hover:bg-slate-800 text-slate-300 hover:text-cyan-300 border border-slate-800 text-[10.5px] font-sans font-semibold shrink-0 transition-all active:scale-95"
          >
            {p.label}
          </button>
        ))}
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto space-y-2.5 pr-1 max-h-[260px]">
        {messages.map((m) => (
          <div
            key={m.id}
            className={`flex flex-col ${m.sender === 'user' ? 'items-end' : 'items-start'}`}
          >
            <div
              className={`p-2.5 rounded-xl max-w-[90%] font-sans text-xs leading-relaxed ${
                m.sender === 'user'
                  ? 'bg-cyan-950/50 text-cyan-200 border border-cyan-700/50 rounded-br-none'
                  : 'bg-slate-900/90 text-slate-200 border border-slate-800 rounded-bl-none shadow-md'
              }`}
            >
              {m.sender === 'apex_ai' && (
                <div className="flex items-center gap-1 text-[10px] font-mono text-cyan-400 font-bold mb-1">
                  <Bot className="w-3 h-3" />
                  <span>RACE STRATEGIST</span>
                </div>
              )}
              <p className="text-[11.5px]">{m.text}</p>
            </div>
            <span className="text-[9px] text-slate-500 font-mono mt-0.5 px-1">{m.timestamp}</span>
          </div>
        ))}

        {isTyping && (
          <div className="flex items-center gap-1.5 p-2 rounded-lg bg-slate-900/80 border border-slate-800 text-cyan-400 text-xs w-28">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-bounce" />
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-bounce [animation-delay:0.2s]" />
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-bounce [animation-delay:0.4s]" />
          </div>
        )}
        <div ref={chatBottomRef} />
      </div>

      {/* Input Field Form */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        className="mt-3 pt-2.5 border-t border-slate-800 flex items-center gap-2"
      >
        <input
          type="text"
          value={inputQuery}
          onChange={(e) => setInputQuery(e.target.value)}
          placeholder="Ask pit wall AI strategist (e.g. 'What is our undercut risk?')..."
          className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500 font-sans"
        />
        <button
          type="submit"
          className="p-2 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-black font-bold shadow-md shadow-cyan-500/20 transition-all active:scale-95"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
};
