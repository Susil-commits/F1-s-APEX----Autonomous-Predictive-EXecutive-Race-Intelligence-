"""Unit tests for Phase 6, 7 & 8: PPO, Hybrid Decision Engine, Emergency Brain, and Risk Engine."""
from backend.app.intelligence.emergency_brain import EmergencyBrain
from backend.app.intelligence.risk_engine import RiskEngine
from backend.app.simulator.engine import RaceSimulator
from backend.app.simulator.models import SafetyCarStatus, StrategyAction, TrackCondition
from backend.app.strategy.hybrid_decision_engine import HybridDecisionAggregator
from backend.app.strategy.ppo_agent import PPOStrategyAgent


def test_ppo_agent_inference():
    sim = RaceSimulator(track_name="silverstone", seed=42)
    state = sim.step()
    agent = PPOStrategyAgent()
    action, conf = agent.select_action(state)
    assert isinstance(action, StrategyAction)
    assert 0.0 <= conf <= 1.0


def test_hybrid_decision_aggregator():
    sim = RaceSimulator(track_name="silverstone", seed=42)
    for _ in range(12):
        sim.step()
    state = sim.get_state()

    aggregator = HybridDecisionAggregator()
    decision = aggregator.evaluate_decision(state)

    assert isinstance(decision.recommendation, StrategyAction)
    assert 0.0 <= decision.confidence_score <= 1.0
    assert len(decision.primary_factors) > 0
    assert "counterfactual_summary" in decision.model_dump()
    assert decision.risk_score >= 0.0


def test_emergency_brain_weather_trigger():
    sim = RaceSimulator(track_name="silverstone", seed=42)
    sim.step()
    # Inject heavy rain
    sim.inject_weather(TrackCondition.WET, rain_intensity=0.85)
    state = sim.get_state()

    emergency = EmergencyBrain.process_state(state)
    assert emergency is not None
    assert emergency.event_type == "SUDDEN_RAIN"
    assert emergency.recommended_action == StrategyAction.PIT_WET
    assert emergency.severity == "CRITICAL"


def test_emergency_brain_safety_car_trigger():
    sim = RaceSimulator(track_name="silverstone", seed=42, enable_dynamic_weather=False)
    # Simulate forward until tyres have wear
    for _ in range(18):
        sim.step()
    sim.inject_safety_car(SafetyCarStatus.SAFETY_CAR, laps=4)
    state = sim.get_state()

    emergency = EmergencyBrain.process_state(state)
    assert emergency is not None
    assert emergency.event_type == "SAFETY_CAR_DEPLOYED"
    assert emergency.recommended_action in (StrategyAction.PIT_HARD, StrategyAction.PIT_MEDIUM)


def test_risk_engine_evaluation():
    sim = RaceSimulator(track_name="silverstone", seed=42)
    for _ in range(25):
        sim.step()
    state = sim.get_state()

    risk_state = RiskEngine.evaluate_risk(state)
    assert 0.0 <= risk_state.overall_risk_score <= 1.0
    assert 0.0 <= risk_state.tyre_blowout_risk <= 1.0
    assert 0.0 <= risk_state.traffic_undercut_risk <= 1.0
    assert 0.0 <= risk_state.dnf_risk <= 1.0
