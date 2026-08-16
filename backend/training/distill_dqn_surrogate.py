"""DQN Policy Distillation Pipeline for APEX TreeSHAP Explainability.

Trains high-fidelity tree surrogate models (global & per-action) to imitate
the trained DQN's Q-value predictions across realistic race rollouts and logged telemetry.
"""
from typing import List, Tuple, Dict, Any, Optional
import os
import sys
import argparse
import asyncio
import hashlib
from datetime import datetime, timezone
import json
import joblib
import numpy as np
import torch
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from stable_baselines3 import DQN

from backend.app.simulator.models import StrategyAction
from backend.app.simulator.track import list_available_tracks
from backend.app.strategy.gym_env import ApexRaceGymEnv, ACTION_MAP
from backend.app.intelligence.feature_builder import FeatureBuilder, FEATURE_NAMES, FEATURE_DIM
from backend.app.twin.database import get_db_session, init_db
from backend.app.twin.db_models import DecisionLogModel, TelemetryTickModel
from sqlalchemy import select


def collect_dqn_rollouts(
    model: DQN,
    num_episodes: int = 100,
    tracks: Optional[List[str]] = None,
    seed_offset: int = 42,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Executes real rollouts using the trained DQN policy in diverse race environments.
    
    Returns:
        X (np.ndarray): Feature matrix of shape (N, FEATURE_DIM)
        y_chosen_q (np.ndarray): Q-value of the DQN's chosen action (N,)
        actions (np.ndarray): Chosen action indices (N,)
        q_distributions (np.ndarray): Full Q-value vector across all 8 actions (N, 8)
    """
    if tracks is None:
        tracks = list_available_tracks() or ["silverstone", "monza", "spa", "monaco", "interlagos"]

    feature_list: List[np.ndarray] = []
    chosen_q_list: List[float] = []
    action_list: List[int] = []
    q_dist_list: List[np.ndarray] = []

    print(f"[Distillation] Collecting rollouts across {len(tracks)} circuits ({num_episodes} total episodes)...")
    device = model.device

    episodes_per_track = max(1, num_episodes // len(tracks))
    total_steps = 0

    for track_idx, track_name in enumerate(tracks):
        for ep in range(episodes_per_track):
            ep_seed = seed_offset + track_idx * 1000 + ep
            env = ApexRaceGymEnv(track_name=track_name, seed=ep_seed)
            obs, _ = env.reset(seed=ep_seed)
            done = False

            while not done:
                # Compute exact Q-values from DQN Q-network
                with torch.no_grad():
                    obs_tensor = torch.as_tensor(obs, dtype=torch.float32).unsqueeze(0).to(device)
                    q_vals = model.q_net(obs_tensor).squeeze(0).cpu().numpy()

                action_int = int(np.argmax(q_vals))
                chosen_q = float(q_vals[action_int])

                feature_list.append(obs.copy())
                chosen_q_list.append(chosen_q)
                action_list.append(action_int)
                q_dist_list.append(q_vals.copy())
                total_steps += 1

                # Advance environment
                obs, reward, terminated, truncated, info = env.step(action_int)
                done = terminated or truncated

    X = np.array(feature_list, dtype=np.float32)
    y = np.array(chosen_q_list, dtype=np.float32)
    actions = np.array(action_list, dtype=np.int64)
    q_distributions = np.array(q_dist_list, dtype=np.float32)

    print(f"[Distillation] Collected {len(X)} state-action-Q transitions from {num_episodes} rollout episodes.")
    return X, y, actions, q_distributions


async def load_persisted_telemetry_samples(
    model: DQN,
) -> Tuple[Optional[np.ndarray], Optional[np.ndarray], Optional[np.ndarray]]:
    """
    Extracts real race session states from database and computes corresponding DQN Q-values.
    """
    try:
        await init_db()
        async with get_db_session() as session:
            stmt = select(TelemetryTickModel).limit(5000)
            result = await session.execute(stmt)
            ticks = result.scalars().all()

            if not ticks:
                return None, None, None

            features = []
            chosen_qs = []
            all_qs = []
            device = model.device

            for tick in ticks:
                payload = tick.state_payload
                if not payload or not isinstance(payload, dict):
                    continue
                try:
                    from backend.app.simulator.models import RaceState
                    state = RaceState.model_validate(payload)
                    feat = FeatureBuilder.extract_features(state)
                    with torch.no_grad():
                        obs_tensor = torch.as_tensor(feat, dtype=torch.float32).unsqueeze(0).to(device)
                        q_vals = model.q_net(obs_tensor).squeeze(0).cpu().numpy()
                    action_int = int(np.argmax(q_vals))
                    features.append(feat)
                    chosen_qs.append(float(q_vals[action_int]))
                    all_qs.append(q_vals.copy())
                except Exception:
                    continue

            if features:
                print(f"[Distillation] Ingested {len(features)} real logged decision states from database.")
                return (
                    np.array(features, dtype=np.float32),
                    np.array(chosen_qs, dtype=np.float32),
                    np.array(all_qs, dtype=np.float32),
                )
    except Exception as e:
        print(f"[Distillation] Note: Database telemetry ingestion skipped: {e}")

    return None, None, None


def train_surrogate_model(
    X: np.ndarray,
    y: np.ndarray,
    q_distributions: np.ndarray,
    save_path: str = "backend/models/shap_surrogate.joblib",
    multi_action_save_path: str = "backend/models/shap_multi_action_surrogate.joblib",
    meta_path: str = "backend/models/shap_surrogate_meta.json",
    dqn_model_hash: Optional[str] = None,
    dqn_model_path: Optional[str] = None,
) -> Tuple[GradientBoostingRegressor, Dict[int, GradientBoostingRegressor]]:
    """
    Trains global chosen-Q surrogate and per-action surrogate tree models.
    """
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, shuffle=True
    )

    print(f"[Distillation] Fitting Global GradientBoosting surrogate (train={len(X_train)}, test={len(X_test)})...")
    surrogate = GradientBoostingRegressor(
        n_estimators=120,
        max_depth=4,
        learning_rate=0.08,
        subsample=0.85,
        random_state=42,
    )
    surrogate.fit(X_train, y_train)

    # Evaluate global fidelity
    y_pred_train = surrogate.predict(X_train)
    y_pred_test = surrogate.predict(X_test)

    r2_train = r2_score(y_train, y_pred_train)
    r2_test = r2_score(y_test, y_pred_test)
    rmse_test = float(np.sqrt(mean_squared_error(y_test, y_pred_test)))
    mae_test = float(mean_absolute_error(y_test, y_pred_test))

    print(f"[Distillation] Global Surrogate Evaluation:")
    print(f"  • Train R² Score: {r2_train:.4f}")
    print(f"  • Test  R² Score: {r2_test:.4f}")
    print(f"  • Test  RMSE:     {rmse_test:.4f}")
    print(f"  • Test  MAE:      {mae_test:.4f}")

    joblib.dump(surrogate, save_path)
    print(f"[Distillation] Saved global surrogate model to {save_path}")

    # Train per-action models
    print(f"[Distillation] Fitting 8 Per-Action tree surrogate models for differential SHAP...")
    action_models: Dict[int, GradientBoostingRegressor] = {}
    action_metrics: Dict[str, Any] = {}

    for action_idx in range(8):
        action_name = ACTION_MAP.get(action_idx, StrategyAction.MAINTAIN).value
        y_act = q_distributions[:, action_idx]
        X_tr, X_te, y_tr, y_te = train_test_split(X, y_act, test_size=0.2, random_state=42)

        act_model = GradientBoostingRegressor(
            n_estimators=70,
            max_depth=3,
            learning_rate=0.1,
            subsample=0.85,
            random_state=42 + action_idx,
        )
        act_model.fit(X_tr, y_tr)
        act_r2 = r2_score(y_te, act_model.predict(X_te))
        action_models[action_idx] = act_model
        action_metrics[action_name] = {"action_idx": action_idx, "r2_test": round(float(act_r2), 4)}

    joblib.dump(action_models, multi_action_save_path)
    print(f"[Distillation] Saved 8 multi-action surrogate models to {multi_action_save_path}")

    # Save metadata with DQN model hash to eliminate drift risk
    feature_importances = {
        name: round(float(imp), 5)
        for name, imp in zip(FEATURE_NAMES, surrogate.feature_importances_)
    }
    feature_importances = dict(sorted(feature_importances.items(), key=lambda item: item[1], reverse=True))

    meta_payload = {
        "dqn_model_hash": dqn_model_hash,
        "dqn_model_path": dqn_model_path,
        "distilled_at": datetime.now(timezone.utc).isoformat(),
        "n_samples": int(len(X)),
        "train_samples": int(len(X_train)),
        "test_samples": int(len(X_test)),
        "r2_test": round(float(r2_test), 4),
        "rmse_test": round(float(rmse_test), 4),
        "mae_test": round(float(mae_test), 4),
        "feature_dim": FEATURE_DIM,
        "feature_importances": feature_importances,
        "action_models": action_metrics,
    }
    with open(meta_path, "w") as f:
        json.dump(meta_payload, f, indent=2)
    print(f"[Distillation] Saved surrogate metadata to {meta_path} (DQN hash: {dqn_model_hash})")

    return surrogate, action_models


def run_distillation(
    dqn_model_path: str = "backend/models/apex_dqn.zip",
    save_path: str = "backend/models/shap_surrogate.joblib",
    multi_action_save_path: str = "backend/models/shap_multi_action_surrogate.joblib",
    episodes: int = 80,
    include_db: bool = True,
):
    """Orchestrates DQN rollout collection, DB telemetry ingestion, and surrogate training."""
    if not os.path.exists(dqn_model_path):
        raise FileNotFoundError(f"DQN policy model not found at {dqn_model_path}")

    # Compute SHA-256 hash of the target DQN checkpoint for drift detection
    with open(dqn_model_path, "rb") as f:
        dqn_hash = hashlib.sha256(f.read()).hexdigest()

    print(f"[Distillation] Loading trained DQN policy from {dqn_model_path} (SHA-256: {dqn_hash[:12]}...)...")
    dqn_model = DQN.load(dqn_model_path)

    # 1. Collect rollout data
    X_rollout, y_rollout, actions, q_dist_rollout = collect_dqn_rollouts(
        model=dqn_model,
        num_episodes=episodes,
    )

    # 2. Ingest DB telemetry if available and requested
    X_combined = X_rollout
    y_combined = y_rollout
    q_dist_combined = q_dist_rollout

    if include_db:
        try:
            db_X, db_y, db_q = asyncio.run(load_persisted_telemetry_samples(dqn_model))
            if db_X is not None and db_y is not None and db_q is not None and len(db_X) > 0:
                X_combined = np.vstack([X_rollout, db_X])
                y_combined = np.concatenate([y_rollout, db_y])
                q_dist_combined = np.vstack([q_dist_rollout, db_q])
                print(f"[Distillation] Combined total dataset: {len(X_combined)} samples.")
        except Exception as e:
            print(f"[Distillation] Database telemetry loading failed: {e}")

    # 3. Train surrogate models
    train_surrogate_model(
        X=X_combined,
        y=y_combined,
        q_distributions=q_dist_combined,
        save_path=save_path,
        multi_action_save_path=multi_action_save_path,
        dqn_model_hash=dqn_hash,
        dqn_model_path=dqn_model_path,
    )
    print("[Distillation] Distillation pipeline completed successfully!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Distill DQN Policy into Tree Surrogate for TreeSHAP")
    parser.add_argument("--dqn-path", type=str, default="backend/models/apex_dqn.zip", help="Path to trained DQN zip checkpoint")
    parser.add_argument("--save-path", type=str, default="backend/models/shap_surrogate.joblib", help="Path to save global surrogate model")
    parser.add_argument("--multi-action-save-path", type=str, default="backend/models/shap_multi_action_surrogate.joblib", help="Path to save multi-action surrogate dictionary")
    parser.add_argument("--episodes", type=int, default=80, help="Number of rollout episodes to collect")
    parser.add_argument("--no-db", action="store_true", help="Disable database telemetry ingestion")

    args = parser.parse_args()
    run_distillation(
        dqn_model_path=args.dqn_path,
        save_path=args.save_path,
        multi_action_save_path=args.multi_action_save_path,
        episodes=args.episodes,
        include_db=not args.no_db,
    )
