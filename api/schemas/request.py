"""
request.py
Pydantic request schemas.
FastAPI validates all incoming requests against these automatically.
Invalid requests are rejected with 422 Unprocessable Entity.
"""

from pydantic import BaseModel, HttpUrl, validator, Field
from typing import Optional, List


class AnalyzeRequest(BaseModel):
    """
    Request body for POST /analyze
    Either product_url OR review_text must be provided, not both.
    """
    product_url: Optional[HttpUrl] = Field(
        None,
        description="Full URL of Amazon India or Flipkart product page",
        example="https://www.amazon.in/dp/B09G3J7G1P"
    )
    review_text: Optional[str] = Field(
        None,
        min_length=20,
        max_length=5000,
        description="Single review text to analyze directly"
    )
    max_pages: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Max review pages to scrape (only used with product_url)"
    )

    # TODO: add validator that ensures either product_url or review_text is provided
    # @validator('review_text', always=True)
    # def check_one_input_provided(cls, v, values):
    #     if not v and not values.get('product_url'):
    #         raise ValueError('Either product_url or review_text must be provided')
    #     return v


class CompareRequest(BaseModel):
    """
    Query parameters for GET /compare
    Accepts 2-3 product URLs for side-by-side comparison.
    """
    product_urls: List[HttpUrl] = Field(
        ...,
        min_items=2,
        max_items=3,
        description="List of 2-3 product URLs to compare"
    )

    # TODO: validator to ensure all URLs are from supported platforms
    # Supported: amazon.in, flipkart.com


class TrendsRequest(BaseModel):
    """
    Query parameters for GET /trends
    """
    product_id: int = Field(..., description="Product ID from database")
    aspect: str = Field(
        ...,
        description="Aspect to get trend for",
        example="battery"
    )
    weeks: int = Field(
        default=8,
        ge=1,
        le=52,
        description="Number of weeks of history to return"
    )