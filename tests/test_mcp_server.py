"""Unit tests for APEX Model Context Protocol (MCP) Server."""
import json
import pytest
from httpx import ASGITransport, AsyncClient

from core.api.main import app
from core.mcp.server import ApexMCPServer


def test_mcp_server_initialize():
    server = ApexMCPServer()
    caps = server.get_server_capabilities()
    assert caps["protocolVersion"] == "2024-11-05"
    assert caps["serverInfo"]["name"] == "apex-f1-mcp-server"
    assert "tools" in caps["capabilities"]
    assert "resources" in caps["capabilities"]
    assert "prompts" in caps["capabilities"]


def test_mcp_server_list_tools():
    server = ApexMCPServer()
    tools = server.list_tools()
    tool_names = [t["name"] for t in tools]
    assert "apex_predict_grid" in tool_names
    assert "apex_simulate_pit_stop" in tool_names
    assert "apex_evaluate_tyre_cliff" in tool_names
    assert "apex_query_fia_regulations" in tool_names
    assert "apex_verify_model_integrity" in tool_names


def test_mcp_server_call_tool_tyre_cliff():
    server = ApexMCPServer()
    resp = server.call_tool(
        "apex_evaluate_tyre_cliff",
        {"compound": "C3", "lap_age": 18, "track_temp_c": 35.0},
    )
    assert resp["isError"] is False
    assert len(resp["content"]) == 1
    data = json.loads(resp["content"][0]["text"])
    assert data["compound"] == "C3"
    assert data["lap_age"] == 18
    assert data["degradation_sec_per_lap"] > 0.0
    assert "cliff_lap" in data


def test_mcp_server_call_tool_regulations():
    server = ApexMCPServer()
    resp = server.call_tool("apex_query_fia_regulations", {"query": "active aero 2026"})
    assert resp["isError"] is False
    data = json.loads(resp["content"][0]["text"])
    assert "Active Aerodynamics" in data["grounded_regulation"]


def test_mcp_server_resources():
    server = ApexMCPServer()
    res_list = server.list_resources()
    uris = [r["uri"] for r in res_list]
    assert "apex://circuits/catalog" in uris
    assert "apex://drivers/roster" in uris

    res_data = server.read_resource("apex://circuits/catalog")
    assert len(res_data["contents"]) == 1
    assert "silverstone" in res_data["contents"][0]["text"]


def test_mcp_server_prompts():
    server = ApexMCPServer()
    prompts = server.list_prompts()
    p_names = [p["name"] for p in prompts]
    assert "race_engineer_briefing" in p_names

    rendered = server.get_prompt(
        "race_engineer_briefing",
        {"driver_id": "NOR", "lap": 20, "recommended_action": "BOX_NOW"},
    )
    assert "messages" in rendered
    assert "NOR" in rendered["messages"][0]["content"]["text"]


@pytest.mark.asyncio
async def test_mcp_json_rpc_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Test tools/list via JSON-RPC 2.0
        resp = await ac.post(
            "/api/mcp",
            json={
                "jsonrpc": "2.0",
                "id": "req-1",
                "method": "tools/list",
                "params": {},
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == "req-1"
        assert "tools" in data["result"]

        # Test tools/call via JSON-RPC 2.0
        resp_call = await ac.post(
            "/api/mcp",
            json={
                "jsonrpc": "2.0",
                "id": "req-2",
                "method": "tools/call",
                "params": {
                    "name": "apex_query_fia_regulations",
                    "arguments": {"query": "drs"},
                },
            },
        )
        assert resp_call.status_code == 200
        call_data = resp_call.json()
        assert "result" in call_data
        assert "DRS" in call_data["result"]["content"][0]["text"]


@pytest.mark.asyncio
async def test_mcp_rest_discovery_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/mcp/capabilities")
        assert resp.status_code == 200
        assert resp.json()["serverInfo"]["name"] == "apex-f1-mcp-server"

        resp_tools = await ac.get("/api/mcp/tools")
        assert resp_tools.status_code == 200
        assert len(resp_tools.json()["tools"]) >= 5


def test_mcp_server_predict_grid_uses_real_model():
    server = ApexMCPServer()
    resp = server.call_tool(
        "apex_predict_grid",
        {
            "race_id": "silverstone",
            "rain_probability": 0.6,
            "grid_overrides": {"VER": 20, "SAR": 1},
        },
    )
    assert resp["isError"] is False
    data = json.loads(resp["content"][0]["text"])
    assert data["total_drivers"] == 20
    assert data["rain_probability"] == 0.6
    assert "model_version" in data
    first = data["grid"][0]
    assert "raw_score" in first
    assert "win_probability_pct" in first
    assert "podium_probability_pct" in first
    # With VER starting P20, VER should not remain trivially P1 from static roster order
    ver_entry = next((d for d in data["grid"] if d["driver_id"] == "VER"), None)
    assert ver_entry is not None
    assert ver_entry["grid_position"] == 20
    assert ver_entry["predicted_position"] > 1

