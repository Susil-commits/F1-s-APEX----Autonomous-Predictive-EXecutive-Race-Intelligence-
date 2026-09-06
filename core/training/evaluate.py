"""APEX Core Model Evaluation Script.

Evaluates trained model on strictly temporal holdout partitions and reports
MAE, RMSE, Pearson correlation, conformal coverage, and segmented performance
broken down by circuit type (Street vs Permanent vs High-Speed).
"""
from __future__ import annotations

import json
import logging
import warnings
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from scipy.stats import ConstantInputWarning, pearsonr, spearmanr
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


from core.training.train import generate_synthetic_training_data

logger = logging.getLogger(__name__)

STREET_CIRCUITS = {
    "monaco", "singapore", "marina_bay", "baku", "jeddah", "albert_park", "miami"
}
HIGH_SPEED_CIRCUITS = {
    "monza", "vegas", "red_bull_ring"
}


def classify_circuit(circuit_id: str) -> str:
    """Classifies a circuit into 'street', 'high_speed', or 'permanent'."""
    cid = circuit_id.lower()
    if cid in STREET_CIRCUITS:
        return "street"
    elif cid in HIGH_SPEED_CIRCUITS:
        return "high_speed"
    return "permanent"


def evaluate_model_temporal(model_artifact: Dict[str, Any], n_test_samples: int = 500) -> Dict[str, Any]:
    """Evaluates artifact on out-of-sample holdout with segmented circuit analysis."""
    model = model_artifact["model"]
    q_hat = model_artifact.get("q_hat_margin", 2.0)
    quantile_models = model_artifact.get("quantile_models")

    from core.training.train import load_or_fetch_prerace_data
    df_test: pd.DataFrame
    try:
        X_all, y_all, df = load_or_fetch_prerace_data(allow_synthetic=True)
        if "data_source" in df.columns and (df["data_source"] == "synthetic_fallback").any():
            fallback_msg = (
                "[APEX EVALUATION WARNING] Dataset is running on synthetic fallback data! "
                "Offline evaluation is not using real historical F1 records."
            )
            logger.warning(fallback_msg)
        if "season" in df.columns and len(df["season"].unique()) > 1:
            max_s = df["season"].max()
            season_mask = df["season"] == max_s
            test_mask = np.asarray(season_mask, dtype=bool)
            X_test, y_test = X_all[test_mask], y_all[test_mask]
            df_test = pd.DataFrame(df[season_mask].copy().reset_index(drop=True))
        else:
            X_test, y_test = X_all[-n_test_samples:], y_all[-n_test_samples:]
            df_test = df.iloc[-n_test_samples:].copy().reset_index(drop=True)
    except Exception as exc:
        fallback_msg = (
            f"[APEX EVALUATION WARNING] Real data loading failed ({exc}). "
            "Falling back to synthetic evaluation data via generate_synthetic_training_data()."
        )
        logger.warning(fallback_msg)
        X_test, y_test, circuits = generate_synthetic_training_data(n_samples=n_test_samples, random_seed=999)
        df_test = pd.DataFrame({"circuit_id": circuits})

    preds = model.predict(X_test)
    n_actual = len(y_test)

    mae = mean_absolute_error(y_test, preds)
    rmse = float(np.sqrt(mean_squared_error(y_test, preds)))
    r2 = r2_score(y_test, preds) if len(np.unique(y_test)) > 1 else 0.0
    pearson_corr = 0.0
    spearman_corr = 0.0
    if (
        len(np.unique(y_test)) > 1
        and len(np.unique(preds)) > 1
        and float(np.std(y_test)) > 1e-9
        and float(np.std(preds)) > 1e-9
    ):
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=ConstantInputWarning)
            try:
                pr = pearsonr(y_test, preds)
                pr_val: Any = getattr(pr, "statistic", pr[0])
                pearson_corr = float(pr_val)
                sr = spearmanr(y_test, preds)
                sr_val: Any = getattr(sr, "statistic", sr[0])
                spearman_corr = float(sr_val)
            except Exception:
                pearson_corr = 0.0
                spearman_corr = 0.0

    # Conformal empirical coverage
    lower = preds - q_hat
    upper = preds + q_hat
    covered = (y_test >= lower) & (y_test <= upper)
    empirical_coverage = float(np.mean(covered))

    # Segmented evaluation by circuit type
    if "circuit_id" in df_test.columns:
        circuit_types = np.array([classify_circuit(str(c)) for c in df_test["circuit_id"]])
    else:
        circuit_types = np.array(["permanent"] * n_actual)

    segmented_metrics: Dict[str, Dict[str, Any]] = {}
    for c_type in ["permanent", "high_speed", "street"]:
        mask = np.asarray(circuit_types == c_type, dtype=bool)
        n_seg = int(np.sum(mask))
        if n_seg >= 5:
            seg_y = y_test[mask]
            seg_p = preds[mask]
            seg_mae = mean_absolute_error(seg_y, seg_p)
            seg_rmse = float(np.sqrt(mean_squared_error(seg_y, seg_p)))
            seg_r2 = r2_score(seg_y, seg_p) if len(np.unique(seg_y)) > 1 else 0.0
            seg_r = 0.0
            if (
                len(np.unique(seg_y)) > 1
                and len(np.unique(seg_p)) > 1
                and float(np.std(seg_y)) > 1e-9
                and float(np.std(seg_p)) > 1e-9
            ):
                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore", category=ConstantInputWarning)
                    try:
                        pr_seg = pearsonr(seg_y, seg_p)
                        pr_seg_val: Any = getattr(pr_seg, "statistic", pr_seg[0])
                        seg_r = float(pr_seg_val)
                    except Exception:
                        seg_r = 0.0
            seg_covered = float(np.mean((seg_y >= (seg_p - q_hat)) & (seg_y <= (seg_p + q_hat))))
            segmented_metrics[c_type] = {
                "n_samples": n_seg,
                "mae": round(seg_mae, 3),
                "rmse": round(seg_rmse, 3),
                "r2": round(seg_r2, 3),
                "pearson_r": round(seg_r, 3),
                "conformal_coverage": round(seg_covered, 3),
            }
        else:
            segmented_metrics[c_type] = {
                "n_samples": n_seg,
                "mae": None,
                "rmse": None,
                "r2": None,
                "pearson_r": None,
                "conformal_coverage": None,
            }

    # Evaluate asymmetric quantiles if present
    quantile_eval = {}
    if quantile_models and "p10" in quantile_models and "p90" in quantile_models:
        try:
            q10_p = quantile_models["p10"].predict(X_test)
            q90_p = quantile_models["p90"].predict(X_test)
            q_covered = (y_test >= q10_p) & (y_test <= q90_p)
            q_cov = float(np.mean(q_covered))
            q_widths = q90_p - q10_p

            pole_w = None
            mid_w = None
            if "grid_position" in df_test.columns:
                gp = np.asarray(df_test["grid_position"].values, dtype=float)
                pole_mask = gp <= 3
                mid_mask = (gp >= 8) & (gp <= 12)
                if np.any(pole_mask):
                    pole_w = round(float(np.mean(q_widths[pole_mask])), 2)
                if np.any(mid_mask):
                    mid_w = round(float(np.mean(q_widths[mid_mask])), 2)

            quantile_eval = {
                "target_coverage": 0.80,
                "empirical_coverage": round(q_cov, 3),
                "mean_interval_width": round(float(np.mean(q_widths)), 2),
                "pole_sitter_mean_width": pole_w,
                "midfield_mean_width": mid_w,
            }
        except Exception as q_err:
            logger.warning(f"[APEX Evaluation] Could not evaluate quantile models: {q_err}")

    report = {
        "model_version": model_artifact.get("version", "core-v1.0.0"),
        "test_samples": n_actual,
        "metrics": {
            "mae": round(mae, 3),
            "rmse": round(rmse, 3),
            "r2": round(r2, 3),
            "pearson_r": round(pearson_corr, 3),
            "spearman_rho": round(spearman_corr, 3),
            "conformal_target_coverage": 0.90,
            "empirical_coverage": round(empirical_coverage, 3),
            "mean_interval_width": round(float(2 * q_hat), 2),
        },
        "segmented_metrics": segmented_metrics,
        "quantile_metrics": quantile_eval,
        "status": "PASS" if empirical_coverage >= 0.85 else "WARN",
    }

    # Log structured summary table
    logger.info("==========================================================================================")
    logger.info("APEX MODEL TEMPORAL EVALUATION REPORT")
    logger.info(f"Test Samples: {n_actual} | Overall R²: {r2:.3f} | Overall MAE: {mae:.3f} pos")
    logger.info(f"Conformal Margin: ±{q_hat:.2f} (Empirical Coverage: {empirical_coverage*100:.1f}%)")
    logger.info("------------------------------------------------------------------------------------------")
    logger.info("CIRCUIT-SEGMENTED PERFORMANCE BREAKDOWN:")
    logger.info(f"{'Circuit Category':<16} | {'Samples':<8} | {'MAE (pos)':<10} | {'RMSE':<8} | {'R²':<8} | {'Coverage':<10}")
    logger.info("-" * 75)
    for c_type, m in segmented_metrics.items():
        if m["mae"] is not None:
            logger.info(
                f"{c_type.replace('_', '-').title():<16} | {m['n_samples']:<8} | {m['mae']:<10.2f} | {m['rmse']:<8.2f} | {m['r2']:<8.3f} | {m['conformal_coverage']*100:<9.1f}%"
            )
        else:
            logger.info(f"{c_type.replace('_', '-').title():<16} | {m['n_samples']:<8} | N/A        | N/A      | N/A      | N/A")
    logger.info("==========================================================================================")

    return report


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    from core.training.train import train_finishing_position_model
    artifact = train_finishing_position_model()
    eval_rep = evaluate_model_temporal(artifact)
    logger.info("Full Evaluation JSON:\n" + json.dumps(eval_rep, indent=2))
