"""
compare.py
POST /compare — compare 2–3 products side by side on aspect sentiment scores.
Returns per-product aspect scores and a winner per aspect.

Architecture note:
  Accepts product_ids (integers from DB), not URLs.
  No scraping — products must already be in the database and analyzed.
  If a product has not been analyzed yet, the endpoint returns 404
  with a clear message directing the user to POST /analyze first.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
from api.schemas.request import CompareRequest
from api.schemas.response import CompareResponse, ProductComparison, WinnerSummary
from api.services.aggregator import aggregate_product_aspects, compute_winner_per_aspect
from db.session import get_db
from db.models import Product, Review, AspectSentiment

router = APIRouter(prefix="/compare", tags=["Comparison"])


@router.post("/", response_model=CompareResponse)
async def compare_products(
    request: CompareRequest,
    db: Session = Depends(get_db)
):
    """
    Compare 2–3 products on aspect sentiment scores.
    Products must already exist in DB and have been through POST /analyze.

    TODO:
      1. For each product_id in request.product_ids:
         a. product = db.query(Product).filter(Product.id == product_id).first()
            Raise HTTPException(404) if not found:
            f"Product ID {product_id} not found in database."

         b. aspect_rows = db.query(AspectSentiment).join(Review).filter(
                Review.product_id == product_id
            ).all()
            Raise HTTPException(404) if no aspect rows:
            f"Product '{product.name}' has not been analyzed yet.
              POST /analyze with product_name='{product.name}'
              and platform='{product.platform}' first."

         c. aspect_dicts = [{"aspect": a.aspect, "sentiment": a.sentiment,
                              "confidence": a.confidence,
                              "review_date": a.scored_at} for a in aspect_rows]
            scores = aggregate_product_aspects(aspect_dicts)

         d. Build ProductComparison object, append to list

      2. Build product_scores dict for compute_winner_per_aspect():
         {product.name: scores_dict}

      3. winners_by_aspect = compute_winner_per_aspect(product_scores)
         Build list of WinnerSummary objects

      4. Return CompareResponse(
             products=comparisons,
             winners=winner_list,
             compared_at=datetime.utcnow()
         )
    """
    pass
