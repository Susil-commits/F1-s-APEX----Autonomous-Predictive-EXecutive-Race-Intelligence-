import React, { useState } from 'react';
import { neuralPitRadio } from '../utils/neuralRadioSynth';
import { Radio, Volume2, Play, Sparkles, MessageSquare, Award, Flame, CheckCircle2 } from 'lucide-react';

interface RadioTransmissionClip {
  id: string;
  driver: string;
  team: string;
  year: number;
  event: string;
  quote: string;
  context: string;
  tags: string[];
}

const HISTORIC_RADIO_CLIPS: RadioTransmissionClip[] = [
  {
    id: 'raikkonen_2012',
    driver: 'Kimi Räikkönen',
    team: 'Lotus F1',
    year: 2012,
    event: 'Abu Dhabi GP',
    quote: 'Leave me alone, I know what to do!',
    context: 'Leading the race under safety car, engineer gave pace updates and tire management instructions.',
    tags: ['Iconic', 'Legendary', 'Radio Silence'],
  },
  {
    id: 'wolff_2021',
    driver: 'Toto Wolff (Team Principal)',
    team: 'Mercedes-AMG',
    year: 2021,
    event: 'Abu Dhabi GP',
    quote: 'No Mikey, no no Mikey that was so not right!',
    context: 'Direct radio communication to FIA Race Director Michael Masi during controversial final safety car restart.',
    tags: ['Championship', 'Controversy', 'FIA Control'],
  },
  {
    id: 'verstappen_2020',
    driver: 'Max Verstappen',
    team: 'Red Bull Racing',
    year: 2020,
    event: '70th Anniversary GP',
    quote: 'Mate, I am not just going to sit here like a grandma!',
    context: 'Replying to Gianpiero Lambiase (GP) telling him to back off and manage tire blisters behind Mercedes.',
    tags: ['Attack Mode', 'Overtake', 'Aggressive'],
  },
  {
    id: 'sainz_2019',
    driver: 'Carlos Sainz',
    team: 'McLaren',
    year: 2019,
    event: 'British GP',
    quote: 'Smooooth Operaaator... Smooooth Operaaator!',
    context: 'Celebration radio after carving through the field to claim a brilliant P6 finish.',
    tags: ['Celebration', 'Fun', 'Smooth'],
  },
  {
    id: 'alonso_2015',
    driver: 'Fernando Alonso',
    team: 'McLaren-Honda',
    year: 2015,
    event: 'Japanese GP (Suzuka)',
    quote: 'GP2 engine! GP2! Aaargh!',
    context: 'Alonso venting frustration at straight-line speed deficit at Honda’s home circuit.',
    tags: ['Power Unit', 'Frustration', 'Straight-line'],
  },
  {
    id: 'ferrari_2022',
    driver: 'Xavi Marcos (Ferrari Engineer)',
    team: 'Scuderia Ferrari',
    year: 2022,
    event: 'Austrian GP',
    quote: 'We are checking. We are checking. Plan F.',
    context: 'Infamous Ferrari strategy radio response to Charles Leclerc asking about tire degradation windows.',
    tags: ['Pit Wall', 'Strategy', 'Ferrari'],
  },
  {
    id: 'hamilton_2019',
    driver: 'Lewis Hamilton',
    team: 'Mercedes-AMG',
    year: 2019,
    event: 'Monaco GP',
    quote: 'Bono, my tyres are dead man! I cannot keep this car behind!',
    context: 'Defending against Verstappen for 65 laps on severely degraded Medium tyres, still won the race.',
    tags: ['Tire Drama', 'Defence', 'Masterclass'],
  },
  {
    id: 'verstappen_2023',
    driver: 'Max Verstappen',
    team: 'Red Bull Racing',
    year: 2023,
    event: 'Belgian GP (Spa)',
    quote: 'I could also push on and we do another stop? A little bit of pit stop training.',
    context: 'Leading by +30 seconds at Spa, casually offering to pit for fresh tyres to practice crew drills.',
    tags: ['Dominance', 'Confidence', 'Pit Stop'],
  },
];

