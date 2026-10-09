"""
health.py
GET /health — system status and sanity check.
GET /metrics — Prometheus-compatible metrics (Phase 6).

The /health endpoint also reports total products and reviews in DB
as a quick sanity check that data_ingestion loaders have been run.
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from api.schemas.response import HealthResponse
from db.session import get_db
from db.models import Product, Review
import time

router = APIRouter(prefix="/health", tags=["Health"])


def get_fake_detector(request: Request):
    return request.app.state.fake_detector


def get_absa(request: Request):
    return request.app.state.absa


@router.get("/", response_model=HealthResponse)
async def health(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Report system health. Used by Docker health checks and monitoring.

    TODO:
      1. Probe DB connectivity:
         try:
             db.execute(text("SELECT 1"))
             database_connected = True
         except Exception:
             database_connected = False

      2. Count products and reviews — quick data sanity check:
         total_products = db.query(func.count(Product.id)).scalar()
         total_reviews  = db.query(func.count(Review.id)).scalar()
         Why: if these are 0, the data_ingestion loaders haven't run yet —
         useful to surface this immediately rather than getting confusing
         404s from /analyze.

      3. Retrieve model versions from app.state:
         fake_detector = request.app.state.fake_detector
         absa = request.app.state.absa
         status = "healthy" if database_connected and total_reviews > 0
                  else "degraded"

      4. Return HealthResponse(
             status=status,
             fake_detector_version=fake_detector.model_version,
             absa_model_version="pyabsa-multilingual",
             database_connected=database_connected,
             uptime_seconds=time.time() - request.app.state.start_time,
             total_products_in_db=total_products,
             total_reviews_in_db=total_reviews
         )
    """
    
    try:
        db.execute(text("SELECT 1"))
        database_connected = True
        total_products = db.query(func.count(Product.id)).scalar()
        total_reviews  = db.query(func.count(Review.id)).scalar()
    except Exception:
        database_connected = False
        total_products = 0
        total_reviews  = 0

    fake_detector = request.app.state.fake_detector
    
    status = "healthy" if database_connected and total_reviews > 0 else "degraded"
    
    return HealthResponse(
        status=status,
        fake_detector_version=fake_detector.model_version,
        absa_model_version="pyabsa-multilingual",
        database_connected=database_connected,
        uptime_seconds=time.time() - request.app.state.start_time,
        total_products_in_db=total_products,
        total_reviews_in_db=total_reviews
    )


@router.get("/metrics")
async def metrics(
    request : Request
):
    """
    Expose Prometheus-compatible metrics.
    Implemented in Phase 6 after the core pipeline works.

    TODO (Phase 6):
      1. pip install prometheus-fastapi-instrumentator
      2. Add Instrumentator().instrument(app).expose(app) in main.py lifespan
      3. This endpoint then auto-returns Prometheus text format
         — no manual implementation needed with the instrumentator
    """

    metrics_data = getattr(request.app.state,"prometheus_metrics",None)
    
    if metrics_data is None:
        return {
            "Message" : "Metrics endpoint not implemented yet"
        }
    
    return metrics_data
