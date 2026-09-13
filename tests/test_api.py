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