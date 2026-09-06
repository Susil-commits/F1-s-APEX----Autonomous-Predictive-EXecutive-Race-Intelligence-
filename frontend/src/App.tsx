import React, { useState } from 'react';
import { Header } from './components/Header';
import { LandingPage } from './components/LandingPage';
import { CoreMode } from './modes/core/CoreMode';
import { ThemeProvider } from './context/ThemeContext';

export const AppContent: React.FC = () => {
  const [currentView, setCurrentView] = useState<'landing' | 'predictor'>('landing');

  if (currentView === 'landing') {
    return <LandingPage onEnterApp={() => setCurrentView('predictor')} />;
  }

  return (
    <div className="min-h-screen bg-[var(--bg-primary)] text-[var(--text-primary)] flex flex-col selection:bg-red-600 selection:text-white relative transition-colors duration-300">
      {/* Header with Navigation & Theme Toggle */}
      <Header
        currentView="predictor"
        onNavigate={(view) => setCurrentView(view)}
      />

      {/* Main Predictive Console */}
      <main className="flex-1 p-4 max-w-7xl w-full mx-auto flex flex-col items-center">
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
