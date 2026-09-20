"""
cleaner.py
Text preprocessing shared by all dataset loaders.
Both the Amazon JSON and Flipkart CSV pass review text through here
before anything is written to the database.
"""

import re
import unicodedata
from typing import Optional


def clean_review_text(raw_text: str) -> Optional[str]:
    """
    Clean a single review string.

    Steps:
    1. Strip leading/trailing whitespace
    2. Remove HTML tags if any slipped through
    3. Normalise unicode (NFC) — handles accented chars, emoji, Hinglish
    4. Replace multiple whitespace with single space
    5. Return None if resulting text is shorter than 10 characters

    Args:
        raw_text: raw review string from any source

    Returns:
        Cleaned string, or None if text is too short to be meaningful

    TODO:
      1. raw_text.strip()
      2. re.sub(r'<[^>]+>', '', text)       — strip HTML tags
      3. unicodedata.normalize('NFC', text)  — normalise unicode
      4. re.sub(r'\s+', ' ', text).strip()  — collapse whitespace
      5. return None if len(text) < 10 else text
    """
    pass


def extract_review_metadata(raw_review: dict) -> dict:
    """
    Extract and type-cast structured metadata from a raw review dict.
    Used by both loaders after they normalise column names to a common shape.

    Args:
        raw_review: dict with keys: text, rating, reviewer, date, verified

    Returns:
        Clean dict with:
        - review_text       : str (cleaned) or None
        - rating            : float (1.0–5.0), None if missing
        - reviewer_name     : str (truncated to 200 chars)
        - review_date       : datetime or None
        - verified_purchase : bool
        - review_length     : int (character count of cleaned text)

    TODO:
      1. Call clean_review_text() on raw_review["text"]
      2. Cast rating to float, clamp between 1.0 and 5.0
      3. Parse date string → datetime (handle multiple format strings)
      4. Return structured dict
    """
    pass
