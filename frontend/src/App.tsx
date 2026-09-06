import React, { useState } from 'react';
import { Header } from './components/Header';
import { LandingPage } from './components/LandingPage';
import { CoreMode } from './modes/core/CoreMode';
import { ThemeProvider } from './context/ThemeContext';
import { Parallax3DBackground } from './components/Parallax3DBackground';

export const AppContent: React.FC = () => {
  const [currentView, setCurrentView] = useState<'landing' | 'predictor'>('landing');

  if (currentView === 'landing') {
    return <LandingPage onEnterApp={() => setCurrentView('predictor')} />;
  }

  return (
    <div className="min-h-screen bg-[var(--bg-primary)] text-[var(--text-primary)] flex flex-col selection:bg-red-600 selection:text-white relative transition-colors duration-300">
      {/* Dynamic 3D Photo Backdrop in Predictor Console */}
      <Parallax3DBackground
        src="/f1/circuit_hologram_3d.jpg"
        alt="Formula 1 Circuit Track Atmosphere"
        intensity={0.7}
        gradientPlacement="predictor"
        spotlightColor="rgba(0, 240, 255, 0.16)"
        showDepthGrid={true}
        className="fixed"
      />

      {/* Header with Navigation & Theme Toggle */}
      <div className="relative z-20">
        <Header
          currentView="predictor"
          onNavigate={(view) => setCurrentView(view)}
        />
      </div>

      {/* Main Race Strategy Workspace */}
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
