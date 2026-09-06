import React, { useState, useEffect, useRef } from 'react';
import {
  Zap, Brain, Shield, BarChart2, ChevronRight, Play,
  ArrowRight, Activity, Clock, TrendingUp, Award, Cpu,
  Target, CheckCircle, Star, Globe, Users, Database, Lock,
} from 'lucide-react';

interface LandingPageProps {
  onEnterApp: () => void;
}

const TICKER_ITEMS = [
  { label: 'Model Accuracy', value: 'R² = 0.688', color: '#00F0FF' },
  { label: 'Temporal Holdout MAE', value: '2.37 positions', color: '#FFB800' },
  { label: 'Split-Conformal Coverage', value: '90% CI', color: '#00E676' },
  { label: 'Training Races', value: '2022–2024', color: '#E10600' },
  { label: 'Pearson Correlation', value: 'r = 0.829', color: '#00F0FF' },
  { label: 'Feature Count', value: '9 pre-race signals', color: '#FFB800' },
  { label: 'Zero Lookahead Bias', value: 'Guaranteed', color: '#00E676' },
  { label: 'Data Source', value: 'Jolpica / FastF1', color: '#E10600' },
];

const FEATURES = [
  {
    icon: Brain,
    title: 'CatBoost Gradient Boosting',
    description: 'Tournament-selected among GBR, XGBoost, and CatBoost. The winning model is retrained on historical F1 data from 2022–2024 with strict temporal holdout validation.',
    badge: 'AI / ML',
    badgeColor: 'cyan',
    accentColor: '#00F0FF',
  },
  {
    icon: Shield,
    title: 'Split-Conformal Confidence Bands',
    description: 'Mathematically guaranteed 90% coverage intervals, not heuristic ±guesses. Each prediction comes with a proven lower/upper bound on finishing position.',
    badge: 'Provably Correct',
    badgeColor: 'gold',
    accentColor: '#FFB800',
  },
  {
    icon: Zap,
    title: 'Zero Lookahead Bias',
    description: 'Every feature used for prediction — grid position, qualifying delta, rolling form, rain forecast — is strictly available before lights out. No race-day data leaks.',
    badge: 'Point-in-Time',
    badgeColor: 'red',
    accentColor: '#E10600',
  },
  {
    icon: BarChart2,
    title: 'Explainable Feature Attribution',
    description: 'Transparent breakdown of each feature\'s impact: car championship pace (58%), grid position (22%), recent driver form (10%), and more — sourced from CatBoost importances.',
    badge: 'Explainable AI',
    badgeColor: 'cyan',
    accentColor: '#00F0FF',
  },
  {
    icon: Database,
    title: 'FIA-Verified Historical Data',
    description: 'Trained on real F1 lap data via the Jolpica ergast API and FastF1. 1,359 real pre-race records across 25 circuits, 22 drivers, and 3 seasons.',
    badge: 'Real Data',
    badgeColor: 'gold',
    accentColor: '#FFB800',
  },
  {
    icon: Globe,
    title: '25 Circuit Profiles',
    description: 'Calibrated aerodynamic downforce, engine power sensitivity, and street track volatility for every circuit on the 2026 calendar — from Monaco\'s 1.00 downforce demand to Vegas\'s 0.30.',
    badge: 'Full Coverage',
    badgeColor: 'red',
    accentColor: '#E10600',
  },
];

const STATS = [
  { value: '0.688', label: 'Temporal Holdout R²', sub: 'vs. 2024 season', icon: TrendingUp, color: '#00F0FF' },
  { value: '90%', label: 'Conformal Coverage', sub: 'Mathematically guaranteed', icon: Shield, color: '#00E676' },
  { value: '2.37', label: 'Mean Abs. Error', sub: 'Positions off from truth', icon: Target, color: '#E10600' },
  { value: '1,359', label: 'Training Records', sub: 'Real F1 pre-race rows', icon: Database, color: '#FFB800' },
];

