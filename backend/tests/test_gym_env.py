"""Unit tests for APEX Gymnasium reinforcement learning environment."""
import pytest
import numpy as np
from backend.app.strategy.gym_env import ApexRaceGymEnv, ACTION_MAP
from backend.app.simulator.models import StrategyAction, TrackCondition, TyreCompound
from backend.app.intelligence.feature_builder import FEATURE_DIM


def test_gym_env_initialization():
    env = ApexRaceGymEnv(track_name="silverstone", seed=42)
    assert getattr(env.action_space, "n", 8) == 8
    assert env.observation_space.shape == (FEATURE_DIM,)


def test_gym_env_reset():
    env = ApexRaceGymEnv(track_name="silverstone", seed=42)
    obs, info = env.reset(seed=123)
    assert isinstance(obs, np.ndarray)
    assert obs.shape == (FEATURE_DIM,)
    assert "race_id" in info
    assert "seed" in info


def test_gym_env_step_maintain():
    env = ApexRaceGymEnv(track_name="silverstone", seed=42)
    env.reset(seed=100)
    obs, reward, terminated, truncated, info = env.step(0)  # MAINTAIN
    assert isinstance(obs, np.ndarray)
    assert isinstance(reward, float)
    assert isinstance(terminated, bool)
    assert not truncated
    assert "position" in info
    assert "tyre_wear" in info


def test_gym_env_severe_cliff_penalty():
    env = ApexRaceGymEnv(track_name="silverstone", seed=42)
    env.reset(seed=100)
    assert env.sim is not None
    player = env.sim.get_player_car()
    assert player is not None
    player.tyre_cliff_reached = True
    player.tyre_wear_pct = 90.0

    _, reward, _, _, _ = env.step(0)  # MAINTAIN on blown tyres
    assert reward < -5.0, "Driving on blown tyres must trigger severe negative reward"


def test_gym_env_wet_tyre_mismatch_penalty():
    env = ApexRaceGymEnv(track_name="silverstone", seed=42)
    env.reset(seed=100)
    assert env.sim is not None
    env.sim.enable_dynamic_weather = False
    env.sim.weather.condition = TrackCondition.WET
    player = env.sim.get_player_car()
    assert player is not None
    player.tyre_compound = TyreCompound.SOFT
    _, reward_slicks, _, _, _ = env.step(0)  # Slicks in the wet

    env.reset(seed=100)
    assert env.sim is not None
    env.sim.enable_dynamic_weather = False
    env.sim.weather.condition = TrackCondition.WET
    player = env.sim.get_player_car()
    assert player is not None
    player.tyre_compound = TyreCompound.WET
    _, reward_wets, _, _, _ = env.step(0)  # Wet tyres in the wet

    assert reward_wets > reward_slicks, "Driving on appropriate wet tyres must score higher reward than slicks in wet"


def test_gym_env_timely_pit_reward():
    env = ApexRaceGymEnv(track_name="silverstone", seed=42)
    env.reset(seed=100)
    assert env.sim is not None
    player = env.sim.get_player_car()
    assert player is not None
    player.tyre_wear_pct = 75.0

    _, reward_timely, _, _, _ = env.step(4)  # PIT_MEDIUM when tyres heavily worn

    env.reset(seed=100)
    assert env.sim is not None
    player_fresh = env.sim.get_player_car()
    assert player_fresh is not None
    player_fresh.tyre_wear_pct = 15.0
    _, reward_wasteful, _, _, _ = env.step(4)  # PIT_MEDIUM on brand new tyres

    assert reward_timely > reward_wasteful, "Timely pit stop must yield higher reward than premature pit on fresh tyres"
