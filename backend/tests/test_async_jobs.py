"""Pytest suite for Asynchronous Job Manager, BullMQ/Redis worker pool, idempotency, and retries."""
import asyncio
import pytest

from backend.app.jobs.job_manager import ApexJobManager, JobStatus, JobType
from backend.app.jobs.workers import ApexWorkerPool


@pytest.mark.asyncio
async def test_job_manager_enqueue_and_idempotency():
    manager = ApexJobManager.get_instance()
    params = {"n_rollouts": 500, "current_lap": 15, "total_laps": 52, "tyre_compound": "MEDIUM"}

    job1 = await manager.enqueue_job(JobType.STRATEGY_MONTE_CARLO, params)
    assert job1.status in (JobStatus.QUEUED, JobStatus.PROCESSING, JobStatus.COMPLETED)

    # Re-enqueuing identical params must return identical job (idempotent deduplication)
    job2 = await manager.enqueue_job(JobType.STRATEGY_MONTE_CARLO, params)
    assert job1.job_id == job2.job_id
    assert job1.idempotency_key == job2.idempotency_key


@pytest.mark.asyncio
async def test_worker_pool_executes_monte_carlo():
    manager = ApexJobManager.get_instance()
    pool = ApexWorkerPool(worker_concurrency=2)
    await pool.start()

    try:
        params = {
            "n_rollouts": 100,
            "current_lap": 20,
            "total_laps": 52,
            "tyre_compound": "HARD",
            "tyre_age": 10,
            "position": 3,
            "actions": ["PIT_NOW", "STAY_OUT"],
        }
        job = await manager.enqueue_job(JobType.STRATEGY_MONTE_CARLO, params)

        # Wait for worker completion
        for _ in range(30):
            status_job = manager.get_job(job.job_id)
            if status_job and status_job.status == JobStatus.COMPLETED:
                break
            await asyncio.sleep(0.1)

        completed_job = manager.get_job(job.job_id)
        assert completed_job is not None
        assert completed_job.status == JobStatus.COMPLETED
        assert completed_job.progress_pct == 100.0
        assert "best_action" in completed_job.result
        assert "evaluations" in completed_job.result
    finally:
        await pool.stop()


@pytest.mark.asyncio
async def test_worker_pool_executes_ml_retrain():
    manager = ApexJobManager.get_instance()
    pool = ApexWorkerPool(worker_concurrency=1)
    await pool.start()

    try:
        job = await manager.enqueue_job(JobType.ML_RETRAIN_BATCH, {"model": "treeshap"})
        for _ in range(30):
            status_job = manager.get_job(job.job_id)
            if status_job and status_job.status == JobStatus.COMPLETED:
                break
            await asyncio.sleep(0.1)

        completed_job = manager.get_job(job.job_id)
        assert completed_job is not None
        assert completed_job.status == JobStatus.COMPLETED
        assert "feature_importances" in completed_job.result
    finally:
        await pool.stop()
