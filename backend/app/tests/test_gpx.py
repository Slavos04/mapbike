import pytest
from app.schemas import RoutePoint
from app.services.gpx_service import GPXService

def test_generate_gpx():
    points = [
        RoutePoint(lat=50.0614, lon=19.9365, elevation_m=220.0, distance_m=0.0),
        RoutePoint(lat=50.0650, lon=19.9400, elevation_m=225.0, distance_m=550.0)
    ]
    xml_str = GPXService.generate_gpx(points, route_name="Test Route")
    assert "<?xml" in xml_str or "<gpx" in xml_str
    assert "Test Route" in xml_str
    assert "50.0614" in xml_str
    assert "220.0" in xml_str
