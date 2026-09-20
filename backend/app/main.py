"""
MapBike Backend - Główny Punkt Wejścia Aplikacji FastAPI

Ten moduł definiuje trasowanie HTTP (REST API), konfigurację CORS,
montowanie interfejsu użytkownika (frontend static files) oraz punkt kontroli stanu zdrowia (health check).
"""

import os
import logging
from fastapi import FastAPI, HTTPException, Response, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.schemas import RouteRequest, RouteResponse, AddressSearchRequest, AddressSearchResponse
from app.services.routing_service import RoutingService
from app.services.osm_service import OSMService
from app.services.gpx_service import GPXService

# Konfiguracja globalnego systemu logowania dla backendu
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("mapbike")

# Inicjalizacja głównej aplikacji FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="REST API do wyznaczania optymalnych tras rowerowych z minimalnym nachyleniem, geokodowaniem i kontrolą dystansu."
)

# Konfiguracja nagłówków CORS pozwalająca na zapytania z dowolnego źródła (np. z aplikacji webowej)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health_check():
    """
    Endpoint sprawdzający stan zdrowia serwera (używany przez Docker i Nginx).
    """
    return {
        "status": "healthy",
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION
    }

@app.get("/api/geocode", response_model=AddressSearchResponse)
def geocode_address(query: str = Query(..., description="Tekst adresu do wyszukania")):
    """
    Przekształca tekst podanego adresu (np. nazwa ulicy/miasta) na współrzędne geograficzne szerokość/długość (lat/lon).
    Używa silnika Nominatim z serwisu OpenStreetMap.
    """
    result = OSMService.geocode_address(query)
    if not result:
        raise HTTPException(status_code=404, detail=f"Nie znaleziono adresu: {query}")
    return AddressSearchResponse(lat=result[0], lon=result[1], display_name=result[2])

@app.get("/api/reverse-geocode")
def reverse_geocode(lat: float, lon: float):
    """
    Reverse Geocoding: Przekształca kliknięte współrzędne (lat, lon) na czytelny adres (miejscowość, ulica i numer).
    """
    address = OSMService.reverse_geocode(lat, lon)
    return {"lat": lat, "lon": lon, "address": address}

@app.post("/api/route", response_model=RouteResponse)
def calculate_route(request: RouteRequest):
    """
    Główny punkt API przeliczający trasy rowerowe.
    Pobiera punkty Start i Meta, pobiera profil wysokościowy Open-Meteo i generuje od 1 do 10 wariantów tras.
    Wariant #1 gwarantuje minimalne nachylenie (najmniej wzniesień), a opcja `avoid_highways` omija drogi krajowe DK.
    """
    try:
        logger.info(f"Zapytanie o trasę: Start({request.start_address or request.start}) -> Meta({request.end_address or request.end})")
        response = RoutingService.calculate_routes(request)
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Błąd podczas wyznaczania trasy: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Błąd serwera podczas obliczania trasy: {str(e)}")

@app.post("/api/gpx")
def download_gpx(request: RouteRequest, variant_index: int = 0):
    """
    Generuje i zwraca plik w formacie .gpx dla wybranego wariantu trasy.
    Umożliwia wgranie śladu bezpośrednio do komputera rowerowego Garmin / Wahoo / Strava.
    """
    try:
        route_response = RoutingService.calculate_routes(request)
        if not route_response.variants or variant_index >= len(route_response.variants):
            raise HTTPException(status_code=404, detail="Wariant trasy nie istnieje.")
            
        selected_variant = route_response.variants[variant_index]
        gpx_content = selected_variant.gpx_data
        
        filename = f"trasa_mapbike_{selected_variant.name.replace(' ', '_').lower()}.gpx"
        return Response(
            content=gpx_content,
            media_type="application/gpx+xml",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Błąd pobierania GPX: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Montowanie statycznych plików HTML/JS/CSS frontendu z katalogu frontend/public
frontend_public_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "public"))
if os.path.exists(frontend_public_dir):
    app.mount("/", StaticFiles(directory=frontend_public_dir, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    # Uruchomienie serwera deweloperskiego na porcie 8000
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
