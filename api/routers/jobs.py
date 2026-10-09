"""
jobs.py
Async analysis jobs — the escape hatch for long CPU-bound runs.

  POST /jobs/analyze  → 202 {job_id} (runs in a worker thread)
  GET  /jobs/{job_id} → status + progress (+ result when done)
  DELETE /jobs/{job_id} → request cancellation (cooperative: the worker
                           checks between ABSA chunks and stops early)

The worker runs the SAME pipeline functions as the sync endpoint, with its
own DB session. One worker at a time on CPU-only hosts keeps latency
predictable; raise max_workers only with cores to spare.
"""

import json
import logging
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from api.schemas.request import AnalyzeRequest
from api.schemas.response import JobAccepted, JobStatus
from api.services.analysis_pipeline import (
    run_single_review,
    run_product_analysis,
    Cancelled,
    ProductNotFoundError,
    NoReviewsError,
    AllFakeError,
)
from db.session import SessionLocal, get_db
from db.models import AnalysisJob

logger = logging.getLogger("reviewlens.api.routers.jobs")

router = APIRouter(prefix="/jobs", tags=["Jobs"])

_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="rl-job")


def _to_status(job: AnalysisJob) -> JobStatus:
    return JobStatus(
        job_id=job.id,
        mode=job.mode,
        status=job.status,
        progress_total=job.progress_total,
        progress_done=job.progress_done,
        cancel_requested=job.cancel_requested,
        result=json.loads(job.result_json) if job.result_json else None,
        error=job.error,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


def _run_job(job_id: str, fake_detector, absa):
    """Worker body. Own session, own transaction discipline: any failure
    rolls back, then the job row records the outcome."""
    db = SessionLocal()
    try:
        job = db.get(AnalysisJob, job_id)
        if job is None:
            return
        job.status = "running"
        db.commit()

        def progress(done: int, total: int):
            job.progress_done = done
            job.progress_total = total
            db.commit()

        def cancelled() -> bool:
            return bool(db.query(AnalysisJob.cancel_requested).filter(
                AnalysisJob.id == job_id).scalar())

        if job.mode == "single":
            result = run_single_review(
                fake_detector, absa,
                job.review_text, job.rating or 4.0)
        else:
            result = run_product_analysis(
                db, fake_detector, absa,
                job.product_name, job.platform,
                progress_cb=progress, cancel_cb=cancelled)

        job.result_json = result.model_dump_json()
        job.status = "done"
        job.progress_done = job.progress_total
        db.commit()
    except Cancelled:
        db.rollback()
        job = db.get(AnalysisJob, job_id)
        if job is not None:
            job.status = "cancelled"
            db.commit()
    except (ProductNotFoundError, NoReviewsError, AllFakeError) as exc:
        db.rollback()
        job = db.get(AnalysisJob, job_id)
        if job is not None:
            job.status = "failed"
            job.error = str(exc)[:500]
            db.commit()
    except Exception as exc:  # noqa: BLE001 — a worker must never die silent
        logger.exception("job %s crashed", job_id)
        db.rollback()
        job = db.get(AnalysisJob, job_id)
        if job is not None:
            job.status = "failed"
            job.error = f"{type(exc).__name__}: {exc}"[:500]
            db.commit()
    finally:
        db.close()


def _get_job_or_404(db: Session, job_id: str) -> AnalysisJob:
    job = db.get(AnalysisJob, job_id)
    if job is None:
        raise HTTPException(404, f"Job {job_id} not found.")
    return job


@router.post("/analyze", response_model=JobAccepted, status_code=202)
async def submit_analyze_job(
    body: AnalyzeRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Queue an analysis run. Same contract as POST /analyze, async."""
    if body.review_text and not body.product_name:
        mode = "single"
    else:
        mode = "product"

    job = AnalysisJob(
        id=uuid.uuid4().hex,
        mode=mode,
        product_name=body.product_name,
        platform=body.platform,
        review_text=body.review_text,
        rating=body.rating,
        status="queued",
    )
    db.add(job)
    db.commit()

    _executor.submit(
        _run_job,
        job.id,
        request.app.state.fake_detector,
        request.app.state.absa,
    )
    return JobAccepted(job_id=job.id, status="queued")


@router.get("/{job_id}", response_model=JobStatus)
async def get_job(job_id: str, db: Session = Depends(get_db)):
    """Poll status, progress and (when done) the result."""
    return _to_status(_get_job_or_404(db, job_id))


@router.delete("/{job_id}", response_model=JobStatus)
async def cancel_job(job_id: str, db: Session = Depends(get_db)):
    """Request cancellation. Takes effect at the next batch boundary;
    an already-terminal job is returned unchanged."""
    job = _get_job_or_404(db, job_id)
    if job.status not in ("done", "failed", "cancelled"):
        job.cancel_requested = True
        db.commit()
        db.refresh(job)
    return _to_status(job)
