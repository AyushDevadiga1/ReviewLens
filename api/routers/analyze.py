"""
analyze.py
POST /analyze — run the full ML pipeline on a product already in the database,
or analyze a single review text directly.

Thin wrapper: the pipeline lives in api/services/analysis_pipeline.py so the
async worker runs the same code. This router only translates domain errors
to HTTP codes.

Two modes:
  1. product_name + platform → full pipeline on all DB reviews for that product
  2. review_text only        → single review analysis, no DB lookup
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from api.schemas.request import AnalyzeRequest
from api.schemas.response import AnalyzeResponse
from api.services.fake_detector import FakeReviewDetector
from api.services.absa import ABSAInference
from api.services.analysis_pipeline import (
    build_aspect_scores,  # noqa: F401 — re-exported for api.routers.compare
    run_single_review,
    run_product_analysis,
    ProductNotFoundError,
    NoReviewsError,
    AllFakeError,
)
from db.session import get_db

router = APIRouter(prefix="/analyze", tags=["Analysis"])


def get_fake_detector(request: Request) -> FakeReviewDetector:
    return request.app.state.fake_detector


def get_absa(request: Request) -> ABSAInference:
    return request.app.state.absa


@router.post("/", response_model=AnalyzeResponse)
async def analyze_product(
    body: AnalyzeRequest,
    db: Session = Depends(get_db),
    fake_detector: FakeReviewDetector = Depends(get_fake_detector),
    absa: ABSAInference = Depends(get_absa)
):
    # ── Mode 2 — single review_text, no DB lookup ──────────────────────────────
    if body.review_text and not body.product_name:
        return run_single_review(
            fake_detector,
            absa,
            body.review_text,
            body.rating if body.rating is not None else 4.0
        )

    # ── Mode 1 — full product pipeline ────────────────────────────────────────
    try:
        return run_product_analysis(
            db, fake_detector, absa, body.product_name, body.platform)
    except ProductNotFoundError as exc:
        raise HTTPException(404, str(exc))
    except NoReviewsError as exc:
        raise HTTPException(404, str(exc))
    except AllFakeError as exc:
        raise HTTPException(422, str(exc))
