"""
absa.py
Aspect-based sentiment analysis service (API layer).
Thin wrapper around the ML inference module so the API
does not talk to PyABSA directly.

Loads the analyser once at startup, reuses it for all requests.
"""

from typing import List

from ml.absa.inference import ABSAInference as CoreABSAInference


class ABSAInference:
    """
    Singleton service — delegates to ml.absa.inference.ABSAInference.
    Loaded once at app startup, reused for all requests.
    """

    def __init__(self, checkpoint: str = "multilingual"):
        """
        Instantiate the core PyABSA-backed analyser.

        TODO:
          self._core = CoreABSAInference(checkpoint=checkpoint)
          Wrap model-load errors so startup reports them clearly
        """
        pass

    def analyze_review(self, review_text: str):
        """
        Run ABSA on a single genuine review.

        Args:
            review_text: cleaned genuine review string

        Returns:
            review result with per-aspect sentiments
        """
        pass

    def analyze_batch(self, review_texts: List[str]):
        """
        Run ABSA on multiple genuine reviews.

        Args:
            review_texts: list of cleaned review strings

        Returns:
            list of per-review aspect sentiment results
        """
        pass