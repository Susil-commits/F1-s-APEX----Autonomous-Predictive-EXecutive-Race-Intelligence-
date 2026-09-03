import React, { useState, useEffect } from 'react';
import { Zap, Clock, Activity } from 'lucide-react';

export const Header: React.FC = () => {
  const [currentTimeUTC, setCurrentTimeUTC] = useState<string>('');

  useEffect(() => {
    const updateTime = () => {
      const d = new Date();
      setCurrentTimeUTC(
        `${d.getUTCHours().toString().padStart(2, '0')}:${d
          .getUTCMinutes()
          .toString()
          .padStart(2, '0')}:${d.getUTCSeconds().toString().padStart(2, '0')} UTC`
      );
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="w-full bg-[#090B10]/95 backdrop-blur-xl border-b border-[#1F2432] px-4 lg:px-8 py-3 flex items-center justify-between sticky top-0 z-50 shadow-2xl shadow-black/80 relative">
      {/* Red underline accent */}
      <div className="absolute bottom-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-[#E10600] to-transparent opacity-80" />

      {/* Brand & Subtitle */}
      <div className="flex items-center gap-3">
        {/* Official F1 Red Angle Box */}
        <div className="h-9 px-3.5 rounded bg-gradient-to-r from-[#E10600] to-[#B30000] flex items-center justify-center shadow-lg shadow-red-600/30 border-t border-white/20 -skew-x-12">
          <span className="font-black text-sm tracking-tighter text-white uppercase skew-x-12 flex items-center gap-1.5 font-sans">
            <Zap className="w-3.5 h-3.5 fill-white" />
            APEX
          </span>
        </div>

        <div>
          <div className="flex items-center gap-2">
            <span className="font-black text-sm tracking-wider text-white font-sans">RACE INTELLIGENCE</span>
            <span className="text-[9px] font-mono font-black uppercase px-1.5 py-0.5 rounded bg-red-950 text-red-400 border border-red-800">
              V1 CORE
            </span>
          </div>
          <p className="text-[10px] text-slate-400 font-mono tracking-tight">
            Autonomous Pre-Race Predictive Intelligence · Conformal Calibration
          </p>
        </div>
      </div>

      {/* Right side stats */}
      <div className="flex items-center gap-3">
        {/* Broadcast Live Session Clock */}
        <div className="hidden sm:flex items-center gap-1.5 px-3 py-1 rounded bg-[#10131B] border border-[#232736] text-xs font-mono text-slate-300">
          <Clock className="w-3.5 h-3.5 text-[#00F0FF]" />
          <span className="font-bold text-white tracking-widest">{currentTimeUTC}</span>
        </div>

        {/* Engine Status Indicator */}
        <div className="flex items-center gap-1.5 px-3 py-1 rounded bg-[#131722] border border-[#232736] text-xs font-mono">
          <Activity className="w-3.5 h-3.5 text-emerald-400" />
          <div className="w-2 h-2 rounded-full bg-emerald-500 shadow-sm shadow-emerald-500/50" />
          <span className="text-slate-200 font-bold text-[11px]">ONLINE</span>
        </div>
      </div>
    </header>
  );
};

export default Header;
