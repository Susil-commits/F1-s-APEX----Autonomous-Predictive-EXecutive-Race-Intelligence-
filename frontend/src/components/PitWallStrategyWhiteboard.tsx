import React, { useState, useRef, useEffect } from 'react';
import { useRaceStore } from '../store/raceStore';
import { CIRCUIT_DATABASE } from '../data/trackGeometries';
import { Edit3, ArrowRight, Flag, ShieldAlert, Sparkles, Trash2, Download, StickyNote, RotateCcw } from 'lucide-react';

export const PitWallStrategyWhiteboard: React.FC = () => {
  const { raceState } = useRaceStore();
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  const [activeTool, setActiveTool] = useState<'PEN' | 'ARROW' | 'PIN' | 'NOTE'>('PEN');
  const [penColor, setPenColor] = useState<string>('#00f0ff');
  const [lineWidth, setLineWidth] = useState<number>(3);
  const [isDrawing, setIsDrawing] = useState<boolean>(false);
  const [notes, setNotes] = useState<{ id: number; x: number; y: number; text: string }[]>([
    { id: 1, x: 120, y: 80, text: 'Plan A: Box L18 for Hards if gap > 22s' },
    { id: 2, x: 500, y: 220, text: 'Undercut window open on car ahead' },
  ]);

  const trackKey = (raceState?.track?.name || 'silverstone').toLowerCase();
  const circuit =
    Object.values(CIRCUIT_DATABASE).find(
      (c) => c.id === trackKey || c.name.toLowerCase().includes(trackKey)
    ) || CIRCUIT_DATABASE.silverstone;

  // Initialize Canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
  }, []);

  const startDrawing = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    if (activeTool === 'NOTE') {
      setNotes((prev) => [...prev, { id: Date.now(), x, y, text: 'New Strategy Tactical Call' }]);
      return;
    }

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    setIsDrawing(true);
    ctx.beginPath();
    ctx.moveTo(x, y);
    ctx.strokeStyle = penColor;
    ctx.lineWidth = lineWidth;
  };

  const draw = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawing || activeTool !== 'PEN') return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    ctx.lineTo(x, y);
    ctx.stroke();
  };

  const stopDrawing = () => {
    if (!isDrawing) return;
    setIsDrawing(false);
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.closePath();
  };

  const clearCanvas = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    setNotes([]);
  };

  const exportStrategyBrief = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const link = document.createElement('a');
    link.download = `APEX_PitWall_Strategy_Brief_${circuit.id}.png`;
    link.href = canvas.toDataURL();
    link.click();
  };

  return (
    <div className="w-full rounded-2xl bg-slate-950 border border-slate-800 p-4 flex flex-col gap-4 shadow-2xl">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Edit3 className="w-5 h-5 text-apex-cyan animate-pulse" />
          <div className="flex flex-col">
            <span className="font-bold text-white text-sm">
              TACTICAL PIT WALL STRATEGY WHITEBOARD & ANNOTATION STUDIO
            </span>
            <span className="text-[11px] font-mono text-slate-400">
              Interactive racing line sketchpad, undercut attack vectors & exportable strategy brief
            </span>
          </div>
        </div>

        {/* Toolbar Controls */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Tool Selector */}
          <div className="flex items-center bg-slate-900 p-1 rounded-xl border border-slate-800 text-xs font-mono">
            <button
              onClick={() => setActiveTool('PEN')}
              className={`px-2.5 py-1 rounded-lg transition-all ${
                activeTool === 'PEN' ? 'bg-apex-cyan text-black font-bold' : 'text-slate-400'
              }`}
            >
              Pen
            </button>
            <button
              onClick={() => setActiveTool('NOTE')}
              className={`px-2.5 py-1 rounded-lg transition-all ${
                activeTool === 'NOTE' ? 'bg-amber-500 text-black font-bold' : 'text-slate-400'
              }`}
            >
              Sticky Note
            </button>
          </div>

          {/* Color Palette */}
          <div className="flex items-center gap-1.5 bg-slate-900 p-1.5 rounded-xl border border-slate-800">
            {['#00f0ff', '#f59e0b', '#ec4899', '#22c55e', '#ffffff'].map((c) => (
              <button
                key={c}
                onClick={() => setPenColor(c)}
                className={`w-5 h-5 rounded-full border-2 transition-all ${
                  penColor === c ? 'scale-110 border-white' : 'border-transparent opacity-70'
                }`}
                style={{ backgroundColor: c }}
              />
            ))}
          </div>

          {/* Clear & Export Buttons */}
          <button
            onClick={clearCanvas}
            className="p-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-300 transition-all"
            title="Clear Whiteboard"
          >
            <Trash2 className="w-4 h-4 text-rose-400" />
          </button>

          <button
            onClick={exportStrategyBrief}
            className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-black text-xs font-mono font-bold transition-all active:scale-95 shadow-sm"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export Brief</span>
          </button>
        </div>
      </div>

      {/* Main Canvas Area with Track Circuit Overlay */}
      <div className="relative w-full h-[520px] rounded-xl overflow-hidden bg-slate-900/90 border border-slate-800 flex items-center justify-center">
        {/* Background Track SVG Outline */}
        <div className="absolute inset-0 flex items-center justify-center opacity-30 pointer-events-none p-8">
          <svg viewBox={circuit.viewBox} className="w-full h-full stroke-slate-500" fill="none">
            <path d={circuit.fullPath} stroke="#64748b" strokeWidth="18" />
            <path d={circuit.fullPath} stroke="#00f0ff" strokeWidth="2" strokeDasharray="4 4" />
          </svg>
        </div>

        {/* Freehand Interactive Drawing Canvas */}
        <canvas
          ref={canvasRef}
          width={1200}
          height={520}
          onMouseDown={startDrawing}
          onMouseMove={draw}
          onMouseUp={stopDrawing}
          onMouseLeave={stopDrawing}
          className="absolute inset-0 w-full h-full cursor-crosshair z-10"
        />

        {/* Strategy Sticky Notes */}
        {notes.map((note) => (
          <div
            key={note.id}
            style={{ left: `${note.x}px`, top: `${note.y}px` }}
            className="absolute z-20 p-2.5 rounded-xl bg-amber-400/90 text-black shadow-2xl max-w-xs border border-amber-300 font-mono text-xs font-bold"
          >
            <div className="flex items-center gap-1 mb-1 text-[10px] text-amber-950 uppercase border-b border-amber-500 pb-0.5">
              <StickyNote className="w-3 h-3" />
              <span>TACTICAL NOTE</span>
            </div>
            <textarea
              defaultValue={note.text}
              className="bg-transparent border-none outline-none resize-none w-full text-xs font-medium text-black"
              rows={2}
            />
          </div>
        ))}
      </div>
    </div>
  );
};
