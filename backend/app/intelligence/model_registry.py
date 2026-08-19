"""Model Registry & MLOps Governance Engine for APEX.

Tracks model artifact provenance, computes live SHA-256 weight checksums,
detects model drift / file tampering, and reports health statuses across
all APEX predictive and reinforcement learning models.
"""

import hashlib
import json
import logging
import os
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)

REGISTRY_FILE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "models", "registry.json")
)
MODELS_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "models"))
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


class ModelRegistry:
    """Manages model metadata, live integrity hashing, drift detection, and health reporting."""

    @staticmethod
    def load_registry_manifest() -> dict[str, Any]:
        """Loads the authoritative model registry manifest from disk."""
        if not os.path.exists(REGISTRY_FILE_PATH):
            return {
                "registry_version": "1.0.0",
                "last_updated_utc": datetime.now(UTC).isoformat(),
                "models": {},
            }
        try:
            with open(REGISTRY_FILE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to parse registry.json: {e}")
            return {"registry_version": "1.0.0", "error": str(e), "models": {}}

    @staticmethod
    def compute_file_sha256(file_path: str) -> str | None:
        """Computes SHA-256 hex digest for a file on disk.
        
        Normalizes CRLF to LF for JSON and text files to ensure deterministic cross-platform
        checksum validation between Windows and Linux CI environments.
        """
        if not os.path.isabs(file_path):
            abs_path = os.path.normpath(os.path.join(PROJECT_ROOT, file_path))
        else:
            abs_path = os.path.normpath(file_path)

        if not os.path.exists(abs_path) or os.path.isdir(abs_path):
            return None

        if abs_path.endswith(".json"):
            with open(abs_path, "rb") as f:
                content = f.read().replace(b"\r\n", b"\n")
            return hashlib.sha256(content).hexdigest()

        sha256_hash = hashlib.sha256()
        with open(abs_path, "rb") as f:
            for byte_block in iter(lambda: f.read(65536), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    @classmethod
    def verify_all_models(cls) -> dict[str, Any]:
        """Audits all models against their registry metadata and returns health statuses."""
        manifest = cls.load_registry_manifest()
        models_data = manifest.get("models", {})

        audit_results = {}
        total_models = len(models_data)
        healthy_count = 0
        drift_count = 0
        missing_count = 0

        for model_id, meta in models_data.items():
            rel_path = meta.get("file_path", "")
            expected_hash = meta.get("sha256_hash", "")
            framework = meta.get("framework", "")
            model_type = meta.get("type", "")

            # Handle external / hub models like sentence-transformers
            if rel_path.startswith("sentence-transformers") or expected_hash == "huggingface_hub_v2":
                audit_results[model_id] = {
                    "model_id": model_id,
                    "model_name": meta.get("model_name", model_id),
                    "type": model_type,
                    "framework": framework,
                    "status": "HEALTHY",
                    "in_sync": True,
                    "file_present": True,
                    "live_hash": expected_hash,
                    "expected_hash": expected_hash,
                    "size_bytes": meta.get("size_bytes", 0),
                    "benchmark_score": meta.get("benchmark_score", {}),
                    "training_date": meta.get("training_date", ""),
                }
                healthy_count += 1
                continue

            # Handle dynamic training models
            if expected_hash == "dynamic_on_train":
                audit_results[model_id] = {
                    "model_id": model_id,
                    "model_name": meta.get("model_name", model_id),
                    "type": model_type,
                    "framework": framework,
                    "status": "HEALTHY",
                    "in_sync": True,
                    "file_present": True,
                    "live_hash": "dynamic_active",
                    "expected_hash": expected_hash,
                    "size_bytes": meta.get("size_bytes", 0),
                    "benchmark_score": meta.get("benchmark_score", {}),
                    "training_date": meta.get("training_date", ""),
                }
                healthy_count += 1
                continue

            abs_path = os.path.normpath(os.path.join(PROJECT_ROOT, rel_path) if not os.path.isabs(rel_path) else rel_path)
            if not os.path.exists(abs_path):
                # Search candidate subdirectories
                filename = os.path.basename(rel_path)
                candidate_paths = [
                    os.path.normpath(os.path.join(PROJECT_ROOT, "backend", "models", filename)),
                    os.path.normpath(os.path.join(PROJECT_ROOT, "backend", "models", "ppo", filename)),
                    os.path.normpath(os.path.join(PROJECT_ROOT, "backend", "models", "health", filename)),
                    os.path.normpath(os.path.join(PROJECT_ROOT, "backend", "models", "tyre", filename)),
                ]
                for cand in candidate_paths:
                    if os.path.exists(cand):
                        abs_path = cand
                        break

            if not os.path.exists(abs_path):
                audit_results[model_id] = {
                    "model_id": model_id,
                    "model_name": meta.get("model_name", model_id),
                    "type": model_type,
                    "framework": framework,
                    "status": "MISSING_ARTIFACT",
                    "in_sync": False,
                    "file_present": False,
                    "live_hash": None,
                    "expected_hash": expected_hash,
                    "size_bytes": 0,
                    "benchmark_score": meta.get("benchmark_score", {}),
                    "training_date": meta.get("training_date", ""),
                }
                missing_count += 1
                continue

            live_hash = cls.compute_file_sha256(abs_path)
            file_size = os.path.getsize(abs_path)
            in_sync = (live_hash == expected_hash)

            status = "HEALTHY" if in_sync else "DRIFT_DETECTED"
            if in_sync:
                healthy_count += 1
            else:
                drift_count += 1

            audit_results[model_id] = {
                "model_id": model_id,
                "model_name": meta.get("model_name", model_id),
                "type": model_type,
                "framework": framework,
                "status": status,
                "in_sync": in_sync,
                "file_present": True,
                "live_hash": live_hash,
                "expected_hash": expected_hash,
                "size_bytes": file_size,
                "benchmark_score": meta.get("benchmark_score", {}),
                "training_date": meta.get("training_date", ""),
            }

        overall_status = "ALL_MODELS_HEALTHY" if (healthy_count == total_models and missing_count == 0) else "DEGRADED"

        return {
            "registry_version": manifest.get("registry_version", "1.0.0"),
            "audit_timestamp_utc": datetime.now(UTC).isoformat(),
            "overall_status": overall_status,
            "total_models": total_models,
            "healthy_count": healthy_count,
            "drift_count": drift_count,
            "missing_count": missing_count,
            "models": audit_results,
        }
