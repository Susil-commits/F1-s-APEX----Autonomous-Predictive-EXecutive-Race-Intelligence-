"""FastF1 Real Race Telemetry Fetcher & Cleaner.

Extracts real-world Formula 1 lap-by-lap tyre degradation data across multiple circuits
and seasons, computing driver-normalized lap-time degradation deltas.
"""
import logging
import os

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "fastf1_cache")
OUTPUT_CSV = os.path.join(os.path.dirname(__file__), "..", "data", "real_tyre_data.csv")

# Standard benchmark sessions covering different degradation profiles
DEFAULT_RACES: list[tuple[int, str, str]] = [
    (2023, "Silverstone", "R"),
    (2023, "Monza", "R"),
    (2023, "Belgium", "R"),
    (2023, "Spanish Grand Prix", "R"),
    (2023, "Bahrain", "R"),
    (2023, "Austria", "R"),
    (2022, "Silverstone", "R"),
    (2022, "Monza", "R"),
]

COMPOUND_NORM_MAP = {
    "SOFT": "SOFT",
    "MEDIUM": "MEDIUM",
    "HARD": "HARD",
    "INTERMEDIATE": "INTERMEDIATE",
    "WET": "WET",
    "TEST-UNKNOWN": "UNKNOWN",
}


def setup_fastf1_cache(cache_dir: str = CACHE_DIR):
    """Enables persistent disk caching for FastF1 API sessions."""
    os.makedirs(cache_dir, exist_ok=True)
    try:
        import fastf1
        fastf1.Cache.enable_cache(cache_dir)
        logger.info(f"[FastF1] Cache enabled at {cache_dir}")
    except Exception as e:
        logger.warning(f"[FastF1] Could not enable cache at {cache_dir}: {e}")


def clean_session_laps(session_laps: pd.DataFrame, circuit_name: str, year: int) -> pd.DataFrame:
    """
    Cleans raw FastF1 session laps dataframe:
    - Filters out pit in-laps, pit out-laps, and inaccurate telemetry marks.
    - Excludes Safety Car, VSC, and Red Flag track status periods.
    - Normalizes compound names.
    - Computes lap_time_delta isolated from driver baseline pace.
    - Excludes extreme outliers.
    """
    if session_laps is None or session_laps.empty:
        return pd.DataFrame()

    required_cols = ["Driver", "Compound", "TyreLife", "LapTime", "Stint"]
    for col in required_cols:
        if col not in session_laps.columns:
            logger.warning(f"[FastF1] Missing required column '{col}' in session laps")
            return pd.DataFrame()

    records = []
    for _, row in session_laps.iterrows():
        # Drop pit laps
        pit_in = str(row.get("PitInTime", ""))
        pit_out = str(row.get("PitOutTime", ""))
        if pit_in not in ("", "nan", "NaT", "None") or pit_out not in ("", "nan", "NaT", "None"):
            continue
        if "IsAccurate" in row and not bool(row["IsAccurate"]):
            continue
        if "TrackStatus" in row and str(row["TrackStatus"]).strip() != "1":
            continue

        lap_time = row.get("LapTime")
        if lap_time is None or str(lap_time) in ("", "nan", "NaT", "None"):
            continue

        lap_s = 0.0
        if hasattr(lap_time, "total_seconds"):
            try:
                lap_s = float(getattr(lap_time, "total_seconds")())
            except Exception:
                continue
        else:
            try:
                lap_s = float(str(lap_time))
            except (ValueError, TypeError):
                continue

        if lap_s <= 30.0:
            continue

        tyre_life = row.get("TyreLife", 1)
        try:
            tyre_age = int(float(str(tyre_life)))
        except (ValueError, TypeError):
            tyre_age = 1

        if tyre_age < 1:
            continue

        raw_comp = str(row.get("Compound", "MEDIUM")).upper()
        comp = COMPOUND_NORM_MAP.get(raw_comp, "UNKNOWN")
        if comp not in ("SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET"):
            continue

        driver = str(row.get("Driver", "UNKNOWN"))
        try:
            stint = int(float(str(row.get("Stint", 1))))
        except (ValueError, TypeError):
            stint = 1

        records.append({
            "Driver": driver,
            "compound_raw": raw_comp,
            "compound": comp,
            "tyre_age": tyre_age,
            "stint": stint,
            "lap_time_s": lap_s,
        })

    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(records)

    # Compute lap_time_delta per driver (relative to driver's fastest clean lap in session)
    driver_bests = df.groupby("Driver")["lap_time_s"].min().to_dict()
    df["driver_fastest_lap_s"] = df["Driver"].apply(lambda d: driver_bests.get(str(d), 90.0))
    raw_delta = df["lap_time_s"] - df["driver_fastest_lap_s"]

    # In F1, fuel burn-off improves pace by ~0.055s per lap. Correcting for fuel isolates pure tyre degradation.
    # Stint-relative fuel correction:
    df["stint_lap"] = df.groupby(["Driver", "stint"]).cumcount() + 1
    df["fuel_corrected_delta"] = raw_delta + (0.055 * df["stint_lap"])
    df["lap_time_delta"] = df["fuel_corrected_delta"].clip(lower=0.0)

    # Filter outliers: delta should be >= 0 and < 12.0 seconds for normal racing pace
    df = df[(df["lap_time_delta"] >= 0.0) & (df["lap_time_delta"] <= 12.0)]

    # Metadata annotations
    df["circuit"] = circuit_name
    df["season"] = year
    df["data_source"] = "fastf1_real"

    result_cols = [
        "season",
        "circuit",
        "Driver",
        "compound",
        "tyre_age",
        "stint",
        "stint_lap",
        "lap_time_s",
        "driver_fastest_lap_s",
        "fuel_corrected_delta",
        "lap_time_delta",
        "data_source",
    ]
    return pd.DataFrame(df[[c for c in result_cols if c in df.columns]])


