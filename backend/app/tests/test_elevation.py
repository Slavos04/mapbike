import pytest
from app.services.elevation_service import (
    SyntheticElevationProvider,
    OpenMeteoElevationProvider,
    ResilientElevationProvider
)

def test_synthetic_elevation_provider():
    provider = SyntheticElevationProvider()
    coords = [(50.0614, 19.9365), (50.0680, 19.9500)]
    elevations = provider.get_elevations(coords)
    assert len(elevations) == 2
    assert all(isinstance(e, float) for e in elevations)
    assert all(e > 0 for e in elevations)

def test_resilient_elevation_provider():
    provider = ResilientElevationProvider(primary_provider_name="open-meteo")
    coords = [(50.0614, 19.9365)]
    elevations = provider.get_elevations(coords)
    assert len(elevations) == 1
    assert isinstance(elevations[0], float)
