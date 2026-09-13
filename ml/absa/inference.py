"""
inference.py
PyABSA aspect-based sentiment analysis inference.
Uses pre-trained BERT checkpoint — no fine-tuning needed for demo.

Install: pip install pyabsa
Model downloads automatically on first run (~500MB, cached after).
"""

from typing import List, Dict
from dataclasses import dataclass
import pyabsa
from aspects import ASPECT_NAMES


@dataclass
class AspectResult:
    aspect: str          # e.g. "battery"
    sentiment: str       # "positive", "negative", "neutral"
    confidence: float    # 0.0 to 1.0


@dataclass
class ReviewABSAResult:
    review_text: str
    aspects: List[AspectResult]


class ABSAInference:
    """
    Singleton service — model loaded once at startup.
    PyABSA handles tokenisation, inference, and aspect extraction.
    """

    def __init__(self):
        """
        Load PyABSA sentiment analyser.
        Model is downloaded automatically on first run.

        TODO:
          self.sentiment_analyser = pyabsa.AspectTermExtraction.SentimentClassifier(
              checkpoint='multilingual',  # works for English and mixed text
              auto_device=True            # uses GPU if available, else CPU
          )
        """
        pass

    def analyze_review(self, review_text: str) -> ReviewABSAResult:
        """
        Run ABSA on a single review text.

        Args:
            review_text: cleaned genuine review string

        Returns:
            ReviewABSAResult with list of AspectResult

        TODO:
          1. result = self.sentiment_analyser.predict(review_text)
             PyABSA returns: {'aspect': [...], 'sentiment': [...], 'confidence': [...]}
          2. Build AspectResult for each (aspect, sentiment, confidence) triple
          3. Map aspect terms to canonical names from ASPECT_NAMES
             e.g. "battery life" → "battery", "cam" → "camera"
          4. Return ReviewABSAResult
        """
        pass

    def analyze_batch(self, review_texts: List[str]) -> List[ReviewABSAResult]:
        """
        Run ABSA on multiple reviews (batched — more efficient than looping).

        TODO:
          results = self.sentiment_analyser.predict(review_texts)
          Parse results list into List[ReviewABSAResult]
        """
        pass

    def map_aspect_to_canonical(self, raw_aspect: str) -> str:
        """
        Map raw PyABSA aspect term to canonical aspect name.

        Args:
            raw_aspect: e.g. "battery life", "cam quality", "build"

        Returns:
            canonical name from ASPECT_NAMES, or "other" if no match

        TODO:
          1. Lowercase raw_aspect
          2. Check if any canonical name is a substring of raw_aspect
          3. Check if any keyword from aspects.py matches
          4. Return matched canonical name or "other"
        """
        pass