def generate_synthetic_fallback_data() -> pd.DataFrame:
    """Generates realistic synthetic F1 telemetry fallback distribution when FastF1 API is offline."""
    np.random.seed(42)
    records = []
    drivers = ["VER", "HAM", "NOR", "LEC", "PIA", "RUS", "SAI", "ALO"]
    circuits = ["Silverstone", "Monza", "Spa"]
    compounds = {
        "SOFT": {"base_loss": 0.08, "cliff_age": 18, "cliff_mult": 0.22},
        "MEDIUM": {"base_loss": 0.055, "cliff_age": 28, "cliff_mult": 0.16},
        "HARD": {"base_loss": 0.038, "cliff_age": 42, "cliff_mult": 0.12},
    }

    for season in [2022, 2023]:
        for circuit in circuits:
            for driver in drivers:
                for comp, specs in compounds.items():
                    max_stint = np.random.randint(specs["cliff_age"] - 6, specs["cliff_age"] + 8)
                    for age in range(1, max_stint + 1):
                        linear_loss = age * specs["base_loss"]
                        cliff_excess = max(0, age - specs["cliff_age"])
                        cliff_loss = (cliff_excess ** 1.8) * specs["cliff_mult"]
                        noise = np.random.normal(0.0, 0.18)
                        fuel_burn_benefit = -0.045 * age  # car gets lighter over stint
                        delta = max(0.0, linear_loss + cliff_loss + fuel_burn_benefit + noise + 0.1)

                        base_lap = 88.0 if circuit == "Silverstone" else (81.0 if circuit == "Monza" else 104.0)
                        driver_pace_offset = np.random.uniform(0.0, 0.6)

                        records.append({
                            "season": season,
                            "circuit": circuit,
                            "Driver": driver,
                            "compound": comp,
                            "tyre_age": age,
                            "stint": 1 if age < 25 else 2,
                            "lap_time_s": round(base_lap + driver_pace_offset + delta, 3),
                            "driver_fastest_lap_s": round(base_lap + driver_pace_offset, 3),
                            "lap_time_delta": round(delta, 3),
                            "data_source": "synthetic_fallback",
                        })

    return pd.DataFrame(records)


