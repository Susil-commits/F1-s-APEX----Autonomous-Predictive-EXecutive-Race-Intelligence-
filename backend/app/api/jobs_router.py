"""API Router for Asynchronous Strategy and Compute Background Jobs."""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from backend.app.api.auth import get_current_user, require_role
from backend.app.core.security import Role, TokenUser
from backend.app.jobs.job_manager import ApexJobManager, JobPayload, JobStatus, JobType

jobs_router = APIRouter(prefix="/api/jobs", tags=["Asynchronous Compute Jobs"])


class EnqueueJobRequest(BaseModel):
    job_type: JobType
    params: Dict[str, Any]
    max_retries: int = 3
    custom_idempotency_key: Optional[str] = None


@jobs_router.post("/enqueue", response_model=JobPayload, status_code=status.HTTP_202_ACCEPTED)
async def enqueue_job(
    req: EnqueueJobRequest,
    current_user: TokenUser = Depends(require_role(Role.ANALYST)),
):
    """Enqueues an asynchronous compute job with idempotency deduplication."""
    manager = ApexJobManager.get_instance()
    job = await manager.enqueue_job(
        job_type=req.job_type,
        params=req.params,
        max_retries=req.max_retries,
        custom_idempotency_key=req.custom_idempotency_key,
    )
    return job


@jobs_router.get("/status/{job_id}", response_model=JobPayload)
async def get_job_status(
    job_id: str,
    current_user: TokenUser = Depends(get_current_user),
):
    """Fetches real-time status, progress %, and results for a specific background job."""
    manager = ApexJobManager.get_instance()
    job = manager.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found.",
        )
    return job


@jobs_router.get("/list", response_model=List[JobPayload])
async def list_jobs(
    limit: int = Query(default=20, ge=1, le=100),
    job_type: Optional[JobType] = None,
    current_user: TokenUser = Depends(get_current_user),
):
    """Lists recent compute jobs with filtering."""
    manager = ApexJobManager.get_instance()
    return manager.list_jobs(limit=limit, job_type=job_type)
