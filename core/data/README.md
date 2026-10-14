# APEX Core Datasets

This directory houses the foundational training data and regulatory reference corpus for APEX Core.

## 1. Pre-Race Feature Dataset (`real_prerace_dataset.csv`)

- **Coverage**: 2022, 2023, and 2024 FIA Formula One World Championship seasons.
- **Total Rows**: 1,359 driver-race entries
  - **2022 Season**: 440 driver entries (used for selection model training)
  - **2023 Season**: 440 driver entries (used for selection validation)
  - **2024 Season**: 479 driver entries (used as strictly held-out test set evaluated once)
- **Features Included**:
  - `grid_position_norm`: Starting grid slot [1..20] normalized to [0, 1]
  - `quali_delta_to_pole_s`: Raw time delta to pole in seconds
  - `driver_rolling_finish_norm`: 5-race rolling finish position average
  - `driver_circuit_experience`: Previous career starts at this circuit
  - `constructor_pts_share`: Constructor championship points share prior to the race
  - `circuit_downforce_index`: Circuit downforce demand score [0.0..1.0]
  - `circuit_power_sensitivity`: Circuit power sensitivity rating [0.0..1.0]
  - `circuit_is_street_track`: Boolean indicator (1.0 = street, 0.0 = permanent)
  - `race_rain_prob`: Pre-race precipitation probability forecast [0.0..1.0]
  - `weather_transition_flag`: Predicted weather transition during the Grand Prix
- **Dropped Features**: `sector_1_delta_norm`, `sector_2_delta_norm`, `sector_3_delta_norm` were removed because sector timing deltas are not in the raw pre-race dataset and zero-filling them created dead features.

## 2. Regulations Corpus (`regulations/`)

The [`regulations/`](regulations/) subdirectory contains **3 curated domain summaries** for strategic lever grounding (DRS, Parc Fermé, Tyre/Weather). These are curated summaries rather than full FIA statutory documents.
