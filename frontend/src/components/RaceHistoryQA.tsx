import React, { useState } from 'react';
import { useRaceStore } from '../store/raceStore';
import {
  MessageSquare,
  Search,
  Sparkles,
  Database,
  ExternalLink,
  ShieldAlert,
  Zap,
  CheckCircle2,
  HelpCircle,
  X,
  Bot,
  Brain,
  Cpu,
  Download,
  FileText,
} from 'lucide-react';

interface DecisionSource {
  race_id?: string;
  lap: number;
  recommendation: string;
  confidence_score: number;
  urgency: string;
  rule_action?: string;
  dqn_action?: string;
  tyre_cliff_risk?: string;
  primary_factors: string[];
  commentary?: string;
  similarity_score?: number;
}

interface QAResponse {
  answer: string;
  sources: DecisionSource[];
  retrieved_count: number;
  model_used: string;
}

const SAMPLE_QUERIES = [
  'Why did we pit on lap 23?',
  'What did the DQN agent recommend during the safety car?',
  'What was our highest urgency tactical directive?',
  'What was the tyre cliff risk and window status in the early stint?',
];

interface RaceHistoryQAProps {
  onClose?: () => void;
}

export const RaceHistoryQA: React.FC<RaceHistoryQAProps> = ({ onClose }) => {
  const { raceState } = useRaceStore();
  const [question, setQuestion] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [qaResult, setQaResult] = useState<QAResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleAsk = async (queryText?: string) => {
    const q = (queryText || question).trim();
    if (!q) return;

    setIsLoading(true);
    setErrorMsg(null);

    try {
      const resp = await fetch('http://localhost:8000/api/race/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          race_id: raceState?.race_id,
          question: q,
          top_k: 5,
        }),
      });

      if (!resp.ok) {
        throw new Error(`Server returned status ${resp.status}`);
      }

      const data: QAResponse = await resp.json();
      setQaResult(data);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to query race history RAG endpoint.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleExportDebrief = async () => {
    try {
      const raceId = raceState?.race_id || 'active_session';
      const resp = await fetch(`http://localhost:8000/api/race/export/${raceId}`);
      if (!resp.ok) throw new Error('Failed to export debrief');
      const data = await resp.json();
      const reportMd = data.markdown_report || JSON.stringify(data, null, 2);
      
      const blob = new Blob([reportMd], { type: 'text/markdown' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `APEX_Race_Debrief_${raceId}.md`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Export error:', err);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in">
      <div className="bg-slate-900 border border-apex-border rounded-2xl w-full max-w-4xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="p-5 border-b border-slate-800 flex items-center justify-between bg-slate-950/60">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-cyan-950/80 border border-cyan-700/60 flex items-center justify-center shadow-lg shadow-cyan-900/30">
              <Brain className="w-5 h-5 text-cyan-400" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-black text-white uppercase tracking-wider">
                  Race History RAG Debrief & Audit
                </h2>
                <span className="text-[10px] font-mono font-bold text-cyan-300 bg-cyan-950/80 px-2 py-0.5 rounded border border-cyan-800/60">
                  Grounded Vector Retrieval
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Ask natural-language tactical questions verified strictly against persisted{' '}
                <code className="text-slate-300 font-mono">DecisionLogModel</code> telemetry records.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleExportDebrief}
              title="Download Full Markdown Strategy Debrief Report"
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-cyan-950/80 hover:bg-cyan-900/80 border border-cyan-700/60 text-cyan-300 text-xs font-mono font-bold transition-all active:scale-95 shadow-md shadow-cyan-950/30"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Export Debrief</span>
            </button>
            {onClose && (
              <button
                onClick={onClose}
                className="p-2 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-400 hover:text-white transition-all active:scale-95"
              >
                <X className="w-5 h-5" />
              </button>
            )}
          </div>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-5 space-y-5 custom-scrollbar">
          {/* Quick Query Chips */}
          <div>
            <span className="text-[10px] uppercase font-mono font-bold text-slate-400 block mb-2">
              Suggested Strategy Queries
            </span>
            <div className="flex flex-wrap gap-2">
              {SAMPLE_QUERIES.map((sq, i) => (
                <button
                  key={i}
                  onClick={() => {
                    setQuestion(sq);
                    handleAsk(sq);
                  }}
                  className="px-3 py-1.5 rounded-lg text-xs bg-slate-800/60 hover:bg-cyan-950/60 text-slate-300 hover:text-cyan-300 border border-slate-700/80 hover:border-cyan-700/50 transition-all font-mono active:scale-95"
                >
                  "{sq}"
                </button>
              ))}
            </div>
          </div>

          {/* Search Input Bar */}
          <div className="flex gap-2">
            <div className="relative flex-1">
              <input
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleAsk()}
                placeholder="Ask about pit calls, tyre cliffs, safety car reactions, or DQN decisions..."
                className="w-full pl-10 pr-4 py-3 bg-slate-950/80 border border-slate-700 rounded-xl text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500 font-sans"
              />
              <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
            </div>
            <button
              onClick={() => handleAsk()}
              disabled={isLoading || !question.trim()}
              className="px-6 py-3 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 disabled:opacity-50 text-black font-black text-xs uppercase tracking-wider rounded-xl transition-all shadow-lg shadow-cyan-500/20 active:scale-95 flex items-center gap-2 shrink-0"
            >
              {isLoading ? (
                <>
                  <div className="w-4 h-4 border-2 border-black border-t-transparent rounded-full animate-spin" />
                  <span>Searching...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>Query Logs</span>
                </>
              )}
            </button>
          </div>

          {/* Error Message */}
          {errorMsg && (
            <div className="p-3 rounded-xl bg-rose-950/40 border border-rose-800 text-rose-300 text-xs">
              {errorMsg}
            </div>
          )}

          {/* Answer Card */}
          {qaResult && (
            <div className="space-y-4">
              <div className="p-4 rounded-xl bg-slate-950/90 border border-cyan-500/40 shadow-xl relative overflow-hidden">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-cyan-400" />
                    <span className="text-xs font-black uppercase tracking-wider text-cyan-300">
                      APEX Intelligence Response
                    </span>
                  </div>
                  <span className="text-[10px] font-mono text-slate-400 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                    Model: {qaResult.model_used}
                  </span>
                </div>
                <p className="text-sm font-sans text-slate-100 leading-relaxed font-medium">
                  {qaResult.answer}
                </p>
              </div>

              {/* Citations & Verified Sources */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[11px] font-mono uppercase font-bold text-slate-400 flex items-center gap-1.5">
                    <Database className="w-3.5 h-3.5 text-cyan-400" />
                    Retrieved Ground-Truth Decision Logs ({qaResult.sources.length})
                  </span>
                  <span className="text-[10px] text-slate-500 font-mono">
                    Cosine Similarity Ranked
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {qaResult.sources.map((src, idx) => (
                    <div
                      key={idx}
                      className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 hover:border-slate-700 transition-all font-mono text-xs space-y-2"
                    >
                      <div className="flex items-center justify-between border-b border-slate-800/80 pb-1.5">
                        <div className="flex items-center gap-2">
                          <span className="px-2 py-0.5 rounded bg-slate-800 text-cyan-300 font-bold">
                            Lap {src.lap}
                          </span>
                          <span className="font-bold text-white">{src.recommendation}</span>
                        </div>
                        <span
                          className={`text-[9.5px] px-2 py-0.5 rounded font-bold uppercase ${
                            src.urgency === 'CRITICAL'
                              ? 'bg-rose-950 text-rose-400 border border-rose-800'
                              : src.urgency === 'HIGH'
                              ? 'bg-amber-950 text-amber-400 border border-amber-800'
                              : 'bg-slate-800 text-slate-300'
                          }`}
                        >
                          {src.urgency}
                        </span>
                      </div>

                      {/* Primary Drivers */}
                      <div className="font-sans text-[11.5px] text-slate-300">
                        {src.primary_factors.map((f, fi) => (
                          <div key={fi} className="flex items-center gap-1 text-slate-300 py-0.5">
                            <CheckCircle2 className="w-3 h-3 text-cyan-400 shrink-0" />
                            <span className="truncate">{f}</span>
                          </div>
                        ))}
                      </div>

                      {/* Model Comparison Pill */}
                      <div className="flex items-center justify-between pt-1 border-t border-slate-800/60 text-[10px] text-slate-400">
                        <span>Rule: {src.rule_action || 'N/A'}</span>
                        <span>DQN: {src.dqn_action || 'N/A'}</span>
                        <span className="text-cyan-400 font-bold">
                          Cliff: {src.tyre_cliff_risk || 'LOW'}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
