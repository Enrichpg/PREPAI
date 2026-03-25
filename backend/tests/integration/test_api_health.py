"""Integration tests for the FastAPI application."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock



@pytest.fixture
def client():
    """Create a test client with mocked DB and ML model."""
    with patch("app.db.database.async_engine"), \
         patch("app.db.database.AsyncSessionLocal"), \
         patch("app.services.ml.comfort_model.get_comfort_model") as mock_model:
        mock_model.return_value.model = None
        mock_model.return_value.version = "test_v1"
        mock_model.return_value.get_metrics.return_value = {
            "mae": 5.2, "rmse": 7.1, "r2": 0.82,
            "training_samples": 10000,
            "validation_samples": 2000,
            "feature_importances": {"temperature": 0.25},
        }
        from app.main import app
        with TestClient(app) as c:
            yield c


class TestHealthEndpoints:
    def test_health_check(self, client):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "PREPAI" in data["app"]

    def test_docs_available(self, client):
        response = client.get("/docs")
        assert response.status_code == 200


class TestRecommendationRequestValidation:
    def test_invalid_coordinates_rejected(self, client):
        payload = {
            "start_lat": 0.0,   # Outside A Coruña valid range
            "start_lon": 0.0,
            "date": "2024-06-15",
            "time_start": 7,
            "time_end": 9,
            "preferred_surface": "mixed",
            "preferred_elevation": "flat",
            "max_results": 5,
            "search_radius_km": 30,
        }
        with patch("app.api.routes.routes_api.get_db"):
            response = client.post("/api/v1/routes/recommend", json=payload)
        assert response.status_code == 422

    def test_time_range_validation(self, client):
        payload = {
            "start_lat": 43.36,
            "start_lon": -8.41,
            "date": "2024-06-15",
            "time_start": 25,   # Invalid hour
            "time_end": 9,
            "preferred_surface": "mixed",
            "preferred_elevation": "flat",
            "max_results": 5,
            "search_radius_km": 30,
        }
        with patch("app.api.routes.routes_api.get_db"):
            response = client.post("/api/v1/routes/recommend", json=payload)
        assert response.status_code == 422
