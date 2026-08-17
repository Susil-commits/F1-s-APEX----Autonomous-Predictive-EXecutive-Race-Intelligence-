import React, { useState } from 'react';
import { Trophy, Play, Award, Zap, Users, BarChart3 } from 'lucide-react';

export const ChampionshipTournamentView: React.FC = () => {
  const [racesCount, setRacesCount] = useState<number>(10);
  const [tournamentData, setTournamentData] = useState<any>(null);
  const [running, setRunning] = useState<boolean>(false);

  const handleRunChampionship = () => {
    setRunning(true);
    fetch(`/api/championship/run?races=${racesCount}`)
      .then((res) => res.json())
      .then((data) => {
        setTournamentData(data);
        setRunning(false);
      })
      .catch(() => setRunning(false));
  };

  return (
    <div className="flex flex-col gap-4 p-2 font-mono">
      <div className="flex items-center justify-between bg-slate-900/90 p-4 rounded-xl border border-slate-800">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-amber-500/20 text-amber-400 border border-amber-500/30">
            <Trophy className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-base font-bold text-white font-sans">Multi-Agent AI-vs-AI Championship Tournament</h2>
            <p className="text-xs text-slate-400">100+ Race season simulation across 5 distinct AI strategy archetypes</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-xs">
            <span className="text-slate-400">Races:</span>
            <select
              value={racesCount}
              onChange={(e) => setRacesCount(Number(e.target.value))}
              className="bg-slate-950 text-slate-200 border border-slate-800 rounded px-2 py-1 focus:outline-none"
            >
              <option value={5}>5 Races (Fast Sprint)</option>
              <option value={10}>10 Races (Half Season)</option>
              <option value={24}>24 Races (Full Season)</option>
              <option value={50}>50 Races (Grand Championship)</option>
            </select>
          </div>
          <button
            onClick={handleRunChampionship}
            disabled={running}
            className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-black font-bold text-xs transition-all shadow-md shadow-amber-500/20 disabled:opacity-50"
          >
            <Play className={`w-3.5 h-3.5 ${running ? 'animate-spin' : ''}`} />
            <span>{running ? 'Simulating Season...' : 'Launch Championship'}</span>
          </button>
        </div>
      </div>

      {tournamentData && (
        <div className="flex flex-col gap-4">
          <div className="bg-slate-950/90 p-4 rounded-xl border border-slate-800 flex items-center justify-between">
            <div>
              <span className="text-xs text-slate-400">WORLD CONSTRUCTORS CHAMPION</span>
              <p className="text-xl font-black text-amber-400 font-sans">{tournamentData.champion}</p>
            </div>
            <div className="text-right">
              <span className="text-xs text-slate-400">Total Races Completed</span>
              <p className="text-xl font-bold text-white font-sans">{tournamentData.total_races}</p>
            </div>
          </div>

          <div className="bg-slate-950/90 p-4 rounded-xl border border-slate-800 flex flex-col gap-3">
            <h3 className="text-xs font-bold text-slate-300 font-sans">Official AI Championship Standings</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400">
                    <th className="p-2.5">POS</th>
                    <th className="p-2.5">AI TEAM / ARCHETYPE</th>
                    <th className="p-2.5 text-center">POINTS</th>
                    <th className="p-2.5 text-center">WINS</th>
                    <th className="p-2.5 text-center">PODIUMS</th>
                    <th className="p-2.5 text-center">TOP 5</th>
                    <th className="p-2.5 text-center">AVG FINISH</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/50">
                  {tournamentData.leaderboard?.map((team: any, idx: number) => (
                    <tr key={idx} className={`hover:bg-slate-900/40 ${idx === 0 ? 'bg-amber-950/20' : ''}`}>
                      <td className="p-2.5 font-bold text-cyan-400">P{idx + 1}</td>
                      <td className="p-2.5">
                        <span className="font-bold text-white font-sans block">{team.team_name}</span>
                        <span className="text-[10px] text-slate-500">{team.archetype}</span>
                      </td>
                      <td className="p-2.5 text-center font-black text-amber-400 text-sm">{team.points}</td>
                      <td className="p-2.5 text-center font-bold text-emerald-400">{team.wins}</td>
                      <td className="p-2.5 text-center text-slate-300">{team.podiums}</td>
                      <td className="p-2.5 text-center text-slate-400">{team.top5s}</td>
                      <td className="p-2.5 text-center font-mono text-cyan-300">P{team.avg_finish.toFixed(1)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
