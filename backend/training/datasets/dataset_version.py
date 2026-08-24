"""Dataset metadata and versioning manager with anti-leakage train/validation/test splits."""
from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import UTC, datetime

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

DATASETS_REGISTRY_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "registry")


class DatasetVersionMetadata(BaseModel):
    """Metadata schema for versioned training datasets."""
    dataset_version: str
    source: str
    seasons: list[int]
    sessions: list[str]
    features_version: str
    creation_timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    row_count: int
    missing_values: dict[str, int]
    schema_hash: str
    feature_names: list[str]
    split_strategy: str = "race_season_split"
    train_races: list[str]
    val_races: list[str]
    test_races: list[str]


class DatasetVersionRegistry:
    """Manages version manifests and split generation for clean data governance."""

    def __init__(self, registry_dir: str | None = None):
        self.registry_dir = registry_dir or DATASETS_REGISTRY_DIR
        os.makedirs(self.registry_dir, exist_ok=True)

    @staticmethod
    def compute_schema_hash(df: pd.DataFrame) -> str:
        """Computes cryptographic hash of column names and dtypes."""
        dtype_dict = {col: str(dtype) for col, dtype in df.dtypes.items()}
        raw = json.dumps(dtype_dict, sort_keys=True)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    @staticmethod
    def create_leak_free_splits(
        df: pd.DataFrame,
        race_col: str = "circuit",
        season_col: str = "season",
        test_season: int = 2025,
        val_ratio: float = 0.20,
    ) -> dict[str, pd.DataFrame]:
        """
        Partitions datasets strictly across chronological horizons using TemporalSplitter.
        Enforces:
          - Train: 2018–2023
          - Validation: 2024
          - Test: 2025 (or future holdout)
        Never allows laps from the same race session or future seasons to mix across splits.
        """
        from backend.training.datasets.temporal_splitter import (
            TemporalSplitConfig,
            TemporalSplitter,
        )

        if df.empty:
            return {"train": pd.DataFrame(), "val": pd.DataFrame(), "test": pd.DataFrame()}

        cfg = TemporalSplitConfig(
            train_seasons=[2018, 2019, 2020, 2021, 2022, 2023],
            val_seasons=[2024],
            test_seasons=[2025],
            season_col=season_col,
            circuit_col=race_col,
        )
        return TemporalSplitter.fixed_horizon_split(df, config=cfg)

    def register_dataset(
        self,
        df: pd.DataFrame,
        version: str,
        source: str,
        features_version: str = "v1.0",
        train_races: list[str] | None = None,
        val_races: list[str] | None = None,
        test_races: list[str] | None = None,
    ) -> DatasetVersionMetadata:
        """Registers and persists metadata manifest for a dataset version."""
        missing: dict[str, int] = {str(col): int(cnt) for col, cnt in df.isnull().sum().items() if int(cnt) > 0}
        seasons = [int(s) for s in df["season"].unique()] if "season" in df.columns else [2023]
        sessions = [str(s) for s in df["circuit"].unique()] if "circuit" in df.columns else ["Silverstone"]

        meta = DatasetVersionMetadata(
            dataset_version=version,
            source=source,
            seasons=seasons,
            sessions=sessions,
            features_version=features_version,
            row_count=len(df),
            missing_values=missing,
            schema_hash=self.compute_schema_hash(df),
            feature_names=list(df.columns),
            train_races=train_races or sessions,
            val_races=val_races or [],
            test_races=test_races or [],
        )

        path = os.path.join(self.registry_dir, f"{version}_manifest.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(meta.model_dump(), f, indent=2)

        logger.info(f"[DatasetVersionRegistry] Registered dataset {version} at {path}")
        return meta
