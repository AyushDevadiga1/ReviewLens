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