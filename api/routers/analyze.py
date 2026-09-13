"""
analyze.py
POST /analyze — scrape product and run full analysis pipeline.
Steps: scrape → clean → fake filter → ABSA → aggregate → store → respond
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from api.schemas.request import AnalyzeRequest
from api.schemas.response import AnalyzeResponse
from api.services.fake_detector import FakeReviewDetector
from api.services.absa import ABSAInference
from api.services.aggregator import aggregate_product_aspects
from db.session import get_db
from scraper.amazon import scrape_product_reviews
from scraper.flipkart import scrape_flipkart_reviews

router = APIRouter(prefix="/analyze", tags=["Analysis"])


@router.post("/", response_model=AnalyzeResponse)
async def analyze_product(
    request: AnalyzeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    fake_detector: FakeReviewDetector = Depends(),
    absa: ABSAInference = Depends()
):
    """
    Analyze a product URL or single review text.

    Pipeline:
    1. If product_url: scrape reviews from e-commerce platform
    2. Clean all review texts
    3. Run fake review detection on all reviews
    4. Filter to genuine reviews only
    5. Run ABSA on genuine reviews
    6. Aggregate aspect scores
    7. Store everything in PostgreSQL
    8. Return AnalyzeResponse

    TODO:
      1. Detect platform from URL (amazon vs flipkart)
      2. Call appropriate scraper
      3. Call fake_detector.predict_batch() on all reviews
      4. Call fake_detector.filter_genuine() to get genuine reviews
      5. Call absa.analyze_batch() on genuine review texts
      6. Store product, reviews, fake_scores, aspect_sentiments to DB
      7. Call aggregate_product_aspects() to compute summary scores
      8. Build and return AnalyzeResponse
      9. Use background_tasks.add_task() for DB writes (non-blocking)

    Raise HTTPException(400) if URL is not from supported platform.
    Raise HTTPException(404) if no reviews found.
    Raise HTTPException(422) if neither product_url nor review_text provided.
    """
    pass