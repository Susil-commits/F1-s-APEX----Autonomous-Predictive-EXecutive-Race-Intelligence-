import React from 'react';
import { OFFICIAL_SPONSORS } from '../../modes/core/data/constants';

export const LandingFooter: React.FC = () => {
  return (
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
          © 2003–2026 Formula One World Championship Limited. APEX Formula 1 Race Intelligence. All racing marks belong to their respective copyright holders.
        </div>
      </div>
    </footer>
  );
};

export default LandingFooter;
