"""SQLAlchemy ORM models for APEX Digital Twin & Telemetry Persistence."""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class RaceSessionModel(Base):
    """Stores full race session metadata."""
    __tablename__ = "race_sessions"

    race_id = Column(String(64), primary_key=True, index=True)
    track_name = Column(String(64), nullable=False)
    total_laps = Column(Integer, nullable=False, default=52)
    current_lap = Column(Integer, nullable=False, default=1)
    is_finished = Column(Boolean, default=False)
    winner_car_id = Column(String(32), nullable=True)
    total_race_time_s = Column(Float, nullable=True)
    seed = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    ticks = relationship("TelemetryTickModel", back_populates="session", cascade="all, delete-orphan")
    decisions = relationship("DecisionLogModel", back_populates="session", cascade="all, delete-orphan")


class TelemetryTickModel(Base):
    """High-frequency telemetry tick snapshots for historical DVR replay."""
    __tablename__ = "telemetry_ticks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    race_id = Column(String(64), ForeignKey("race_sessions.race_id", ondelete="CASCADE"), index=True)
    lap = Column(Integer, nullable=False, index=True)
    tick_index = Column(Integer, nullable=False)
    track_condition = Column(String(32), default="DRY")
    safety_car = Column(String(32), default="NONE")
    state_payload = Column(JSON, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    session = relationship("RaceSessionModel", back_populates="ticks")


class DecisionLogModel(Base):
    """Auditable log of every strategic recommendation and ML attribution."""
    __tablename__ = "decision_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    race_id = Column(String(64), ForeignKey("race_sessions.race_id", ondelete="CASCADE"), index=True)
    lap = Column(Integer, nullable=False)
    recommendation = Column(String(32), nullable=False)
    confidence_score = Column(Float, nullable=False)
    urgency = Column(String(32), nullable=False)
    rule_action = Column(String(32), nullable=True)
    dqn_action = Column(String(32), nullable=True)
    q_value_margin = Column(Float, nullable=True)
    tyre_cliff_risk = Column(Float, nullable=True)
    explanation_payload = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    session = relationship("RaceSessionModel", back_populates="decisions")


class BenchmarkRunModel(Base):
    """Historical record of evaluation and benchmark suite runs."""
    __tablename__ = "benchmark_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_date = Column(DateTime, default=datetime.utcnow)
    track_name = Column(String(64), nullable=False)
    num_races = Column(Integer, nullable=False)
    policy_name = Column(String(64), nullable=False)
    avg_finish_position = Column(Float, nullable=False)
    win_rate_pct = Column(Float, nullable=False)
    podium_rate_pct = Column(Float, nullable=False)
    avg_gap_to_p1_s = Column(Float, nullable=False)
    blown_tyre_laps = Column(Float, nullable=False)
    avg_pit_stops = Column(Float, nullable=False)
    details_json = Column(JSON, nullable=True)
