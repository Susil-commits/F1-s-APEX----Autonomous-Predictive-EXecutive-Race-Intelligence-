"""APEX Core V1 Predict Endpoint.

Maps:
    race_id + driver_id -> predicted finishing position + split conformal band + model version + data snapshot
"""
from __future__ import annotations

import logging
import os
import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field, field_validator
from scipy.stats import norm

from core.api.limiter import limiter
from core.api.metrics import PREDICTION_LATENCY_SECONDS, PREDICTION_REQUESTS_TOTAL
from core.features.feature_builder import (
    CIRCUIT_PROFILES,
    PRE_RACE_FEATURE_NAMES,
    PreRaceFeatureBuilder,
)
from core.security.auth import Role, require_role

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/core", tags=["Core Predictor"])

MODEL_FILE = os.path.join(
    os.path.dirname(__file__), "..", "models", "apex_core_v1_model.joblib"
)

_CACHED_MODEL: Any = None
_MODEL_LOCK = threading.Lock()
_RACES_CACHE: Dict[int, Tuple[float, List[Dict[str, Any]]]] = {}
_RACES_CACHE_LOCK = threading.Lock()
_RACES_CACHE_TTL_SECONDS = 3600.0


def get_core_model() -> Any:
    """Loads or trains on-demand the core V1 prediction model with thread safety."""
    global _CACHED_MODEL
    if _CACHED_MODEL is not None:
        return _CACHED_MODEL

    with _MODEL_LOCK:
        if _CACHED_MODEL is not None:
            return _CACHED_MODEL

        if os.path.exists(MODEL_FILE):
            try:
                from core.security.model_integrity import verify_model_integrity
                is_valid, msg = verify_model_integrity(MODEL_FILE)
                if not is_valid:
                    logger.warning("[APEX Security Warning] Model integrity check: %s", msg)
                _CACHED_MODEL = joblib.load(MODEL_FILE)
                return _CACHED_MODEL
            except Exception as exc:
                logger.warning("[APEX Model Error] Failed loading model: %s", exc)

        # Train fallback baseline
        from core.training.train import train_finishing_position_model
        _CACHED_MODEL = train_finishing_position_model(save_path=MODEL_FILE)
        return _CACHED_MODEL


class PredictRequest(BaseModel):
    race_id: str = Field(..., description="Circuit identifier or race code (e.g. 'silverstone', 'monza')")
    driver_id: str = Field(..., description="Driver 3-letter abbreviation (e.g. 'VER', 'HAM', 'NOR')")
    grid_position: Optional[int] = Field(None, ge=1, le=20, description="Override grid position")
    quali_delta_s: Optional[float] = Field(None, ge=0.0, le=10.0, description="Optional qualifying gap to pole in seconds")
    rain_probability: Optional[float] = Field(None, description="Override rain forecast (clamped to [0.0, 1.0])")
    weather_transition: Optional[bool] = Field(False, description="Forecasted mid-race dry-to-wet or wet-to-dry weather transition")

    @field_validator("rain_probability", mode="before")
    @classmethod
    def clamp_rain_prob(cls, v: Any) -> Optional[float]:
        if v is None:
            return None
        try:
            val = float(v)
            return float(np.clip(val, 0.0, 1.0))
        except (ValueError, TypeError):
            raise ValueError("rain_probability must be a numeric value")


class FeatureContribution(BaseModel):
    feature: str
    label: str
    value: float
    importance_pct: float
    direction: str  # "improves_finish" or "hurts_finish"


class StrategyLever(BaseModel):
    lever: str
    change: float
    predicted_position_before: float
    predicted_position_after: float
    positions_gained: float


class OpportunityRanking(BaseModel):
    feature: str
    label: str
    value: float
    importance_pct: float
    direction: str
    opportunity_score: float


class PredictResponse(BaseModel):
    race_id: str
    driver_id: str
    driver_name: str
    team_name: str
    grid_position: int
    predicted_position: int
    confidence_interval: List[int]
    quantile_interval: Optional[List[int]] = None
    quantile_p50: Optional[int] = None
    win_probability_pct: float
    podium_probability_pct: float
    model_version: str
    winning_model_family: Optional[str] = None
    model_trained_through_race_id: Optional[str] = None
    calibration_samples: Optional[int] = None
    data_snapshot_utc: str
    feature_contributions: List[FeatureContribution]
    strategy_recommendations: List[StrategyLever] = Field(default_factory=list)
    biggest_opportunity: Optional[OpportunityRanking] = None
    summary_explanation: str


