"""Tests for Curriculum Learning Reinforcement Learning Pipeline."""
import tempfile
from pathlib import Path

from backend.app.simulator.models import SafetyCarStatus, TrackCondition
from backend.training.curriculum_learning import (
    CURRICULUM_STAGES,
    StageCustomRaceEnv,
    train_curriculum_policy,
)


def test_curriculum_stages_definitions():
    """Verifies that all 3 curriculum stages have valid monotonic difficulty parameters."""
    assert len(CURRICULUM_STAGES) == 3
    # Stage 1: Novice
    assert not CURRICULUM_STAGES[0].enable_dynamic_weather
    assert not CURRICULUM_STAGES[0].enable_safety_cars
    # Stage 2: Intermediate
    assert CURRICULUM_STAGES[1].enable_dynamic_weather
    assert not CURRICULUM_STAGES[1].enable_safety_cars
    # Stage 3: Master/Pro
    assert CURRICULUM_STAGES[2].enable_dynamic_weather
    assert CURRICULUM_STAGES[2].enable_safety_cars


def test_stage_custom_race_env_constraints():
    """Verifies that StageCustomRaceEnv enforces stage-specific environment constraints upon reset."""
    stage1 = CURRICULUM_STAGES[0]
    env = StageCustomRaceEnv(stage=stage1, track_name="silverstone")
    obs, info = env.reset()

    assert env.sim is not None
    assert env.sim.weather.condition == TrackCondition.DRY
    assert env.sim.weather.rain_intensity == 0.0
    assert env.sim.safety_car == SafetyCarStatus.NONE
    assert env.sim.enable_dynamic_weather is False


def test_curriculum_training_smoke_execution():
    """Verifies that curriculum learning runs a short smoke training loop and saves artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        out_model = Path(tmpdir) / "test_curriculum_dqn.zip"
        out_plot = Path(tmpdir) / "test_curriculum_plot.png"

        result = train_curriculum_policy(
            stages=[CURRICULUM_STAGES[0]],
            output_path=out_model,
            plot_path=out_plot,
            smoke_test=True,
        )

        assert result["status"] == "COMPLETED"
        assert result["stages_evaluated"] == 1
        assert out_model.exists()
        assert out_plot.exists()
