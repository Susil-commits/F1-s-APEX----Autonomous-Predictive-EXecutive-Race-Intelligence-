import React, { useState, useEffect } from 'react';
import { Clock, ShieldCheck, Activity, ChevronRight } from 'lucide-react';

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
    <header className="w-full bg-[#0D0F16]/95 backdrop-blur-2xl border-b border-[#242633] px-4 lg:px-10 py-3 flex flex-wrap items-center justify-between sticky top-0 z-50 shadow-2xl shadow-black/90 relative">
      {/* Official F1 Red Racing Stripe Accent Bottom */}
      <div className="absolute bottom-0 left-0 right-0 h-[3px] bg-gradient-to-r from-[#E10600] via-[#FF1801] to-[#990000]" />

      {/* LEFT: Official Formula 1 Brand & APEX Identifier */}
      <div className="flex items-center gap-5">
        <a href="/" className="flex items-center gap-4 group cursor-pointer">
          {/* Official F1 SVG Logo */}
          <div className="h-8 flex items-center">
            <img
              src="/f1/f1-logo.svg"
              alt="Formula 1"
              className="h-7 w-auto object-contain transition-transform group-hover:scale-105"
            />
          </div>

          {/* Slanted APEX Red Badge */}
          <div className="h-7 px-3 rounded bg-gradient-to-r from-[#E10600] to-[#B30000] flex items-center justify-center shadow-lg shadow-red-600/30 f1-angle">
            <span className="font-black text-xs tracking-wider text-white uppercase f1-angle-reverse font-f1">
              APEX PREDICTOR
            </span>
          </div>
        </a>

        <div className="h-6 w-px bg-[#242633] hidden md:block" />

        {/* F1 Quick Metadata Badges */}
        <div className="hidden lg:flex items-center gap-3 text-xs font-f1 font-semibold text-slate-300">
          <span className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#161822] border border-[#2B2E3D]">
            <span className="w-2 h-2 rounded-full bg-[#E10600] animate-pulse" />
            <span className="text-white">FIA Verified Data</span>
            <span className="text-slate-400 text-[10px]">· Jolpica / FastF1</span>
          </span>

          <span className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#161822] border border-[#2B2E3D]">
            <ShieldCheck className="w-3.5 h-3.5 text-[#00F0FF]" />
            <span className="text-white">Split-Conformal</span>
            <span className="text-[#00F0FF] font-mono text-[10px]">90% Coverage</span>
          </span>
        </div>
      </div>

      {/* RIGHT: Live Broadcast Session Clock & Status Indicator */}
      <div className="flex items-center gap-3">
        {/* Broadcast Live Session Clock */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#151722] border border-[#262A3B] text-xs font-mono text-slate-200 shadow-inner">
          <Clock className="w-3.5 h-3.5 text-[#E10600]" />
          <span className="font-bold text-white tracking-widest">{currentTimeUTC}</span>
        </div>

        {/* Active Telemetry Beacon */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#151722] border border-[#262A3B] text-xs font-f1">
          <div className="relative flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500" />
          </div>
          <span className="text-slate-200 font-bold text-xs uppercase tracking-wider">LIVE 2026 ENGINE</span>
        </div>
      </div>
    </header>
  );
};

export default Header;
