"""Dataset Builder: End-to-end orchestration of RAW -> CLEAN -> FEATURES -> VALIDATE -> VERSION -> SPLITS."""
from __future__ import annotations

import os
import logging
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd

from ..data.session_loader import UnifiedSessionLoader
from ..data.raw_storage import RawStorageManager
from ..preprocessing.merge_sessions import SessionDataMerger
from ..features.tyre_features import compute_tyre_features
from ..features.weather_features import compute_weather_features
from ..features.opponent_features import compute_opponent_features
from ..features.driver_features import compute_driver_features
from ..features.vehicle_features import compute_vehicle_features
from ..features.strategy_features import compute_strategy_features
from .dataset_validator import DatasetValidator
from .dataset_version import DatasetVersionRegistry, DatasetVersionMetadata

logger = logging.getLogger(__name__)

DEFAULT_SESSIONS = [
    (2023, "Silverstone"),
    (2023, "Monza"),
    (2023, "Belgium"),
    (2023, "Bahrain"),
    (2023, "Austria"),
]


class DatasetBuilder:
    """Builds, transforms, validates, and versions machine learning ready datasets."""

    def __init__(
        self,
        raw_storage: Optional[RawStorageManager] = None,
        version_registry: Optional[DatasetVersionRegistry] = None,
    ):
        self.storage = raw_storage or RawStorageManager()
        self.loader = UnifiedSessionLoader(raw_storage=self.storage)
        self.registry = version_registry or DatasetVersionRegistry()

    def build_dataset(
        self,
        sessions: Optional[List[Tuple[int, str]]] = None,
        dataset_version: str = "apex_dataset_v1.0",
        source: str = "fastf1_multi_session",
    ) -> Dict[str, Any]:
        """
        Executes complete pipeline:
        1. RAW extraction
        2. Clean & Normalize
        3. Feature Engineering (Tyre, Weather, Opponent, Driver, Vehicle, Strategy)
        4. Validate
        5. Version & Split (Train / Val / Test)
        """
        session_list = sessions or DEFAULT_SESSIONS
        clean_dfs: List[pd.DataFrame] = []

        for year, circuit in session_list:
            logger.info(f"[DatasetBuilder] Processing session: {year} {circuit}")
            raw_comp = self.loader.load_session(year, circuit, session_type="R", allow_synthetic_fallback=True)
            merged = SessionDataMerger.merge_session_components(raw_comp, circuit_name=circuit, season=year)
            if not merged.empty:
                clean_dfs.append(merged)

        if not clean_dfs:
            raise RuntimeError("[DatasetBuilder] No sessions were successfully cleaned.")

        combined_df = pd.concat(clean_dfs, ignore_index=True)

        # Apply rich feature engineering layers
        f_df = compute_tyre_features(combined_df)
        f_df = compute_weather_features(f_df)
        f_df = compute_opponent_features(f_df)
        f_df = compute_driver_features(f_df)
        f_df = compute_vehicle_features(f_df)
        f_df = compute_strategy_features(f_df)

        # Validate
        validation_report = DatasetValidator.validate_features_dataframe(f_df)

        # Split across race boundaries (zero leakage)
        splits = DatasetVersionRegistry.create_leak_free_splits(f_df)

        # Register metadata
        meta = self.registry.register_dataset(
            df=f_df,
            version=dataset_version,
            source=source,
            features_version="v1.0",
            train_races=list(splits["train"]["session_key"].unique()) if "session_key" in splits["train"] else [],
            val_races=list(splits["val"]["session_key"].unique()) if "session_key" in splits["val"] else [],
            test_races=list(splits["test"]["session_key"].unique()) if "session_key" in splits["test"] else [],
        )

        return {
            "dataset_version": dataset_version,
            "metadata": meta.model_dump(),
            "validation": validation_report,
            "full_dataset": f_df,
            "splits": splits,
        }
