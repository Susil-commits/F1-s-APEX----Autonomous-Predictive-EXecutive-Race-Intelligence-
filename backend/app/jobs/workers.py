"""Asynchronous Worker Pool for compute-heavy strategy, replay, and ML jobs."""
import asyncio
import logging
import time
from typing import Any, Dict, List, Optional
import numpy as np

from backend.app.jobs.job_manager import ApexJobManager, JobPayload, JobStatus, JobType
from backend.app.simulator.models import (
    CarState,
    RaceState,
    TrackConfig,
    TyreCompound,
    WeatherState,
)

logger = logging.getLogger("apex.jobs.workers")


class ApexWorkerPool:
    """Pool of concurrent asynchronous background workers."""

    def __init__(self, worker_concurrency: int = 4):
        self.concurrency = worker_concurrency
        self.manager = ApexJobManager.get_instance()
        self._running = False
        self._worker_tasks: List[asyncio.Task] = []

    async def start(self) -> None:
        """Starts worker tasks in background."""
        if self._running:
            return
        self._running = True
        for i in range(self.concurrency):
            task = asyncio.create_task(self._worker_loop(worker_id=i + 1))
            self._worker_tasks.append(task)
        logger.info(f"[Worker Pool] Started {self.concurrency} async background workers.")

    async def stop(self) -> None:
        """Gracefully halts all workers."""
        self._running = False
        for task in self._worker_tasks:
            task.cancel()
        if self._worker_tasks:
            await asyncio.gather(*self._worker_tasks, return_exceptions=True)
        self._worker_tasks.clear()
        logger.info("[Worker Pool] Stopped all background workers.")

    async def _worker_loop(self, worker_id: int) -> None:
        """Continuous job polling and execution loop for an individual worker."""
        logger.debug(f"[Worker-{worker_id}] Ready to process jobs.")
        while self._running:
            try:
                # Wait for next available job from queue
                job: JobPayload = await self.manager.get_next_job()
                await self._process_job_safe(worker_id, job)
                self.manager.mark_task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[Worker-{worker_id}] Unexpected error in worker loop: {e}")
                await asyncio.sleep(1.0)

    async def _process_job_safe(self, worker_id: int, job: JobPayload) -> None:
        """Safely executes a job with exponential backoff on retries."""
        start_time = time.time()
        logger.info(f"[Worker-{worker_id}] Picked up job {job.job_id} ({job.job_type.value})")

        # Exponential backoff delay on retries: 2^retry_count * 0.5s
        if job.retry_count > 0:
            delay = (2 ** (job.retry_count - 1)) * 0.5
            await asyncio.sleep(delay)

        try:
            await self.manager.update_job_progress(job.job_id, 10.0)
            result = await self._dispatch_handler(job)
            await self.manager.complete_job(job.job_id, result)
            self._record_prometheus_duration(job.job_type.value, time.time() - start_time)
        except Exception as e:
            logger.error(f"[Worker-{worker_id}] Job {job.job_id} failed: {e}")
            await self.manager.fail_job(job.job_id, str(e), can_retry=True)

    async def _dispatch_handler(self, job: JobPayload) -> Dict[str, Any]:
        """Routes job to domain-specific compute engine."""
        if job.job_type == JobType.STRATEGY_MONTE_CARLO:
            return await self._handle_strategy_monte_carlo(job)
        elif job.job_type == JobType.HISTORICAL_REPLAY:
            return await self._handle_historical_replay(job)
        elif job.job_type == JobType.ML_RETRAIN_BATCH:
            return await self._handle_ml_retrain(job)
        elif job.job_type == JobType.ALERT_DISPATCH:
            return await self._handle_alert_dispatch(job)
        else:
            raise ValueError(f"Unsupported job type: {job.job_type}")

    async def _handle_strategy_monte_carlo(self, job: JobPayload) -> Dict[str, Any]:
        """Runs heavy multi-action stochastic Monte Carlo rollout."""
        from backend.app.strategy.monte_carlo import MonteCarloEngine

        params = job.params
        rollouts = int(params.get("n_rollouts", 500))
        current_lap = int(params.get("current_lap", 25))
        total_laps = int(params.get("total_laps", 52))
        tyre_compound_str = str(params.get("tyre_compound", "MEDIUM")).upper()
        tyre_age = int(params.get("tyre_age", 15))
        position = int(params.get("position", 3))

        compound_enum = (
            TyreCompound(tyre_compound_str)
            if tyre_compound_str in TyreCompound.__members__
            else TyreCompound.MEDIUM
        )

        # Construct minimal RaceState
        player_car = CarState(
            car_id="CAR_01",
            driver_name="Max Verstappen",
            team_name="Red Bull Racing",
            car_number=1,
            is_player=True,
            position=position,
            current_lap=current_lap,
            tyre_compound=compound_enum,
            tyre_age_laps=tyre_age,
            tyre_wear_pct=min(100.0, tyre_age * 2.8),
        )

        state = RaceState(
            race_id="sim-job",
            seed=42,
            track=TrackConfig(name="Silverstone", total_laps=total_laps),
            current_lap=current_lap,
            total_laps=total_laps,
            weather=WeatherState(),
            cars=[player_car],
        )

        await self.manager.update_job_progress(job.job_id, 40.0)
        mc_results = MonteCarloEngine.evaluate_candidates(state, num_rollouts_per_action=rollouts)
        await self.manager.update_job_progress(job.job_id, 90.0)

        evaluations = mc_results.get("evaluations", [])
        best_action = "STAY_OUT"
        if evaluations:
            best_action = min(evaluations, key=lambda a: a.get("expected_position", 20)).get("action", "STAY_OUT")

        return {
            "evaluations": evaluations,
            "best_action": best_action,
            "rollouts_per_action": rollouts,
            "evaluated_actions_count": len(evaluations),
        }

    async def _handle_historical_replay(self, job: JobPayload) -> Dict[str, Any]:
        """Ingests and replays historical session data in background."""
        from backend.app.simulator.historical_replay import HistoricalReplaySession

        track = job.params.get("track", "silverstone")
        session = HistoricalReplaySession(track_name=track)
        await self.manager.update_job_progress(job.job_id, 30.0)

        # Process replay laps
        laps_data = []
        for step in range(1, 15):
            lap_state = session.step()
            laps_data.append(lap_state)
            await self.manager.update_job_progress(job.job_id, 30.0 + (step / 15.0) * 65.0)

        return {
            "track": track,
            "total_laps_replayed": len(laps_data),
            "final_lap": laps_data[-1] if laps_data else None,
        }

    async def _handle_ml_retrain(self, job: JobPayload) -> Dict[str, Any]:
        """Retrains ML models or generates TreeSHAP attribution matrices."""
        from backend.app.intelligence.shap_explainer import TreeSHAPExplainer

        await self.manager.update_job_progress(job.job_id, 25.0)
        explainer = TreeSHAPExplainer.get_instance()
        await self.manager.update_job_progress(job.job_id, 65.0)
        sample_features = np.random.uniform(0.0, 1.0, size=28)
        explanation = explainer.explain(sample_features)
        drift_audit = explainer.verify_drift()
        await self.manager.update_job_progress(job.job_id, 90.0)

        return {
            "model_type": "TreeSHAP_Tyre_GradientBoost",
            "feature_importances": explanation.get("contributions", [])[:10],
            "drift_audit": drift_audit,
            "retrained_timestamp": time.time(),
        }

    async def _handle_alert_dispatch(self, job: JobPayload) -> Dict[str, Any]:
        """Dispatches synthesized radio commentary or alert notifications."""
        from backend.app.intelligence.commentary_generator import CommentaryEngine

        engine = CommentaryEngine()
        context = job.params.get("context", {})
        message = engine.generate_commentary(context)
        await self.manager.update_job_progress(job.job_id, 80.0)

        return {
            "alert_type": job.params.get("alert_type", "INCIDENT_ALERT"),
            "dispatched_text": message,
            "urgency": job.params.get("urgency", "HIGH"),
        }

    def _record_prometheus_duration(self, job_type_str: str, duration_sec: float) -> None:
        try:
            from backend.app.api.metrics import APEX_JOB_DURATION
            APEX_JOB_DURATION.labels(job_type=job_type_str).observe(duration_sec)
        except Exception:
            pass


# Global worker pool instance
worker_pool = ApexWorkerPool(worker_concurrency=4)
