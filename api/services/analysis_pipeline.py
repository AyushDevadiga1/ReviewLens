"""
analysis_pipeline.py
The analyze pipeline as plain functions — shared by the sync endpoint
(api/routers/analyze.py) and the async worker (api/routers/jobs.py).

Sync and async run THE SAME code; only the transport differs. The router
translates domain errors to HTTP codes; the worker translates them to
failed-job rows. Cancel/progress hooks are no-ops when not provided.
"""

from datetime import datetime
from typing import Callable, List, Optional

from sqlalchemy.orm import Session

from api.schemas.response import (
    AnalyzeResponse, ReviewFilterSummary, AspectScore,
)
from api.services.aggregator import aggregate_product_aspects
from db.models import Product, Review, FakeScore, AspectSentiment
from ml.absa.aspects import ASPECTS


class Cancelled(Exception):
    """Raised when a cooperative cancel is requested mid-pipeline."""


class ProductNotFoundError(Exception):
    pass


class NoReviewsError(Exception):
    pass


class AllFakeError(Exception):
    pass


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


def run_single_review(fake_detector, absa, review_text: str, rating: float) -> AnalyzeResponse:
    """Mode 2 — one review, no DB. Fast; cancel hooks not needed."""
    fake_result = fake_detector.predict_single(review_text, rating)

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

    absa_result = absa.analyze_review(review_text)
    aspects = getattr(absa_result, "aspects", []) or []
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


def run_product_analysis(
    db: Session,
    fake_detector,
    absa,
    product_name: str,
    platform: str,
    progress_cb: Optional[Callable[[int, int], None]] = None,
    cancel_cb: Optional[Callable[[], bool]] = None,
    absa_batch_size: int = 10,
) -> AnalyzeResponse:
    """Mode 1 — full pipeline. Cancel is checked between ABSA chunks
    (each chunk is one uninterruptible model call); progress counts
    reviews through ABSA."""
    cancelled = cancel_cb or (lambda: False)

    def progress(done: int, total: int):
        if progress_cb:
            progress_cb(done, total)

    product = db.query(Product).filter(
        Product.name == product_name,
        Product.platform == platform
    ).first()

    if not product:
        raise ProductNotFoundError(
            f"Product '{product_name}' not found on {platform}. "
            "Run data_ingestion loaders first."
        )

    reviews = db.query(Review).filter(Review.product_id == product.id).all()

    if not reviews:
        raise NoReviewsError("No reviews found for this product in the database.")

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
        raise AllFakeError("All reviews for this product were flagged as fake.")

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

    if cancelled():
        raise Cancelled()

    # ── ABSA on genuine reviews, in chunks so cancel stays responsive ─────────
    progress(0, len(reviews))
    absa_results = []
    for start in range(0, len(genuine_texts), absa_batch_size):
        if cancelled():
            raise Cancelled()
        chunk = genuine_texts[start:start + absa_batch_size]
        absa_results.extend(absa.analyze_batch(chunk))
        progress(min(start + len(chunk), len(reviews)), len(reviews))

    # ── Store AspectSentiment rows ─────────────────────────────────────────────
    # Dedup on (review_id, aspect, sentiment) — same pattern as FakeScore above.
    # Re-analyzing a product must not multiply aspect mentions in aggregation.
    for review_id, absa_result in zip(genuine_ids, absa_results):
        aspects = getattr(absa_result, "aspects", []) or []
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
