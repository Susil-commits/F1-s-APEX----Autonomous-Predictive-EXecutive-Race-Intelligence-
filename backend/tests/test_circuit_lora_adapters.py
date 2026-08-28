"""Unit and integration tests for Multi-Circuit LoRA fine-tuning and evaluation."""
import json
import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.main import app
from backend.app.mcp_server.server import get_circuit_lora_adapters
from backend.training.circuit_lora_benchmark import (
    CIRCUIT_PROFILES,
    generate_circuit_stint_dataset,
    train_circuit_lora_adapter,
)


def test_circuit_profiles_definitions():
    """Verify all 4 core Grand Prix circuits are defined with distinct physical parameters."""
    for circuit_id in ["monaco", "monza", "spa", "silverstone"]:
        assert circuit_id in CIRCUIT_PROFILES
        prof = CIRCUIT_PROFILES[circuit_id]
        assert "name" in prof
        assert "downforce" in prof
        assert "pit_delta_s" in prof
        assert "stint_wear_multiplier" in prof


def test_circuit_dataset_generation_properties():
    """Verify circuit-specific telemetry feature generation."""
    X_monaco, y_bid_monaco, y_act_monaco = generate_circuit_stint_dataset("monaco", n_samples=50, seed=1)
    X_monza, y_bid_monza, y_act_monza = generate_circuit_stint_dataset("monza", n_samples=50, seed=1)

    assert X_monaco.shape == (50, 8, 28)
    assert y_bid_monaco.shape == (50, 1)
    assert y_act_monaco.shape == (50,)
    assert not (y_bid_monaco == y_bid_monza).all()


def test_train_single_circuit_lora_smoke(tmp_path):
    """Smoke test quick 2-epoch LoRA adapter training."""
    summary = train_circuit_lora_adapter("monaco", epochs=2, batch_size=16)
    assert summary["circuit_id"] == "monaco"
    assert summary["trainable_pct"] <= 10.0
    assert "val_mae_seconds" in summary


def test_mcp_get_circuit_lora_adapters():
    """Verify MCP server tool returns valid circuit benchmarks JSON."""
    res_str = get_circuit_lora_adapters()
    data = json.loads(res_str)
    assert "circuits_evaluated" in data
    assert data["circuits_evaluated"] >= 4
    assert "circuit_benchmarks" in data
    assert "monaco" in data["circuit_benchmarks"]


@pytest.mark.asyncio
async def test_api_circuit_lora_adapters_endpoint():
    """Verify GET /api/training/circuit-adapters returns report structure."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/training/circuit-adapters")
        assert res.status_code == 200
        data = res.json()
        assert "circuit_benchmarks" in data
        assert "parameter_reduction_vs_full_model" in data
