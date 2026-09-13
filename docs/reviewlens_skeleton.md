# ReviewLens — Skeleton Code Reference
**Production-Level Aspect-Based Sentiment Analysis for E-Commerce Reviews**
Mumbai University C-Scheme | Natural Language Processing Mini-Project
B.E. Computer Science (AI & ML) | Bharat College of Engineering

---

## Quick Context

**What ReviewLens does:**
Scrapes e-commerce product reviews, filters out fake ones using a trained classifier,
runs Aspect-Based Sentiment Analysis on genuine reviews, stores everything in PostgreSQL,
and serves results through a FastAPI REST API with a Streamlit comparison dashboard.

**The three-stage pipeline:**
1. Fake Review Filter — DistilBERT / Logistic Regression classifier
2. ABSA — PyABSA with BERT, extracts per-aspect sentiment scores
3. Comparative Dashboard — side-by-side aspect comparison across products

**Stack:** Python 3.11, FastAPI, PostgreSQL, SQLAlchemy, PyABSA, scikit-learn,
          DistilBERT, BeautifulSoup, Streamlit, Plotly, MLflow, Docker, pytest

**Cost:** Rs. 0 | **GPU:** Not needed for inference | **Internet:** Needed for scraping only

---

## Repository Structure

```
reviewlens/
│
├── api/
│   ├── main.py                  # FastAPI app entry point
│   ├── routers/
│   │   ├── analyze.py           # POST /analyze endpoint
│   │   ├── compare.py           # GET /compare endpoint
│   │   ├── trends.py            # GET /trends endpoint
│   │   └── health.py            # GET /health, GET /metrics
│   ├── schemas/
│   │   ├── request.py           # Pydantic input models
│   │   └── response.py          # Pydantic output models
│   ├── services/
│   │   ├── fake_detector.py     # Fake review classifier wrapper
│   │   ├── absa.py              # PyABSA inference wrapper
│   │   └── aggregator.py        # Aspect score aggregation
│   └── middleware/
│       ├── auth.py              # API key validation
│       └── rate_limit.py        # Request rate limiter
│
├── ml/
│   ├── fake_review/
│   │   ├── train.py             # Train fake review classifier
│   │   ├── evaluate.py          # Evaluation metrics and report
│   │   └── model/               # Saved model artifacts
│   ├── absa/
│   │   ├── inference.py         # PyABSA inference wrapper
│   │   └── aspects.py           # Aspect category definitions
│   └── mlflow_tracking.py       # Experiment logging helpers
│
├── scraper/
│   ├── amazon.py                # Amazon India review scraper
│   ├── flipkart.py              # Flipkart review scraper
│   └── cleaner.py               # Raw text preprocessing
│
├── db/
│   ├── models.py                # SQLAlchemy ORM models
│   ├── session.py               # Database connection
│   └── migrations/              # Alembic migration files
│
├── frontend/
│   ├── app.py                   # Streamlit entry point
│   └── pages/
│       ├── single.py            # Single product analysis page
│       ├── compare.py           # Product comparison page
│       └── trends.py            # Sentiment drift timeline page
│
├── tests/
│   ├── test_api.py              # API endpoint tests
│   ├── test_fake_detector.py    # Fake classifier tests
│   ├── test_absa.py             # ABSA inference tests
│   └── test_scraper.py          # Scraper tests
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

---

## File 1 — `db/models.py`

**Purpose:** SQLAlchemy ORM models. Defines all database tables.
Build this first — everything else depends on the schema.

```python
"""
models.py
SQLAlchemy ORM models for ReviewLens.
Five core tables: products, reviews, fake_scores, aspect_sentiments, api_logs.
Run migrations with: alembic upgrade head
"""

