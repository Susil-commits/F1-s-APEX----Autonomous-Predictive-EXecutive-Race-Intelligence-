import React from 'react';
import { Flag, Trophy, CloudRain, Activity } from 'lucide-react';

const STAGES = [
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
];

export const HowItWorks: React.FC = () => {
  return (
    <section className="py-20 border-t border-slate-200 dark:border-white/10 bg-slate-50/50 dark:bg-[#0A0C13]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-2xl mx-auto mb-16 flex flex-col items-center gap-2">
          <span className="text-xs font-bold uppercase tracking-widest text-[#E10600]">Strategic Analysis</span>
          <h2 className="text-3xl sm:text-4xl font-extrabold uppercase tracking-tight text-slate-900 dark:text-white font-['Outfit']">
            HOW APEX CALCULATES PREDICTIONS
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            A 4-stage race day projection based strictly on real-world track conditions and driver pacing.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {STAGES.map((card) => {
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
  );
};

export default HowItWorks;
