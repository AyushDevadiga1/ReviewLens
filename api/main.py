"""
main.py
ReviewLens FastAPI application entry point.
Run: uvicorn api.main:app --reload --port 8000
Swagger UI: http://localhost:8000/docs

Architecture note:
  No live scraping. Reviews are pre-loaded from offline datasets via
  data_ingestion/loaders/. The API queries PostgreSQL and runs the
  ML pipeline (fake detection + ABSA) on pre-loaded reviews.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from api.routers import analyze, compare, trends, health, products, jobs
from api.services.fake_detector import FakeReviewDetector
from api.services.absa import ABSAInference
from api.middleware.auth import APIKeyMiddleware
from api.middleware.rate_limit import RateLimitMiddleware
from db.session import create_tables
import time

START_TIME = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown lifecycle.
    ML models are loaded once here — not per request — so inference is fast.

    TODO on startup:
      1. create_tables()
         Why: ensures DB schema exists on first boot without needing a
         manual Alembic migration run during development.

      2. app.state.fake_detector = FakeReviewDetector()
         Why: loading the sklearn model + vectorizer from disk takes ~1s.
         Doing it at startup means the first /analyze request is fast.
         Stored on app.state so routers retrieve it via request.app.state.

      3. app.state.absa = ABSAInference()
         Why: same reason — PyABSA model loading is expensive (~5s).
         Load once, reuse for all requests.

      4. app.state.start_time = time.time()
         Why: used by /health to report uptime accurately.

      5. print("ReviewLens API ready")
         print(f"  Fake detector: {app.state.fake_detector.model_version}")
         print(f"  ABSA: multilingual checkpoint")

    TODO on shutdown:
      1. No explicit DB cleanup needed — SQLAlchemy connection pool
         cleans up automatically when the process exits.
      2. If you add background tasks later, cancel them here.
    """
    
    # startup
    create_tables()
    app.state.fake_detector = FakeReviewDetector()
    app.state.absa = ABSAInference()
    app.state.start_time = time.time()
    print("ReviewLens API ready")
    print(f"  Fake detector: {app.state.fake_detector.model_version}")
    yield
    # shutdown — nothing needed


# Self-documentation (Swagger/ReDoc/schema) is an attack-surface map —
# off unless explicitly enabled. Local dev: ENABLE_DOCS=true in .env.
_DOCS_ENABLED = os.getenv("ENABLE_DOCS", "false").lower() in ("true", "1", "yes")

app = FastAPI(
    title="ReviewLens API",
    description=(
        "Aspect-Based Sentiment Analysis for E-Commerce Reviews. "
        "Reviews are pre-loaded from offline datasets (McAuley Amazon + Flipkart CSV). "
        "POST /analyze to run the ML pipeline. GET /products/search to discover available products."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if _DOCS_ENABLED else None,
    redoc_url="/redoc" if _DOCS_ENABLED else None,
    openapi_url="/openapi.json" if _DOCS_ENABLED else None,
)

# CORS — allow all origins for development
# Restrict to your Streamlit URL in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth + rate limiting. Starlette runs LAST-added FIRST, so auth checks
# each request before it can consume rate-limit budget. Both skip /health.
app.add_middleware(RateLimitMiddleware, max_requests=100, window_seconds=60)
app.add_middleware(APIKeyMiddleware)

# Register all routers
app.include_router(analyze.router)
app.include_router(compare.router)
app.include_router(trends.router)
app.include_router(health.router)
app.include_router(products.router)   # new — product discovery
app.include_router(jobs.router)       # async analyze jobs + polling
