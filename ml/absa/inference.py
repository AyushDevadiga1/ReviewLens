"""
inference.py
PyABSA aspect-based sentiment analysis inference.
Uses pre-trained BERT checkpoint — no fine-tuning needed for demo.

Install: pip install pyabsa
Model downloads automatically on first run (~500MB, cached after).
"""

from typing import List, Dict
from dataclasses import dataclass

import os
os.environ["PYABSA_DISABLE_CUDNN"] = "1"
os.environ["AUTO_DEVICE"] = "False"

import warnings
warnings.filterwarnings("ignore")
from pyabsa import AspectTermExtraction as ATEPC

from ml.absa.aspects import ASPECTS

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

        Uses AspectExtractor — present in both pyabsa 2.3.x (pinned for
        Docker) and 2.4.x (dev venv) — instead of SentimentClassifier,
        which only exists on 2.4.x and broke the container import chain.
        """
        self.sentiment_analyzer = ATEPC.AspectExtractor(
              checkpoint='multilingual',
              auto_device=False
          )

    def _build_aspect_results(self, aspects, sentiments, confidences) -> List[AspectResult]:
        """
        Single parse contract for one model's raw output triple.

        Tolerates version drift: sentiments arrive capitalised
        ('Positive') and confidence may be a flat list of floats
        ('confidence' key) or per-aspect probability vectors
        ('probs' key) — confidence is then max(prob_vector),
        independent of class ordering.
        """
        aspect_results = []
        for i, aspect in enumerate(aspects or []):
            raw_sent = sentiments[i] if i < len(sentiments or []) else "neutral"
            sentiment = str(raw_sent).strip().lower()

            conf = 0.5
            if i < len(confidences or []):
                c = confidences[i]
                conf = float(max(c)) if isinstance(c, (list, tuple)) else float(c)

            aspect_results.append(AspectResult(
                aspect=self.map_aspect_to_canonical(aspect),
                sentiment=sentiment,
                confidence=conf
            ))
        return aspect_results

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
        
        result = self.sentiment_analyzer.predict(review_text)

        # 2.3.x returns one dict for a single text; tolerate list-wrapped
        # results so a minor-version shape change degrades instead of 500s.
        if isinstance(result, list):
            result = result[0] if result else {}

        aspects = result.get('aspect', []) or []
        sentiments = result.get('sentiment', []) or []
        confidences = result.get('confidence', None) or result.get('probs', []) or []

        aspect_results = self._build_aspect_results(aspects, sentiments, confidences)
            
        return ReviewABSAResult(review_text=review_text, aspects=aspect_results)

    def analyze_batch(self, review_texts: List[str]) -> List[ReviewABSAResult]:
        """
        Run ABSA on multiple reviews (batched — more efficient than looping).

        TODO:
          results = self.sentiment_analyser.predict(review_texts)
          Parse results list into List[ReviewABSAResult]
        """
        
        results = self.sentiment_analyzer.predict(review_texts)

        # Ensure results is treated as a list even if a single string was passed
        if isinstance(results, dict):
            results = [results]
            
        parsed_batch = []
        
        # Parse the results list into List[ReviewABSAResult]
        
        for text, res in zip(review_texts, results):
            aspects = res.get('aspect', []) or []
            sentiments = res.get('sentiment', []) or []
            confidences = res.get('confidence', None) or res.get('probs', []) or []
            
            aspect_results = self._build_aspect_results(aspects, sentiments, confidences)
                
            parsed_batch.append(ReviewABSAResult(review_text=text, aspects=aspect_results))
            
        return parsed_batch


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
        
        aspect_lower = raw_aspect.lower().strip()

        # Check direct canonical name match first
        if aspect_lower in ASPECTS:
            return aspect_lower

        # Check if canonical name is substring of raw aspect
        # e.g. "battery life" contains "battery"
        for canonical, data in ASPECTS.items():
            if canonical in aspect_lower:
                return canonical

        # Check keywords from aspects.py
        # e.g. "cam" matches camera keywords, "mah" matches battery
        for canonical, data in ASPECTS.items():
            for keyword in data["keywords"]:
                if keyword in aspect_lower:
                    return canonical

        return "other"