def fetch_all_real_races(
    races: list[tuple[int, str, str]] | None = None,
    output_path: str = OUTPUT_CSV,
    force_download: bool = False,
    allow_synthetic_fallback: bool = False,
    register_manifest: bool = True,
    dataset_version: str = "v1.0_telemetry",
) -> pd.DataFrame:
    """
    Downloads, processes, and persists clean F1 tyre degradation telemetry across specified races.
    Validates data quality with DataQualityChecker and registers version manifest.
    If no real sessions were fetched and allow_synthetic_fallback is False, raises RuntimeError.
    If allow_synthetic_fallback is True, generates synthetic fallback dataset.
    """
    from backend.training.datasets.data_quality import DataQualityChecker
    from backend.training.datasets.dataset_version import DatasetVersionRegistry

    races_to_fetch = races or DEFAULT_RACES
    setup_fastf1_cache()

    collected_dfs: list[pd.DataFrame] = []

    try:
        import fastf1

        for year, event, session_type in races_to_fetch:
            try:
                print(f"[FastF1] Loading {year} {event} ({session_type})...")
                session = fastf1.get_session(year, event, session_type)
                session.load(telemetry=False, weather=False, messages=False)
                clean_df = clean_session_laps(session.laps, circuit_name=event, year=year)
                if not clean_df.empty:
                    collected_dfs.append(clean_df)
                    print(f"[FastF1] Processed {len(clean_df)} clean laps from {year} {event}")
            except Exception as e:
                print(f"[FastF1] Warning fetching {year} {event}: {e}")

    except ImportError:
        print("[FastF1] fastf1 package not found.")

    if collected_dfs:
        full_df = pd.concat(collected_dfs, ignore_index=True)
        source_name = "fastf1_real"
    else:
        if not allow_synthetic_fallback:
            raise RuntimeError(
                "[FastF1] No real sessions were fetched from FastF1 API and allow_synthetic_fallback is False. "
                "Check network connection/FastF1 endpoints or pass allow_synthetic_fallback=True if offline."
            )
        print("[FastF1] No remote sessions fetched. Generating synthetic fallback dataset.")
        full_df = generate_synthetic_fallback_data()
        source_name = "synthetic_fallback"

    # Run automated data quality and leakage checks
    quality_report = DataQualityChecker.run(full_df, dataset_name=dataset_version, fail_on_severe=False)
    print(f"[DataQuality] Quality Check: {quality_report.summary()}")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    full_df.to_csv(output_path, index=False)
    print(f"[FastF1] Saved {len(full_df)} total cleaned telemetry records to {output_path}")

    # Register version manifest with leak-free splits
    if register_manifest:
        try:
            registry = DatasetVersionRegistry()
            splits = registry.create_leak_free_splits(full_df)
            train_races = list(splits["train"]["circuit"].unique()) if not splits["train"].empty and "circuit" in splits["train"].columns else []
            val_races = list(splits["val"]["circuit"].unique()) if not splits["val"].empty and "circuit" in splits["val"].columns else []
            test_races = list(splits["test"]["circuit"].unique()) if not splits["test"].empty and "circuit" in splits["test"].columns else []

            manifest = registry.register_dataset(
                full_df,
                version=dataset_version,
                source=source_name,
                train_races=train_races,
                val_races=val_races,
                test_races=test_races,
            )
            print(f"[DatasetRegistry] Registered dataset manifest {dataset_version} ({manifest.row_count} rows)")
        except Exception as e:
            print(f"[DatasetRegistry] Manifest registration notice: {e}")

    return full_df


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="APEX FastF1 Telemetry Fetcher")
    parser.add_argument("--quick", action="store_true", help="Fetch 1 race only for quick test")
    parser.add_argument("--allow-synthetic", action="store_true", default=True, help="Allow fallback synthetic data if offline")
    parser.add_argument("--version", type=str, default="v1.0_telemetry", help="Dataset version identifier")
    parser.add_argument("--output", type=str, default=OUTPUT_CSV, help="Output CSV file path")
    args = parser.parse_args()

    races = DEFAULT_RACES[:1] if args.quick else DEFAULT_RACES
    fetch_all_real_races(
        races=races,
        output_path=args.output,
        allow_synthetic_fallback=args.allow_synthetic,
        dataset_version=args.version,
    )


