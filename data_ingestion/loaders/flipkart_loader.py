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
from db.session import get_session_factory
from db.models import Product, Review

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

    with open(filepath, encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield row


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
    # 1. Fall back to Summary if Review is empty or absent
    text = raw.get("Review") or raw.get("Summary", "")

    # 2. Build normalised input for extract_review_metadata
    input_dict = {
        "text": text,
        "rating": raw.get("Rate"),
        "reviewer": "",        # Flipkart dataset has no reviewer name col
        "date": "",            # No date column
        "verified": False      # No verified column
    }

    # 3. Call extract_review_metadata()
    normalised_data = extract_review_metadata(input_dict)
    
    # Return None if review_text is None (or dropped by minimum char threshold)
    if not normalised_data.get("review_text"):
        return None

    # 4 & 5. Assemble final dict with product identifier and target platform
    final_dict = dict(normalised_data)
    final_dict["product_identifier"] = raw.get("product_name", "").strip()
    final_dict["platform"] = "flipkart"

    # 6. Return the final dict
    return final_dict


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

    # 1. Base Variables Init
    db = get_session_factory()
    session = db()
    product_cache = {}  # Format: {product_name: product_id}
    seen_reviews = {}  # Format: {product_name: set((reviewer_name, review_text))} — skips rows on re-runs
    review_count = 0
    
    # 2. Master Safety Fence Opens
    try:
        # Assuming you have a companion stream_flipkart_file generator yielding row dicts via csv.DictReader
        for raw in stream_flipkart_file(filepath):
            if limit is not None and review_count >= limit:
                break

            mapping = flipkart_to_reviewlens(raw)
            if mapping is None:
                continue

            # Extract the raw string product name from our mapping schema layout
            product_name = mapping.get("product_identifier")
            if not product_name:
                continue

            # b. Get-or-create Product row using the optimized in-memory cache pattern
            if product_name not in product_cache:
                # Query matches exactly to your db.py Product class column constraints
                product = (
                    session.query(Product)
                    .filter(Product.name == product_name, Product.platform == "flipkart")
                    .first()
                )
                
                # If it doesn't exist on disk, persist it instantly to generate an autoincrement ID
                if not product:
                    product = Product(
                        name=product_name,
                        platform="flipkart"
                    )
                    session.add(product)
                    session.flush()  # Allocates an index serial sequence immediately without a full commit overhead
                
                # Cache the product ID to bypass heavy downstream loop database queries
                product_cache[product_name] = product.id

                # Idempotency: snapshot (reviewer, text) pairs already stored for
                # this product (one query per product, not per review).
                # Re-running the loader — or duplicated rows in the source
                # file — can no longer multiply review rows and corrupt
                # aggregation. Keyed on reviewer+text so two users posting
                # the same words are still kept as separate reviews.
                seen_reviews[product_name] = {
                    (r, t) for (r, t) in session.query(
                        Review.reviewer_name, Review.review_text).filter(
                        Review.product_id == product.id).all()
                }

            # Skip reviews already in the DB from a previous load
            review_key = (mapping.get("reviewer_name"), mapping.get("review_text"))
            if review_key in seen_reviews[product_name]:
                continue
            seen_reviews[product_name].add(review_key)

            # c. Build the Review ORM object mapping directly to your exact db.py schema columns
            review = Review(
                product_id=product_cache[product_name],
                reviewer_name=mapping.get("reviewer_name"),
                review_text=mapping.get("review_text"),
                review_date=mapping.get("review_date"),
                rating=mapping.get("rating"),
                verified_purchase=mapping.get("verified_purchase"),
                review_length=mapping.get("review_length")
            )
            
            # d. Enqueue database entity operation and increment transaction counter
            session.add(review)
            review_count += 1
            
            # e. Every 1,000 rows: save transaction boundaries to disk and print progress
            if review_count % 1000 == 0:
                session.commit()
                print(f"[Flipkart] Processed {review_count} reviews...")
                
        # 3. Final Catch-all Commit captures remaining buffer mutations right as the streaming finishes
        session.commit()
        
    except Exception as e:
        session.rollback()
        print(f"[Flipkart Error] Pipeline failed. Rolled back transaction block. Error: {e}")
        raise e
    finally:
        session.close()
        
    # 4. Print Summary metrics after successful transaction completion and connection release
    print(f"Loaded {review_count} reviews across {len(product_cache)} products")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load Flipkart review dataset → PostgreSQL")
    parser.add_argument("--file", required=True, help="Path to Flipkart CSV file")
    parser.add_argument("--limit", type=int, default=None, help="Max reviews to load")
    args = parser.parse_args()
    load_flipkart(args.file, args.limit)
