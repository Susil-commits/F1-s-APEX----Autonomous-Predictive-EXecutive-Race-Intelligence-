import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { TimingTower } from './components/TimingTower';
import { TrackMap } from './components/TrackMap';
import { TelemetryCharts } from './components/TelemetryCharts';
import { StrategyCard } from './components/StrategyCard';
import { ExplainabilityPanel } from './components/ExplainabilityPanel';
import { CounterfactualView } from './components/CounterfactualView';
import { RaceControls } from './components/RaceControls';
import { DriverTelemetryModal } from './components/DriverTelemetryModal';
import { PitRejoinRadar } from './components/PitRejoinRadar';
import { TelemetryLab } from './components/TelemetryLab';
import { StrategySandbox } from './components/StrategySandbox';
import { StintStrategyPlanner } from './components/StintStrategyPlanner';
import { DriverBattleRadar } from './components/DriverBattleRadar';
import { WeatherDopplerRadar } from './components/WeatherDopplerRadar';
import { AIPitWallCopilot } from './components/AIPitWallCopilot';
import { PostRaceDebriefModal } from './components/PostRaceDebriefModal';
import { RaceTimeTravelDVR } from './components/RaceTimeTravelDVR';
import { DQNPolicyVisualizer } from './components/DQNPolicyVisualizer';
import { DualDriverTelemetryOverlay } from './components/DualDriverTelemetryOverlay';
import { PitStopReactionSim } from './components/PitStopReactionSim';
import { MonteCarloStrategySim } from './components/MonteCarloStrategySim';
import { MiniSectorTimingGrid } from './components/MiniSectorTimingGrid';
import { ChampionshipStandings } from './components/ChampionshipStandings';
import { RadioWaveformVisualizer } from './components/RadioWaveformVisualizer';
import { ChassisSetupTuner } from './components/ChassisSetupTuner';
import { RaceEventLogViewer } from './components/RaceEventLogViewer';
import { SHAPFeatureWaterfall } from './components/SHAPFeatureWaterfall';
import { LapTimeDeltaTDecomposition } from './components/LapTimeDeltaTDecomposition';
import { PitStrategyIsochroneMatrix } from './components/PitStrategyIsochroneMatrix';
import { UndercutThreatMatrix } from './components/UndercutThreatMatrix';
import { LiveScenarioInjector } from './components/LiveScenarioInjector';
import { BenchmarkComparisonModal } from './components/BenchmarkComparisonModal';
import { RaceHistoryQA } from './components/RaceHistoryQA';
import { TyreIntelligenceView } from './components/TyreIntelligenceView';
import { WeatherIntelligenceView } from './components/WeatherIntelligenceView';
import { OpponentIntelligenceView } from './components/OpponentIntelligenceView';
import { DriverIntelligenceView } from './components/DriverIntelligenceView';
import { VehicleHealthView } from './components/VehicleHealthView';
import { HistoricalReplayView } from './components/HistoricalReplayView';
import { ChampionshipTournamentView } from './components/ChampionshipTournamentView';
import { SystemHealthView } from './components/SystemHealthView';
import { PitWallConsensusModal } from './components/PitWallConsensusModal';
import { MCTSVisualizer } from './components/MCTSVisualizer';
import { AerodynamicWakeRadar } from './components/AerodynamicWakeRadar';
import { WindTunnelCFDLab } from './components/WindTunnelCFDLab';
import { TyreThermodynamicsView } from './components/TyreThermodynamicsView';
import { GhostCarTelemetryOverlay } from './components/GhostCarTelemetryOverlay';
import { PitStop3DCrewLab } from './components/PitStop3DCrewLab';
import { SensorAnomalyDetector } from './components/SensorAnomalyDetector';
import { BroadcastDirectorTV } from './components/BroadcastDirectorTV';
import { SteeringWheelDDU } from './components/SteeringWheelDDU';
import { FastF1TelemetryDuel } from './components/FastF1TelemetryDuel';
import { PitWallStrategyWhiteboard } from './components/PitWallStrategyWhiteboard';
import { StewardInvestigationRoom } from './components/StewardInvestigationRoom';
import { DriverBiometricCockpit } from './components/DriverBiometricCockpit';
import { HistoricalRadioSoundboard } from './components/HistoricalRadioSoundboard';
import { PressConferenceStudio } from './components/PressConferenceStudio';
import { AeroelasticWingFlexLab } from './components/AeroelasticWingFlexLab';
import { FIAInspectionBay } from './components/FIAInspectionBay';
import { SatelliteDopplerRadar } from './components/SatelliteDopplerRadar';
import { HelmetVisorHUD } from './components/HelmetVisorHUD';
import { ChassisSuspensionLab } from './components/ChassisSuspensionLab';
import { DriverMarketHub } from './components/DriverMarketHub';
import { StereoscopicVRCockpit } from './components/StereoscopicVRCockpit';
import { LiDARSurfaceScanner } from './components/LiDARSurfaceScanner';
import { EngineDynoCombustionLab } from './components/EngineDynoCombustionLab';
import { SafetyCarMissionControl } from './components/SafetyCarMissionControl';
import { HallOfFameTrophyRoom } from './components/HallOfFameTrophyRoom';
import { RedFlagStrategyMatrix } from './components/RedFlagStrategyMatrix';
import { SteeringCustomizationLab } from './components/SteeringCustomizationLab';
import { TrackMarshallLightPanels } from './components/TrackMarshallLightPanels';
import { AtmosphericSoundingLab } from './components/AtmosphericSoundingLab';
import { DriverCoolingSuitCockpit } from './components/DriverCoolingSuitCockpit';
import { CFDSupercomputerQueue } from './components/CFDSupercomputerQueue';
import { OilSpectroscopyForensics } from './components/OilSpectroscopyForensics';
import { StewardHearingTribunal } from './components/StewardHearingTribunal';
import { CarbonCompositeAutoclave } from './components/CarbonCompositeAutoclave';
import { TyreBlanketInductionRig } from './components/TyreBlanketInductionRig';
import { RadioStressClassifier } from './components/RadioStressClassifier';
import { GearboxShiftDynamicsLab } from './components/GearboxShiftDynamicsLab';
import { BrakePyrometryLab } from './components/BrakePyrometryLab';
import { RadioCommsHub } from './components/RadioCommsHub';
import { CommandPalette } from './components/CommandPalette';
import { useRaceStore } from './store/raceStore';
import { audioEngine } from './utils/audioEngine';
import {
  Radio,
  Terminal,
  Brain,
  Trophy,
  Bot,
  Timer,
  Layers,
  Dices,
  Wrench,
  FileText,
  Volume2,
  VolumeX,
  Zap,
  BarChart2,
  Users,
  X,
  Wind,
  Command,
} from 'lucide-react';

