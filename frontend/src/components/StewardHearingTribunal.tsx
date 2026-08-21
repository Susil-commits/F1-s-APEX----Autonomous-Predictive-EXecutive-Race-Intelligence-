import React, { useState } from 'react';
import { useRaceStore } from '../store/raceStore';
import { Scale, Gavel, ShieldAlert, Award, FileText, CheckCircle2, Sparkles, UserCheck } from 'lucide-react';
import confetti from 'canvas-confetti';

interface StewardVote {
  role: string;
  name: string;
  verdict: 'NO_ACTION' | '5S_PENALTY' | '10S_PENALTY' | 'GRID_DROP_3' | 'REPRIMAND';
}

export const StewardHearingTribunal: React.FC = () => {
  const [selectedIncident, setSelectedIncident] = useState<string>('TURN_4_COLLISION');
  const [penaltyPointsAssigned, setPenaltyPointsAssigned] = useState<number>(2);
  const [verdictAnnounced, setVerdictAnnounced] = useState<boolean>(false);

  const stewardJury: StewardVote[] = [
    { role: 'FIA Chairman Steward', name: 'Garry Connelly', verdict: '5S_PENALTY' },
    { role: 'Driver Steward', name: 'Derek Warwick (Ex-F1)', verdict: '5S_PENALTY' },
    { role: 'National ASN Steward', name: 'Felix Holter', verdict: 'NO_ACTION' },
    { role: 'FIA Permanent Steward', name: 'Mathieu Remmerie', verdict: '5S_PENALTY' },
  ];

  const handleIssueVerdict = () => {
    setVerdictAnnounced(true);
    confetti({ particleCount: 50, spread: 60 });
  };

  return (
    <div className="w-full rounded-2xl bg-slate-950 border border-slate-800 p-4 flex flex-col gap-4 shadow-2xl">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Scale className="w-5 h-5 text-amber-400 animate-pulse" />
          <div className="flex flex-col">
            <span className="font-bold text-white text-sm">
              FIA STEWARD HEARING & DISCIPLINARY APPEAL TRIBUNAL
            </span>
            <span className="text-[11px] font-mono text-slate-400">
              Driver testimony hearings, telemetry apex overlap forensics, 4-steward voting & Superlicense penalty points
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2 bg-slate-900 px-3 py-1.5 rounded-xl border border-slate-800 text-xs font-mono">
          <span className="text-slate-400">Docket: </span>
          <strong className="text-amber-400">DOC 48 • CAR #1 vs CAR #44</strong>
        </div>
      </div>

      {/* Primary Docket Information */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3 font-mono text-xs">
        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] text-slate-400 uppercase">ALLEGED BREACH</span>
          <span className="text-sm font-bold text-white mt-1">Article 33.3 (Causing a Collision)</span>
          <span className="text-[10px] text-slate-400 mt-0.5">Turn 4 Apex Left Front Contact</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] text-slate-400 uppercase">APEX OVERLAP AT APEX</span>
          <div className="flex items-baseline gap-1">
            <span className="text-2xl font-black text-apex-cyan">68.5%</span>
          </div>
          <span className="text-[10px] text-emerald-400 font-bold">Driver 1 was along-side</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] text-slate-400 uppercase">PENALTY POINTS ASSIGNED</span>
          <div className="flex items-baseline gap-1">
            <span className="text-2xl font-black text-rose-400">+{penaltyPointsAssigned} PTS</span>
          </div>
          <span className="text-[10px] text-slate-400">12 Month Validity (Ban at 12)</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] text-slate-400 uppercase">TRIBUNAL STATUS</span>
          <span className={`text-xs font-bold px-2 py-1 rounded mt-1 text-center border ${verdictAnnounced ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40' : 'bg-amber-500/20 text-amber-300 border-amber-500/40 animate-pulse'}`}>
            {verdictAnnounced ? 'OFFICIAL VERDICT PUBLISHED' : 'DELIBERATION IN PROGRESS'}
          </span>
        </div>
      </div>

      {/* Main Grid: Driver Testimonies (Left 6 cols) & Stewards Voting Panel (Right 6 cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 font-mono text-xs">
        {/* Driver Testimonies */}
        <div className="lg:col-span-6 p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col gap-3">
          <span className="font-bold text-slate-300 uppercase border-b border-slate-800 pb-2">
            FORMAL DRIVER & TEAM REPRESENTATIVE TESTIMONIES
          </span>

          <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 flex flex-col gap-1">
            <span className="font-bold text-apex-cyan">Car #1 (Max V. / Red Bull Team Representative):</span>
            <p className="text-slate-300 font-sans text-xs italic">
              "I was fully alongside at the apex braking point. He didn't leave a car width on the exit kerb and squeezed me into the sausage kerb."
            </p>
          </div>

          <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 flex flex-col gap-1">
            <span className="font-bold text-rose-400">Car #44 (Lewis H. / Mercedes Team Representative):</span>
            <p className="text-slate-300 font-sans text-xs italic">
              "He arrived with excessive entry speed and understeered across the racing line. I left sufficient room on the initial turn-in."
            </p>
          </div>
        </div>

        {/* Stewards Voting & Verdict Release */}
        <div className="lg:col-span-6 p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col justify-between gap-3">
          <span className="font-bold text-slate-300 uppercase border-b border-slate-800 pb-2">
            STEWARDS JURY VOTING BREAKDOWN
          </span>

          <div className="flex flex-col gap-2">
            {stewardJury.map((s, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between p-2 rounded-lg bg-slate-950 border border-slate-800 text-[11px]"
              >
                <div className="flex flex-col">
                  <span className="font-bold text-white">{s.name}</span>
                  <span className="text-slate-500">{s.role}</span>
                </div>
                <span className="text-amber-400 font-bold px-2 py-0.5 rounded bg-amber-500/10 border border-amber-500/30">
                  {s.verdict}
                </span>
              </div>
            ))}
          </div>

          <button
            onClick={handleIssueVerdict}
            disabled={verdictAnnounced}
            className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 disabled:bg-slate-800 text-black font-bold transition-all active:scale-95 shadow-md shadow-amber-500/20"
          >
            <Gavel className="w-4 h-4" />
            <span>{verdictAnnounced ? 'OFFICIAL FIA VERDICT RATIFIED' : 'ISSUE OFFICIAL FIA PENALTY VERDICT'}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
