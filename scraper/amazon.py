"""
amazon.py
Amazon India review scraper.
Scrapes up to max_pages of reviews for a given product URL.

IMPORTANT: Add delays between requests (time.sleep(2-3 seconds))
to avoid rate limiting. Respect robots.txt.
"""

import time
import requests
from bs4 import BeautifulSoup
from typing import List, Optional
from cleaner import clean_review_text, extract_review_metadata


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-IN,en;q=0.9",
}


def get_product_name(soup: BeautifulSoup) -> str:
    """
    Extract product name from Amazon product page.
    TODO:
      Look for: soup.find("span", {"id": "productTitle"})
      Strip whitespace from .get_text()
      Return "Unknown Product" if not found
    """
    pass


def parse_review_page(soup: BeautifulSoup) -> List[dict]:
    """
    Parse all reviews from one page of Amazon reviews.

    Each review block on Amazon has:
    - data-hook="review" — the review container div
    - data-hook="review-body" — the review text
    - data-hook="review-star-rating" — star rating
    - data-hook="review-date" — date string
    - data-hook="avp-badge" — verified purchase badge

    Returns:
        List of raw review dicts (not yet cleaned)

    TODO:
      1. Find all divs with data-hook="review"
      2. For each: extract text, rating, date, verified status
      3. Return list of raw dicts
    """
    pass


def scrape_product_reviews(
    product_url: str,
    max_pages: int = 5
) -> dict:
    """
    Scrape up to max_pages of reviews for a product URL.

    Args:
        product_url: Amazon India product URL
        max_pages: maximum number of review pages to scrape

    Returns:
        dict with:
        - product_name: str
        - platform: "amazon"
        - url: product_url
        - reviews: list of cleaned review dicts

    TODO:
      1. Extract ASIN from URL using regex: r'/dp/([A-Z0-9]{10})'
      2. Build review pages URL:
         f"https://www.amazon.in/product-reviews/{asin}/?pageNumber={page}"
      3. For each page 1..max_pages:
         a. GET request with HEADERS
         b. Parse with BeautifulSoup
         c. Call parse_review_page()
         d. Call extract_review_metadata() on each raw review
         e. time.sleep(2) between pages — avoid rate limiting
      4. Return structured dict
    """
    pass