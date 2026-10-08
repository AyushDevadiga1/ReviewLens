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

    clean_sentiment = sentiment.strip().lower()
    
    if clean_sentiment == "positive":
        score = 7.0 + (confidence * 3.0)
    elif clean_sentiment == "neutral":
        score = 5.0 + (confidence - 0.5)
    elif clean_sentiment == "negative":
        score = 3.0 - (confidence * 3.0)
    else:
        score = 5.0  # Safe middle fallback for unexpected strings

    # Clamp the final mathematical float value strictly between 0.0 and 10.0
    return max(0.0, min(score, 10.0))


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

    if not aspect_sentiments:
        return {}

    # 1. Group by aspect using defaultdict(list)
    aspect_groups = defaultdict(list)
    for entry in aspect_sentiments:
        aspect_name = entry.get("aspect")
        if aspect_name:
            aspect_groups[aspect_name].append(entry)

    summary_scores = {}

    # 2. Process metrics for each individual aspect tier group
    for aspect, entries in aspect_groups.items():
        scores = []
        pos_count = 0
        neg_count = 0
        neu_count = 0
        total_count = len(entries)

        for entry in entries:
            sent = entry.get("sentiment", "neutral")
            conf = entry.get("confidence", 0.5)
            
            # Accumulate converted numeric ratings
            scores.append(sentiment_to_score(sent, conf))
            
            # Tally string occurrences for percentage generation distributions
            clean_sent = sent.strip().lower()
            if clean_sent == "positive":
                pos_count += 1
            elif clean_sent == "negative":
                neg_count += 1
            else:
                neu_count += 1

        mean_score = float(np.mean(scores)) if scores else 5.0

        # Assign dynamic semantic tracking labels based on calculated score cutoffs
        if mean_score >= 7.0:
            sentiment_label = "positive"
        elif mean_score <= 4.0:
            sentiment_label = "negative"
        else:
            sentiment_label = "neutral"

        summary_scores[aspect] = {
            "mean_score": round(mean_score, 2),
            "review_count": total_count,
            "positive_pct": round((pos_count / total_count) * 100.0, 2) if total_count else 0.0,
            "negative_pct": round((neg_count / total_count) * 100.0, 2) if total_count else 0.0,
            "neutral_pct": round((neu_count / total_count) * 100.0, 2) if total_count else 0.0,
            "sentiment_label": sentiment_label
        }

    return summary_scores



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

    if not product_scores:
        return {}

    # Collect all unique aspect category entries found across all products
    all_aspects = set()
    for aspects_dict in product_scores.values():
        all_aspects.update(aspects_dict.keys())

    winners = {}

    # Calculate maximum evaluation rankings for every aspect group matrix column
    for aspect in all_aspects:
        best_product = None
        best_score = -1.0

        for product_name, aspects_dict in product_scores.items():
            if aspect in aspects_dict:
                current_score = aspects_dict[aspect].get("mean_score", 0.0)
                
                # Check for direct score improvements
                if current_score > best_score:
                    best_score = current_score
                    best_product = product_name
                # Deterministic tie-handling: fall back to alphabetical ordering string checks
                elif current_score == best_score:
                    if best_product is None or product_name < best_product:
                        best_product = product_name

        if best_product:
            winners[aspect] = best_product

    return winners


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
    
    if not aspect_sentiments:
        return []

    # 1. Filter metrics down to strictly target the single requested aspect token key
    filtered_entries = [
        e for e in aspect_sentiments 
        if e.get("aspect", "").strip().lower() == aspect.strip().lower()
    ]

    # Group score vectors by tracking string key names: "YYYY-WXX"
    weekly_data = defaultdict(list)

    for entry in filtered_entries:
        raw_date = entry.get("review_date")
        
        # Parse timestamp objects safely out of string representations if required
        if isinstance(raw_date, str):
            try:
                dt = datetime.fromisoformat(raw_date.replace("Z", ""))
            except ValueError:
                continue  # Skip rows with malformed dates
        elif isinstance(raw_date, datetime):
            dt = raw_date
        else:
            continue

        # Extract strict ISO Year and ISO Week tracking tokens
        iso_year, iso_week, _ = dt.isocalendar()
        week_key = f"{iso_year}-W{iso_week:02d}"
        
        sent = entry.get("sentiment", "neutral")
        conf = entry.get("confidence", 0.5)
        score = sentiment_to_score(sent, conf)
        
        weekly_data[week_key].append(score)

    trend_list = []

    # 2. Build aggregated data list maps
    for week_str, scores in weekly_data.items():
        trend_list.append({
            "week": week_str,
            "mean_score": round(float(np.mean(scores)), 2),
            "review_count": len(scores)
        })

    # 3. Return sorted elements sequentially (Oldest week key string first)
    trend_list.sort(key=lambda x: x["week"])
    
    # Return up to the maximum number of requested window historical snapshots
    return trend_list[-weeks:]