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
        TODO: detector = FakeReviewDetector()
              result = detector.predict_single("Very good phone")
              assert isinstance(result, FakeDetectionResult)
        """
        pass

    def test_predict_batch_matches_input_length(self):
        """
        predict_batch should return one result per input review.
        TODO: assert len(results) == len(review_texts)
        """
        pass

    def test_filter_genuine_drops_fake(self):
        """
        filter_genuine should only keep reviews flagged as genuine.
        TODO: build fake results list, assert fake ones are removed.
        """
        pass