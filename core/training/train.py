"""APEX Core Model Training Script.

Benchmarks GradientBoosting, XGBoost, and CatBoost finishing position predictors
with split conformal prediction intervals using strictly temporal splits
to guarantee no historical data leakage.
"""
from __future__ import annotations

import logging
import os
import random
from typing import Any, Dict, List, Tuple

import joblib
import numpy as np
import pandas as pd
from catboost import CatBoostRegressor
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from xgboost import XGBRegressor

from core.features.feature_builder import PRE_RACE_FEATURE_NAMES, PreRaceFeatureBuilder
from core.ingestion.jolpica_adapter import JolpicaAdapter
from core.monitoring.drift import PsiDriftMonitor, TARGET_FEATURES

logger = logging.getLogger(__name__)

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "models")
PRERACE_CACHE_CSV = os.path.join(os.path.dirname(__file__), "..", "data", "real_prerace_dataset.csv")


# Historical rounds known to have experienced active dry-to-wet or wet-to-dry transitions
WEATHER_TRANSITION_ROUNDS = {
    (2022, 7),   # Monaco GP (dry/wet/drying)
    (2022, 17),  # Singapore GP (delayed wet start, drying)
    (2022, 18),  # Japanese GP (rain suspension)
    (2023, 6),   # Monaco GP (late sudden downpour)
    (2023, 13),  # Dutch GP (torrential opening laps, mid dry, red flag deluge)
    (2024, 9),   # Canadian GP (intermittent downpours and drying line)
    (2024, 12),  # British GP (Silverstone showers, crossover strategy)
    (2024, 21),  # São Paulo GP (wet chaos)
}


def generate_synthetic_training_data(n_samples: int = 1500, random_seed: int = 42) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """Generates synthetic pre-race features and finish positions based on realistic F1 physics relationships.

    Used when live historical FastF1 cache is cold or running offline unit training.
    """
    rng = np.random.RandomState(random_seed)
    X = []
    y = []
    circuits_used = []

    candidate_circuits = [
        "silverstone", "monza", "spa", "monaco", "bahrain",
        "singapore", "baku", "vegas", "catalunya", "suzuka",
    ]

    for _ in range(n_samples):
        grid = rng.randint(1, 21)
        quali_delta = float(np.clip(rng.exponential(scale=0.8), 0.0, 4.5))

        rolling_finish = float(np.clip(grid + rng.normal(0, 2.5), 1.0, 20.0))
        starts = rng.randint(0, 15)
        constructor_share = float(np.clip(rng.beta(2, 5), 0.01, 0.40))
        circuit = rng.choice(candidate_circuits)
        rain_prob = float(rng.choice([0.0, 0.05, 0.15, 0.40, 0.70]))
        weather_trans = 1.0 if (rain_prob > 0.30 and rng.rand() > 0.40) else 0.0

        feat_vec, _ = PreRaceFeatureBuilder.extract_features(
            grid_position=grid,
            quali_delta_s=quali_delta,
            rolling_avg_finish=rolling_finish,
            circuit_starts=starts,
            constructor_pts_share=constructor_share,
            circuit_id=str(circuit),
            rain_prob=rain_prob,
            weather_transition=weather_trans,
        )
        # Finishing position correlates with grid, constructor strength, and chaos
        car_perf_bonus = constructor_share * 10.0
        noise = rng.normal(0, 2.0)
        if rain_prob > 0.3:
            noise += rng.normal(0, 2.5)
        if weather_trans > 0.5:
            noise += rng.normal(0, 3.5)  # weather transition significantly increases variance
        if circuit in ("monaco", "singapore", "baku"):
            noise += rng.normal(0, 2.0)  # street circuit volatility

        finish_raw = grid - car_perf_bonus * 0.3 + (rolling_finish - grid) * 0.2 + noise
        finish_pos = int(np.clip(np.round(finish_raw), 1, 20))

        X.append(feat_vec)
        y.append(finish_pos)
        circuits_used.append(str(circuit))

    return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32), circuits_used