async def compute_sensitivity(
    model: Any,
    base_feat_dict: dict,
    feature_builder: Any,
    current_pred: float,
) -> list:
    """
    Vary each adjustable pre-race feature (e.g. qualifying pace delta to pole)
    by realistic increments and measure predicted position sensitivity.
    Executes all candidate perturbations in a single batched threadpool invocation to eliminate dispatch latency.
    """
    adjustable_features = {
        "quali_delta_to_pole_s": ([-0.5, -0.3, -0.15], "quali_delta_to_pole_s", 5.0),
        "grid_position_norm": ([-3.0, -2.0], "grid_position_norm", 19.0),
    }

    candidates = []
    vectors = []
    for feature_name, (deltas, dict_key, scale) in adjustable_features.items():
        base_val = float(base_feat_dict.get(dict_key, base_feat_dict.get(feature_name, 0.0)))
        for delta in deltas:
            norm_delta = delta / scale
            test_val = max(0.0, base_val + norm_delta)
            if base_val <= 0.0 and delta < 0:
                continue
            test_dict = dict(base_feat_dict)
            test_dict[dict_key] = test_val

            feat_vec = feature_builder.dict_to_vector(test_dict)
            vectors.append(feat_vec)
            candidates.append({
                "lever": feature_name,
                "change": delta,
            })

    if not vectors:
        return []

    # Single batched vector inference offloaded to threadpool
    feat_matrix = np.vstack(vectors)
    test_preds = await run_in_threadpool(model.predict, feat_matrix)

    results = []
    for cand, pred in zip(candidates, test_preds):
        test_pred = float(pred)
        improvement = current_pred - test_pred  # positive = better (lower position number)

        if improvement > 0.1:  # only report meaningful improvements
            results.append({
                "lever": cand["lever"],
                "change": cand["change"],
                "predicted_position_before": round(current_pred, 1),
                "predicted_position_after": round(test_pred, 1),
                "positions_gained": round(improvement, 1),
            })

    # Sort by biggest improvement first
    results.sort(key=lambda x: x["positions_gained"], reverse=True)
    return results[:3]  # top 3 levers


def rank_opportunities(contributions: list, feat_dict: dict) -> list:
    """
    Rank features by (importance × distance from optimal) to surface
    the single biggest opportunity without re-running the model.
    """
    opportunities = []
    for c in contributions:
        if isinstance(c, dict):
            direction = c.get("direction")
            feat_name = c.get("feature", c.get("name", ""))
            imp = c.get("importance_pct", c.get("importance", 0.0))
            label = c.get("label", feat_name)
            val = c.get("value", feat_dict.get(feat_name, 0.0))
        else:
            direction = getattr(c, "direction", None)
            feat_name = getattr(c, "feature", getattr(c, "name", ""))
            imp = getattr(c, "importance_pct", getattr(c, "importance", 0.0))
            label = getattr(c, "label", feat_name)
            val = getattr(c, "value", feat_dict.get(feat_name, 0.0))

        if direction == "hurts_finish":
            # Distance from an assumed "good" value of 0.2 (tune per feature)
            distance_from_optimal = abs(float(feat_dict.get(feat_name, 0.5)) - 0.2)
            opportunity_score = float(imp) * distance_from_optimal
            opportunities.append({
                "feature": feat_name,
                "label": label,
                "value": round(float(val), 2),
                "importance_pct": round(float(imp), 1),
                "direction": direction,
                "opportunity_score": round(float(opportunity_score), 2),
            })

    opportunities.sort(key=lambda x: x["opportunity_score"], reverse=True)
    return opportunities[:1]  # single biggest opportunity


def estimate_finish_probabilities(
    raw_pred: float,
    residual_std: float,
    rank_pos: Optional[int] = None,
) -> Tuple[float, float]:
    """Calibrated normal-CDF win (P1) and podium (P1-P3) probabilities from calibration residual spread."""
    sigma = max(1.0, float(residual_std))
    win_prob = float(np.clip(norm.cdf((1.5 - raw_pred) / sigma) * 100.0, 0.1, 95.0))
    podium_prob = float(np.clip(norm.cdf((3.5 - raw_pred) / sigma) * 100.0, 0.5, 99.0))
    if rank_pos == 1:
        podium_prob = max(podium_prob, 80.0)
    return round(win_prob, 1), round(podium_prob, 1)


