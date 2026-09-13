"""
cleaner.py
Text preprocessing for scraped reviews.
Cleans HTML artifacts, normalises unicode, handles Hinglish text.
"""

import re
import unicodedata
from typing import Optional


def clean_review_text(raw_text: str) -> Optional[str]:
    """
    Clean a single review string.

    Steps:
    1. Strip leading/trailing whitespace
    2. Remove HTML tags if any slipped through the scraper
    3. Normalise unicode (NFC) — handles accented characters and emoji
    4. Replace multiple whitespace with single space
    5. Return None if resulting text is shorter than 10 characters
       (too short to be a meaningful review)

    Args:
        raw_text: raw review string from scraper

    Returns:
        Cleaned string, or None if text is too short to process

    TODO:
      1. raw_text.strip()
      2. re.sub(r'<[^>]+>', '', text) — remove HTML tags
      3. unicodedata.normalize('NFC', text)
      4. re.sub(r'\s+', ' ', text) — collapse whitespace
      5. return None if len(text) < 10 else text
    """
    pass


def extract_review_metadata(raw_review: dict) -> dict:
    """
    Extract and type-cast structured metadata from a raw scraped review dict.

    Args:
        raw_review: dict from scraper with keys:
                    text, rating, reviewer, date, verified

    Returns:
        Clean dict with:
        - review_text: str (cleaned)
        - rating: float (1.0-5.0, None if missing)
        - reviewer_name: str (truncated to 200 chars)
        - review_date: datetime or None
        - verified_purchase: bool
        - review_length: int (len of cleaned text)

    TODO:
      1. Call clean_review_text() on raw_review["text"]
      2. Cast rating to float, clamp between 1.0 and 5.0
      3. Parse date string to datetime object (handle multiple formats)
      4. Return structured dict
    """
    pass