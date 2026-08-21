import React, { useState } from 'react';
import { useRaceStore } from '../store/raceStore';
import { MessageSquare, Mic, Sparkles, Award, Heart, ThumbsUp, Flame, CheckCircle2 } from 'lucide-react';
import confetti from 'canvas-confetti';

interface MediaQuestion {
  id: number;
  reporter: string;
  outlet: string;
  question: string;
  options: {
    label: string;
    text: string;
    effect: { chemistry: number; morale: number; reputation: number };
    tone: 'DIPLOMATIC' | 'AGGRESSIVE' | 'ANALYTICAL' | 'HUMOROUS';
  }[];
}

export const PressConferenceStudio: React.FC = () => {
  const { raceState } = useRaceStore();
  const player = raceState?.cars.find((c) => c.is_player) || raceState?.cars[0];

  // Media Ratings
  const [teamChemistry, setTeamChemistry] = useState<number>(88);
  const [driverMorale, setDriverMorale] = useState<number>(92);
  const [mediaReputation, setMediaReputation] = useState<number>(85);

  const [activeQuestionIdx, setActiveQuestionIdx] = useState<number>(0);
  const [answeredMap, setAnsweredMap] = useState<Record<number, string>>({});

  const questions: MediaQuestion[] = [
    {
      id: 1,
      reporter: 'Rachel Brookes',
      outlet: 'Sky Sports F1',
      question: `Brilliant drive today! What was going through your mind during that critical undercut window on lap ${raceState?.current_lap || 18}?`,
      options: [
        {
          label: 'Option A (Team First)',
          text: 'Full credit to the pit wall engineers and mechanics. The strategy team executed the 2.1-second stop flawlessly.',
          effect: { chemistry: +4, morale: +2, reputation: +3 },
          tone: 'DIPLOMATIC',
        },
        {
          label: 'Option B (Aggressive)',
          text: 'I knew we had the raw pace. Once I got clean air in Sector 2, nobody was going to touch us today.',
          effect: { chemistry: -1, morale: +5, reputation: +2 },
          tone: 'AGGRESSIVE',
        },
        {
          label: 'Option C (Analytical)',
          text: 'The delta-T telemetry showed our tire degradation was 0.08s/lap lower than our competitors, creating the delta window.',
          effect: { chemistry: +3, morale: +3, reputation: +5 },
          tone: 'ANALYTICAL',
        },
      ],
    },
    {
      id: 2,
      reporter: 'Will Buxton',
      outlet: 'F1 TV Paddock Pass',
      question: 'There was a very heated wheel-to-wheel moment into Turn 4 that the Stewards reviewed. Do you feel the racing was fair?',
      options: [
        {
          label: 'Option A (Analytical)',
          text: 'We were ahead at the apex by half a car length. According to FIA driving guidelines, the corner was ours.',
          effect: { chemistry: +2, morale: +3, reputation: +4 },
          tone: 'ANALYTICAL',
        },
        {
          label: 'Option B (Humorous)',
          text: 'If you no longer go for a gap that exists, you are no longer a racing driver! It is motor racing, we went car racing.',
          effect: { chemistry: +1, morale: +4, reputation: +5 },
          tone: 'HUMOROUS',
        },
        {
          label: 'Option C (Diplomatic)',
          text: 'Tough, hard racing between two championship contenders. Respect to them, and we look forward to the next battle.',
          effect: { chemistry: +3, morale: +2, reputation: +4 },
          tone: 'DIPLOMATIC',
        },
      ],
    },
    {
      id: 3,
      reporter: 'Ted Kravitz',
      outlet: "Ted's Notebook",
      question: 'We saw you switching engine maps on the steering wheel during the final 5 laps. Was there a reliability scare?',
      options: [
        {
          label: 'Option A (Diplomatic)',
          text: 'Just standard thermal management on the MGU-K and protecting the gearbox to bring the car home in one piece.',
          effect: { chemistry: +3, morale: +2, reputation: +3 },
          tone: 'DIPLOMATIC',
        },
        {
          label: 'Option B (Analytical)',
          text: 'Reconstructed telemetry detected a minor 4°C oil temperature variance, so we triggered FAILSAFE-2 as precaution.',
          effect: { chemistry: +4, morale: +3, reputation: +5 },
          tone: 'ANALYTICAL',
        },
      ],
    },
  ];

  const handleSelectAnswer = (qId: number, option: MediaQuestion['options'][0]) => {
    setAnsweredMap((prev) => ({ ...prev, [qId]: option.text }));

    setTeamChemistry((prev) => Math.min(100, Math.max(0, prev + option.effect.chemistry)));
    setDriverMorale((prev) => Math.min(100, Math.max(0, prev + option.effect.morale)));
    setMediaReputation((prev) => Math.min(100, Math.max(0, prev + option.effect.reputation)));

    if (activeQuestionIdx < questions.length - 1) {
      setActiveQuestionIdx((prev) => prev + 1);
    } else {
      confetti({ particleCount: 60, spread: 60 });
    }
  };

  const currentQ = questions[activeQuestionIdx];

  return (
    <div className="w-full rounded-2xl bg-slate-950 border border-slate-800 p-4 flex flex-col gap-4 shadow-2xl">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <MessageSquare className="w-5 h-5 text-apex-cyan animate-pulse" />
          <div className="flex flex-col">
            <span className="font-bold text-white text-sm">
              AI POST-RACE MEDIA PRESS CONFERENCE & PADDOCK STUDIO
            </span>
            <span className="text-[11px] font-mono text-slate-400">
              Interactive journalist interviews, team chemistry dynamics & media reputation management
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

      {/* Media Reputation & Chemistry KPI Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col gap-1">
          <div className="flex justify-between text-xs font-mono">
            <span className="text-slate-400 flex items-center gap-1">
              <Heart className="w-3.5 h-3.5 text-rose-400" /> TEAM CHEMISTRY
            </span>
            <span className="font-bold text-white">{teamChemistry}%</span>
          </div>
          <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
            <div className="h-full bg-rose-500 transition-all duration-500" style={{ width: `${teamChemistry}%` }} />
          </div>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col gap-1">
          <div className="flex justify-between text-xs font-mono">
            <span className="text-slate-400 flex items-center gap-1">
              <Flame className="w-3.5 h-3.5 text-amber-400" /> DRIVER MORALE
            </span>
            <span className="font-bold text-white">{driverMorale}%</span>
          </div>
          <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
            <div className="h-full bg-amber-400 transition-all duration-500" style={{ width: `${driverMorale}%` }} />
          </div>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col gap-1">
          <div className="flex justify-between text-xs font-mono">
            <span className="text-slate-400 flex items-center gap-1">
              <Award className="w-3.5 h-3.5 text-apex-cyan" /> MEDIA REPUTATION
            </span>
            <span className="font-bold text-white">{mediaReputation}%</span>
          </div>
          <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
            <div className="h-full bg-cyan-400 transition-all duration-500" style={{ width: `${mediaReputation}%` }} />
          </div>
        </div>
      </div>

      {/* Main Press Conference Stage */}
      <div className="p-5 rounded-2xl bg-gradient-to-b from-slate-900 to-slate-950 border border-slate-800 flex flex-col gap-4">
        {/* Question Bubble */}
        <div className="flex items-start gap-3 p-4 rounded-xl bg-slate-950/80 border border-slate-800">
          <div className="w-10 h-10 rounded-xl bg-rose-500/20 border border-rose-500/40 flex items-center justify-center font-bold text-rose-300 text-xs">
            <Mic className="w-5 h-5 text-rose-400" />
          </div>
          <div className="flex flex-col gap-1">
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-bold text-white">{currentQ.reporter}</span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-800">
                {currentQ.outlet}
              </span>
            </div>
            <p className="text-sm font-sans font-medium text-slate-200">
              "{currentQ.question}"
            </p>
          </div>
        </div>

        {/* Answer Options */}
        <div className="flex flex-col gap-2.5">
          <span className="text-xs font-mono text-slate-400 uppercase font-bold">
            SELECT DRIVER RESPONSE (QUESTION {activeQuestionIdx + 1} OF {questions.length}):
          </span>

          {currentQ.options.map((opt, idx) => (
            <button
              key={idx}
              onClick={() => handleSelectAnswer(currentQ.id, opt)}
              className="p-3.5 rounded-xl bg-slate-900/70 hover:bg-slate-800/90 border border-slate-800 hover:border-cyan-500/60 text-left transition-all flex flex-col gap-1 group active:scale-[0.99]"
            >
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="font-bold text-apex-cyan group-hover:text-white transition-all">
                  {opt.label}
                </span>
                <span
                  className={`text-[9px] px-2 py-0.5 rounded font-bold ${
                    opt.tone === 'DIPLOMATIC'
                      ? 'bg-emerald-500/20 text-emerald-300'
                      : opt.tone === 'AGGRESSIVE'
                      ? 'bg-rose-500/20 text-rose-300'
                      : opt.tone === 'ANALYTICAL'
                      ? 'bg-cyan-500/20 text-cyan-300'
                      : 'bg-amber-500/20 text-amber-300'
                  }`}
                >
                  {opt.tone}
                </span>
              </div>
              <p className="text-xs text-slate-300 font-sans">{opt.text}</p>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
