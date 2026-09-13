"""
test_scraper.py
Unit tests for the scraper and cleaner modules.
Run: pytest tests/test_scraper.py -v
"""

import pytest
from scraper.cleaner import clean_review_text, extract_review_metadata


class TestCleanReviewText:

    def test_strips_html(self):
        """
        HTML tags should be removed from review text.
        TODO: assert no "<" or ">" remains after cleaning
        """
        pass

    def test_collapses_whitespace(self):
        """
        Multiple spaces / newlines should collapse to a single space.
        TODO: assert "  good   phone " becomes "good phone"
        """
        pass

    def test_short_review_returns_none(self):
        """
        Text shorter than 10 chars should return None.
        TODO: assert clean_review_text("too short") is None
        """
        pass


class TestExtractMetadata:

    def test_rating_clamped_to_range(self):
        """
        Ratings above 5.0 should be clamped to 5.0.
        TODO: assert extract_review_metadata({"rating": "9"})["rating"] == 5.0
        """
        pass

    def test_reviewer_name_truncated(self):
        """
        Reviewer names longer than 200 chars should be truncated.
        TODO: assert len(result["reviewer_name"]) <= 200
        """
        pass