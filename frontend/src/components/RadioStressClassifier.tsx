import React, { useState } from 'react';
import { useRaceStore } from '../store/raceStore';
import { Radio, Mic, Activity, Heart, Sparkles, MessageSquare, CheckCircle2 } from 'lucide-react';
import confetti from 'canvas-confetti';

interface RadioSample {
  id: string;
  driver: string;
  transcript: string;
  pitchHz: number;
  jitterPct: number;
  speechRateWpm: number;
  detectedEmotion: 'PANIC' | 'FRUSTRATION' | 'HYPER_FOCUSED' | 'EXHAUSTION' | 'DEFIANT';
  recommendedResponse: string;
}

const RADIO_SAMPLES: RadioSample[] = [
  {
    id: 'sample-1',
    driver: 'Car #1 (Max V.)',
    transcript: 'Mate! The balance is completely gone on front right! I cannot turn the car in!',
    pitchHz: 284,
    jitterPct: 4.8,
    speechRateWpm: 195,
    detectedEmotion: 'FRUSTRATION',
    recommendedResponse: 'Understood Max, we see the front graining. Switch to DIFF MID 60 and EB 4 to protect the tyre.',
  },
  {
    id: 'sample-2',
    driver: 'Car #44 (Lewis H.)',
    transcript: 'Bono, my tyres are dead man... he is right on my gearbox.',
    pitchHz: 210,
    jitterPct: 2.1,
    speechRateWpm: 110,
    detectedEmotion: 'EXHAUSTION',
    recommendedResponse: 'Copy Lewis, you are matching his laptimes. Mode 6 and full battery deploy onto the straight.',
  },
  {
    id: 'sample-3',
    driver: 'Car #16 (Charles L.)',
    transcript: 'NOOOO! What are you doing?! Why did we box?!',
    pitchHz: 345,
    jitterPct: 6.5,
    speechRateWpm: 215,
    detectedEmotion: 'PANIC',
    recommendedResponse: 'Stay focused Charles. We are on the new mediums with 12 laps remaining. Hunt them down.',
  },
  {
    id: 'sample-4',
    driver: 'Car #4 (Lando N.)',
    transcript: 'Gap ahead is 1.4. I am catching him by 3 tenths a lap. Leave me to it.',
    pitchHz: 165,
    jitterPct: 1.2,
    speechRateWpm: 130,
    detectedEmotion: 'HYPER_FOCUSED',
    recommendedResponse: 'Head down Lando, gap is now 1.1. DRS available at turn 1.',
  },
];

