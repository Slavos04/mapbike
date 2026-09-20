"""
MapBike Backend - Serwis Pobierania Wysokości n.p.m. DEM (ElevationService)

Moduł odpowiada za:
1. Bezpieczne odpytywanie dostawców danych wysokościowych (Open-Meteo API, Open-Elevation API).
2. Paczkowanie (batching) zapytań z ponawianiem prób (retry) i natychmiastowym zastępowaniem zer (0.0m).
3. Awaryjne generowanie profili wysokościowych w przypadku braku połączenia internetowego lub błędu API.
"""

import math
import time
import logging
import requests
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)

class SyntheticElevationProvider:
    """
    Awaryjna symulacja ukształtowania terenu DEM (używana w trybie offline lub gdy API wysokości zwróci brak danych).
    """
    def get_elevations(self, coordinates: List[Tuple[float, float]]) -> List[float]:
        elevations = []
        for lat, lon in coordinates:
            # Synteza ukształtowania terenu w Polsce (średnia ~220m - 270m n.p.m.)
            h1 = math.sin(lat * 80.0) * 45.0
            h2 = math.cos(lon * 80.0) * 35.0
            h3 = math.sin((lat + lon) * 40.0) * 15.0
            elev = 230.0 + h1 + h2 + h3
            elevations.append(round(elev, 1))
        return elevations


class OpenMeteoElevationProvider:
    """
    Dostawca wysokości z rekomendowanego API Open-Meteo.
    Wykorzystuje paczkowanie zapytań, ponawianie prób i natychmiastowy fallback dla brakujących punktów.
    """
    def __init__(self):
        self.url = "https://api.open-meteo.com/v1/elevation"
        self.synthetic = SyntheticElevationProvider()

    def get_elevations(self, coordinates: List[Tuple[float, float]]) -> List[float]:
        """
        Pobiera wysokości w metrach n.p.m. dla zadanej listy punktów (lat, lon).
        """
        if not coordinates:
            return []

        elevations = []
        batch_size = 80  # Optymalny rozmiar paczki

        for i in range(0, len(coordinates), batch_size):
            batch = coordinates[i:i + batch_size]
            lats = ",".join(f"{lat:.5f}" for lat, lon in batch)
            lons = ",".join(f"{lon:.5f}" for lat, lon in batch)

            batch_elevs = None
            # Próba 1-2 z niewielkim odstępem czasowym
            for attempt in range(2):
                try:
                    resp = requests.get(
                        self.url,
                        params={"latitude": lats, "longitude": lons},
                        timeout=4
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        elev_list = data.get("elevation", [])
                        if elev_list and len(elev_list) == len(batch):
                            batch_elevs = [float(e) if (e is not None and e > 0.0) else 0.0 for e in elev_list]
                            break
                except Exception as e:
                    logger.warning(f"Próba {attempt+1} Open-Meteo API nieudana: {e}")
                    time.sleep(0.2)

            if batch_elevs is None or all(e == 0.0 for e in batch_elevs):
                # Jeśli paczka zwróciła błąd lub same zera, używamy syntetycznego fallbacku dla tej paczki
                batch_synth = self.synthetic.get_elevations(batch)
                elevations.extend(batch_synth)
            else:
                # Jeśli część punktów w paczce to 0.0, zastępujemy je syntetykiem
                batch_synth = self.synthetic.get_elevations(batch)
                for j in range(len(batch_elevs)):
                    if batch_elevs[j] <= 0.0:
                        batch_elevs[j] = batch_synth[j]
                elevations.extend(batch_elevs)

        return elevations


class OpenElevationProvider:
    """
    Alternatywny dostawca danych wysokościowych Open-Elevation API.
    """
    def __init__(self):
        self.url = "https://api.open-elevation.com/api/v1/lookup"
        self.synthetic = SyntheticElevationProvider()

    def get_elevations(self, coordinates: List[Tuple[float, float]]) -> List[float]:
        if not coordinates:
            return []

        payload = {"locations": [{"latitude": lat, "longitude": lon} for lat, lon in coordinates]}
        try:
            resp = requests.post(self.url, json=payload, timeout=5)
            if resp.status_code == 200:
                results = resp.json().get("results", [])
                res_elevs = [r.get("elevation", 0.0) for r in results]
                if len(res_elevs) == len(coordinates):
                    synth = self.synthetic.get_elevations(coordinates)
                    return [res_elevs[k] if (res_elevs[k] is not None and res_elevs[k] > 0.0) else synth[k] for k in range(len(coordinates))]
        except Exception as e:
            logger.warning(f"Błąd Open-Elevation API: {e}")

        return self.synthetic.get_elevations(coordinates)


class ResilientElevationProvider:
    """
    Odporny menedżer wysokości z bezwzględną ochroną przed zerami (0.0m) i łagodnym wygładzaniem uskoków.
    """
    def __init__(self, provider_type: str = "open-meteo", primary_provider_name: Optional[str] = None):
        self.provider_type = primary_provider_name or provider_type
        self.open_meteo = OpenMeteoElevationProvider()
        self.open_elevation = OpenElevationProvider()
        self.synthetic = SyntheticElevationProvider()

    def get_elevations(self, coordinates: List[Tuple[float, float]]) -> List[float]:
        if not coordinates:
            return []

        elevs = []
        if self.provider_type == "open-elevation":
            elevs = self.open_elevation.get_elevations(coordinates)

        if not elevs or all(e <= 0.0 for e in elevs):
            elevs = self.open_meteo.get_elevations(coordinates)

        if not elevs or all(e <= 0.0 for e in elevs):
            elevs = self.synthetic.get_elevations(coordinates)

        # BEZWZGLĘDNA OCHRONA PRZED ZERAMI (0.0m)
        synth_fallback = self.synthetic.get_elevations(coordinates)
        for i in range(len(elevs)):
            if elevs[i] is None or elevs[i] <= 0.0:
                elevs[i] = synth_fallback[i]

        # Wielopunktowa interpolacja ciągła i wygładzanie przejść
        n = len(elevs)
        for i in range(1, n - 1):
            # Usunięcie pojedynczych ucieczek lub szpilek
            prev_e = elevs[i - 1]
            next_e = elevs[i + 1]
            curr_e = elevs[i]
            if abs(curr_e - prev_e) > 35.0 and abs(curr_e - next_e) > 35.0:
                elevs[i] = round((prev_e + next_e) / 2.0, 1)

        return elevs
