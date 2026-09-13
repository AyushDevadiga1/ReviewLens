"""
health.py
GET /health — system status for uptime checks.
GET /metrics — Prometheus-compatible metrics (added during the monitoring phase).
"""

from fastapi import APIRouter, Depends
from api.services.fake_detector import FakeReviewDetector
from api.services.absa import ABSAInference
from api.schemas.response import HealthResponse
import time

router = APIRouter(prefix="/health", tags=["Health"])

# Set in api/main.py at startup
START_TIME = time.time()


@router.get("/", response_model=HealthResponse)
async def health(
    fake_detector: FakeReviewDetector = Depends(),
    absa: ABSAInference = Depends()
):
    """
    Report service health: model versions, DB connectivity, uptime.

    TODO:
      1. status = "healthy" if DB connects and both models are loaded
      2. fake_detector_version from FakeReviewDetector.model_version
      3. absa_model_version from ABSAInference
      4. database_connected = probe DB with a SELECT 1
      5. uptime_seconds = time.time() - START_TIME
      6. Build and return HealthResponse
    """
    pass


@router.get("/metrics")
async def metrics():
    """
    Expose Prometheus-compatible metrics.

    TODO:
      1. Add prometheus-client to requirements
      2. Instrument api.main with counters/histograms:
         - requests per endpoint
         - response latency (p50/p90/p99)
         - model inference time
         - fake review detection rate
      3. Return generate_latest(REGISTRY) as plain text
    """
    pass