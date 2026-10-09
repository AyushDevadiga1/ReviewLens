"""
fake_detector.py
Fake review detection service.
Loads saved model at startup, runs inference per review.
"""

import os
import json
import pickle
import numpy as np
import scipy.sparse as sp
from typing import List,Dict,Any
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
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        target_dir = os.path.join(base_dir, model_dir)
        
        self.vectorizer_path = os.path.join(target_dir, "tfidf_vectorizer.pkl")
        self.model_path = os.path.join(target_dir, "classifier.pkl")
        
        self.vectorizer = None
        self.model = None

         # Target path for the version metadata file
        self.metadata_path = os.path.join(target_dir, "metadata.json")
        self.model_version = "unknown"  # Default fallback if file is missing

        self.label_encoder_path = os.path.join(target_dir, "label_encoder.pkl")

        # Load the assets and metadata immediately into memory
        self.load_artifacts()

    def load_artifacts(self):
        """Helper method to handle safe file reading at startup."""
        try:
            # 1. Load the ML files
            if os.path.exists(self.vectorizer_path) and os.path.exists(self.model_path):
                with open(self.vectorizer_path, "rb") as f:
                    self.vectorizer = pickle.load(f)
                with open(self.model_path, "rb") as f:
                    self.model = pickle.load(f)
                with open(self.label_encoder_path, "rb") as f:
                    self.label_encoder = pickle.load(f)
                print(f"Successfully loaded Fake Review Detector from {self.model_path}")
            else:
                print("Warning: Model files not found.")

            # 2. DYNAMIC LOOKUP: Load model version from metadata JSON
            if os.path.exists(self.metadata_path):
                with open(self.metadata_path, "r") as f:
                    meta_data = json.load(f)
                    # Safely look for 'version' key, fallback to "1.0.0" if key doesn't exist
                    self.model_version = meta_data.get("model_type", "TF-IDF+LR")
            else:
                print(f"Metadata JSON not found at {self.metadata_path}. Using fallback version '1.0.0'.")
                self.model_version = "1.0.0"

        except Exception as e:
            print(f"Error initializing ML artifacts: {str(e)}")

    def predict_single(self, review_text: str ,rating : float = 4.0) -> FakeDetectionResult:
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
        if self.vectorizer is None or self.model is None:
            return FakeDetectionResult(is_fake=False, confidence=0.0, model_version=self.model_version)

        X_text = self.vectorizer.transform([review_text])
        normalised_rating = (rating - 1.0) / 4.0
        
        X_rating = np.array([[normalised_rating]])
        X_combined = sp.hstack([X_text, X_rating], format="csr")

        proba = self.model.predict_proba(X_combined)[0]
        # Classes are alphabetical: negative=0, neutral=1, positive=2
        positive_prob = float(proba[2])

        # Fake heuristic from train.py docstring:
        # Suspicious = predicted positive with high confidence AND short text,
        # OR 5-star rating with one-liner text (classic incentivised-fake shape).
        # Thresholds must sit ABOVE the ingestion floor (cleaner drops <20 chars,
        # schema enforces min_length=20) or the filter can never fire.
        # Calibrated 2026-10-08 on 500 real DB reviews: flags ~5%.
        text_length = len(review_text.strip())

        heuristic_fake = (
            (positive_prob > 0.90 and text_length < 50) or
            (rating >= 5.0 and text_length < 30)
        )

        # Fake confidence = how strongly the heuristic fires
        # Use positive_prob as proxy — high positive confidence on short text = suspicious
        fake_confidence = positive_prob if heuristic_fake else (positive_prob * 0.3)

        return FakeDetectionResult(
            is_fake=heuristic_fake,
            confidence=round(fake_confidence, 4),
            model_version=self.model_version
        )

    def predict_batch(self, review_texts: List[str],ratings: List[float] = None) -> List[FakeDetectionResult]:
        """
        Run fake detection on a list of reviews (more efficient than looping).

        TODO:
          1. Transform all texts at once: X = self.vectorizer.transform(review_texts)
          2. Get all probabilities: probas = self.model.predict_proba(X)
          3. Build FakeDetectionResult for each
          4. Return list
        """
        if self.vectorizer is None or self.model is None or not review_texts:
            return []

        X_text_batch = self.vectorizer.transform(review_texts)

        if ratings is None :
            ratings = [4.0] * len(review_texts)

        normalised_ratings = [(r - 1.0) / 4.0 for r in ratings]
        X_rating_batch = np.array(normalised_ratings).reshape(-1, 1)

        X_combined_batch = sp.hstack([X_text_batch, X_rating_batch], format="csr")

        probas = self.model.predict_proba(X_combined_batch)

        results = []

        for i, proba in enumerate(probas):
            positive_prob = float(proba[2])  # negative=0, neutral=1, positive=2
            
            text_length = len(review_texts[i].strip())  # ← use index to get matching text
            rating = ratings[i]                          # ← use index to get matching rating

            # Same heuristic as predict_single — keep both in sync.
            # Calibrated 2026-10-08 on 500 real DB reviews: flags ~5%.
            heuristic_fake = (
                (positive_prob > 0.90 and text_length < 50) or
                (rating >= 5.0 and text_length < 30)
            )

            fake_confidence = positive_prob if heuristic_fake else (positive_prob * 0.3)

            results.append(FakeDetectionResult(
                is_fake=heuristic_fake,
                confidence=round(fake_confidence, 4),
                model_version=self.model_version
            ))

        return results       

    def filter_genuine(
        self,
        reviews: List,
        results: List[FakeDetectionResult]
    ) -> List:
        """
        Filter reviews to keep only genuine ones.
        Attach confidence score to each kept review.

        TODO:
          Return [r for r, res in zip(reviews, results) if not res.is_fake]
          Add res.confidence to each kept review dict as "genuine_confidence"
        """
        genuine_reviews = []

        for review, detection_res in zip(reviews, results):
            if not detection_res.is_fake:
                genuine_reviews.append(review)

        return genuine_reviews

    