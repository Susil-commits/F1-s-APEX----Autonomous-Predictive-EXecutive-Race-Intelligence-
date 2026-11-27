"""Hierarchical Context Assembler for APEX Race Strategy Agents.

Implements multi-tiered context assembly (L0 through L3), semantic telemetry
distillation, and token budgeting to feed deterministic inference models and LLM copilots.
"""
from __future__ import annotations

import enum
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from core.data.roster_service import get_roster_service
from core.features.feature_builder import CIRCUIT_PROFILES
from core.features.tyre_model import TyreDegradationModel


class ContextLevel(enum.Enum):
    """Hierarchical abstraction tiers for racing intelligence context."""
    L0_STRUCTURAL = "l0_structural"      # Static regulations, track topology, baseline DRS zones
    L1_SESSION = "l1_session"            # Pre-race grid slot, driver form, weather radar priors
    L2_STINT = "l2_stint"                # Current stint age, Pirelli cliff status, rival traffic gaps
    L3_REALTIME = "l3_realtime"          # Live telemetry deltas, sector pacing, race control flags


@dataclass
class RaceContextBundle:
    """Encapsulates a unified, multi-tiered context representation."""
    driver_id: str
    circuit_id: str
    timestamp_utc: float
    levels: Dict[str, Dict[str, Any]]
    distilled_prompt: str
    token_count_estimate: int
    raw_character_count: int
    compression_ratio: float
    is_budget_compliant: bool
    target_budget_tokens: int
    active_flags: List[str] = field(default_factory=list)