export const App: React.FC = () => {
  const { raceState, activeTab, inspectedCar, showDebriefModal, setShowDebriefModal } =
    useRaceStore();
  const [showCopilotModal, setShowCopilotModal] = useState<boolean>(false);
  const [showConsensusModal, setShowConsensusModal] = useState<boolean>(false);
  const [showQAModal, setShowQAModal] = useState<boolean>(false);
  const [showPitSimModal, setShowPitSimModal] = useState<boolean>(false);
  const [showStandingsModal, setShowStandingsModal] = useState<boolean>(false);
  const [showAeroTunerModal, setShowAeroTunerModal] = useState<boolean>(false);
  const [showBenchmarkModal, setShowBenchmarkModal] = useState<boolean>(false);
  const [showCommandPalette, setShowCommandPalette] = useState<boolean>(false);
  const [showRadioHubModal, setShowRadioHubModal] = useState<boolean>(false);
  const [engineAudioActive, setEngineAudioActive] = useState<boolean>(false);

  // Global Ctrl+K / Cmd+K listener for Command Palette
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        setShowCommandPalette((prev) => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);



  const events = raceState?.events_log || [];

  const toggleEngineSynth = () => {
    const active = audioEngine.toggleEngineSound(11500);
    setEngineAudioActive(active);
  };

  return (
    <div className="min-h-screen bg-apex-bg text-slate-100 flex flex-col selection:bg-apex-cyan selection:text-black relative">
      {/* Top Mission Control Header */}
      <Header />

      {/* Main Grid Workspace */}
      <main className="flex-1 p-4 max-w-[1920px] w-full mx-auto flex flex-col gap-4">
        {/* Top Control Bar & Time-Travel DVR Scrubber */}
        <div className="flex flex-col gap-2">
          <RaceControls />

          {/* Time-Travel DVR Bar */}
          <RaceTimeTravelDVR />

            {/* Quick Bar Action Buttons & Radio Waveform */}
          <div className="flex flex-wrap items-center justify-between gap-2 px-1 text-xs">
            <div className="flex flex-wrap items-center gap-2">
              <button
                onClick={() => setShowCommandPalette(true)}
                className="flex items-center gap-1.5 px-3 py-1 rounded bg-[#12151E] hover:bg-[#1A1F2C] text-white border border-[#2A3042] font-bold transition-all active:scale-95 shadow-sm hover:border-[#E10600]"
              >
                <Command className="w-3.5 h-3.5 text-[#E10600]" />
                <span>Command Palette</span>
                <span className="text-[10px] px-1 py-0.2 rounded bg-black text-slate-400 border border-slate-800">Ctrl+K</span>
              </button>

              <button
                onClick={() => setShowRadioHubModal(true)}
                className="flex items-center gap-1.5 px-3 py-1 rounded bg-red-950/80 hover:bg-red-900 text-white border border-red-700/80 font-bold transition-all active:scale-95 shadow-sm shadow-red-900/40"
              >
                <Radio className="w-3.5 h-3.5 text-white animate-pulse" />
                <span>Neural Pit Radio</span>
              </button>

              <button
                onClick={() => setShowConsensusModal(true)}
                className="flex items-center gap-1.5 px-3 py-1 rounded bg-[#12151E] hover:bg-[#1A1F2C] text-white border border-[#2A3042] font-bold transition-all active:scale-95 shadow-sm hover:border-[#E10600]"
              >
                <Users className="w-3.5 h-3.5 text-emerald-400" />
                <span>Pit Wall 5-Agent Consensus</span>
              </button>

              <button
                onClick={() => setShowQAModal(true)}
                className="flex items-center gap-1.5 px-3 py-1 rounded bg-[#12151E] hover:bg-[#1A1F2C] text-white border border-[#2A3042] font-bold transition-all active:scale-95 shadow-sm hover:border-[#E10600]"
              >
                <Brain className="w-3.5 h-3.5 text-[#E10600]" />
                <span>RAG Race Debrief</span>
              </button>

              <button
                onClick={() => setShowBenchmarkModal(true)}
                className="flex items-center gap-1.5 px-3 py-1 rounded bg-[#12151E] hover:bg-[#1A1F2C] text-white border border-[#2A3042] font-bold transition-all active:scale-95 shadow-sm hover:border-[#E10600]"
              >
                <BarChart2 className="w-3.5 h-3.5 text-purple-400" />
                <span>Strategy Benchmarks</span>
              </button>

              <button
                onClick={() => setShowCopilotModal(!showCopilotModal)}
                className="flex items-center gap-1.5 px-3 py-1 rounded bg-[#12151E] hover:bg-[#1A1F2C] text-white border border-[#2A3042] font-bold transition-all active:scale-95 shadow-sm hover:border-[#E10600]"
              >
                <Bot className="w-3.5 h-3.5 text-[#E10600]" />
                <span>AI Strategist Copilot</span>
              </button>

              <button
                onClick={() => setShowAeroTunerModal(true)}
                className="flex items-center gap-1.5 px-3 py-1 rounded bg-[#12151E] hover:bg-[#1A1F2C] text-white border border-[#2A3042] font-bold transition-all active:scale-95 shadow-sm hover:border-[#E10600]"
              >
                <Wrench className="w-3.5 h-3.5 text-blue-400" />
                <span>Chassis Aero Tuner</span>
              </button>

              <button
                onClick={() => setShowPitSimModal(true)}
                className="flex items-center gap-1.5 px-3 py-1 rounded bg-[#12151E] hover:bg-[#1A1F2C] text-white border border-[#2A3042] font-bold transition-all active:scale-95 shadow-sm hover:border-[#E10600]"
              >
                <Timer className="w-3.5 h-3.5 text-emerald-400" />
                <span>Pit Stop Reaction Drill</span>
              </button>

              <button
                onClick={() => setShowStandingsModal(true)}
                className="flex items-center gap-1.5 px-3 py-1 rounded bg-[#12151E] hover:bg-[#1A1F2C] text-white border border-[#2A3042] font-bold transition-all active:scale-95 shadow-sm hover:border-[#E10600]"
              >
                <Trophy className="w-3.5 h-3.5 text-amber-400" />
                <span>Live Standings</span>
              </button>

              <button
                onClick={() => setShowDebriefModal(true)}
                className="flex items-center gap-1.5 px-3 py-1 rounded bg-[#12151E] hover:bg-[#1A1F2C] text-white border border-[#2A3042] font-bold transition-all active:scale-95 shadow-sm hover:border-[#E10600]"
              >
                <Trophy className="w-3.5 h-3.5 text-yellow-400" />
                <span>Podium Debrief</span>
              </button>

              <button
                onClick={toggleEngineSynth}
                className={`flex items-center gap-1 px-2.5 py-1 rounded border text-[11px] font-mono font-bold transition-all active:scale-95 ${
                  engineAudioActive
                    ? 'bg-[#E10600] text-white border-white shadow-md shadow-red-600/40'
                    : 'bg-[#12151E] text-slate-300 border-[#2A3042] hover:text-white hover:border-[#E10600]'
                }`}
                title="Toggle V6 Turbo Hybrid Audio Synthesizer"
              >
                {engineAudioActive ? <Volume2 className="w-3 h-3" /> : <VolumeX className="w-3 h-3" />}
                <span>V6 AUDIO</span>
              </button>
            </div>

            <div className="flex items-center gap-3">
              <RadioWaveformVisualizer />
            </div>
          </div>
        </div>

        {/* Tab 1: Tactical Pit Wall Command Center & 3D Twin */}
        {activeTab === 'tactical' && (
          <div className="flex flex-col gap-4 flex-1">
            {/* Top Tactical Row: Timing Tower + 3D Track Map + Real-Time Telemetry */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
              {/* Timing Tower (Left 3 cols) */}
              <div className="lg:col-span-3">
                <TimingTower />
              </div>

              {/* Vector Circuit Geometry & 3D Spatial Digital Twin (Center 6 cols) */}
              <div className="lg:col-span-6 flex flex-col gap-4">
                <TrackMap />
                <TelemetryCharts />
              </div>

              {/* AI Strategic Intelligence & Copilot (Right 3 cols) */}
              <div className="lg:col-span-3 flex flex-col gap-4">
                <StrategyCard />
                <ExplainabilityPanel />
                <LiveScenarioInjector />
                <CounterfactualView />
              </div>
            </div>

            {/* Middle Row: Radar & Pit Windows */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <PitRejoinRadar />
              <DriverBattleRadar />
              <WeatherDopplerRadar />
            </div>

            {/* Competitor Undercut Threat Matrix */}
            <UndercutThreatMatrix />

            {/* Micro-Sector Timing Grid */}
            <MiniSectorTimingGrid />

            {/* Race Event Logger */}
            <RaceEventLogViewer />
          </div>
        )}

        {/* Tab 2: Strategy Center & Stint Planner */}
        {activeTab === 'strategy_center' && (
          <div className="flex flex-col gap-4 flex-1">
            <StintStrategyPlanner />
            <MonteCarloStrategySim />
            <PitStrategyIsochroneMatrix />
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
              <div className="lg:col-span-6">
                <StrategyCard />
              </div>
              <div className="lg:col-span-6">
                <PitStopReactionSim />
              </div>
            </div>
          </div>
        )}

        {/* Tab: FIA Steering Wheel Digital Dash Unit (DDU) */}
        {activeTab === 'steering_ddu' && (
          <div className="flex flex-col gap-4 flex-1">
            <SteeringWheelDDU />
            <TrackMap />
          </div>
        )}

        {/* Tab: Driver Radio Voice Acoustic Stress & Emotion AI */}
        {activeTab === 'radio_stress' && (
          <div className="flex flex-col gap-4 flex-1">
            <RadioStressClassifier />
            <RadioCommsHub />
          </div>
        )}

        {/* Tab: Seamless Shift Gearbox Barrel & Dog Ring Lab */}
        {activeTab === 'gearbox_lab' && (
          <div className="flex flex-col gap-4 flex-1">
            <GearboxShiftDynamicsLab />
          </div>
        )}

        {/* Tab: Brembo Carbon Brake Rotor Pyrometry & Ducts */}
        {activeTab === 'brake_pyrometry' && (
          <div className="flex flex-col gap-4 flex-1">
            <BrakePyrometryLab />
          </div>
        )}

        {/* Tab: FIA Steward Hearing & Disciplinary Appeal Tribunal */}
        {activeTab === 'steward_tribunal' && (
          <div className="flex flex-col gap-4 flex-1">
            <StewardHearingTribunal />
            <StewardInvestigationRoom />
          </div>
        )}

        {/* Tab: Carbon Composite Autoclave & Crash Sled Rig */}
        {activeTab === 'carbon_autoclave' && (
          <div className="flex flex-col gap-4 flex-1">
            <CarbonCompositeAutoclave />
          </div>
        )}

        {/* Tab: Tyre Blanket Induction Heating & Cold Pressure Rig */}
        {activeTab === 'tyre_blankets' && (
          <div className="flex flex-col gap-4 flex-1">
            <TyreBlanketInductionRig />
            <TyreThermodynamicsView />
          </div>
        )}

        {/* Tab: Driver Thermal Heatmap & Liquid Cooling Suit */}
        {activeTab === 'cooling_suit' && (
          <div className="flex flex-col gap-4 flex-1">
            <DriverCoolingSuitCockpit />
          </div>
        )}

        {/* Tab: Paddock Factory Supercomputer CFD Cloud Queue */}
        {activeTab === 'cfd_queue' && (
          <div className="flex flex-col gap-4 flex-1">
            <CFDSupercomputerQueue />
            <WindTunnelCFDLab />
          </div>
        )}

        {/* Tab: Engine Oil Chemical Spectroscopy & Forensics */}
        {activeTab === 'oil_forensics' && (
          <div className="flex flex-col gap-4 flex-1">
            <OilSpectroscopyForensics />
          </div>
        )}

        {/* Tab: Driver Steering Wheel Rotary & Paddle Lab */}
        {activeTab === 'steering_custom' && (
          <div className="flex flex-col gap-4 flex-1">
            <SteeringCustomizationLab />
            <SteeringWheelDDU />
          </div>
        )}

        {/* Tab: Track Marshall Electronic LED Light Panels Matrix */}
        {activeTab === 'marshall_panels' && (
          <div className="flex flex-col gap-4 flex-1">
            <TrackMarshallLightPanels />
            <TrackMap />
          </div>
        )}

        {/* Tab: Weather Balloon Atmospheric Sounding & Barometric Lab */}
        {activeTab === 'atmospheric_lab' && (
          <div className="flex flex-col gap-4 flex-1">
            <AtmosphericSoundingLab />
          </div>
        )}

        {/* Tab: FIA Safety Car & VSC Mission Control */}
        {activeTab === 'safety_car_control' && (
          <div className="flex flex-col gap-4 flex-1">
            <SafetyCarMissionControl />
            <TrackMap />
          </div>
        )}

        {/* Tab: Formula 1 Championship Trophy Cabinet & Hall of Fame */}
        {activeTab === 'trophy_room' && (
          <div className="flex flex-col gap-4 flex-1">
            <HallOfFameTrophyRoom />
          </div>
        )}

        {/* Tab: Emergency Red Flag Free Tyre Strategy Matrix */}
        {activeTab === 'red_flag_matrix' && (
          <div className="flex flex-col gap-4 flex-1">
            <RedFlagStrategyMatrix />
          </div>
        )}

        {/* Tab: WebXR Stereoscopic 3D VR Cockpit */}
        {activeTab === 'vr_cockpit' && (
          <div className="flex flex-col gap-4 flex-1">
            <StereoscopicVRCockpit />
          </div>
        )}

        {/* Tab: LiDAR 3D Laser Track Surface Scanner */}
        {activeTab === 'lidar_scanner' && (
          <div className="flex flex-col gap-4 flex-1">
            <LiDARSurfaceScanner />
          </div>
        )}

        {/* Tab: Engine Dyno & 100% E-Fuel Combustion Lab */}
        {activeTab === 'engine_dyno' && (
          <div className="flex flex-col gap-4 flex-1">
            <EngineDynoCombustionLab />
          </div>
        )}

        {/* Tab: Driver In-Helmet Visor Tear-Off & Rain HUD */}
        {activeTab === 'helmet_visor' && (
          <div className="flex flex-col gap-4 flex-1">
            <HelmetVisorHUD />
            <TrackMap />
          </div>
        )}

        {/* Tab: Chassis Suspension Kinematics & Venturi Lab */}
        {activeTab === 'suspension_lab' && (
          <div className="flex flex-col gap-4 flex-1">
            <ChassisSuspensionLab />
            <AerodynamicWakeRadar />
          </div>
        )}

        {/* Tab: Paddock Live Driver Market & Budget Cap Hub */}
        {activeTab === 'driver_market' && (
          <div className="flex flex-col gap-4 flex-1">
            <DriverMarketHub />
          </div>
        )}

        {/* Tab: FIA Race Control & Stewards VAR Room */}
        {activeTab === 'steward_var' && (
          <div className="flex flex-col gap-4 flex-1">
            <StewardInvestigationRoom />
          </div>
        )}

        {/* Tab: FIA Technical Scrutineering & Inspection Bay */}
        {activeTab === 'scrutineering_bay' && (
          <div className="flex flex-col gap-4 flex-1">
            <FIAInspectionBay />
          </div>
        )}

        {/* Tab: Paddock Satellite Doppler Rain Radar */}
        {activeTab === 'doppler_radar' && (
          <div className="flex flex-col gap-4 flex-1">
            <SatelliteDopplerRadar />
          </div>
        )}

        {/* Tab: AI Post-Race Press Conference & Media Studio */}
        {activeTab === 'press_conference' && (
          <div className="flex flex-col gap-4 flex-1">
            <PressConferenceStudio />
          </div>
        )}

        {/* Tab: Iconic FIA Team Radio Soundboard Archives */}
        {activeTab === 'radio_soundboard' && (
          <div className="flex flex-col gap-4 flex-1">
            <HistoricalRadioSoundboard />
          </div>
        )}

        {/* Tab: Aeroelastic Wing Flex & FIA Deflection Lab */}
        {activeTab === 'wing_flex' && (
          <div className="flex flex-col gap-4 flex-1">
            <AeroelasticWingFlexLab />
            <AerodynamicWakeRadar />
          </div>
        )}

        {/* Tab: Driver Biometrics & Cognitive Stress */}
        {activeTab === 'biometrics' && (
          <div className="flex flex-col gap-4 flex-1">
            <DriverBiometricCockpit />
            <TelemetryCharts />
          </div>
        )}

        {/* Tab: AI Broadcast TV Director & Cinematic Graphics */}
        {activeTab === 'broadcast_tv' && (
          <div className="flex flex-col gap-4 flex-1">
            <BroadcastDirectorTV />
            <TrackMap />
          </div>
        )}

        {/* Tab: Real-World FastF1 Telemetry Duel Mode */}
        {activeTab === 'fastf1_duel' && (
          <div className="flex flex-col gap-4 flex-1">
            <FastF1TelemetryDuel />
            <TelemetryCharts />
          </div>
        )}

        {/* Tab: Tactical Pit Wall Strategy Whiteboard */}
        {activeTab === 'whiteboard' && (
          <div className="flex flex-col gap-4 flex-1">
            <PitWallStrategyWhiteboard />
          </div>
        )}

        {/* Tab: AlphaZero-Style MCTS Decision Tree Search */}
        {activeTab === 'mcts_search' && (
          <div className="flex flex-col gap-4 flex-1">
            <MCTSVisualizer />
            <MonteCarloStrategySim />
          </div>
        )}

        {/* Tab: 3D Pit Crew & Sub-2.0s Wheel Gun Lab */}
        {activeTab === 'pit_crew_3d' && (
          <div className="flex flex-col gap-4 flex-1">
            <PitStop3DCrewLab />
            <PitStopReactionSim />
          </div>
        )}

        {/* Tab: 3D Wind Tunnel & Aerodynamic CFD Lab */}
        {activeTab === 'wind_tunnel' && (
          <div className="flex flex-col gap-4 flex-1">
            <WindTunnelCFDLab />
            <AerodynamicWakeRadar />
          </div>
        )}

        {/* Tab: Telemetry Sensor Fusion Autoencoder */}
        {activeTab === 'sensor_anomalies' && (
          <div className="flex flex-col gap-4 flex-1">
            <SensorAnomalyDetector />
            <VehicleHealthView />
          </div>
        )}

        {/* Tab: Multi-Zone Tyre Thermodynamics */}
        {activeTab === 'tyre_thermo' && (
          <div className="flex flex-col gap-4 flex-1">
            <TyreThermodynamicsView />
            <TyreIntelligenceView />
          </div>
        )}

        {/* Tab: Aerodynamic Wake & ERS Energy */}
        {activeTab === 'aerodynamics' && (
          <div className="flex flex-col gap-4 flex-1">
            <AerodynamicWakeRadar />
            <LapTimeDeltaTDecomposition />
          </div>
        )}

        {/* Tab 3: Tyre Intelligence & RUL */}
        {activeTab === 'tyre_intel' && (
          <div className="flex flex-col gap-4 flex-1">
            <TyreIntelligenceView />
          </div>
        )}

        {/* Tab 4: Weather Doppler & Grip Crossover */}
        {activeTab === 'weather_intel' && (
          <div className="flex flex-col gap-4 flex-1">
            <WeatherIntelligenceView />
          </div>
        )}

        {/* Tab 5: Opponent Tactics & Undercut Matrix */}
        {activeTab === 'opponent_intel' && (
          <div className="flex flex-col gap-4 flex-1">
            <OpponentIntelligenceView />
          </div>
        )}

        {/* Tab 6: Driver Behavioral Analytics */}
        {activeTab === 'driver_intel' && (
          <div className="flex flex-col gap-4 flex-1">
            <DriverIntelligenceView />
          </div>
        )}

        {/* Tab 7: Powertrain & Vehicle Health */}
        {activeTab === 'vehicle_health' && (
          <div className="flex flex-col gap-4 flex-1">
            <VehicleHealthView />
          </div>
        )}

        {/* Tab 8: Counterfactual Simulation Lab */}
        {activeTab === 'counterfactual' && (
          <div className="flex flex-col gap-4 flex-1">
            <LiveScenarioInjector />
            <StrategySandbox />
            <CounterfactualView />
            <MonteCarloStrategySim />
          </div>
        )}

        {/* Tab 9: RL Training & Action Masking */}
        {activeTab === 'rl_training' && (
          <div className="flex flex-col gap-4 flex-1">
            <DQNPolicyVisualizer />
            <SHAPFeatureWaterfall />
            <ExplainabilityPanel />
          </div>
        )}

        {/* Tab 10: Deep Telemetry Lab */}
        {activeTab === 'telemetry' && (
          <div className="flex flex-col gap-4 flex-1">
            <GhostCarTelemetryOverlay />
            <TelemetryLab />
            <DualDriverTelemetryOverlay />
            <LapTimeDeltaTDecomposition />
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
              <div className="lg:col-span-6">
                <ChassisSetupTuner />
              </div>
              <div className="lg:col-span-6">
                <WeatherDopplerRadar />
              </div>
            </div>
          </div>
        )}

        {/* Tab 11: Historical Race Replay */}
        {activeTab === 'replays' && (
          <div className="flex flex-col gap-4 flex-1">
            <HistoricalReplayView />
          </div>
        )}

        {/* Tab 12: TreeSHAP AI Reasoner */}
        {activeTab === 'explainability' && (
          <div className="flex flex-col gap-4 flex-1">
            <SHAPFeatureWaterfall />
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
              <div className="lg:col-span-6 flex flex-col gap-4">
                <StrategyCard />
                <ExplainabilityPanel />
              </div>
              <div className="lg:col-span-6 flex flex-col gap-4">
                <AIPitWallCopilot />
              </div>
            </div>
          </div>
        )}

        {/* Tab 13: AI-vs-AI Championship */}
        {activeTab === 'championship' && (
          <div className="flex flex-col gap-4 flex-1">
            <ChampionshipTournamentView />
            <ChampionshipStandings />
          </div>
        )}

        {/* Tab 14: System Observability & Diagnostics */}
        {activeTab === 'system_health' && (
          <div className="flex flex-col gap-4 flex-1">
            <SystemHealthView />
          </div>
        )}
      </main>

      {/* Floating AI Pit Wall Copilot Drawer (when opened) */}
      {showCopilotModal && (
        <div className="fixed bottom-6 right-6 z-40 w-96 max-w-[calc(100vw-3rem)] shadow-2xl animate-slide-up">
          <div className="relative">
            <button
              onClick={() => setShowCopilotModal(false)}
              className="absolute top-2 right-2 z-10 p-1 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-all"
            >
              <X className="w-4 h-4" />
            </button>
            <AIPitWallCopilot />
          </div>
        </div>
      )}

      {/* Benchmark Comparison Modal */}
      <BenchmarkComparisonModal
        isOpen={showBenchmarkModal}
        onClose={() => setShowBenchmarkModal(false)}
      />

      {/* Chassis Aero Setup Modal */}
      {showAeroTunerModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fadeIn">
          <div className="relative w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <button
              onClick={() => setShowAeroTunerModal(false)}
              className="absolute top-3 right-3 z-10 p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-all"
            >
              <X className="w-5 h-5" />
            </button>
            <ChassisSetupTuner />
          </div>
        </div>
      )}

      {/* Pit Stop Reaction Drill Modal */}
      {showPitSimModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fadeIn">
          <div className="relative w-full max-w-xl">
            <button
              onClick={() => setShowPitSimModal(false)}
              className="absolute top-3 right-3 z-10 p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-all"
            >
              <X className="w-5 h-5" />
            </button>
            <PitStopReactionSim />
          </div>
        </div>
      )}

      {/* Live Championship Standings Modal */}
      {showStandingsModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fadeIn">
          <div className="relative w-full max-w-2xl">
            <button
              onClick={() => setShowStandingsModal(false)}
              className="absolute top-3 right-3 z-10 p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-all"
            >
              <X className="w-5 h-5" />
            </button>
            <ChampionshipStandings />
          </div>
        </div>
      )}

      {/* Driver Pit Wall Telemetry Modal (when clicked) */}
      {inspectedCar && <DriverTelemetryModal />}

      {/* RAG Race History Debrief Modal */}
      {showQAModal && <RaceHistoryQA onClose={() => setShowQAModal(false)} />}

      {/* Multi-Agent Pit Wall Consensus Modal */}
      <PitWallConsensusModal
        isOpen={showConsensusModal}
        onClose={() => setShowConsensusModal(false)}
      />

      {/* Post-Race Podium & Analytics Debrief Modal */}
      {showDebriefModal && (
        <PostRaceDebriefModal onClose={() => setShowDebriefModal(false)} />
      )}

      {/* Neural Pit Radio Hub Modal */}
      {showRadioHubModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fadeIn">
          <div className="relative w-full max-w-3xl max-h-[90vh] overflow-y-auto">
            <button
              onClick={() => setShowRadioHubModal(false)}
              className="absolute top-3 right-3 z-10 p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-all"
            >
              <X className="w-5 h-5" />
            </button>
            <RadioCommsHub />
          </div>
        </div>
      )}

      {/* Global Command Palette (Ctrl+K) */}
      <CommandPalette
        isOpen={showCommandPalette}
        onClose={() => setShowCommandPalette(false)}
        onOpenConsensus={() => setShowConsensusModal(true)}
        onOpenQA={() => setShowQAModal(true)}
      />
    </div>
  );
};


export default App;
