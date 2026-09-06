import React, { useState } from 'react';
import { Header } from './components/Header';
import { LandingPage } from './components/LandingPage';
import { CoreMode } from './modes/core/CoreMode';

export const App: React.FC = () => {
  const [showApp, setShowApp] = useState<boolean>(false);

  if (!showApp) {
    return <LandingPage onEnterApp={() => setShowApp(true)} />;
  }

  return (
    <div className="min-h-screen bg-[#060709] text-slate-100 flex flex-col selection:bg-apex-cyan selection:text-black relative">
      {/* Header */}
      <Header />
      {/* Main Single-Tier Predictive Console */}
      <main className="flex-1 p-4 max-w-[1920px] w-full mx-auto flex flex-col items-center">
        <CoreMode />
      </main>
    </div>
  );
};

export default App;