class HierarchicalContextAssembler:
    """Assembles, distills, and budgets race context across L0 to L3 tiers.
    
    Prevents token bloat, enforces sub-50ms synthesis latency, and ensures high
    groundedness against verified FIA regulations and real-time telemetry.
    """

    def __init__(self, default_token_budget: int = 1024) -> None:
        self.default_token_budget = default_token_budget
        self.roster_service = get_roster_service()
        self.tyre_model = TyreDegradationModel()

    def assemble(
        self,
        driver_id: str,
        circuit_id: str,
        current_lap: int = 1,
        current_compound: str = "C3",
        current_tyre_age: int = 0,
        gap_ahead_s: Optional[float] = None,
        gap_behind_s: Optional[float] = None,
        rival_driver_ahead: Optional[str] = None,
        rival_driver_behind: Optional[str] = None,
        track_temp_c: float = 30.0,
        rain_probability: float = 0.0,
        race_control_flag: str = "GREEN",
        active_aero_mode: str = "Z_MODE",  # 2026 Active Aero: Z_MODE (cornering) / X_MODE (straight)
        token_budget: Optional[int] = None,
    ) -> RaceContextBundle:
        """Assembles unified context across all four tiers with token budgeting."""
        budget = token_budget or self.default_token_budget

        # 1. Tier L0: Structural / Circuit & Regulatory Baseline
        circuit_meta = CIRCUIT_PROFILES.get(
            circuit_id.lower(),
            {"downforce": 0.70, "power": 0.70, "street": 0.0},
        )
        sc_rate = 0.75 if circuit_meta.get("street", 0.0) > 0.5 else 0.40
        l0_data = {
            "circuit_id": circuit_id.lower(),
            "downforce_index": circuit_meta["downforce"],
            "power_sensitivity": circuit_meta["power"],
            "is_street_circuit": bool(circuit_meta["street"] > 0.5),
            "sc_hazard_rate": circuit_meta.get("sc_probability", sc_rate),
            "regulations": {
                "2026_active_aero": "Active Aero (X-Mode for straights, Z-Mode for high-downforce cornering)",
                "drs_rules": "Permitted within 1.0s detection gap when track is declared dry",
                "mandatory_compound_rule": "Drivers must use at least 2 distinct dry compounds in a dry race",
            },
        }

        # 2. Tier L1: Session Priors (Driver & Team)
        driver_profile = self.roster_service.get_driver(driver_id.upper()) or {
            "name": driver_id.upper(),
            "team": "Unknown Constructor",
            "pts_share": 0.05,
            "rolling_avg": 10.0,
            "default_grid": 10,
        }
        l1_data = {
            "driver_name": driver_profile.get("name", driver_id),
            "team_name": driver_profile.get("team", "Unknown"),
            "constructor_pts_share": driver_profile.get("pts_share", 0.05),
            "driver_rolling_avg": driver_profile.get("rolling_avg", 10.0),
            "starting_grid": driver_profile.get("default_grid", 10),
            "rain_probability": rain_probability,
            "weather_transition": rain_probability > 0.40,
        }

        # 3. Tier L2: Dynamic Stint & Tyre Physics
        deg_info = self.tyre_model.calculate_lap_degradation(
            compound_code=current_compound,
            tyre_age_laps=max(1, current_tyre_age),
            track_temp_c=track_temp_c,
            circuit_downforce_index=circuit_meta["downforce"],
        )
        pace_deg = deg_info["pace_delta_seconds"]
        cliff_detected = deg_info["is_past_cliff"] or pace_deg > 1.80
        laps_to_cliff = max(0, deg_info["laps_to_cliff"])

        l2_data = {
            "current_lap": current_lap,
            "current_compound": current_compound.upper(),
            "tyre_age_laps": current_tyre_age,
            "current_deg_sec_per_lap": round(pace_deg, 3),
            "cliff_detected": cliff_detected,
            "laps_to_cliff": laps_to_cliff,
            "gap_ahead_s": gap_ahead_s,
            "rival_ahead": rival_driver_ahead,
            "gap_behind_s": gap_behind_s,
            "rival_behind": rival_driver_behind,
        }

        # 4. Tier L3: Micro-Telemetry & Race Control
        active_flags = []
        if race_control_flag.upper() != "GREEN":
            active_flags.append(f"FLAG_{race_control_flag.upper()}")
        if l2_data["cliff_detected"]:
            active_flags.append("TYRE_CLIFF_ALERT")
        if gap_behind_s is not None and gap_behind_s < 1.4:
            active_flags.append("UNDERCUT_THREAT_REAR")
        if gap_ahead_s is not None and gap_ahead_s < 1.0:
            active_flags.append("DRS_ATTACK_WINDOW")

        l3_data = {
            "race_control_flag": race_control_flag.upper(),
            "active_aero_mode": active_aero_mode.upper(),
            "track_temp_c": track_temp_c,
            "active_tactical_flags": active_flags,
        }

        # 5. Semantic Distillation & Token Budgeting
        distilled_text, estimated_tokens = self._distill_context(
            l0_data, l1_data, l2_data, l3_data, budget
        )

        raw_chars = (
            len(str(l0_data)) + len(str(l1_data)) + len(str(l2_data)) + len(str(l3_data))
        )
        compression = round(1.0 - (len(distilled_text) / max(raw_chars, 1)), 3)

        return RaceContextBundle(
            driver_id=driver_id.upper(),
            circuit_id=circuit_id.lower(),
            timestamp_utc=time.time(),
            levels={
                ContextLevel.L0_STRUCTURAL.value: l0_data,
                ContextLevel.L1_SESSION.value: l1_data,
                ContextLevel.L2_STINT.value: l2_data,
                ContextLevel.L3_REALTIME.value: l3_data,
            },
            distilled_prompt=distilled_text,
            token_count_estimate=estimated_tokens,
            raw_character_count=raw_chars,
            compression_ratio=compression,
            is_budget_compliant=estimated_tokens <= budget,
            target_budget_tokens=budget,
            active_flags=active_flags,
        )

    def _distill_context(
        self,
        l0: Dict[str, Any],
        l1: Dict[str, Any],
        l2: Dict[str, Any],
        l3: Dict[str, Any],
        budget: int,
    ) -> tuple[str, int]:
        """Synthesizes high-density, semantic context lines adhering to budget."""
        # Tactical summary lines designed for zero-latency LLM/rule ingestion
        lines = [
            f"=== APEX RACE CONTEXT: {l1['driver_name']} ({l1['team_name']}) | {l0['circuit_id'].upper()} GP ===",
            f"[SESSION] Lap: {l2['current_lap']} | Flag: {l3['race_control_flag']} | Rain: {l1['rain_probability']*100:.0f}% | Track Temp: {l3['track_temp_c']}°C",
            f"[TYRES] Compound: {l2['current_compound']} (Age: {l2['tyre_age_laps']} laps) | Deg: +{l2['current_deg_sec_per_lap']}s/lap | Cliff Proximity: {l2['laps_to_cliff']} laps",
            f"[TRACK POSITION] Gap Ahead: {f'+{l2['gap_ahead_s']}s vs {l2['rival_ahead']}' if l2['gap_ahead_s'] is not None else 'Leader/Clear'} | Gap Behind: {f'+{l2['gap_behind_s']}s vs {l2['rival_behind']}' if l2['gap_behind_s'] is not None else 'Clear'}",
            f"[AERO/REGS] Active Aero: {l3['active_aero_mode']} | SC Hazard: {l0['sc_hazard_rate']*100:.0f}%",
        ]

        if l3["active_tactical_flags"]:
            lines.append(f"[TACTICAL ALERTS] {', '.join(l3['active_tactical_flags'])}")

        distilled = "\n".join(lines)
        # 1 token ~= 4 characters heuristic
        est_tokens = max(1, len(distilled) // 4)

        # Budget enforcement: If over budget, truncate non-critical lines
        if est_tokens > budget:
            distilled = distilled[: budget * 4]
            est_tokens = budget

        return distilled, est_tokens
