"""APEX Model Context Protocol (MCP) Server.

Implements the open Model Context Protocol (JSON-RPC 2.0) standard to expose
APEX's predictive models, Monte Carlo pit simulator, tyre degradation physics,
and FIA regulatory RAG to external AI agents, IDEs, and pit wall clients.
"""
from __future__ import annotations

import json
import logging
import os
import time
from typing import Any, Dict, List

import numpy as np

from core.data.roster_service import get_roster_service
from core.features.feature_builder import CIRCUIT_PROFILES, PreRaceFeatureBuilder
from core.features.tyre_model import TyreDegradationModel
from core.security.model_integrity import verify_model_integrity
from core.simulation.monte_carlo import MonteCarloRaceSimulator

logger = logging.getLogger(__name__)

MCP_PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "apex-f1-mcp-server"
SERVER_VERSION = "1.2.0"


class ApexMCPServer:
    """Enterprise Model Context Protocol Server for APEX Race Intelligence."""

    def __init__(self) -> None:
        self.roster_service = get_roster_service()
        self.tyre_model = TyreDegradationModel()
        self.monte_carlo = MonteCarloRaceSimulator()

    def get_server_capabilities(self) -> Dict[str, Any]:
        """Returns protocol capabilities supported by the APEX MCP Server."""
        return {
            "protocolVersion": MCP_PROTOCOL_VERSION,
            "serverInfo": {
                "name": SERVER_NAME,
                "version": SERVER_VERSION,
            },
            "capabilities": {
                "tools": {"listChanged": False},
                "resources": {"subscribe": False, "listChanged": False},
                "prompts": {"listChanged": False},
            },
        }

    # ── TOOLS ─────────────────────────────────────────────────────────────────

    def list_tools(self) -> List[Dict[str, Any]]:
        """Lists all registered tools exposed to MCP agent clients."""
        return [
            {
                "name": "apex_predict_grid",
                "description": "Predicts finishing positions and conformal uncertainty intervals for all 20 drivers in a Formula 1 Grand Prix.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "race_id": {
                            "type": "string",
                            "description": "Grand Prix identifier (e.g. 'silverstone', 'monaco', 'monza')",
                        },
                        "rain_probability": {
                            "type": "number",
                            "description": "Forecasted rain probability [0.0 to 1.0]",
                            "default": 0.0,
                        },
                        "weather_transition": {
                            "type": "boolean",
                            "description": "True if weather transition is expected mid-race",
                            "default": False,
                        },
                    },
                    "required": ["race_id"],
                },
            },
            {
                "name": "apex_simulate_pit_stop",
                "description": "Runs 10,000 Monte Carlo rollouts modeling tyre degradation, VSC/SC hazard rates, pit lane transit deltas, and undercut expectation.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "race_id": {"type": "string", "description": "Grand Prix venue identifier"},
                        "current_lap": {"type": "integer", "description": "Current race lap"},
                        "current_position": {"type": "integer", "description": "Current track position [1-20]"},
                        "current_compound": {"type": "string", "description": "Tyre compound code (C1 to C5)", "default": "C3"},
                        "current_tyre_age": {"type": "integer", "description": "Laps completed on current tyres", "default": 10},
                        "simulations_count": {"type": "integer", "description": "Monte Carlo iteration count", "default": 5000},
                        "rain_probability": {"type": "number", "description": "Forecasted rain probability [0.0 to 1.0]", "default": 0.0},
                    },
                    "required": ["race_id", "current_lap", "current_position"],
                },
            },
            {
                "name": "apex_evaluate_tyre_cliff",
                "description": "Physics-informed evaluation of Pirelli tyre degradation and the non-linear thermal cliff drop-off lap.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "compound": {"type": "string", "description": "Compound code (C1 through C5)", "default": "C3"},
                        "lap_age": {"type": "integer", "description": "Current tyre age in laps"},
                        "track_temp_c": {"type": "number", "description": "Track temperature in Celsius", "default": 30.0},
                    },
                    "required": ["compound", "lap_age"],
                },
            },
            {
                "name": "apex_query_fia_regulations",
                "description": "Retrieves grounded FIA Technical and Sporting Regulations (2026 Active Aero, DRS, Parc Fermé, Tyre rules).",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Regulatory question or topic"},
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "apex_verify_model_integrity",
                "description": "Cryptographically audits the HMAC-SHA256 signature and SHA-256 hash of the active ML model artifact.",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                },
            },
        ]

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatches tool execution and wraps response in MCP standard schema."""
        start = time.perf_counter()

        if name == "apex_predict_grid":
            from core.api.predict import estimate_finish_probabilities, get_core_model

            race_id = str(arguments.get("race_id", "silverstone"))
            circuit_id = race_id.lower().replace("_2024", "").replace("_2025", "")
            rain_prob = float(np.clip(float(arguments.get("rain_probability", 0.0)), 0.0, 1.0))
            weather_trans = bool(arguments.get("weather_transition", False))
            grid_overrides = arguments.get("grid_overrides") or {}

            drivers = self.roster_service.get_all_drivers(active_only=True)[:20]
            artifact = get_core_model()
            model = artifact["model"]
            q_hat = float(artifact.get("q_hat_margin", 2.0))

            feature_matrix: List[np.ndarray] = []
            for d in drivers:
                code = d["code"]
                grid = int(grid_overrides.get(code, d.get("default_grid", 10)))
                feat_vec, _ = PreRaceFeatureBuilder.extract_features(
                    grid_position=grid,
                    quali_delta_s=max(0.0, (grid - 1) * 0.12),
                    rolling_avg_finish=float(d.get("rolling_avg", 10.0)),
                    circuit_starts=int(d.get("starts", 5)),
                    constructor_pts_share=float(d.get("pts_share", 0.05)),
                    circuit_id=circuit_id,
                    rain_prob=rain_prob,
                    weather_transition=weather_trans,
                )
                feature_matrix.append(feat_vec)

            X = np.array(feature_matrix, dtype=np.float32)
            raw_preds = model.predict(X)
            indexed_scores = sorted(enumerate(raw_preds), key=lambda item: float(item[1]))

            residual_std = float(artifact.get("residual_std", max(1.0, q_hat / 1.645)))
            results = []
            for rank_idx, (orig_idx, score) in enumerate(indexed_scores, start=1):
                d = drivers[orig_idx]
                raw_val = float(score)
                lower = max(1, int(np.floor(raw_val - q_hat)))
                upper = min(20, int(np.ceil(raw_val + q_hat)))
                win_prob, podium_prob = estimate_finish_probabilities(raw_val, residual_std, rank_pos=rank_idx)
                results.append({
                    "driver_id": d["code"],
                    "driver_name": d["name"],
                    "team": d["team"],
                    "grid_position": int(grid_overrides.get(d["code"], d.get("default_grid", 10))),
                    "predicted_position": rank_idx,
                    "raw_score": round(raw_val, 2),
                    "conformal_interval": [lower, upper],
                    "win_probability_pct": win_prob,
                    "podium_probability_pct": podium_prob,
                })
            content = {
                "race_id": race_id,
                "rain_probability": rain_prob,
                "weather_transition": weather_trans,
                "model_version": artifact.get("version", "core-v1.0.0"),
                "total_drivers": len(results),
                "grid": results,
                "latency_ms": round((time.perf_counter() - start) * 1000.0, 2),
            }

        elif name == "apex_simulate_pit_stop":
            race_id = arguments.get("race_id", "silverstone")
            lap = arguments.get("current_lap", 20)
            pos = arguments.get("current_position", 3)
            compound = arguments.get("current_compound", "C3")
            age = arguments.get("current_tyre_age", 12)
            n_sims = arguments.get("simulations_count", 3000)
            rain_prob = float(arguments.get("rain_probability", 0.0))

            sim_result = self.monte_carlo.simulate_strategy_comparison(
                circuit_id=race_id,
                current_lap=lap,
                current_pos=pos,
                current_compound=compound,
                current_tyre_age=age,
                n_simulations=n_sims,
                rain_probability=rain_prob,
            )
            content = sim_result

        elif name == "apex_evaluate_tyre_cliff":
            compound = arguments.get("compound", "C3")
            age = arguments.get("lap_age", 15)
            temp = arguments.get("track_temp_c", 30.0)
            deg_info = self.tyre_model.calculate_lap_degradation(
                compound_code=compound, tyre_age_laps=age, track_temp_c=temp
            )
            spec = self.tyre_model.compounds.get(compound.upper(), self.tyre_model.compounds["C3"])
            cliff_lap = spec.cliff_lap
            content = {
                "compound": compound.upper(),
                "lap_age": age,
                "degradation_sec_per_lap": round(deg_info["pace_delta_seconds"], 3),
                "cliff_lap": cliff_lap,
                "laps_remaining_to_cliff": max(0, deg_info["laps_to_cliff"]),
                "cliff_triggered": deg_info["is_past_cliff"] or deg_info["pace_delta_seconds"] > 1.80,
            }

        elif name == "apex_query_fia_regulations":
            from core.api.narration import get_regulations_store

            query = str(arguments.get("query", "")).strip()
            store = get_regulations_store()
            matches = store.retrieve(query, top_k=2, threshold=0.05) if query else []
            if matches:
                top = matches[0]
                grounded = f"{top['topic']} ({top['article']}): {top['excerpt']}"
            else:
                grounded = (
                    "FIA Sporting Regulations: Drivers must use at least two distinct dry-weather "
                    "compounds during a dry Grand Prix unless intermediate or wet tyres are fitted."
                )
            content = {
                "query": query,
                "grounded_regulation": grounded,
                "matches": matches,
            }

        elif name == "apex_verify_model_integrity":
            model_path = os.path.join(os.path.dirname(__file__), "..", "models", "apex_core_v1_model.joblib")
            sig_path = model_path + ".sig"
            is_valid, msg = verify_model_integrity(model_path, sig_path)
            content = {
                "is_valid": is_valid,
                "verification_message": msg,
                "algorithm": "HMAC-SHA256",
            }
        else:
            raise ValueError(f"Unknown MCP tool: {name}")

        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(content, indent=2),
                }
            ],
            "isError": False,
        }

    # ── RESOURCES ─────────────────────────────────────────────────────────────

    def list_resources(self) -> List[Dict[str, Any]]:
        """Lists resources available for inspection via MCP."""
        return [
            {
                "uri": "apex://circuits/catalog",
                "name": "F1 Circuit Engineering Profiles Catalog",
                "description": "Downforce indices, power sensitivities, and safety car hazard rates for all 24 Grand Prix tracks.",
                "mimeType": "application/json",
            },
            {
                "uri": "apex://drivers/roster",
                "name": "Live Formula 1 Driver Roster",
                "description": "Driver profiles, team affiliations, points share, and short-term rolling averages.",
                "mimeType": "application/json",
            },
            {
                "uri": "apex://regulations/2026_active_aero",
                "name": "2026 Active Aerodynamics and MGU-K Regulations",
                "description": "Official FIA technical specifications for Z-Mode, X-Mode, and 350kW electrical boost.",
                "mimeType": "text/markdown",
            },
            {
                "uri": "apex://monitoring/drift_thresholds",
                "name": "MLOps PSI and Z-Score Drift Thresholds",
                "description": "Population Stability Index monitoring specifications and drift thresholds.",
                "mimeType": "application/json",
            },
        ]

    def read_resource(self, uri: str) -> Dict[str, Any]:
        """Resolves and returns resource content."""
        if uri == "apex://circuits/catalog":
            text = json.dumps(CIRCUIT_PROFILES, indent=2)
            mime = "application/json"
        elif uri == "apex://drivers/roster":
            text = json.dumps(self.roster_service.get_all_drivers(), indent=2)
            mime = "application/json"
        elif uri == "apex://regulations/2026_active_aero":
            text = (
                "# 2026 FIA Technical Regulations: Active Aerodynamics\n\n"
                "- **Z-Mode**: High-downforce baseline active during cornering phases.\n"
                "- **X-Mode**: Low-drag low-downforce straightline mode active to reduce drag.\n"
                "- **Manual Override Mode (MOM)**: 350kW electrical deploy within 1.0s gap at 290+ km/h."
            )
            mime = "text/markdown"
        elif uri == "apex://monitoring/drift_thresholds":
            text = json.dumps({
                "psi_stable": 0.10,
                "psi_warning": 0.25,
                "z_score_threshold": 2.0,
                "action_on_major_drift": "Trigger CI/CD model retraining pipeline",
            }, indent=2)
            mime = "application/json"
        else:
            raise ValueError(f"Resource URI not found: {uri}")

        return {
            "contents": [
                {
                    "uri": uri,
                    "mimeType": mime,
                    "text": text,
                }
            ]
        }

    # ── PROMPTS ───────────────────────────────────────────────────────────────

    def list_prompts(self) -> List[Dict[str, Any]]:
        """Lists standardized prompt templates for race engineer interactions."""
        return [
            {
                "name": "race_engineer_briefing",
                "description": "Synthesizes tactical radio briefing for a driver entering a pit window.",
                "arguments": [
                    {"name": "driver_id", "description": "Driver code (e.g. 'NOR')", "required": True},
                    {"name": "lap", "description": "Current lap number", "required": True},
                    {"name": "recommended_action", "description": "Action (BOX_NOW, STAY_OUT)", "required": True},
                ],
            },
            {
                "name": "undercut_threat_analysis",
                "description": "Detailed multi-lap tactical assessment of undercut vs overcut risk against a rival.",
                "arguments": [
                    {"name": "driver_id", "description": "Our driver", "required": True},
                    {"name": "rival_id", "description": "Rival driver behind/ahead", "required": True},
                    {"name": "gap_seconds", "description": "Current interval in seconds", "required": True},
                ],
            },
        ]

    def get_prompt(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Renders prompt templates with provided arguments."""
        if name == "race_engineer_briefing":
            driver = arguments.get("driver_id", "NOR")
            lap = arguments.get("lap", 18)
            action = arguments.get("recommended_action", "BOX_NOW")
            messages = [
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": (
                            f"Generate an authentic, concise Formula 1 race engineer radio call for driver {driver} on lap {lap}. "
                            f"Recommended strategic action is '{action}'. Cite tyre compound and delta."
                        ),
                    },
                }
            ]
        elif name == "undercut_threat_analysis":
            driver = arguments.get("driver_id", "VER")
            rival = arguments.get("rival_id", "NOR")
            gap = arguments.get("gap_seconds", "1.2")
            messages = [
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": (
                            f"Analyze undercut threat between {driver} and rival {rival} with current interval {gap}s. "
                            f"Evaluate fresh tyre out-lap pace delta and provide optimal pit window response."
                        ),
                    },
                }
            ]
        else:
            raise ValueError(f"Unknown prompt template: {name}")

        return {"description": f"Rendered prompt: {name}", "messages": messages}

    # ── JSON-RPC 2.0 HANDLER ──────────────────────────────────────────────────

    def handle_json_rpc(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handles standard JSON-RPC 2.0 MCP requests."""
        req_id = request_data.get("id")
        method = request_data.get("method")
        params = request_data.get("params", {})

        try:
            if method == "initialize":
                result = self.get_server_capabilities()
            elif method == "tools/list":
                result = {"tools": self.list_tools()}
            elif method == "tools/call":
                tool_name = params.get("name")
                tool_args = params.get("arguments", {})
                result = self.call_tool(tool_name, tool_args)
            elif method == "resources/list":
                result = {"resources": self.list_resources()}
            elif method == "resources/read":
                uri = params.get("uri")
                result = self.read_resource(uri)
            elif method == "prompts/list":
                result = {"prompts": self.list_prompts()}
            elif method == "prompts/get":
                prompt_name = params.get("name")
                prompt_args = params.get("arguments", {})
                result = self.get_prompt(prompt_name, prompt_args)
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"},
                }

            return {"jsonrpc": "2.0", "id": req_id, "result": result}

        except Exception as e:
            logger.error(f"MCP error handling method {method}: {str(e)}", exc_info=True)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32000, "message": str(e)},
            }
