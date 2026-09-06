import React from 'react';
import { ChevronRight } from 'lucide-react';
import { GRAND_PRIX_LIST } from '../../modes/core/data/constants';

interface CalendarPreviewProps {
  onEnterApp: () => void;
}

export const CalendarPreview: React.FC<CalendarPreviewProps> = ({ onEnterApp }) => {
  return (
    <section id="calendar" className="py-20 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div className="flex flex-col md:flex-row md:items-end justify-between mb-10 gap-4">
        <div>
          <span className="text-xs font-bold uppercase tracking-widest text-[#E10600]">2026 World Tour</span>
          <h2 className="text-3xl sm:text-4xl font-extrabold uppercase tracking-tight text-slate-900 dark:text-white font-['Outfit']">
            FEATURED VENUES
          </h2>
        </div>
        <button
          type="button"
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
            onClick={onEnterApp}
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
  );
};

export default CalendarPreview;