export const RadioStressClassifier: React.FC = () => {
  const [selectedSample, setSelectedSample] = useState<RadioSample>(RADIO_SAMPLES[0]);
  const [responseSent, setResponseSent] = useState<boolean>(false);

  const handleSendResponse = () => {
    setResponseSent(true);
    confetti({ particleCount: 35, spread: 50 });
  };

  const getEmotionColor = (emotion: RadioSample['detectedEmotion']) => {
    switch (emotion) {
      case 'PANIC':
        return 'bg-rose-600 text-white border-rose-400 animate-pulse';
      case 'FRUSTRATION':
        return 'bg-amber-500 text-black border-amber-400 font-bold';
      case 'HYPER_FOCUSED':
        return 'bg-emerald-500 text-black border-emerald-400 font-bold';
      case 'EXHAUSTION':
        return 'bg-purple-500/20 text-purple-300 border-purple-500/40';
      default:
        return 'bg-slate-800 text-white border-slate-700';
    }
  };

  return (
    <div className="w-full rounded-2xl bg-slate-950 border border-slate-800 p-4 flex flex-col gap-4 shadow-2xl">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Radio className="w-5 h-5 text-rose-400 animate-pulse" />
          <div className="flex flex-col">
            <span className="font-bold text-white text-sm">
              DRIVER RADIO VOICE ACOUSTIC STRESS & EMOTION CLASSIFIER
            </span>
            <span className="text-[11px] font-mono text-slate-400">
              DSP pitch extraction (F0), vocal jitter % analysis, cognitive state detection & de-escalation response AI
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2 bg-slate-900 px-3 py-1.5 rounded-xl border border-slate-800 text-xs font-mono">
          <span className="text-slate-400">Audio Classifier: </span>
          <strong className="text-emerald-400">ONLINE (250 Hz DSP FFT)</strong>
        </div>
      </div>

      {/* Primary Stress KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 font-mono">
        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] text-slate-400 uppercase">FUNDAMENTAL PITCH (F0)</span>
          <div className="flex items-baseline gap-1">
            <span className={`text-3xl font-black ${selectedSample.pitchHz > 250 ? 'text-rose-400' : 'text-emerald-400'}`}>
              {selectedSample.pitchHz}
            </span>
            <span className="text-xs text-slate-400">HZ</span>
          </div>
          <span className="text-[10px] text-slate-400">Baseline Resting: 140 Hz</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] text-slate-400 uppercase">VOCAL JITTER (TREMOR)</span>
          <div className="flex items-baseline gap-1">
            <span className={`text-3xl font-black ${selectedSample.jitterPct > 3.0 ? 'text-amber-400' : 'text-apex-cyan'}`}>
              {selectedSample.jitterPct}%
            </span>
          </div>
          <span className="text-[10px] text-slate-400">Vocal Cord Strain</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] text-slate-400 uppercase">SPEECH CADENCE</span>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-black text-purple-400">{selectedSample.speechRateWpm}</span>
            <span className="text-xs text-slate-400">WPM</span>
          </div>
          <span className="text-[10px] text-slate-400">Urgency Velocity</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] text-slate-400 uppercase">DETECTED EMOTION</span>
          <span className={`text-xs font-mono font-bold px-2 py-1 rounded mt-1 text-center border ${getEmotionColor(selectedSample.detectedEmotion)}`}>
            {selectedSample.detectedEmotion}
          </span>
          <span className="text-[10px] text-slate-400">AI Confidence: 94.2%</span>
        </div>
      </div>

      {/* Main Grid: Radio Samples (Left 5 cols) & AI De-escalation Dispatcher (Right 7 cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 font-mono text-xs">
        {/* Samples List */}
        <div className="lg:col-span-5 flex flex-col gap-2">
          <span className="font-bold text-slate-300 uppercase border-b border-slate-800 pb-1.5">
            LIVE RADIO COMMS BUFFER
          </span>

          {RADIO_SAMPLES.map((sample) => (
            <div
              key={sample.id}
              onClick={() => {
                setSelectedSample(sample);
                setResponseSent(false);
              }}
              className={`p-3 rounded-xl border cursor-pointer transition-all flex flex-col gap-1.5 ${
                selectedSample.id === sample.id
                  ? 'bg-slate-900 border-rose-500 shadow-md shadow-rose-500/10'
                  : 'bg-slate-900/50 border-slate-800 hover:border-slate-700'
              }`}
            >
              <div className="flex justify-between items-center">
                <span className="font-bold text-white">{sample.driver}</span>
                <span className="text-[10px] text-amber-400 font-bold">{sample.pitchHz} Hz</span>
              </div>
              <p className="text-slate-300 font-sans text-xs italic line-clamp-1">"{sample.transcript}"</p>
            </div>
          ))}
        </div>

        {/* AI De-escalation Response Dispatcher */}
        <div className="lg:col-span-7 p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col justify-between gap-3">
          <div className="flex flex-col gap-2.5">
            <span className="font-bold text-slate-300 uppercase border-b border-slate-800 pb-1.5">
              AI RACE ENGINEER DE-ESCALATION COPILOT
            </span>

            <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 flex flex-col gap-1">
              <span className="text-[10px] text-slate-400 uppercase font-bold">DRIVER RADIO INPUT:</span>
              <p className="text-white font-sans text-sm italic font-medium">"{selectedSample.transcript}"</p>
            </div>

            <div className="p-3 rounded-lg bg-cyan-950/40 border border-cyan-500/40 flex flex-col gap-1">
              <span className="text-[10px] text-apex-cyan uppercase font-bold">RECOMMENDED STRATEGY RESPONSE:</span>
              <p className="text-cyan-200 font-sans text-sm">{selectedSample.recommendedResponse}</p>
            </div>
          </div>

          <button
            onClick={handleSendResponse}
            disabled={responseSent}
            className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 disabled:bg-slate-800 text-black font-bold transition-all active:scale-95 shadow-md shadow-cyan-500/20"
          >
            <MessageSquare className="w-4 h-4" />
            <span>{responseSent ? 'RADIO TRANSMISSION DISPATCHED TO DRIVER' : 'TRANSMIT AI DE-ESCALATION RADIO CALL'}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
