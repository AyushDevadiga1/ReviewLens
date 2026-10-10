"""
test_api.py
Integration tests for ReviewLens API endpoints.
Uses FastAPI TestClient — no live server needed.
Run: pytest tests/test_api.py -v

Isolation: temp SQLite DB + fixed API key are forced BEFORE importing
the app, so tests never touch real data and never depend on .env.
"""

import os
import tempfile
from datetime import datetime

_TMP = tempfile.mkdtemp(prefix="rl_pytest_api_")
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP}/api_test.db"
os.environ["API_KEY_SECRET"] = "test-secret-key"

import pytest  # noqa: E402 — env isolation must precede app import
from fastapi.testclient import TestClient  # noqa: E402

from api.main import app  # noqa: E402
from db.session import SessionLocal, create_tables  # noqa: E402
from db.models import Product, Review  # noqa: E402

KEY = {"X-API-Key": "test-secret-key"}

create_tables()
_seed = SessionLocal()
_product = Product(name="Test Phone", platform="amazon", category="phone")
_seed.add(_product)
_seed.flush()
_seed.add_all([
    Review(product_id=_product.id, reviewer_name="t1",
           review_text="battery lasts two days, excellent camera quality indeed",
           rating=5.0, review_date=datetime(2026, 1, 8), review_length=58),
    Review(product_id=_product.id, reviewer_name="t2",
           review_text="the camera is awful and battery drains fast every day",
           rating=2.0, review_date=datetime(2026, 1, 15), review_length=57),
])
_seed.commit()
PID = _product.id
_seed.close()


@pytest.fixture(scope="module")
def client():
    # Lifespan (tables + both models) runs on context entry.
    with TestClient(app) as c:
        yield c


class TestHealthEndpoint:

    def test_health_returns_200(self, client):
        """
        GET /health should return 200 with status "healthy".
        """
        response = client.get("/health/")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_health_includes_model_versions(self, client):
        """
        Health response must include fake_detector_version and absa_model_version.
        """
        body = client.get("/health/").json()
        assert "fake_detector_version" in body
        assert "absa_model_version" in body


class TestAnalyzeEndpoint:

    def test_analyze_with_review_text(self, client):
        """
        POST /analyze with review_text should return aspect sentiments.
        """
        response = client.post("/analyze/", json={
            "review_text": "Battery life is excellent but camera quality is disappointing",
            "rating": 4.0,
        }, headers=KEY)
        assert response.status_code == 200
        data = response.json()
        assert "aspects" in data
        for item in data["aspects"]:
            assert "aspect" in item and "sentiment_label" in item

    def test_analyze_requires_input(self, client):
        """
        POST /analyze with neither product_name nor review_text → 422.
        """
        assert client.post("/analyze/", json={}, headers=KEY).status_code == 422

    def test_analyze_review_text_minimum_length(self, client):
        """
        review_text shorter than 20 chars should return 422.
        """
        response = client.post("/analyze/", json={
            "review_text": "too short", "rating": 5.0}, headers=KEY)
        assert response.status_code == 422


class TestFakeDetector:

    LONG_FAKE = (
        "This is absolutely the most amazing product I have ever purchased "
        "in my entire life. The quality exceeded all my expectations and the "
        "customer service was phenomenal. I recommend it to everyone I know "
        "wholeheartedly!"
    )
    LONG_GENUINE = (
        "Battery lasts two full days of heavy use with screen on most of the "
        "time. Camera struggles a bit in low light but daylight shots are "
        "sharp. Charging is fast, speakers are average. Overall solid for "
        "the price."
    )

    def test_obvious_fake_review(self, client):
        """
        A long, elaborate glowing review should be flagged as fake.
        """
        response = client.post("/analyze/", json={
            "review_text": self.LONG_FAKE, "rating": 5.0}, headers=KEY)
        assert response.status_code == 200
        assert response.json()["review_filter"]["fake_count"] == 1

    def test_detailed_genuine_review(self, client):
        """
        A detailed review mentioning specific product features should be genuine.
        """
        response = client.post("/analyze/", json={
            "review_text": self.LONG_GENUINE, "rating": 4.0}, headers=KEY)
        assert response.status_code == 200
        assert response.json()["review_filter"]["fake_count"] == 0
