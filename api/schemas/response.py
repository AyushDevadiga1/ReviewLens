"""
response.py
Pydantic response schemas.
FastAPI serialises all responses using these automatically.
Also used for Swagger UI documentation.
"""

from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime


class AspectScore(BaseModel):
    aspect: str
    display_name: str
    mean_score: float          # 0.0 to 10.0
    review_count: int
    positive_pct: float        # 0.0 to 100.0
    negative_pct: float
    neutral_pct: float
    sentiment_label: str       # "positive", "negative", "neutral"


class FakeFilterSummary(BaseModel):
    total_scraped: int
    fake_count: int
    genuine_count: int
    fake_percentage: float


class AnalyzeResponse(BaseModel):
    product_name: str
    product_url: str
    platform: str
    fake_filter: FakeFilterSummary
    aspects: List[AspectScore]
    analyzed_at: datetime


class ProductComparison(BaseModel):
    product_name: str
    product_url: str
    aspects: List[AspectScore]


class WinnerSummary(BaseModel):
    aspect: str
    display_name: str
    winner: str
    winning_score: float


class CompareResponse(BaseModel):
    products: List[ProductComparison]
    winners: List[WinnerSummary]      # which product wins per aspect
    compared_at: datetime


class WeeklyDataPoint(BaseModel):
    week: str                  # ISO format e.g. "2026-W01"
    mean_score: float
    review_count: int


class TrendsResponse(BaseModel):
    product_name: str
    aspect: str
    display_name: str
    trend: List[WeeklyDataPoint]
    overall_direction: str     # "improving", "declining", "stable"


class HealthResponse(BaseModel):
    status: str                # "healthy" or "degraded"
    fake_detector_version: str
    absa_model_version: str
    database_connected: bool
    uptime_seconds: float