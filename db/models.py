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