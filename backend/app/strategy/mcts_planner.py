"""AlphaZero-style Monte Carlo Tree Search (MCTS) Strategy Planner for APEX.

Performs deep sequential tree search under stochastic race uncertainty, computing
Upper Confidence Bounds for Trees (UCT), state values V(s), and policy priors P(s,a).
"""
from __future__ import annotations

import copy
import math
import uuid
from typing import Any, Optional

from pydantic import BaseModel, Field

from backend.app.simulator.models import (
    CarState,
    DrivingMode,
    RaceState,
    StrategyAction,
    TyreCompound,
)


class MCTSNodeData(BaseModel):
    """Serializable node representation for frontend decision tree visualizer."""
    node_id: str
    parent_id: Optional[str] = None
    action_name: str
    lap: int
    visits: int = 0
    value: float = 0.0          # Q-value / Expected finishing score (0.0 to 1.0)
    win_probability_pct: float = 0.0
    prior: float = 0.0          # Prior probability P(s, a)
    uct_score: float = 0.0
    compound: str
    tyre_wear_pct: float
    projected_position: int
    gap_to_leader_s: float
    is_optimal_path: bool = False
    children: list[MCTSNodeData] = Field(default_factory=list)


class MCTSInternalNode:
    """Internal graph node for MCTS algorithm."""

    def __init__(
        self,
        car_state: CarState,
        race_state: RaceState,
        parent: Optional[MCTSInternalNode] = None,
        action: Optional[StrategyAction] = None,
        prior: float = 1.0,
    ):
        self.node_id = f"node_{uuid.uuid4().hex[:8]}"
        self.parent = parent
        self.action = action
        self.prior = prior
        self.car_state = copy.deepcopy(car_state)
        self.race_state = copy.deepcopy(race_state)

        self.visits: int = 0
        self.total_value: float = 0.0
        self.children: dict[StrategyAction, MCTSInternalNode] = {}
        self.is_terminal: bool = self.car_state.current_lap >= self.race_state.track.total_laps or self.car_state.is_dnf

    @property
    def q_value(self) -> float:
        """Mean estimated value of this node."""
        return (self.total_value / self.visits) if self.visits > 0 else 0.50

    def uct_value(self, c_puct: float = 1.414) -> float:
        """Calculates Upper Confidence Bound for Trees."""
        if not self.parent or self.parent.visits == 0:
            return self.q_value
        exploration = c_puct * self.prior * math.sqrt(self.parent.visits) / (1 + self.visits)
        return self.q_value + exploration

    def is_fully_expanded(self) -> bool:
        legal_actions = self.get_legal_actions()
        return len(self.children) == len(legal_actions)

    def get_legal_actions(self) -> list[StrategyAction]:
        """Filters sensible strategic options to maintain branching factor efficiency."""
        actions: list[StrategyAction] = [
            StrategyAction.MAINTAIN,
            StrategyAction.PUSH,
            StrategyAction.CONSERVE,
        ]

        rain = self.race_state.weather.rain_intensity
        curr_compound = self.car_state.tyre_compound

        # Pit actions
        if rain < 0.20:
            if curr_compound != TyreCompound.SOFT:
                actions.append(StrategyAction.PIT_SOFT)
            if curr_compound != TyreCompound.MEDIUM:
                actions.append(StrategyAction.PIT_MEDIUM)
            if curr_compound != TyreCompound.HARD:
                actions.append(StrategyAction.PIT_HARD)
        elif 0.20 <= rain <= 0.55:
            if curr_compound != TyreCompound.INTERMEDIATE:
                actions.append(StrategyAction.PIT_INTER)
            if curr_compound != TyreCompound.MEDIUM:
                actions.append(StrategyAction.PIT_MEDIUM)
        else:
            if curr_compound != TyreCompound.WET:
                actions.append(StrategyAction.PIT_WET)
            if curr_compound != TyreCompound.INTERMEDIATE:
                actions.append(StrategyAction.PIT_INTER)

        # ERS Energy tactics
        if self.car_state.ers_battery_soc_pct > 25.0:
            actions.append(StrategyAction.ENERGY_DEPLOY)
        elif self.car_state.ers_battery_soc_pct < 65.0:
            actions.append(StrategyAction.ENERGY_HARVEST)

        return actions


