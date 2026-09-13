"""
compare.py
GET /compare — compare two or three products side by side.
Returns aspect scores for each product and winner per aspect.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from api.schemas.request import CompareRequest
from api.schemas.response import CompareResponse
from api.services.aggregator import compute_winner_per_aspect
from db.session import get_db
from db.models import Product, AspectSentiment

router = APIRouter(prefix="/compare", tags=["Comparison"])


@router.get("/", response_model=CompareResponse)
async def compare_products(
    request: CompareRequest = Depends(),
    db: Session = Depends(get_db)
):
    """
    Compare 2-3 products on aspect sentiment scores.

    TODO:
      1. For each URL in request.product_urls:
         a. Look up product in DB by URL
         b. If not found: trigger analysis (call analyze_product internally)
            or raise HTTPException(404, "Product not yet analyzed")
         c. Fetch all AspectSentiment records for this product from DB
         d. Call aggregate_product_aspects() to get scores
      2. Call compute_winner_per_aspect() across all products
      3. Build CompareResponse with per-product aspects and winner summary
      4. Return response
    """
    pass