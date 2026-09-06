import React, { useState, useEffect, useCallback } from 'react';
import { AlertCircle, RotateCcw, Compass, Flag, Sparkles } from 'lucide-react';
import { PredictionCard, PredictionData } from './PredictionCard';
import {
  GRAND_PRIX_LIST,
  DRIVERS_LIST,
  OFFICIAL_SPONSORS,
  DriverItem,
} from './data/constants';
import {
  GrandPrixSelector,
  DriverGrid,
  RaceConditionsPanel,
  GlobalPartners,
} from './components';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

export const CoreMode: React.FC = () => {
  const [drivers, setDrivers] = useState<DriverItem[]>(DRIVERS_LIST);
  const [selectedRace, setSelectedRace] = useState<string>('silverstone');
  const [selectedDriver, setSelectedDriver] = useState<string>('NOR');
  const [customGrid, setCustomGrid] = useState<number | ''>('');
  const [rainForecast, setRainForecast] = useState<number>(10);
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [prediction, setPrediction] = useState<PredictionData | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Fetch driver roster from backend if available, merging with high-res local photos
  useEffect(() => {
    const fetchDrivers = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/core/drivers`);
        if (res.ok) {
          const data = await res.json();
          if (Array.isArray(data.drivers) && data.drivers.length > 0) {
            setDrivers(
              data.drivers.map((d: any) => ({
                code: d.code,
                firstName: d.first_name || d.name?.split(' ')[0] || d.code,
                lastName: d.last_name || d.name?.split(' ').slice(1).join(' ').toUpperCase() || d.code,
                team: d.team,
                number: d.number ?? 0,
                color: d.color || '#E10600',
                country: d.country || '🏁',
                defaultGrid: d.default_grid ?? 10,
                photo: `/f1/drivers/${d.code}.webp`,
              }))
            );
          }
        }
      } catch {
        // Fall back to static DRIVERS_LIST if backend is starting or offline
      }
    };

    fetchDrivers();
  }, []);

  const handleAnalyze = useCallback(async () => {
    setIsAnalyzing(true);
    setError(null);

    const driverObj = drivers.find((d) => d.code === selectedDriver) || drivers[0];
    const gridVal = customGrid === '' ? driverObj.defaultGrid : Number(customGrid);

    try {
      const res = await fetch(`${API_BASE}/api/core/predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          race_id: selectedRace,
          driver_id: selectedDriver,
          grid_position: gridVal,
          rain_probability: rainForecast / 100.0,
        }),
      });

      if (!res.ok) {
        throw new Error(`Prediction service error: ${res.status}`);
      }

      const data = await res.json();
      setPrediction(data);
      setError(null);
    } catch {
      setError('Race strategy service temporarily unavailable. Please try again shortly.');
      setPrediction(null);
    } finally {
      setIsAnalyzing(false);
    }
  }, [drivers, selectedDriver, selectedRace, customGrid, rainForecast]);

  // Initial calculation on mount
  useEffect(() => {
    handleAnalyze();
  }, [handleAnalyze]);

  const activeGP = GRAND_PRIX_LIST.find((g) => g.id === selectedRace) || GRAND_PRIX_LIST[0];
  const activeDriver = drivers.find((d) => d.code === selectedDriver) || drivers[0];

  return (
    <div className="flex flex-col items-center justify-center w-full max-w-6xl mx-auto py-4 px-2 sm:px-4 gap-8">
      {/* 1. OFFICIAL RACE HEADER BANNER */}
      <div className="text-center max-w-3xl flex flex-col items-center gap-3">
        <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-red-600/10 border border-red-600/20 text-xs font-bold text-[#E10600] uppercase tracking-wider">
          <span className="w-2 h-2 rounded-full bg-[#E10600] animate-pulse" />
          <span>Live Pre-Race Simulation</span>
          <span className="text-slate-400 dark:text-slate-500">· 2026 Regulations</span>
        </div>

        <h1 className="text-3xl sm:text-5xl font-extrabold uppercase tracking-tight text-slate-900 dark:text-white font-['Outfit']">
          GRAND PRIX <span className="text-[#E10600]">FINISH PREDICTOR</span>
        </h1>

        <p className="text-sm sm:text-base text-slate-600 dark:text-slate-400 font-normal max-w-2xl leading-relaxed">
          Select a Grand Prix venue and driver to simulate race day outcomes. APEX evaluates circuit aerodynamics, starting grid delta, and weather probability to project finishing windows.
        </p>
      </div>

      {/* 2. GRAND PRIX CALENDAR SELECTOR */}
      <GrandPrixSelector
        races={GRAND_PRIX_LIST}
        selectedRace={selectedRace}
        onSelect={setSelectedRace}
      />

      {/* 3. OFFICIAL 2026 F1 DRIVER GRID */}
      <DriverGrid
        drivers={drivers}
        selectedDriver={selectedDriver}
        onSelect={(code, defaultGrid) => {
          setSelectedDriver(code);
          setCustomGrid(defaultGrid);
        }}
      />

      {/* 4. PRE-RACE CONDITIONS & FINE-TUNING PANEL */}
      <RaceConditionsPanel
        gridPosition={customGrid}
        rainForecast={rainForecast}
        activeDriverDefaultGrid={activeDriver.defaultGrid}
        isAnalyzing={isAnalyzing}
        onGridChange={setCustomGrid}
        onRainChange={setRainForecast}
        onAnalyze={handleAnalyze}
      />

      {/* 5. PREDICTION RESULT STAGE */}
      {error && (
        <div className="w-full p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-700 dark:text-amber-400 flex items-center gap-3 text-xs">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {prediction && !error && (
        <div className="w-full">
          <PredictionCard data={prediction} />
        </div>
      )}

      {/* 6. GLOBAL PARTNERS */}
      <GlobalPartners sponsors={OFFICIAL_SPONSORS} />
    </div>
  );
};

export default CoreMode;
