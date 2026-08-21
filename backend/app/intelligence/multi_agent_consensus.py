"""Multi-Agent Pit Wall Consensus & Deliberation Engine for APEX.

Simulates an F1 pit wall team comprising 5 specialized autonomous agents:
1. Chief Race Strategist
2. Tyre & Degradation Specialist
3. Meteorological Officer
4. Powertrain & Systems Health Engineer
5. Driver Performance Coach

The agents debate in real time using domain-specific telemetry features, cast weighted votes,
and generate a synthesized consensus action with a debate dialogue transcript.
"""
import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.app.simulator.models import RaceState, StrategyAction, TyreCompound


class AgentProposal(BaseModel):
    agent_id: str
    agent_name: str
    role_title: str
    avatar_color: str
    proposed_action: StrategyAction
    confidence: float = Field(ge=0.0, le=1.0)
    urgency: str  # LOW | MEDIUM | HIGH | CRITICAL
    primary_rationale: str
    key_metric_label: str
    key_metric_value: str
    weighted_vote_weight: float


class PitWallConsensus(BaseModel):
    timestamp_utc: str
    lap: int
    consensus_action: StrategyAction
    consensus_confidence: float
    consensus_strength: str  # UNANIMOUS | STRONG_MAJORITY | SPLIT_DECISION | OVERRULE
    action_vote_distribution: Dict[str, float]
    proposals: List[AgentProposal]
    dissenting_views: List[str]
    pitwall_radio_transcript: List[Dict[str, str]]
    executive_verdict: str


