"""Extract and standardize Race Control events (Safety Car, VSC, Red Flag)."""
from __future__ import annotations

import logging

import pandas as pd

logger = logging.getLogger(__name__)


def clean_race_control_dataframe(raw_messages: pd.DataFrame) -> pd.DataFrame:
    """
    Parses and categorizes race control message logs into structured status intervals:
    - SAFETY_CAR
    - VSC
    - RED_FLAG
    - YELLOW_FLAG
    - GREEN_FLAG
    """
    if raw_messages is None or raw_messages.empty:
        return pd.DataFrame(columns=["lap", "time_s", "category", "flag", "message", "status"])

    df = raw_messages.copy()
    records = []

    for _, row in df.iterrows():
        msg = str(row.get("Message", "")).upper()
        category = str(row.get("Category", "OTHER")).upper()
        lap = int(row.get("Lap", 0)) if pd.notna(row.get("Lap")) else 0
        
        status = "NONE"
        if "VIRTUAL SAFETY CAR" in msg or "VSC" in msg:
            status = "VSC"
        elif "SAFETY CAR" in msg or "SC" in msg:
            status = "SAFETY_CAR"
        elif "RED FLAG" in msg:
            status = "RED_FLAG"
        elif "YELLOW" in msg:
            status = "YELLOW"
        elif "CLEAR" in msg or "TRACK CLEAR" in msg or "GREEN" in msg:
            status = "GREEN"

        records.append({
            "lap": lap,
            "category": category,
            "status": status,
            "message": row.get("Message", ""),
        })

    return pd.DataFrame(records)