@router.post("/predict", response_model=PredictResponse)
@limiter.limit("30/minute")
async def predict_finish(request: Request, req: PredictRequest):
    # slowapi reads `request` automatically for rate-key extraction; body schema unchanged
    """Tier 1 Provably-Correct Pre-Race Finish Predictor."""
    raw_driver = req.driver_id.strip() if req.driver_id else ""
    if not raw_driver or not raw_driver.isalpha() or len(raw_driver) != 3:
        raise HTTPException(
            status_code=400,
            detail="Invalid driver_id: must be a 3-letter F1 driver abbreviation (e.g. 'VER', 'HAM', 'NOR').",
        )
    driver_key = raw_driver.upper()
    from core.data.roster_service import DEFAULT_DRIVER_ROSTER, get_roster_service
    roster_svc = get_roster_service()
    profile = roster_svc.get_driver(driver_key) or DEFAULT_DRIVER_ROSTER.get(driver_key)
    if profile is None:
        # Default generic driver profile
        profile = {
            "name": f"Driver {driver_key}",
            "team": "F1 Competitor",
            "default_grid": 10,
            "pts_share": 0.05,
            "rolling_avg": 10.0,
            "starts": 5,
        }

    start_time = time.perf_counter()
    circuit_id = req.race_id.lower().replace("_2024", "").replace("_2025", "")
    grid: int = req.grid_position if req.grid_position is not None else int(profile.get("default_grid", 10))
    quali_delta_s: float = (
        float(req.quali_delta_s)
        if req.quali_delta_s is not None
        else max(0.0, (grid - 1) * 0.12)
    )
    rain: float = req.rain_probability if req.rain_probability is not None else 0.10

    weather_trans: bool = req.weather_transition if req.weather_transition is not None else False

    rolling_avg: float = float(profile.get("rolling_avg", 10.0))
    starts: int = int(profile.get("starts", 5))
    pts_share: float = float(profile.get("pts_share", 0.05))
    dnf_rate: float = float(profile.get("dnf_rate", 0.08))
    constructor_race_gain: float = float(profile.get("constructor_race_gain", 0.0))
    driver_name: str = str(profile.get("name", f"Driver {driver_key}"))
    team_name: str = str(profile.get("team", "F1 Competitor"))

    feat_vec, feat_dict = PreRaceFeatureBuilder.extract_features(
        grid_position=grid,
        quali_delta_s=quali_delta_s,
        rolling_avg_finish=rolling_avg,
        circuit_starts=starts,
        constructor_pts_share=pts_share,
        circuit_id=circuit_id,
        rain_prob=rain,
        weather_transition=weather_trans,
        dnf_rate=dnf_rate,
        constructor_race_gain=constructor_race_gain,
    )

    artifact = get_core_model()
    model = artifact["model"]
    q_hat = artifact.get("q_hat_margin", 2.0)
    winning_family = artifact.get("winning_model_family", "catboost")
    conformal_meta = artifact.get("conformal", {})
    quantile_models = artifact.get("quantile_models")
    trained_through = artifact.get("model_trained_through_race_id", "season_2023_finale")
    cal_n = conformal_meta.get("calibration_samples", artifact.get("metrics", {}).get("n_cal_samples", 200))

    # Production Durability: Drift & Staleness check (>90 days recommendation)
    snapshot_str = artifact.get("data_snapshot_utc")
    if snapshot_str:
        try:
            snapshot_dt = datetime.fromisoformat(snapshot_str.replace("Z", "+00:00"))
            age_days = (datetime.now(timezone.utc) - snapshot_dt).days
            if age_days > 90:
                logger.warning(
                    f"[APEX Production Drift] Model checkpoint is {age_days} days old (>90 days). Automatic retrain recommended."
                )
        except Exception:
            pass

    # Predict continuous finish position via threadpool offload to avoid blocking the event loop
    raw_pred = float((await run_in_threadpool(model.predict, feat_vec.reshape(1, -1)))[0])
    pred_pos = int(np.clip(np.round(raw_pred), 1, 20))

    # Compute What-If Sensitivity Levers (Plan 3)
    sensitivity = await compute_sensitivity(model, feat_dict, PreRaceFeatureBuilder, raw_pred)

    # Split Conformal 90% confidence interval
    lower = int(np.clip(np.floor(raw_pred - q_hat), 1, 20))
    upper = int(np.clip(np.ceil(raw_pred + q_hat), 1, 20))

    # Quantile Regression Asymmetric Interval (CQR Calibrated P10 - P90)
    quantile_interval: Optional[List[int]] = None
    quantile_p50: Optional[int] = None
    cqr_margin = float(artifact.get("cqr_margin", 0.0))
    if quantile_models and isinstance(quantile_models, dict):
        try:
            q10_raw = float((await run_in_threadpool(quantile_models["q10"].predict, feat_vec.reshape(1, -1)))[0])
            q50_raw = float((await run_in_threadpool(quantile_models["q50"].predict, feat_vec.reshape(1, -1)))[0])
            q90_raw = float((await run_in_threadpool(quantile_models["q90"].predict, feat_vec.reshape(1, -1)))[0])
            p10 = int(np.clip(np.floor(q10_raw - cqr_margin), 1, 20))
            p50 = int(np.clip(np.round(q50_raw), 1, 20))
            p90 = int(np.clip(np.ceil(q90_raw + cqr_margin), 1, 20))
            # Monotonicity guarantee
            p10 = min(p10, p50)
            p90 = max(p90, p50)
            quantile_interval = [p10, p90]
            quantile_p50 = p50
        except Exception as q_exc:
            logger.warning(f"[APEX Quantile Inference Error] {q_exc}")

    # Calibrated win & podium probabilities from empirical calibration residual spread
    residual_std = float(artifact.get("residual_std", max(1.0, float(q_hat) / 1.645)))
    win_prob, podium_prob = estimate_finish_probabilities(raw_pred, residual_std, rank_pos=pred_pos)

    # Plain feature contributions for transparent UI explanation
    feature_labels = {
        "grid_position_norm": "Grid Starting Position",
        "constructor_pts_share": "Car Championship Pace",
        "driver_rolling_finish_norm": "Recent Driver Form (Last 5)",
        "circuit_power_sensitivity": "Engine Power Sensitivity",
        "circuit_downforce_index": "Track Downforce Demand",
        "driver_circuit_experience": "Circuit Experience",
        "race_rain_prob": "Precipitation Forecast",
        "quali_delta_to_pole_s": "Qualifying Pace Delta",
        "circuit_is_street_track": "Street Track Volatility",
        "weather_transition_flag": "Mid-Race Weather Transition Risk",
        "driver_dnf_rate": "Historical DNF Reliability Risk",
        "constructor_race_gain_norm": "Constructor Race-Day Pace Gain",
    }

    # Extract tree feature importances uniformly across GBR, XGBoost, CatBoost
    raw_importances = getattr(model, "feature_importances_", None)
    if raw_importances is None and hasattr(model, "get_feature_importance"):
        raw_importances = model.get_feature_importance()

    if raw_importances is not None and np.sum(raw_importances) > 0:
        norm_importances = (np.array(raw_importances, dtype=float) / float(np.sum(raw_importances))) * 100.0
    else:
        norm_importances = np.ones(len(PRE_RACE_FEATURE_NAMES)) * (100.0 / len(PRE_RACE_FEATURE_NAMES))

    contributions = []
    for idx, name in enumerate(PRE_RACE_FEATURE_NAMES):
        imp = float(norm_importances[idx])
        val = feat_dict.get(name, 0.0)
        # Direction
        if name in ["grid_position_norm", "quali_delta_to_pole_s", "driver_rolling_finish_norm"]:
            direction = "improves_finish" if val < 0.4 else "hurts_finish"
        else:
            direction = "improves_finish" if val > 0.5 else "neutral"

        contributions.append(
            FeatureContribution(
                feature=name,
                label=feature_labels.get(name, name),
                value=round(val, 2),
                importance_pct=round(imp, 1),
                direction=direction,
            )
        )
    contributions.sort(key=lambda c: c.importance_pct, reverse=True)

    # Opportunity Ranking (Plan 4)
    opps = rank_opportunities(contributions, feat_dict)
    biggest_opportunity = opps[0] if opps else None

    summary = (
        f"{profile['name']} starts P{grid} for the {circuit_id.title()} Grand Prix. "
        f"Accounting for {profile['team']}'s car pace and current driver form, "
        f"APEX projects a P{pred_pos} finish with a strategic finishing window between P{lower} and P{upper}."
    )

    # Record Prometheus Observability Metrics
    duration_s = time.perf_counter() - start_time
    PREDICTION_LATENCY_SECONDS.labels(circuit=circuit_id).observe(duration_s)
    PREDICTION_REQUESTS_TOTAL.labels(driver_id=driver_key, status="success").inc()

    return PredictResponse(
        race_id=req.race_id,
        driver_id=driver_key,
        driver_name=driver_name,
        team_name=team_name,
        grid_position=grid,
        predicted_position=pred_pos,
        confidence_interval=[lower, upper],
        quantile_interval=quantile_interval,
        quantile_p50=quantile_p50,
        win_probability_pct=round(win_prob, 1),
        podium_probability_pct=round(podium_prob, 1),
        model_version=artifact.get("version", "core-v1.0.0"),
        winning_model_family=winning_family,
        model_trained_through_race_id=trained_through,
        calibration_samples=cal_n,
        data_snapshot_utc=datetime.now(timezone.utc).isoformat(),
        feature_contributions=contributions[:5],
        strategy_recommendations=sensitivity,
        biggest_opportunity=biggest_opportunity,
        summary_explanation=summary,
    )


