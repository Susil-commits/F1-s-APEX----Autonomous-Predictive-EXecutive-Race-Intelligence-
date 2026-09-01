"""APEX Core (Tier 1) — The Provably-Correct Predictive Baseline.

Provides:
- Ingestion: Clean adapters for FastF1, Jolpica, and historical race timing snapshots.
- Features: Point-in-time-safe feature builders with zero lookahead bias.
- Training: Reproducible XGBoost/Calibrated models with fixed temporal splits.
- API: Lightweight, standalone FastAPI prediction service (race_id + driver_id -> predicted finish).
"""

__version__ = "1.0.0"
