"""
test_absa.py
Unit tests for ABSA inference and aggregation.
Run: pytest tests/test_absa.py -v
"""

import pytest
from collections import defaultdict
from api.services.aggregator import (
    sentiment_to_score,
    aggregate_product_aspects,
    compute_winner_per_aspect,
    compute_weekly_trend
)


class TestSentimentToScore:

    def test_positive_scores_high(self):
        """
        A positive sentiment with high confidence should score >= 7.0.
        """
        assert sentiment_to_score("positive", 0.9) >= 7.0

    def test_negative_scores_low(self):
        """
        A negative sentiment should score below 3.0.
        """
        assert sentiment_to_score("negative", 0.9) < 3.0

    def test_score_clamped(self):
        """
        sentiment_to_score should never exceed 10.0.
        """
        assert sentiment_to_score("positive", 1.0) <= 10.0
        assert sentiment_to_score("negative", 1.0) >= 0.0


class TestAggregation:

    def _sample(self):
        from datetime import datetime
        return [
            {"aspect": "battery", "sentiment": "positive",
             "confidence": 0.9, "review_date": datetime(2026, 1, 5)},
            {"aspect": "battery", "sentiment": "negative",
             "confidence": 0.8, "review_date": datetime(2026, 1, 12)},
            {"aspect": "camera", "sentiment": "positive",
             "confidence": 0.7, "review_date": datetime(2026, 1, 19)},
        ]

    def test_aggregate_groups_by_aspect(self):
        """
        aggregate_product_aspects should return one entry per aspect.
        """
        result = aggregate_product_aspects(self._sample())
        assert "battery" in result
        assert result["battery"]["review_count"] == 2
        assert result["camera"]["review_count"] == 1

    def test_winner_per_aspect(self):
        """
        compute_winner_per_aspect should pick the product with the highest score.
        """
        scores = {
            "Alpha": {"battery": {"mean_score": 9.0}},
            "Beta": {"battery": {"mean_score": 4.0}},
        }
        assert compute_winner_per_aspect(scores) == {"battery": "Alpha"}

    def test_weekly_trend_sorted(self):
        """
        compute_weekly_trend should return weeks oldest first.
        """
        trend = compute_weekly_trend(self._sample(), "battery", weeks=8)
        weeks = [point["week"] for point in trend]
        assert weeks == sorted(weeks)
        assert all("review_count" in point for point in trend)