"""SQLAlchemy ORM models for APEX Digital Twin & Telemetry Persistence."""
from datetime import UTC, datetime
from typing import Any, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def utcnow() -> datetime:
    return datetime.now(UTC)


class RaceSessionModel(Base):
    """Stores full race session metadata."""
    __tablename__ = "race_sessions"

    race_id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    track_name: Mapped[str] = mapped_column(String(64), nullable=False)
    total_laps: Mapped[int] = mapped_column(Integer, nullable=False, default=52)
    current_lap: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_finished: Mapped[bool] = mapped_column(Boolean, default=False)
    winner_car_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    total_race_time_s: Mapped[float | None] = mapped_column(Float, nullable=True)
    seed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    ticks: Mapped[list["TelemetryTickModel"]] = relationship("TelemetryTickModel", back_populates="session", cascade="all, delete-orphan")
    decisions: Mapped[list["DecisionLogModel"]] = relationship("DecisionLogModel", back_populates="session", cascade="all, delete-orphan")


class TelemetryTickModel(Base):
    """High-frequency telemetry tick snapshots for historical DVR replay."""
    __tablename__ = "telemetry_ticks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    race_id: Mapped[str] = mapped_column(String(64), ForeignKey("race_sessions.race_id", ondelete="CASCADE"), index=True)
    lap: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    tick_index: Mapped[int] = mapped_column(Integer, nullable=False)
    track_condition: Mapped[str] = mapped_column(String(32), default="DRY")
    safety_car: Mapped[str] = mapped_column(String(32), default="NONE")
    state_payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    session: Mapped[Optional["RaceSessionModel"]] = relationship("RaceSessionModel", back_populates="ticks")


class DecisionLogModel(Base):
    """Auditable log of every strategic recommendation and ML attribution."""
    __tablename__ = "decision_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    race_id: Mapped[str] = mapped_column(String(64), ForeignKey("race_sessions.race_id", ondelete="CASCADE"), index=True)
    lap: Mapped[int] = mapped_column(Integer, nullable=False)
    recommendation: Mapped[str] = mapped_column(String(32), nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    urgency: Mapped[str] = mapped_column(String(32), default="MEDIUM")
    rule_action: Mapped[str | None] = mapped_column(String(32), nullable=True)
    dqn_action: Mapped[str | None] = mapped_column(String(32), nullable=True)
    q_value_margin: Mapped[float | None] = mapped_column(Float, nullable=True)
    tyre_cliff_risk: Mapped[str | None] = mapped_column(String(32), nullable=True)
    explanation_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    session: Mapped[Optional["RaceSessionModel"]] = relationship("RaceSessionModel", back_populates="decisions")


class BenchmarkRunModel(Base):
    """Historical record of evaluation and benchmark suite runs."""
    __tablename__ = "benchmark_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_date: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    track_name: Mapped[str] = mapped_column(String(64), nullable=False)
    num_races: Mapped[int] = mapped_column(Integer, nullable=False)
    policy_name: Mapped[str] = mapped_column(String(64), nullable=False)
    avg_finish_position: Mapped[float] = mapped_column(Float, nullable=False)
    win_rate_pct: Mapped[float] = mapped_column(Float, nullable=False)
    podium_rate_pct: Mapped[float] = mapped_column(Float, nullable=False)
    avg_gap_to_p1_s: Mapped[float] = mapped_column(Float, nullable=False)
    blown_tyre_laps: Mapped[float] = mapped_column(Float, nullable=False)
    avg_pit_stops: Mapped[float] = mapped_column(Float, nullable=False)
    details_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
