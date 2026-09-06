import React from 'react';
import { Play, ChevronRight, Sparkles, ArrowRight } from 'lucide-react';
import { Parallax3DBackground } from '../Parallax3DBackground';
import { F1Aerodynamics3D } from '../F1Aerodynamics3D';
import { useTheme } from '../../context/ThemeContext';

interface HeroProps {
  onEnterApp: () => void;
}

export const Hero: React.FC<HeroProps> = ({ onEnterApp }) => {
  const { theme } = useTheme();

  return (
    <section className="relative overflow-hidden pt-12 pb-20 lg:pt-20 lg:pb-28">
      {/* Full-bleed Interactive 3D Car Background */}
      <Parallax3DBackground
        src="/f1/hero_car_3d.jpg"
        alt="3D Formula 1 Race Car Background"
        intensity={1.15}
        gradientPlacement="hero"
        spotlightColor="rgba(225, 6, 0, 0.25)"
        showDepthGrid={true}
      />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          {/* Left Column: Typography & Call to Action */}
          <div className="lg:col-span-7 flex flex-col gap-6 text-left">
            {/* Badge */}
            <div className="inline-flex items-center gap-2.5 px-3.5 py-1.5 rounded-full bg-red-600/10 border border-red-600/20 text-[#E10600] text-xs font-bold tracking-wider uppercase w-fit backdrop-blur-sm">
              <span className="w-2 h-2 rounded-full bg-[#E10600] animate-pulse" />
              <span>2026 World Championship Intelligence</span>
            </div>

            {/* Main Headline */}
            <h1 className="text-4xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight leading-[1.05] uppercase font-['Outfit'] text-slate-900 dark:text-white drop-shadow-sm">
              PRECISION <span className="text-[#E10600]">RACE FINISH</span> INTELLIGENCE
            </h1>

            {/* Subtitle */}
            <p className="text-lg sm:text-xl text-slate-700 dark:text-slate-300 max-w-2xl font-normal leading-relaxed">
              Experience broadcast-level Grand Prix strategy forecasting. Simulate qualifying grid positions, circuit downforce demands, and race-day weather to project finishing windows and podium probabilities.
            </p>

            {/* Action Buttons */}
            <div className="flex flex-wrap items-center gap-4 pt-2">
              <button
                type="button"
                onClick={onEnterApp}
                className="btn-f1-primary px-8 py-4 text-sm font-bold flex items-center gap-3 cursor-pointer group shadow-xl"
              >
                <Play className="w-4 h-4 fill-current" />
                <span>Launch Predictor Console</span>
                <ChevronRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
              </button>

              <a
                href="#calendar"
                className="btn-f1-secondary px-6 py-4 text-sm font-semibold flex items-center gap-2 backdrop-blur-md"
              >
                <span>Grand Prix Calendar</span>
                <ArrowRight className="w-4 h-4" />
              </a>
            </div>

            {/* Key Racing Indicators */}
            <div className="grid grid-cols-3 gap-4 pt-4 border-t border-slate-300/40 dark:border-white/10 max-w-lg">
              <div>
                <div className="text-2xl font-black text-[#E10600] font-['Outfit']">24</div>
                <div className="text-xs text-slate-600 dark:text-slate-400 font-medium">Championship Rounds</div>
              </div>
              <div>
                <div className="text-2xl font-black text-slate-900 dark:text-white font-['Outfit']">24</div>
                <div className="text-xs text-slate-600 dark:text-slate-400 font-medium">Drivers on Grid</div>
              </div>
              <div>
                <div className="text-2xl font-black text-cyan-600 dark:text-cyan-400 font-['Outfit']">P1 — P24</div>
                <div className="text-xs text-slate-600 dark:text-slate-400 font-medium">Grid Position Pacing</div>
              </div>
            </div>
          </div>

          {/* Right Column: 3D Aerodynamics Simulation Panel */}
          <div className="lg:col-span-5 flex flex-col gap-3">
            <div className="flex items-center justify-between px-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-400 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-[#E10600]" />
                <span>Aerodynamic Wind Tunnel</span>
              </span>
              <span className="text-[11px] font-mono text-slate-500 dark:text-slate-400">
                Airflow Streamline Dynamics
              </span>
            </div>

            {/* 3D Wind Tunnel Interactive Canvas */}
            <div className="matte-panel-elevated overflow-hidden p-2 group relative h-[380px] sm:h-[420px] flex items-center justify-center backdrop-blur-xl border border-slate-300/60 dark:border-white/15">
              <div className="w-full h-full relative rounded-xl overflow-hidden bg-slate-950/40">
                <F1Aerodynamics3D theme={theme} accentColor="#E10600" />
                <div className="absolute bottom-3 left-3 text-[10px] font-mono text-slate-300 bg-black/60 backdrop-blur-md px-2.5 py-1 rounded border border-white/10">
                  Airflow Vortices · Drag to rotate chassis
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Hero;
