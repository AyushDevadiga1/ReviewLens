"""
fake_detector.py
Fake review detection service.
Loads saved model at startup, runs inference per review.
"""

import pickle
import numpy as np
from typing import List
from dataclasses import dataclass


@dataclass
class FakeDetectionResult:
    is_fake: bool
    confidence: float      # probability of being fake (0.0 to 1.0)
    model_version: str


class FakeReviewDetector:
    """
    Singleton service — loaded once at app startup, reused for all requests.
    """

    def __init__(self, model_dir: str = "ml/fake_review/model"):
        """
        Load classifier and vectorizer from disk.
        TODO:
          self.model = pickle.load(open(f"{model_dir}/classifier.pkl", "rb"))
          self.vectorizer = pickle.load(open(f"{model_dir}/vectorizer.pkl", "rb"))
          self.model_version = load from metadata JSON
        """
        pass

    def predict_single(self, review_text: str) -> FakeDetectionResult:
        """
        Run fake detection on one review.

        Args:
            review_text: cleaned review string

        Returns:
            FakeDetectionResult with is_fake, confidence, model_version

        TODO:
          1. Transform text: X = self.vectorizer.transform([review_text])
          2. Get probability: proba = self.model.predict_proba(X)[0]
             proba[1] = probability of being fake
          3. Threshold at 0.5: is_fake = proba[1] > 0.5
          4. Return FakeDetectionResult(is_fake, proba[1], self.model_version)
        """
        pass

    def predict_batch(self, review_texts: List[str]) -> List[FakeDetectionResult]:
        """
        Run fake detection on a list of reviews (more efficient than looping).

        TODO:
          1. Transform all texts at once: X = self.vectorizer.transform(review_texts)
          2. Get all probabilities: probas = self.model.predict_proba(X)
          3. Build FakeDetectionResult for each
          4. Return list
        """
        pass

    def filter_genuine(
        self,
        reviews: List[dict],
        results: List[FakeDetectionResult]
    ) -> List[dict]:
        """
        Filter reviews to keep only genuine ones.
        Attach confidence score to each kept review.

        TODO:
          Return [r for r, res in zip(reviews, results) if not res.is_fake]
          Add res.confidence to each kept review dict as "genuine_confidence"
        """
        pass