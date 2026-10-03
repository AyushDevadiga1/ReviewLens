"""
response.py
Pydantic response schemas.
FastAPI serialises all responses using these automatically.
Also used for Swagger UI documentation at /docs.

Architecture note:
  No scraping — reviews come from pre-loaded DB datasets.
  Responses reference product_id (DB integer) not product_url.
"""

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class AspectScore(BaseModel):
    aspect: str                # internal key e.g. "battery"
    display_name: str          # human label e.g. "Battery Life"
    mean_score: float          # 0.0 to 10.0
    review_count: int          # number of reviews mentioning this aspect
    positive_pct: float        # 0.0 to 100.0
    negative_pct: float
    neutral_pct: float
    sentiment_label: str       # "positive", "negative", "neutral"


class ReviewFilterSummary(BaseModel):
    """
    Summary of fake review filtering applied to the product's DB reviews.
    Renamed from FakeFilterSummary — 'scraped' is no longer accurate
    since reviews come from pre-loaded datasets, not live scraping.
    """
    total_reviews: int         # total reviews in DB for this product
    fake_count: int
    genuine_count: int
    fake_percentage: float


class AnalyzeResponse(BaseModel):
    product_id: int            # DB primary key — use this for /compare and /trends
    product_name: str
    platform: str              # "amazon" or "flipkart"
    review_filter: ReviewFilterSummary
    aspects: List[AspectScore]
    analyzed_at: datetime


class ProductComparison(BaseModel):
    product_id: int
    product_name: str
    platform: str
    aspects: List[AspectScore]


class WinnerSummary(BaseModel):
    aspect: str
    display_name: str
    winner: str                # product_name of the winner
    winning_score: float
    margin: float              # winning_score minus second place score


class CompareResponse(BaseModel):
    products: List[ProductComparison]
    winners: List[WinnerSummary]
    compared_at: datetime


class WeeklyDataPoint(BaseModel):
    week: str                  # ISO week string e.g. "2026-W01"
    mean_score: float
    review_count: int


class TrendsResponse(BaseModel):
    product_id: int
    product_name: str
    aspect: str
    display_name: str
    trend: List[WeeklyDataPoint]
    overall_direction: str     # "improving", "declining", "stable"


class ProductSearchResult(BaseModel):
    """One result row from GET /products/search."""
    product_id: int
    product_name: str
    platform: str
    review_count: int          # how many reviews exist in DB for this product


class HealthResponse(BaseModel):
    status: str                # "healthy" or "degraded"
    fake_detector_version: str
    absa_model_version: str
    database_connected: bool
    uptime_seconds: float
    total_products_in_db: int  # quick sanity check that data was loaded
    total_reviews_in_db: int
