import React, { useState } from 'react';
import { useRaceStore } from '../store/raceStore';
import { FileText, Download, Search, Radio, Filter, ShieldAlert, CloudRain, Disc } from 'lucide-react';
import { RaceEvent } from '../types/race';

export const RaceEventLogViewer: React.FC = () => {
  const { raceState } = useRaceStore();
  const [filterType, setFilterType] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  if (!raceState) return null;

  const events = raceState.events_log || [];

  const filteredEvents = events.filter((ev: RaceEvent) => {
    const matchesSearch =
      ev.message.toLowerCase().includes(searchQuery.toLowerCase()) ||
      ev.event_type.toLowerCase().includes(searchQuery.toLowerCase());

    if (!matchesSearch) return false;

    if (filterType === 'PIT') return ev.event_type.includes('PIT');
    if (filterType === 'SAFETY_CAR') return ev.event_type.includes('SAFETY') || ev.event_type.includes('VSC');
    if (filterType === 'WEATHER') return ev.event_type.includes('WEATHER') || ev.event_type.includes('RAIN');
    return true;
  });

  const exportCSV = () => {
    const headers = ['Lap', 'Timestamp_S', 'Event_Type', 'Message'];
    const rows = events.map((ev) => [
      ev.lap,
      ev.timestamp_s,
      `"${ev.event_type}"`,
      `"${ev.message.replace(/"/g, '""')}"`,
    ]);

    const csvContent =
      'data:text/csv;charset=utf-8,' +
      [headers.join(','), ...rows.map((e) => e.join(','))].join('\n');

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `apex_race_events_${raceState.race_id}.csv`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  };

  return (
    <div className="glass-panel rounded-xl p-5 flex flex-col border border-apex-border shadow-2xl font-mono text-xs">
      {/* Header & Export Actions */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2.5">
          <FileText className="w-5 h-5 text-apex-cyan animate-pulse" />
          <div>
            <h3 className="text-xs font-black uppercase tracking-widest text-slate-200">
              Race Control Event Telemetry Logger
            </h3>
            <p className="text-[10.5px] text-slate-400 font-sans">
              Chronological log of incidents, pit calls, weather transitions, and strategic decisions
            </p>
          </div>
        </div>

        <button
          onClick={exportCSV}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-sans font-semibold text-xs transition-all active:scale-95 shadow"
        >
          <Download className="w-4 h-4 text-cyan-400" />
          <span>Export Event Log (.CSV)</span>
        </button>
      </div>

      {/* Filter Tabs & Search Bar */}
      <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
        <div className="flex items-center bg-slate-950/80 p-0.5 rounded-lg border border-slate-800 text-[10px]">
          {['ALL', 'PIT', 'SAFETY_CAR', 'WEATHER'].map((t) => (
            <button
              key={t}
              onClick={() => setFilterType(t)}
              className={`px-2.5 py-1 rounded transition-all font-bold ${
                filterType === t
                  ? 'bg-cyan-500 text-black shadow'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {t.replace('_', ' ')}
            </button>
          ))}
        </div>

        <div className="relative">
          <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search event log..."
            className="bg-slate-950 border border-slate-800 rounded-lg pl-8 pr-3 py-1 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500 font-sans"
          />
        </div>
      </div>

      {/* Events List */}
      <div className="space-y-1.5 overflow-y-auto max-h-[280px] pr-1">
        {filteredEvents.length > 0 ? (
          filteredEvents
            .slice()
            .reverse()
            .map((ev, idx) => (
              <div
                key={idx}
                className="p-2.5 rounded-lg bg-slate-900/70 border border-slate-800/80 flex items-start gap-3 text-[11.5px] font-sans"
              >
                <span className="font-mono text-slate-400 font-bold shrink-0">
                  [Lap {ev.lap}]
                </span>
                <span className="font-mono text-cyan-400 font-bold uppercase text-[10px] shrink-0 px-1.5 py-0.2 rounded bg-cyan-950/80 border border-cyan-800/40">
                  {ev.event_type}
                </span>
                <span className="text-slate-200 flex-1">{ev.message}</span>
              </div>
            ))
        ) : (
          <div className="text-center text-slate-500 py-6 italic font-sans">
            No events found matching your filter criteria.
          </div>
        )}
      </div>
    </div>
  );
};