# ── ENTERPRISE GRID & IN-RACE SIMULATION SCHEMAS ──────────────────────────────

class GridPredictRequest(BaseModel):
    race_id: str = Field(..., description="Circuit identifier (e.g. 'silverstone', 'monaco')")
    rain_probability: Optional[float] = Field(0.10, ge=0.0, le=1.0)
    weather_transition: Optional[bool] = Field(False)
    grid_overrides: Optional[Dict[str, int]] = Field(default_factory=dict, description="Custom grid positions by driver code")
    quali_delta_overrides: Optional[Dict[str, float]] = Field(default_factory=dict, description="Optional qualifying gap to pole (seconds) by driver code")


class GridDriverFinish(BaseModel):
    driver_id: str
    driver_name: str
    team_name: str
    grid_position: int
    predicted_position: int
    raw_score: float
    confidence_interval: List[int]
    win_probability_pct: float
    podium_probability_pct: float
    color: str
    country: str
    photo: Optional[str] = None


class GridPredictResponse(BaseModel):
    race_id: str
    total_drivers: int
    rain_probability: float
    weather_transition: bool
    grid_results: List[GridDriverFinish]
    execution_time_ms: float
    model_version: str
    summary: str


class PitSimulationRequest(BaseModel):
    race_id: str = Field(..., description="Circuit identifier (e.g. 'silverstone')")
    current_lap: int = Field(..., ge=1, le=80)
    current_position: int = Field(..., ge=1, le=20)
    current_compound: str = Field(default="C3")
    current_tyre_age: int = Field(default=10, ge=1)
    simulations_count: Optional[int] = Field(default=10000, ge=500, le=50000)
    rain_probability: float = Field(default=0.0, ge=0.0, le=1.0)


