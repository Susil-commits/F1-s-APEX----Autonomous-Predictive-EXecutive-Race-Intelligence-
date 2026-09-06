"""Lightweight Pre-Race Data Drift Monitoring for APEX Core.

Compares incoming race weekend distributions of grid_position, quali_delta_s,
and rain_prob against the historical training baseline statistics.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Union

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

DATA_CSV = os.path.join(os.path.dirname(__file__), "..", "data", "real_prerace_dataset.csv")

TARGET_FEATURES = ["grid_position", "quali_delta_s", "rain_prob"]

# Fallback reference stats from 2022-2024 training dataset (1,361 records)
DEFAULT_BASELINE_STATS: Dict[str, Dict[str, float]] = {
    "grid_position": {"mean": 10.50, "std": 5.76, "min": 1.0, "max": 20.0},
    "quali_delta_s": {"mean": 1.25, "std": 0.94, "min": 0.0, "max": 4.50},
    "rain_prob": {"mean": 0.08, "std": 0.12, "min": 0.0, "max": 0.85},
}


class WeekendDriftMonitor:
    """Monitors incoming race weekend priors against training baseline distributions."""

    def __init__(self, baseline_stats: Dict[str, Dict[str, float]] | None = None, csv_path: str = DATA_CSV):
        self.csv_path = csv_path
        self.baseline = baseline_stats or self._load_or_compute_baseline()

    @staticmethod
    def _clean_numeric_column(series: Any) -> np.ndarray:
        """Extracts valid finite floats from a series or iterable."""
        clean: List[float] = []
        for v in series:
            try:
                fv = float(v)
                if not np.isnan(fv):
                    clean.append(fv)
            except (ValueError, TypeError):
                continue
        return np.array(clean, dtype=float)

    def _load_or_compute_baseline(self) -> Dict[str, Dict[str, float]]:
        """Computes baseline mean and std directly from cached training data if available."""
        if os.path.exists(self.csv_path):
            try:
                df = pd.read_csv(self.csv_path)
                stats = {}
                for feat in TARGET_FEATURES:
                    if feat in df.columns:
                        vals = self._clean_numeric_column(df[feat])
                        computed_std = float(np.std(vals)) if len(vals) > 1 else 0.0
                        effective_std = round(computed_std, 3) if computed_std >= 0.05 else DEFAULT_BASELINE_STATS[feat]["std"]
                        stats[feat] = {
                            "mean": round(float(np.mean(vals)), 3) if len(vals) > 0 else DEFAULT_BASELINE_STATS[feat]["mean"],
                            "std": effective_std,
                            "min": round(float(np.min(vals)), 3) if len(vals) > 0 else DEFAULT_BASELINE_STATS[feat]["min"],
                            "max": round(float(np.max(vals)), 3) if len(vals) > 0 else DEFAULT_BASELINE_STATS[feat]["max"],
                        }
                    else:
                        stats[feat] = DEFAULT_BASELINE_STATS[feat]
                logger.info(f"[DriftMonitor] Initialized baseline stats from {self.csv_path}")
                return stats
            except Exception as e:
                logger.warning(f"[DriftMonitor] Failed to compute baseline from CSV ({e}); using defaults")
        return DEFAULT_BASELINE_STATS

    def check_weekend_drift(
        self,
        weekend_records: Union[List[Dict[str, Any]], pd.DataFrame],
        z_threshold: float = 2.0,
    ) -> Dict[str, Any]:
        """Evaluates whether incoming weekend distributions deviate significantly from training baseline.
        
        Uses standardized mean difference (z-distance):
            z_score = |sample_mean - baseline_mean| / baseline_std
        Flags any feature where z_score exceeds z_threshold.
        """
        if isinstance(weekend_records, list):
            if not weekend_records:
                return {
                    "status": "INSUFFICIENT_DATA",
                    "n_records": 0,
                    "drift_detected_features": [],
                    "features": {},
                }
            df = pd.DataFrame(weekend_records)
        else:
            df = weekend_records

        n_records = len(df)
        if n_records < 3:
            return {
                "status": "INSUFFICIENT_DATA",
                "n_records": n_records,
                "message": f"Sample count ({n_records}) is too small for statistical drift detection (minimum 3 records required).",
                "drift_detected_features": [],
                "features": {},
            }

        features_report: Dict[str, Dict[str, Any]] = {}
        drift_detected_features: List[str] = []

        for feat in TARGET_FEATURES:
            base = self.baseline.get(feat, DEFAULT_BASELINE_STATS.get(feat, {"mean": 0.0, "std": 1.0}))
            base_mean = base["mean"]
            base_std = base["std"] if base["std"] > 0 else 1.0

            if feat not in df.columns:
                features_report[feat] = {"error": "Feature missing from weekend records"}
                continue

            vals = self._clean_numeric_column(df[feat])
            if len(vals) == 0:
                features_report[feat] = {"error": "No valid numeric records found"}
                continue

            sample_mean = float(np.mean(vals))
            sample_std = float(np.std(vals)) if len(vals) > 1 else 0.0
            drift_score = abs(sample_mean - base_mean) / base_std
            is_drift: bool = True if drift_score > z_threshold else False

            if is_drift:
                drift_detected_features.append(feat)

            features_report[feat] = {
                "baseline_mean": round(base_mean, 3),
                "baseline_std": round(base_std, 3),
                "sample_mean": round(sample_mean, 3),
                "sample_std": round(sample_std, 3),
                "sample_min": round(float(np.min(vals)), 3),
                "sample_max": round(float(np.max(vals)), 3),
                "drift_score_z": round(drift_score, 3),
                "drift_detected": is_drift,
            }

        has_drift = len(drift_detected_features) > 0
        status = "DRIFT_DETECTED" if has_drift else "HEALTHY"

        report = {
            "status": status,
            "n_records": n_records,
            "z_threshold": z_threshold,
            "drift_detected_features": drift_detected_features,
            "features": features_report,
            "recommendation": (
                f"Feature distribution drift detected in: {', '.join(drift_detected_features)}. "
                "Investigate external factors (extreme weather, unusual penalties) or trigger retraining."
            ) if has_drift else "Feature distributions match training baseline within acceptable bounds.",
        }

        if has_drift:
            logger.warning(f"[DriftMonitor] {report['recommendation']}")
        else:
            logger.info("[DriftMonitor] Weekend distributions verified healthy.")

        return report
