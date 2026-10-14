"""Pre-Race Data Drift Monitoring for APEX Core.

Two complementary monitors are shipped:

1. **WeekendDriftMonitor** (baseline-statistics drift):
   Compares the mean of incoming race-weekend data against the training-set
   mean using a z-score (standardised mean difference). Fast and interpretable;
   requires only the mean and std stored at training time.

2. **PsiDriftMonitor** (Population Stability Index):
   Computes PSI = Σ (P_actual − P_expected) · ln(P_actual / P_expected) over
   equal-frequency bins built from the training distribution. PSI is the
   industry-standard scalar for covariate shift.

   Standard thresholds:
     PSI < 0.10  → stable (no significant drift)
     0.10 ≤ PSI < 0.25 → moderate / minor shift (monitor closely)
     PSI ≥ 0.25  → major drift (consider retraining)
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Union

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

DATA_CSV = os.path.join(os.path.dirname(__file__), "..", "data", "real_prerace_dataset.csv")
DEFAULT_PSI_BINS_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "apex_core_v1_psi_bins.json")

TARGET_FEATURES = ["grid_position", "quali_delta_s", "rain_prob"]

# Fallback reference stats from 2022-2024 training dataset (1,361 records)
DEFAULT_BASELINE_STATS: Dict[str, Dict[str, float]] = {
    "grid_position": {"mean": 10.50, "std": 5.76, "min": 1.0, "max": 20.0},
    "quali_delta_s": {"mean": 1.25, "std": 0.94, "min": 0.0, "max": 4.50},
    "rain_prob": {"mean": 0.08, "std": 0.12, "min": 0.0, "max": 0.85},
}


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


class PsiDriftMonitor:
    """Population Stability Index (PSI) drift detector.

    PSI measures how much a new distribution has shifted relative to a reference
    (training) distribution by binning both into the same equal-frequency buckets
    and comparing proportions.

    Standard thresholds:
      PSI < 0.10  → no significant drift (stable)
      0.10 ≤ PSI < 0.25 → minor / moderate shift — investigate
      PSI ≥ 0.25  → major drift — trigger retraining

    Usage::
        monitor = PsiDriftMonitor()
        monitor.fit(training_df[["grid_position", "quali_delta_s", "rain_prob"]])
        result = monitor.compute(incoming_df)
    """

    PSI_STABLE = 0.10
    PSI_WARN = 0.25
    DEFAULT_N_BINS = 10

    def __init__(self, n_bins: int = DEFAULT_N_BINS):
        self.n_bins = n_bins
        self._bin_edges: Dict[str, np.ndarray] = {}
        self._ref_proportions: Dict[str, np.ndarray] = {}
        self._fitted = False

    def fit(self, reference_df: Any, features: List[str] = TARGET_FEATURES) -> "PsiDriftMonitor":
        """Compute equal-frequency bin edges and reference proportions from training data."""
        if isinstance(reference_df, list):
            reference_df = pd.DataFrame(reference_df)

        for feat in features:
            if feat not in reference_df.columns:
                logger.warning(f"[PSI] Feature '{feat}' not found in reference data — skipping.")
                continue
            vals = _clean_numeric_column(reference_df[feat])
            if len(vals) < self.n_bins * 2:
                logger.warning(f"[PSI] Not enough reference samples for '{feat}' — need ≥ {self.n_bins * 2}.")
                continue
            # Equal-frequency quantile edges
            quantiles = np.linspace(0.0, 100.0, self.n_bins + 1)
            edges = np.unique(np.percentile(vals, quantiles))
            if len(edges) < 3:
                # Fall back to equal-width if all values are identical or very low diversity
                edges = np.linspace(vals.min() - 1e-9, vals.max() + 1e-9, self.n_bins + 1)
            edges[0] = -np.inf
            edges[-1] = np.inf
            counts, _ = np.histogram(vals, bins=edges)
            proportions = counts / counts.sum()
            # Replace zeros to avoid division-by-zero in PSI log term
            proportions = np.where(proportions == 0, 1e-4, proportions)
            self._bin_edges[feat] = edges
            self._ref_proportions[feat] = proportions

        self._fitted = True
        return self

    def compute(
        self,
        incoming: Any,
        features: List[str] = TARGET_FEATURES,
    ) -> Dict[str, Any]:
        """Compute PSI for each feature between training reference and incoming data.

        Returns a dict with per-feature PSI values and an overall status.
        """
        if not self._fitted:
            raise RuntimeError("PsiDriftMonitor must be fitted before calling compute().")

        if isinstance(incoming, list):
            incoming = pd.DataFrame(incoming)

        results: Dict[str, Any] = {}
        for feat in features:
            if feat not in self._bin_edges:
                results[feat] = {"error": "Feature not fitted (missing from reference or insufficient data)"}
                continue
            if feat not in incoming.columns:
                results[feat] = {"error": "Feature missing from incoming data"}
                continue

            vals = _clean_numeric_column(incoming[feat])
            if len(vals) == 0:
                results[feat] = {"error": "No valid numeric records in incoming data"}
                continue

            counts, _ = np.histogram(vals, bins=self._bin_edges[feat])
            proportions = counts / counts.sum()
            proportions = np.where(proportions == 0, 1e-4, proportions)

            ref_p = self._ref_proportions[feat]
            # PSI = Σ (actual - expected) * ln(actual / expected)
            psi = float(np.sum((proportions - ref_p) * np.log(proportions / ref_p)))

            if psi < self.PSI_STABLE:
                status = "STABLE"
            elif psi < self.PSI_WARN:
                status = "MINOR_SHIFT"
            else:
                status = "MAJOR_DRIFT"

            results[feat] = {
                "psi": round(psi, 4),
                "status": status,
                "n_incoming": len(vals),
                "n_bins": len(ref_p),
            }

        drifted = [f for f, v in results.items() if isinstance(v, dict) and v.get("status") == "MAJOR_DRIFT"]
        overall = "MAJOR_DRIFT" if drifted else (
            "MINOR_SHIFT" if any(
                isinstance(v, dict) and v.get("status") == "MINOR_SHIFT" for v in results.values()
            ) else "STABLE"
        )

        report = {
            "overall_status": overall,
            "drifted_features": drifted,
            "features": results,
        }
        if overall == "MAJOR_DRIFT":
            logger.warning(f"[PSI] Major drift detected in: {drifted}. Retraining recommended.")
        elif overall == "MINOR_SHIFT":
            logger.info("[PSI] Minor shift detected — monitor closely.")
        else:
            logger.info("[PSI] All features stable.")

        return report

    def to_dict(self) -> Dict[str, Any]:
        """Serializes fitted bin edges and reference proportions to a JSON-serializable dict."""
        return {
            "n_bins": self.n_bins,
            "fitted": self._fitted,
            "bin_edges": {
                feat: [
                    "-Infinity" if np.isneginf(x) else ("Infinity" if np.isposinf(x) else float(x))
                    for x in edges
                ]
                for feat, edges in self._bin_edges.items()
            },
            "ref_proportions": {
                feat: [float(p) for p in props]
                for feat, props in self._ref_proportions.items()
            },
            "features": list(self._bin_edges.keys()),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PsiDriftMonitor":
        """Reconstructs a fitted PsiDriftMonitor from serialized dict."""
        monitor = cls(n_bins=data.get("n_bins", cls.DEFAULT_N_BINS))
        for feat, edges in data.get("bin_edges", {}).items():
            parsed_edges = []
            for x in edges:
                if x == "-Infinity" or x == -float("inf") or x == "-inf":
                    parsed_edges.append(-np.inf)
                elif x == "Infinity" or x == float("inf") or x == "inf":
                    parsed_edges.append(np.inf)
                else:
                    parsed_edges.append(float(x))
            monitor._bin_edges[feat] = np.array(parsed_edges, dtype=float)

        for feat, props in data.get("ref_proportions", {}).items():
            monitor._ref_proportions[feat] = np.array(props, dtype=float)

        monitor._fitted = bool(data.get("fitted", True))
        return monitor

    def save(self, filepath: str) -> None:
        """Persists fitted reference bins to disk as JSON."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)
        logger.info(f"[PSI] Saved reference bins to {filepath}")

    @classmethod
    def load(cls, filepath: str) -> "PsiDriftMonitor":
        """Loads fitted reference bins from JSON file."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info(f"[PSI] Loaded reference bins from {filepath}")
        return cls.from_dict(data)


class WeekendDriftMonitor:
    """Monitors incoming race weekend priors against training baseline distributions.

    Combines standardized z-score checks against training mean/std with
    Population Stability Index (PSI) covariate shift detection.
    """

    def __init__(
        self,
        baseline_stats: Dict[str, Dict[str, float]] | None = None,
        csv_path: str = DATA_CSV,
        psi_monitor: PsiDriftMonitor | None = None,
        psi_bins_path: str = DEFAULT_PSI_BINS_PATH,
    ):
        self.csv_path = csv_path
        self.psi_bins_path = psi_bins_path
        self.baseline = baseline_stats or self._load_or_compute_baseline()
        self.psi_monitor = psi_monitor or self._load_or_fit_psi_monitor()

    @staticmethod
    def _clean_numeric_column(series: Any) -> np.ndarray:
        return _clean_numeric_column(series)

    def _load_or_compute_baseline(self) -> Dict[str, Dict[str, float]]:
        """Computes baseline mean and std directly from cached training data if available."""
        if os.path.exists(self.csv_path):
            try:
                df = pd.read_csv(self.csv_path)
                stats = {}
                for feat in TARGET_FEATURES:
                    if feat in df.columns:
                        vals = _clean_numeric_column(df[feat])
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

    def _load_or_fit_psi_monitor(self) -> PsiDriftMonitor:
        """Loads persisted PSI reference bins from disk or fits on cached training CSV."""
        if os.path.exists(self.psi_bins_path):
            try:
                return PsiDriftMonitor.load(self.psi_bins_path)
            except Exception as e:
                logger.warning(f"[DriftMonitor] Failed to load PSI bins from {self.psi_bins_path} ({e}); falling back to CSV fit")

        if os.path.exists(self.csv_path):
            try:
                df = pd.read_csv(self.csv_path)
                train_df = df[df["season"] < 2024] if "season" in df.columns else df
                monitor = PsiDriftMonitor()
                monitor.fit(train_df, features=TARGET_FEATURES)
                logger.info(f"[DriftMonitor] Fitted PsiDriftMonitor on {len(train_df)} rows from {self.csv_path}")
                return monitor
            except Exception as e:
                logger.warning(f"[DriftMonitor] Failed to fit PSI monitor from CSV ({e})")

        return PsiDriftMonitor()

    def check_weekend_drift(
        self,
        weekend_records: Union[List[Dict[str, Any]], pd.DataFrame],
        z_threshold: float = 2.0,
    ) -> Dict[str, Any]:
        """Evaluates whether incoming weekend distributions deviate significantly from training baseline.

        Returns both standardized z-score (|sample_mean - baseline_mean| / baseline_std)
        and Population Stability Index (PSI) per feature with standard 0.10/0.25 thresholds.
        """
        if isinstance(weekend_records, list):
            if not weekend_records:
                return {
                    "status": "INSUFFICIENT_DATA",
                    "n_records": 0,
                    "drift_detected_features": [],
                    "psi_drifted_features": [],
                    "psi_status": "INSUFFICIENT_DATA",
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
                "psi_drifted_features": [],
                "psi_status": "INSUFFICIENT_DATA",
                "features": {},
            }

        features_report: Dict[str, Dict[str, Any]] = {}
        drift_detected_features: List[str] = []

        # Run PSI monitor if fitted
        psi_report: Dict[str, Any] = {}
        if self.psi_monitor and self.psi_monitor._fitted:
            try:
                psi_report = self.psi_monitor.compute(df, features=TARGET_FEATURES)
            except Exception as e:
                logger.warning(f"[DriftMonitor] PSI computation failed: {e}")

        psi_features = psi_report.get("features", {})
        psi_drifted_features: List[str] = psi_report.get("drifted_features", [])
        overall_psi_status: str = psi_report.get("overall_status", "UNKNOWN")

        for feat in TARGET_FEATURES:
            base = self.baseline.get(feat, DEFAULT_BASELINE_STATS.get(feat, {"mean": 0.0, "std": 1.0}))
            base_mean = base["mean"]
            base_std = base["std"] if base["std"] > 0 else 1.0

            if feat not in df.columns:
                features_report[feat] = {"error": "Feature missing from weekend records"}
                continue

            vals = _clean_numeric_column(df[feat])
            if len(vals) == 0:
                features_report[feat] = {"error": "No valid numeric records found"}
                continue

            sample_mean = float(np.mean(vals))
            sample_std = float(np.std(vals)) if len(vals) > 1 else 0.0
            drift_score = abs(sample_mean - base_mean) / base_std
            is_drift: bool = True if drift_score > z_threshold else False

            if is_drift:
                drift_detected_features.append(feat)

            feat_psi_info = psi_features.get(feat, {})
            feat_psi = feat_psi_info.get("psi") if isinstance(feat_psi_info, dict) else None
            feat_psi_status = feat_psi_info.get("status") if isinstance(feat_psi_info, dict) else "UNKNOWN"

            features_report[feat] = {
                "baseline_mean": round(base_mean, 3),
                "baseline_std": round(base_std, 3),
                "sample_mean": round(sample_mean, 3),
                "sample_std": round(sample_std, 3),
                "sample_min": round(float(np.min(vals)), 3),
                "sample_max": round(float(np.max(vals)), 3),
                "drift_score_z": round(drift_score, 3),
                "drift_detected": is_drift,
                "z_drift_detected": is_drift,
                "psi": round(feat_psi, 4) if feat_psi is not None else None,
                "psi_status": feat_psi_status,
                "psi_drift_detected": feat_psi_status == "MAJOR_DRIFT",
            }

        has_z_drift = len(drift_detected_features) > 0
        status = "DRIFT_DETECTED" if has_z_drift else "HEALTHY"

        recommendations: List[str] = []
        if has_z_drift:
            recommendations.append(f"Z-score mean drift detected in: {', '.join(drift_detected_features)}.")
        if psi_drifted_features:
            recommendations.append(f"Major PSI covariate shift (PSI ≥ 0.25) detected in: {', '.join(psi_drifted_features)}.")

        rec_msg = (
            " ".join(recommendations) + " Investigate external factors (extreme weather, unusual grid penalties) or trigger retraining."
            if recommendations
            else "Feature distributions match training baseline within acceptable bounds."
        )

        report = {
            "status": status,
            "n_records": n_records,
            "z_threshold": z_threshold,
            "psi_thresholds": {
                "stable": PsiDriftMonitor.PSI_STABLE,
                "major": PsiDriftMonitor.PSI_WARN,
            },
            "drift_detected_features": drift_detected_features,
            "psi_drifted_features": psi_drifted_features,
            "psi_status": overall_psi_status,
            "features": features_report,
            "recommendation": rec_msg,
        }

        if has_z_drift or psi_drifted_features:
            logger.warning(f"[DriftMonitor] {report['recommendation']}")
        else:
            logger.info("[DriftMonitor] Weekend distributions verified healthy.")

        return report
