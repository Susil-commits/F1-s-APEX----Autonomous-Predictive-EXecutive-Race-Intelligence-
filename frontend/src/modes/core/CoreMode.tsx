import React, { useState, useEffect, useCallback } from 'react';
import { AlertTriangle, RotateCcw } from 'lucide-react';
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

  // Fetch driver roster from backend as single source of truth
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
                photo: d.photo,
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
      // Strictly surface error — no fabricated or synthetic data is ever rendered
      setError('Prediction service unavailable');
      setPrediction(null);
    } finally {
      setIsAnalyzing(false);
    }
  }, [drivers, selectedDriver, selectedRace, customGrid, rainForecast]);

  // Initial calculation on mount
  useEffect(() => {
    handleAnalyze();
  }, [handleAnalyze]);

  const activeDriver = drivers.find((d) => d.code === selectedDriver) || drivers[0];

  return (
    <div className="flex flex-col items-center justify-center w-full max-w-6xl mx-auto py-6 px-4 gap-8">
      {/* 1. OFFICIAL F1 HEADER & BANNER */}
      <div className="text-center max-w-3xl flex flex-col items-center gap-3">
        <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded bg-[#181A25] border border-[#2B2E40] text-xs font-f1 font-bold uppercase tracking-wider">
          <span className="w-2 h-2 rounded-full bg-[#E10600] animate-pulse" />
          <span className="text-white">Point-in-Time Predictive Intelligence</span>
          <span className="text-[#00F0FF]">· Temporal Holdout R² = 0.688</span>
        </div>

        <h1 className="text-3xl sm:text-5xl font-black text-white uppercase tracking-tight font-f1">
          F1 PRE-RACE <span className="text-[#E10600]">FINISH PREDICTOR</span>
        </h1>

        <p className="text-sm sm:text-base text-slate-300 font-f1 max-w-2xl leading-relaxed">
          Select a Grand Prix and driver. The model evaluates verified facts known strictly before lights out to project finishing positions and mathematically guaranteed 90% split-conformal confidence bands.
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
        activeDriverDefaultGrid={activeDriver?.defaultGrid ?? 10}
        isAnalyzing={isAnalyzing}
        onGridChange={setCustomGrid}
        onRainChange={setRainForecast}
        onAnalyze={handleAnalyze}
      />

      {/* ERROR STATE: RETRY BANNER (No synthetic predictions ever rendered) */}
      {error && (
        <div className="w-full max-w-2xl bg-[#1C1317] border border-red-800/80 rounded-2xl p-6 text-center flex flex-col items-center gap-4 shadow-xl shadow-red-950/40 animate-fade-in">
          <div className="w-12 h-12 rounded-full bg-red-950/80 border border-red-700/60 flex items-center justify-center text-[#E10600]">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <div className="flex flex-col gap-1">
            <h3 className="font-f1 font-black text-lg text-white uppercase tracking-wide">
              {error}
            </h3>
            <p className="text-xs text-slate-400 max-w-md">
              Unable to reach the APEX CatBoost model endpoint. Please ensure the backend prediction service is running.
            </p>
          </div>
          <button
            type="button"
            onClick={handleAnalyze}
            disabled={isAnalyzing}
            className="px-6 py-2.5 rounded-xl bg-[#E10600] hover:bg-red-600 active:scale-95 text-white font-f1 font-bold text-xs uppercase tracking-wider flex items-center gap-2 transition-all cursor-pointer shadow-lg shadow-red-900/30"
          >
            <RotateCcw className={`w-3.5 h-3.5 ${isAnalyzing ? 'animate-spin' : ''}`} />
            <span>Retry Prediction</span>
          </button>
        </div>
      )}

      {/* 5. PREDICTION RESULTS CARD */}
      {!error && prediction && <PredictionCard data={prediction} />}

      {/* 6. OFFICIAL F1 GLOBAL PARTNER LOGO STRIP */}
      <GlobalPartners sponsors={OFFICIAL_SPONSORS} />
    </div>
  );
};

export default CoreMode;
