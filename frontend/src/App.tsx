import React from 'react';
import { Header } from './components/Header';
import { CoreMode } from './modes/core/CoreMode';

export const App: React.FC = () => {
  return (
    <div className="min-h-screen bg-apex-bg text-slate-100 flex flex-col selection:bg-apex-cyan selection:text-black relative">
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
