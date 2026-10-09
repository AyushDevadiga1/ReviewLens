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
from api.routers.analyze import build_aspect_scores

from db.session import get_db
from db.models import Product, Review, AspectSentiment
from ml.absa.aspects import ASPECTS

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
    comparisons = []

    product_scores = {}
    
    for product_id in request.product_ids:
        product = db.query(Product).filter(Product.id == product_id).first()
        
        if not product:
            raise HTTPException(404, f"Product ID {product_id} not found in database.")
        aspect_rows = db.query(AspectSentiment).join(Review).filter(
            Review.product_id == product_id
        ).all()

        if not aspect_rows:
            raise HTTPException(404, f"Product '{product.name}' has not been analyzed yet.")
        aspect_dicts = [{"aspect": a.aspect, "sentiment": a.sentiment,
                        "confidence": a.confidence,
                        "review_date": a.scored_at} for a in aspect_rows]
        
        scores = aggregate_product_aspects(aspect_dicts)
        
        comparisons.append(ProductComparison(
            product_id=product.id,
            product_name=product.name,
            platform=product.platform,
            aspects=build_aspect_scores(scores)
        ))

        product_scores[product.name] = scores

    winners_by_aspect = compute_winner_per_aspect(product_scores)
    
    winner_list = []
    for aspect, winning_product in winners_by_aspect.items():
        display_name = ASPECTS.get(aspect, {}).get("display_name", aspect.title())
        winning_score = product_scores[winning_product].get(aspect, {}).get("mean_score", 0.0)
        
        # compute margin — difference between winner and second best
        all_scores = [
            product_scores[p].get(aspect, {}).get("mean_score", 0.0)
            for p in product_scores if p != winning_product
        ]
        second_best = max(all_scores) if all_scores else 0.0
        
        winner_list.append(WinnerSummary(
            aspect=aspect,
            display_name=display_name,
            winner=winning_product,
            winning_score=round(winning_score, 2),
            margin=round(winning_score - second_best, 2)
        ))

    return CompareResponse(
            products=comparisons,
            winners=winner_list,
            compared_at=datetime.utcnow()
    )