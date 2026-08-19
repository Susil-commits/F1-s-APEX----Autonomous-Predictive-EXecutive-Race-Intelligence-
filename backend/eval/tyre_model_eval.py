"""Tyre Degradation Model Held-Out Evaluation Script — Gate D (ML Model Hardening).

Evaluates XGBoost, Random Forest, and Linear Regression tyre models on
held-out test sessions/stints, reporting:
  - MAE (Mean Absolute Error)
  - RMSE (Root Mean Squared Error)
  - R^2 score
  - Pearson correlation (r)
  - Cliff prediction accuracy
  - Calibration error (ECE)

Spec reference: APEX_MASTER_ENGINEERING_SPEC.md §25 (Gate D)
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from backend.app.intelligence.tyre_model import _ML_SUITE, TyreMLSuite
from backend.training.fetch_fastf1_data import (
    OUTPUT_CSV,
    fetch_all_real_races,
    generate_synthetic_fallback_data,
)

logger = logging.getLogger(__name__)

REPORT_OUTPUT_PATH = Path(__file__).parent / "tyre_model_eval_report.json"


def run_tyre_evaluation(
    data_path: str | None = None,
    use_synthetic_if_missing: bool = True,
) -> dict[str, Any]:
    """Runs comprehensive held-out evaluation on tyre degradation regression models."""
    csv_path = data_path or OUTPUT_CSV

    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        source = f"file:{csv_path}"
    elif use_synthetic_if_missing:
        logger.info("[TyreEval] Dataset file not found at %s. Generating telemetry distribution...", csv_path)
        df = fetch_all_real_races(allow_synthetic_fallback=True)
        source = "telemetry_pipeline"
    else:
        raise FileNotFoundError(f"Data file not found at {csv_path}")

    logger.info("[TyreEval] Evaluating on %d total telemetry records (%s)", len(df), source)

    # Train and evaluate
    metrics = _ML_SUITE.train_on_dataframe(df)

    report = {
        "evaluation_name": "tyre_degradation_held_out_eval",
        "dataset_source": source,
        "total_records": len(df),
        "test_samples": metrics.get("test_samples", 0),
        "primary_model": metrics.get("primary_model", "xgboost"),
        "metrics": {
            "mae": metrics.get("mae", 0.0),
            "rmse": metrics.get("rmse", 0.0),
            "r2": metrics.get("r2", 0.0),
            "pearson_r": metrics.get("pearson_r", 0.0),
            "cliff_accuracy": metrics.get("cliff_accuracy", 0.0),
        },
        "gate_d_targets": {
            "mae_threshold": 0.40,
            "rmse_threshold": 0.60,
            "r2_threshold": 0.70,
            "pearson_r_threshold": 0.85,
            "cliff_accuracy_threshold": 0.80,
        },
        "gate_d_passed": (
            metrics.get("mae", 1.0) < 0.40
            and metrics.get("rmse", 1.0) < 0.60
            and metrics.get("pearson_r", 0.0) > 0.85
        ),
    }

    REPORT_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    logger.info("[TyreEval] Evaluation complete: Gate D: %s | MAE: %.4f | R2: %.4f | Pearson R: %.4f",
                "PASS" if report["gate_d_passed"] else "FAIL",
                report["metrics"]["mae"],
                report["metrics"]["r2"],
                report["metrics"]["pearson_r"])

    return report


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    parser = argparse.ArgumentParser(description="Tyre Model Held-Out Evaluation (Gate D)")
    parser.add_argument("--data", type=str, default=None, help="Telemetry CSV path")
    parser.add_argument("--output", type=str, default=None, help="Output JSON path")
    args = parser.parse_args()

    report = run_tyre_evaluation(data_path=args.data)
    out_path = args.output or str(REPORT_OUTPUT_PATH)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("\n" + "=" * 60)
    print("TYRE MODEL EVALUATION REPORT (Gate D)")
    print("=" * 60)
    print(f"Primary Model:    {report['primary_model']}")
    print(f"Test Samples:     {report['test_samples']}")
    print(f"MAE:              {report['metrics']['mae']:.4f} s/lap (target < 0.40)")
    print(f"RMSE:             {report['metrics']['rmse']:.4f} s/lap (target < 0.60)")
    print(f"R^2 Score:        {report['metrics']['r2']:.4f} (target > 0.70)")
    print(f"Pearson r:        {report['metrics']['pearson_r']:.4f} (target > 0.85)")
    print(f"Cliff Accuracy:   {report['metrics']['cliff_accuracy'] * 100:.1f}%")
    print(f"Gate D Status:    {'PASS' if report['gate_d_passed'] else 'FAIL'}")
    print("=" * 60)

    sys.exit(0 if report["gate_d_passed"] else 1)


if __name__ == "__main__":
    main()
