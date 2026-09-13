"""
flipkart.py
Flipkart review scraper.
Scrapes up to max_pages of reviews for a given product URL.

IMPORTANT: Add delays between requests (time.sleep(2-3 seconds))
to avoid rate limiting. Respect robots.txt.
"""

import time
import requests
from bs4 import BeautifulSoup
from typing import List
from cleaner import clean_review_text, extract_review_metadata


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-IN,en;q=0.9",
}


def parse_review_page(soup: BeautifulSoup) -> List[dict]:
    """
    Parse all reviews from one page of Flipkart reviews.

    Each review block on Flipkart has:
    - div with class "_1AtVbE" — the review container
    - div with class "t-ZTKy" — the review text
    - div with class "_3LWZlK" — star rating
    - div with class "col-7-12" — reviewer name and date

    Returns:
        List of raw review dicts (not yet cleaned)

    TODO:
      1. Find all review containers by their class
      2. For each: extract text, rating, reviewer name, date
      3. Return list of raw dicts
    """
    pass


def scrape_flipkart_reviews(
    product_url: str,
    max_pages: int = 5
) -> dict:
    """
    Scrape up to max_pages of reviews for a Flipkart product URL.

    Args:
        product_url: Flipkart product URL
        max_pages: maximum number of review pages to scrape

    Returns:
        dict with:
        - product_name: str
        - platform: "flipkart"
        - url: product_url
        - reviews: list of cleaned review dicts

    TODO:
      1. Extract product ID from URL (pid / pothis token)
      2. Build review pages URL from the "Read all reviews" link
      3. For each page 1..max_pages:
         a. GET request with HEADERS
         b. Parse with BeautifulSoup
         c. Call parse_review_page()
         d. Call extract_review_metadata() on each raw review
         e. time.sleep(2) between pages — avoid rate limiting
      4. Return structured dict
    """
    pass