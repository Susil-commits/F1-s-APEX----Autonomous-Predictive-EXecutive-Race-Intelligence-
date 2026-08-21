import React, { useState, useMemo } from 'react';
import { useRaceStore } from '../store/raceStore';
import { Cloud, Wind, Compass, Gauge, Zap, Activity, CheckCircle2 } from 'lucide-react';

export const AtmosphericSoundingLab: React.FC = () => {
  const { raceState } = useRaceStore();

  const [altitudeMeters, setAltitudeMeters] = useState<number>(2285); // Default Mexico City altitude
  const [ambientTempC, setAmbientTempC] = useState<number>(24);
  const [relativeHumidityPct, setRelativeHumidityPct] = useState<number>(45);

  // Atmospheric physics formulas
  const atmosphericMetrics = useMemo(() => {
    // Barometric pressure formula P = P0 * exp(-M*g*h / (R*T))
    const p0 = 1013.25;
    const tempK = ambientTempC + 273.15;
    const pressureHpa = Number((p0 * Math.exp((-0.0289644 * 9.80665 * altitudeMeters) / (8.3144598 * tempK))).toFixed(1));

    // Air density rho = P / (R_spec * T)
    const rSpec = 287.058;
    const airDensityKgM3 = Number(((pressureHpa * 100) / (rSpec * tempK)).toFixed(3));

    // Downforce penalty compared to sea level (1.225 kg/m3)
    const downforceRetentionPct = Number(((airDensityKgM3 / 1.225) * 100).toFixed(1));
    const turboOverspinRpm = Math.round(100000 + (1.225 - airDensityKgM3) * 80000);
    const topSpeedGainKmh = Number(((1.225 - airDensityKgM3) * 45).toFixed(1));

    return {
      pressureHpa,
      airDensityKgM3,
      downforceRetentionPct,
      turboOverspinRpm,
      topSpeedGainKmh,
    };
  }, [altitudeMeters, ambientTempC, relativeHumidityPct]);

  return (
    <div className="w-full rounded-2xl bg-slate-950 border border-slate-800 p-4 flex flex-col gap-4 shadow-2xl">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Cloud className="w-5 h-5 text-sky-400 animate-pulse" />
          <div className="flex flex-col">
            <span className="font-bold text-white text-sm">
              PADDOCK WEATHER BALLOON ATMOSPHERIC SOUNDING & BAROMETRIC LAB
            </span>
            <span className="text-[11px] font-mono text-slate-400">
              High-altitude air density (rho), barometric pressure, turbo compressor overspin & aero downforce loss
            </span>
          </div>
        </div>

        {/* Preset Altitudes */}
        <div className="flex items-center bg-slate-900 p-1 rounded-xl border border-slate-800 text-xs font-mono">
          <button
            onClick={() => setAltitudeMeters(20)}
            className={`px-2.5 py-1 rounded-lg transition-all ${
              altitudeMeters === 20 ? 'bg-sky-500 text-black font-bold' : 'text-slate-400'
            }`}
          >
            Sea Level (Silverstone)
          </button>
          <button
            onClick={() => setAltitudeMeters(700)}
            className={`px-2.5 py-1 rounded-lg transition-all ${
              altitudeMeters === 700 ? 'bg-sky-500 text-black font-bold' : 'text-slate-400'
            }`}
          >
            Red Bull Ring (700m)
          </button>
          <button
            onClick={() => setAltitudeMeters(2285)}
            className={`px-2.5 py-1 rounded-lg transition-all ${
              altitudeMeters === 2285 ? 'bg-sky-500 text-black font-bold' : 'text-slate-400'
            }`}
          >
            Mexico City (2,285m)
          </button>
        </div>
      </div>

      {/* Primary Atmospheric KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 font-mono">
        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] text-slate-400 uppercase">AIR DENSITY (ρ)</span>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-black text-sky-400">
              {atmosphericMetrics.airDensityKgM3}
            </span>
            <span className="text-xs text-slate-400">KG/M³</span>
          </div>
          <span className="text-[10px] text-slate-400">Sea level datum: 1.225</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] text-slate-400 uppercase">BAROMETRIC PRESSURE</span>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-black text-apex-cyan">
              {atmosphericMetrics.pressureHpa}
            </span>
            <span className="text-xs text-slate-400">HPA</span>
          </div>
          <span className="text-[10px] text-slate-400">Atmospheric Sounding</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] text-slate-400 uppercase">AERO DOWNFORCE RETENTION</span>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-black text-amber-400">
              {atmosphericMetrics.downforceRetentionPct}%
            </span>
          </div>
          <span className="text-[10px] text-slate-400">Wing Efficiency Factor</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] text-slate-400 uppercase">TURBO SHAFT SPEED</span>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-black text-rose-400">
              {atmosphericMetrics.turboOverspinRpm.toLocaleString()}
            </span>
            <span className="text-xs text-slate-400">RPM</span>
          </div>
          <span className="text-[10px] text-slate-400">Thinner Air Mass Boost</span>
        </div>
      </div>

      {/* Interactive Controls & Sounding Profile */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 font-mono text-xs">
        {/* Controls (Left 6 cols) */}
        <div className="lg:col-span-6 p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col gap-3">
          <span className="font-bold text-slate-300 uppercase border-b border-slate-800 pb-2">
            WEATHER BALLOON TELEMETRY PARAMETERS
          </span>

          {/* Altitude Slider */}
          <div className="flex flex-col gap-1">
            <div className="flex justify-between">
              <span className="text-slate-400">Track Altitude:</span>
              <span className="font-bold text-sky-400">{altitudeMeters} Meters AMSL</span>
            </div>
            <input
              type="range"
              min={0}
              max={2500}
              step={25}
              value={altitudeMeters}
              onChange={(e) => setAltitudeMeters(Number(e.target.value))}
              className="accent-sky-400 cursor-pointer"
            />
          </div>

          {/* Temperature Slider */}
          <div className="flex flex-col gap-1">
            <div className="flex justify-between">
              <span className="text-slate-400">Ambient Temperature:</span>
              <span className="font-bold text-amber-400">{ambientTempC}°C</span>
            </div>
            <input
              type="range"
              min={10}
              max={45}
              value={ambientTempC}
              onChange={(e) => setAmbientTempC(Number(e.target.value))}
              className="accent-amber-400 cursor-pointer"
            />
          </div>

          {/* Humidity Slider */}
          <div className="flex flex-col gap-1">
            <div className="flex justify-between">
              <span className="text-slate-400">Relative Air Humidity:</span>
              <span className="font-bold text-emerald-400">{relativeHumidityPct}%</span>
            </div>
            <input
              type="range"
              min={10}
              max={100}
              value={relativeHumidityPct}
              onChange={(e) => setRelativeHumidityPct(Number(e.target.value))}
              className="accent-emerald-400 cursor-pointer"
            />
          </div>
        </div>

        {/* Aerodynamic Impact Analysis (Right 6 cols) */}
        <div className="lg:col-span-6 p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col justify-between gap-3">
          <span className="font-bold text-slate-300 uppercase border-b border-slate-800 pb-2">
            AERODYNAMIC & POWER UNIT IMPACT
          </span>

          <div className="flex flex-col gap-2 text-slate-300">
            <div className="flex justify-between">
              <span className="text-slate-400">Straight-line Top Speed Boost:</span>
              <strong className="text-emerald-400">+{atmosphericMetrics.topSpeedGainKmh} km/h (Reduced Drag)</strong>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Cornering Grip Deficit:</span>
              <strong className="text-rose-400">-{(100 - atmosphericMetrics.downforceRetentionPct).toFixed(1)}% Downforce</strong>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Brake & Power Unit Cooling Airflow:</span>
              <strong className="text-amber-400">Severely Constrained (Open Louvres)</strong>
            </div>
          </div>

          <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-[11px] text-slate-400 leading-relaxed">
            <strong>Engineering Setup Advice:</strong> Run maximum Monaco-level high-downforce rear wing to compensate for the {100 - Math.round(atmosphericMetrics.downforceRetentionPct)}% air density deficit while opening all engine engine cover cooling louvres.
          </div>
        </div>
      </div>
    </div>
  );
};
