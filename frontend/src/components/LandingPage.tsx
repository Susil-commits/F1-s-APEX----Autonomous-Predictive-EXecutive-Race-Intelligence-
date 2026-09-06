import React from 'react';
import { Header } from './Header';
import {
  Hero,
  FeatureShowcase,
  DriverLineup,
  HowItWorks,
  CalendarPreview,
  LandingFooter,
} from './landing';

interface LandingPageProps {
  onEnterApp: () => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({ onEnterApp }) => {
  return (
    <div className="min-h-screen bg-[var(--bg-primary)] text-[var(--text-primary)] selection:bg-red-600 selection:text-white transition-colors duration-300">
      {/* Top Header */}
      <Header currentView="landing" onNavigate={(v) => v === 'predictor' && onEnterApp()} />

      {/* Hero Section */}
      <Hero onEnterApp={onEnterApp} />

      {/* 3D Circuit Holographic Showcase */}
      <FeatureShowcase />

      {/* 2026 Driver Grid Lineup */}
      <DriverLineup onEnterApp={onEnterApp} />

      {/* How APEX Forecasts */}
      <HowItWorks />

      {/* Calendar Preview */}
      <CalendarPreview onEnterApp={onEnterApp} />

      {/* Global Partners & Footer */}
      <LandingFooter />
    </div>
  );
};

export default LandingPage;
