import React, { useState, useEffect } from 'react';
import { Clock, Sun, Moon, Radio, ChevronRight, LayoutDashboard, Compass } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';

interface HeaderProps {
  currentView?: 'landing' | 'predictor';
  onNavigate?: (view: 'landing' | 'predictor') => void;
}

export const Header: React.FC<HeaderProps> = ({ currentView = 'predictor', onNavigate }) => {
  const [currentTimeUTC, setCurrentTimeUTC] = useState<string>('');
  const { theme, toggleTheme } = useTheme();

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
    <header className="w-full matte-glass sticky top-0 z-50 transition-colors duration-300">
      {/* Precision Red Accent Line */}
      <div className="racing-accent-bar w-full" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* LEFT: Branding */}
        <div className="flex items-center gap-4 sm:gap-6">
          <button
            onClick={() => onNavigate?.('landing')}
            className="flex items-center gap-3 group text-left cursor-pointer focus:outline-none"
          >
            <img
              src="/f1/f1-logo.svg"
              alt="Formula 1"
              className="h-6 sm:h-7 w-auto object-contain transition-transform group-hover:scale-105"
            />
            <div className="flex items-center gap-2">
              <span className="text-sm sm:text-base font-extrabold tracking-wider uppercase text-slate-900 dark:text-white font-['Outfit']">
                APEX
              </span>
              <span className="text-[11px] font-bold px-2 py-0.5 rounded-md bg-red-500/10 text-[#E10600] border border-red-500/20 uppercase tracking-widest">
                2026
              </span>
            </div>
          </button>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center gap-1 pl-4 border-l border-slate-200 dark:border-white/10">
            <button
              onClick={() => onNavigate?.('landing')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold tracking-wide transition-all ${
                currentView === 'landing'
                  ? 'bg-slate-200/70 dark:bg-white/10 text-slate-900 dark:text-white'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              Overview
            </button>
            <button
              onClick={() => onNavigate?.('predictor')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold tracking-wide transition-all ${
                currentView === 'predictor'
                  ? 'bg-slate-200/70 dark:bg-white/10 text-slate-900 dark:text-white'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              Race Predictor
            </button>
          </nav>
        </div>

        {/* RIGHT: Status, UTC Clock, Theme Toggle */}
        <div className="flex items-center gap-3 sm:gap-4">
          {/* Live Telemetry Beacon */}
          <div className="hidden sm:flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-slate-100 dark:bg-white/[0.04] border border-slate-200 dark:border-white/[0.08] text-xs">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
            </span>
            <span className="font-semibold text-slate-700 dark:text-slate-300 text-[11px] tracking-wide uppercase">
              Live Telemetry
            </span>
          </div>

          {/* Broadcast Clock */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-100 dark:bg-white/[0.04] border border-slate-200 dark:border-white/[0.08] text-xs font-mono text-slate-700 dark:text-slate-300">
            <Clock className="w-3.5 h-3.5 text-[#E10600]" />
            <span className="font-bold tracking-wider">{currentTimeUTC || '00:00:00 UTC'}</span>
          </div>

          {/* Light / Dark Mode Toggle */}
          <button
            type="button"
            onClick={toggleTheme}
            aria-label="Toggle theme"
            className="w-9 h-9 rounded-xl flex items-center justify-center bg-slate-100 hover:bg-slate-200 dark:bg-white/[0.06] dark:hover:bg-white/[0.12] border border-slate-200 dark:border-white/[0.08] text-slate-700 dark:text-slate-200 transition-all cursor-pointer"
          >
            {theme === 'dark' ? (
              <Sun className="w-4 h-4 text-amber-400 transition-transform duration-300 rotate-0 hover:rotate-45" />
            ) : (
              <Moon className="w-4 h-4 text-indigo-600 transition-transform duration-300 -rotate-12 hover:rotate-0" />
            )}
          </button>

          {/* Action CTA if on landing */}
          {currentView === 'landing' && onNavigate && (
            <button
              onClick={() => onNavigate('predictor')}
              className="btn-f1-primary px-4 py-1.5 text-xs font-bold tracking-wider flex items-center gap-1.5 shadow-sm"
            >
              <span>Predictor</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>
    </header>
  );
};

export default Header;
