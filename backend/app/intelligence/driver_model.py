"""Driver performance modeling, psychological pressure reaction, and skill profiles."""
from __future__ import annotations

import logging
from typing import Any

import numpy as np
from pydantic import BaseModel

from backend.app.simulator.models import CarState, DrivingMode

logger = logging.getLogger(__name__)


class DriverSkillProfile(BaseModel):
    """Static and dynamic driver behavioral traits."""
    driver_name: str
    team: str
    pace_bias_s: float
    consistency_score: float # 0.0 to 1.0 (1.0 = ultra-consistent robot)
    tyre_management_skill: float # 0.0 to 1.0 (multiplier on tyre wear)
    aggression: float # 0.0 to 1.0
    defence_strength: float # 0.0 to 1.0
    overtake_skill: float # 0.0 to 1.0
    mistake_base_prob: float # per lap error chance


DRIVER_REGISTRY: dict[str, DriverSkillProfile] = {
    "M. Verstappen": DriverSkillProfile(driver_name="M. Verstappen", team="Red Bull Racing", pace_bias_s=-0.25, consistency_score=0.95, tyre_management_skill=0.92, aggression=0.92, defence_strength=0.94, overtake_skill=0.95, mistake_base_prob=0.015),
    "L. Norris": DriverSkillProfile(driver_name="L. Norris", team="McLaren", pace_bias_s=-0.15, consistency_score=0.90, tyre_management_skill=0.88, aggression=0.86, defence_strength=0.88, overtake_skill=0.90, mistake_base_prob=0.025),
    "C. Leclerc": DriverSkillProfile(driver_name="C. Leclerc", team="Ferrari", pace_bias_s=-0.10, consistency_score=0.88, tyre_management_skill=0.84, aggression=0.89, defence_strength=0.87, overtake_skill=0.92, mistake_base_prob=0.030),
    "APEX AI (You)": DriverSkillProfile(driver_name="APEX AI (You)", team="APEX Strategy Team", pace_bias_s=-0.05, consistency_score=0.92, tyre_management_skill=0.90, aggression=0.85, defence_strength=0.89, overtake_skill=0.88, mistake_base_prob=0.018),
    "O. Piastri": DriverSkillProfile(driver_name="O. Piastri", team="McLaren", pace_bias_s=0.00, consistency_score=0.91, tyre_management_skill=0.86, aggression=0.82, defence_strength=0.86, overtake_skill=0.85, mistake_base_prob=0.022),
    "G. Russell": DriverSkillProfile(driver_name="G. Russell", team="Mercedes", pace_bias_s=0.05, consistency_score=0.89, tyre_management_skill=0.85, aggression=0.88, defence_strength=0.86, overtake_skill=0.87, mistake_base_prob=0.028),
    "C. Sainz": DriverSkillProfile(driver_name="C. Sainz", team="Ferrari", pace_bias_s=0.08, consistency_score=0.91, tyre_management_skill=0.89, aggression=0.80, defence_strength=0.90, overtake_skill=0.84, mistake_base_prob=0.020),
    "L. Hamilton": DriverSkillProfile(driver_name="L. Hamilton", team="Mercedes", pace_bias_s=0.10, consistency_score=0.94, tyre_management_skill=0.95, aggression=0.84, defence_strength=0.92, overtake_skill=0.91, mistake_base_prob=0.015),
    "F. Alonso": DriverSkillProfile(driver_name="F. Alonso", team="Aston Martin", pace_bias_s=0.20, consistency_score=0.96, tyre_management_skill=0.96, aggression=0.90, defence_strength=0.96, overtake_skill=0.93, mistake_base_prob=0.012),
    "S. Perez": DriverSkillProfile(driver_name="S. Perez", team="Red Bull Racing", pace_bias_s=0.25, consistency_score=0.82, tyre_management_skill=0.88, aggression=0.76, defence_strength=0.80, overtake_skill=0.81, mistake_base_prob=0.040),
}


class DriverIntelligenceEngine:
    """Computes dynamic driver performance state, pressure degradation, and mistake risks."""

    @classmethod
    def get_profile(cls, driver_name: str) -> DriverSkillProfile:
        """Retrieves or creates a driver skill profile."""
        for name, profile in DRIVER_REGISTRY.items():
            if name.lower() in driver_name.lower() or driver_name.lower() in name.lower():
                return profile
        return DriverSkillProfile(
            driver_name=driver_name,
            team="Formula 1 Team",
            pace_bias_s=0.15,
            consistency_score=0.85,
            tyre_management_skill=0.85,
            aggression=0.80,
            defence_strength=0.80,
            overtake_skill=0.80,
            mistake_base_prob=0.03,
        )

    @classmethod
    def evaluate_driver_state(
        cls,
        car: CarState,
        race_lap: int,
        total_laps: int,
    ) -> dict[str, Any]:
        """Calculates dynamic driver status under current race context."""
        profile = cls.get_profile(car.driver_name)
        
        # Pressure multiplier when chased closely (< 1.0s)
        chased_pressure = 1.8 if (0.0 < car.gap_to_car_behind_s <= 1.0) else 1.0
        # Fatigue factor towards end of race
        fatigue = 1.0 + 0.15 * (race_lap / max(1, total_laps))

        # Dynamic mistake probability
        mistake_prob = profile.mistake_base_prob * chased_pressure * fatigue
        if car.tyre_cliff_reached:
            mistake_prob *= 2.2 # Blown tyres dramatically increase error rate

        # Overtake probability against car ahead
        overtake_prob = 0.0
        if 0.0 < car.gap_to_car_ahead_s <= 1.2:
            base_overtake = profile.overtake_skill * (1.2 - car.gap_to_car_ahead_s)
            mode_boost = 0.15 if car.driving_mode == DrivingMode.PUSH else 0.0
            overtake_prob = float(np.clip(base_overtake + mode_boost, 0.05, 0.95))

        return {
            "driver_name": car.driver_name,
            "pace_bias_s": profile.pace_bias_s,
            "consistency": profile.consistency_score,
            "tyre_management": profile.tyre_management_skill,
            "mistake_probability": round(float(np.clip(mistake_prob, 0.0, 0.50)), 3),
            "overtake_probability": round(overtake_prob, 3),
            "defence_strength": profile.defence_strength,
            "fatigue_index": round(fatigue - 1.0, 2),
        }
