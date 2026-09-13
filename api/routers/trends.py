"""
trends.py
GET /trends — weekly sentiment timeline for one aspect of one product.
Used by the Streamlit "Sentiment Trends" page.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from api.schemas.request import TrendsRequest
from api.schemas.response import TrendsResponse
from api.services.aggregator import compute_weekly_trend
from db.session import get_db
from db.models import Product, AspectSentiment

router = APIRouter(prefix="/trends", tags=["Trends"])


@router.get("/", response_model=TrendsResponse)
async def get_trend(
    request: TrendsRequest = Depends(),
    db: Session = Depends(get_db)
):
    """
    Return weekly sentiment trend for one aspect of one product.

    TODO:
      1. Look up product by request.product_id
         Raise HTTPException(404) if not found
      2. Fetch all AspectSentiment rows for product + aspect from DB
      3. Call compute_weekly_trend() for the last request.weeks weeks
      4. Determine overall_direction from first vs last weekly mean score:
         improving if rising, declining if falling, else stable
      5. Build and return TrendsResponse
    """
    pass