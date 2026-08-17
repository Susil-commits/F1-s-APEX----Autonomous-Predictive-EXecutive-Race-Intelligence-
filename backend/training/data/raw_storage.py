"""Raw data storage manager with cryptographic hashing, metadata tracking, and disk persistence."""
from __future__ import annotations

import hashlib
import json
import logging
import os
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

DEFAULT_RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw")


class RawStorageManager:
    """Manages raw dataset artifacts, disk serialization, and integrity hashing."""

    def __init__(self, storage_dir: str | None = None):
        self.storage_dir = storage_dir or DEFAULT_RAW_DIR
        os.makedirs(self.storage_dir, exist_ok=True)

    @staticmethod
    def compute_dataframe_hash(df: pd.DataFrame) -> str:
        """Computes a SHA256 cryptographic hash representing the dataframe contents and schema."""
        if df.empty:
            return hashlib.sha256(b"empty_dataframe").hexdigest()[:16]
        # Hash schema + head/tail representation
        schema_repr = str(df.dtypes.to_dict()) + str(df.shape)
        sample_bytes = df.head(100).to_csv(index=False).encode("utf-8")
        h = hashlib.sha256(schema_repr.encode("utf-8"))
        h.update(sample_bytes)
        return h.hexdigest()[:16]

    def save_raw_table(
        self,
        df: pd.DataFrame,
        category: str,
        identifier: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Saves a raw dataframe as CSV alongside its JSON metadata manifest.
        
        Returns the absolute filepath to the saved file.
        """
        category_dir = os.path.join(self.storage_dir, category)
        os.makedirs(category_dir, exist_ok=True)

        clean_id = identifier.replace(" ", "_").replace("/", "_").lower()
        filepath = os.path.join(category_dir, f"{clean_id}.csv")
        meta_path = os.path.join(category_dir, f"{clean_id}_meta.json")

        df.to_csv(filepath, index=False)

        manifest = {
            "category": category,
            "identifier": identifier,
            "row_count": len(df),
            "columns": list(df.columns),
            "sha256": self.compute_dataframe_hash(df),
            "metadata": metadata or {},
        }
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        logger.info(f"[RawStorageManager] Stored {len(df)} rows to {filepath}")
        return filepath

    def load_raw_table(self, category: str, identifier: str) -> pd.DataFrame | None:
        """Loads a raw dataframe from disk if it exists."""
        clean_id = identifier.replace(" ", "_").replace("/", "_").lower()
        filepath = os.path.join(self.storage_dir, category, f"{clean_id}.csv")
        if os.path.exists(filepath):
            try:
                return pd.read_csv(filepath)
            except Exception as e:
                logger.warning(f"[RawStorageManager] Failed to read {filepath}: {e}")
        return None

    def exists(self, category: str, identifier: str) -> bool:
        """Checks whether a raw table exists on disk."""
        clean_id = identifier.replace(" ", "_").replace("/", "_").lower()
        filepath = os.path.join(self.storage_dir, category, f"{clean_id}.csv")
        return os.path.exists(filepath)
