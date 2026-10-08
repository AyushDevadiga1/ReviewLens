from sqlalchemy import (
    Column, Integer, String, Float, Boolean,
    DateTime, Text, ForeignKey, UniqueConstraint
)
from typing import Optional
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, mapped_column, Mapped
from datetime import datetime

Base = declarative_base()


class Product(Base):
    """One row per unique product. Platform + name must be unique together."""
    __tablename__ = "products"

    id       : Mapped[int] = mapped_column(Integer, primary_key=True)
    name     : Mapped[str] = mapped_column(String(500), nullable=False)
    platform : Mapped[str] = mapped_column(String(50))
    category : Mapped[str] = mapped_column(String(200),nullable=True)

    reviews  : Mapped[list["Review"]] = relationship("Review", back_populates="product")

    __table_args__ = (
        UniqueConstraint("name", "platform", name="uq_product_name_platform"),
    )


class Review(Base):
    """One row per review. review_date nullable to support datasets with no date column."""
    __tablename__ = "reviews"

    id                : Mapped[int]      = mapped_column(Integer, primary_key=True)
    product_id        : Mapped[int]      = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    reviewer_name     : Mapped[str]      = mapped_column(String(200))
    review_text       : Mapped[str]      = mapped_column(Text, nullable=False)
    review_date       : Mapped[datetime] = mapped_column(DateTime, nullable=True)
    rating            : Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    verified_purchase : Mapped[bool]     = mapped_column(Boolean, default=False)
    review_length     : Mapped[int]      = mapped_column(Integer, nullable=True)

    product           : Mapped["Product"]            = relationship("Product", back_populates="reviews")
    fake_score        : Mapped["FakeScore"]          = relationship("FakeScore", back_populates="review", uselist=False)
    aspect_sentiments : Mapped[list["AspectSentiment"]] = relationship("AspectSentiment", back_populates="review")


class FakeScore(Base):
    """One row per review — 1:1 with Review."""
    __tablename__ = "fake_scores"

    id            : Mapped[int]      = mapped_column(Integer, primary_key=True)
    review_id     : Mapped[int]      = mapped_column(Integer, ForeignKey("reviews.id"), nullable=False, unique=True)
    is_fake       : Mapped[bool]     = mapped_column(Boolean, nullable=False)
    confidence    : Mapped[float]    = mapped_column(Float, nullable=False)
    model_version : Mapped[str]      = mapped_column(String(50))
    scored_at     : Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    review : Mapped["Review"] = relationship("Review", back_populates="fake_score")


class AspectSentiment(Base):
    """One row per aspect found per review. Multiple rows per review."""
    __tablename__ = "aspect_sentiments"

    id            : Mapped[int]      = mapped_column(Integer, primary_key=True)
    review_id     : Mapped[int]      = mapped_column(Integer, ForeignKey("reviews.id"), nullable=False)
    aspect        : Mapped[str]      = mapped_column(String(100))
    sentiment     : Mapped[str]      = mapped_column(String(20))
    confidence    : Mapped[float]    = mapped_column(Float)
    model_version : Mapped[str]      = mapped_column(String(50))
    scored_at     : Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    review : Mapped["Review"] = relationship("Review", back_populates="aspect_sentiments")


class ApiLog(Base):
    """One row per API request."""
    __tablename__ = "api_logs"

    id           : Mapped[int]      = mapped_column(Integer, primary_key=True)
    endpoint     : Mapped[str]      = mapped_column(String(200))
    method       : Mapped[str]      = mapped_column(String(10))
    api_key_hash : Mapped[str]      = mapped_column(String(64))
    status_code  : Mapped[int]      = mapped_column(Integer)
    latency_ms   : Mapped[float]    = mapped_column(Float)
    requested_at : Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)