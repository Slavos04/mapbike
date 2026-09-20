import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schemas import RouteRequest, Coordinate

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_empty_request_rejects():
    # Pusty wniosek bez punktów odrzucany
    response = client.post("/api/route", json={})
    assert response.status_code in (400, 422)

def test_route_api_endpoint_valid():
    payload = {
        "start": {"lat": 50.0614, "lon": 19.9365},
        "end": {"lat": 50.0680, "lon": 19.9500},
        "num_variants": 5,
        "max_detour_percent": 100.0,
        "elevation_provider": "synthetic"
    }
    response = client.post("/api/route", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "variants" in data
    assert len(data["variants"]) == 5
    assert data["start_address"] is not None
    assert data["end_address"] is not None

def test_geocode_endpoint():
    response = client.get("/api/geocode?query=Krakow")
    assert response.status_code == 200
    data = response.json()
    assert "lat" in data
    assert "lon" in data
