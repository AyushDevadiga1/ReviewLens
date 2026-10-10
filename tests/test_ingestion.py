"""
test_ingestion.py
Unit tests for data_ingestion — cleaner and both dataset loaders.
Run: pytest tests/test_ingestion.py -v

Renamed from test_scraper.py — scraper/ replaced by data_ingestion/.
No network or DB required; all tests use in-memory data only.
"""

import pytest
from data_ingestion.cleaner import clean_review_text, extract_review_metadata


# ── cleaner.py tests ───────────────────────────────────────────────────────────

class TestCleanReviewText:

    def test_strips_html(self):
        """HTML tags must be removed from review text."""
        raw = "<b>Great phone with excellent battery life indeed</b>"
        cleaned = clean_review_text(raw)
        assert cleaned is not None
        assert "<" not in cleaned and ">" not in cleaned
        assert "Great phone with excellent battery life indeed" in cleaned

    def test_collapses_whitespace(self):
        """Multiple spaces/newlines must collapse to a single space."""
        assert clean_review_text("  good   phone with great battery life  ") == \
            "good phone with great battery life"

    def test_short_review_returns_none(self):
        """Text under 10 chars must return None."""
        assert clean_review_text("ok") is None

    def test_unicode_normalised(self):
        """Combining marks fold to ASCII; Devanagari script is preserved."""
        import unicodedata
        # Force decomposed form programmatically: e + combining acute.
        decomposed = unicodedata.normalize(
            "NFD", "e\u0301clair is a tasty French pastry indeed")
        assert any(unicodedata.combining(c) for c in decomposed)
        cleaned = clean_review_text(decomposed)
        assert not any(unicodedata.combining(c) for c in cleaned)
        assert cleaned.startswith("eclair")
        hinglish = ("\u092f\u0939 \u092b\u094b\u0928 \u092c\u0939\u0941\u0924 "
                    "\u0905\u091a\u091b\u093e \u0948 and the battery "
                    "life is great overall")
        kept = clean_review_text(hinglish)
        assert any("\u0900" <= c <= "\u097f" for c in kept)

class TestExtractMetadata:

    def test_rating_clamped_to_range(self):
        """Ratings above 5.0 must be clamped to 5.0."""
        result = extract_review_metadata({
            "text": "Great battery life on this phone indeed",
            "rating": "9", "reviewer": "R"})
        assert result["rating"] == 5.0

    def test_reviewer_name_truncated(self):
        """Reviewer names over 200 chars must be truncated."""
        result = extract_review_metadata({
            "text": "Great battery life on this phone indeed",
            "rating": "4", "reviewer": "A" * 300})
        assert len(result["reviewer_name"]) == 200

    def test_missing_text_returns_none_review(self):
        """When text is empty, review_text in result should be None."""
        result = extract_review_metadata({"text": "", "rating": "4"})
        assert result["review_text"] is None


# ── amazon_loader.py tests ─────────────────────────────────────────────────────

class TestMcauleyMapping:

    def test_maps_required_fields(self):
        """
        mcauley_to_reviewlens must map all five required fields.
        """
        from data_ingestion.loaders.amazon_loader import mcauley_to_reviewlens
        raw = {"asin": "B001", "reviewText": "Great battery life on this phone.",
               "overall": 5.0, "reviewerName": "Rahul", "reviewTime": "01 1, 2020",
               "verified": True}
        result = mcauley_to_reviewlens(raw)
        assert result["product_identifier"] == "B001"
        assert result["rating"] == 5.0
        assert result["verified_purchase"] is True

    def test_falls_back_to_summary(self):
        """
        If reviewText is missing, summary must be used as fallback text.
        """
        from data_ingestion.loaders.amazon_loader import mcauley_to_reviewlens
        raw = {"asin": "B002", "summary": "Amazing camera quality here.",
               "overall": 4.0, "reviewTime": "02 1, 2020", "verified": False}
        result = mcauley_to_reviewlens(raw)
        assert result is not None
        assert "camera" in result["review_text"]

    def test_missing_text_returns_none(self):
        """
        If both reviewText and summary are absent, return None.
        """
        from data_ingestion.loaders.amazon_loader import mcauley_to_reviewlens
        raw = {"asin": "B003", "overall": 3.0}
        assert mcauley_to_reviewlens(raw) is None


# ── flipkart_loader.py tests ───────────────────────────────────────────────────

class TestFlipkartMapping:

    def test_maps_required_fields(self):
        """
        flipkart_to_reviewlens must map product name, review text, rating.
        Accepts both "Product Name" and "product_name" headers.
        """
        from data_ingestion.loaders.flipkart_loader import flipkart_to_reviewlens
        for key in ("Product Name", "product_name"):
            result = flipkart_to_reviewlens({
                key: "OnePlus 12",
                "Review": "Excellent display quality here indeed.",
                "Rate": "4", "Summary": "Good phone"})
            assert result["product_identifier"] == "OnePlus 12"
            assert result["platform"] == "flipkart"
            assert result["rating"] == 4.0

    def test_falls_back_to_summary(self):
        """
        If Review column is empty, Summary must be used.
        """
        from data_ingestion.loaders.flipkart_loader import flipkart_to_reviewlens
        result = flipkart_to_reviewlens({
            "Product Name": "Redmi Note 13", "Review": "",
            "Rate": "3", "Summary": "Average battery performance overall."})
        assert result is not None
        assert "battery" in result["review_text"]
