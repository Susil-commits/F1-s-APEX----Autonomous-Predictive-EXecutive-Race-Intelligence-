import React, { useState } from 'react';
import { useRaceStore } from '../store/raceStore';
import { ShieldAlert, Video, Flag, AlertTriangle, CheckCircle2, Scale, Play, RotateCcw, Award } from 'lucide-react';
import confetti from 'canvas-confetti';

interface IncidentCase {
  id: string;
  title: string;
  lap: number;
  involvedCars: string[];
  severity: 'INVESTIGATING' | 'PENALTY_APPLIED' | 'NO_FURTHER_ACTION';
  description: string;
  telemetryEvidence: string;
  currentVerdict?: string;
}

export const StewardInvestigationRoom: React.FC = () => {
  const { raceState } = useRaceStore();

  const [incidents, setIncidents] = useState<IncidentCase[]>([
    {
      id: 'INC-01',
      title: 'Turn 4 Collision & Forcing Off Track',
      lap: raceState?.current_lap || 14,
      involvedCars: ['#1 M. Verstappen', '#4 L. Norris'],
      severity: 'INVESTIGATING',
      description: 'Car #1 carried higher entry speed into apex and did not leave sufficient racing room on exit of Turn 4.',
      telemetryEvidence: 'Delta Speed at Apex: +8 km/h • Lateral Separation: 0.12m • Throttle pickup: 95%',
    },
    {
      id: 'INC-02',
      title: 'Turn 9 Copse Track Limits (3rd Strike)',
      lap: raceState?.current_lap || 12,
      involvedCars: ['#44 L. Hamilton'],
      severity: 'INVESTIGATING',
      description: 'Car #44 exceeded track boundaries with all 4 wheels beyond the white line at Turn 9 exit.',
      telemetryEvidence: 'Optical Sensor 9B Triggered • Wheel Extent: +14cm beyond curb',
    },
    {
      id: 'INC-03',
      title: 'Unsafe Pit Lane Release into Fast Lane',
      lap: raceState?.current_lap || 10,
      involvedCars: ['#55 C. Sainz', '#16 C. Leclerc'],
      severity: 'INVESTIGATING',
      description: 'Car #55 released from pit box into the fast lane directly into the path of incoming Car #16.',
      telemetryEvidence: 'Pit Rejoin Proximity: 0.8m • Car #16 forced to brake 40 bar',
    },
  ]);

  const [selectedIncidentId, setSelectedIncidentId] = useState<string>('INC-01');
  const [selectedAngle, setSelectedAngle] = useState<'HELI' | 'ONBOARD_1' | 'ONBOARD_2' | 'OPTICAL'>('HELI');

  const activeIncident = incidents.find((i) => i.id === selectedIncidentId) || incidents[0];

  const applyVerdict = (verdict: string, isPenalty: boolean = true) => {
    setIncidents((prev) =>
      prev.map((inc) =>
        inc.id === activeIncident.id
          ? {
              ...inc,
              severity: isPenalty ? 'PENALTY_APPLIED' : 'NO_FURTHER_ACTION',
              currentVerdict: verdict,
            }
          : inc
      )
    );

    if (isPenalty) {
      confetti({ particleCount: 40, spread: 50 });
    }
  };

  return (
    <div className="w-full rounded-2xl bg-slate-950 border border-slate-800 p-4 flex flex-col gap-4 shadow-2xl">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Scale className="w-5 h-5 text-amber-400 animate-pulse" />
          <div className="flex flex-col">
            <span className="font-bold text-white text-sm">
              FIA RACE CONTROL & STEWARDS INCIDENT INVESTIGATION VAR ROOM
            </span>
            <span className="text-[11px] font-mono text-slate-400">
              Multi-angle VAR incident scrubbers, telemetry forensics & official FIA penalty adjudication
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2 bg-slate-900 px-3 py-1.5 rounded-xl border border-slate-800 text-xs font-mono">
          <ShieldAlert className="w-4 h-4 text-amber-400" />
          <span className="text-slate-300">Active Investigations: </span>
          <strong className="text-white">{incidents.filter((i) => i.severity === 'INVESTIGATING').length}</strong>
        </div>
      </div>

      {/* Main Grid: Incident List & VAR Screen */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Incident Case Selector (Left 4 cols) */}
        <div className="lg:col-span-4 flex flex-col gap-2.5">
          <span className="text-xs font-mono text-slate-400 uppercase font-bold">
            INCIDENT DOCKET (RACE LAP {raceState?.current_lap || 14})
          </span>

          {incidents.map((inc) => (
            <div
              key={inc.id}
              onClick={() => setSelectedIncidentId(inc.id)}
              className={`p-3 rounded-xl border cursor-pointer transition-all flex flex-col gap-1.5 ${
                selectedIncidentId === inc.id
                  ? 'bg-slate-900 border-amber-500 shadow-md shadow-amber-500/10'
                  : 'bg-slate-900/50 border-slate-800 hover:border-slate-700'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-bold text-white">{inc.id} • {inc.title}</span>
                <span
                  className={`text-[9px] font-mono font-bold px-1.5 py-0.5 rounded ${
                    inc.severity === 'PENALTY_APPLIED'
                      ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                      : inc.severity === 'NO_FURTHER_ACTION'
                      ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                      : 'bg-amber-500/20 text-amber-300 border border-amber-500/40 animate-pulse'
                  }`}
                >
                  {inc.severity.replace(/_/g, ' ')}
                </span>
              </div>

              <div className="text-[11px] font-mono text-slate-400 flex justify-between">
                <span>Cars: {inc.involvedCars.join(' vs ')}</span>
                <span>Lap {inc.lap}</span>
              </div>

              {inc.currentVerdict && (
                <div className="text-[11px] font-mono text-amber-300 font-bold mt-1 bg-black/40 p-1.5 rounded">
                  Verdict: {inc.currentVerdict}
                </div>
              )}
            </div>
          ))}
        </div>

        {/* VAR Video Review & Adjudication (Right 8 cols) */}
        <div className="lg:col-span-8 flex flex-col gap-4">
          {/* VAR Camera Multi-Angle Screen */}
          <div className="relative w-full h-[320px] rounded-xl overflow-hidden bg-black border border-slate-800 flex items-center justify-center">
            <div className="text-center flex flex-col items-center gap-2 text-slate-600">
              <Video className="w-10 h-10 text-slate-700 animate-pulse" />
              <span className="font-mono text-xs uppercase text-slate-400 font-bold">
                FIA VAR ANGLE: {selectedAngle}
              </span>
              <span className="text-[11px] font-mono text-slate-500">
                120 FPS SYNCHRONIZED FORENSIC TELEMETRY REPLAY
              </span>
            </div>

            {/* Camera Angle Selector */}
            <div className="absolute top-3 left-3 flex items-center gap-1.5 bg-black/80 backdrop-blur-md p-1 rounded-lg border border-slate-700 text-[10px] font-mono">
              {(['HELI', 'ONBOARD_1', 'ONBOARD_2', 'OPTICAL'] as const).map((angle) => (
                <button
                  key={angle}
                  onClick={() => setSelectedAngle(angle)}
                  className={`px-2 py-0.5 rounded transition-all ${
                    selectedAngle === angle
                      ? 'bg-amber-500 text-black font-bold'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  {angle}
                </button>
              ))}
            </div>

            {/* Incident Title Tag */}
            <div className="absolute bottom-3 left-3 bg-black/80 backdrop-blur-md px-3 py-1.5 rounded-lg border border-slate-700 text-xs font-mono text-white">
              Incident: <strong className="text-amber-400">{activeIncident.title}</strong>
            </div>
          </div>

          {/* Telemetry Evidence Box */}
          <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col gap-1.5 text-xs font-mono">
            <span className="text-slate-300 font-bold uppercase">FIA TELEMETRY FORENSIC EVIDENCE:</span>
            <p className="text-slate-400">{activeIncident.description}</p>
            <p className="text-apex-cyan bg-slate-950 p-2 rounded-lg border border-slate-800">
              {activeIncident.telemetryEvidence}
            </p>
          </div>

          {/* Official FIA Penalty Adjudication Action Panel */}
          <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col gap-3">
            <span className="text-xs font-mono text-amber-400 font-bold uppercase">
              STEWARDS OFFICIAL VERDICT ADJUDICATION
            </span>

            <div className="flex flex-wrap items-center gap-2">
              <button
                onClick={() => applyVerdict('5-SECOND TIME PENALTY')}
                className="px-3 py-1.5 rounded-lg bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/50 text-xs font-mono font-bold transition-all active:scale-95"
              >
                + 5s Time Penalty
              </button>

              <button
                onClick={() => applyVerdict('10-SECOND TIME PENALTY')}
                className="px-3 py-1.5 rounded-lg bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 border border-rose-500/50 text-xs font-mono font-bold transition-all active:scale-95"
              >
                + 10s Time Penalty
              </button>

              <button
                onClick={() => applyVerdict('DRIVE-THROUGH PENALTY')}
                className="px-3 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-mono font-bold transition-all active:scale-95"
              >
                Drive-Through Penalty
              </button>

              <button
                onClick={() => applyVerdict('BLACK & WHITE FLAG (WARNING)')}
                className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-white border border-slate-600 text-xs font-mono font-bold transition-all active:scale-95"
              >
                Black & White Warning
              </button>

              <button
                onClick={() => applyVerdict('NO FURTHER ACTION (RACING INCIDENT)', false)}
                className="px-3 py-1.5 rounded-lg bg-emerald-950 hover:bg-emerald-900 text-emerald-300 border border-emerald-700 text-xs font-mono font-bold transition-all active:scale-95 ml-auto"
              >
                No Further Action
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
