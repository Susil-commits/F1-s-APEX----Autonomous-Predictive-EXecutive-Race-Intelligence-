import React, { useState } from 'react';
import { LeftRail, PitWallZone } from './LeftRail';
import { TimingTower } from '../../components/TimingTower';
import { MiniSectorTimingGrid } from '../../components/MiniSectorTimingGrid';
import { TrackMap } from '../../components/TrackMap';
import { LinearTrackRibbon } from '../../components/LinearTrackRibbon';
import { StrategyCard } from '../../components/StrategyCard';
import { CounterfactualLabView } from '../../components/CounterfactualLabView';
import { MonteCarloStrategySim } from '../../components/MonteCarloStrategySim';
import { PitStrategyIsochroneMatrix } from '../../components/PitStrategyIsochroneMatrix';
import { UndercutThreatMatrix } from '../../components/UndercutThreatMatrix';
import { StintStrategyPlanner } from '../../components/StintStrategyPlanner';
import { DQNPolicyVisualizer } from '../../components/DQNPolicyVisualizer';
import { TyreIntelligenceView } from '../../components/TyreIntelligenceView';
import { TyreThermodynamicsView } from '../../components/TyreThermodynamicsView';
import { WeatherIntelligenceView } from '../../components/WeatherIntelligenceView';
import { OpponentIntelligenceView } from '../../components/OpponentIntelligenceView';
import { DriverIntelligenceView } from '../../components/DriverIntelligenceView';
import { VehicleHealthView } from '../../components/VehicleHealthView';
import { SensorAnomalyDetector } from '../../components/SensorAnomalyDetector';
import { ExplainabilityPanel } from '../../components/ExplainabilityPanel';
import { SHAPFeatureWaterfall } from '../../components/SHAPFeatureWaterfall';
import { DataLineageView } from '../../components/DataLineageView';
import { AblationStudyView } from '../../components/AblationStudyView';
import { ErrorAnalysisView } from '../../components/ErrorAnalysisView';
import { AgentTraceView } from '../../components/AgentTraceView';
import { RadioCommsHub } from '../../components/RadioCommsHub';
import { AIPitWallCopilot } from '../../components/AIPitWallCopilot';
import { RaceHistoryQA } from '../../components/RaceHistoryQA';
import { RaceEventLogViewer } from '../../components/RaceEventLogViewer';
import { HeroDecisionBar } from '../../components/HeroDecisionBar';

export const PitWallMode: React.FC = () => {
  const [activeZone, setActiveZone] = useState<PitWallZone>('timing');

  return (
    <div className="flex flex-1 w-full min-h-[calc(100vh-140px)] rounded-xl overflow-hidden border border-[#1F2432] bg-[#08090C]">
      {/* Left Rail Sidebar Navigation */}
      <LeftRail activeZone={activeZone} onSelectZone={setActiveZone} />

      {/* Main Pit-Wall Workspace Canvas */}
      <div className="flex-1 flex flex-col p-4 overflow-y-auto gap-4">
        {/* Prominent Decision Intelligence Bar */}
        <HeroDecisionBar />

        {/* ========================================================================= */}
        {/* ZONE 1: TIMING TOWER & TRACK MAP */}
        {/* ========================================================================= */}
        {activeZone === 'timing' && (
          <div className="flex flex-col gap-4">
            <LinearTrackRibbon />
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
              <div className="lg:col-span-5 flex flex-col gap-4">
                <div className="border-status-telemetry rounded-xl overflow-hidden">
                  <TimingTower />
                </div>
                <div className="border-status-nominal rounded-xl overflow-hidden">
                  <MiniSectorTimingGrid />
                </div>
              </div>
              <div className="lg:col-span-7 flex flex-col gap-4">
                <div className="border-status-telemetry rounded-xl overflow-hidden">
                  <TrackMap />
                </div>
                <div className="border-status-caution rounded-xl overflow-hidden">
                  <RaceEventLogViewer />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* ZONE 2: STRATEGY ROOM */}
        {/* ========================================================================= */}
        {activeZone === 'strategy' && (
          <div className="flex flex-col gap-4">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
              <div className="lg:col-span-4 flex flex-col gap-4">
                <div className="border-status-alert rounded-xl overflow-hidden">
                  <StrategyCard />
                </div>
                <div className="border-status-telemetry rounded-xl overflow-hidden">
                  <DQNPolicyVisualizer />
                </div>
              </div>
              <div className="lg:col-span-8 flex flex-col gap-4">
                <div className="border-status-nominal rounded-xl overflow-hidden">
                  <CounterfactualLabView />
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="border-status-telemetry rounded-xl overflow-hidden">
                    <PitStrategyIsochroneMatrix />
                  </div>
                  <div className="border-status-alert rounded-xl overflow-hidden">
                    <UndercutThreatMatrix />
                  </div>
                </div>
                <div className="border-status-telemetry rounded-xl overflow-hidden">
                  <MonteCarloStrategySim />
                </div>
                <div className="border-status-nominal rounded-xl overflow-hidden">
                  <StintStrategyPlanner />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* ZONE 3: INTELLIGENCE */}
        {/* ========================================================================= */}
        {activeZone === 'intelligence' && (
          <div className="flex flex-col gap-4">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
              <div className="lg:col-span-6 flex flex-col gap-4">
                <div className="border-status-alert rounded-xl overflow-hidden">
                  <TyreIntelligenceView />
                </div>
                <div className="border-status-caution rounded-xl overflow-hidden">
                  <TyreThermodynamicsView />
                </div>
                <div className="border-status-telemetry rounded-xl overflow-hidden">
                  <SensorAnomalyDetector />
                </div>
              </div>
              <div className="lg:col-span-6 flex flex-col gap-4">
                <div className="border-status-telemetry rounded-xl overflow-hidden">
                  <WeatherIntelligenceView />
                </div>
                <div className="border-status-nominal rounded-xl overflow-hidden">
                  <OpponentIntelligenceView />
                </div>
                <div className="border-status-telemetry rounded-xl overflow-hidden">
                  <DriverIntelligenceView />
                </div>
                <div className="border-status-alert rounded-xl overflow-hidden">
                  <VehicleHealthView />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* ZONE 4: EXPLAINABILITY & TRUST */}
        {/* ========================================================================= */}
        {activeZone === 'explainability' && (
          <div className="flex flex-col gap-4">
            <div className="border-status-telemetry rounded-xl overflow-hidden">
              <ExplainabilityPanel />
            </div>
            <div className="border-status-nominal rounded-xl overflow-hidden">
              <SHAPFeatureWaterfall />
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div className="border-status-telemetry rounded-xl overflow-hidden">
                <DataLineageView />
              </div>
              <div className="border-status-caution rounded-xl overflow-hidden">
                <AblationStudyView />
              </div>
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div className="border-status-alert rounded-xl overflow-hidden">
                <ErrorAnalysisView />
              </div>
              <div className="border-status-telemetry rounded-xl overflow-hidden">
                <AgentTraceView />
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* ZONE 5: RACE OPS & COMMS */}
        {/* ========================================================================= */}
        {activeZone === 'race_ops' && (
          <div className="flex flex-col gap-4">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
              <div className="lg:col-span-7 flex flex-col gap-4">
                <div className="border-status-telemetry rounded-xl overflow-hidden">
                  <RadioCommsHub />
                </div>
                <div className="border-status-alert rounded-xl overflow-hidden">
                  <AIPitWallCopilot />
                </div>
              </div>
              <div className="lg:col-span-5 flex flex-col gap-4">
                <div className="border-status-nominal rounded-xl overflow-hidden">
                  <RaceHistoryQA />
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
