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
from api.schemas.response import ProductSearchResult
from db.session import get_db
from db.models import Product, Review
from sqlalchemy import func

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("/search", response_model=List[ProductSearchResult])
async def search_products(
    request: SearchRequest = Depends(),
    db: Session = Depends(get_db)
):
    """
    Search for products in the database by partial name match.
    Returns matching products with their review counts.

    TODO:
      1. Build query with partial match (case-insensitive):
         query = db.query(
             Product.id,
             Product.name,
             Product.platform,
             func.count(Review.id).label("review_count")
         ).outerjoin(Review, Review.product_id == Product.id)
          .filter(Product.name.ilike(f"%{request.query}%"))
          .group_by(Product.id, Product.name, Product.platform)

      2. If request.platform is provided:
         query = query.filter(Product.platform == request.platform)

      3. results = query.limit(request.limit).all()
         Raise HTTPException(404) if no results:
         f"No products matching '{request.query}' found in database."

      4. Return [ProductSearchResult(product_id=r.id, product_name=r.name,
                                     platform=r.platform,
                                     review_count=r.review_count)
                 for r in results]
    """
    pass


@router.get("/", response_model=List[ProductSearchResult])
async def list_products(
    platform: str = None,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    List all products in the database, optionally filtered by platform.
    Used by the Streamlit dropdown on the single-product page.

    TODO:
      1. query = db.query(Product.id, Product.name, Product.platform,
                          func.count(Review.id).label("review_count"))
                  .outerjoin(Review)
                  .group_by(Product.id)
      2. If platform: query = query.filter(Product.platform == platform)
      3. results = query.order_by(func.count(Review.id).desc()).limit(limit).all()
      4. Return list of ProductSearchResult
    """
    pass
