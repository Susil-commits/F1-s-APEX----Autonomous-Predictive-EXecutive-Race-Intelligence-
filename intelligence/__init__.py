"""APEX Intelligence (Tier 2) — Live Race Strategy, Digital Twin & Physics-Informed ML.

Components:
- strategy: Monte Carlo tree search, DQN / PPO reinforcement learning, counterfactual optimizer.
- models: Real-time tyre degradation, weather forecasting, driver performance, and vehicle health models.
- simulator: Millisecond-fidelity race session physics engine with safety cars and pit windows.
- twin: State store, telemetry cache, and SQLite/PostgreSQL persistence.
- streaming: Kafka event broker and FastF1 live telemetry producer/consumer daemon.
- context: Dynamic race knowledge graph with point-in-time lineage.
"""

from backend.app import intelligence, simulator, strategy, streaming, twin

__all__ = [
    "strategy",
    "intelligence",
    "simulator",
    "twin",
    "streaming",
]
