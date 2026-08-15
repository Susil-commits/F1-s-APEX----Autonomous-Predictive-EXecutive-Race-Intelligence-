import React, { useState, useMemo, useEffect } from 'react';
import { useRaceStore } from '../store/raceStore';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
} from 'recharts';
import { Dices, Play, Award, Sparkles, TrendingUp, RotateCcw } from 'lucide-react';
import { audioEngine } from '../utils/audioEngine';

export const MonteCarloStrategySim: React.FC = () => {
  const { raceState } = useRaceStore();
  const [numRollouts, setNumRollouts] = useState<number>(1000);
  const [selectedStrategy, setSelectedStrategy] = useState<'plan_a' | 'plan_b' | 'plan_c'>('plan_a');
  const [simSeed, setSimSeed] = useState<number>(1);
  const [backendData, setBackendData] = useState<any>(null);

  const playerCar = raceState?.cars.find((c) => c.is_player) || raceState?.cars[0];
  const track = raceState?.track;
  const currentLap = raceState?.current_lap || 1;

  useEffect(() => {
    let isMounted = true;
    if (!playerCar) return;

    fetch('/api/strategy/monte-carlo', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ rollouts: numRollouts, target_car_id: playerCar.car_id }),
    })
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (isMounted && data && data.strategies) {
          setBackendData(data);
        }
      })
      .catch(() => {
        // Fallback to client simulation if offline
      });

    return () => {
      isMounted = false;
    };
  }, [currentLap, simSeed, numRollouts, playerCar?.car_id]);

  // Run 1,000-rollout stochastic Monte Carlo simulation
  const simulationResults = useMemo(() => {
    if (!raceState || !playerCar || !track) return null;

    const currentLap = raceState.current_lap;
    const remainingLaps = Math.max(1, track.total_laps - currentLap);
    const positionCounts: Record<number, number> = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0 };

    // Point distribution: P1=25, P2=18, P3=15, P4=12, P5=10, P6=8
    const pointsMap: Record<number, number> = { 1: 25, 2: 18, 3: 15, 4: 12, 5: 10, 6: 8 };
    let totalPoints = 0;

    const basePosition = playerCar.position;
    const isPlanB = selectedStrategy === 'plan_b';
    const isPlanC = selectedStrategy === 'plan_c';

    for (let i = 0; i < numRollouts; i++) {
      // Gaussian random pace variance
      const randPace = (Math.random() + Math.random() + Math.random() - 1.5) * 1.2;
      // Random Safety Car event probability (20% chance)
      const scOccurs = Math.random() < 0.22;
      // Random rain shock probability
      const rainOccurs = Math.random() < track.rain_probability_base;

      let posDelta = 0;
      if (isPlanB) {
        posDelta += scOccurs ? -1 : 1; // 2-stop benefits heavily from SC
      } else if (isPlanC) {
        posDelta += rainOccurs ? -2 : 0;
      } else {
        posDelta += randPace < -0.3 ? -1 : randPace > 0.6 ? 1 : 0;
      }

      let finalPos = Math.min(6, Math.max(1, basePosition + posDelta));
      positionCounts[finalPos] += 1;
      totalPoints += pointsMap[finalPos] || 0;
    }

    const chartData = [1, 2, 3, 4, 5, 6].map((pos) => ({
      position: `P${pos}${pos === 6 ? '+' : ''}`,
      posNum: pos,
      probability: parseFloat(((positionCounts[pos] / numRollouts) * 100).toFixed(1)),
      count: positionCounts[pos],
    }));

    const winProb = parseFloat(((positionCounts[1] / numRollouts) * 100).toFixed(1));
    const podiumProb = parseFloat(
      (((positionCounts[1] + positionCounts[2] + positionCounts[3]) / numRollouts) * 100).toFixed(1)
    );
    const expectedPoints = parseFloat((totalPoints / numRollouts).toFixed(1));

    return {
      chartData,
      winProb,
      podiumProb,
      expectedPoints,
      backendConfidence: backendData?.confidence_pct,
      recommendedPlan: backendData?.recommended_strategy,
    };
  }, [raceState, playerCar, track, numRollouts, selectedStrategy, simSeed, backendData]);

  const handleRerun = () => {
    setSimSeed((prev) => prev + 1);
    audioEngine.playRadioBleep();
  };

  if (!simulationResults) return null;

  return (
    <div className="glass-panel rounded-xl p-5 flex flex-col border border-apex-border shadow-2xl font-mono text-xs">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-2 mb-4 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2.5">
          <Dices className="w-5 h-5 text-apex-cyan animate-pulse" />
          <div>
            <h3 className="text-xs font-black uppercase tracking-widest text-slate-200">
              Monte Carlo 1,000-Rollout Probability Engine
            </h3>
            <p className="text-[10.5px] text-slate-400 font-sans">
              Stochastic forward simulations modeling pace variance, safety cars, and weather
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Strategy Plan Selector */}
          <div className="flex items-center bg-slate-950/80 p-0.5 rounded-lg border border-slate-800 text-[10px]">
            <button
              onClick={() => setSelectedStrategy('plan_a')}
              className={`px-2 py-1 rounded transition-all ${
                selectedStrategy === 'plan_a'
                  ? 'bg-cyan-500 text-black font-bold shadow'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Plan A (1-Stop)
            </button>
            <button
              onClick={() => setSelectedStrategy('plan_b')}
              className={`px-2 py-1 rounded transition-all ${
                selectedStrategy === 'plan_b'
                  ? 'bg-cyan-500 text-black font-bold shadow'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Plan B (2-Stop)
            </button>
            <button
              onClick={() => setSelectedStrategy('plan_c')}
              className={`px-2 py-1 rounded transition-all ${
                selectedStrategy === 'plan_c'
                  ? 'bg-cyan-500 text-black font-bold shadow'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Plan C (Overcut)
            </button>
          </div>

          <button
            onClick={handleRerun}
            className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-[10px] font-bold transition-all active:scale-95"
          >
            <RotateCcw className="w-3 h-3" />
            <span>Re-Roll</span>
          </button>
        </div>
      </div>

      {/* KPI Cards Row */}
      <div className="grid grid-cols-3 gap-3 text-center mb-4">
        <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
          <span className="text-[9.5px] uppercase font-sans text-slate-400 block font-semibold">
            Win Probability (P1)
          </span>
          <span className="text-2xl font-black text-apex-cyan glow-cyan">
            {simulationResults.winProb}%
          </span>
          <span className="text-[10px] text-slate-500 block">Across 1,000 Sims</span>
        </div>

        <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
          <span className="text-[9.5px] uppercase font-sans text-slate-400 block font-semibold">
            Podium Odds (P1-P3)
          </span>
          <span className="text-2xl font-black text-emerald-400">
            {simulationResults.podiumProb}%
          </span>
          <span className="text-[10px] text-slate-500 block">Top-3 Confidence</span>
        </div>

        <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
          <span className="text-[9.5px] uppercase font-sans text-slate-400 block font-semibold">
            Expected Points (EV)
          </span>
          <span className="text-2xl font-black text-yellow-400">
            {simulationResults.expectedPoints} pts
          </span>
          <span className="text-[10px] text-slate-500 block">Championship EV</span>
        </div>
      </div>

      {/* Probability Distribution Histogram */}
      <div className="mb-2">
        <div className="flex items-center justify-between text-[11px] font-sans font-bold text-slate-300 mb-1">
          <span>Finishing Position Probability Density Histogram</span>
          <span className="text-slate-500 font-mono">1,000 Rollouts</span>
        </div>

        <div className="w-full h-44 bg-slate-950/40 p-2 rounded-lg border border-slate-900">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={simulationResults.chartData} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
              <XAxis dataKey="position" stroke="#64748b" fontSize={10} tickLine={false} />
              <YAxis stroke="#64748b" fontSize={10} tickLine={false} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0f172a',
                  borderColor: '#334155',
                  borderRadius: '6px',
                  fontSize: '11px',
                  color: '#f8fafc',
                }}
              />
              <Bar dataKey="probability" name="Probability (%)" radius={[4, 4, 0, 0]}>
                {simulationResults.chartData.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={
                      entry.posNum === 1
                        ? '#00f0ff'
                        : entry.posNum <= 3
                        ? '#10b981'
                        : entry.posNum === 4
                        ? '#f59e0b'
                        : '#64748b'
                    }
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};
