"""
test_fake_detector.py
Unit tests for the fake review detection service.
Run: pytest tests/test_fake_detector.py -v
"""

import pytest
from api.services.fake_detector import FakeReviewDetector, FakeDetectionResult


class TestFakeReviewDetector:

    def test_predict_single_returns_result(self):
        """
        predict_single should return a FakeDetectionResult.
        """
        detector = FakeReviewDetector()
        result = detector.predict_single(
            "The battery lasts two full days of heavy use here", 5.0)
        assert isinstance(result, FakeDetectionResult)
        assert isinstance(result.is_fake, bool)
        assert 0.0 <= result.confidence <= 1.0

    def test_predict_batch_matches_input_length(self):
        """
        predict_batch should return one result per input review.
        """
        detector = FakeReviewDetector()
        review_texts = [
            "The battery lasts two full days of heavy use here",
            "Camera struggles in low light but daylight shots are sharp",
            "Average build quality for the price point overall",
        ]
        results = detector.predict_batch(review_texts, [5.0, 3.0, 4.0])
        assert len(results) == len(review_texts)
        assert all(isinstance(r, FakeDetectionResult) for r in results)

    def test_filter_genuine_drops_fake(self):
        """
        filter_genuine should only keep reviews flagged as genuine.
        """
        detector = FakeReviewDetector()
        reviews = ["r1", "r2", "r3"]
        results = [
            FakeDetectionResult(is_fake=False, confidence=0.1,
                                model_version="t"),
            FakeDetectionResult(is_fake=True, confidence=0.9,
                                model_version="t"),
            FakeDetectionResult(is_fake=False, confidence=0.2,
                                model_version="t"),
        ]
        assert detector.filter_genuine(reviews, results) == ["r1", "r3"]