const CIRCUITS = [
  { name: 'Monaco GP', circuit: 'Circuit de Monaco', flag: '🇲🇨', downforce: 'MAXIMUM', downforceVal: 1.00 },
  { name: 'Italian GP', circuit: 'Monza', flag: '🇮🇹', downforce: 'LOW', downforceVal: 0.10 },
  { name: 'Belgian GP', circuit: 'Spa-Francorchamps', flag: '🇧🇪', downforce: 'MEDIUM', downforceVal: 0.65 },
  { name: 'British GP', circuit: 'Silverstone', flag: '🇬🇧', downforce: 'HIGH', downforceVal: 0.75 },
  { name: 'Las Vegas GP', circuit: 'Vegas Strip', flag: '🇺🇸', downforce: 'LOW', downforceVal: 0.30 },
  { name: 'Singapore GP', circuit: 'Marina Bay', flag: '🇸🇬', downforce: 'MAXIMUM', downforceVal: 0.95 },
];

const HOW_IT_WORKS = [
  { step: '01', title: 'Select Grand Prix', desc: 'Choose from the 2026 calendar. Circuit aerodynamic profile is automatically loaded.' },
  { step: '02', title: 'Choose Your Driver', desc: 'Pick from the full 2026 grid. Driver rolling form and constructor pace are pre-loaded.' },
  { step: '03', title: 'Set Race Conditions', desc: 'Override the qualifying grid slot and set the rain forecast probability for the race start.' },
  { step: '04', title: 'APEX Predicts', desc: 'CatBoost evaluates 9 pre-race features and returns a position with a 90% conformal interval.' },
];

