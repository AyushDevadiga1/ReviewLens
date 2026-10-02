"""
cleaner.py
Text preprocessing shared by all dataset loaders.
Both amazon_loader.py and dataset_sa_loader.py pass review text through here
before anything is written to the database.

EDA findings that shaped this cleaner:
  - Amazon: min review length is 1 char, mean 277, max 33,457
  - Amazon: reviewTime is inconsistent — single and double digit months/days
             e.g. "8 4, 2014" and "02 12, 2014" both appear
  - Amazon: 33,971 reviews from "Amazon Customer" — anonymous, store as-is
  - Dataset-SA: Summary is the longer useful text, Review is the short title
                ("super!", "awesome") — Summary should be primary
  - Dataset-SA: product names contain ?????? from encoding issues —
                same garbling can appear in review text
  - Both: heavily right-skewed ratings, no contradictory sentiment labels
  - Threshold: 20 chars minimum — anything under is noise ("good", "BUENO")
"""

import re
import unicodedata
from datetime import datetime
from typing import Optional

def clean_review_text(raw_text: str) -> Optional[str]:
    r"""
    Clean a single review string and return None if it is too short to use.

   Args:
      raw_text: raw review string from any dataset source

    Returns:
      Cleaned string, or None if text is under 20 chars after cleaning

    TODO:
      1. Guard clause — if raw_text is None or not a string, return None
         Why: both datasets have null reviewText rows; passing None to .strip()
         crashes. Check with: if not raw_text or not isinstance(raw_text, str)

      2. raw_text.strip()
         Why: leading/trailing whitespace is common in CSV and JSON fields

      3. re.sub(r'<[^>]+>', '', text)
         Why: some Amazon reviews contain HTML like <br />, &amp; — strip tags
         before any length check so they don't inflate the char count

      4. re.sub(r'[^\x00-\x7F\u0900-\u097F]+', '', text)
         Why: the ?????? garbling in Dataset-SA comes from mojibake —
         non-ASCII, non-Devanagari characters that aren't real content.
         \x00-\x7F keeps standard ASCII (English).
         \u0900-\u097F keeps Devanagari (Hindi reviews exist in Dataset-SA).
         Anything outside those ranges is garbled encoding — drop it.

      5. unicodedata.normalize('NFC', text)
         Why: NFC composites combining characters into single code points.
         Handles accented chars and Hinglish mixed text that can appear
         as two-char sequences instead of one, causing length miscounts.

      6. re.sub(r'\s+', ' ', text).strip()
         Why: after stripping HTML and non-ASCII, multiple spaces/newlines
         are left behind. Collapse them to a single space.

      7. return None if len(text) < 20 else text
         Why: EDA showed Amazon min is 1 char ("great", "BUENO", single words).
         Dataset-SA mean is only 12.6 chars for the Review column.
         Anything under 20 chars after cleaning has no aspect signal for PyABSA
         and is noise for the fake detector. 20 is the informed threshold.
    """

    if (raw_text is None) or (not isinstance(raw_text, str)):
        return None
    
    text = raw_text.strip()
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'[^\x00-\x7F\u0900-\u097F]+', '', text)
    text = unicodedata.normalize("NFC",text)
    text = re.sub(r'\s+', ' ', text).strip()

    if len(text) < 20:
        return None

    return text


