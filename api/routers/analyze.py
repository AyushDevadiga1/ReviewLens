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
from typing import List
from api.schemas.request import AnalyzeRequest
from api.schemas.response import AnalyzeResponse, ReviewFilterSummary, AspectScore
from api.services.fake_detector import FakeReviewDetector
from api.services.absa import ABSAInference
from api.services.aggregator import aggregate_product_aspects
from db.session import get_db
from db.models import Product, Review, FakeScore, AspectSentiment
from ml.absa.aspects import ASPECTS

router = APIRouter(prefix="/analyze", tags=["Analysis"])


def get_fake_detector(request: Request) -> FakeReviewDetector:
    return request.app.state.fake_detector


def get_absa(request: Request) -> ABSAInference:
    return request.app.state.absa


def build_aspect_scores(aspect_scores: dict) -> List[AspectScore]:
    """
    Convert aggregator output dict to list of AspectScore response objects.
    Adds display_name from aspects.py config.
    """
    result = []
    for aspect_key, data in aspect_scores.items():
        display_name = ASPECTS.get(aspect_key, {}).get("display_name", aspect_key.title())
        result.append(AspectScore(
            aspect=aspect_key,
            display_name=display_name,
            mean_score=data["mean_score"],
            review_count=data["review_count"],
            positive_pct=data["positive_pct"],
            negative_pct=data["negative_pct"],
            neutral_pct=data["neutral_pct"],
            sentiment_label=data["sentiment_label"],
        ))
    return result


@router.post("/", response_model=AnalyzeResponse)
async def analyze_product(
    body: AnalyzeRequest,
    db: Session = Depends(get_db),
    fake_detector: FakeReviewDetector = Depends(get_fake_detector),
    absa: ABSAInference = Depends(get_absa)
):
    # ── Mode 2 — single review_text, no DB lookup ──────────────────────────────
    if body.review_text and not body.product_name:
        fake_result = fake_detector.predict_single(
            body.review_text, body.rating if body.rating is not None else 4.0
        )

        if fake_result.is_fake:
            return AnalyzeResponse(
                product_id=0,
                product_name="Single Review",
                platform="unknown",
                review_filter=ReviewFilterSummary(
                    total_reviews=1,
                    fake_count=1,
                    genuine_count=0,
                    fake_percentage=100.0
                ),
                aspects=[],
                analyzed_at=datetime.utcnow()
            )

        absa_result = absa.analyze_review(body.review_text)
        aspects = getattr(absa_result,"aspects",[]) or []
        aspect_dicts = [
            {"aspect": a.aspect, "sentiment": a.sentiment,
             "confidence": a.confidence, "review_date": datetime.utcnow()}
            for a in aspects
        ]
        aspect_scores = aggregate_product_aspects(aspect_dicts)

        return AnalyzeResponse(
            product_id=0,
            product_name="Single Review",
            platform="unknown",
            review_filter=ReviewFilterSummary(
                total_reviews=1,
                fake_count=0,
                genuine_count=1,
                fake_percentage=0.0
            ),
            aspects=build_aspect_scores(aspect_scores),
            analyzed_at=datetime.utcnow()
        )

    # ── Mode 1 — full product pipeline ────────────────────────────────────────
    product = db.query(Product).filter(
        Product.name == body.product_name,
        Product.platform == body.platform
    ).first()

    if not product:
        raise HTTPException(
            404,
            f"Product '{body.product_name}' not found on {body.platform}. "
            "Run data_ingestion loaders first."
        )

    reviews = db.query(Review).filter(Review.product_id == product.id).all()

    if not reviews:
        raise HTTPException(404, "No reviews found for this product in the database.")

    # ── Extract everything from ORM objects BEFORE any commit ──────────────────
    # After db.commit(), SQLAlchemy expires ORM objects. Accessing attributes
    # on expired objects triggers a lazy reload which fails if the session
    # transaction is in a broken state. Extract to plain Python first.
    review_ids   = [r.id for r in reviews]
    review_texts = [r.review_text for r in reviews]
    review_ratings = [r.rating or 4.0 for r in reviews]

    # ── Fake detection ─────────────────────────────────────────────────────────
    fake_results = fake_detector.predict_batch(review_texts, review_ratings)

    genuine_indices = [i for i, res in enumerate(fake_results) if not res.is_fake]
    genuine_count   = len(genuine_indices)
    fake_count      = len(reviews) - genuine_count

    if genuine_count == 0:
        raise HTTPException(422, "All reviews for this product were flagged as fake.")

    genuine_texts = [review_texts[i] for i in genuine_indices]
    genuine_ids   = [review_ids[i] for i in genuine_indices]

    # ── Store FakeScore rows ───────────────────────────────────────────────────
    for i, result in enumerate(fake_results):
        existing = db.query(FakeScore).filter(
            FakeScore.review_id == review_ids[i]
        ).first()
        if not existing:
            db.add(FakeScore(
                review_id=review_ids[i],
                is_fake=result.is_fake,
                confidence=result.confidence,
                model_version=result.model_version
            ))
    db.commit()

    # ── ABSA on genuine reviews ────────────────────────────────────────────────
    absa_results = absa.analyze_batch(genuine_texts)

    # ── Store AspectSentiment rows ─────────────────────────────────────────────
    # Dedup on (review_id, aspect, sentiment) — same pattern as FakeScore above.
    # Re-analyzing a product must not multiply aspect mentions in aggregation.
    for review_id, absa_result in zip(genuine_ids, absa_results):
        aspects = getattr(absa_result,"aspects",[]) or []
        for aspect_mention in aspects:
            existing_aspect = db.query(AspectSentiment).filter(
                AspectSentiment.review_id == review_id,
                AspectSentiment.aspect == aspect_mention.aspect,
                AspectSentiment.sentiment == aspect_mention.sentiment
            ).first()
            if not existing_aspect:
                db.add(AspectSentiment(
                    review_id=review_id,
                    aspect=aspect_mention.aspect,
                    sentiment=aspect_mention.sentiment,
                    confidence=aspect_mention.confidence,
                    model_version="pyabsa-multilingual"
                ))
    db.commit()

    # ── Aggregate aspect scores ────────────────────────────────────────────────
    aspect_rows = db.query(AspectSentiment).join(Review).filter(
        Review.product_id == product.id
    ).all()

    aspect_dicts = [
        {"aspect": a.aspect, "sentiment": a.sentiment,
         "confidence": a.confidence, "review_date": a.scored_at}
        for a in aspect_rows
    ]
    aspect_scores = aggregate_product_aspects(aspect_dicts)

    # ── Build and return response ──────────────────────────────────────────────
    return AnalyzeResponse(
        product_id=product.id,
        product_name=product.name,
        platform=product.platform,
        review_filter=ReviewFilterSummary(
            total_reviews=len(reviews),
            fake_count=fake_count,
            genuine_count=genuine_count,
            fake_percentage=round(fake_count / len(reviews) * 100, 2)
        ),
        aspects=build_aspect_scores(aspect_scores),
        analyzed_at=datetime.utcnow()
    )
