"""
products.py
GET /products/search — search available products in the database.
Lets the Streamlit frontend discover what products exist before
submitting an AnalyzeRequest or CompareRequest.

Architecture note:
  Since there is no live scraping, users can't just paste a URL.
  They need to know what product names exist in the DB.
  This endpoint provides that discovery layer.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from api.schemas.request import SearchRequest
from api.schemas.response import ProductSearchResult, AnalyzeResponse
from api.services.analysis_pipeline import build_partial_response
from db.session import get_db
from db.models import Product, Review, AspectSentiment, FakeScore
from sqlalchemy import func, or_

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("/search", response_model=List[ProductSearchResult])
async def search_products(
    request: SearchRequest = Depends(),
    db: Session = Depends(get_db)
):
    query = db.query(
        Product.id,
        Product.name,
        Product.platform,
        func.count(func.distinct(Review.id)).label("review_count"),
        func.count(func.distinct(AspectSentiment.id)).label("aspect_count")
    ).outerjoin(Review, Review.product_id == Product.id)\
     .outerjoin(AspectSentiment, AspectSentiment.review_id == Review.id)\
     .filter(or_(
         Product.name.ilike(f"%{request.query}%"),
         Product.platform.ilike(f"%{request.query}%"),
     ))\
     .group_by(Product.id, Product.name, Product.platform)
    
    if request.platform:
        query = query.filter(Product.platform == request.platform)

    results = query.limit(request.limit).all()
    
    if not results:
        raise HTTPException(404, f"No products matching '{request.query}' found in database.")
    
    return [ProductSearchResult(product_id=r.id, product_name=r.name,
                                 platform=r.platform,
                                 review_count=r.review_count,
                                 aspect_count=r.aspect_count)
            for r in results]


@router.get("/", response_model=List[ProductSearchResult])
async def list_products(
    platform: str = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(
        Product.id,
        Product.name,
        Product.platform,
        func.count(func.distinct(Review.id)).label("review_count"),
        func.count(func.distinct(AspectSentiment.id)).label("aspect_count")
    ).outerjoin(Review, Review.product_id == Product.id)\
     .outerjoin(AspectSentiment, AspectSentiment.review_id == Review.id)\
     .group_by(Product.id, Product.name, Product.platform)
    
    if platform:
        query = query.filter(Product.platform == platform)
    
    results = query.order_by(func.count(func.distinct(Review.id)).desc()).limit(limit).all()
    
    return [
        ProductSearchResult(
            product_id=r.id, 
            product_name=r.name,
            platform=r.platform,
            review_count=r.review_count,
            aspect_count=r.aspect_count
        )
        for r in results
    ]


@router.get("/{product_id}/analysis", response_model=AnalyzeResponse)
def get_product_analysis(
    product_id: int,
    db: Session = Depends(get_db)
):
    """Return pre-computed aspect sentiment and review filter metrics instantly from DB."""
    result = build_partial_response(db, product_id)
    if result is None:
        raise HTTPException(404, f"Product ID {product_id} not found in database.")
    return result


@router.get("/{product_id}/reviews")
def get_product_reviews(
    product_id: int,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Return sample reviews with their fake detector verdicts."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(404, f"Product ID {product_id} not found.")
    reviews = db.query(Review).filter(Review.product_id == product_id).limit(limit).all()
    out = []
    for r in reviews:
        fake_score = db.query(FakeScore).filter(FakeScore.review_id == r.id).first()
        out.append({
            "id": r.id,
            "text": r.review_text,
            "rating": r.rating,
            "date": r.review_date.isoformat() if r.review_date else None,
            "reviewer": r.reviewer_name,
            "is_fake": fake_score.is_fake if fake_score else False,
            "confidence": round(fake_score.confidence, 4) if fake_score else None,
        })
    return out
