import React, { useState, useEffect } from 'react';
import { useRaceStore } from '../store/raceStore';
import { MCTSNodeData, MCTSSummary } from '../types/race';
import { GitBranch, Play, RefreshCw, Trophy, Activity, Zap, CheckCircle2, ChevronRight } from 'lucide-react';

export const MCTSVisualizer: React.FC = () => {
  const { raceState } = useRaceStore();
  const [treeData, setTreeData] = useState<MCTSNodeData | null>(null);
  const [summary, setSummary] = useState<MCTSSummary | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [simCount, setSimCount] = useState<number>(150);
  const [selectedNode, setSelectedNode] = useState<MCTSNodeData | null>(null);

  const fetchMCTSTree = async () => {
    setLoading(true);
    try {
      const res = await fetch(`http://localhost:8000/api/strategy/mcts-tree?simulations=${simCount}`);
      if (res.ok) {
        const data = await res.json();
        setTreeData(data.tree);
        setSummary(data.summary);
        setSelectedNode(data.tree);
      }
    } catch (err) {
      console.warn('[APEX MCTS] Could not fetch MCTS tree:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMCTSTree();
  }, [raceState?.current_lap]);

  const renderTreeNode = (node: MCTSNodeData, depth: number = 0) => {
    const isSelected = selectedNode?.node_id === node.node_id;

    return (
      <div key={node.node_id} className="flex flex-col items-start gap-2 my-1">
        <div
          onClick={() => setSelectedNode(node)}
          className={`flex items-center gap-3 px-3.5 py-2 rounded-xl border text-xs font-mono transition-all cursor-pointer select-none ${
            node.is_optimal_path
              ? 'bg-emerald-950/70 border-emerald-500/80 text-emerald-200 shadow-md shadow-emerald-950/50'
              : 'bg-slate-900/80 border-slate-800 text-slate-300 hover:border-slate-700'
          } ${isSelected ? 'ring-2 ring-apex-cyan' : ''}`}
        >
          {node.is_optimal_path && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />}

          <div className="flex flex-col">
            <div className="flex items-center gap-2">
              <span className="font-bold text-white uppercase">{node.action_name.replace('_', ' ')}</span>
              <span className="px-1.5 py-0.2 rounded text-[10px] bg-slate-800 text-slate-400">
                LAP {node.lap}
              </span>
              <span
                className={`px-1.5 py-0.2 rounded text-[10px] font-bold ${
                  node.compound === 'SOFT'
                    ? 'bg-rose-500/20 text-rose-300'
                    : node.compound === 'MEDIUM'
                    ? 'bg-amber-500/20 text-amber-300'
                    : 'bg-slate-700 text-slate-200'
                }`}
              >
                {node.compound}
              </span>
            </div>

            <div className="flex items-center gap-3 text-[11px] text-slate-400 mt-1">
              <span>
                Visits: <strong className="text-slate-200">{node.visits}</strong>
              </span>
              <span>
                Win: <strong className="text-apex-cyan">{node.win_probability_pct}%</strong>
              </span>
              <span>
                Wear: <strong className="text-amber-400">{node.tyre_wear_pct}%</strong>
              </span>
              <span>
                Pos: <strong className="text-white">P{node.projected_position}</strong>
              </span>
            </div>
          </div>
        </div>

        {/* Child branches */}
        {node.children && node.children.length > 0 && (
          <div className="flex flex-col pl-6 border-l-2 border-slate-800/80 gap-2 mt-1">
            {node.children.map((child) => renderTreeNode(child, depth + 1))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="w-full rounded-2xl bg-slate-950 border border-slate-800 p-4 flex flex-col gap-4 shadow-2xl">
      {/* Header & Controls */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <GitBranch className="w-5 h-5 text-emerald-400 animate-pulse" />
          <div className="flex flex-col">
            <span className="font-bold text-white text-sm">ALPHAZERO-STYLE MONTE CARLO TREE SEARCH (MCTS)</span>
            <span className="text-[11px] font-mono text-slate-400">
              Deep stochastic tree search under safety car, weather & undercut uncertainty
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 bg-slate-900 px-2 py-1 rounded-lg border border-slate-800 text-xs font-mono">
            <span className="text-slate-400">Rollouts:</span>
            <select
              value={simCount}
              onChange={(e) => setSimCount(Number(e.target.value))}
              className="bg-transparent text-white font-bold focus:outline-none"
            >
              <option value={80}>80 Sim</option>
              <option value={150}>150 Sim</option>
              <option value={250}>250 Sim</option>
            </select>
          </div>

          <button
            onClick={fetchMCTSTree}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-black font-bold text-xs transition-all active:scale-95 shadow-sm shadow-emerald-500/30"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>{loading ? 'Simulating...' : 'Run MCTS Search'}</span>
          </button>
        </div>
      </div>

      {/* Summary KPI Cards */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col gap-1">
            <span className="text-[10px] font-mono text-slate-400 uppercase">RECOMMENDED ACTION</span>
            <span className="text-base font-black font-mono text-emerald-400">
              {summary.recommended_action.replace('_', ' ')}
            </span>
          </div>

          <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col gap-1">
            <span className="text-[10px] font-mono text-slate-400 uppercase">PROJECTED WIN RATE</span>
            <span className="text-base font-black font-mono text-apex-cyan">
              {summary.win_probability_pct}%
            </span>
          </div>

          <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col gap-1">
            <span className="text-[10px] font-mono text-slate-400 uppercase">SEARCH DEPTH</span>
            <span className="text-base font-black font-mono text-purple-400">
              {summary.optimal_path_depth} LAPS AHEAD
            </span>
          </div>

          <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col gap-1">
            <span className="text-[10px] font-mono text-slate-400 uppercase">EXPLORED NODES</span>
            <span className="text-base font-black font-mono text-amber-400">
              {summary.simulations_executed} ROLLOUTS
            </span>
          </div>
        </div>
      )}

      {/* Tree Visualization & Node Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Tree Branch View */}
        <div className="lg:col-span-8 p-4 rounded-xl bg-slate-900/50 border border-slate-800/80 max-h-[460px] overflow-y-auto">
          <span className="text-xs font-mono text-slate-400 font-bold uppercase mb-2 block">
            POLICY SEARCH TREE (OPTIMAL PATH HIGHLIGHTED)
          </span>
          {treeData ? (
            renderTreeNode(treeData)
          ) : (
            <div className="text-center py-12 text-slate-500 font-mono text-xs">
              No MCTS Tree data available. Click 'Run MCTS Search' to explore future branches.
            </div>
          )}
        </div>

        {/* Selected Node Inspector */}
        <div className="lg:col-span-4 p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col gap-3">
          <span className="text-xs font-mono text-apex-cyan font-bold uppercase border-b border-slate-800 pb-1.5">
            BRANCH NODE INSPECTOR
          </span>

          {selectedNode ? (
            <div className="flex flex-col gap-2 text-xs font-mono">
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Action:</span>
                <span className="font-bold text-white">{selectedNode.action_name}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Lap:</span>
                <span className="font-bold text-white">{selectedNode.lap}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Visit Count (N):</span>
                <span className="font-bold text-apex-cyan">{selectedNode.visits}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Value Q(s, a):</span>
                <span className="font-bold text-emerald-400">{selectedNode.value}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Prior P(s, a):</span>
                <span className="font-bold text-purple-400">{selectedNode.prior}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Tyre Wear:</span>
                <span className="font-bold text-amber-400">{selectedNode.tyre_wear_pct}%</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Gap to Leader:</span>
                <span className="font-bold text-white">+{selectedNode.gap_to_leader_s}s</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-400">Projected Position:</span>
                <span className="font-bold text-emerald-400">P{selectedNode.projected_position}</span>
              </div>
            </div>
          ) : (
            <span className="text-slate-500 text-xs font-mono">Select a branch node to inspect properties.</span>
          )}
        </div>
      </div>
    </div>
  );
};
