"""
aggregator.py
Aggregates aspect sentiment scores across all reviews of a product.
Produces the final scores shown in the comparison dashboard.
"""

import numpy as np
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict


def sentiment_to_score(sentiment: str, confidence: float) -> float:
    """
    Convert sentiment label + confidence to a numeric score (0.0 to 10.0).

    Mapping:
      positive: base score 7.0 + confidence * 3.0  → range [7.0, 10.0]
      neutral:  base score 5.0 + (confidence - 0.5) → range [4.5, 5.5]
      negative: base score 3.0 - confidence * 3.0  → range [0.0, 3.0]

    TODO: implement the mapping above and clamp result to [0.0, 10.0]
    """
    pass


def aggregate_product_aspects(
    aspect_sentiments: List[dict]
) -> Dict[str, dict]:
    """
    Aggregate all aspect sentiments for one product into summary scores.

    Args:
        aspect_sentiments: list of dicts from DB with keys:
                           aspect, sentiment, confidence, review_date

    Returns:
        Dict keyed by aspect name, value is:
        {
          "mean_score": float (0.0-10.0),
          "review_count": int,
          "positive_pct": float,
          "negative_pct": float,
          "neutral_pct": float,
          "sentiment_label": str ("positive"/"negative"/"neutral")
        }

    TODO:
      1. Group by aspect using defaultdict(list)
      2. For each aspect:
         a. Compute mean score using sentiment_to_score()
         b. Count positive/negative/neutral occurrences
         c. Compute percentages
         d. Assign overall sentiment_label based on mean_score:
            ≥ 7.0 → positive, ≤ 4.0 → negative, else → neutral
      3. Return dict
    """
    pass


def compute_winner_per_aspect(
    product_scores: Dict[str, Dict[str, dict]]
) -> Dict[str, str]:
    """
    Determine which product wins on each aspect.

    Args:
        product_scores: {product_name: {aspect: {"mean_score": float, ...}}}

    Returns:
        {aspect: winning_product_name}

    TODO:
      For each aspect, find product with highest mean_score.
      Handle ties by returning first alphabetically.
    """
    pass


def compute_weekly_trend(
    aspect_sentiments: List[dict],
    aspect: str,
    weeks: int = 8
) -> List[dict]:
    """
    Compute weekly sentiment trend for one aspect of one product.

    Args:
        aspect_sentiments: list of dicts with aspect, sentiment, confidence, review_date
        aspect: which aspect to filter for
        weeks: how many weeks of history to return

    Returns:
        List of dicts: [{"week": "2026-W01", "mean_score": float, "count": int}]

    TODO:
      1. Filter aspect_sentiments to only the requested aspect
      2. Group by ISO week: datetime.isocalendar()[1]
      3. Compute mean score per week
      4. Return sorted list of weekly dicts (oldest first)
    """
    pass