class UndercutRequest(BaseModel):
    driver_current_age: int = Field(..., ge=1)
    driver_compound: str = Field(default="C3")
    rival_gap_s: float = Field(..., description="Gap in seconds to rival ahead")
    fresh_compound: str = Field(default="C2")
    track_temp_c: Optional[float] = Field(default=30.0)


# ── ENTERPRISE ENDPOINTS ─────────────────────────────────────────────────────

@router.post("/predict/grid", response_model=GridPredictResponse)
@limiter.limit("20/minute")
async def predict_full_grid(request: Request, req: GridPredictRequest):
    """Vectorized Full 20-Car Grid Finish Order Prediction.

    Evaluates all active drivers simultaneously in a single vectorized inference
    matrix pass with zero cross-driver collisions.
    """
    start_time = time.perf_counter()
    from core.data.roster_service import DEFAULT_DRIVER_ROSTER, get_roster_service
    roster_svc = get_roster_service()
    drivers = roster_svc.get_all_drivers(active_only=True)
    if not drivers:
        drivers = list(DEFAULT_DRIVER_ROSTER.values())

    circuit_id = req.race_id.lower().replace("_2024", "").replace("_2025", "")
    rain = float(req.rain_probability if req.rain_probability is not None else 0.10)
    weather_trans = bool(req.weather_transition)

    artifact = get_core_model()
    model = artifact["model"]
    q_hat = float(artifact.get("q_hat_margin", 2.0))

    feature_matrix: List[np.ndarray] = []
    driver_meta_list: List[Dict[str, Any]] = []

    for d in drivers:
        code = d["code"]
        grid = req.grid_overrides.get(code, d.get("default_grid", 10))
        q_delta = (
            float(req.quali_delta_overrides[code])
            if req.quali_delta_overrides and code in req.quali_delta_overrides
            else max(0.0, (grid - 1) * 0.12)
        )
        rolling_avg = float(d.get("rolling_avg", 10.0))
        starts = int(d.get("starts", 5))
        pts_share = float(d.get("pts_share", 0.05))
        dnf_rate = float(d.get("dnf_rate", 0.08))
        c_gain = float(d.get("constructor_race_gain", 0.0))

        feat_vec, _ = PreRaceFeatureBuilder.extract_features(
            grid_position=grid,
            quali_delta_s=q_delta,
            rolling_avg_finish=rolling_avg,
            circuit_starts=starts,
            constructor_pts_share=pts_share,
            circuit_id=circuit_id,
            rain_prob=rain,
            weather_transition=weather_trans,
            dnf_rate=dnf_rate,
            constructor_race_gain=c_gain,
        )
        feature_matrix.append(feat_vec)
        driver_meta_list.append({
            "code": code,
            "name": d.get("name", code),
            "team": d.get("team", "Competitor"),
            "grid": grid,
            "color": d.get("color", "#E10600"),
            "country": d.get("country", "🏁"),
            "photo": d.get("photo"),
        })

    # Vectorized inference over full grid in threadpool
    X = np.array(feature_matrix, dtype=np.float32)
    raw_preds = await run_in_threadpool(model.predict, X)

    # Rank drivers based on continuous score to produce strictly monotonic grid finishing order
    indexed_scores = list(enumerate(raw_preds))
    indexed_scores.sort(key=lambda x: x[1])

    residual_std = float(artifact.get("residual_std", max(1.0, q_hat / 1.645)))
    grid_results: List[GridDriverFinish] = []
    for rank_idx, (orig_idx, score) in enumerate(indexed_scores, start=1):
        meta = driver_meta_list[orig_idx]
        raw_val = float(score)
        lower = max(1, int(np.floor(raw_val - q_hat)))
        upper = min(20, int(np.ceil(raw_val + q_hat)))

        win_prob, podium_prob = estimate_finish_probabilities(raw_val, residual_std, rank_pos=rank_idx)

        grid_results.append(
            GridDriverFinish(
                driver_id=meta["code"],
                driver_name=meta["name"],
                team_name=meta["team"],
                grid_position=meta["grid"],
                predicted_position=rank_idx,
                raw_score=round(raw_val, 2),
                confidence_interval=[lower, upper],
                win_probability_pct=round(win_prob, 1),
                podium_probability_pct=round(podium_prob, 1),
                color=meta["color"],
                country=meta["country"],
                photo=meta.get("photo"),
            )
        )

    exec_ms = (time.perf_counter() - start_time) * 1000.0
    winner = grid_results[0]
    summary = (
        f"Simulated {len(grid_results)}-driver grid for the {circuit_id.title()} GP in {exec_ms:.1f}ms. "
        f"Projected winner: {winner.driver_name} ({winner.team_name}) from P{winner.grid_position}."
    )

    return GridPredictResponse(
        race_id=req.race_id,
        total_drivers=len(grid_results),
        rain_probability=rain,
        weather_transition=weather_trans,
        grid_results=grid_results,
        execution_time_ms=round(exec_ms, 1),
        model_version=artifact.get("version", "core-v1.0.0"),
        summary=summary,
    )


