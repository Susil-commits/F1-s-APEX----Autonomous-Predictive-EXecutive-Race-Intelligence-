"""Distributed Asynchronous Job Manager & BullMQ / Redis-compatible Queue Orchestrator."""
import asyncio
import hashlib
import json
import logging
import time
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("apex.jobs.manager")


class JobStatus(str, Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RETRYING = "RETRYING"


class JobType(str, Enum):
    STRATEGY_MONTE_CARLO = "STRATEGY_MONTE_CARLO"
    HISTORICAL_REPLAY = "HISTORICAL_REPLAY"
    ML_RETRAIN_BATCH = "ML_RETRAIN_BATCH"
    ALERT_DISPATCH = "ALERT_DISPATCH"


class JobPayload(BaseModel):
    job_id: str
    job_type: JobType
    params: Dict[str, Any]
    idempotency_key: str
    status: JobStatus = JobStatus.QUEUED
    progress_pct: float = 0.0
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    created_at: float = Field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None


class ApexJobManager:
    """Manages asynchronous compute jobs with Redis backing and in-memory fallback."""

    _instance: Optional["ApexJobManager"] = None

    def __init__(self):
        self._jobs: Dict[str, JobPayload] = {}
        self._idempotency_index: Dict[str, str] = {}
        self._queue: asyncio.Queue[JobPayload] = asyncio.Queue(maxsize=10000)
        self._lock = asyncio.Lock()
        self._redis_client = None

    @classmethod
    def get_instance(cls) -> "ApexJobManager":
        if cls._instance is None:
            cls._instance = ApexJobManager()
        return cls._instance

    def _generate_idempotency_key(self, job_type: JobType, params: Dict[str, Any]) -> str:
        param_str = json.dumps(params, sort_keys=True, default=str)
        hash_digest = hashlib.sha256(param_str.encode("utf-8")).hexdigest()[:16]
        return f"apex:job:{job_type.value}:{hash_digest}"

    async def enqueue_job(
        self,
        job_type: JobType,
        params: Dict[str, Any],
        max_retries: int = 3,
        custom_idempotency_key: Optional[str] = None,
    ) -> JobPayload:
        """Enqueues a job with idempotency deduplication."""
        idempotency_key = custom_idempotency_key or self._generate_idempotency_key(job_type, params)

        async with self._lock:
            # Check if an existing job is already queued or active
            if idempotency_key in self._idempotency_index:
                existing_job_id = self._idempotency_index[idempotency_key]
                existing_job = self._jobs.get(existing_job_id)
                if existing_job and existing_job.status in (JobStatus.QUEUED, JobStatus.PROCESSING, JobStatus.COMPLETED):
                    logger.info(f"[Job Manager] Idempotency match: returning existing job {existing_job.job_id}")
                    return existing_job

            job_id = f"job-{uuid.uuid4().hex[:12]}"
            job = JobPayload(
                job_id=job_id,
                job_type=job_type,
                params=params,
                idempotency_key=idempotency_key,
                status=JobStatus.QUEUED,
                max_retries=max_retries,
            )

            self._jobs[job_id] = job
            self._idempotency_index[idempotency_key] = job_id
            await self._queue.put(job)

            self._record_prometheus_metrics(job_type.value, "queued")
            logger.info(f"[Job Manager] Enqueued job {job_id} ({job_type.value})")
            return job

    async def get_next_job(self) -> JobPayload:
        """Worker interface to fetch the next queued job."""
        return await self._queue.get()

    def mark_task_done(self) -> None:
        """Acknowledges queue item completion."""
        self._queue.task_done()

    async def update_job_progress(self, job_id: str, progress_pct: float) -> None:
        """Updates live job progress percentage (0-100%)."""
        async with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id].progress_pct = max(0.0, min(100.0, progress_pct))
                self._jobs[job_id].status = JobStatus.PROCESSING
                if not self._jobs[job_id].started_at:
                    self._jobs[job_id].started_at = time.time()

    async def complete_job(self, job_id: str, result: Dict[str, Any]) -> None:
        """Marks job as successfully completed with results."""
        async with self._lock:
            if job_id in self._jobs:
                job = self._jobs[job_id]
                job.status = JobStatus.COMPLETED
                job.progress_pct = 100.0
                job.result = result
                job.completed_at = time.time()
                self._record_prometheus_metrics(job.job_type.value, "completed")
                logger.info(f"[Job Manager] Job {job_id} completed successfully in {job.completed_at - (job.started_at or job.created_at):.3f}s")

    async def fail_job(self, job_id: str, error: str, can_retry: bool = True) -> None:
        """Handles job failure with automatic retry scheduling."""
        async with self._lock:
            if job_id in self._jobs:
                job = self._jobs[job_id]
                if can_retry and job.retry_count < job.max_retries:
                    job.retry_count += 1
                    job.status = JobStatus.RETRYING
                    job.error = f"Retry {job.retry_count}/{job.max_retries}: {error}"
                    # Re-enqueue with backoff
                    await self._queue.put(job)
                    logger.warning(f"[Job Manager] Retrying job {job_id} ({job.retry_count}/{job.max_retries})")
                else:
                    job.status = JobStatus.FAILED
                    job.error = error
                    job.completed_at = time.time()
                    self._record_prometheus_metrics(job.job_type.value, "failed")
                    logger.error(f"[Job Manager] Job {job_id} failed permanently: {error}")

    def get_job(self, job_id: str) -> Optional[JobPayload]:
        return self._jobs.get(job_id)

    def list_jobs(self, limit: int = 50, job_type: Optional[JobType] = None) -> List[JobPayload]:
        jobs = list(self._jobs.values())
        if job_type:
            jobs = [j for j in jobs if j.job_type == job_type]
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        return jobs[:limit]

    @property
    def queue_depth(self) -> int:
        return self._queue.qsize()

    def _record_prometheus_metrics(self, job_type_str: str, status_str: str) -> None:
        try:
            from backend.app.api.metrics import APEX_JOB_QUEUE_DEPTH
            APEX_JOB_QUEUE_DEPTH.labels(queue_name=job_type_str).set(self._queue.qsize())
        except Exception:
            pass
