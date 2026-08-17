"""Opponent relative gaps, undercut threats, and track position features."""
from __future__ import annotations

import numpy as np
import pandas as pd


def _get_numeric_series(df: pd.DataFrame, col: str, default: float) -> pd.Series:
    if col in df.columns:
        return pd.Series(pd.to_numeric(df[col], errors="coerce")).fillna(default)
    return pd.Series(default, index=df.index)


def compute_opponent_features(df: pd.DataFrame) -> pd.DataFrame:
    """Generates opponent interaction metrics and undercut/overcut vulnerability indicators."""
    if df.empty:
        return pd.DataFrame()

    out = df.copy()

    gap_ahead = _get_numeric_series(out, "gap_ahead_s", 2.5)
    gap_behind = _get_numeric_series(out, "gap_behind_s", 3.0)
    wear_pct = _get_numeric_series(out, "estimated_wear_pct", 50.0)

    out["gap_ahead_norm"] = np.clip(gap_ahead / 15.0, 0.0, 1.0)
    out["gap_behind_norm"] = np.clip(gap_behind / 15.0, 0.0, 1.0)

    # DRS zone proximity (within 1.0s of car ahead)
    out["in_drs_window"] = (gap_ahead <= 1.0).astype(float)

    # Undercut vulnerability: rival behind is within pit window delta (~1.5s-3.0s) and our tyres are degrading
    out["undercut_threat_score"] = np.clip(
        (1.0 - (gap_behind / 3.0)) * (wear_pct / 75.0),
        0.0,
        1.0,
    )

    # Overcut potential: clear air ahead (> 3.0s) with good tyre life
    out["overcut_potential_score"] = np.clip(
        (gap_ahead / 4.0) * (1.0 - wear_pct / 100.0),
        0.0,
        1.0,
    )

    return out