from sqlalchemy import (
    Column, Integer, String, Float, Boolean,
    DateTime, Text, ForeignKey, JSON
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Product(Base):
    """
    Stores product metadata scraped from e-commerce URLs.
    One row per unique product.
    """
    __tablename__ = "products"

    # TODO: define columns
    # id          — Integer, primary key, autoincrement
    # name        — String(500), not null
    # url         — String(1000), unique, not null
    # platform    — String(50) e.g. "amazon", "flipkart"
    # category    — String(200) e.g. "smartphones"
    # scraped_at  — DateTime, default=datetime.utcnow
    # reviews     — relationship to Review (one product → many reviews)
    pass


class Review(Base):
    """
    Stores individual reviews scraped from product pages.
    One row per review.
    """
    __tablename__ = "reviews"

    # TODO: define columns
    # id                — Integer, primary key, autoincrement
    # product_id        — Integer, ForeignKey("products.id"), not null
    # review_text       — Text, not null
    # rating            — Float (1.0 to 5.0)
    # reviewer_name     — String(200)
    # review_date       — DateTime
    # verified_purchase — Boolean, default=False
    # review_length     — Integer (computed: len(review_text))
    # scraped_at        — DateTime, default=datetime.utcnow
    # product           — relationship back to Product
    # fake_score        — relationship to FakeScore (one review → one score)
    # aspect_sentiments — relationship to AspectSentiment (one review → many)
    pass


class FakeScore(Base):
    """
    Stores fake review detection results for each review.
    One row per review (1:1 with Review).
    """
    __tablename__ = "fake_scores"

    # TODO: define columns
    # id             — Integer, primary key, autoincrement
    # review_id      — Integer, ForeignKey("reviews.id"), unique, not null
    # is_fake        — Boolean, not null
    # confidence     — Float (0.0 to 1.0)
    # model_version  — String(50) e.g. "logistic_v1", "distilbert_v2"
    # scored_at      — DateTime, default=datetime.utcnow
    # review         — relationship back to Review
    pass


class AspectSentiment(Base):
    """
    Stores per-aspect sentiment for each genuine review.
    Multiple rows per review (one per aspect found).
    """
    __tablename__ = "aspect_sentiments"

    # TODO: define columns
    # id             — Integer, primary key, autoincrement
    # review_id      — Integer, ForeignKey("reviews.id"), not null
    # aspect         — String(100) e.g. "battery", "camera", "display"
    # sentiment      — String(20) e.g. "positive", "negative", "neutral"
    # confidence     — Float (0.0 to 1.0)
    # model_version  — String(50)
    # scored_at      — DateTime, default=datetime.utcnow
    # review         — relationship back to Review
    pass


class ApiLog(Base):
    """
    Logs every API request for monitoring and rate limiting.
    """
    __tablename__ = "api_logs"

    # TODO: define columns
    # id           — Integer, primary key, autoincrement
    # endpoint     — String(200) e.g. "/analyze"
    # method       — String(10) e.g. "POST"
    # api_key_hash — String(64) — hashed API key (never store plain text)
    # status_code  — Integer
    # latency_ms   — Float
    # requested_at — DateTime, default=datetime.utcnow
    pass
```

---

## File 2 — `db/session.py`

**Purpose:** Database connection and session management.

```python
"""
session.py
SQLAlchemy database connection setup.
Reads DATABASE_URL from environment variables.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base


# Read from environment — set in .env or docker-compose.yml
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://reviewlens:password@localhost:5432/reviewlens"
)


def get_engine():
    """
    Create SQLAlchemy engine.
    TODO:
      return create_engine(DATABASE_URL, echo=False)
      echo=True for debugging (logs all SQL), False for production
    """
    pass


def get_session_factory():
    """
    Create session factory bound to engine.
    TODO:
      engine = get_engine()
      return sessionmaker(autocommit=False, autoflush=False, bind=engine)
    """
    pass


def create_tables():
    """
    Create all tables defined in models.py.
    Run once on first startup.
    TODO:
      engine = get_engine()
      Base.metadata.create_all(bind=engine)
    """
    pass


def get_db():
    """
    FastAPI dependency — yields a database session per request.
    Closes session after request completes (success or error).
    TODO:
      SessionLocal = get_session_factory()
      db = SessionLocal()
      try:
          yield db
      finally:
          db.close()
    """
    pass
```

---

## File 3 — `scraper/cleaner.py`

**Purpose:** Clean raw scraped review text before ML processing.

```python
"""
cleaner.py
Text preprocessing for scraped reviews.
Cleans HTML artifacts, normalises unicode, handles Hinglish text.
"""

import re
import unicodedata
from typing import Optional


def clean_review_text(raw_text: str) -> Optional[str]:
    """
    Clean a single review string.

    Steps:
    1. Strip leading/trailing whitespace
    2. Remove HTML tags if any slipped through the scraper
    3. Normalise unicode (NFC) — handles accented characters and emoji
    4. Replace multiple whitespace with single space
    5. Return None if resulting text is shorter than 10 characters
       (too short to be a meaningful review)

    Args:
        raw_text: raw review string from scraper

    Returns:
        Cleaned string, or None if text is too short to process

    TODO:
      1. raw_text.strip()
      2. re.sub(r'<[^>]+>', '', text) — remove HTML tags
      3. unicodedata.normalize('NFC', text)
      4. re.sub(r'\s+', ' ', text) — collapse whitespace
      5. return None if len(text) < 10 else text
    """
    pass


def extract_review_metadata(raw_review: dict) -> dict:
    """
    Extract and type-cast structured metadata from a raw scraped review dict.

    Args:
        raw_review: dict from scraper with keys:
                    text, rating, reviewer, date, verified

    Returns:
        Clean dict with:
        - review_text: str (cleaned)
        - rating: float (1.0-5.0, None if missing)
        - reviewer_name: str (truncated to 200 chars)
        - review_date: datetime or None
        - verified_purchase: bool
        - review_length: int (len of cleaned text)

    TODO:
      1. Call clean_review_text() on raw_review["text"]
      2. Cast rating to float, clamp between 1.0 and 5.0
      3. Parse date string to datetime object (handle multiple formats)
      4. Return structured dict
    """
    pass
```

---

## File 4 — `scraper/amazon.py`

**Purpose:** Scrape reviews from Amazon India product pages.

```python
"""
amazon.py
Amazon India review scraper.
Scrapes up to max_pages of reviews for a given product URL.

IMPORTANT: Add delays between requests (time.sleep(2-3 seconds))
to avoid rate limiting. Respect robots.txt.
"""

import time
import requests
from bs4 import BeautifulSoup
from typing import List, Optional
from cleaner import clean_review_text, extract_review_metadata


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-IN,en;q=0.9",
}


def get_product_name(soup: BeautifulSoup) -> str:
    """
    Extract product name from Amazon product page.
    TODO:
      Look for: soup.find("span", {"id": "productTitle"})
      Strip whitespace from .get_text()
      Return "Unknown Product" if not found
    """
    pass


def parse_review_page(soup: BeautifulSoup) -> List[dict]:
    """
    Parse all reviews from one page of Amazon reviews.

    Each review block on Amazon has:
    - data-hook="review" — the review container div
    - data-hook="review-body" — the review text
    - data-hook="review-star-rating" — star rating
    - data-hook="review-date" — date string
    - data-hook="avp-badge" — verified purchase badge

    Returns:
        List of raw review dicts (not yet cleaned)

    TODO:
      1. Find all divs with data-hook="review"
      2. For each: extract text, rating, date, verified status
      3. Return list of raw dicts
    """
    pass


def scrape_product_reviews(
    product_url: str,
    max_pages: int = 5
) -> dict:
    """
    Scrape up to max_pages of reviews for a product URL.

    Args:
        product_url: Amazon India product URL
        max_pages: maximum number of review pages to scrape

    Returns:
        dict with:
        - product_name: str
        - platform: "amazon"
        - url: product_url
        - reviews: list of cleaned review dicts

    TODO:
      1. Extract ASIN from URL using regex: r'/dp/([A-Z0-9]{10})'
      2. Build review pages URL:
         f"https://www.amazon.in/product-reviews/{asin}/?pageNumber={page}"
      3. For each page 1..max_pages:
         a. GET request with HEADERS
         b. Parse with BeautifulSoup
         c. Call parse_review_page()
         d. Call extract_review_metadata() on each raw review
         e. time.sleep(2) between pages — avoid rate limiting
      4. Return structured dict
    """
    pass
```

---

## File 5 — `ml/fake_review/train.py`

**Purpose:** Train the fake review classifier.
Run once to produce the saved model artifact.

```python
"""
train.py
Train fake review classifier on Deceptive Opinion Spam Corpus.
Dataset: https://myleott.com/op-spam.html (free, academic)

Two model options:
  - LogisticRegression on TF-IDF features (fast, 84% accuracy)
  - DistilBERT fine-tuned (slower, 91% accuracy)

For submission: use LogisticRegression (no GPU needed)
For portfolio: upgrade to DistilBERT

Run: python ml/fake_review/train.py
"""

import os
import json
import pickle
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import mlflow
from mlflow_tracking import log_experiment


def load_deceptive_opinion_corpus(data_dir: str) -> tuple:
    """
    Load the Deceptive Opinion Spam Corpus.
    Dataset has two classes: deceptive (fake) and truthful (genuine).
    Folder structure: data/op_spam_v1.4/negative_polarity/deceptive_from_MTurk/
                      data/op_spam_v1.4/negative_polarity/truthful_from_Web/

    Returns:
        (texts, labels) where labels: 1=fake, 0=genuine

    TODO:
      1. Walk data_dir looking for .txt files
      2. Read each file's text
      3. Assign label 1 if path contains "deceptive", 0 if "truthful"
      4. Return (list of texts, list of labels)
    """
    pass


def build_features(texts: list) -> tuple:
    """
    Convert raw texts to TF-IDF feature matrix.

    Returns:
        (X_matrix, fitted_vectorizer)

    TODO:
      vectorizer = TfidfVectorizer(
          max_features=10000,
          ngram_range=(1, 2),  # unigrams and bigrams
          sublinear_tf=True,   # apply log normalization
          stop_words='english'
      )
      X = vectorizer.fit_transform(texts)
      return X, vectorizer
    """
    pass


def train_classifier(X_train, y_train) -> LogisticRegression:
    """
    Train Logistic Regression classifier.

    TODO:
      model = LogisticRegression(
          max_iter=1000,
          C=1.0,
          solver='lbfgs',
          multi_class='ovr'
      )
      model.fit(X_train, y_train)
      return model
    """
    pass


def save_model(model, vectorizer, output_dir: str = "ml/fake_review/model"):
    """
    Save trained model and vectorizer to disk.
    Both are needed at inference time.

    TODO:
      os.makedirs(output_dir, exist_ok=True)
      pickle.dump(model, open(f"{output_dir}/classifier.pkl", "wb"))
      pickle.dump(vectorizer, open(f"{output_dir}/vectorizer.pkl", "wb"))
      Save metadata JSON: model_type, accuracy, trained_at, feature_count
    """
    pass


def main():
    """
    Full training pipeline with MLflow tracking.

    TODO:
      1. Load corpus: texts, labels = load_deceptive_opinion_corpus("data/op_spam")
      2. Train/test split: 80/20, stratified
      3. Build features: X_train, vectorizer = build_features(train_texts)
         Transform test: X_test = vectorizer.transform(test_texts)
      4. Train: model = train_classifier(X_train, y_train)
      5. Evaluate: predictions = model.predict(X_test)
         Print classification_report(y_test, predictions)
      6. Log to MLflow: accuracy, precision, recall, F1
      7. Save model: save_model(model, vectorizer)
    """
    pass


if __name__ == "__main__":
    main()
```

---

## File 6 — `api/services/fake_detector.py`

**Purpose:** Load saved model and run fake review inference at request time.

```python
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
```

---

## File 7 — `ml/absa/aspects.py`

**Purpose:** Define the aspects to extract. Central config — used by ABSA and dashboard.

```python
"""
aspects.py
Aspect category definitions for ReviewLens.
These are the dimensions measured per product.
Add or remove aspects here — changes propagate everywhere.
"""

# Core aspects for electronics / smartphones
# Each aspect has: canonical name, display name, keywords
# Keywords help with aspect matching if needed

ASPECTS = {
    "battery": {
        "display_name": "Battery Life",
        "keywords": ["battery", "charge", "charging", "mah", "drain", "life"],
        "icon": "🔋"
    },
    "camera": {
        "display_name": "Camera",
        "keywords": ["camera", "photo", "picture", "selfie", "lens", "megapixel"],
        "icon": "📷"
    },
    "display": {
        "display_name": "Display",
        "keywords": ["screen", "display", "amoled", "lcd", "brightness", "resolution"],
        "icon": "🖥️"
    },
    "build_quality": {
        "display_name": "Build Quality",
        "keywords": ["build", "quality", "plastic", "glass", "metal", "premium", "solid"],
        "icon": "🏗️"
    },
    "value": {
        "display_name": "Value for Money",
        "keywords": ["price", "value", "worth", "expensive", "cheap", "budget", "money"],
        "icon": "💰"
    },
    "delivery": {
        "display_name": "Delivery",
        "keywords": ["delivery", "shipping", "courier", "arrived", "packaging", "days"],
        "icon": "📦"
    },
    "performance": {
        "display_name": "Performance",
        "keywords": ["fast", "slow", "lag", "performance", "processor", "smooth", "speed"],
        "icon": "⚡"
    },
}

ASPECT_NAMES = list(ASPECTS.keys())
ASPECT_DISPLAY_NAMES = {k: v["display_name"] for k, v in ASPECTS.items()}
```

---

## File 8 — `ml/absa/inference.py`

**Purpose:** PyABSA inference wrapper. Runs ABSA on genuine reviews.

```python
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
```

---

## File 9 — `api/services/aggregator.py`

**Purpose:** Aggregate per-review aspect sentiments into per-product scores.

```python
"""
aggregator.py
Aggregates aspect sentiment scores across all reviews of a product.
Produces the final scores shown in the comparison dashboard.
"""

import numpy as np
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict


def sentiment_to_score(sentiment: str, confidence: float) -> float:
    """
    Convert sentiment label + confidence to a numeric score (0.0 to 10.0).

    Mapping:
      positive: base score 7.0 + confidence * 3.0  → range [7.0, 10.0]
      neutral:  base score 5.0 + (confidence - 0.5) → range [4.5, 5.5]
      negative: base score 3.0 - confidence * 3.0  → range [0.0, 3.0]

    TODO: implement the mapping above and clamp result to [0.0, 10.0]
    """
    pass


def aggregate_product_aspects(
    aspect_sentiments: List[dict]
) -> Dict[str, dict]:
    """
    Aggregate all aspect sentiments for one product into summary scores.

    Args:
        aspect_sentiments: list of dicts from DB with keys:
                           aspect, sentiment, confidence, review_date

    Returns:
        Dict keyed by aspect name, value is:
        {
          "mean_score": float (0.0-10.0),
          "review_count": int,
          "positive_pct": float,
          "negative_pct": float,
          "neutral_pct": float,
          "sentiment_label": str ("positive"/"negative"/"neutral")
        }

    TODO:
      1. Group by aspect using defaultdict(list)
      2. For each aspect:
         a. Compute mean score using sentiment_to_score()
         b. Count positive/negative/neutral occurrences
         c. Compute percentages
         d. Assign overall sentiment_label based on mean_score:
            ≥ 7.0 → positive, ≤ 4.0 → negative, else → neutral
      3. Return dict
    """
    pass


def compute_winner_per_aspect(
    product_scores: Dict[str, Dict[str, dict]]
) -> Dict[str, str]:
    """
    Determine which product wins on each aspect.

    Args:
        product_scores: {product_name: {aspect: {"mean_score": float, ...}}}

    Returns:
        {aspect: winning_product_name}

    TODO:
      For each aspect, find product with highest mean_score.
      Handle ties by returning first alphabetically.
    """
    pass


def compute_weekly_trend(
    aspect_sentiments: List[dict],
    aspect: str,
    weeks: int = 8
) -> List[dict]:
    """
    Compute weekly sentiment trend for one aspect of one product.

    Args:
        aspect_sentiments: list of dicts with aspect, sentiment, confidence, review_date
        aspect: which aspect to filter for
        weeks: how many weeks of history to return

    Returns:
        List of dicts: [{"week": "2026-W01", "mean_score": float, "count": int}]

    TODO:
      1. Filter aspect_sentiments to only the requested aspect
      2. Group by ISO week: datetime.isocalendar()[1]
      3. Compute mean score per week
      4. Return sorted list of weekly dicts (oldest first)
    """
    pass
```

---

## File 10 — `api/schemas/request.py`

**Purpose:** Pydantic models for API request validation.
FastAPI uses these to auto-validate incoming JSON and generate Swagger docs.

```python
"""
request.py
Pydantic request schemas.
FastAPI validates all incoming requests against these automatically.
Invalid requests are rejected with 422 Unprocessable Entity.
"""

from pydantic import BaseModel, HttpUrl, validator, Field
from typing import Optional, List


class AnalyzeRequest(BaseModel):
    """
    Request body for POST /analyze
    Either product_url OR review_text must be provided, not both.
    """
    product_url: Optional[HttpUrl] = Field(
        None,
        description="Full URL of Amazon India or Flipkart product page",
        example="https://www.amazon.in/dp/B09G3J7G1P"
    )
    review_text: Optional[str] = Field(
        None,
        min_length=20,
        max_length=5000,
        description="Single review text to analyze directly"
    )
    max_pages: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Max review pages to scrape (only used with product_url)"
    )

    # TODO: add validator that ensures either product_url or review_text is provided
    # @validator('review_text', always=True)
    # def check_one_input_provided(cls, v, values):
    #     if not v and not values.get('product_url'):
    #         raise ValueError('Either product_url or review_text must be provided')
    #     return v


class CompareRequest(BaseModel):
    """
    Query parameters for GET /compare
    Accepts 2-3 product URLs for side-by-side comparison.
    """
    product_urls: List[HttpUrl] = Field(
        ...,
        min_items=2,
        max_items=3,
        description="List of 2-3 product URLs to compare"
    )

    # TODO: validator to ensure all URLs are from supported platforms
    # Supported: amazon.in, flipkart.com


class TrendsRequest(BaseModel):
    """
    Query parameters for GET /trends
    """
    product_id: int = Field(..., description="Product ID from database")
    aspect: str = Field(
        ...,
        description="Aspect to get trend for",
        example="battery"
    )
    weeks: int = Field(
        default=8,
        ge=1,
        le=52,
        description="Number of weeks of history to return"
    )
```

---

## File 11 — `api/schemas/response.py`

**Purpose:** Pydantic models for API response serialisation.

```python
"""
response.py
Pydantic response schemas.
FastAPI serialises all responses using these automatically.
Also used for Swagger UI documentation.
"""

from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime


class AspectScore(BaseModel):
    aspect: str
    display_name: str
    mean_score: float          # 0.0 to 10.0
    review_count: int
    positive_pct: float        # 0.0 to 100.0
    negative_pct: float
    neutral_pct: float
    sentiment_label: str       # "positive", "negative", "neutral"


class FakeFilterSummary(BaseModel):
    total_scraped: int
    fake_count: int
    genuine_count: int
    fake_percentage: float


class AnalyzeResponse(BaseModel):
    product_name: str
    product_url: str
    platform: str
    fake_filter: FakeFilterSummary
    aspects: List[AspectScore]
    analyzed_at: datetime


class ProductComparison(BaseModel):
    product_name: str
    product_url: str
    aspects: List[AspectScore]


class WinnerSummary(BaseModel):
    aspect: str
    display_name: str
    winner: str
    winning_score: float


class CompareResponse(BaseModel):
    products: List[ProductComparison]
    winners: List[WinnerSummary]      # which product wins per aspect
    compared_at: datetime


class WeeklyDataPoint(BaseModel):
    week: str                  # ISO format e.g. "2026-W01"
    mean_score: float
    review_count: int


class TrendsResponse(BaseModel):
    product_name: str
    aspect: str
    display_name: str
    trend: List[WeeklyDataPoint]
    overall_direction: str     # "improving", "declining", "stable"


class HealthResponse(BaseModel):
    status: str                # "healthy" or "degraded"
    fake_detector_version: str
    absa_model_version: str
    database_connected: bool
    uptime_seconds: float
```

---

## File 12 — `api/routers/analyze.py`

**Purpose:** POST /analyze endpoint. The main entry point.

```python
"""
analyze.py
POST /analyze — scrape product and run full analysis pipeline.
Steps: scrape → clean → fake filter → ABSA → aggregate → store → respond
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from api.schemas.request import AnalyzeRequest
from api.schemas.response import AnalyzeResponse
from api.services.fake_detector import FakeReviewDetector
from api.services.absa import ABSAInference
from api.services.aggregator import aggregate_product_aspects
from db.session import get_db
from scraper.amazon import scrape_product_reviews
from scraper.flipkart import scrape_flipkart_reviews

router = APIRouter(prefix="/analyze", tags=["Analysis"])


@router.post("/", response_model=AnalyzeResponse)
async def analyze_product(
    request: AnalyzeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    fake_detector: FakeReviewDetector = Depends(),
    absa: ABSAInference = Depends()
):
    """
    Analyze a product URL or single review text.

    Pipeline:
    1. If product_url: scrape reviews from e-commerce platform
    2. Clean all review texts
    3. Run fake review detection on all reviews
    4. Filter to genuine reviews only
    5. Run ABSA on genuine reviews
    6. Aggregate aspect scores
    7. Store everything in PostgreSQL
    8. Return AnalyzeResponse

    TODO:
      1. Detect platform from URL (amazon vs flipkart)
      2. Call appropriate scraper
      3. Call fake_detector.predict_batch() on all reviews
      4. Call fake_detector.filter_genuine() to get genuine reviews
      5. Call absa.analyze_batch() on genuine review texts
      6. Store product, reviews, fake_scores, aspect_sentiments to DB
      7. Call aggregate_product_aspects() to compute summary scores
      8. Build and return AnalyzeResponse
      9. Use background_tasks.add_task() for DB writes (non-blocking)

    Raise HTTPException(400) if URL is not from supported platform.
    Raise HTTPException(404) if no reviews found.
    Raise HTTPException(422) if neither product_url nor review_text provided.
    """
    pass
```

---

## File 13 — `api/routers/compare.py`

**Purpose:** GET /compare — side-by-side aspect comparison of multiple products.

```python
"""
compare.py
GET /compare — compare two or three products side by side.
Returns aspect scores for each product and winner per aspect.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from api.schemas.request import CompareRequest
from api.schemas.response import CompareResponse
from api.services.aggregator import compute_winner_per_aspect
from db.session import get_db
from db.models import Product, AspectSentiment

router = APIRouter(prefix="/compare", tags=["Comparison"])


@router.get("/", response_model=CompareResponse)
async def compare_products(
    request: CompareRequest = Depends(),
    db: Session = Depends(get_db)
):
    """
    Compare 2-3 products on aspect sentiment scores.

    TODO:
      1. For each URL in request.product_urls:
         a. Look up product in DB by URL
         b. If not found: trigger analysis (call analyze_product internally)
            or raise HTTPException(404, "Product not yet analyzed")
         c. Fetch all AspectSentiment records for this product from DB
         d. Call aggregate_product_aspects() to get scores
      2. Call compute_winner_per_aspect() across all products
      3. Build CompareResponse with per-product aspects and winner summary
      4. Return response
    """
    pass
```

---

## File 14 — `api/main.py`

**Purpose:** FastAPI application entry point. Registers all routers and middleware.

```python
"""
main.py
ReviewLens FastAPI application.
Run: uvicorn api.main:app --reload --port 8000
Swagger UI: http://localhost:8000/docs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from api.routers import analyze, compare, trends, health
from api.middleware.auth import APIKeyMiddleware
from api.middleware.rate_limit import RateLimitMiddleware
from api.services.fake_detector import FakeReviewDetector
from api.services.absa import ABSAInference
from db.session import create_tables
import time

# Track startup time for /health uptime metric
START_TIME = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown events.
    Load ML models once at startup — not per request.

    TODO on startup:
      1. create_tables() — ensure DB schema exists
      2. Load FakeReviewDetector — store on app.state
      3. Load ABSAInference — store on app.state
      4. Print "ReviewLens ready" with model versions

    TODO on shutdown:
      1. Close DB connections gracefully
    """
    # startup
    yield
    # shutdown


app = FastAPI(
    title="ReviewLens API",
    description="Aspect-Based Sentiment Analysis for E-Commerce Reviews",
    version="1.0.0",
    lifespan=lifespan
)

# TODO: add CORS middleware — allow all origins for development
# app.add_middleware(CORSMiddleware, allow_origins=["*"], ...)

# TODO: add API key middleware
# app.add_middleware(APIKeyMiddleware)

# TODO: add rate limit middleware
# app.add_middleware(RateLimitMiddleware, max_requests=100, window_seconds=60)

# Register routers
app.include_router(analyze.router)
app.include_router(compare.router)
app.include_router(trends.router)
app.include_router(health.router)
```

---

## File 15 — `frontend/app.py`

**Purpose:** Streamlit dashboard entry point.

```python
"""
app.py
ReviewLens Streamlit dashboard.
Run: streamlit run frontend/app.py

Three pages:
  1. Single Product — analyze one URL
  2. Compare Products — side-by-side comparison
  3. Sentiment Trends — aspect drift over time
"""

import streamlit as st

st.set_page_config(
    page_title="ReviewLens",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Sidebar navigation ────────────────────────────────────────────────
st.sidebar.title("ReviewLens")
st.sidebar.caption("AI-powered e-commerce review analysis")

page = st.sidebar.radio(
    "Navigate",
    ["Single Product", "Compare Products", "Sentiment Trends"]
)

# TODO: import and call the appropriate page renderer
# if page == "Single Product":
#     from pages.single import render_single_page
#     render_single_page()
# elif page == "Compare Products":
#     from pages.compare import render_compare_page
#     render_compare_page()
# elif page == "Sentiment Trends":
#     from pages.trends import render_trends_page
#     render_trends_page()
```

---

## File 16 — `frontend/pages/compare.py`

**Purpose:** Product comparison page — the main demo slide.

```python
"""
compare.py
Side-by-side product comparison page.
This is the most important page — the demo moment.

Shows:
  - Radar chart comparing all products on all aspects
  - Table with aspect scores per product
  - Winner column highlighting which product wins per aspect
  - Summary: "Product A wins on: Battery, Value. Product B wins on: Camera"
"""

import streamlit as st
import plotly.graph_objects as go
import requests
from typing import List


API_BASE = "http://localhost:8000"


def render_radar_chart(product_data: List[dict], aspects: List[str]):
    """
    Render a Plotly radar chart comparing products across aspects.

    Args:
        product_data: [{"name": str, "scores": {aspect: float}}]
        aspects: list of aspect names for radar axes

    TODO:
      1. Create go.Figure()
      2. For each product, add go.Scatterpolar trace:
         r = [scores[a] for a in aspects]
         theta = [display_name for a in aspects]
         fill = 'toself'
         name = product name
      3. Update layout: polar, showlegend=True
      4. st.plotly_chart(fig, use_container_width=True)
    """
    pass


def render_comparison_table(compare_response: dict):
    """
    Render side-by-side aspect score table with winner highlighting.

    TODO:
      1. Build pandas DataFrame:
         rows = aspects, columns = product names + "Winner"
      2. For each cell: show mean_score with sentiment emoji
         (≥7: 🟢, 4-7: 🟡, <4: 🔴)
      3. Winner column: show product name that won this aspect
      4. st.dataframe() with styling
    """
    pass


def render_compare_page():
    """
    Main comparison page renderer.

    TODO:
      1. st.title("Compare Products")
      2. st.text_input() for each of up to 3 product URLs
      3. "Compare" button
      4. On click:
         a. POST to /analyze for each URL (or GET /compare with all URLs)
         b. Call render_radar_chart()
         c. Call render_comparison_table()
         d. Show winner summary: "Product A wins on 3 of 7 aspects"
      5. Show fake review stats: "Filtered X fake reviews across all products"
    """
    pass
```

---

## File 17 — `tests/test_api.py`

**Purpose:** FastAPI endpoint tests. Run before every commit.

```python
"""
test_api.py
Integration tests for ReviewLens API endpoints.
Uses FastAPI TestClient — no live server needed.
Run: pytest tests/test_api.py -v
"""

import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


class TestHealthEndpoint:

    def test_health_returns_200(self):
        """
        GET /health should return 200 with status "healthy".
        TODO: response = client.get("/health")
              assert response.status_code == 200
              assert response.json()["status"] == "healthy"
        """
        pass

    def test_health_includes_model_versions(self):
        """
        Health response must include fake_detector_version and absa_model_version.
        TODO: assert both keys exist in response.json()
        """
        pass


class TestAnalyzeEndpoint:

    def test_analyze_with_review_text(self):
        """
        POST /analyze with review_text should return aspect sentiments.
        TODO:
          response = client.post("/analyze", json={
              "review_text": "Battery life is excellent but camera quality is disappointing"
          })
          assert response.status_code == 200
          data = response.json()
          assert "aspects" in data
          assert len(data["aspects"]) > 0
        """
        pass

    def test_analyze_requires_input(self):
        """
        POST /analyze with neither product_url nor review_text should return 422.
        TODO: assert client.post("/analyze", json={}).status_code == 422
        """
        pass

    def test_analyze_review_text_minimum_length(self):
        """
        review_text shorter than 20 chars should return 422.
        TODO: assert short text returns 422
        """
        pass


class TestFakeDetector:

    def test_obvious_fake_review(self):
        """
        A generic 5-word glowing review should be classified as fake.
        TODO: post obviously fake review, assert is_fake=True in response.
        """
        pass

    def test_detailed_genuine_review(self):
        """
        A detailed review mentioning specific product features should be genuine.
        TODO: post detailed review, assert is_fake=False in response.
        """
        pass
```

---

## File 18 — `requirements.txt`

```
# API
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
python-multipart==0.0.6
slowapi==0.1.9
python-jose[cryptography]==3.3.0

# Database
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
alembic==1.13.0

# ML — Fake Review Detection
scikit-learn==1.3.2
transformers==4.35.2
torch==2.1.1

# ML — ABSA
pyabsa==2.3.3

# Scraping
requests==2.31.0
beautifulsoup4==4.12.2
lxml==4.9.3

# Experiment Tracking
mlflow==2.8.1

# Dashboard
streamlit==1.28.2
plotly==5.18.0
pandas==2.1.3

# Utilities
python-dotenv==1.0.0
numpy==1.24.4

# Testing
pytest==7.4.3
httpx==0.25.2
```

---

## File 19 — `docker-compose.yml`

```yaml
version: '3.8'

services:

  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://reviewlens:password@db:5432/reviewlens
      - MLFLOW_TRACKING_URI=http://mlflow:5000
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - ./ml:/app/ml          # mount trained models
    command: uvicorn api.main:app --host 0.0.0.0 --port 8000

  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=reviewlens
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=reviewlens
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U reviewlens"]
      interval: 5s
      timeout: 5s
      retries: 5

  mlflow:
    image: python:3.11-slim
    ports:
      - "5000:5000"
    command: >
      bash -c "pip install mlflow && mlflow server
               --host 0.0.0.0 --port 5000
               --backend-store-uri sqlite:///mlflow.db"
    volumes:
      - mlflow_data:/mlflow

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "8501:8501"
    depends_on:
      - api
    command: streamlit run frontend/app.py --server.port 8501

volumes:
  postgres_data:
  mlflow_data:
```

---

## File 20 — `.env.example`

```bash
# Copy to .env and fill in values
# Never commit .env to git

# Database
DATABASE_URL=postgresql://reviewlens:password@localhost:5432/reviewlens

# API Security
API_KEY_SECRET=your-secret-key-here-change-this

# MLflow
MLFLOW_TRACKING_URI=http://localhost:5000

# Model paths
FAKE_DETECTOR_MODEL_DIR=ml/fake_review/model
ABSA_CHECKPOINT=multilingual

# Scraping
MAX_SCRAPE_PAGES=5
SCRAPE_DELAY_SECONDS=2
```

---

## Implementation Order

Build in this exact order. Do not skip ahead.

```
PHASE 1 — Data Foundation (Week 1 Days 1-2)
  db/models.py          → define all tables
  db/session.py         → database connection
  scraper/cleaner.py    → text cleaning
  scraper/amazon.py     → scrape reviews

PHASE 2 — ML Models (Week 1 Days 3-7)
  ml/fake_review/train.py     → train classifier
  ml/absa/aspects.py          → define aspects
  ml/absa/inference.py        → ABSA wrapper

PHASE 3 — Services (Week 2 Days 1-3)
  api/services/fake_detector.py  → load model + inference
  api/services/aggregator.py     → score aggregation

PHASE 4 — API (Week 2 Days 4-7)
  api/schemas/request.py   → Pydantic inputs
  api/schemas/response.py  → Pydantic outputs
  api/routers/analyze.py   → POST /analyze
  api/routers/compare.py   → GET /compare
  api/routers/health.py    → GET /health
  api/main.py              → register everything

PHASE 5 — Frontend (Week 3 Days 1-4)
  frontend/pages/single.py   → single product page
  frontend/pages/compare.py  → comparison page
  frontend/app.py            → navigation

PHASE 6 — Docker + MLflow (Week 3 Days 5-7)
  Dockerfile
  docker-compose.yml
  ml/mlflow_tracking.py

PHASE 7 — Tests (Week 4)
  tests/test_api.py
  tests/test_fake_detector.py
```

---

## The One Rule

**Do not build the frontend until POST /analyze returns correct JSON in Swagger UI.**

Test every phase in this order:
1. `pytest tests/` — all tests pass
2. Swagger UI at `localhost:8000/docs` — manually test each endpoint
3. Frontend only after both above pass

A backend that works with a broken dashboard is recoverable in an hour.
A polished dashboard with a broken backend fails in the viva.
