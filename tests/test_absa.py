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
        TODO: assert sentiment_to_score("positive", 0.9) >= 7.0
        """
        pass

    def test_negative_scores_low(self):
        """
        A negative sentiment should score below 3.0.
        TODO: assert sentiment_to_score("negative", 0.9) < 3.0
        """
        pass

    def test_score_clamped(self):
        """
        sentiment_to_score should never exceed 10.0.
        TODO: assert sentiment_to_score("positive", 1.0) <= 10.0
        """
        pass


class TestAggregation:

    def test_aggregate_groups_by_aspect(self):
        """
        aggregate_product_aspects should return one entry per aspect.
        TODO: build sample aspect_sentiments, assert "battery" in result.
        """
        pass

    def test_winner_per_aspect(self):
        """
        compute_winner_per_aspect should pick the product with the highest score.
        TODO: two products, assert winner is the higher-scoring one.
        """
        pass

    def test_weekly_trend_sorted(self):
        """
        compute_weekly_trend should return weeks oldest first.
        TODO: assert weeks are sorted ascending.
        """
        pass