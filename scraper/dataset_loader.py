"""
dataset_loader.py
Loads the McAuley Lab Amazon Review dataset into PostgreSQL.

Dataset: Cell Phones & Accessories — 5-core (1,128,437 reviews)
Source : https://jmcauley.ucsd.edu/data/amazon_v2/categoryFilesSmall/
         Cell_Phones_and_Accessories_5.json.gz
Format : gzipped JSON-lines — one review object per line

Column mapping (McAuley → ReviewLens schema):
  asin            → products.url  (used as unique product identifier)
  reviewText      → reviews.review_text
  overall         → reviews.rating
  reviewerName    → reviews.reviewer_name
  reviewTime      → reviews.review_date
  verified        → reviews.verified_purchase
  (computed)      → reviews.review_length

Usage:
  python -m scraper.dataset_loader --file data/Cell_Phones_and_Accessories_5.json.gz
  python -m scraper.dataset_loader --file data/Cell_Phones_and_Accessories_5.json.gz --limit 50000
"""

import gzip
import json
import argparse
from datetime import datetime
from typing import Iterator
from scraper.cleaner import clean_review_text


def parse_mcauley_file(filepath: str) -> Iterator[dict]:
    """
    Stream reviews from a McAuley .json.gz file one at a time.
    Uses a generator so the full file is never loaded into memory.

    Args:
        filepath: path to the .json.gz file

    Yields:
        Raw review dicts with McAuley column names

    TODO:
      1. gzip.open(filepath, 'rb')
      2. For each line: json.loads(line)
      3. yield the parsed dict
      4. Skip lines that raise json.JSONDecodeError (malformed rows exist)
    """
    pass


def mcauley_to_reviewlens(raw: dict) -> dict:
    """
    Map one McAuley review dict to ReviewLens schema shape.

    Args:
        raw: one parsed JSON line from the McAuley dataset

    Returns:
        Dict matching ReviewLens Review model columns, or None if review_text
        is empty after cleaning

    Column mapping:
      raw["asin"]         → product_identifier (used to group reviews by product)
      raw["reviewText"]   → review_text (run through clean_review_text)
      raw["overall"]      → rating (float, 1.0–5.0)
      raw["reviewerName"] → reviewer_name
      raw["reviewTime"]   → review_date (parse "MM DD, YYYY" format)
      raw["verified"]     → verified_purchase (bool)
      raw["summary"]      → stored in review_text prefix if reviewText missing

    TODO:
      1. Clean review text — return None if clean_review_text returns None
      2. Parse reviewTime string to datetime:
         datetime.strptime(raw.get("reviewTime", ""), "%m %d, %Y")
      3. Return mapped dict — None if no usable text
    """
    pass


def load_dataset(filepath: str, limit: int = None) -> None:
    """
    Full pipeline: read file → map columns → write to PostgreSQL.

    Args:
        filepath: path to the .json.gz dataset file
        limit   : max number of reviews to load (None = load all)
                  Use limit=50000 for dev/demo, None for full training data

    TODO:
      1. Import get_db, Product, Review from db layer
      2. Group reviews by asin — one Product row per unique asin
      3. Batch insert in chunks of 1000 rows (avoid memory issues)
      4. Print progress every 10,000 rows
      5. Log final count: X products, Y reviews loaded
    """
    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load McAuley dataset into ReviewLens DB")
    parser.add_argument("--file", required=True, help="Path to .json.gz dataset file")
    parser.add_argument("--limit", type=int, default=None, help="Max reviews to load")
    args = parser.parse_args()
    load_dataset(args.file, args.limit)
