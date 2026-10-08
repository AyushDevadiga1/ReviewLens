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
  overall       → reviews.rating       (float 1.0-5.0)
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
from db.session import get_session_factory
from db.models import Product, Review


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
  if filepath.endswith('.gz'):
    open_func = gzip.open(filepath, 'rb')
    
  else:
    open_func = open(filepath, 'rb')

    with open_func as f:
      for line in f:
        try:
          yield json.loads(line.decode("utf-8"))
        except json.JSONDecodeError:
          continue


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
    text = raw.get("reviewText") or raw.get("summary","")
  
    input_dict = {
      "text":text,
      "rating":raw.get("overall"),
      "reviewer":raw.get("reviewerName",""),
      "date":raw.get("reviewTime",""), # Fallback if the date does not exist in the passed dict
      "verified":raw.get("verified",False)
    }

    normalised_data = extract_review_metadata(input_dict)
    
    if not normalised_data["review_text"] or not normalised_data.get("review_text"):
      return None

    final_dict = dict(normalised_data)
    final_dict["product_identifier"] = raw.get("asin")
    return final_dict



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

    # 1. Base Variables Init
    db = get_session_factory()
    session = db()
    product_cache = {}  # Format: {asin: product_id}
    seen_reviews = {}  # Format: {asin: set((reviewer_name, review_text))} — skips rows on re-runs
    review_count = 0
    
    # 2. Master Safety Fence Opens
    try:
        for raw in stream_mcauley_file(filepath):
            if limit is not None and review_count >= limit:
                break

            mapping = mcauley_to_reviewlens(raw)
            if mapping is None:
                continue

            # Extract product identifier matching the dict keys from step 4
            asin = mapping.get("product_identifier")
            if not asin:
                continue

            # b. Get-or-create Product row using the in-memory cache
            if asin not in product_cache:
                product = (
                    session.query(Product)
                    .filter(Product.name == asin, Product.platform == "amazon")
                    .first()
                )
                
                # If it doesn't exist, build and persist it immediately to get an ID
                if not product:
                    product = Product(
                        name=asin,
                        platform="amazon"
                        # Set other Product fields from mapping if needed (e.g., title)
                    )
                    session.add(product)
                    session.flush()  # Generates product.id without committing the transaction
                
                # Cache the ID to skip DB lookups for future reviews of this item
                product_cache[asin] = product.id

                # Idempotency: snapshot (reviewer, text) pairs already stored for
                # this product (one query per product, not per review).
                # Re-running the loader — or duplicated rows in the source
                # file — can no longer multiply review rows and corrupt
                # aggregation. Keyed on reviewer+text so two users posting
                # the same words are still kept as separate reviews.
                seen_reviews[asin] = {
                    (r, t) for (r, t) in session.query(
                        Review.reviewer_name, Review.review_text).filter(
                        Review.product_id == product.id).all()
                }

            # c1. Skip reviews already in the DB from a previous load
            review_key = (mapping.get("reviewer_name"), mapping.get("review_text"))
            if review_key in seen_reviews[asin]:
                continue
            seen_reviews[asin].add(review_key)

            # c2. Build the Review ORM object
            review = Review(
                                product_id        = product_cache[asin],
                                reviewer_name     = mapping.get("reviewer_name"),    
                                review_text       = mapping.get("review_text"),      
                                review_date       = mapping.get("review_date"),
                                rating            = mapping.get("rating"),           
                                verified_purchase = mapping.get("verified_purchase"),
                                review_length     = mapping.get("review_length")     
                            )

            
            # d. Add review to session and increment count
            session.add(review)
            review_count += 1
            
            # e. Every 1,000 rows: batch commit changes to the DB
            if review_count % 1000 == 0:
                session.commit()
                print(f"[Amazon] Processed {review_count} reviews...")
                
        # 3. Final Catch-all Commit sits inside the try, right after the loop finishes
        session.commit()
        
    except Exception as e:
        session.rollback()
        print(f"[Amazon Error] Pipeline failed. Rolled back transaction. Error: {e}")
        raise e
    finally:
        session.close()
        
    # 4. Print Summary out here after successful execution and session closure
    print(f"Loaded {review_count} reviews across {len(product_cache)} products")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load McAuley Amazon dataset → PostgreSQL")
    parser.add_argument("--file", required=True, help="Path to .json.gz file")
    parser.add_argument("--limit", type=int, default=None, help="Max reviews to load")
    args = parser.parse_args()
    load_amazon(args.file, args.limit)
