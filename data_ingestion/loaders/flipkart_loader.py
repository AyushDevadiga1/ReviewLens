"""
flipkart_loader.py
Loads the Flipkart Products Review Dataset (363K reviews) into PostgreSQL.

Dataset  : Flipkart Products Review Dataset — 363K reviews
Download : https://www.kaggle.com/datasets/niraliivaghani/flipkart-dataset
Format   : CSV
Place at : data/flipkart_reviews.csv  (gitignored)

Flipkart CSV column → ReviewLens schema mapping:
  Product Name     → products.name + used as product identifier
  Review           → reviews.review_text  (cleaned via cleaner.py)
  Rate             → reviews.rating       (float 1.0–5.0)
  Summary          → fallback if Review column is empty
  (no date col)    → reviews.review_date = None
  (no verified col)→ reviews.verified_purchase = False

Usage:
  python -m data_ingestion.loaders.flipkart_loader --file data/flipkart_reviews.csv

  # Load a sample for dev/demo:
  python -m data_ingestion.loaders.flipkart_loader --file data/flipkart_reviews.csv --limit 30000
"""

import csv
import argparse
from typing import Optional
from data_ingestion.cleaner import clean_review_text, extract_review_metadata


# ── Parsing ────────────────────────────────────────────────────────────────────

def stream_flipkart_file(filepath: str):
    """
    Stream rows from the Flipkart CSV one at a time.
    Generator — avoids loading the full file into memory.

    Args:
        filepath: path to the CSV file

    Yields:
        Raw row dicts with Flipkart column names

    TODO:
      1. open(filepath, encoding='utf-8', errors='replace')
         — errors='replace' handles the occasional bad encoding in Flipkart data
      2. csv.DictReader(f) — yields one dict per row with header keys
      3. yield each row
    """
    pass


def flipkart_to_reviewlens(raw: dict) -> Optional[dict]:
    """
    Map one raw Flipkart CSV row to the ReviewLens common schema.

    Args:
        raw: one row dict from csv.DictReader

    Returns:
        Dict with ReviewLens-shaped keys, or None if no usable review text

    Flipkart CSV column names (verify against actual file header):
      "Product Name", "Review", "Rate", "Summary"

    TODO:
      1. text = raw.get("Review") or raw.get("Summary", "")
         — fall back to Summary if Review is empty
      2. Build normalised input for extract_review_metadata:
         {"text": text, "rating": raw.get("Rate"),
          "reviewer": "",        — Flipkart dataset has no reviewer name col
          "date": "",            — no date column
          "verified": False}     — no verified column
      3. Call extract_review_metadata() — return None if review_text is None
      4. Add "product_identifier": raw.get("Product Name", "").strip()
      5. Add "platform": "flipkart"
      6. Return the final dict
    """
    pass


# ── DB writing ─────────────────────────────────────────────────────────────────

def load_flipkart(filepath: str, limit: int = None) -> None:
    """
    Full pipeline: stream CSV → map columns → batch-write to PostgreSQL.

    Args:
        filepath: path to the Flipkart CSV file
        limit   : max reviews to load (None = all ~363K)
                  30_000 is a good starting point for dev/demo

    TODO:
      1. Import get_session_factory, Product, Review from db layer
      2. Open a DB session
      3. For each row from stream_flipkart_file():
         a. Call flipkart_to_reviewlens() — skip if None
         b. get-or-create a Product row using product_identifier as name
            (check by name=product_identifier, platform="flipkart")
         c. Build a Review ORM object, set product_id
         d. session.add(review)
         e. Every 1000 rows: session.commit() + print progress
      4. Final session.commit()
      5. Print summary: "Loaded X reviews across Y products"

    Notes:
      - Same in-memory product cache pattern as amazon_loader:
        dict {product_name: product_id} — avoids repeated DB lookups
      - Flipkart has far fewer unique products than Amazon (~1K vs ~27K),
        so the cache stays small
    """
    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load Flipkart review dataset → PostgreSQL")
    parser.add_argument("--file", required=True, help="Path to Flipkart CSV file")
    parser.add_argument("--limit", type=int, default=None, help="Max reviews to load")
    args = parser.parse_args()
    load_flipkart(args.file, args.limit)
