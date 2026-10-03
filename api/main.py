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
from api.routers import analyze, compare, trends, health, products
from api.services.fake_detector import FakeReviewDetector
from api.services.absa import ABSAInference
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
    yield
    # shutdown


app = FastAPI(
    title="ReviewLens API",
    description=(
        "Aspect-Based Sentiment Analysis for E-Commerce Reviews. "
        "Reviews are pre-loaded from offline datasets (McAuley Amazon + Flipkart CSV). "
        "POST /analyze to run the ML pipeline. GET /products/search to discover available products."
    ),
    version="1.0.0",
    lifespan=lifespan
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

# TODO: uncomment when auth is implemented
# app.add_middleware(APIKeyMiddleware)

# TODO: uncomment when rate limiting is implemented
# app.add_middleware(RateLimitMiddleware, max_requests=100, window_seconds=60)

# Register all routers
app.include_router(analyze.router)
app.include_router(compare.router)
app.include_router(trends.router)
app.include_router(health.router)
app.include_router(products.router)   # new — product discovery
