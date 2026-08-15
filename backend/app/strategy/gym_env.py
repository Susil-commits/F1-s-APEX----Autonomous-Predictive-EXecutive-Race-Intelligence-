"""Gymnasium Environment for training RL race strategy agents."""
from typing import Optional, Dict, Any, Tuple
import gymnasium as gym
from gymnasium import spaces
import numpy as np

from backend.app.simulator.engine import RaceSimulator
from backend.app.simulator.models import StrategyAction, TrackCondition, TyreCompound
from backend.app.intelligence.feature_builder import FeatureBuilder, FEATURE_DIM


ACTION_MAP = {
    0: StrategyAction.MAINTAIN,
    1: StrategyAction.PUSH,
    2: StrategyAction.CONSERVE,
    3: StrategyAction.PIT_SOFT,
    4: StrategyAction.PIT_MEDIUM,
    5: StrategyAction.PIT_HARD,
}


class ApexRaceGymEnv(gym.Env):
    """Reinforcement learning environment for race strategy optimization."""

    metadata = {"render_modes": ["human"]}

    def __init__(self, track_name: str = "silverstone", seed: int = 42):
        super().__init__()
        self.track_name = track_name
        self.default_seed = seed
        self.sim: Optional[RaceSimulator] = None

        # 6 discrete actions
        self.action_space = spaces.Discrete(6)

        # 28 continuous normalized features
        self.observation_space = spaces.Box(
            low=0.0,
            high=1.1,
            shape=(FEATURE_DIM,),
            dtype=np.float32,
        )

    def reset(
        self,
        *,
        seed: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        super().reset(seed=seed)
        race_seed = seed if seed is not None else int(np.random.randint(1, 100000))
        self.sim = RaceSimulator(
            track_name=self.track_name,
            seed=race_seed,
            enable_dynamic_weather=True,
        )
        # Advance initial tick
        state = self.sim.step()
        obs = FeatureBuilder.extract_features(state)
        return obs, {"race_id": state.race_id, "seed": race_seed}

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        strat_action = ACTION_MAP.get(action, StrategyAction.MAINTAIN)
        player_before = self.sim.get_player_car()
        prev_pos = player_before.position
        prev_gap_to_leader = player_before.gap_to_leader_s

        # Advance simulator
        state = self.sim.step(player_action=strat_action)
        player = self.sim.get_player_car()

        # -------------------------------------------------------------
        # Reward Shaping
        # -------------------------------------------------------------
        reward = 0.0

        # 1. Position change reward (overtaking is rewarded, losing positions penalized)
        pos_change = prev_pos - player.position
        reward += pos_change * 2.5

        # 2. Pace / Gap change
        if player.position > 1:
            gap_delta = prev_gap_to_leader - player.gap_to_leader_s
            reward += np.clip(gap_delta * 0.15, -1.0, 1.0)
        else:
            reward += 0.5  # Leading the race bonus

        # 3. Penalties for critical strategic errors
        # Severe penalty for driving on blown tyres
        if player.tyre_cliff_reached and player.tyre_wear_pct > 88.0:
            reward -= 2.0

        # Severe penalty for wrong tyres in wet weather
        if state.weather.condition == TrackCondition.WET and player.tyre_compound in (TyreCompound.SOFT, TyreCompound.MEDIUM, TyreCompound.HARD):
            reward -= 5.0

        # Penalty for excessive/pointless consecutive pit stops
        if strat_action in (StrategyAction.PIT_SOFT, StrategyAction.PIT_MEDIUM, StrategyAction.PIT_HARD):
            if player.tyre_wear_pct < 25.0 and state.weather.condition == TrackCondition.DRY and state.safety_car == "NONE":
                reward -= 4.0  # Wasted pit stop penalty

        # 4. Terminal Rewards
        terminated = state.is_finished
        truncated = False

        if terminated:
            if player.position == 1:
                reward += 60.0
            elif player.position == 2:
                reward += 40.0
            elif player.position == 3:
                reward += 25.0
            elif player.position <= 5:
                reward += 15.0
            elif player.position <= 10:
                reward += 5.0
            else:
                reward -= 10.0

        obs = FeatureBuilder.extract_features(state)
        info = {
            "lap": state.current_lap,
            "position": player.position,
            "tyre_wear": player.tyre_wear_pct,
            "race_time_s": player.total_race_time_s,
        }

        return obs, float(reward), terminated, truncated, info
