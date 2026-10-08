"""
request.py
Pydantic request schemas.
FastAPI validates all incoming requests against these automatically.
Invalid requests are rejected with 422 Unprocessable Entity.

Architecture note:
  ReviewLens uses offline datasets (McAuley Amazon + Flipkart CSV) loaded into
  PostgreSQL via data_ingestion/. There is no live scraping. The API queries the
  DB for pre-loaded reviews and runs the ML pipeline on them.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from enum import Enum


class Platform(str, Enum):
    """Supported platforms — must match the platform column in the products table."""
    amazon   = "amazon"
    flipkart = "flipkart"


class AnalyzeRequest(BaseModel):
    """
    Request body for POST /analyze

    Two modes:
      1. product_name + platform — run full pipeline on a product already in DB
      2. review_text only        — analyze a single review text directly (no DB lookup)

    Either product_name or review_text must be provided, not both.
    """
    product_name: Optional[str] = Field(
        None,
        min_length=2,
        max_length=500,
        description="Product name as stored in the database",
        examples=["OnePlus Nord CE 3 Lite 5G"]
    )
    platform: Optional[Platform] = Field(
        None,
        description="Platform the product is from — required when product_name is provided",
        examples=["amazon"]
    )
    review_text: Optional[str] = Field(
        None,
        min_length=20,
        max_length=5000,
        description="Single review text to analyze directly — skips DB lookup"
    )
    rating: Optional[float] = Field(
        None,
        ge=1.0,
        le=5.0,
        description="Star rating for single-review mode — feeds fake detection",
        examples=[5.0]
    )

    @validator("review_text", always=True)
    def check_one_input_provided(cls, v, values):
        if not v and not values.get("product_name"):
            raise ValueError("Either product_name or review_text must be provided")
        return v

    @validator("platform", always=True)
    def platform_required_with_name(cls, v, values):
        if values.get("product_name") and not v:
            raise ValueError("platform is required when product_name is provided")
        return v


class CompareRequest(BaseModel):
    """
    Request body for POST /compare
    Accepts 2–3 product IDs for side-by-side aspect comparison.
    Uses product IDs (integers from DB) — not URLs, since there is no scraper.
    """
    product_ids: List[int] = Field(
        ...,
        min_length=2,
        max_length=3,
        description="List of 2-3 product IDs from the database to compare"
    )

    @validator("product_ids")
    def ids_must_be_unique(cls, v):
        if len(set(v)) != len(v):
            raise ValueError("product_ids must be unique — cannot compare a product with itself")
        return v


class TrendsRequest(BaseModel):
    """
    Query parameters for GET /trends
    """
    product_id: int = Field(
        ...,
        description="Product ID from the database"
    )
    aspect: str = Field(
        ...,
        description="Aspect key to get trend for",
        examples=["battery"]
    )
    weeks: int = Field(
        default=8,
        ge=1,
        le=52,
        description="Number of weeks of review history to return"
    )


class SearchRequest(BaseModel):
    """
    Query parameters for GET /products/search
    Allows the frontend to search available products in the DB
    before submitting an AnalyzeRequest or CompareRequest.
    """
    query: str = Field(
        ...,
        min_length=2,
        description="Partial product name to search for",
        examples=["OnePlus"]
    )
    platform: Optional[Platform] = Field(
        None,
        description="Filter by platform — omit to search both"
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Max results to return"
    )
