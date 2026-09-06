import React, { useState } from 'react';
import { Gauge, CloudRain, Layers } from 'lucide-react';
import { Parallax3DBackground } from '../Parallax3DBackground';

export const FeatureShowcase: React.FC = () => {
  const [showcasePhoto, setShowcasePhoto] = useState<'hologram' | 'car'>('hologram');

  return (
    <section className="py-24 border-y border-slate-200 dark:border-white/10 relative overflow-hidden">
      {/* Full-bleed Interactive 3D Hologram Circuit Background */}
      <Parallax3DBackground
        src="/f1/circuit_hologram_3d.jpg"
        alt="Formula 1 Circuit Track Background"
        intensity={0.95}
        gradientPlacement="circuit"
        spotlightColor="rgba(0, 240, 255, 0.22)"
        showDepthGrid={true}
      />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
          {/* Hologram Card with Telemetry Beacons & Photo Switcher */}
          <div className="lg:col-span-7 matte-panel overflow-hidden p-3 group backdrop-blur-xl border border-slate-300/60 dark:border-white/15 card-3d">
            <div className="relative rounded-xl overflow-hidden aspect-video bg-black/80">
              <img
                src={showcasePhoto === 'hologram' ? '/f1/circuit_hologram_3d.jpg' : '/f1/hero_car_3d.jpg'}
                alt={showcasePhoto === 'hologram' ? 'Formula 1 Circuit Elevation Map' : '2026 Formula 1 Aerodynamic Chassis'}
                className="w-full h-full object-cover transition-all duration-700 group-hover:scale-105"
              />
              <div className="absolute inset-0 bg-gradient-to-tr from-black/80 via-transparent to-black/30 pointer-events-none" />
              
              {/* Header Overlay with Photo Switcher */}
              <div className="absolute top-4 left-4 right-4 flex items-center justify-between">
                <span className="px-2.5 py-1 rounded-md bg-red-600/90 text-white font-black text-[10px] tracking-widest uppercase font-mono shadow-md">
                  {showcasePhoto === 'hologram' ? 'CIRCUIT TELEMETRY · TRACK PROFILE' : 'AERODYNAMICS · 2026 CHAMPIONSHIP CHASSIS'}
                </span>
                
                <div className="flex items-center gap-1 bg-black/70 backdrop-blur-md p-1 rounded-lg border border-white/20">
                  <button
                    type="button"
                    onClick={() => setShowcasePhoto('hologram')}
                    className={`px-2.5 py-1 rounded text-[10px] font-mono font-bold transition-all cursor-pointer ${
                      showcasePhoto === 'hologram'
                        ? 'bg-[#E10600] text-white shadow'
                        : 'text-slate-300 hover:text-white'
                    }`}
                  >
                    Track Map
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowcasePhoto('car')}
                    className={`px-2.5 py-1 rounded text-[10px] font-mono font-bold transition-all cursor-pointer ${
                      showcasePhoto === 'car'
                        ? 'bg-[#E10600] text-white shadow'
                        : 'text-slate-300 hover:text-white'
                    }`}
                  >
                    Car Chassis
                  </button>
                </div>
              </div>

              <div className="absolute bottom-4 left-4 right-4 flex items-center justify-between text-xs text-white">
                <div className="font-mono text-[11px] text-slate-300">
                  {showcasePhoto === 'hologram' ? 'Circuit Elevation & Downforce Profile' : 'Ground Effect Venturi & Rear Wing Aero'}
                </div>
                <span className="px-2.5 py-1 rounded bg-black/60 backdrop-blur-md border border-white/20 text-[10px] font-mono text-cyan-400">
                  Grand Prix Map
                </span>
              </div>
            </div>
          </div>

          {/* Strategic Explanations */}
          <div className="lg:col-span-5 flex flex-col gap-5">
            <div className="inline-flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[#E10600]">
              <Layers className="w-4 h-4" />
              <span>Track Aerodynamics & Dynamics</span>
            </div>
            <h2 className="text-3xl sm:text-4xl font-extrabold uppercase tracking-tight text-slate-900 dark:text-white font-['Outfit']">
              CIRCUIT DYNAMICS & DOWNFORCE DEMAND
            </h2>
            <p className="text-sm sm:text-base text-slate-700 dark:text-slate-300 leading-relaxed">
              Every circuit on the calendar tests different performance dimensions. From Monza&apos;s low-drag high-speed straights to Monaco&apos;s maximum downforce street chicanes, APEX analyzes each track&apos;s unique overtaking delta and tire degradation profile.
            </p>

            <div className="space-y-3 pt-2">
              <div className="p-3.5 rounded-xl bg-white/80 dark:bg-white/[0.04] border border-slate-200 dark:border-white/[0.1] backdrop-blur-md flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-red-500/10 flex items-center justify-center text-[#E10600]">
                  <Gauge className="w-4 h-4" />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider">Aero Downforce Tiers</h4>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400">Low, Medium, High, and Maximum downforce configurations configured per track.</p>
                </div>
              </div>

              <div className="p-3.5 rounded-xl bg-white/80 dark:bg-white/[0.04] border border-slate-200 dark:border-white/[0.1] backdrop-blur-md flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-cyan-500/10 flex items-center justify-center text-cyan-600 dark:text-cyan-400">
                  <CloudRain className="w-4 h-4" />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider">Dynamic Weather Scenarios</h4>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400">Dry, mixed conditions, and heavy wet tire crossover thresholds.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default FeatureShowcase;
