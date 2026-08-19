"""Tests for APEX Model Registry, SHA-256 integrity hashing, and drift detection."""
import pytest
from starlette.testclient import TestClient

from backend.app.intelligence.model_registry import ModelRegistry
from backend.app.main import app


def test_model_registry_manifest_load():
    """Verifies that the registry manifest loads cleanly with all expected models."""
    manifest = ModelRegistry.load_registry_manifest()
    assert "models" in manifest
    assert "apex_dqn" in manifest["models"]
    assert "calibrated_tyre_model" in manifest["models"]
    assert "pinn_tyre_residual" in manifest["models"]
    assert "shap_surrogate" in manifest["models"]


def test_verify_all_models_integrity():
    """Verifies that all on-disk model artifacts match their recorded SHA-256 hashes."""
    audit = ModelRegistry.verify_all_models()
    assert audit["overall_status"] == "ALL_MODELS_HEALTHY"
    assert audit["total_models"] >= 8
    assert audit["healthy_count"] == audit["total_models"]
    assert audit["drift_count"] == 0
    assert audit["missing_count"] == 0


def test_model_registry_api_endpoint():
    """Verifies that GET /api/models/registry returns valid JSON with health status."""
    client = TestClient(app)
    response = client.get("/api/models/registry")
    assert response.status_code == 200
    data = response.json()
    assert data["overall_status"] == "ALL_MODELS_HEALTHY"
    assert "models" in data
    assert "apex_dqn" in data["models"]
    assert data["models"]["apex_dqn"]["status"] == "HEALTHY"


def test_mcp_check_model_health():
    """Verifies that the MCP tool check_model_health executes and returns structured JSON."""
    import json
    from backend.app.mcp_server.server import check_model_health

    result_str = check_model_health()
    report = json.loads(result_str)
    assert report["overall_status"] == "ALL_MODELS_HEALTHY"
    assert report["healthy_count"] >= 8
