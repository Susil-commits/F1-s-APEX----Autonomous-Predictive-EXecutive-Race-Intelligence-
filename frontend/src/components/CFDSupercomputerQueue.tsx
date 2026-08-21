import React, { useState } from 'react';
import { useRaceStore } from '../store/raceStore';
import { Cpu, Wind, Activity, Zap, CheckCircle2, Play, Sparkles } from 'lucide-react';
import confetti from 'canvas-confetti';

interface CFDJob {
  id: string;
  name: string;
  meshCellsMillion: number;
  computeHours: number;
  teraflopsRequired: number;
  progressPct: number;
  status: 'RUNNING' | 'QUEUED' | 'COMPLETED';
  predictedDownforceGainPts: number;
}

const INITIAL_JOBS: CFDJob[] = [
  {
    id: 'job-1',
    name: 'Underfloor Venturi Inwash Strakes v4.2',
    meshCellsMillion: 120,
    computeHours: 48,
    teraflopsRequired: 35,
    progressPct: 84,
    status: 'RUNNING',
    predictedDownforceGainPts: 14.2,
  },
  {
    id: 'job-2',
    name: 'Rear Beam Wing High-Camber Cascade',
    meshCellsMillion: 85,
    computeHours: 32,
    teraflopsRequired: 22,
    progressPct: 0,
    status: 'QUEUED',
    predictedDownforceGainPts: 8.5,
  },
  {
    id: 'job-3',
    name: 'Front Wing Endplate Outwash Vortex Generator',
    meshCellsMillion: 150,
    computeHours: 64,
    teraflopsRequired: 45,
    progressPct: 0,
    status: 'QUEUED',
    predictedDownforceGainPts: 18.0,
  },
];

export const CFDSupercomputerQueue: React.FC = () => {
  const [jobs, setJobs] = useState<CFDJob[]>(INITIAL_JOBS);
  const [usedTeraflops, setUsedTeraflops] = useState<number>(102);

  const totalAtrTeraflopsCap = 200;
  const remainingTeraflops = totalAtrTeraflopsCap - usedTeraflops;

  const handleDispatchJob = () => {
    const newJob: CFDJob = {
      id: `job-${jobs.length + 1}`,
      name: `Sidepod Undercut Channel Refinement v${jobs.length + 1}`,
      meshCellsMillion: 95,
      computeHours: 36,
      teraflopsRequired: 25,
      progressPct: 12,
      status: 'RUNNING',
      predictedDownforceGainPts: 10.5,
    };
    setJobs([newJob, ...jobs]);
    setUsedTeraflops((prev) => Math.min(totalAtrTeraflopsCap, prev + 25));
    confetti({ particleCount: 40, spread: 55 });
  };

  return (
    <div className="w-full rounded-2xl bg-slate-950 border border-slate-800 p-4 flex flex-col gap-4 shadow-2xl">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Cpu className="w-5 h-5 text-indigo-400 animate-pulse" />
          <div className="flex flex-col">
            <span className="font-bold text-white text-sm">
              PADDOCK FACTORY SUPERCOMPUTER CFD CLOUD & ATR ALLOCATOR
            </span>
            <span className="text-[11px] font-mono text-slate-400">
              FIA Article 7 Aerodynamic Testing Restrictions (ATR), TeraFLOPs compute quotas & 100M+ cell mesh queue
            </span>
          </div>
        </div>

        <button
          onClick={handleDispatchJob}
          disabled={remainingTeraflops < 25}
          className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white font-mono text-xs font-bold transition-all active:scale-95 shadow-md shadow-indigo-500/20"
        >
          <Sparkles className="w-4 h-4" />
          <span>Dispatch CFD Mesh Job</span>
        </button>
      </div>

      {/* Primary ATR Quota KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 font-mono">
        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] text-slate-400 uppercase">COMPUTE BUDGET USED</span>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-black text-indigo-400">{usedTeraflops}</span>
            <span className="text-xs text-slate-400">/ 200 TFLOPS</span>
          </div>
          <span className="text-[10px] text-slate-400">FIA ATR Period 4</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] text-slate-400 uppercase">REMAINING QUOTA</span>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-black text-emerald-400">{remainingTeraflops}</span>
            <span className="text-xs text-slate-400">TFLOPS</span>
          </div>
          <span className="text-[10px] text-slate-400">Headroom for Upgrades</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] text-slate-400 uppercase">WIND TUNNEL OCCUPANCY</span>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-black text-amber-400">184</span>
            <span className="text-xs text-slate-400">/ 280 HOURS</span>
          </div>
          <span className="text-[10px] text-slate-400">60% Scale Model Test</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] text-slate-400 uppercase">ACTIVE MESH RUNS</span>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-black text-apex-cyan">
              {jobs.filter((j) => j.status === 'RUNNING').length}
            </span>
            <span className="text-xs text-slate-400">SOLVERS</span>
          </div>
          <span className="text-[10px] text-slate-400">Navier-Stokes Supercluster</span>
        </div>
      </div>

      {/* Active CFD Simulation Jobs List */}
      <div className="flex flex-col gap-2.5 font-mono text-xs">
        <span className="font-bold text-slate-300 uppercase border-b border-slate-800 pb-1.5">
          ACTIVE AERODYNAMIC GEOMETRY COMPUTE QUEUE
        </span>

        {jobs.map((job) => (
          <div
            key={job.id}
            className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col gap-2"
          >
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <span className="text-indigo-400 font-bold">[{job.id.toUpperCase()}]</span>
                <span className="text-white font-bold">{job.name}</span>
                <span className="text-[10px] text-slate-400">({job.meshCellsMillion}M Cells)</span>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-emerald-400 font-bold">+{job.predictedDownforceGainPts} pts Downforce</span>
                <span
                  className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                    job.status === 'RUNNING'
                      ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40 animate-pulse'
                      : 'bg-slate-800 text-slate-400 border-slate-700'
                  }`}
                >
                  {job.status}
                </span>
              </div>
            </div>

            {/* Progress Bar */}
            <div className="w-full h-2 bg-slate-950 rounded-full overflow-hidden border border-slate-800">
              <div
                style={{ width: `${job.progressPct}%` }}
                className="h-full bg-gradient-to-r from-indigo-500 to-cyan-400 transition-all duration-300"
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
