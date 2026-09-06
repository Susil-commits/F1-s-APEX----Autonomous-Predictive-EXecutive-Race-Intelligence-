import React, { useState } from 'react';
import {
  Play,
  ChevronRight,
  Gauge,
  Flag,
  CloudRain,
  Trophy,
  Activity,
  Layers,
  Sparkles,
  ArrowRight,
  Shield,
  Zap,
} from 'lucide-react';
import { GRAND_PRIX_LIST, DRIVERS_LIST, OFFICIAL_SPONSORS } from '../modes/core/data/constants';
import { F1Aerodynamics3D } from './F1Aerodynamics3D';
import { useTheme } from '../context/ThemeContext';
import { Header } from './Header';

interface LandingPageProps {
  onEnterApp: () => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({ onEnterApp }) => {
  const { theme } = useTheme();
  const [activeTab, setActiveTab] = useState<'3d_car' | '3d_windtunnel'>('3d_car');
  const [selectedCircuit, setSelectedCircuit] = useState(GRAND_PRIX_LIST[0]);

  return (
    <div className="min-h-screen bg-[var(--bg-primary)] text-[var(--text-primary)] selection:bg-red-600 selection:text-white transition-colors duration-300">
      {/* Top Header */}
      <Header currentView="landing" onNavigate={(v) => v === 'predictor' && onEnterApp()} />

      {/* ─── HERO SECTION ─── */}
      <section className="relative overflow-hidden pt-8 pb-16 lg:pt-16 lg:pb-24">
        {/* Subtle ambient light gradient */}
        <div className={`absolute inset-0 pointer-events-none ${theme === 'dark' ? 'hero-ambient-dark' : 'hero-ambient-light'}`} />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
            
            {/* Left Column: Typography & Call to Action */}
            <div className="lg:col-span-7 flex flex-col gap-6 text-left">
              {/* Badge */}
              <div className="inline-flex items-center gap-2.5 px-3.5 py-1.5 rounded-full bg-red-600/10 border border-red-600/20 text-[#E10600] text-xs font-bold tracking-wider uppercase w-fit">
                <span className="w-2 h-2 rounded-full bg-[#E10600] animate-pulse" />
                <span>2026 World Championship Intelligence</span>
              </div>

              {/* Main Headline */}
              <h1 className="text-4xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight leading-[1.05] uppercase font-['Outfit'] text-slate-900 dark:text-white">
                PRECISION <span className="text-[#E10600]">RACE FINISH</span> INTELLIGENCE
              </h1>

              {/* Subtitle */}
              <p className="text-lg sm:text-xl text-slate-600 dark:text-slate-300 max-w-2xl font-normal leading-relaxed">
                Experience broadcast-level Grand Prix strategy forecasting. Simulate qualifying grid positions, circuit downforce demands, and race-day weather to project finishing windows and podium probabilities.
              </p>

              {/* Action Buttons */}
              <div className="flex flex-wrap items-center gap-4 pt-2">
                <button
                  type="button"
                  onClick={onEnterApp}
                  className="btn-f1-primary px-8 py-4 text-sm font-bold flex items-center gap-3 cursor-pointer group"
                >
                  <Play className="w-4 h-4 fill-current" />
                  <span>Launch Predictor Console</span>
                  <ChevronRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
                </button>

                <a
                  href="#calendar"
                  className="btn-f1-secondary px-6 py-4 text-sm font-semibold flex items-center gap-2"
                >
                  <span>Grand Prix Calendar</span>
                  <ArrowRight className="w-4 h-4" />
                </a>
              </div>

              {/* Key Racing Indicators */}
              <div className="grid grid-cols-3 gap-4 pt-4 border-t border-slate-200 dark:border-white/10 max-w-lg">
                <div>
                  <div className="text-2xl font-black text-[#E10600] font-['Outfit']">24</div>
                  <div className="text-xs text-slate-500 dark:text-slate-400 font-medium">Championship Rounds</div>
                </div>
                <div>
                  <div className="text-2xl font-black text-slate-900 dark:text-white font-['Outfit']">12+</div>
                  <div className="text-xs text-slate-500 dark:text-slate-400 font-medium">Drivers Calibrated</div>
                </div>
                <div>
                  <div className="text-2xl font-black text-cyan-600 dark:text-cyan-400 font-['Outfit']">&lt; 100ms</div>
                  <div className="text-xs text-slate-500 dark:text-slate-400 font-medium">Real-Time Simulation</div>
                </div>
              </div>
            </div>

            {/* Right Column: 3D Visual Stage with Interactive Switcher */}
            <div className="lg:col-span-5 flex flex-col gap-3">
              {/* Mode Toggle */}
              <div className="flex items-center justify-between px-2">
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-[#E10600]" />
                  <span>3D Telemetry Visualization</span>
                </span>
                <div className="inline-flex p-1 rounded-xl bg-slate-200/80 dark:bg-white/10 border border-slate-300/60 dark:border-white/10 text-xs">
                  <button
                    onClick={() => setActiveTab('3d_car')}
                    className={`px-3 py-1 rounded-lg font-semibold transition-all ${
                      activeTab === '3d_car'
                        ? 'bg-white dark:bg-[#11141C] text-slate-900 dark:text-white shadow-sm'
                        : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
                    }`}
                  >
                    3D Studio Car
                  </button>
                  <button
                    onClick={() => setActiveTab('3d_windtunnel')}
                    className={`px-3 py-1 rounded-lg font-semibold transition-all ${
                      activeTab === '3d_windtunnel'
                        ? 'bg-white dark:bg-[#11141C] text-slate-900 dark:text-white shadow-sm'
                        : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
                    }`}
                  >
                    3D Aerodynamics
                  </button>
                </div>
              </div>

              {/* 3D Canvas / Render Container */}
              <div className="matte-panel-elevated overflow-hidden p-2 group relative h-[380px] sm:h-[420px] flex items-center justify-center">
                {activeTab === '3d_car' ? (
                  <div className="relative w-full h-full rounded-xl overflow-hidden bg-black/40">
                    <img
                      src="/f1/hero_car_3d.jpg"
                      alt="2026 Formula 1 3D Car Render"
                      className="w-full h-full object-cover object-center transition-transform duration-700 group-hover:scale-105"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent pointer-events-none" />
                    <div className="absolute bottom-4 left-4 right-4 flex items-center justify-between text-white text-xs">
                      <div>
                        <div className="font-bold uppercase tracking-wider text-[11px] text-slate-300">2026 Aerodynamic Model</div>
                        <div className="font-mono text-[10px] text-red-400">Ground Effect & DRS Simulation Active</div>
                      </div>
                      <span className="px-2 py-1 rounded bg-white/20 backdrop-blur-md font-mono text-[10px]">
                        HD Studio
                      </span>
                    </div>
                  </div>
                ) : (
                  <div className="w-full h-full relative rounded-xl overflow-hidden bg-slate-900/40">
                    <F1Aerodynamics3D theme={theme} accentColor="#E10600" />
                    <div className="absolute bottom-3 left-3 text-[10px] font-mono text-slate-400 bg-black/50 backdrop-blur-md px-2.5 py-1 rounded">
                      Drag to orbit wind tunnel streamlines
                    </div>
                  </div>
                )}
              </div>
            </div>

          </div>
        </div>
      </section>

      {/* ─── 3D CIRCUIT HOLOGRAPHIC SHOWCASE ─── */}
      <section className="py-16 border-y border-slate-200 dark:border-white/10 bg-slate-50/50 dark:bg-[#0A0C13]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
            {/* Hologram Image */}
            <div className="lg:col-span-7 matte-panel overflow-hidden p-3 group">
              <div className="relative rounded-xl overflow-hidden aspect-video bg-black">
                <img
                  src="/f1/circuit_hologram_3d.jpg"
                  alt="3D Holographic Circuit Telemetry"
                  className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
                />
                <div className="absolute inset-0 bg-gradient-to-tr from-black/70 via-transparent to-black/30 pointer-events-none" />
                <div className="absolute top-4 left-4 flex items-center gap-2">
                  <span className="px-2.5 py-1 rounded-md bg-red-600/90 text-white font-black text-[10px] tracking-widest uppercase font-mono">
                    HOLOGRAPHIC SECTOR TELEMETRY
                  </span>
                </div>
              </div>
            </div>

            {/* Strategic Explanations */}
            <div className="lg:col-span-5 flex flex-col gap-5">
              <div className="inline-flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[#E10600]">
                <Layers className="w-4 h-4" />
                <span>Track Profiling Engine</span>
              </div>
              <h2 className="text-3xl sm:text-4xl font-extrabold uppercase tracking-tight text-slate-900 dark:text-white font-['Outfit']">
                CIRCUIT DYNAMICS & AERODYNAMIC DEMAND
              </h2>
              <p className="text-sm sm:text-base text-slate-600 dark:text-slate-300 leading-relaxed">
                Every circuit on the calendar tests different performance dimensions. From Monza&apos;s low-drag high-speed straights to Monaco&apos;s maximum downforce street chicanes, APEX models each track&apos;s unique overtaking delta and tire degradation profile.
              </p>

              <div className="space-y-3 pt-2">
                <div className="p-3.5 rounded-xl bg-white dark:bg-white/[0.03] border border-slate-200 dark:border-white/[0.08] flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-red-500/10 flex items-center justify-center text-[#E10600]">
                    <Gauge className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider">Aero Downforce Tiers</h4>
                    <p className="text-[11px] text-slate-500 dark:text-slate-400">Low, Medium, High, and Maximum downforce configurations modeled per track.</p>
                  </div>
                </div>

                <div className="p-3.5 rounded-xl bg-white dark:bg-white/[0.03] border border-slate-200 dark:border-white/[0.08] flex items-center gap-3">
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

      {/* ─── 2026 DRIVER GRID SHOWCASE (HIGH RES PORTRAITS) ─── */}
      <section className="py-20 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-2xl mx-auto mb-12 flex flex-col items-center gap-2">
          <span className="text-xs font-bold uppercase tracking-widest text-[#E10600]">Championship Contenders</span>
          <h2 className="text-3xl sm:text-5xl font-extrabold uppercase tracking-tight text-slate-900 dark:text-white font-['Outfit']">
            2026 DRIVER LINEUP
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Official high-fidelity driver profiles with verified rolling form and constructor pacing.
          </p>
        </div>

        {/* 12 Driver Cards with 3D Tilt Effect and Crystal Clear Face Lighting */}
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
          {DRIVERS_LIST.map((driver) => (
            <div
              key={driver.code}
              className="matte-card-interactive card-3d p-4 flex flex-col justify-between h-56 relative overflow-hidden group"
            >
              {/* Livery Accent Bar */}
              <div
                className="absolute top-0 left-0 right-0 h-1"
                style={{ backgroundColor: driver.color }}
              />

              {/* Ambient face backlight halo */}
              <div
                className="absolute top-6 left-1/2 -translate-x-1/2 w-28 h-28 rounded-full blur-2xl opacity-20 group-hover:opacity-40 transition-opacity pointer-events-none"
                style={{ backgroundColor: driver.color }}
              />

              {/* Top: Country Flag & Number */}
              <div className="flex items-center justify-between text-xs z-10">
                <span className="text-base">{driver.country}</span>
                <span className="font-mono font-black text-slate-400 group-hover:text-slate-900 dark:group-hover:text-white transition-colors">
                  #{driver.number}
                </span>
              </div>

              {/* Driver Face Photo: High Resolution, Centered, Illuminated */}
              <div className="relative h-28 w-full flex items-center justify-center my-1 z-10 overflow-hidden">
                <img
                  src={driver.photo}
                  alt={`${driver.firstName} ${driver.lastName}`}
                  className="h-full w-auto object-contain transition-transform duration-300 group-hover:scale-110 drop-shadow-md"
                  onError={(e) => {
                    // Fallback to stylized initials if image fails
                    const target = e.currentTarget;
                    target.style.display = 'none';
                    if (target.nextElementSibling) {
                      (target.nextElementSibling as HTMLElement).style.display = 'flex';
                    }
                  }}
                />
                <div
                  style={{ display: 'none' }}
                  className="w-16 h-16 rounded-full bg-slate-200 dark:bg-slate-800 items-center justify-center font-bold text-lg text-slate-700 dark:text-white"
                >
                  {driver.code}
                </div>
              </div>

              {/* Bottom: Names & Constructor */}
              <div className="z-10 text-left">
                <div className="text-[10px] uppercase tracking-wider text-slate-500 dark:text-slate-400 font-medium">
                  {driver.firstName}
                </div>
                <div className="text-sm font-extrabold uppercase tracking-tight text-slate-900 dark:text-white font-['Outfit'] truncate">
                  {driver.lastName}
                </div>
                <div className="text-[10px] font-semibold tracking-wide truncate" style={{ color: driver.color }}>
                  {driver.team}
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="text-center mt-8">
          <button
            onClick={onEnterApp}
            className="btn-f1-primary px-8 py-3 text-xs font-bold tracking-wider inline-flex items-center gap-2 cursor-pointer"
          >
            <span>Select Driver in Predictor</span>
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </section>

      {/* ─── HOW APEX FORECASTS (ZERO ML JARGON) ─── */}
      <section className="py-20 border-t border-slate-200 dark:border-white/10 bg-slate-50/50 dark:bg-[#0A0C13]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-16 flex flex-col items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-widest text-[#E10600]">Strategic Analysis</span>
            <h2 className="text-3xl sm:text-4xl font-extrabold uppercase tracking-tight text-slate-900 dark:text-white font-['Outfit']">
              HOW APEX CALCULATES PREDICTIONS
            </h2>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              A 4-stage racing simulation modeled strictly on verifiable pre-race telemetry and conditions.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              {
                step: '01',
                title: 'Circuit Downforce Profile',
                desc: 'Loads track aerodynamic characteristics, cornering loads, and overtaking difficulty.',
                icon: Flag,
              },
              {
                step: '02',
                title: 'Driver & Chassis Pace',
                desc: 'Integrates driver current form, teammate differentials, and constructor engine efficiency.',
                icon: Trophy,
              },
              {
                step: '03',
                title: 'Starting Grid & Weather',
                desc: 'Simulates the qualifying grid slot starting advantage and rain probability on race pace.',
                icon: CloudRain,
              },
              {
                step: '04',
                title: 'Strategic Finish Window',
                desc: 'Delivers the most probable finishing position, expected position window, and win odds.',
                icon: Activity,
              },
            ].map((card) => {
              const Icon = card.icon;
              return (
                <div key={card.step} className="matte-panel p-6 flex flex-col justify-between gap-6 relative">
                  <div className="flex items-center justify-between">
                    <span className="text-2xl font-black text-slate-300 dark:text-white/20 font-mono">
                      {card.step}
                    </span>
                    <div className="w-10 h-10 rounded-xl bg-red-600/10 text-[#E10600] flex items-center justify-center">
                      <Icon className="w-5 h-5" />
                    </div>
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-slate-900 dark:text-white uppercase tracking-tight mb-2">
                      {card.title}
                    </h3>
                    <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                      {card.desc}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ─── CALENDAR PREVIEW ─── */}
      <section id="calendar" className="py-20 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-10 gap-4">
          <div>
            <span className="text-xs font-bold uppercase tracking-widest text-[#E10600]">2026 World Tour</span>
            <h2 className="text-3xl sm:text-4xl font-extrabold uppercase tracking-tight text-slate-900 dark:text-white font-['Outfit']">
              FEATURED VENUES
            </h2>
          </div>
          <button
            onClick={onEnterApp}
            className="btn-f1-primary px-5 py-2.5 text-xs font-bold tracking-wider flex items-center gap-2 self-start md:self-auto cursor-pointer"
          >
            <span>Open in Predictor</span>
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {GRAND_PRIX_LIST.slice(0, 4).map((gp) => (
            <div
              key={gp.id}
              onClick={() => {
                setSelectedCircuit(gp);
                onEnterApp();
              }}
              className="matte-card-interactive p-5 flex flex-col justify-between h-44 cursor-pointer text-left group"
            >
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-bold text-red-600 dark:text-red-400 uppercase">
                  ROUND {gp.round}
                </span>
                <span className="text-2xl">{gp.flag}</span>
              </div>
              <div>
                <h3 className="text-lg font-extrabold uppercase text-slate-900 dark:text-white group-hover:text-[#E10600] transition-colors">
                  {gp.name}
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 truncate">{gp.circuit}</p>
              </div>
              <div className="flex items-center justify-between text-[11px] font-mono text-slate-500 dark:text-slate-400 pt-2 border-t border-slate-200 dark:border-white/10">
                <span>{gp.laps} LAPS</span>
                <span className="px-2 py-0.5 rounded bg-slate-100 dark:bg-white/10 font-bold text-[10px]">
                  {gp.downforce} DF
                </span>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ─── GLOBAL PARTNERS & FOOTER ─── */}
      <footer className="py-12 border-t border-slate-200 dark:border-white/10 bg-slate-100/60 dark:bg-[#06070B] transition-colors">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col items-center gap-6">
          <span className="text-xs font-bold uppercase tracking-widest text-slate-400">
            Formula 1 Global Partners
          </span>

          <div className="flex flex-wrap items-center justify-center gap-6 sm:gap-10 opacity-70 hover:opacity-100 transition-opacity">
            {OFFICIAL_SPONSORS.map((sponsor) => (
              <img
                key={sponsor.name}
                src={sponsor.logo}
                alt={sponsor.name}
                className="h-5 sm:h-6 w-auto object-contain filter grayscale dark:invert hover:grayscale-0 dark:hover:invert-0 transition-all"
              />
            ))}
          </div>

          <div className="text-xs text-slate-500 dark:text-slate-500 text-center pt-4 border-t border-slate-200 dark:border-white/10 w-full max-w-2xl">
            © 2003–2026 Formula One World Championship Limited. APEX Predictive Intelligence Engine. All racing marks belong to their respective copyright holders.
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