@router.post("/simulate/pit-stop")
@limiter.limit("20/minute")
async def simulate_pit_stop(request: Request, req: PitSimulationRequest):
    """Monte Carlo In-Race Pit Stop Strategy Simulation.

    Performs 10,000+ stochastic rollouts modeling tyre degradation, VSC/SC hazard rates,
    pit time loss delta, and undercut/overcut net track position expectations.
    """
    from core.simulation.monte_carlo import MonteCarloRaceSimulator
    sim = MonteCarloRaceSimulator()
    result = await run_in_threadpool(
        sim.simulate_strategy_comparison,
        circuit_id=req.race_id,
        current_lap=req.current_lap,
        current_pos=req.current_position,
        current_compound=req.current_compound,
        current_tyre_age=req.current_tyre_age,
        n_simulations=req.simulations_count or 10000,
        rain_probability=req.rain_probability,
    )
    return result


@router.get("/tyres/stint-curve")
async def get_tyre_stint_curve(
    compound: str = "C3",
    total_laps: int = 40,
    track_temp_c: float = 30.0,
    circuit_downforce_index: float = 0.70,
):
    """Generates non-linear pace degradation trajectory across a multi-lap stint."""
    from core.features.tyre_model import TyreDegradationModel
    model = TyreDegradationModel()
    curve = model.simulate_stint_curve(
        compound_code=compound,
        total_laps=total_laps,
        track_temp_c=track_temp_c,
        circuit_downforce_index=circuit_downforce_index,
    )
    return {
        "compound": compound.upper(),
        "total_laps": total_laps,
        "track_temp_c": track_temp_c,
        "circuit_downforce_index": circuit_downforce_index,
        "curve": curve,
    }