export const HistoricalRadioSoundboard: React.FC = () => {
  const [playingClipId, setPlayingClipId] = useState<string | null>(null);
  const [activeFilter, setActiveFilter] = useState<string>('ALL');

  const playRadioTransmission = (clip: RadioTransmissionClip) => {
    setPlayingClipId(clip.id);
    neuralPitRadio.broadcastTransmission(clip.quote, clip.driver, 'TACTICAL', 24);

    setTimeout(() => {
      setPlayingClipId(null);
    }, 3500);
  };

  const filteredClips =
    activeFilter === 'ALL'
      ? HISTORIC_RADIO_CLIPS
      : HISTORIC_RADIO_CLIPS.filter((c) =>
          c.tags.some((t) => t.toLowerCase() === activeFilter.toLowerCase()) ||
          c.driver.toLowerCase().includes(activeFilter.toLowerCase())
        );

  return (
    <div className="w-full rounded-2xl bg-slate-950 border border-slate-800 p-4 flex flex-col gap-4 shadow-2xl">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Radio className="w-5 h-5 text-rose-400 animate-pulse" />
          <div className="flex flex-col">
            <span className="font-bold text-white text-sm">
              ICONIC FIA TEAM RADIO BROADCAST ARCHIVES & SOUNDBOARD
            </span>
            <span className="text-[11px] font-mono text-slate-400">
              Legendary team radio transmissions with authentic DSP bandpass VHF acoustic filtering
            </span>
          </div>
        </div>

        {/* Filter Pills */}
        <div className="flex flex-wrap items-center gap-1.5 text-xs font-mono">
          {['ALL', 'Iconic', 'Strategy', 'Celebration', 'Tire Drama', 'Ferrari'].map((f) => (
            <button
              key={f}
              onClick={() => setActiveFilter(f)}
              className={`px-2.5 py-1 rounded-lg border transition-all ${
                activeFilter === f
                  ? 'bg-rose-500 text-black font-bold border-rose-400'
                  : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-white'
              }`}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {/* Radio Clips Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
        {filteredClips.map((clip) => {
          const isPlaying = playingClipId === clip.id;
          return (
            <div
              key={clip.id}
              onClick={() => playRadioTransmission(clip)}
              className={`p-4 rounded-xl border cursor-pointer transition-all flex flex-col justify-between gap-3 ${
                isPlaying
                  ? 'bg-rose-950/80 border-rose-500 shadow-lg shadow-rose-500/20 scale-[1.02]'
                  : 'bg-slate-900/80 border-slate-800 hover:border-slate-700 hover:bg-slate-900'
              }`}
            >
              <div className="flex flex-col gap-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-bold text-white">{clip.driver}</span>
                  <span className="text-[10px] font-mono text-slate-400">
                    {clip.year} • {clip.event}
                  </span>
                </div>

                <div className="p-2.5 rounded-lg bg-black/60 border border-slate-800/80 text-xs font-mono text-apex-cyan italic font-bold">
                  "{clip.quote}"
                </div>

                <p className="text-[11px] text-slate-400 font-mono mt-1 line-clamp-2">
                  {clip.context}
                </p>
              </div>

              <div className="flex items-center justify-between pt-2 border-t border-slate-800/60 text-[10px] font-mono">
                <span className="text-slate-500 uppercase">{clip.team}</span>
                <div className="flex items-center gap-1 text-rose-400 font-bold">
                  {isPlaying ? (
                    <>
                      <Volume2 className="w-3 h-3 animate-bounce" />
                      <span>TRANSMITTING...</span>
                    </>
                  ) : (
                    <>
                      <Play className="w-3 h-3 fill-current" />
                      <span>PLAY RADIO</span>
                    </>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
