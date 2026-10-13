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
        weeks: how many weeks of history to return (calendar weeks from today)

    Returns:
        List of dicts: [{"week": "2026-W01", "mean_score": float, "count": int}]

    TODO:
      1. Filter aspect_sentiments to only the requested aspect
      2. Group by ISO week: datetime.isocalendar()[1]
      2. Compute mean score per week
      3. Filter to last N calendar weeks from today
      4. Return sorted list of weekly dicts (oldest first)
    """
    
    if not aspect_sentiments:
        return []

    # 1. Filter metrics down to strictly target the single requested aspect token key
    filtered_entries = [
        e for e in aspect_sentiments 
        if e.get("aspect", "").strip().lower() == aspect.strip().lower()
    ]
    if not filtered_entries:
        return []

    # Parse and extract valid datetime objects
    valid_entries = []
    for entry in filtered_entries:
        raw_date = entry.get("review_date")
        if isinstance(raw_date, str):
            try:
                dt = datetime.fromisoformat(raw_date.replace("Z", ""))
            except ValueError:
                continue
        elif isinstance(raw_date, datetime):
            dt = raw_date
        else:
            continue
        valid_entries.append((dt, entry))

    if not valid_entries:
        return []

    # Determine reference anchor: if reviews are historical (>90 days old), anchor to newest review
    all_dts = [item[0] for item in valid_entries]
    max_dt = max(all_dts)
    anchor = datetime.now() if (datetime.now() - max_dt).days < 90 else max_dt
    cutoff_date = anchor - timedelta(weeks=weeks)

    # First attempt: filter by cutoff_date
    weekly_data = defaultdict(list)
    for dt, entry in valid_entries:
        if dt >= cutoff_date:
            iso_year, iso_week, _ = dt.isocalendar()
            week_key = f"{iso_year}-W{iso_week:02d}"
            sent = entry.get("sentiment", "neutral")
            conf = entry.get("confidence", 0.5)
            weekly_data[week_key].append(sentiment_to_score(sent, conf))

    # If cutoff yielded nothing (e.g. data before cutoff), take the last `weeks` distinct week buckets
    if not weekly_data:
        all_weekly = defaultdict(list)
        for dt, entry in valid_entries:
            iso_year, iso_week, _ = dt.isocalendar()
            week_key = f"{iso_year}-W{iso_week:02d}"
            sent = entry.get("sentiment", "neutral")
            conf = entry.get("confidence", 0.5)
            all_weekly[week_key].append(sentiment_to_score(sent, conf))
        sorted_keys = sorted(all_weekly.keys())[-weeks:]
        weekly_data = {k: all_weekly[k] for k in sorted_keys}

    trend_list = []
    for week_str, scores in weekly_data.items():
        trend_list.append({
            "week": week_str,
            "mean_score": round(float(np.mean(scores)), 2),
            "review_count": len(scores)
        })

    trend_list.sort(key=lambda x: x["week"])
    return trend_list


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