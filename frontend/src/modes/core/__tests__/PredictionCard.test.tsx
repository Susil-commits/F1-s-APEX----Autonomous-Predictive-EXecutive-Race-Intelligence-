import { describe, it, expect, vi, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom/vitest';
import { PredictionCard, PredictionData } from '../PredictionCard';
import { RaceConditionsPanel } from '../components/RaceConditionsPanel';
import { PitWallWarRoom } from '../components/PitWallWarRoom';

const SAMPLE_PREDICTION: PredictionData = {
  race_id: 'silverstone',
  driver_id: 'NOR',
  driver_name: 'Lando Norris',
  team_name: 'McLaren',
  grid_position: 2,
  predicted_position: 2,
  confidence_interval: [1, 7],
  quantile_interval: [1, 5],
  quantile_p50: 2,
  win_probability_pct: 42.5,
  podium_probability_pct: 74.0,
  model_version: 'core-v1.0.0',
  data_snapshot_utc: '2026-11-28T10:00:00Z',
  summary_explanation: 'Lando Norris starts P2 for the Silverstone Grand Prix.',
  narrative: 'Box window opens lap 20; hold Z-Mode through Copse and Maggotts.',
  retrieved_sources: [
    {
      topic: 'FIA DRS Regulations',
      article: 'Article 21',
      similarity: 0.88,
      excerpt: 'DRS enabled within 1.000s at detection points.',
    },
  ],
};

describe('PredictionCard & RaceConditionsPanel', () => {
  it('renders projected finish, conformal window, quantile P10-P90 band, narrative, and FIA citations', () => {
    render(<PredictionCard data={SAMPLE_PREDICTION} />);

    expect(screen.getByText('Norris')).toBeInTheDocument();
    expect(screen.getAllByText((_, el) => el?.textContent === 'P2').length).toBeGreaterThan(0);
    expect(screen.getByText(/P10–P90: P1–P5 \(Med P2\)/)).toBeInTheDocument();
    expect(screen.getByText(/Box window opens lap 20/)).toBeInTheDocument();
    expect(screen.getByText('Article 21')).toBeInTheDocument();
  });

  it('renders RaceConditionsPanel with qualifying delta and weather transition controls', () => {
    render(
      <RaceConditionsPanel
        gridPosition={2}
        qualiDelta={0.25}
        rainForecast={35}
        weatherTransition={true}
        activeDriverDefaultGrid={2}
        isAnalyzing={false}
        onGridChange={() => {}}
        onQualiDeltaChange={() => {}}
        onRainChange={() => {}}
        onWeatherTransitionChange={() => {}}
        onAnalyze={() => {}}
      />
    );

    expect(screen.getByText(/\+0\.25s/)).toBeInTheDocument();
    expect(screen.getByText(/35% Rain Probability/)).toBeInTheDocument();
    expect(screen.getByRole('checkbox')).toBeChecked();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders 2-STOP badge, second pit lap, and circuit-scaled 2026 Active Aero metrics in PitWallWarRoom', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation(async (input) => {
      const url = String(input);
      if (url.includes('/api/core/simulate/pit-stop')) {
        return new Response(
          JSON.stringify({
            circuit: 'monza',
            total_laps: 53,
            current_lap: 18,
            current_position: 3,
            simulations_count: 10000,
            total_runtime_ms: 42.1,
            optimal_strategy: 'Aggressive 2-Stop Push',
            optimal_pit_lap: 20,
            expected_finish: 2.1,
            tactical_briefing: 'Two-stop maximizes tyre delta.',
            strategies: [
              {
                strategy_name: 'Aggressive 2-Stop Push',
                target_pit_lap: 20,
                stops_count: 2,
                second_pit_lap: 39,
                expected_finish_pos: 2.1,
                confidence_interval_90: [1, 4],
                win_probability_pct: 32.0,
                podium_probability_pct: 78.0,
                points_finish_probability_pct: 99.0,
                sc_benefit_probability_pct: 25.0,
                simulation_runtime_ms: 14.2,
              },
            ],
          }),
          { status: 200 }
        );
      }
      return new Response(JSON.stringify({}), { status: 200 });
    });

    render(
      <PitWallWarRoom
        selectedRace="monza"
        selectedDriver="VER"
        rainForecast={10}
        apiBase=""
      />
    );

    await waitFor(() => {
      expect(screen.getByText('2-STOP')).toBeInTheDocument();
    });
    expect(screen.getByText('Lap 39')).toBeInTheDocument();

    fireEvent.click(screen.getByText('2026 Active Aero'));
    expect(screen.getByText('Italian GP')).toBeInTheDocument();
    expect(screen.getByText('-59% Drag')).toBeInTheDocument();
  });
});