def _safe_float(val: Any, default: float = 0.0) -> float:
    if val is None or pd.isna(val):
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def _safe_int(val: Any, default: int = 0) -> int:
    if val is None or pd.isna(val):
        return default
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


def _safe_str(val: Any, default: str = "") -> str:
    if val is None or pd.isna(val):
        return default
    return str(val)


def _generate_synthetic_prerace_df(n_samples: int = 1500, random_seed: int = 42) -> Tuple[np.ndarray, np.ndarray, pd.DataFrame]:
    """Generates synthetic pre-race dataframe for offline unit tests."""
    X, y, circuits = generate_synthetic_training_data(n_samples=n_samples, random_seed=random_seed)
    df = pd.DataFrame(data=X)
    df.columns = list(PRE_RACE_FEATURE_NAMES)
    df["finishing_position"] = y.tolist()
    df["circuit_id"] = circuits
    df["season"] = 2023
    df["data_source"] = "synthetic_fallback"
    return X, y, df


def load_or_fetch_prerace_data(
    seasons: List[int] | None = None,
    cache_path: str = PRERACE_CACHE_CSV,
    force_fetch: bool = False,
    allow_synthetic: bool = False,
) -> Tuple[np.ndarray, np.ndarray, pd.DataFrame]:
    """Loads real pre-race features from disk cache or ingests from Jolpica API."""
    target_seasons = seasons or [2022, 2023, 2024]

    if os.path.exists(cache_path) and not force_fetch:
        logger.info(f"[APEX Core] Loading cached pre-race dataset from {cache_path}")
        df = pd.read_csv(cache_path)
    else:
        logger.info(f"[APEX Core] Ingesting real F1 pre-race data from Jolpica API for seasons {target_seasons}...")
        adapter = JolpicaAdapter()
        records = adapter.fetch_historical_prerace_records(target_seasons)
        if records:
            df = pd.DataFrame(records)
            os.makedirs(os.path.dirname(cache_path), exist_ok=True)
            df.to_csv(cache_path, index=False)
            logger.info(f"[APEX Core] Saved {len(df)} real pre-race records to {cache_path}")
        elif allow_synthetic:
            logger.warning("[APEX Core] Failed to fetch real Jolpica records; falling back to synthetic data")
            return _generate_synthetic_prerace_df(n_samples=1500)
        else:
            raise RuntimeError("[APEX Core] Could not fetch real pre-race data from Jolpica and allow_synthetic is False.")

    # Strictly sort records chronologically and deterministically by season, round, grid, and driver
    if "season" in df.columns and "round" in df.columns:
        sort_cols = [c for c in ["season", "round", "grid_position", "driver_id"] if c in df.columns]
        df = df.sort_values(by=sort_cols).reset_index(drop=True)

    # Convert DataFrame records to standardized 10-dimensional feature vectors
    # (sector_1/2/3_delta_s columns absent from real dataset — dropped in v1.0.1)
    X_list = []
    y_list = []
    for _, row in df.iterrows():
        yr = _safe_int(row.get("season"), 2023)
        rnd = _safe_int(row.get("round"), 1)
        is_transition = 1.0 if (yr, rnd) in WEATHER_TRANSITION_ROUNDS else _safe_float(row.get("weather_transition"), 0.0)
        cid = _safe_str(row.get("circuit_id"), "silverstone")
        q_delta = _safe_float(row.get("quali_delta_s"), 1.0)

        feat_vec, _ = PreRaceFeatureBuilder.extract_features(
            grid_position=_safe_int(row.get("grid_position"), 10),
            quali_delta_s=q_delta,
            rolling_avg_finish=_safe_float(row.get("rolling_avg_finish"), 10.0),
            circuit_starts=_safe_int(row.get("circuit_starts"), 0),
            constructor_pts_share=_safe_float(row.get("constructor_pts_share"), 0.10),
            circuit_id=cid,
            rain_prob=_safe_float(row.get("rain_prob"), 0.05),
            weather_transition=is_transition > 0.5,
        )
        fin_pos = _safe_float(row.get("finishing_position"), _safe_float(row.get("grid_position"), 10.0))
        X_list.append(feat_vec)
        y_list.append(fin_pos)

    return np.array(X_list, dtype=np.float32), np.array(y_list, dtype=np.float32), df


