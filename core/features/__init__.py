"""APEX Core Feature Engineering.

Transforms pre-race session state into strictly point-in-time validated feature vectors.
"""
from core.features.feature_builder import PreRaceFeatureBuilder, PRE_RACE_FEATURE_NAMES
from core.features.tyre_model import (
    PIRELLI_COMPOUNDS,
    TyreCompoundSpec,
    TyreDegradationModel,
)

__all__ = [
    "PreRaceFeatureBuilder",
    "PRE_RACE_FEATURE_NAMES",
    "TyreDegradationModel",
    "PIRELLI_COMPOUNDS",
    "TyreCompoundSpec",
]
