"""
analyze.py
POST /analyze — run the full ML pipeline on a product already in the database,
or analyze a single review text directly.

Architecture note:
  No live scraping. Reviews are pre-loaded from offline datasets
  (McAuley Amazon JSON + Flipkart CSV) via data_ingestion/loaders/.
  This endpoint queries the DB for existing reviews and runs
  fake detection + ABSA on them.

Two modes:
  1. product_name + platform → full pipeline on all DB reviews for that product
  2. review_text only        → single review analysis, no DB lookup
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import datetime
from api.schemas.request import AnalyzeRequest
from api.schemas.response import AnalyzeResponse, ReviewFilterSummary
from api.services.fake_detector import FakeReviewDetector
from api.services.absa import ABSAInference
from api.services.aggregator import aggregate_product_aspects
from db.session import get_db
from db.models import Product, Review, FakeScore, AspectSentiment

router = APIRouter(prefix="/analyze", tags=["Analysis"])


def get_fake_detector(request: Request) -> FakeReviewDetector:
    """Retrieve the FakeReviewDetector singleton from app.state."""
    return request.app.state.fake_detector


def get_absa(request: Request) -> ABSAInference:
    """Retrieve the ABSAInference singleton from app.state."""
    return request.app.state.absa


@router.post("/", response_model=AnalyzeResponse)
async def analyze_product(
    request: AnalyzeRequest,
    db: Session = Depends(get_db),
    fake_detector: FakeReviewDetector = Depends(get_fake_detector),
    absa: ABSAInference = Depends(get_absa)
):
    """
    Run fake detection + ABSA on a product's reviews from the database,
    or analyze a single review text directly.

    Mode 1 — product_name + platform (full pipeline):
    1. Look up product in DB by name + platform
    2. Fetch all its Review rows
    3. Run fake_detector.predict_batch() on all review texts
    4. Filter to genuine reviews only
    5. Run absa.analyze_batch() on genuine review texts
    6. Store FakeScore + AspectSentiment rows back to DB
    7. Aggregate aspect scores
    8. Return AnalyzeResponse

    Mode 2 — review_text only (single review):
    1. Run fake_detector.predict_single() on the text
    2. If genuine: run absa.analyze_review() on the text
    3. Return AnalyzeResponse with single-review results (no DB write)

    TODO:
      Mode 1:
        1. product = db.query(Product).filter(
               Product.name == request.product_name,
               Product.platform == request.platform
           ).first()
           Raise HTTPException(404) if not found —
           message: f"Product '{request.product_name}' not found on {request.platform}.
                      Run data_ingestion loaders first."

        2. reviews = db.query(Review).filter(
               Review.product_id == product.id
           ).all()
           Raise HTTPException(404) if no reviews —
           message: "No reviews found for this product in the database."

        3. review_texts = [r.review_text for r in reviews]
           fake_results = fake_detector.predict_batch(review_texts)

        4. genuine_reviews = fake_detector.filter_genuine(reviews, fake_results)
           Raise HTTPException(422) if len(genuine_reviews) == 0 —
           message: "All reviews for this product were flagged as fake."

        5. Store FakeScore rows:
           For each (review, result) in zip(reviews, fake_results):
             existing = db.query(FakeScore).filter(FakeScore.review_id == review.id).first()
             if not existing:
               db.add(FakeScore(review_id=review.id, is_fake=result.is_fake,
                                confidence=result.confidence,
                                model_version=result.model_version))
           db.commit()

        6. genuine_texts = [r.review_text for r in genuine_reviews]
           absa_results = absa.analyze_batch(genuine_texts)

        7. Store AspectSentiment rows:
           For each (review, result) in zip(genuine_reviews, absa_results):
             For each aspect_mention in result:
               db.add(AspectSentiment(review_id=review.id,
                                      aspect=aspect_mention.aspect,
                                      sentiment=aspect_mention.sentiment,
                                      confidence=aspect_mention.confidence,
                                      model_version="pyabsa-multilingual"))
           db.commit()

        8. aspect_rows = db.query(AspectSentiment).join(Review).filter(
               Review.product_id == product.id
           ).all()
           aspect_dicts = [{"aspect": a.aspect, "sentiment": a.sentiment,
                            "confidence": a.confidence,
                            "review_date": a.scored_at} for a in aspect_rows]
           aspect_scores = aggregate_product_aspects(aspect_dicts)

        9. Build ReviewFilterSummary and AnalyzeResponse, return

      Mode 2 (review_text only):
        1. fake_result = fake_detector.predict_single(request.review_text)
        2. If fake_result.is_fake: return minimal AnalyzeResponse flagging as fake
        3. absa_result = absa.analyze_review(request.review_text)
        4. aggregate and return — no DB writes for single-review mode
    """
    pass
