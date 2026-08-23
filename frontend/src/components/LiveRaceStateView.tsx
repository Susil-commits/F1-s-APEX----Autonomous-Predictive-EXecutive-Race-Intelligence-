import React from 'react';
import { TimingTower } from './TimingTower';
import { TrackMap } from './TrackMap';
import { TelemetryCharts } from './TelemetryCharts';
import { DriverBattleRadar } from './DriverBattleRadar';
import { MiniSectorTimingGrid } from './MiniSectorTimingGrid';
import { UndercutThreatMatrix } from './UndercutThreatMatrix';
import { Activity, Compass, Flame, ShieldAlert } from 'lucide-react';

export const LiveRaceStateView: React.FC = () => {
  return (
    <div className="space-y-4">
      {/* Top Grid: Timing Tower + Track Map + Driver Battle Radar */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Left Column: Timing Tower (4 cols) */}
        <div className="lg:col-span-4 h-full">
          <TimingTower />
        </div>

        {/* Center & Right Columns: 2D/3D Track Map & Live Battle (8 cols) */}
        <div className="lg:col-span-8 flex flex-col gap-4">
          <div className="bg-[#121622] border border-[#20273B] rounded-xl p-4 shadow-lg min-h-[380px] flex flex-col">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-mono font-bold text-slate-300 flex items-center gap-1.5 uppercase">
                <Compass className="w-4 h-4 text-cyan-400" />
                <span>Live Digital Twin Track Coordinates</span>
              </span>
            </div>
            <div className="flex-1 w-full relative rounded-lg overflow-hidden border border-[#1A2234]">
              <TrackMap />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <DriverBattleRadar />
            <UndercutThreatMatrix />
          </div>
        </div>
      </div>

      {/* Mini-Sectors & Live Telemetry Telemetry Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        <div className="lg:col-span-4">
          <MiniSectorTimingGrid />
        </div>
        <div className="lg:col-span-8">
          <TelemetryCharts />
        </div>
      </div>
    </div>
  );
};
