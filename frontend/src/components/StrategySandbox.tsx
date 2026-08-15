import React, { useState, useMemo } from 'react';
import { useRaceStore } from '../store/raceStore';
import { Sliders, Play, RotateCcw, Award, CheckCircle, Sparkles, AlertCircle } from 'lucide-react';
import { TyreCompound, DrivingMode, StrategyAction } from '../types/race';

export const StrategySandbox: React.FC = () => {
  const { raceState } = useRaceStore();

  const [boxLap, setBoxLap] = useState<number>(20);
  const [compound, setCompound] = useState<TyreCompound>('MEDIUM');
  const [mode, setMode] = useState<DrivingMode>('NORMAL');
  const [scenarioSC, setScenarioSC] = useState<'NONE' | 'VSC' | 'SAFETY_CAR'>('NONE');
  const [scenarioRain, setScenarioRain] = useState<boolean>(false);

  const playerCar = raceState?.cars.find((c) => c.is_player) || raceState?.cars[0];
  const track = raceState?.track;

  // Compute sandbox counterfactual outcome
  const simulationOutcome = useMemo(() => {
    if (!raceState || !playerCar || !track) return null;

    const currentLap = raceState.current_lap;
    const currentWear = playerCar.tyre_wear_pct;
    const remainingLaps = Math.max(1, track.total_laps - currentLap);

    // Calculate pit delta advantage
    let pitCost = track.pit_lane_delta_s;
    if (scenarioSC === 'SAFETY_CAR') pitCost -= track.sc_pit_advantage_s;
    if (scenarioSC === 'VSC') pitCost -= track.vsc_pit_advantage_s;

    // Projected wear at box lap
    const lapsUntilBox = Math.max(0, boxLap - currentLap);
    const wearAtBox = Math.min(100, currentWear + lapsUntilBox * 2.8);
    const cliffPenalty = wearAtBox >= 78 ? (wearAtBox - 78) * 0.8 : 0;

    // Stint 2 projected degradation
    const stint2Laps = Math.max(0, track.total_laps - boxLap);
    const stint2WearRate = compound === 'SOFT' ? 3.8 : compound === 'MEDIUM' ? 2.6 : 1.8;
    const stint2Wear = Math.min(100, stint2Laps * stint2WearRate * track.tyre_wear_factor);

    // Weather impact
    let rainLoss = 0;
    if (scenarioRain && compound !== 'INTERMEDIATE' && compound !== 'WET') {
      rainLoss = 8.5 * Math.min(5, remainingLaps);
    }

    // Net delta vs maintaining current baseline
    const netTimeDelta = parseFloat(
      (pitCost + cliffPenalty + rainLoss - (lapsUntilBox > 0 ? 0 : 2.5)).toFixed(1)
    );
    const projectedPos = Math.min(
      10,
      Math.max(1, playerCar.position + (netTimeDelta > 15 ? 3 : netTimeDelta > 5 ? 1 : 0))
    );

    return {
      wearAtBox: parseFloat(wearAtBox.toFixed(1)),
      stint2Wear: parseFloat(stint2Wear.toFixed(1)),
      pitCost: parseFloat(pitCost.toFixed(1)),
      netTimeDelta,
      projectedPos,
      cliffRisk: wearAtBox >= 78 ? 'CRITICAL' : wearAtBox >= 60 ? 'HIGH' : 'LOW',
    };
  }, [raceState, playerCar, track, boxLap, compound, mode, scenarioSC, scenarioRain]);

  if (!raceState || !playerCar || !track) return null;

  return (
    <div className="flex flex-col gap-4 w-full">
      {/* Sandbox Header */}
      <div className="glass-panel rounded-xl p-4 flex items-center justify-between border border-apex-border shadow-2xl">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center font-bold text-white shadow-lg shadow-purple-500/20">
            <Sliders className="w-4 h-4 text-white stroke-[2.5]" />
          </div>
          <div>
            <h2 className="text-sm font-black uppercase tracking-wider text-white">
              Tactical Strategy Sandbox & What-If Studio
            </h2>
            <p className="text-xs text-slate-400">
              Model hypothetical pit windows, weather transitions, and safety car scenarios in real time
            </p>
          </div>
        </div>

        <span className="text-[10px] font-mono font-bold px-2.5 py-1 rounded bg-purple-950/60 text-purple-300 border border-purple-800/60">
          Digital Twin Forward Sandbox
        </span>
      </div>

      {/* Main Grid: Controls on left, Live Outcomes on right */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Left Column: Interactive Scenario Controls (5 cols) */}
        <div className="lg:col-span-5 glass-panel rounded-xl p-5 flex flex-col gap-4 border border-apex-border shadow-2xl">
          <h3 className="text-xs font-black uppercase tracking-wider text-slate-200 border-b border-slate-800 pb-2">
            Scenario Parameters
          </h3>

          {/* Target Pit Lap Slider */}
          <div>
            <div className="flex items-center justify-between text-xs font-mono mb-1.5">
              <span className="text-slate-300 font-sans font-semibold">Planned Pit Stop Lap:</span>
              <span className="font-bold text-apex-cyan text-sm">Lap {boxLap}</span>
            </div>
            <input
              type="range"
              min={Math.max(1, raceState.current_lap)}
              max={track.total_laps}
              value={boxLap}
              onChange={(e) => setBoxLap(Number(e.target.value))}
              className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-400"
            />
            <div className="flex justify-between text-[10px] font-mono text-slate-500 mt-1">
              <span>Current (Lap {raceState.current_lap})</span>
              <span>Finish (Lap {track.total_laps})</span>
            </div>
          </div>

          {/* Compound Selection */}
          <div>
            <label className="text-xs font-sans font-semibold text-slate-300 block mb-1.5">
              Tyre Compound to Fit:
            </label>
            <div className="grid grid-cols-3 gap-2 font-mono text-xs">
              {(['SOFT', 'MEDIUM', 'HARD', 'INTERMEDIATE', 'WET'] as TyreCompound[]).map((c) => (
                <button
                  key={c}
                  onClick={() => setCompound(c)}
                  className={`py-1.5 px-2 rounded-lg border text-center font-bold transition-all ${
                    compound === c
                      ? 'bg-cyan-500/20 text-apex-cyan border-cyan-400 shadow-sm shadow-cyan-500/20'
                      : 'bg-slate-900/80 text-slate-400 border-slate-800 hover:text-slate-200'
                  }`}
                >
                  {c}
                </button>
              ))}
            </div>
          </div>

          {/* Driving Mode */}
          <div>
            <label className="text-xs font-sans font-semibold text-slate-300 block mb-1.5">
              Stint Driving Aggression:
            </label>
            <div className="grid grid-cols-3 gap-2 font-mono text-xs">
              {(['PUSH', 'NORMAL', 'CONSERVE'] as DrivingMode[]).map((m) => (
                <button
                  key={m}
                  onClick={() => setMode(m)}
                  className={`py-1.5 px-2 rounded-lg border text-center font-bold transition-all ${
                    mode === m
                      ? 'bg-amber-500/20 text-amber-300 border-amber-400'
                      : 'bg-slate-900/80 text-slate-400 border-slate-800 hover:text-slate-200'
                  }`}
                >
                  {m}
                </button>
              ))}
            </div>
          </div>

          {/* Shock Injectors */}
          <div className="pt-2 border-t border-slate-800/80">
            <span className="text-[10px] uppercase font-mono text-slate-500 block mb-2 font-bold">
              Simulated Incident Shocks
            </span>
            <div className="space-y-2 text-xs">
              {/* Safety Car Toggle */}
              <div className="flex items-center justify-between p-2 rounded bg-slate-900/60 border border-slate-800">
                <span className="text-slate-300 font-medium">Safety Car Phase:</span>
                <select
                  value={scenarioSC}
                  onChange={(e) => setScenarioSC(e.target.value as any)}
                  className="bg-slate-950 border border-slate-700 rounded px-2 py-1 text-xs text-slate-200 font-mono"
                >
                  <option value="NONE">None (Green Flag)</option>
                  <option value="VSC">Virtual Safety Car (VSC)</option>
                  <option value="SAFETY_CAR">Full Safety Car</option>
                </select>
              </div>

              {/* Rain Shock */}
              <div className="flex items-center justify-between p-2 rounded bg-slate-900/60 border border-slate-800">
                <span className="text-slate-300 font-medium">Sudden Heavy Rain:</span>
                <button
                  onClick={() => setScenarioRain(!scenarioRain)}
                  className={`px-3 py-1 rounded text-xs font-mono font-bold transition-all ${
                    scenarioRain
                      ? 'bg-cyan-500 text-black shadow'
                      : 'bg-slate-800 text-slate-400 hover:text-white'
                  }`}
                >
                  {scenarioRain ? 'ON (WET TRACK)' : 'OFF (DRY)'}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Projected Simulated Results (7 cols) */}
        <div className="lg:col-span-7 glass-panel rounded-xl p-5 flex flex-col justify-between border border-apex-border shadow-2xl">
          <div>
            <div className="flex items-center justify-between border-b border-slate-800 pb-2 mb-4">
              <h3 className="text-xs font-black uppercase tracking-wider text-slate-200">
                Forward Digital Twin Projection
              </h3>
              <span className="text-[10px] font-mono text-emerald-400 font-bold flex items-center gap-1">
                <Sparkles className="w-3 h-3" /> Live Forward Model
              </span>
            </div>

            {simulationOutcome && (
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 font-mono text-center mb-4">
                <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800">
                  <span className="text-[9.5px] uppercase text-slate-400 font-sans block font-semibold">
                    Projected Finish Pos
                  </span>
                  <span className="text-2xl font-black text-apex-cyan">
                    P{simulationOutcome.projectedPos}
                  </span>
                  <span className="text-[10px] text-slate-500 block">
                    (Current: P{playerCar.position})
                  </span>
                </div>

                <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800">
                  <span className="text-[9.5px] uppercase text-slate-400 font-sans block font-semibold">
                    Tyre Wear at Box Lap
                  </span>
                  <span
                    className={`text-2xl font-black ${
                      simulationOutcome.wearAtBox >= 78 ? 'text-rose-400 glow-red' : 'text-amber-400'
                    }`}
                  >
                    {simulationOutcome.wearAtBox}%
                  </span>
                  <span className="text-[10px] text-slate-500 block">
                    {simulationOutcome.cliffRisk} RISK
                  </span>
                </div>

                <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800">
                  <span className="text-[9.5px] uppercase text-slate-400 font-sans block font-semibold">
                    Stint 2 Final Wear
                  </span>
                  <span className="text-2xl font-black text-emerald-400">
                    {simulationOutcome.stint2Wear}%
                  </span>
                  <span className="text-[10px] text-slate-500 block">on {compound}s</span>
                </div>
              </div>
            )}

            {/* Strategic Rationale & Evaluation */}
            <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800/80 text-xs font-sans space-y-2">
              <span className="text-[10px] uppercase font-mono font-bold text-slate-400 block">
                AI Strategic Evaluation
              </span>
              {simulationOutcome && simulationOutcome.wearAtBox >= 78 ? (
                <div className="flex items-start gap-2 text-rose-300">
                  <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                  <p>
                    ⚠️ <strong>Warning:</strong> Delaying pit stop to Lap {boxLap} exceeds tyre cliff
                    threshold (78%), costing ~2.8s per lap in severe lap pace degradation.
                  </p>
                </div>
              ) : (
                <div className="flex items-start gap-2 text-emerald-300">
                  <CheckCircle className="w-4 h-4 shrink-0 mt-0.5" />
                  <p>
                    ✅ <strong>Viable Window:</strong> Pitting on Lap {boxLap} for {compound} tyres keeps
                    degradation within safety limits and maintains optimal pit window re-emergence.
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Reset Sandbox */}
          <div className="pt-4 border-t border-slate-800 flex items-center justify-between text-xs">
            <span className="text-slate-400">Want to reset scenario to current race state?</span>
            <button
              onClick={() => {
                setBoxLap(raceState.current_lap + 2);
                setCompound('MEDIUM');
                setMode('NORMAL');
                setScenarioSC('NONE');
                setScenarioRain(false);
              }}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-all font-semibold"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Reset Sandbox</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
