from pydantic import BaseModel, Field
from typing import List, Optional

class Coordinate(BaseModel):
    lat: float
    lon: float

class AddressSearchRequest(BaseModel):
    query: str

class AddressSearchResponse(BaseModel):
    lat: float
    lon: float
    display_name: str

class RouteRequest(BaseModel):
    start: Optional[Coordinate] = None
    end: Optional[Coordinate] = None
    start_address: Optional[str] = None
    end_address: Optional[str] = None
    num_variants: int = Field(default=5, ge=1, le=10)
    max_detour_percent: float = Field(default=100.0, ge=10.0, le=200.0)
    elevation_provider: str = Field(default="open-meteo")
    route_type: str = Field(default="cycleway", description="cycleway | all_public")
    avoid_highways: bool = Field(default=True, description="Unikaj dróg o dużym ruchu ulicznym (krajowych/wojewódzkich)")

class ElevationPoint(BaseModel):
    distance_m: float
    elevation_m: float
    grade_percent: float

class RoutePoint(BaseModel):
    lat: float
    lon: float
    elevation_m: float
    distance_m: float

class RouteVariant(BaseModel):
    id: int
    name: str
    color: str
    total_distance_km: float
    avg_grade_percent: float
    max_grade_percent: float
    total_ascent_m: float
    total_descent_m: float
    elevation_profile: List[ElevationPoint]
    geometry: List[RoutePoint]
    gpx_data: str
    is_within_limit: bool

class RouteResponse(BaseModel):
    start: Coordinate
    end: Coordinate
    start_address: Optional[str] = None
    end_address: Optional[str] = None
    shortest_distance_km: float
    max_allowed_distance_km: float
    variants: List[RouteVariant]
