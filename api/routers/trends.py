"""
trends.py
GET /trends — weekly sentiment timeline for one aspect of one product.
Used by the Streamlit "Sentiment Trends" page.

Architecture note:
  Queries AspectSentiment rows from DB grouped by ISO week.
  Uses scored_at (when ABSA ran) as the time axis since McAuley reviews
  have review_date but Flipkart/Dataset-SA rows may have review_date = None.
  Falls back to review_date when available, scored_at otherwise.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from api.schemas.request import TrendsRequest
from api.schemas.response import TrendsResponse
from api.services.aggregator import compute_weekly_trend
from db.session import get_db
from db.models import Product, Review, AspectSentiment
from ml.absa.aspects import ASPECTS

router = APIRouter(prefix="/trends", tags=["Trends"])


@router.get("/", response_model=TrendsResponse)
async def get_trend(
    request: TrendsRequest = Depends(),
    db: Session = Depends(get_db)
):
    """
    Return weekly sentiment trend for one aspect of one product.

    TODO:
      1. product = db.query(Product).filter(Product.id == request.product_id).first()
         Raise HTTPException(404) if not found

      2. Validate aspect key:
         if request.aspect not in ASPECTS:
             raise HTTPException(400, f"Unknown aspect '{request.aspect}'.
                                  Valid aspects: {list(ASPECTS.keys())}")

      3. aspect_rows = db.query(AspectSentiment).join(Review).filter(
             Review.product_id == request.product_id,
             AspectSentiment.aspect == request.aspect
         ).all()
         Raise HTTPException(404) if no rows —
         f"No '{request.aspect}' sentiment data found for '{product.name}'.
           Run POST /analyze first."

      4. Build aspect_dicts using the best available date:
         For each row: use review.review_date if not None, else row.scored_at
         aspect_dicts = [{"aspect": a.aspect, "sentiment": a.sentiment,
                          "confidence": a.confidence,
                          "review_date": date} for a, date in ...]

      5. trend = compute_weekly_trend(aspect_dicts, request.aspect, request.weeks)
         Raise HTTPException(404) if trend is empty

      6. Compute overall_direction:
         first_score = trend[0]["mean_score"]
         last_score  = trend[-1]["mean_score"]
         if last_score - first_score > 0.5:   overall_direction = "improving"
         elif first_score - last_score > 0.5: overall_direction = "declining"
         else:                                 overall_direction = "stable"

      7. Return TrendsResponse(
             product_id=product.id,
             product_name=product.name,
             aspect=request.aspect,
             display_name=ASPECTS[request.aspect]["display_name"],
             trend=trend,
             overall_direction=overall_direction
         )
    """
    
    product = db.query(Product).filter(Product.id == request.product_id).first()
    if not product:
        raise HTTPException(404, f"Product with ID {request.product_id} not found.")

    if request.aspect not in ASPECTS:
        raise HTTPException(400, f"Unknown aspect '{request.aspect}'. Valid aspects: {list(ASPECTS.keys())}")

    aspect_rows = db.query(
        AspectSentiment,
        Review.review_date
    ).join(Review).filter(
        Review.product_id == request.product_id,
        AspectSentiment.aspect == request.aspect
    ).all()

    if not aspect_rows:
        raise HTTPException(404, f"No '{request.aspect}' sentiment data found for '{product.name}'. Run POST /analyze first.")

    aspect_dicts = []
    for sentiment_row, review_date in aspect_rows:
        use_date = review_date if review_date else sentiment_row.scored_at
        aspect_dicts.append({
            "aspect": sentiment_row.aspect,
            "sentiment": sentiment_row.sentiment,
            "confidence": sentiment_row.confidence,
            "review_date": use_date
        })

    trend = compute_weekly_trend(aspect_dicts, request.aspect, request.weeks)

    if not trend:
        raise HTTPException(404, "Could not compute trend. Check if there are enough reviews with dates.")

    first_score = trend[0]["mean_score"]
    last_score = trend[-1]["mean_score"]

    if last_score - first_score > 0.5:
        overall_direction = "improving"
    elif first_score - last_score > 0.5:
        overall_direction = "declining"
    else:
        overall_direction = "stable"

    return TrendsResponse(
        product_id=product.id,
        product_name=product.name,
        aspect=request.aspect,
        display_name=ASPECTS[request.aspect]["display_name"],
        trend=trend,
        overall_direction=overall_direction
    )