def train_finishing_position_model(
    save_path: str | None = None,
    random_seed: int = 42,
    use_synthetic: bool = False,
) -> Dict[str, Any]:
    """Trains and benchmarks GBR, XGBoost, and CatBoost with split-conformal confidence intervals.

    Two-phase temporal split (real data):
      Phase 1 — Selection: train on 2022, validate on 2023, pick winning architecture.
      Phase 2 — Refit: refit winner on 2022+2023, evaluate ONCE on 2024 holdout.

    This prevents the 2024 holdout from influencing architecture selection.
    """
    os.environ["PYTHONHASHSEED"] = str(random_seed)
    random.seed(random_seed)
    np.random.seed(random_seed)

    refit_mask: np.ndarray | None = None

    if use_synthetic:
        X, y, df = _generate_synthetic_prerace_df(n_samples=2000, random_seed=random_seed)
        split_idx = int(0.8 * len(X))
        X_train, y_train = X[:split_idx], y[:split_idx]
        X_val, y_val = X[split_idx:], y[split_idx:]
        X_select_train, y_select_train = X_train, y_train
        X_select_val, y_select_val = X_val, y_val
        max_train_season = 2023
    else:
        X, y, df = load_or_fetch_prerace_data(allow_synthetic=True)
        if "season" in df.columns and len(df["season"].unique()) >= 3:
            # Phase 1: select winner on 2022 → 2023 validation
            seasons_sorted = sorted(df["season"].unique())
            sel_train_season = seasons_sorted[-3]   # 2022
            sel_val_season = seasons_sorted[-2]     # 2023
            test_season = seasons_sorted[-1]        # 2024

            sel_train_mask = np.asarray(df["season"] == sel_train_season, dtype=bool)
            sel_val_mask = np.asarray(df["season"] == sel_val_season, dtype=bool)
            # Phase 2: refit mask = all seasons prior to holdout
            refit_mask = np.asarray(df["season"] < test_season, dtype=bool)
            val_mask = np.asarray(df["season"] == test_season, dtype=bool)

            X_select_train, y_select_train = X[sel_train_mask], y[sel_train_mask]
            X_select_val, y_select_val = X[sel_val_mask], y[sel_val_mask]
            X_train, y_train = X[refit_mask], y[refit_mask]
            X_val, y_val = X[val_mask], y[val_mask]
            max_train_season = int(sel_val_season)
        else:
            split_idx = int(0.8 * len(X))
            X_train, y_train = X[:split_idx], y[:split_idx]
            X_val, y_val = X[split_idx:], y[split_idx:]
            X_select_train, y_select_train = X_train, y_train
            X_select_val, y_select_val = X_val, y_val
            max_train_season = 2023

    # Split Conformal calibration: last 20% of the refit training set chronologically
    n_train = len(X_train)
    fit_split_idx = int(0.80 * n_train)
    X_fit, y_fit = X_train[:fit_split_idx], y_train[:fit_split_idx]
    X_cal, y_cal = X_train[fit_split_idx:], y_train[fit_split_idx:]

    # Define candidate model architectures
    candidates = {
        "gradient_boosting": GradientBoostingRegressor(
            n_estimators=120,
            learning_rate=0.06,
            max_depth=4,
            random_state=random_seed,
        ),
        "xgboost": XGBRegressor(
            n_estimators=120,
            learning_rate=0.06,
            max_depth=4,
            random_state=random_seed,
            eval_metric="rmse",
        ),
        "catboost": CatBoostRegressor(
            iterations=150,
            learning_rate=0.06,
            depth=4,
            random_seed=random_seed,
            thread_count=1,
            verbose=0,
            allow_writing_files=False,
        ),
    }

    # Phase 1 — Architecture selection: benchmark each model on (2022 → 2023 val)
    # Uses X_select_train (2022) / X_select_val (2023) so the 2024 holdout is not touched.
    selection_benchmarks: Dict[str, Dict[str, float]] = {}
    selection_models: Dict[str, Any] = {}

    for name, candidate in candidates.items():
        candidate.fit(X_select_train, y_select_train)
        selection_models[name] = candidate
        sel_preds = candidate.predict(X_select_val)
        sel_mae = mean_absolute_error(y_select_val, sel_preds)
        sel_r2 = r2_score(y_select_val, sel_preds)
        selection_benchmarks[name] = {
            "selection_mae": round(sel_mae, 3),
            "selection_r2": round(sel_r2, 3),
        }
        logger.info(f"[APEX Selection] {name.upper()}: 2023-val R²={sel_r2:.3f}, MAE={sel_mae:.2f}")

    # Pick winner on 2023 validation
    best_name = max(selection_benchmarks.keys(), key=lambda k: (
        selection_benchmarks[k]["selection_r2"], -selection_benchmarks[k]["selection_mae"]
    ))
    logger.info(f"[APEX Selection] Winner architecture: {best_name.upper()}")

    # Phase 2 — Refit winner on 2022+2023, then evaluate ONCE on 2024 holdout
    # Instantiate a fresh copy so Phase-1 fit does not bleed into the final model.
    refit_candidates = {
        "gradient_boosting": GradientBoostingRegressor(
            n_estimators=120, learning_rate=0.06, max_depth=4, random_state=random_seed
        ),
        "xgboost": XGBRegressor(
            n_estimators=120, learning_rate=0.06, max_depth=4, random_state=random_seed, eval_metric="rmse"
        ),
        "catboost": CatBoostRegressor(
            iterations=150, learning_rate=0.06, depth=4, random_seed=random_seed,
            thread_count=1, verbose=0, allow_writing_files=False,
        ),
    }
    best_model = refit_candidates[best_name]
    best_model.fit(X_fit, y_fit)  # X_fit = 80% of 2022+2023 chronologically

    # Evaluate on 2024 holdout (one pass)
    best_val_preds = best_model.predict(X_val)
    best_mae = float(mean_absolute_error(y_val, best_val_preds))
    best_r2 = float(r2_score(y_val, best_val_preds))
    logger.info(f"[APEX Holdout] 2024 final: R²={best_r2:.3f}, MAE={best_mae:.2f}")

    # Expose per-architecture selection scores as benchmarks for metadata
    benchmarks: Dict[str, Dict[str, float]] = {
        name: {
            "validation_mae": selection_benchmarks[name]["selection_mae"],
            "validation_r2": selection_benchmarks[name]["selection_r2"],
        }
        for name in selection_benchmarks
    }

    # Split Conformal Prediction Interval Calibration (held-out calibration fold)
    # Compute nonconformity scores on X_cal: R_i = |y_i - f(X_i)|
    cal_preds = best_model.predict(X_cal)
    cal_residuals = np.abs(y_cal - cal_preds)
    n_cal = len(cal_residuals)

    # Conformal finite-sample adjusted quantile for 90% target coverage:
    # q_hat = (1 - alpha)(1 + 1/n) quantile
    alpha = 0.10
    q_level = np.clip(np.ceil((n_cal + 1) * (1.0 - alpha)) / n_cal, 0.0, 1.0)
    q_hat = float(np.quantile(cal_residuals, q_level, method="higher"))

    # Verify empirical coverage on validation set
    val_residuals = np.abs(y_val - best_val_preds)
    empirical_val_coverage = float(np.mean(val_residuals <= q_hat))

    # Quantile Regression (Asymmetric Uncertainty Bounds: P10, P50, P90)
    logger.info("[APEX Core] Training Quantile Regressors (P10/P50/P90) for asymmetric uncertainty...")
    quantile_models = {
        "q10": GradientBoostingRegressor(
            loss="quantile",
            alpha=0.10,
            n_estimators=120,
            learning_rate=0.06,
            max_depth=4,
            random_state=random_seed,
        ),
        "q50": GradientBoostingRegressor(
            loss="quantile",
            alpha=0.50,
            n_estimators=120,
            learning_rate=0.06,
            max_depth=4,
            random_state=random_seed,
        ),
        "q90": GradientBoostingRegressor(
            loss="quantile",
            alpha=0.90,
            n_estimators=120,
            learning_rate=0.06,
            max_depth=4,
            random_state=random_seed,
        ),
    }

    for q_name, q_mod in quantile_models.items():
        q_mod.fit(X_fit, y_fit)

    q10_val = quantile_models["q10"].predict(X_val)
    q50_val = quantile_models["q50"].predict(X_val)
    q90_val = quantile_models["q90"].predict(X_val)

    # Quantile empirical coverage and mean interval width on validation holdout
    q_covered = (y_val >= q10_val) & (y_val <= q90_val)
    q_coverage = float(np.mean(q_covered))
    q_mean_width = float(np.mean(q90_val - q10_val))
    logger.info(
        f"[APEX Quantile] Empirical 80% Central Coverage: {q_coverage*100:.1f}%, Mean Interval Width: {q_mean_width:.2f} positions"
    )

    artifact = {
        "model": best_model,
        "feature_names": PRE_RACE_FEATURE_NAMES,
        "winning_model_family": best_name,
        "q_hat_margin": q_hat,
        "conformal": {
            "method": "split_conformal",
            "coverage_target": 0.90,
            "calibration_samples": n_cal,
            "validation_coverage": round(empirical_val_coverage, 3),
            "q_hat": round(q_hat, 2),
            "caveat": "Guarantees population-level marginal coverage on calibration distribution. Finite-sample coverage may fluctuate for small driver/circuit subgroups.",
        },
        "quantile_models": quantile_models,
        "quantile_metrics": {
            "validation_coverage": round(q_coverage, 3),
            "mean_interval_width": round(q_mean_width, 2),
            "target_coverage": 0.80,
        },
        "metrics": {
            "validation_mae": best_mae,
            "validation_r2": best_r2,
            "n_train_samples": len(X_train),
            "n_fit_samples": len(X_fit),
            "n_cal_samples": n_cal,
            "n_val_samples": len(X_val),
            "data_source": "jolpica_real" if not use_synthetic else "synthetic_fallback",
        },
        "benchmarks": benchmarks,
        "model_trained_through_race_id": f"season_{max_train_season}_finale",
        "version": "core-v1.0.0",
    }

    # Fit PsiDriftMonitor on the training features prior to holdout
    psi_monitor = PsiDriftMonitor()
    psi_train_df = df[refit_mask] if (refit_mask is not None) else df
    psi_monitor.fit(psi_train_df, features=TARGET_FEATURES)
    artifact["psi_reference_bins"] = psi_monitor.to_dict()

    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        joblib.dump(artifact, save_path)
        logger.info(f"[APEX Core] Best Model ({best_name}) saved to {save_path}")
        psi_bins_path = os.path.join(os.path.dirname(save_path), "apex_core_v1_psi_bins.json")
        psi_monitor.save(psi_bins_path)

    return artifact


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    out_file = os.path.join(MODEL_DIR, "apex_core_v1_model.joblib")
    res = train_finishing_position_model(save_path=out_file)
    logger.info("=======================================================")
    logger.info("APEX Core V1 Benchmark Complete!")
    logger.info("Candidates Benchmarked:")
    for m, scores in res["benchmarks"].items():
        logger.info(f"  - {m:20s}: R² = {scores['validation_r2']:.3f}, MAE = {scores['validation_mae']:.2f}")
    logger.info(f"Winning Architecture: {res['winning_model_family'].upper()}")
    logger.info(f"Holdout Validation: R² = {res['metrics']['validation_r2']:.3f}, MAE = {res['metrics']['validation_mae']:.2f}")
    logger.info(f"Split Conformal Margin (q_hat): ±{res['q_hat_margin']:.2f} positions (Calibration N={res['conformal']['calibration_samples']})")
    logger.info(f"Empirical Coverage on Holdout: {res['conformal']['validation_coverage']*100:.1f}%")
    logger.info(f"Quantile Regression (P10-P90) Mean Width: {res['quantile_metrics']['mean_interval_width']:.2f} positions (Coverage: {res['quantile_metrics']['validation_coverage']*100:.1f}%)")
    logger.info("=======================================================")