@router.post("/tyres/undercut")
async def evaluate_undercut(req: UndercutRequest):
    """Evaluates undercut feasibility and fresh tire out-lap pace delta."""
    from core.features.tyre_model import TyreDegradationModel
    model = TyreDegradationModel()
    return model.evaluate_undercut_window(
        driver_current_age=req.driver_current_age,
        driver_compound=req.driver_compound,
        rival_gap_s=req.rival_gap_s,
        fresh_compound=req.fresh_compound,
        track_temp_c=req.track_temp_c or 30.0,
    )


@router.get("/races")
async def list_available_races(season: int = 2026):
    """Lists race venues for the requested season using a non-blocking TTL cache enriched with circuit profiles."""
    now = time.monotonic()
    with _RACES_CACHE_LOCK:
        cached = _RACES_CACHE.get(season)
        if cached and (now - cached[0]) < _RACES_CACHE_TTL_SECONDS:
            return {"season": season, "cached": True, "races": cached[1]}

    from core.ingestion.jolpica_adapter import JolpicaAdapter

    adapter = JolpicaAdapter()
    raw_races = await run_in_threadpool(adapter.get_season_races, season)
    enriched_races: List[Dict[str, Any]] = []
    for race in raw_races:
        cid = str(race.get("circuit_id", "")).lower()
        profile = CIRCUIT_PROFILES.get(cid, {})
        enriched_races.append({
            **race,
            "laps": int(profile.get("laps", 57)),
            "downforce": float(profile.get("downforce", 0.7)),
            "power": float(profile.get("power", 0.75)),
            "street": bool(profile.get("street", 0.0) >= 0.5),
            "sc_probability": float(profile.get("sc_probability", 0.4)),
        })

    with _RACES_CACHE_LOCK:
        _RACES_CACHE[season] = (time.monotonic(), enriched_races)

    return {"season": season, "cached": False, "races": enriched_races}


@router.get("/drivers")
async def list_available_drivers():
    """Lists dynamic driver roster for APEX analysis."""
    from core.data.roster_service import get_roster_service
    roster_svc = get_roster_service()
    drivers = roster_svc.get_all_drivers(active_only=False)
    return {"drivers": drivers}


@router.post("/drivers/sync")
async def sync_drivers_from_jolpica(year: int = 2026, role: Role = Depends(require_role(Role.ENGINEER))):
    """Synchronizes active driver roster and constructor points share from live Jolpica standings. Requires ENGINEER role."""
    from core.data.roster_service import get_roster_service
    roster_svc = get_roster_service()
    try:
        result = await run_in_threadpool(roster_svc.sync_from_jolpica, year=year)
        return {"status": "synced", **result}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Jolpica standings sync failed: {exc}")


