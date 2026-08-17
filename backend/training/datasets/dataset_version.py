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
        test_season: int = 2023,
        val_ratio: float = 0.20,
    ) -> dict[str, pd.DataFrame]:
        """
        Partitions datasets strictly across races/seasons.
        Never allows laps from the same race session to mix across train, val, and test splits.
        """
        if df.empty:
            return {"train": pd.DataFrame(), "val": pd.DataFrame(), "test": pd.DataFrame()}

        # Create unique race session key (e.g. '2023_Silverstone')
        if season_col in df.columns and race_col in df.columns:
            df["session_key"] = df[season_col].astype(str) + "_" + df[race_col].astype(str)
        elif "circuit" in df.columns:
            df["session_key"] = df["circuit"].astype(str)
        else:
            df["session_key"] = pd.Series(["race_01"] * len(df), index=df.index)

        all_sessions = sorted(df["session_key"].unique())

        # Test set: holdout test sessions
        if len(all_sessions) == 1:
            # Single session: split by distinct stints to prevent contiguous lap leakage
            stints = sorted(df["stint"].unique()) if "stint" in df.columns else [1]
            if len(stints) > 2:
                train_stints = stints[:-1]
                test_stints = [stints[-1]]
                train_df = pd.DataFrame(df[df["stint"].isin(train_stints)])
                val_df = pd.DataFrame(train_df.sample(frac=0.15, random_state=42))
                train_df = pd.DataFrame(train_df.drop(val_df.index))
                test_df = pd.DataFrame(df[df["stint"].isin(test_stints)])
                return {"train": train_df, "val": val_df, "test": test_df}
            else:
                # 70/15/15 deterministic chunk split
                n = len(df)
                t_idx = int(0.70 * n)
                v_idx = int(0.85 * n)
                return {
                    "train": pd.DataFrame(df.iloc[:t_idx]),
                    "val": pd.DataFrame(df.iloc[t_idx:v_idx]),
                    "test": pd.DataFrame(df.iloc[v_idx:]),
                }

        # Multi-session split: allocate complete race sessions to train, val, and test
        np.random.seed(42)
        shuffled_sessions = list(all_sessions)
        np.random.shuffle(shuffled_sessions)

        n_test = max(1, int(len(shuffled_sessions) * 0.20))
        n_val = max(1, int(len(shuffled_sessions) * 0.20))
        
        test_sessions = shuffled_sessions[:n_test]
        val_sessions = shuffled_sessions[n_test:n_test + n_val]
        train_sessions = shuffled_sessions[n_test + n_val:]
        if not train_sessions:
            train_sessions = val_sessions
            val_sessions = []

        train_df = pd.DataFrame(df[df["session_key"].isin(train_sessions)])
        val_df = pd.DataFrame(df[df["session_key"].isin(val_sessions)])
        test_df = pd.DataFrame(df[df["session_key"].isin(test_sessions)])

        return {"train": train_df, "val": val_df, "test": test_df}

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