class MultiAgentPitWallEngine:
    """Orchestrates real-time multi-agent debate and weighted voting across the pit wall."""

    _instance: Optional["MultiAgentPitWallEngine"] = None

    @classmethod
    def get_instance(cls) -> "MultiAgentPitWallEngine":
        if cls._instance is None:
            cls._instance = MultiAgentPitWallEngine()
        return cls._instance

    def evaluate_pitwall_consensus(self, state: RaceState, target_car_id: Optional[str] = None) -> PitWallConsensus:
        """Executes multi-agent deliberation and aggregates weighted voting."""
        player = next(
            (c for c in state.cars if (target_car_id and c.car_id == target_car_id) or c.is_player),
            state.cars[0] if state.cars else None,
        )

        current_lap = state.current_lap
        total_laps = state.total_laps
        laps_remaining = max(1, total_laps - current_lap)
        tyre_wear = player.tyre_wear_pct if player else 30.0
        tyre_compound = player.tyre_compound if player else TyreCompound.MEDIUM
        is_slick = tyre_compound in (TyreCompound.SOFT, TyreCompound.MEDIUM, TyreCompound.HARD)
        rain_intensity = state.weather.rain_intensity
        rain_prob = state.weather.rain_probability_next_5_laps
        track_wetness = state.weather.track_wetness
        sc_status = str(state.safety_car.value if hasattr(state.safety_car, "value") else state.safety_car)
        is_neutralized = sc_status in ("SAFETY_CAR", "VSC")
        position = player.position if player else 1

        proposals: List[AgentProposal] = []
        transcript: List[Dict[str, str]] = []

        # --- 1. Chief Race Strategist (Weight: 0.30) ---
        strat_action = StrategyAction.MAINTAIN
        strat_conf = 0.85
        strat_urgency = "LOW"
        strat_rationale = f"Track position P{position} is protected. Current lap delta within target window."

        if (rain_intensity > 0.50 or track_wetness > 0.50) and is_slick:
            strat_action = StrategyAction.PIT_WET
            strat_conf = 0.95
            strat_urgency = "CRITICAL"
            strat_rationale = f"Torrential track wetness ({track_wetness:.2f}). Mandatory pit stop for Full Wet tyres."
        elif (rain_intensity > 0.20 or track_wetness > 0.20) and is_slick:
            strat_action = StrategyAction.PIT_INTER
            strat_conf = 0.90
            strat_urgency = "HIGH"
            strat_rationale = "Intermediate crossover threshold reached. Box for Intermediate tyres."
        elif is_neutralized and tyre_wear > 40.0:
            strat_action = StrategyAction.PIT_HARD if tyre_compound != TyreCompound.HARD else StrategyAction.PIT_MEDIUM
            strat_conf = 0.95
            strat_urgency = "HIGH"
            strat_rationale = f"Free pit stop opportunity under {sc_status}. Box now to minimize stationary time loss."
        elif tyre_wear > 75.0:
            strat_action = StrategyAction.PIT_HARD
            strat_conf = 0.90
            strat_urgency = "HIGH"
            strat_rationale = "Tyres nearing critical threshold. Box required to avoid undercut."
        elif position > 3 and laps_remaining > 15:
            strat_action = StrategyAction.PUSH
            strat_conf = 0.78
            strat_rationale = "Gap to car ahead is closing. Push mode active to attempt overtake."

        proposals.append(
            AgentProposal(
                agent_id="chief_strategist",
                agent_name="James V.",
                role_title="Chief Race Strategist",
                avatar_color="#00E5FF",
                proposed_action=strat_action,
                confidence=strat_conf,
                urgency=strat_urgency,
                primary_rationale=strat_rationale,
                key_metric_label="Expected Net Delta",
                key_metric_value="+14.2s vs Stay Out" if is_neutralized else "+1.8s",
                weighted_vote_weight=0.30,
            )
        )
        transcript.append({
            "speaker": "James (Strategist)",
            "message": f"Lap {current_lap}: We are running P{position}. {strat_rationale}",
            "tone": "tactical",
        })

        # --- 2. Tyre & Degradation Specialist (Weight: 0.25) ---
        tyre_action = StrategyAction.MAINTAIN
        tyre_conf = 0.82
        tyre_urgency = "LOW"
        cliff_est = max(1, int((85.0 - tyre_wear) / 2.8))

        if (rain_intensity > 0.50 or track_wetness > 0.50) and is_slick:
            tyre_action = StrategyAction.PIT_WET
            tyre_conf = 0.95
            tyre_urgency = "CRITICAL"
            tyre_rationale = "Hydroplaning risk on slicks. Immediate switch to Full Wets required."
        elif (rain_intensity > 0.20 or track_wetness > 0.20) and is_slick:
            tyre_action = StrategyAction.PIT_INTER
            tyre_conf = 0.90
            tyre_urgency = "HIGH"
            tyre_rationale = "Standing water on track. Slicks cannot maintain thermal operating window."
        elif tyre_wear >= 70.0:
            tyre_action = StrategyAction.PIT_HARD
            tyre_conf = 0.94
            tyre_urgency = "CRITICAL"
            tyre_rationale = f"Thermal degradation cliff reached at {tyre_wear:.1f}% wear. Surface blistered."
        elif tyre_wear >= 50.0:
            tyre_action = StrategyAction.CONSERVE
            tyre_conf = 0.75
            tyre_urgency = "MEDIUM"
            tyre_rationale = f"Tyre wear at {tyre_wear:.1f}%. Manage rear surface temps to extend stint {cliff_est} laps."
        else:
            tyre_rationale = f"Tyre degradation linear on {tyre_compound.value}. Cliff horizon ~{cliff_est} laps."

        proposals.append(
            AgentProposal(
                agent_id="tyre_specialist",
                agent_name="Hiroshi T.",
                role_title="Tyre & Thermal Specialist",
                avatar_color="#FF9100",
                proposed_action=tyre_action,
                confidence=tyre_conf,
                urgency=tyre_urgency,
                primary_rationale=tyre_rationale,
                key_metric_label="Estimated Cliff Horizon",
                key_metric_value=f"{cliff_est} laps ({tyre_wear:.1f}% wear)",
                weighted_vote_weight=0.25,
            )
        )
        transcript.append({
            "speaker": "Hiroshi (Tyres)",
            "message": tyre_rationale,
            "tone": "technical",
        })

        # --- 3. Meteorological Officer (Weight: 0.20) ---
        wx_action = StrategyAction.MAINTAIN
        wx_conf = 0.88
        wx_urgency = "LOW"
        wx_rationale = "Doppler radar clear. Track bone dry with optimal grip."

        if rain_intensity > 0.60 or track_wetness > 0.60:
            wx_action = StrategyAction.PIT_WET
            wx_conf = 0.96
            wx_urgency = "CRITICAL"
            wx_rationale = f"Torrential rain ({rain_intensity*100:.0f}% intensity). Crossover threshold to Full Wets reached."
        elif rain_intensity > 0.20 or rain_prob > 0.65 or track_wetness > 0.20:
            wx_action = StrategyAction.PIT_INTER
            wx_conf = 0.90
            wx_urgency = "HIGH"
            wx_rationale = f"Rain cell over Turn 4 in 2 minutes. Intermediate crossover imminent."
        elif rain_prob > 0.35:
            wx_action = StrategyAction.MAINTAIN
            wx_conf = 0.70
            wx_rationale = "25% rain probability next 5 laps. Hold slick compound and monitor radar."

        proposals.append(
            AgentProposal(
                agent_id="met_officer",
                agent_name="Sarah M.",
                role_title="Senior Meteorologist",
                avatar_color="#00E676",
                proposed_action=wx_action,
                confidence=wx_conf,
                urgency=wx_urgency,
                primary_rationale=wx_rationale,
                key_metric_label="Track Wetness Index",
                key_metric_value=f"{track_wetness:.2f} (Rain: {rain_intensity*100:.0f}%)",
                weighted_vote_weight=0.20,
            )
        )
        transcript.append({
            "speaker": "Sarah (Weather)",
            "message": wx_rationale,
            "tone": "observational",
        })

        # --- 4. Powertrain & Systems Health Engineer (Weight: 0.15) ---
        pu_action = StrategyAction.MAINTAIN
        pu_conf = 0.85
        pu_urgency = "LOW"
        pu_health = 92.4
        pu_rationale = "ICE and MGU-K operating within nominal thermal envelopes. ERS deployment ready."

        if is_neutralized:
            pu_action = StrategyAction.ENERGY_HARVEST
            pu_conf = 0.88
            pu_rationale = "Under neutralization: Set ERS dial to Harvest 8 to recharge state of charge to 100%."
        elif laps_remaining <= 5 and position > 1:
            pu_action = StrategyAction.ENERGY_DEPLOY
            pu_conf = 0.91
            pu_rationale = "Final stint sprint: Discharge maximum 120kW MGU-K battery energy for overtake."

        proposals.append(
            AgentProposal(
                agent_id="powertrain_engineer",
                agent_name="Marco R.",
                role_title="Power Unit & ERS Engineer",
                avatar_color="#D500F9",
                proposed_action=pu_action,
                confidence=pu_conf,
                urgency=pu_urgency,
                primary_rationale=pu_rationale,
                key_metric_label="Powertrain Health",
                key_metric_value=f"{pu_health}% (Nominal)",
                weighted_vote_weight=0.15,
            )
        )
        transcript.append({
            "speaker": "Marco (Power Unit)",
            "message": pu_rationale,
            "tone": "systems",
        })

        # --- 5. Driver Performance Coach (Weight: 0.10) ---
        coach_action = StrategyAction.MAINTAIN
        coach_conf = 0.80
        coach_urgency = "LOW"
        coach_rationale = "Driver rhythm consistent. Sector 2 delta -0.12s vs reference."

        if position > 1 and laps_remaining > 5 and not (rain_intensity > 0.30 and is_slick):
            coach_action = StrategyAction.ATTACK
            coach_conf = 0.82
            coach_rationale = "Closing delta +0.4s/lap. Ready to execute overtake sequence into Turn 6."

        proposals.append(
            AgentProposal(
                agent_id="driver_coach",
                agent_name="Riccardo D.",
                role_title="Driver Performance Coach",
                avatar_color="#FFD600",
                proposed_action=coach_action,
                confidence=coach_conf,
                urgency=coach_urgency,
                primary_rationale=coach_rationale,
                key_metric_label="Driver Consistency",
                key_metric_value="98.2% (Low Fatigue)",
                weighted_vote_weight=0.10,
            )
        )
        transcript.append({
            "speaker": "Riccardo (Coach)",
            "message": coach_rationale,
            "tone": "driver_coach",
        })

        # --- Weighted Vote Aggregation ---
        vote_scores: Dict[str, float] = {}
        for p in proposals:
            action_key = p.proposed_action.value
            weighted_score = p.confidence * p.weighted_vote_weight
            vote_scores[action_key] = vote_scores.get(action_key, 0.0) + weighted_score

        winning_action_str = max(vote_scores.keys(), key=lambda a: vote_scores[a])
        winning_action = StrategyAction(winning_action_str)
        total_weight = sum(vote_scores.values())
        consensus_confidence = round(vote_scores[winning_action_str] / total_weight, 3) if total_weight > 0 else 0.85

        # Dissenting views analysis
        dissenting: List[str] = []
        for p in proposals:
            if p.proposed_action != winning_action:
                dissenting.append(f"{p.role_title} ({p.agent_name}) favoured {p.proposed_action.value}: {p.primary_rationale}")

        if len(dissenting) == 0:
            consensus_strength = "UNANIMOUS"
            verdict = f"All 5 pit wall specialists are fully aligned on {winning_action.value}."
        elif len(dissenting) <= 2:
            consensus_strength = "STRONG_MAJORITY"
            verdict = f"Strong pit wall consensus for {winning_action.value} ({consensus_confidence*100:.0f}% support)."
        else:
            consensus_strength = "SPLIT_DECISION"
            verdict = f"Split pit wall debate. Chief Strategist priority overrules dissent for {winning_action.value}."

        return PitWallConsensus(
            timestamp_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            lap=current_lap,
            consensus_action=winning_action,
            consensus_confidence=consensus_confidence,
            consensus_strength=consensus_strength,
            action_vote_distribution={k: round(v, 3) for k, v in vote_scores.items()},
            proposals=proposals,
            dissenting_views=dissenting,
            pitwall_radio_transcript=transcript,
            executive_verdict=verdict,
        )


multi_agent_engine = MultiAgentPitWallEngine.get_instance()
