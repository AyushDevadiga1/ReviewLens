"""
amazon_loader.py
Loads the McAuley Lab "Amazon Review Data (2018)" — Cell Phones & Accessories
5-core subset into PostgreSQL.

Dataset  : Cell Phones & Accessories 5-core (1,128,437 reviews)
Download : https://jmcauley.ucsd.edu/data/amazon_v2/categoryFilesSmall/
           Cell_Phones_and_Accessories_5.json.gz
Format   : Gzipped JSON-lines (.json.gz) — one review object per line
Place at : data/Cell_Phones_and_Accessories_5.json.gz  (gitignored)

McAuley column → ReviewLens schema mapping:
  asin          → used as product identifier to group reviews
  reviewText    → reviews.review_text  (cleaned via cleaner.py)
  overall       → reviews.rating       (float 1.0–5.0)
  reviewerName  → reviews.reviewer_name
  reviewTime    → reviews.review_date  (string "MM DD, YYYY" → datetime)
  verified      → reviews.verified_purchase (bool)
  summary       → fallback if reviewText is empty

Usage:
  # Load 50k reviews for dev/demo (~2 min):
  python -m data_ingestion.loaders.amazon_loader --file data/Cell_Phones_and_Accessories_5.json.gz --limit 50000

  # Load all 1.1M for training (~20 min):
  python -m data_ingestion.loaders.amazon_loader --file data/Cell_Phones_and_Accessories_5.json.gz
"""

import gzip
import json
import argparse
from datetime import datetime
from typing import Iterator, Optional
from data_ingestion.cleaner import clean_review_text, extract_review_metadata


# ── Parsing ────────────────────────────────────────────────────────────────────

def stream_mcauley_file(filepath: str) -> Iterator[dict]:
    """
    Stream reviews from the McAuley .json.gz file one at a time.
    Generator — never loads the full 300MB file into memory.

    Args:
        filepath: path to the .json.gz file on disk

    Yields:
        Raw review dicts with McAuley column names

    TODO:
      1. Open with gzip.open(filepath, 'rb')
      2. Iterate lines: for line in f
      3. json.loads(line) — yield the result
      4. Wrap in try/except json.JSONDecodeError and skip bad lines
         (the dataset has ~0.1% malformed rows)
    """
    pass


def mcauley_to_reviewlens(raw: dict) -> Optional[dict]:
    """
    Map one raw McAuley review dict to the ReviewLens common schema.

    Args:
        raw: one parsed JSON line from the McAuley dataset

    Returns:
        Dict with ReviewLens-shaped keys, or None if no usable review text

    TODO:
      1. text = raw.get("reviewText") or raw.get("summary", "")
         — fall back to summary if reviewText is absent
      2. Build a normalised input dict for extract_review_metadata:
         {"text": text, "rating": raw.get("overall"),
          "reviewer": raw.get("reviewerName", ""),
          "date": raw.get("reviewTime", ""), "verified": raw.get("verified", False)}
      3. Call extract_review_metadata() — return None if result["review_text"] is None
      4. Add "product_identifier": raw.get("asin") to the result dict
         (used by load_amazon to group reviews under a Product row)
      5. Return the final dict
    """
    pass


# ── DB writing ─────────────────────────────────────────────────────────────────

def load_amazon(filepath: str, limit: int = None) -> None:
    """
    Full pipeline: stream file → map columns → batch-write to PostgreSQL.

    Args:
        filepath: path to the .json.gz dataset file
        limit   : max reviews to load (None = all 1.1M)
                  50_000 is a good starting point for dev/demo

    TODO:
      1. Import get_session_factory, Product, Review from db layer
      2. Open a DB session
      3. For each raw review from stream_mcauley_file():
         a. Call mcauley_to_reviewlens() — skip if None
         b. get-or-create a Product row for the asin
            (check by url=asin, platform="amazon")
         c. Build a Review ORM object, set product_id
         d. session.add(review)
         e. Every 1000 rows: session.commit() + print progress
      4. Final session.commit()
      5. Print summary: "Loaded X reviews across Y products"

    Notes:
      - Use a dict {asin: product_id} as an in-memory cache so you don't
        query the DB for every review — there are only ~27k unique products
        but 1.1M reviews, so the query overhead would be massive without it
      - The limit applies to the number of reviews mapped, not lines read
        (some lines are skipped due to missing text)
    """
    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load McAuley Amazon dataset → PostgreSQL")
    parser.add_argument("--file", required=True, help="Path to .json.gz file")
    parser.add_argument("--limit", type=int, default=None, help="Max reviews to load")
    args = parser.parse_args()
    load_amazon(args.file, args.limit)
