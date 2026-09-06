import React, { useState } from 'react';
import { Header } from './components/Header';
import { LandingPage } from './components/LandingPage';
import { CoreMode } from './modes/core/CoreMode';
import { ThemeProvider } from './context/ThemeContext';
import { Parallax3DBackground } from './components/Parallax3DBackground';
import { Sparkles } from 'lucide-react';

export const AppContent: React.FC = () => {
  const [currentView, setCurrentView] = useState<'landing' | 'predictor'>('landing');
  const [backdropMode, setBackdropMode] = useState<'circuit' | 'car' | 'minimal'>('circuit');

  if (currentView === 'landing') {
    return <LandingPage onEnterApp={() => setCurrentView('predictor')} />;
  }

  return (
    <div className="min-h-screen bg-[var(--bg-primary)] text-[var(--text-primary)] flex flex-col selection:bg-red-600 selection:text-white relative transition-colors duration-300">
      {/* Dynamic 3D Photo Backdrop in Predictor Console */}
      {backdropMode === 'circuit' && (
        <Parallax3DBackground
          src="/f1/circuit_hologram_3d.jpg"
          alt="3D Hologram Circuit Mission Control"
          intensity={0.7}
          gradientPlacement="predictor"
          spotlightColor="rgba(0, 240, 255, 0.16)"
          showDepthGrid={true}
          className="fixed"
        />
      )}
      {backdropMode === 'car' && (
        <Parallax3DBackground
          src="/f1/hero_car_3d.jpg"
          alt="3D F1 Race Car Atmosphere"
          intensity={0.7}
          gradientPlacement="predictor"
          spotlightColor="rgba(225, 6, 0, 0.16)"
          showDepthGrid={true}
          className="fixed"
        />
      )}

      {/* Header with Navigation & Theme Toggle */}
      <div className="relative z-20">
        <Header
          currentView="predictor"
          onNavigate={(view) => setCurrentView(view)}
        />
      </div>

      {/* Floating 3D Backdrop Control Pill */}
      <div className="fixed bottom-4 right-4 z-40 flex items-center gap-1.5 p-1.5 rounded-xl bg-black/80 dark:bg-black/90 text-white backdrop-blur-xl border border-white/15 shadow-2xl text-[11px] font-mono">
        <div className="px-2 py-1 flex items-center gap-1 text-slate-400 font-bold uppercase tracking-wider text-[9px]">
          <Sparkles className="w-3 h-3 text-[#E10600]" />
          <span>3D Backdrop:</span>
        </div>
        <button
          type="button"
          onClick={() => setBackdropMode('circuit')}
          className={`px-2.5 py-1 rounded-lg transition-all cursor-pointer ${
            backdropMode === 'circuit'
              ? 'bg-[#E10600] text-white font-bold shadow-md'
              : 'text-slate-300 hover:text-white'
          }`}
        >
          3D Track
        </button>
        <button
          type="button"
          onClick={() => setBackdropMode('car')}
          className={`px-2.5 py-1 rounded-lg transition-all cursor-pointer ${
            backdropMode === 'car'
              ? 'bg-[#E10600] text-white font-bold shadow-md'
              : 'text-slate-300 hover:text-white'
          }`}
        >
          3D Car
        </button>
        <button
          type="button"
          onClick={() => setBackdropMode('minimal')}
          className={`px-2 py-1 rounded-lg transition-all cursor-pointer ${
            backdropMode === 'minimal'
              ? 'bg-slate-700 text-white font-bold'
              : 'text-slate-400 hover:text-white'
          }`}
        >
          Off
        </button>
      </div>

      {/* Main Predictive Console */}
      <main className="flex-1 p-4 max-w-7xl w-full mx-auto flex flex-col items-center relative z-10">
        <CoreMode />
      </main>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <ThemeProvider>
      <AppContent />
    </ThemeProvider>
  );
};

export default App;