class MCTSStrategyPlanner:
    """Monte Carlo Tree Search policy planner with deterministic rollout simulation."""

    def __init__(self, c_puct: float = 1.414, rollout_depth: int = 5):
        self.c_puct = c_puct
        self.rollout_depth = rollout_depth

    def search(
        self,
        current_state: RaceState,
        num_simulations: int = 120,
    ) -> tuple[StrategyAction, MCTSNodeData, dict[str, Any]]:
        """Executes MCTS simulations from the current state and returns optimal recommendation and tree data."""
        player_car = next((c for c in current_state.cars if c.is_player), current_state.cars[0])
        root = MCTSInternalNode(car_state=player_car, race_state=current_state)

        for _ in range(num_simulations):
            # 1. Selection
            node = root
            while not node.is_terminal and node.is_fully_expanded():
                node = self._best_child(node)

            # 2. Expansion
            if not node.is_terminal:
                node = self._expand(node)

            # 3. Simulation / Fast Rollout
            value = self._rollout(node)

            # 4. Backpropagation
            self._backpropagate(node, value)

        # Determine best action from root visit counts
        best_action = StrategyAction.MAINTAIN
        max_visits = -1
        for action, child in root.children.items():
            if child.visits > max_visits:
                max_visits = child.visits
                best_action = action

        # Mark optimal path through tree
        self._mark_optimal_path(root)

        # Convert to serializable structure
        serialized_tree = self._serialize_node(root)

        summary = {
            "recommended_action": best_action.value,
            "root_q_value": round(root.q_value, 4),
            "simulations_executed": num_simulations,
            "explored_branches": len(root.children),
            "optimal_path_depth": self._calculate_depth(root),
            "win_probability_pct": round(root.q_value * 100.0, 1),
        }

        return best_action, serialized_tree, summary

    def _best_child(self, node: MCTSInternalNode) -> MCTSInternalNode:
        """Selects child with highest UCT score."""
        best_score = -float("inf")
        best_child = None
        for child in node.children.values():
            score = child.uct_value(self.c_puct)
            if score > best_score:
                best_score = score
                best_child = child
        return best_child or list(node.children.values())[0]

    def _expand(self, node: MCTSInternalNode) -> MCTSInternalNode:
        """Expands an unvisited legal action."""
        legal = node.get_legal_actions()
        unvisited = [a for a in legal if a not in node.children]

        if not unvisited:
            return node

        action = unvisited[0]

        # Prior policy heuristic
        prior = 0.40 if action == StrategyAction.MAINTAIN else 0.15
        if "PIT_" in action.value and (node.car_state.tyre_wear_pct > 75.0 or node.car_state.tyre_cliff_reached):
            prior = 0.65

        # Create next state
        next_car = copy.deepcopy(node.car_state)
        next_race = copy.deepcopy(node.race_state)

        self._apply_action_step(next_car, next_race, action)

        child = MCTSInternalNode(
            car_state=next_car,
            race_state=next_race,
            parent=node,
            action=action,
            prior=prior,
        )
        node.children[action] = child
        return child

    def _apply_action_step(self, car: CarState, race: RaceState, action: StrategyAction) -> None:
        """Applies a one-lap tactical transition."""
        car.current_lap += 1
        car.tyre_age_laps += 1

        if action == StrategyAction.PUSH:
            car.driving_mode = DrivingMode.PUSH
            car.tyre_wear_pct += 3.8
            pace_gain = 0.75
        elif action == StrategyAction.CONSERVE:
            car.driving_mode = DrivingMode.CONSERVE
            car.tyre_wear_pct += 1.3
            pace_gain = -0.60
        elif "PIT_" in action.value:
            compound_str = action.value.replace("PIT_", "")
            try:
                car.tyre_compound = TyreCompound(compound_str)
            except ValueError:
                car.tyre_compound = TyreCompound.MEDIUM
            car.tyre_wear_pct = 0.0
            car.tyre_age_laps = 0
            car.tyre_cliff_reached = False
            car.in_pit = True
            car.pit_count += 1
            # Pit lane delta time loss
            car.gap_to_leader_s += race.track.pit_lane_delta_s
            pace_gain = -race.track.pit_lane_delta_s
        elif action == StrategyAction.ENERGY_DEPLOY:
            car.ers_deploy_mode = "OVERTAKE"
            car.ers_battery_soc_pct = max(5.0, car.ers_battery_soc_pct - 15.0)
            pace_gain = 0.50
        elif action == StrategyAction.ENERGY_HARVEST:
            car.ers_deploy_mode = "HARVEST"
            car.ers_battery_soc_pct = min(100.0, car.ers_battery_soc_pct + 20.0)
            pace_gain = -0.40
        else:
            car.driving_mode = DrivingMode.NORMAL
            car.tyre_wear_pct += 2.2
            pace_gain = 0.0

        if car.tyre_wear_pct >= 78.0:
            car.tyre_cliff_reached = True
            pace_gain -= 1.8

        car.gap_to_leader_s = max(0.0, car.gap_to_leader_s - pace_gain)
        # Position estimation based on gap
        if car.gap_to_leader_s < 2.0:
            car.position = 1
        elif car.gap_to_leader_s < 7.0:
            car.position = 2
        elif car.gap_to_leader_s < 15.0:
            car.position = 3
        else:
            car.position = min(10, 4 + int(car.gap_to_leader_s // 8.0))

    def _rollout(self, node: MCTSInternalNode) -> float:
        """Fast rollout evaluating outcome value between 0.0 (P10) and 1.0 (P1)."""
        sim_car = copy.deepcopy(node.car_state)
        sim_race = copy.deepcopy(node.race_state)

        for _ in range(self.rollout_depth):
            if sim_car.current_lap >= sim_race.track.total_laps:
                break
            # Heuristic auto rollout policy
            if sim_car.tyre_wear_pct > 80.0:
                action = StrategyAction.PIT_HARD
            elif sim_car.gap_to_leader_s < 1.5:
                action = StrategyAction.PUSH
            else:
                action = StrategyAction.MAINTAIN
            self._apply_action_step(sim_car, sim_race, action)

        # Score function: higher for better finishing position and lower tyre cliff
        pos_score = max(0.0, 1.0 - (sim_car.position - 1) * 0.12)
        gap_penalty = min(0.30, sim_car.gap_to_leader_s * 0.005)
        wear_penalty = 0.15 if sim_car.tyre_cliff_reached else 0.0

        value = max(0.0, min(1.0, pos_score - gap_penalty - wear_penalty))
        return round(value, 4)

    def _backpropagate(self, node: MCTSInternalNode, value: float) -> None:
        """Propagates simulation outcome value back up to the root."""
        curr: Optional[MCTSInternalNode] = node
        while curr is not None:
            curr.visits += 1
            curr.total_value += value
            curr = curr.parent

    def _mark_optimal_path(self, root: MCTSInternalNode) -> None:
        """Marks the sequence of most-visited nodes as the optimal trajectory."""
        curr: Optional[MCTSInternalNode] = root
        while curr and curr.children:
            best_child = max(curr.children.values(), key=lambda c: c.visits)
            setattr(best_child, "_is_optimal", True)
            curr = best_child

    def _calculate_depth(self, node: MCTSInternalNode) -> int:
        if not node.children:
            return 1
        return 1 + max(self._calculate_depth(c) for c in node.children.values())

    def _serialize_node(self, node: MCTSInternalNode) -> MCTSNodeData:
        """Recursively serializes MCTS node graph."""
        is_opt = getattr(node, "_is_optimal", False) or node.parent is None
        action_name = node.action.value if node.action else "CURRENT_STATE"

        children_data = [self._serialize_node(c) for c in node.children.values()]

        return MCTSNodeData(
            node_id=node.node_id,
            parent_id=node.parent.node_id if node.parent else None,
            action_name=action_name,
            lap=node.car_state.current_lap,
            visits=node.visits,
            value=round(node.q_value, 4),
            win_probability_pct=round(node.q_value * 100.0, 1),
            prior=round(node.prior, 3),
            uct_score=round(node.uct_value(self.c_puct), 4),
            compound=node.car_state.tyre_compound.value,
            tyre_wear_pct=round(node.car_state.tyre_wear_pct, 1),
            projected_position=node.car_state.position,
            gap_to_leader_s=round(node.car_state.gap_to_leader_s, 2),
            is_optimal_path=is_opt,
            children=children_data,
        )
