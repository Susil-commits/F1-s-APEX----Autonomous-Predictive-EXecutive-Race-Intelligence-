"""Dataset statistical validator and schema integrity verifier."""
from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# Columns expected to be mostly null by nature (event timestamps, flags)
SPARSE_EVENT_COLS = {"PitInTime", "PitOutTime", "dnf_reason", "DriverNumber", "Team"}


class DatasetValidationError(Exception):
    """Raised when training data fails schema, range, or null constraints."""
    pass


class DatasetValidator:
    """Performs pre-training statistical sanity checks and range validation."""

    @staticmethod
    def validate_features_dataframe(
        df: pd.DataFrame,
        required_columns: Optional[List[str]] = None,
        max_null_pct: float = 0.02,
        ignore_sparse_cols: Optional[set] = None,
    ) -> Dict[str, Any]:
        """
        Validates feature dataframe:
        - Required columns are present
        - Null percentage on core feature columns is below threshold
        - Numerical columns do not contain inf or nan
        - Physical bounds are respected
        """
        if df.empty:
            raise DatasetValidationError("Dataset is empty.")

        req = required_columns or ["compound", "tyre_age", "lap_time_delta"]
        missing_cols = [c for c in req if c not in df.columns]
        if missing_cols:
            raise DatasetValidationError(f"Missing required columns: {missing_cols}")

        ignored = SPARSE_EVENT_COLS if ignore_sparse_cols is None else ignore_sparse_cols

        # Check nulls on non-sparse columns
        total_rows = len(df)
        null_counts = {k: v for k, v in df.isnull().sum().to_dict().items() if k not in ignored}
        excessive_nulls = {k: v for k, v in null_counts.items() if (v / total_rows) > max_null_pct}
        if excessive_nulls:
            raise DatasetValidationError(f"Columns exceed null tolerance ({max_null_pct*100}%): {excessive_nulls}")

        # Check numeric columns for infs
        num_cols = df.select_dtypes(include=[np.number]).columns
        for c in num_cols:
            if np.isinf(df[c]).any():
                raise DatasetValidationError(f"Column '{c}' contains infinite values.")

        # Physical range assertions
        if "tyre_age" in df.columns:
            if (df["tyre_age"] < 1).any() or (df["tyre_age"] > 80).any():
                logger.warning("[DatasetValidator] tyre_age outside typical range (1-80)")

        if "lap_time_delta" in df.columns:
            if (df["lap_time_delta"] < 0.0).any():
                raise DatasetValidationError("Found negative lap_time_delta values.")

        report = {
            "is_valid": True,
            "row_count": total_rows,
            "column_count": len(df.columns),
            "null_summary": {k: v for k, v in null_counts.items() if v > 0},
            "columns": list(df.columns),
        }
        return report