export const LandingPage: React.FC<LandingPageProps> = ({ onEnterApp }) => {
  const [tick, setTick] = useState(0);
  const heroRef = useRef<HTMLDivElement>(null);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const t = setInterval(() => setTick(p => p + 1), 50);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    const handler = () => setScrolled(window.scrollY > 60);
    window.addEventListener('scroll', handler);
    return () => window.removeEventListener('scroll', handler);
  }, []);

  const downforceColor = (val: number) => {
    if (val >= 0.9) return '#E10600';
    if (val >= 0.65) return '#FFB800';
    if (val >= 0.4) return '#00F0FF';
    return '#00E676';
  };

  return (
    <div className="min-h-screen bg-[#060709] text-white overflow-x-hidden">

      {/* ─── NAV ─── */}
      <nav className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${scrolled ? 'glass-panel shadow-2xl shadow-black/80' : 'bg-transparent'}`}>
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <img src="/f1/f1-logo.svg" alt="Formula 1" className="h-7 w-auto object-contain" />
            <div className="h-6 w-px bg-white/10" />
            <div className="h-7 px-3 rounded bg-gradient-to-r from-[#E10600] to-[#B30000] flex items-center justify-center shadow-lg shadow-red-600/30 f1-angle">
              <span className="font-black text-xs tracking-wider text-white uppercase f1-angle-reverse font-f1">APEX PREDICTOR</span>
            </div>
          </div>
          <div className="hidden md:flex items-center gap-6 text-xs font-f1 font-semibold text-slate-400 uppercase tracking-wider">
            <a href="#features" className="hover:text-white transition-colors">Features</a>
            <a href="#how-it-works" className="hover:text-white transition-colors">How It Works</a>
            <a href="#model" className="hover:text-white transition-colors">Model</a>
          </div>
          <button
            onClick={onEnterApp}
            className="flex items-center gap-2 px-5 py-2.5 rounded-lg f1-racing-bar text-white font-f1 font-black text-xs uppercase tracking-widest shadow-lg shadow-red-900/40 hover:brightness-110 active:scale-95 transition-all"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            Launch APEX
          </button>
        </div>
      </nav>

      {/* ─── HERO ─── */}
      <section ref={heroRef} className="relative hero-bg grid-bg min-h-screen flex flex-col items-center justify-center overflow-hidden pt-20">
        {/* Red speed lines */}
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          {[...Array(6)].map((_, i) => (
            <div
              key={i}
              className="absolute h-px opacity-20"
              style={{
                background: `linear-gradient(90deg, transparent, #E10600, transparent)`,
                top: `${15 + i * 14}%`,
                left: 0, right: 0,
                animation: `speed-line ${3 + i * 0.7}s ease-out ${i * 0.4}s infinite`,
              }}
            />
          ))}
        </div>

        {/* Hero Content */}
        <div className="relative z-10 max-w-5xl mx-auto px-6 text-center flex flex-col items-center gap-8">

          {/* Top badge */}
          <div className="animate-f1-slide-up flex items-center gap-3">
            <div className="apex-badge">
              <span className="w-1.5 h-1.5 rounded-full bg-[#E10600] animate-pulse inline-block" />
              2026 F1 Season Active
            </div>
            <div className="apex-badge-cyan">
              <Activity className="w-3 h-3" />
              Live Prediction Engine
            </div>
          </div>

          {/* Main Title */}
          <div className="animate-f1-slide-up delay-100">
            <h1 className="font-f1 font-black text-5xl sm:text-7xl lg:text-8xl uppercase leading-[0.9] tracking-tight">
              <span className="text-white">F1 RACE</span>
              <br />
              <span
                className="text-[#E10600] glow-f1-red"
                style={{ WebkitTextStroke: '1px rgba(255,0,0,0.3)' }}
              >
                PREDICTOR
              </span>
            </h1>
          </div>

          {/* Subtitle */}
          <p className="animate-f1-slide-up delay-200 font-f1 text-lg sm:text-xl text-slate-300 max-w-2xl leading-relaxed">
            CatBoost-powered finishing position intelligence with{' '}
            <span className="text-[#00F0FF] font-bold">mathematically guaranteed 90% split-conformal confidence intervals</span>.
            Zero lookahead bias. FIA-verified data.
          </p>

          {/* Stat Pills */}
          <div className="animate-f1-slide-up delay-300 flex flex-wrap items-center justify-center gap-3">
            {[
              { label: 'R² = 0.688', color: '#00F0FF', icon: TrendingUp },
              { label: 'Pearson r = 0.83', color: '#00E676', icon: Activity },
              { label: 'MAE = 2.37 pos', color: '#FFB800', icon: Target },
              { label: '25 Circuits', color: '#E10600', icon: Globe },
            ].map(({ label, color, icon: Icon }) => (
              <div key={label} className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-[#0E1017]/80 border border-white/8 text-xs font-mono font-bold" style={{ color }}>
                <Icon className="w-3.5 h-3.5" />
                {label}
              </div>
            ))}
          </div>

          {/* CTA Buttons */}
          <div className="animate-f1-slide-up delay-400 flex flex-col sm:flex-row items-center gap-4">
            <button
              onClick={onEnterApp}
              className="group relative px-10 py-4 rounded-xl f1-racing-bar text-white font-f1 font-black text-base uppercase tracking-widest shadow-xl shadow-red-950/60 hover:brightness-110 active:scale-95 transition-all flex items-center gap-3"
            >
              <Play className="w-5 h-5 fill-current" />
              <span>Launch Predictor</span>
              <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              {/* Shimmer sweep */}
              <div className="absolute inset-0 rounded-xl overflow-hidden pointer-events-none">
                <div className="absolute inset-0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700 bg-gradient-to-r from-transparent via-white/15 to-transparent skew-x-12" />
              </div>
            </button>
            <a
              href="#how-it-works"
              className="px-8 py-4 rounded-xl border border-white/12 text-slate-300 font-f1 font-bold text-sm uppercase tracking-wider hover:border-white/25 hover:text-white transition-all flex items-center gap-2"
            >
              See How It Works
              <ArrowRight className="w-4 h-4" />
            </a>
          </div>

          {/* Hero bottom accent */}
          <div className="animate-f1-fade-in delay-500 w-full max-w-md red-line mt-2" />
        </div>

        {/* Scroll chevron */}
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 animate-bounce">
          <div className="w-px h-10 bg-gradient-to-b from-transparent to-[#E10600]/50" />
          <div className="w-2 h-2 border-r border-b border-[#E10600]/50 rotate-45" />
        </div>
      </section>

      {/* ─── LIVE TICKER BAR ─── */}
      <div className="ticker-bar py-2.5 overflow-hidden relative">
        <div className="animate-ticker flex gap-0 whitespace-nowrap" style={{ width: 'max-content' }}>
          {[...TICKER_ITEMS, ...TICKER_ITEMS].map((item, i) => (
            <span key={i} className="inline-flex items-center gap-2 px-6 text-xs font-mono font-bold">
              <span className="text-slate-500">·</span>
              <span className="text-slate-400 uppercase tracking-wider">{item.label}</span>
              <span style={{ color: item.color }}>{item.value}</span>
            </span>
          ))}
        </div>
      </div>

      {/* ─── STATS SECTION ─── */}
      <section id="model" className="relative py-24 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-14 flex flex-col items-center gap-3">
            <div className="apex-badge-gold">
              <Award className="w-3 h-3" />
              Model Performance
            </div>
            <h2 className="font-f1 font-black text-4xl sm:text-5xl uppercase tracking-tight text-white">
              Tested. <span className="text-[#E10600]">Validated.</span> Trusted.
            </h2>
            <p className="text-slate-400 font-f1 max-w-xl text-base">
              Strictly temporal holdout evaluation — the model has never seen 2024 race results during training.
            </p>
          </div>

          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {STATS.map(({ value, label, sub, icon: Icon, color }, i) => (
              <div
                key={label}
                className="stat-card text-center animate-f1-slide-up"
                style={{ animationDelay: `${i * 0.1}s` }}
              >
                <div className="w-10 h-10 rounded-xl flex items-center justify-center mx-auto mb-4" style={{ background: `${color}15`, border: `1px solid ${color}30` }}>
                  <Icon className="w-5 h-5" style={{ color }} />
                </div>
                <div className="font-f1 font-black text-4xl text-white mb-1" style={{ color }}>{value}</div>
                <div className="font-f1 font-bold text-sm text-white uppercase tracking-wide mb-1">{label}</div>
                <div className="text-xs text-slate-500 font-mono">{sub}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── RED DIVIDER ─── */}
      <div className="red-line mx-auto max-w-4xl" />

      {/* ─── FEATURES SECTION ─── */}
      <section id="features" className="py-24 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16 flex flex-col items-center gap-3">
            <div className="apex-badge">
              <Cpu className="w-3 h-3" />
              What Powers APEX
            </div>
            <h2 className="font-f1 font-black text-4xl sm:text-5xl uppercase tracking-tight">
              Race Intelligence<br /><span className="text-[#E10600]">By The Numbers</span>
            </h2>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
            {FEATURES.map(({ icon: Icon, title, description, badge, badgeColor, accentColor }, i) => (
              <div
                key={title}
                className="feature-card animate-f1-slide-up"
                style={{ animationDelay: `${i * 0.1}s` }}
              >
                {/* Top accent line */}
                <div className="absolute top-0 left-6 right-6 h-px" style={{ background: `linear-gradient(90deg, transparent, ${accentColor}50, transparent)` }} />

                <div className="w-11 h-11 rounded-xl flex items-center justify-center mb-5" style={{ background: `${accentColor}12`, border: `1px solid ${accentColor}25` }}>
                  <Icon className="w-5.5 h-5.5" style={{ color: accentColor, width: 22, height: 22 }} />
                </div>

                <div className={`apex-badge${badgeColor === 'cyan' ? '-cyan' : badgeColor === 'gold' ? '-gold' : ''} mb-3`} style={badgeColor === 'red' ? { borderColor: 'rgba(225,6,0,0.35)', background: 'rgba(225,6,0,0.10)', color: '#FF4040' } : {}}>
                  {badge}
                </div>

                <h3 className="font-f1 font-black text-lg text-white uppercase tracking-wide mb-3">{title}</h3>
                <p className="text-slate-400 text-sm leading-relaxed font-f1">{description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── CIRCUIT PROFILES SHOWCASE ─── */}
      <section className="py-20 px-6 relative overflow-hidden">
        {/* BG tint */}
        <div className="absolute inset-0 bg-[#080A10]/80" />
        <div className="absolute inset-0 grid-bg opacity-40" />
        <div className="relative z-10 max-w-6xl mx-auto">
          <div className="text-center mb-12 flex flex-col items-center gap-3">
            <div className="apex-badge-cyan">
              <Globe className="w-3 h-3" />
              25 Circuit Profiles
            </div>
            <h2 className="font-f1 font-black text-4xl sm:text-5xl uppercase tracking-tight">
              Every Circuit,<br /><span className="text-[#00F0FF] glow-cyan">Calibrated</span>
            </h2>
            <p className="text-slate-400 font-f1 max-w-xl">Real aerodynamic downforce, power sensitivity, and street track volatility for each venue.</p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            {CIRCUITS.map(({ name, circuit, flag, downforce, downforceVal }) => (
              <div key={name} className="f1-card p-4 flex flex-col gap-2.5 hover:scale-[1.02] transition-transform">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-500 font-mono font-bold uppercase text-[10px]">{downforce}</span>
                  <span className="text-xl">{flag}</span>
                </div>
                <h3 className="font-f1 font-black text-xs uppercase text-white leading-tight">{name}</h3>
                <p className="text-[10px] text-slate-500 font-mono">{circuit}</p>
                {/* Downforce bar */}
                <div className="mt-1">
                  <div className="text-[10px] text-slate-500 font-mono mb-1">Downforce {(downforceVal * 100).toFixed(0)}%</div>
                  <div className="h-1 rounded-full bg-[#1A1A28] overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all"
                      style={{ width: `${downforceVal * 100}%`, background: downforceColor(downforceVal) }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-8 text-center">
            <p className="text-slate-500 text-sm font-mono">
              + 19 more circuits · Americas · Hungaroring · Yas Marina · Qatar · Imola and more
            </p>
          </div>
        </div>
      </section>

      {/* ─── HOW IT WORKS ─── */}
      <section id="how-it-works" className="py-24 px-6">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-16 flex flex-col items-center gap-3">
            <div className="apex-badge">
              <Zap className="w-3 h-3" />
              The APEX Pipeline
            </div>
            <h2 className="font-f1 font-black text-4xl sm:text-5xl uppercase tracking-tight">
              Four steps to<br /><span className="text-[#E10600]">Race Prediction</span>
            </h2>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-5 relative">
            {/* Connecting line */}
            <div className="absolute top-10 left-[12.5%] right-[12.5%] h-px bg-gradient-to-r from-[#E10600]/20 via-[#E10600]/60 to-[#E10600]/20 hidden lg:block" />

            {HOW_IT_WORKS.map(({ step, title, desc }, i) => (
              <div key={step} className="flex flex-col items-center text-center gap-4 animate-f1-slide-up" style={{ animationDelay: `${i * 0.15}s` }}>
                <div className="relative">
                  <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-[#1A1A28] to-[#0E0F18] border border-[#E10600]/30 flex items-center justify-center animate-border-pulse shadow-lg shadow-red-950/30">
                    <span className="font-f1 font-black text-2xl text-[#E10600]">{step}</span>
                  </div>
                </div>
                <h3 className="font-f1 font-black text-sm text-white uppercase tracking-wide">{title}</h3>
                <p className="text-slate-400 text-xs leading-relaxed font-f1">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── TRUST / DATA INTEGRITY STRIP ─── */}
      <section className="py-16 px-6 border-y border-white/5">
        <div className="max-w-6xl mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {[
              { icon: Lock, label: 'No Lookahead Bias', desc: 'Strictly pre-race features only' },
              { icon: CheckCircle, label: 'Real Historical Data', desc: '1,359 FIA-verified rows' },
              { icon: Star, label: 'Tournament Selected', desc: 'CatBoost beat GBR & XGBoost' },
              { icon: Users, label: 'Full 2026 Grid', desc: '22 drivers, 25 circuits' },
            ].map(({ icon: Icon, label, desc }) => (
              <div key={label} className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-xl bg-[#E10600]/10 border border-[#E10600]/20 flex items-center justify-center flex-shrink-0">
                  <Icon className="w-4.5 h-4.5 text-[#E10600]" style={{ width: 18, height: 18 }} />
                </div>
                <div>
                  <div className="font-f1 font-bold text-sm text-white">{label}</div>
                  <div className="text-xs text-slate-500 font-mono mt-0.5">{desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── CTA SECTION ─── */}
      <section className="py-28 px-6 relative overflow-hidden">
        <div className="absolute inset-0 hero-bg opacity-60" />
        <div className="absolute inset-0 grid-bg opacity-30" />

        <div className="relative z-10 max-w-3xl mx-auto text-center flex flex-col items-center gap-8">
          <div className="w-20 h-1 f1-racing-bar rounded-full" />
          <h2 className="font-f1 font-black text-5xl sm:text-6xl uppercase tracking-tight leading-[0.95]">
            Ready for<br /><span className="text-[#E10600] glow-f1-red">Lights Out?</span>
          </h2>
          <p className="font-f1 text-slate-300 text-lg max-w-lg leading-relaxed">
            Run your first prediction in under 10 seconds. Select a circuit, pick a driver, and let the CatBoost model deliver a race finish with a provable confidence band.
          </p>

          <button
            onClick={onEnterApp}
            className="group relative px-12 py-5 rounded-2xl f1-racing-bar text-white font-f1 font-black text-lg uppercase tracking-widest shadow-2xl shadow-red-950/60 box-glow-red hover:brightness-110 active:scale-95 transition-all flex items-center gap-4"
          >
            <Play className="w-6 h-6 fill-current" />
            <span>Enter APEX Predictor</span>
            <ChevronRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            <div className="absolute inset-0 rounded-2xl overflow-hidden pointer-events-none">
              <div className="absolute inset-0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700 bg-gradient-to-r from-transparent via-white/15 to-transparent skew-x-12" />
            </div>
          </button>

          <div className="flex flex-wrap items-center justify-center gap-4 text-xs font-mono text-slate-500">
            <span className="flex items-center gap-1.5"><CheckCircle className="w-3 h-3 text-emerald-500" /> Free to use</span>
            <span className="flex items-center gap-1.5"><CheckCircle className="w-3 h-3 text-emerald-500" /> No account required</span>
            <span className="flex items-center gap-1.5"><CheckCircle className="w-3 h-3 text-emerald-500" /> Real model, real data</span>
          </div>
        </div>
      </section>

      {/* ─── FOOTER ─── */}
      <footer className="border-t border-white/5 py-10 px-6">
        <div className="max-w-6xl mx-auto">
          {/* Sponsor logos */}
          <div className="flex flex-wrap items-center justify-center gap-8 opacity-30 hover:opacity-60 transition-opacity mb-8">
            {['/f1/pirelli.webp', '/f1/aramco.webp', '/f1/AWS GLOBAL.webp', '/f1/dhl.webp', '/f1/qatar.webp'].map((src, i) => (
              <img key={i} src={src} alt="" className="h-5 w-auto object-contain filter grayscale" />
            ))}
          </div>
          <div className="red-line mb-6" />
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 text-[11px] font-mono text-slate-600">
            <div className="flex items-center gap-3">
              <img src="/f1/f1-logo.svg" alt="Formula 1" className="h-5 opacity-40 grayscale" />
              <span>APEX Autonomous Predictive Intelligence</span>
            </div>
            <span>© 2003–2026 Formula One World Championship Limited</span>
            <span className="text-[#E10600]/50">CatBoost · Split-Conformal · FastF1</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