def extract_review_metadata(raw_review: dict) -> dict:
    """
   Normalise and type-cast one review dict into the ReviewLens schema shape.
   Called by both loaders after they map their source columns to common keys.

    Args:
        raw_review: dict with these keys (all optional except text):
            text     — review body string (primary text, already chosen by loader)
            rating   — numeric rating, may be int/float/string
            reviewer — reviewer name string, may be missing
            date     — date string, may be missing or format may vary
            verified — bool or missing

    Returns:
        Dict with ReviewLens Review column names:
            review_text       : str or None (None means skip this row)
            rating            : float (1.0-5.0) or None
            reviewer_name     : str max 200 chars, empty string if missing
            review_date       : datetime or None
            verified_purchase : bool, False if missing
            review_length     : int, 0 if review_text is None

    TODO:
      1. Clean the text first — call clean_review_text(raw_review.get("text", ""))
         Store result as review_text.
         Why: do this first so review_length is based on cleaned text,
         not raw text with HTML tags inflating the count.

      2. Cast rating to float safely:
             float(raw_review.get("rating", 0) or 0)
         Then clamp: max(1.0, min(5.0, rating))
         Wrap in try/except ValueError — Dataset-SA Rate column is object dtype
         and may have non-numeric values (your EDA noted this needs checking).
         Set rating = None on any failure.
         Why: both datasets have ratings as different types — Amazon stores
         overall as float64, Dataset-SA stores Rate as object (string).

      3. Reviewer name — raw_review.get("reviewer", "") or ""
         Slice to 200 chars: [:200]
         Why: DB column is String(200). "Amazon Customer" appears 33,971 times
         — store it as-is, don't treat it specially.

      4. Parse date string → datetime. Try these formats in order:
            "%m %d, %Y"   — covers "08 4, 2014" AND "02 12, 2014"
                              (strptime handles single/double digit day with %d)
            "%d %B %Y"    — covers "12 March 2024" style if present
            "%Y-%m-%d"    — ISO format fallback
         Loop over formats, return first that parses. Set None if all fail.
         Why: Amazon reviewTime is inconsistent — EDA showed "8 4, 2014" and
         "02 12, 2014" both appear. Dataset-SA has no date column so date
         arrives as "" — all formats will fail and None is returned, which is
         correct since review_date is nullable=True in the schema.

      5. verified_purchase — bool(raw_review.get("verified", False))
         Why: Amazon stores this as a JSON bool. Dataset-SA has no verified
         column so the loader passes False, and bool(False) stays False.

      6. review_length — len(review_text) if review_text else 0
         Why: stored as a DB column so the fake detector can query
         "reviews where review_length < 20" directly without recomputing.
         Short length is one of the strongest fake review signals.

      7. Return the assembled dict with all six keys.
         Do NOT return None here even if review_text is None —
         the loader checks result["review_text"] and skips the row itself.
         Why: keeping the return shape consistent means the loader never
         needs to handle two different return types from this function.

    """

    DATE_FORMATS = ["%m %d, %Y", "%d %B %Y", "%Y-%m-%d"]

    review_text = clean_review_text(raw_review.get("text", ""))
    rating = None
    
    try:
        # If rating is missing, None, or "", float() will raise a ValueError or TypeError
        raw_val = raw_review.get("rating")
        # Check if raw_val is not None and not an empty string
        if raw_val and str(raw_val).strip():
            rating = float(raw_val)
            rating = max(1.0, min(5.0, rating))
    except (TypeError,ValueError):
        print(f'The parsing for {raw_review.get("rating")} failed ! Expecting a numeric value in between 1.0 and 5.0 for the key : rating ')
    except Exception as e:
        print(f'Oh oh @ {e} @')

    reviewer_name = raw_review.get("reviewer","") or ""
    reviewer_name = reviewer_name[:200] 

    if isinstance(raw_review.get("date",""), datetime):
        review_date = raw_review.get("date","")
        parsed_date = review_date
    else:
        review_date = (raw_review.get("date","") or "").strip()
        parsed_date = None

        for curr_pattern in DATE_FORMATS:
            try:
                parsed_date = datetime.strptime(review_date,curr_pattern)
                break
            except ValueError:
                pass
            except Exception as e:
                print(f'Unable to parse {review_date} because of exception : {e}')

    verified_purchase = bool(raw_review.get("verified",False)) 

    if review_text :
        review_length = len(review_text)
    else:
        review_length = 0

    
    return {
                "review_text"       : review_text,
                "rating"            : rating,
                "reviewer_name"     : reviewer_name,
                "review_date"       : parsed_date,
                "verified_purchase" : verified_purchase,
                "review_length"     : review_length,
    }

