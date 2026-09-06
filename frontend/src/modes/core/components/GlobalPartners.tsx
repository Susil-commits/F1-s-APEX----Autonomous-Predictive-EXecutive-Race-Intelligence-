import React from 'react';
import { OfficialSponsor } from '../data/constants';

export interface GlobalPartnersProps {
  sponsors: OfficialSponsor[];
}

export const GlobalPartners: React.FC<GlobalPartnersProps> = ({ sponsors }) => {
  return (
    <div className="w-full pt-8 pb-4 border-t border-[#1F2230] flex flex-col items-center gap-4">
      <span className="text-[10px] font-f1 font-bold uppercase tracking-widest text-slate-400">
        Formula 1 Global Partners
      </span>

      <div className="flex flex-wrap items-center justify-center gap-6 sm:gap-10 opacity-70 hover:opacity-100 transition-opacity">
        {sponsors.map((s) => (
          <img
            key={s.name}
            src={s.logo}
            alt={s.name}
            className="h-5 sm:h-6 w-auto object-contain filter grayscale hover:grayscale-0 transition-all duration-200"
          />
        ))}
      </div>

      <p className="text-[10px] font-f1 text-slate-400 text-center mt-2">
        © 2003–2026 Formula One World Championship Limited. APEX Autonomous Predictive Intelligence.
      </p>
    </div>
  );
};
