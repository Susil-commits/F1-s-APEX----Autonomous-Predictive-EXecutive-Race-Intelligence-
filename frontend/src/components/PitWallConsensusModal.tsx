import React, { useState, useEffect } from 'react';
import {
  Users,
  X,
  Radio,
  CheckCircle2,
  AlertTriangle,
  Flame,
  CloudRain,
  Cpu,
  UserCheck,
  RefreshCw,
  Volume2,
  TrendingUp,
} from 'lucide-react';
import { useRaceStore } from '../store/raceStore';
import { audioEngine } from '../utils/audioEngine';

interface AgentProposal {
  agent_id: string;
  agent_name: string;
  role_title: string;
  avatar_color: string;
  proposed_action: string;
  confidence: number;
  urgency: string;
  primary_rationale: string;
  key_metric_label: string;
  key_metric_value: string;
  weighted_vote_weight: number;
}

interface PitWallConsensus {
  timestamp_utc: string;
  lap: number;
  consensus_action: string;
  consensus_confidence: number;
  consensus_strength: string;
  action_vote_distribution: Record<string, number>;
  proposals: AgentProposal[];
  dissenting_views: string[];
  pitwall_radio_transcript: Array<{ speaker: string; message: string; tone: string }>;
  executive_verdict: string;
}

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export const PitWallConsensusModal: React.FC<Props> = ({ isOpen, onClose }) => {
  const { raceState } = useRaceStore();
  const [consensus, setConsensus] = useState<PitWallConsensus | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchConsensus = async () => {
    try {
      const raceId = raceState?.race_id || 'default';
      const res = await fetch(`/api/strategy/pitwall-consensus/${raceId}`);
      if (res.ok) {
        const data = await res.json();
        setConsensus(data);
      }
      setLoading(false);
    } catch (e) {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchConsensus();
      const interval = setInterval(fetchConsensus, 4000);
      return () => clearInterval(interval);
    }
  }, [isOpen, raceState?.current_lap]);

  if (!isOpen) return null;

  const playRadioVerbalization = () => {
    if (!consensus) return;
    const msg = `Pit Wall Executive Order on Lap ${consensus.lap}: ${consensus.consensus_action}. Consensus confidence ${Math.round(
      consensus.consensus_confidence * 100
    )} percent.`;
    audioEngine.speakRadioMessage(msg);
  };

  const getAgentIcon = (id: string) => {
    switch (id) {
      case 'chief_strategist':
        return <Users className="w-5 h-5" />;
      case 'tyre_specialist':
        return <Flame className="w-5 h-5 text-amber-400" />;
      case 'met_officer':
        return <CloudRain className="w-5 h-5 text-emerald-400" />;
      case 'powertrain_engineer':
        return <Cpu className="w-5 h-5 text-purple-400" />;
      default:
        return <UserCheck className="w-5 h-5 text-yellow-400" />;
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl max-w-4xl w-full max-h-[90vh] flex flex-col shadow-2xl overflow-hidden font-mono text-slate-100">
        {/* Header */}
        <div className="p-4 bg-slate-950/80 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              <Users className="w-6 h-6 animate-pulse" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white font-sans flex items-center gap-2">
                Multi-Agent Pit Wall Deliberation & Consensus Protocol
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/30">
                  5 Autonomous Specialists
                </span>
              </h2>
              <p className="text-xs text-slate-400">Real-time debate and weighted vote aggregation across pit wall roles</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={playRadioVerbalization}
              className="px-3 py-1.5 rounded-lg bg-cyan-950 border border-cyan-700/60 hover:bg-cyan-900/60 text-cyan-300 text-xs flex items-center gap-1.5 transition-colors"
            >
              <Volume2 className="w-3.5 h-3.5" /> Radio Synthesizer
            </button>
            <button onClick={onClose} className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors">
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-4">
          {loading || !consensus ? (
            <div className="p-12 text-center text-slate-400 flex flex-col items-center gap-3">
              <RefreshCw className="w-6 h-6 animate-spin text-cyan-400" />
              <span>Synthesizing multi-agent specialist debate...</span>
            </div>
          ) : (
            <>
              {/* Verdict Banner */}
              <div className="p-4 rounded-xl bg-gradient-to-r from-cyan-950/40 via-slate-900 to-slate-900 border border-cyan-500/30 flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                  <span className="text-[10px] text-cyan-400 font-bold uppercase tracking-wider block mb-1">
                    Executive Strategic Verdict (Lap {consensus.lap})
                  </span>
                  <div className="flex items-center gap-3">
                    <span className="text-2xl font-bold font-sans text-white">{consensus.consensus_action}</span>
                    <span className="px-2.5 py-1 rounded text-xs font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
                      {consensus.consensus_strength} ({Math.round(consensus.consensus_confidence * 100)}% Confidence)
                    </span>
                  </div>
                  <p className="text-xs text-slate-300 mt-1">{consensus.executive_verdict}</p>
                </div>

                <div className="flex flex-col gap-1 text-right">
                  <span className="text-[10px] text-slate-400 uppercase">Vote Distribution</span>
                  <div className="flex items-center gap-2">
                    {Object.entries(consensus.action_vote_distribution).map(([act, score]) => (
                      <span key={act} className="px-2 py-0.5 rounded bg-slate-950 text-[10px] text-slate-300 border border-slate-800">
                        {act}: <strong className="text-cyan-400">{Math.round(score * 100)}%</strong>
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* 5 Specialist Proposals Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {consensus.proposals.map((agent) => (
                  <div
                    key={agent.agent_id}
                    className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 flex flex-col justify-between gap-2.5 hover:border-slate-700 transition-colors"
                  >
                    <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
                      <div className="flex items-center gap-2">
                        <div className="p-1.5 rounded-lg bg-slate-900 border border-slate-800">
                          {getAgentIcon(agent.agent_id)}
                        </div>
                        <div>
                          <span className="text-xs font-bold text-white block">{agent.agent_name}</span>
                          <span className="text-[10px] text-slate-400">{agent.role_title}</span>
                        </div>
                      </div>
                      <span className="text-[10px] text-slate-500 font-mono">Weight {Math.round(agent.weighted_vote_weight * 100)}%</span>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="text-[11px] text-slate-300 font-semibold">Vote: <span className="text-cyan-400">{agent.proposed_action}</span></span>
                      <span className="text-[10px] px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-300">
                        {Math.round(agent.confidence * 100)}% Conf
                      </span>
                    </div>

                    <p className="text-[11px] text-slate-300 italic bg-slate-900/60 p-2 rounded border border-slate-800/50">
                      "{agent.primary_rationale}"
                    </p>

                    <div className="flex items-center justify-between text-[10px] text-slate-400 pt-1 border-t border-slate-800/60">
                      <span>{agent.key_metric_label}:</span>
                      <strong className="text-slate-200 font-mono">{agent.key_metric_value}</strong>
                    </div>
                  </div>
                ))}
              </div>

              {/* Radio Transcript Feed */}
              <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 flex flex-col gap-2.5">
                <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                  <Radio className="w-3.5 h-3.5 text-cyan-400" /> Pit Wall Intercom Channel Transcript
                </h3>
                <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                  {consensus.pitwall_radio_transcript.map((line, idx) => (
                    <div key={idx} className="text-xs flex items-start gap-2 text-slate-300">
                      <span className="font-bold text-cyan-400 whitespace-nowrap min-w-[130px]">{line.speaker}:</span>
                      <span className="text-slate-300">{line.message}</span>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
