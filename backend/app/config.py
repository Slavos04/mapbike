import os
from pydantic import BaseModel

class Settings(BaseModel):
    PROJECT_NAME: str = "MapBike - Minimal Gradient Route Planner"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    
    # Elevation Provider Options: "open-meteo", "open-elevation", "synthetic"
    DEFAULT_ELEVATION_PROVIDER: str = os.getenv("ELEVATION_PROVIDER", "open-meteo")
    
    # OSM Routing Defaults
    DEFAULT_NUM_VARIANTS: int = 5
    MAX_VARIANTS: int = 10
    MIN_VARIANTS: int = 1
    
    # Max Detour Percentage compared to shortest path (e.g. 100 = 100% longer, i.e., 2x shortest length)
    DEFAULT_MAX_DETOUR_PERCENT: float = 100.0
    
    # Cache directory for OSMnx graphs
    CACHE_DIR: str = os.path.join(os.path.dirname(__file__), "..", "cache")

settings = Settings()
