"""Gymnasium Environment for training RL race strategy agents."""
from typing import Any

import gymnasium as gym
import numpy as np
from gymnasium import spaces

from backend.app.intelligence.feature_builder import FEATURE_DIM, FeatureBuilder
from backend.app.simulator.engine import RaceSimulator
from backend.app.simulator.models import StrategyAction, TrackCondition, TyreCompound

ACTION_MAP = {
    0: StrategyAction.MAINTAIN,
    1: StrategyAction.PUSH,
    2: StrategyAction.CONSERVE,
    3: StrategyAction.PIT_SOFT,
    4: StrategyAction.PIT_MEDIUM,
    5: StrategyAction.PIT_HARD,
    6: StrategyAction.PIT_INTER,
    7: StrategyAction.PIT_WET,
}


class ApexRaceGymEnv(gym.Env):
    """Reinforcement learning environment for race strategy optimization."""

    metadata = {"render_modes": ["human"]}

    def __init__(self, track_name: str = "silverstone", seed: int = 42):
        super().__init__()
        self.track_name = track_name
        self.default_seed = seed
        self.sim: RaceSimulator | None = None

        # 8 discrete strategic actions
        self.action_space = spaces.Discrete(8)

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
        seed: int | None = None,
        options: dict[str, Any] | None = None,
    ) -> tuple[np.ndarray, dict[str, Any]]:
        super().reset(seed=seed)
        race_seed = seed if seed is not None else np.random.randint(1, 100000)
        self.sim = RaceSimulator(
            track_name=self.track_name,
            seed=race_seed,
            enable_dynamic_weather=True,
        )
        # Advance initial tick
        state = self.sim.step()
        obs = FeatureBuilder.extract_features(state)
        return obs, {"race_id": state.race_id, "seed": race_seed}

    def step(self, action: int) -> tuple[np.ndarray, float, bool, bool, dict[str, Any]]:
        if self.sim is None:
            self.reset()
        assert self.sim is not None

        strat_action = ACTION_MAP.get(action, StrategyAction.MAINTAIN)
        player_before = self.sim.get_player_car()
        assert player_before is not None
        prev_pos = player_before.position
        prev_gap_to_leader = player_before.gap_to_leader_s
        prev_wear = player_before.tyre_wear_pct

        # Advance simulator
        state = self.sim.step(player_action=strat_action)
        player = self.sim.get_player_car()
        assert player is not None

        # -------------------------------------------------------------
        # Reward Shaping Formulation
        # -------------------------------------------------------------
        reward = 0.0

        # 1. Track Position Delta (Overtakes rewarded, position drops penalized)
        pos_change = prev_pos - player.position
        reward += pos_change * 3.0

        # 2. Gap to Leader Delta
        if player.position > 1:
            gap_delta = prev_gap_to_leader - player.gap_to_leader_s
            reward += np.clip(gap_delta * 0.2, -1.5, 1.5)
        else:
            reward += 0.75  # Clean air race lead bonus

        # 3. Driving Mode & Tyre Preservation
        is_pit_action = strat_action in (
            StrategyAction.PIT_SOFT,
            StrategyAction.PIT_MEDIUM,
            StrategyAction.PIT_HARD,
            StrategyAction.PIT_INTER,
            StrategyAction.PIT_WET,
        )

        # Severe penalty for driving on blown tyres (tyre cliff reached or wear > 75%)
        if player.tyre_cliff_reached or player.tyre_wear_pct > 75.0:
            cliff_severity = ((player.tyre_wear_pct - 75.0) / 10.0) ** 2
            reward -= (3.0 + cliff_severity)
            if player.tyre_wear_pct > 85.0:
                reward -= 10.0  # Catastrophic wear penalty

        # Rewarding timely pit stops when tyre life is depleted
        if is_pit_action:
            if prev_wear >= 65.0 or player_before.tyre_cliff_reached:
                reward += 6.0  # Timely pit stop incentive
                if state.safety_car in ("VSC", "SAFETY_CAR"):
                    reward += 5.0  # Opportunistic pit under safety car
            elif prev_wear < 35.0 and state.weather.condition == TrackCondition.DRY and state.safety_car == "NONE":
                reward -= 8.0  # Wasteful pit stop penalty on fresh tyres

        # Pushing on heavily degraded tyres is heavily penalized
        if strat_action == StrategyAction.PUSH and player.tyre_wear_pct > 65.0:
            reward -= 2.5

        # 4. Weather Compound Appropriateness
        is_wet = state.weather.condition == TrackCondition.WET or "WET" in str(state.weather.condition).upper()
        is_damp = state.weather.condition == TrackCondition.DAMP or "DAMP" in str(state.weather.condition).upper()
        is_dry = state.weather.condition == TrackCondition.DRY or "DRY" in str(state.weather.condition).upper()
        
        is_slick = player.tyre_compound in (TyreCompound.SOFT, TyreCompound.MEDIUM, TyreCompound.HARD) or any(c in str(player.tyre_compound).upper() for c in ("SOFT", "MEDIUM", "HARD"))
        is_rain_tyre = player.tyre_compound in (TyreCompound.INTERMEDIATE, TyreCompound.WET) or any(c in str(player.tyre_compound).upper() for c in ("INTER", "WET"))

        if is_wet:
            if is_slick:
                reward -= 12.0  # Driving on slicks in wet
            elif is_pit_action and strat_action == StrategyAction.PIT_WET:
                reward += 8.0  # Tactical switch to wet compound
        elif is_damp:
            if is_rain_tyre:
                reward += 1.5  # Appropriate tyre for damp conditions
            elif is_pit_action and strat_action == StrategyAction.PIT_INTER:
                reward += 6.0
        elif is_dry:
            if is_rain_tyre:
                reward -= 6.0  # Driving wet tyres on bone dry track

        # 5. Terminal Horizon Rewards
        terminated = state.is_finished
        truncated = False

        if terminated:
            if player.position == 1:
                reward += 100.0
            elif player.position == 2:
                reward += 60.0
            elif player.position == 3:
                reward += 40.0
            elif player.position <= 5:
                reward += 25.0
            elif player.position <= 10:
                reward += 10.0
            else:
                reward -= 20.0

            # Bonus for completing race without blown tyre laps
            if not player.tyre_cliff_reached:
                reward += 15.0

        obs = FeatureBuilder.extract_features(state)
        info = {
            "lap": state.current_lap,
            "position": player.position,
            "tyre_wear": player.tyre_wear_pct,
            "race_time_s": player.total_race_time_s,
        }

        return obs, float(reward), terminated, truncated, info
