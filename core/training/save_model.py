"""Saves and versions trained APEX Core model artifacts."""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
import joblib

from core.training.train import train_finishing_position_model
from core.training.evaluate import evaluate_model_temporal

logger = logging.getLogger(__name__)

DEFAULT_MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "backend", "models")


def build_and_save_core_baseline(output_dir: str = DEFAULT_MODEL_DIR) -> str:
    """Trains, evaluates, and writes model artifact + evaluation metadata to disk."""
    os.makedirs(output_dir, exist_ok=True)
    model_path = os.path.join(output_dir, "apex_core_v1_model.joblib")
    meta_path = os.path.join(output_dir, "apex_core_v1_metadata.json")

    logger.info("[APEX Core] Training fresh baseline model...")
    artifact = train_finishing_position_model(save_path=model_path, random_seed=42)
    eval_report = evaluate_model_temporal(artifact)

    meta = {
        "model_version": artifact["version"],
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "feature_names": artifact["feature_names"],
        "q_hat_margin": artifact["q_hat_margin"],
        "metrics": eval_report["metrics"],
        "status": eval_report["status"],
    }
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    logger.info(f"[APEX Core] Saved model to {model_path} and metadata to {meta_path}")
    return model_path


if __name__ == "__main__":
    saved = build_and_save_core_baseline()
    print(f"Model saved successfully to: {saved}")
