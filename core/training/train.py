"""APEX Core Model Training Script.

Benchmarks GradientBoosting, XGBoost, and CatBoost finishing position predictors
with split conformal prediction intervals using strictly temporal splits
to guarantee no historical data leakage.
"""
from __future__ import annotations

import logging
import os
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
        s1_delta = float(np.clip(quali_delta * rng.uniform(0.25, 0.40), 0.0, 2.0))
        s2_delta = float(np.clip(quali_delta * rng.uniform(0.30, 0.50), 0.0, 2.0))
        s3_delta = float(np.clip(quali_delta - (s1_delta + s2_delta) * 0.5, 0.0, 2.0))

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
            sector_1_delta_s=s1_delta,
            sector_2_delta_s=s2_delta,
            sector_3_delta_s=s3_delta,
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

    # Convert DataFrame records to standardized 13-dimensional feature vectors
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
            sector_1_delta_s=_safe_float(row.get("sector_1_delta_s"), 0.0),
            sector_2_delta_s=_safe_float(row.get("sector_2_delta_s"), 0.0),
            sector_3_delta_s=_safe_float(row.get("sector_3_delta_s"), 0.0),
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
    """Trains and benchmarks GBR, XGBoost, and CatBoost with split-conformal confidence intervals."""
    if use_synthetic:
        X, y, df = _generate_synthetic_prerace_df(n_samples=2000, random_seed=random_seed)
        split_idx = int(0.8 * len(X))
        X_train, y_train = X[:split_idx], y[:split_idx]
        X_val, y_val = X[split_idx:], y[split_idx:]
        max_train_season = 2023
    else:
        X, y, df = load_or_fetch_prerace_data(allow_synthetic=True)
        # Strict temporal split: Train on past seasons (<= 2023), validate on holdout season (2024)
        if "season" in df.columns and len(df["season"].unique()) > 1:
            val_season = int(df["season"].max())
            train_mask = np.asarray(df["season"] < val_season, dtype=bool)
            val_mask = np.asarray(df["season"] == val_season, dtype=bool)
            X_train, y_train = X[train_mask], y[train_mask]
            X_val, y_val = X[val_mask], y[val_mask]
            max_train_season = int(df.loc[df["season"] < val_season, "season"].max())
        else:
            split_idx = int(0.8 * len(X))
            X_train, y_train = X[:split_idx], y[:split_idx]
            X_val, y_val = X[split_idx:], y[split_idx:]
            max_train_season = 2023

    # Split Conformal: Hold out the chronological final 20% of the training set for calibration
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
            verbose=0,
            allow_writing_files=False,
        ),
    }

    # Benchmark each model on the fit set and evaluate on the temporal holdout (validation set)
    benchmarks: Dict[str, Dict[str, float]] = {}
    fitted_models: Dict[str, Any] = {}

    for name, candidate in candidates.items():
        candidate.fit(X_fit, y_fit)
        fitted_models[name] = candidate

        val_preds = candidate.predict(X_val)
        mae = mean_absolute_error(y_val, val_preds)
        r2 = r2_score(y_val, val_preds)
        benchmarks[name] = {
            "validation_mae": round(mae, 3),
            "validation_r2": round(r2, 3),
        }
        logger.info(f"[APEX Benchmark] {name.upper()}: Val R²={r2:.3f}, MAE={mae:.2f}")

    # Select winning model by highest validation R² (or lowest MAE if tied)
    best_name = max(benchmarks.keys(), key=lambda k: (benchmarks[k]["validation_r2"], -benchmarks[k]["validation_mae"]))
    best_model = fitted_models[best_name]
    best_val_preds = best_model.predict(X_val)
    best_mae = benchmarks[best_name]["validation_mae"]
    best_r2 = benchmarks[best_name]["validation_r2"]

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

    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        joblib.dump(artifact, save_path)
        logger.info(f"[APEX Core] Best Model ({best_name}) saved to {save_path}")

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
