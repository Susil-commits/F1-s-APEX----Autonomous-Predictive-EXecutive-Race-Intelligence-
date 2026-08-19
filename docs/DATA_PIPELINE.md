# APEX — Data Pipeline Documentation
## Spec §5 — Data Ingestion, Validation, and Versioning

**Document Version:** 1.0
**Last Updated:** 2026-08-19

---

## 1. Overview

The APEX data pipeline ingests real F1 telemetry from FastF1, transforms it into
ML-ready feature vectors, validates quality, and stores versioned manifests.

`
FastF1 API
    |
    v
fetch_fastf1_data.py          (Season/session downloader)
    |
    v
dataset_builder.py            (Feature engineering + normalization)
    |
    v
data_quality.py               (11-check quality + leakage guard)
    |
    v
dataset_version.py            (Race-based splits + manifest)
    |
    v
backend/data/registry/        (Versioned JSON manifests)
    |
    v
TyreModel.train()             (XGBoost + RandomForest ensemble)
`

---

## 2. Data Source

| Source | Library | URL |
|--------|---------|-----|
| F1 Telemetry | fastf1 | https://github.com/theOehrly/Fast-F1 |
| Sessions | Race, Qualifying, Practice | Per-circuit, per-season |
| Seasons | 2019–2024 | ~22 rounds x 6 seasons = ~130 race sessions |

---

## 3. Feature Schema (v1.0)

Per-lap feature vector (28 features, FEATURE_DIM=28):

| # | Feature | Range | Source |
|---|---------|-------|--------|
| 0 | tyre_age_laps | [0, 80] | FastF1 |
| 1 | tyre_wear_pct | [0, 1.0] | Derived from laps |
| 2 | compound_soft | {0,1} | OneHot |
| 3 | compound_medium | {0,1} | OneHot |
| 4 | compound_hard | {0,1} | OneHot |
| 5 | compound_inter | {0,1} | OneHot |
| 6 | compound_wet | {0,1} | OneHot |
| 7 | driving_mode_push | {0,1} | Rule-inferred |
| 8 | driving_mode_conserve | {0,1} | Rule-inferred |
| 9 | fuel_kg_norm | [0, 1.0] | 100kg normalized |
| 10 | laps_remaining_norm | [0, 1.0] | total_laps normalized |
| 11 | position_norm | [0, 1.0] | N_cars normalized |
| 12 | gap_leader_norm | [0, 1.0] | Clipped at 120s |
| 13 | gap_ahead_norm | [0, 1.0] | Clipped at 30s |
| 14 | gap_behind_norm | [0, 1.0] | Clipped at 30s |
| 15 | rain_intensity | [0, 1.0] | FastF1 weather |
| 16 | track_temp_norm | [0, 1.0] | 0-60°C normalized |
| 17 | rain_prob_5_laps | [0, 1.0] | Weather model |
| 18 | safety_car_none | {0,1} | OneHot |
| 19 | safety_car_vsc | {0,1} | OneHot |
| 20 | safety_car_sc | {0,1} | OneHot |
| 21 | pit_count_norm | [0, 1.0] | /5 normalized |
| 22 | tyre_cliff_reached | {0,1} | Binary flag |
| 23 | lap_progress_pct | [0, 1.0] | race progress |
| 24 | overall_risk_score | [0, 1.0] | RiskEngine |
| 25 | health_score_norm | [0, 1.0] | VehicleHealthModel |
| 26 | track_wear_factor | [0.5, 2.0] / 2.0 | TrackConfig |
| 27 | in_traffic | {0,1} | gap_ahead < 1.2s |

---

## 4. Anti-Leakage Split Strategy

All splits are performed at **race session granularity** — no lap from the same
race session appears in both train and test sets.

`python
from backend.training.datasets.dataset_version import DatasetVersionRegistry
splits = DatasetVersionRegistry.create_leak_free_splits(df, test_season=2024)
# -> {"train": df_train, "val": df_val, "test": df_test}
`

**Split allocation (default):**
- Train: 60% of sessions (ordered chronologically)
- Val:   20% of sessions
- Test:  20% of sessions (most recent by default)

**Why race-level splits matter:**
Laps within a single race are autocorrelated (same car, same conditions, same
tyre batch). Row-level splits would leak autocorrelated signal across splits.

---

## 5. Quality Checks (data_quality.py)

11 automated checks run before every training job:

| Check | Severity | What it detects |
|-------|----------|----------------|
| duplicate_rows | WARNING (>5% SEVERE) | Exact row duplicates |
| impossible_tyre_age | SEVERE | tyre_age outside [1, 80] |
| negative_values | SEVERE | Negative fuel/lap-time |
| invalid_compound | SEVERE | Unknown compound label |
| future_leakage | SEVERE | _next/_future columns + target |
| target_leakage | SEVERE | r>0.98 correlation with target |
| timestamp_ordering | SEVERE (>5 groups) | Non-monotonic tyre_age in stint |
| missing_bursts | WARNING | >2% consecutive null lap-time-delta |
| outlier_lap_times | WARNING | lap_time_s outside [50, 300] |
| invalid_race_position | WARNING | Position outside [1, 20] |
| impossible_pit_timing | SEVERE | tyre_age backward jump without stint change |

Any SEVERE check raises DataLeakageError and aborts the training job.

---

## 6. Dataset Manifest

Each registered dataset produces a JSON manifest at:
ackend/data/registry/{version}_manifest.json

Schema (DatasetVersionMetadata):

`json
{
  "dataset_version": "v1.2_2024",
  "source": "fastf1",
  "seasons": [2022, 2023, 2024],
  "sessions": ["Bahrain", "Silverstone", ...],
  "features_version": "v1.0",
  "creation_timestamp": "2024-06-01T00:00:00+00:00",
  "row_count": 127450,
  "missing_values": {"PitInTime": 118000},
  "schema_hash": "a1b2c3d4e5f6a7b8",
  "feature_names": ["tyre_age", "compound", ...],
  "split_strategy": "race_season_split",
  "train_races": ["2022_Bahrain", "2022_Silverstone", ...],
  "val_races": ["2023_Monza", ...],
  "test_races": ["2024_Silverstone", ...]
}
`

---

## 7. Running the Pipeline

`ash
# Full pipeline (2022-2024 seasons)
.venv\Scripts\python.exe -m backend.training.fetch_fastf1_data

# Quick smoke test (1 session)
.venv\Scripts\python.exe -m backend.training.fetch_fastf1_data --quick

# Quality check only (no re-download)
.venv\Scripts\python.exe -c "
from backend.training.datasets.data_quality import DataQualityChecker
import pandas as pd
df = pd.read_parquet('backend/data/tyre_data.parquet')
report = DataQualityChecker.run(df, 'tyre_data')
print(report.summary())
"
`

---

## 8. Reproducibility

All pipeline runs must log and store:
1. dataset_version string
2. schema_hash of the feature DataFrame
3. creation_timestamp
4. 	rain_races / al_races / 	est_races lists

These are stored in {version}_manifest.json and must be referenced in any
model artifact metadata to ensure end-to-end reproducibility.
