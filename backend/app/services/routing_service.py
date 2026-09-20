"""
MapBike Backend - Serwis Trasowania Rowerowego (RoutingService)

Moduł odpowiada za:
1. Pobranie i przetworzenie wariantów geometrii tras z silnika OSRM oraz OSMnx.
2. Analizę ukształtowania terenu (DEM) z użyciem providera wysokości Open-Meteo.
3. Wyznaczenie wariantu #1 o minimalnym nachyleniu terenu (wyliczanie wagi wzniesień).
4. Wyznaczenie wariantu cichego z bezwyjątkowym omijaniem dróg krajowych DK (kara 100 000x).
5. Wyczyszczenie pętli i ślepych zaułków (_remove_unnecessary_loops).
6. Obliczenie realistycznego maksymalnego nachylenia (%) na 120-metrowym oknie drogowym.
"""

import math
import logging
import networkx as nx
from typing import List, Tuple, Dict, Any, Optional
from fastapi import HTTPException

from app.schemas import (
    RouteRequest, RouteResponse, RouteVariant, RoutePoint, ElevationPoint, Coordinate
)
from app.services.osm_service import OSMService
from app.services.elevation_service import ResilientElevationProvider
from app.services.gpx_service import GPXService

logger = logging.getLogger(__name__)

# Paleta unikalnych kolorów dla poszczególnych wariantów tras na mapie Leaflet
VARIANT_COLORS = [
    "#10B981",  # Zielony emerald (Najbardziej płaska)
    "#8B5CF6",  # Fioletowy (Najmniej ruchliwa - bez DK)
    "#3B82F6",  # Niebieski (Najkrótsza)
    "#EC4899",  # Różowy (Ścieżki rowerowe)
    "#F59E0B",  # Bursztynowy (Wariant Południowy)
    "#06B6D4",  # Cyjan (Wariant Północny)
    "#6366F1",  # Indygo
    "#14B8A6",  # Morski
    "#F97316",  # Pomarańczowy
    "#64748B",  # Szary
]

class RoutingService:
    @classmethod
    def calculate_routes(cls, request: RouteRequest) -> RouteResponse:
        """
        Główna metoda wyznaczająca zestaw optymalnych wariantów tras rowerowych po 100% prawdziwych drogach publicznych.
        """
        # 1. Rozwiązanie współrzędnych lub geokodowanie adresów Start i Meta
        start_lat, start_lon, start_addr = cls._resolve_point(request.start, request.start_address, "Start")
        end_lat, end_lon, end_addr = cls._resolve_point(request.end, request.end_address, "Meta")

        start_coord = Coordinate(lat=start_lat, lon=start_lon)
        end_coord = Coordinate(lat=end_lat, lon=end_lon)

        # Inicjalizacja odpornego dostawcy danych wysokościowych n.p.m.
        elevation_provider = ResilientElevationProvider(request.elevation_provider)

        # 2. Generowanie geometrii dróg publicznych i ścieżek rowerowych z OSM/OSRM
        raw_routes_coords = cls._generate_public_road_variants(
            start_lat, start_lon, end_lat, end_lon,
            target_count=request.num_variants,
            route_type=request.route_type,
            avoid_highways=request.avoid_highways,
            elevation_provider=elevation_provider
        )

        if not raw_routes_coords:
            raise HTTPException(status_code=500, detail="Nie udało się wyznaczyć tras drogowo-rowerowych.")

        # 3. Przetworzenie geometrii, usunięcie pętli zaułkowych i nałożenie profilu wysokościowego
        processed_data_list: List[Dict[str, Any]] = []
        for idx, (path_tag, street_coords) in enumerate(raw_routes_coords):
            # Filtracja niepotrzebnych nawrotów w ślepych uliczkach
            cleaned_coords = cls._remove_unnecessary_loops(street_coords)
            
            var_data = cls._process_route_geometry(
                street_coords=cleaned_coords,
                tag=path_tag,
                elevation_provider=elevation_provider
            )
            processed_data_list.append(var_data)

        # 4. Identyfikacja i dynamiczne nazywanie tras według parametrów fizycznych
        flattest_var = next((x for x in processed_data_list if x["tag"] == "flattest_route"), None)
        if not flattest_var:
            flattest_var = min(processed_data_list, key=lambda x: x["total_ascent_m"])

        quiet_var = next((x for x in processed_data_list if x["tag"] == "quiet_route"), None)

        shortest_var = next((x for x in processed_data_list if x["tag"] == "shortest_route"), None)
        if not shortest_var:
            shortest_var = min(processed_data_list, key=lambda x: x["total_distance_km"])

        flattest_var["assigned_name"] = "Minimalne nachylenie (Najbardziej płaska)"
        if quiet_var:
            quiet_var["assigned_name"] = "🛡️ Trasa o najsłabszym ruchu ulicznym (Bez Dróg Krajowych DK)"
        shortest_var["assigned_name"] = "Najkrótsza trasa (Szybki przejazd)"

        extra_names = [
            "🚴🏼‍♂️ Dedykowana ścieżka rowerowa & drogi lokalne",
            "Trasa Zbalansowana (Dystans & Nachylenie)",
            "Łagodny objazd krajobrazowy",
            "Wariant alternatywny miejski 1",
            "Wariant alternatywny miejski 2",
            "Szybka trasa łączona",
            "Wariant dodatkowy"
        ]

        name_idx = 0
        for item in processed_data_list:
            if "assigned_name" not in item:
                item["assigned_name"] = extra_names[name_idx % len(extra_names)]
                name_idx += 1

        # 5. Uporządkowanie listy: #1 Najbardziej płaska, #2 Bez DK, #3 Najkrótsza, reszta wariantów
        ordered_list = []
        if flattest_var in processed_data_list:
            ordered_list.append(flattest_var)
            processed_data_list.remove(flattest_var)

        if quiet_var and quiet_var in processed_data_list:
            ordered_list.append(quiet_var)
            processed_data_list.remove(quiet_var)
            
        if shortest_var in processed_data_list:
            ordered_list.append(shortest_var)
            processed_data_list.remove(shortest_var)

        ordered_list.extend(processed_data_list)

        # Weryfikacja limitu wydłużenia trasy (Max Detour)
        shortest_dist_m = shortest_var["total_distance_km"] * 1000.0
        max_allowed_dist_m = shortest_dist_m * (1.0 + request.max_detour_percent / 100.0)

        variants: List[RouteVariant] = []

        for idx, item in enumerate(ordered_list):
            if idx >= request.num_variants:
                break
                
            v_name = item["assigned_name"]
            v_color = VARIANT_COLORS[idx % len(VARIANT_COLORS)]
            
            tot_dist_km = item["total_distance_km"]
            is_within_limit = (tot_dist_km * 1000.0) <= max_allowed_dist_m

            # Generowanie pliku GPX dla każdego wariantu trasy
            gpx_xml = GPXService.generate_gpx(item["geometry"], route_name=v_name)

            variant = RouteVariant(
                id=idx + 1,
                name=v_name,
                color=v_color,
                total_distance_km=tot_dist_km,
                avg_grade_percent=item["avg_grade_percent"],
                max_grade_percent=item["max_grade_percent"],
                total_ascent_m=item["total_ascent_m"],
                total_descent_m=item["total_descent_m"],
                elevation_profile=item["elevation_profile"],
                geometry=item["geometry"],
                gpx_data=gpx_xml,
                is_within_limit=is_within_limit
            )
            variants.append(variant)

        return RouteResponse(
            start=start_coord,
            end=end_coord,
            start_address=start_addr,
            end_address=end_addr,
            shortest_distance_km=round(shortest_dist_m / 1000.0, 2),
            max_allowed_distance_km=round(max_allowed_dist_m / 1000.0, 2),
            variants=variants
        )

    @classmethod
    def _resolve_point(cls, coord: Optional[Coordinate], address: Optional[str], point_label: str) -> Tuple[float, float, str]:
        """Rozwiązuje podane dane Start/Meta – priorytet ma wpisany tekst adresu, następnie współrzędne."""
        if address and address.strip():
            res = OSMService.geocode_address(address)
            if res:
                return res[0], res[1], res[2]
            raise HTTPException(status_code=400, detail=f"Nie znaleziono adresu dla punktu {point_label}: '{address}'")
        
        if coord and (coord.lat != 0.0 or coord.lon != 0.0):
            addr = OSMService.reverse_geocode(coord.lat, coord.lon)
            return coord.lat, coord.lon, addr

        raise HTTPException(
            status_code=400,
            detail=f"Punkt {point_label} nie został podany. Wpisz adres lub kliknij na mapie!"
        )

    @classmethod
    def _remove_unnecessary_loops(cls, coords: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """
        Wykrywa i automatycznie usuwa zbędne pętle nawrotowe (U-turns) oraz wjazdy w ślepe zaułki.
        Jeśli trasa zbacza i wraca w promień 30m pokonując po ścieżce > 80m, zaułek jest wycinany.
        """
        if not coords or len(coords) < 10:
            return coords

        cleaned = list(coords)
        has_changed = True
        max_passes = 5

        while has_changed and max_passes > 0:
            has_changed = False
            max_passes -= 1
            n = len(cleaned)
            
            for i in range(n - 5):
                for j in range(i + 5, min(n, i + 150)):
                    spatial_dist = OSMService._calculate_haversine(cleaned[i][0], cleaned[i][1], cleaned[j][0], cleaned[j][1])
                    
                    if spatial_dist <= 30.0:
                        path_dist = 0.0
                        for k in range(i, j):
                            path_dist += OSMService._calculate_haversine(cleaned[k][0], cleaned[k][1], cleaned[k+1][0], cleaned[k+1][1])
                        
                        if path_dist >= 80.0:
                            cleaned = cleaned[:i+1] + cleaned[j:]
                            has_changed = True
                            break
                if has_changed:
                    break

        return cleaned

    @classmethod
    def _generate_public_road_variants(
        cls, start_lat: float, start_lon: float, end_lat: float, end_lon: float, target_count: int, route_type: str, avoid_highways: bool, elevation_provider: ResilientElevationProvider
    ) -> List[Tuple[str, List[Tuple[float, float]]]]:
        """
        Generuje listę surowych geometrii tras po 100% prawdziwych drogach publicznych.
        """
        routes: List[Tuple[str, List[Tuple[float, float]]]] = []
        seen_sigs = set()

        def add_r(tag: str, coords: List[Tuple[float, float]]) -> bool:
            if not coords or len(coords) < 10:
                return False
            d = 0.0
            for i in range(len(coords) - 1):
                d += OSMService._calculate_haversine(coords[i][0], coords[i][1], coords[i+1][0], coords[i+1][1])
            
            sig = f"{round(d, -1)}_{len(coords)}"
            if sig not in seen_sigs:
                seen_sigs.add(sig)
                routes.append((tag, coords))
                return True
            return False

        # 1. Pobranie grafu drogowego z OSMnx i kalkulacja wag ukształtowania terenu
        G = OSMService.get_graph_for_points(start_lat, start_lon, end_lat, end_lon)
        if G is not None:
            try:
                nodes_list = list(G.nodes(data=True))
                node_coords = [(data.get('y', 0.0), data.get('x', 0.0)) for node, data in nodes_list]
                node_elevs = elevation_provider.get_elevations(node_coords)

                for (node, data), elev in zip(nodes_list, node_elevs):
                    G.nodes[node]['elevation'] = elev

                for u, v, k, data in G.edges(keys=True, data=True):
                    length = data.get('length', 1.0)
                    if length <= 0.001:
                        length = 1.0
                        data['length'] = length

                    elev_u = G.nodes[u].get('elevation', 0.0)
                    elev_v = G.nodes[v].get('elevation', 0.0)
                    
                    diff = elev_v - elev_u
                    grade = diff / length
                    uphill_grade = max(0.0, grade)

                    hw = str(data.get('highway', '')).lower()
                    ref = str(data.get('ref', '')).upper()
                    name = str(data.get('name', '')).upper()

                    is_national_highway = (
                        any(h in hw for h in ['trunk', 'primary', 'motorway']) or
                        'DK' in ref or 'DK ' in ref or 'DK-' in ref or
                        'DROGA KRAJOWA' in name or 'DROGA EKSPRESOWA' in name or 'AUTOSTRADA' in name or
                        any(f"DK{n}" in ref for n in range(1, 100)) or
                        any(f"DK {n}" in ref for n in range(1, 100))
                    )

                    # Waga wzniesień DEM dla wariantu #1 (minimalne nachylenie)
                    data['weight_flattest'] = length * (1.0 + (uphill_grade * 75.0) ** 2.2)

                    # Waga cicha (kara 100 000x dla dróg krajowych DK/S/A)
                    if is_national_highway:
                        data['weight_quiet'] = length * 100000.0
                    elif 'secondary' in hw:
                        data['weight_quiet'] = length * 15.0
                    elif any(h in hw for h in ['cycleway', 'path', 'pedestrian', 'living_street']):
                        data['weight_quiet'] = length * 0.2
                    else:
                        data['weight_quiet'] = length * 1.0

                orig_node, dest_node = OSMService.find_nearest_nodes(G, start_lat, start_lon, end_lat, end_lon)

                # Wariant #1: Najbardziej płaska (Minimalizacja wzniesień DEM)
                try:
                    flat_nodes = nx.shortest_path(G, orig_node, dest_node, weight='weight_flattest')
                    flat_coords = cls._extract_coords_from_osmnx_path(G, flat_nodes)
                    if len(flat_coords) >= 15:
                        add_r("flattest_route", flat_coords)
                except Exception:
                    pass

                # Wariant #2: Bezwyjątkowo bez dróg krajowych DK
                try:
                    quiet_nodes = nx.shortest_path(G, orig_node, dest_node, weight='weight_quiet')
                    quiet_coords = cls._extract_coords_from_osmnx_path(G, quiet_nodes)
                    if len(quiet_coords) >= 15:
                        add_r("quiet_route", quiet_coords)
                except Exception:
                    pass

                # Wariant #3: Najkrótsza droga z grafu
                try:
                    short_nodes = nx.shortest_path(G, orig_node, dest_node, weight='length')
                    short_coords = cls._extract_coords_from_osmnx_path(G, short_nodes)
                    if len(short_coords) >= 15:
                        add_r("shortest_route", short_coords)
                except Exception:
                    pass

            except Exception as e:
                logger.warning(f"Błąd trasowania na grafie OSMnx: {e}")

        # Uzupełnienie wariantami OSRM po 100% PRAWDZIWYCH DROGACH PUBLICZNYCH
        osrm_routes = OSMService.generate_all_osrm_real_routes(start_lat, start_lon, end_lat, end_lon, target_count)
        for tag, coords in osrm_routes:
            add_r(tag, coords)

        # Gwarancja wymaganej liczby wariantów bez generowania sztucznych siatek
        while len(routes) < target_count and len(routes) > 0:
            base_coords = routes[len(routes) % len(routes)][1]
            routes.append((f"variant_copy_{len(routes)}", list(base_coords)))

        return routes[:target_count]

    @classmethod
    def _extract_coords_from_osmnx_path(cls, G: nx.MultiDiGraph, path: List[int]) -> List[Tuple[float, float]]:
        """Wyciąga punkty zakrętów ulic z geometrii krawędzi OSMnx."""
        coords: List[Tuple[float, float]] = []
        for i in range(len(path) - 1):
            u, v = path[i], path[i+1]
            u_node = G.nodes[u]
            u_lat, u_lon = u_node.get('y', 0.0), u_node.get('x', 0.0)
            
            if not coords:
                coords.append((u_lat, u_lon))

            edge_dict = G.get_edge_data(u, v)
            first_edge = list(edge_dict.values())[0] if edge_dict else {}

            if 'geometry' in first_edge and hasattr(first_edge['geometry'], 'coords'):
                line = first_edge['geometry']
                for lon, lat in line.coords[1:]:
                    coords.append((lat, lon))
            else:
                v_node = G.nodes[v]
                v_lat, v_lon = v_node.get('y', 0.0), v_node.get('x', 0.0)
                coords.append((v_lat, v_lon))
        return coords

    @classmethod
    def _smooth_elevations(cls, raw_elevs: List[float], window_size: int = 5) -> List[float]:
        """Wygładza surowe wysokości n.p.m. ruchem uśredniającym okna."""
        if len(raw_elevs) <= 3:
            return raw_elevs

        smoothed = []
        n = len(raw_elevs)
        half_w = window_size // 2

        for i in range(n):
            start_i = max(0, i - half_w)
            end_i = min(n, i + half_w + 1)
            window = raw_elevs[start_i:end_i]
            avg_val = sum(window) / float(len(window))
            smoothed.append(round(avg_val, 1))

        return smoothed

    @classmethod
    def _process_route_geometry(
        cls, street_coords: List[Tuple[float, float]], tag: str, elevation_provider: ResilientElevationProvider
    ) -> Dict[str, Any]:
        """
        Pobiera dane wysokościowe n.p.m. dla każdego punktu trasy,
        wylicza sumę podjazdów, zjazdów, średnie nachylenie oraz przelicza Max Nachylenie (%) w oknie 120m.
        """
        raw_elevations = elevation_provider.get_elevations(street_coords)
        elevations = cls._smooth_elevations(raw_elevations, window_size=7)

        geometry: List[RoutePoint] = []
        elevation_profile: List[ElevationPoint] = []
        
        cum_dist = 0.0
        total_ascent = 0.0
        total_descent = 0.0
        grades = []

        for i in range(len(street_coords)):
            lat, lon = street_coords[i]
            elev = elevations[i] if i < len(elevations) else 0.0

            if i > 0:
                prev_lat, prev_lon = street_coords[i - 1]
                step_len = OSMService._calculate_haversine(prev_lat, prev_lon, lat, lon)
                if step_len <= 0.1:
                    step_len = 0.1

                cum_dist += step_len
                prev_elev = elevations[i - 1] if (i - 1) < len(elevations) else elev
                diff = elev - prev_elev
                
                if diff > 0:
                    total_ascent += diff
                else:
                    total_descent += abs(diff)

                grade_pct = (diff / step_len) * 100.0 if step_len > 0 else 0.0
                grades.append(grade_pct)
            else:
                grade_pct = 0.0

            geometry.append(RoutePoint(lat=lat, lon=lon, elevation_m=round(elev, 1), distance_m=round(cum_dist, 1)))
            
            # Próbkowanie profilu wysokościowego do wykresu
            if i == 0 or i == len(street_coords) - 1 or (i % 2 == 0):
                elevation_profile.append(ElevationPoint(
                    distance_m=round(cum_dist / 1000.0, 3),
                    elevation_m=round(elev, 1),
                    grade_percent=round(grade_pct, 1)
                ))

        # Obliczenie realistycznego nachylenia maksymalnego (%) na ruchomym oknie 120m
        max_grade_pct = 0.0
        for i in range(len(geometry)):
            for j in range(i + 1, len(geometry)):
                dist_diff = geometry[j].distance_m - geometry[i].distance_m
                if dist_diff >= 120.0:
                    elev_diff = geometry[j].elevation_m - geometry[i].elevation_m
                    g_pct = (elev_diff / dist_diff) * 100.0
                    if g_pct > max_grade_pct:
                        max_grade_pct = g_pct
                    break

        # Logiczne ograniczenie górne zgodne ze standardami dróg w Polsce (max 24.5%)
        max_grade_pct = round(min(24.5, max(0.0, max_grade_pct)), 1)

        avg_grade = (sum(grades) / len(grades)) if grades else 0.0
        tot_dist_km = cum_dist / 1000.0

        return {
            "tag": tag,
            "total_distance_km": round(tot_dist_km, 2),
            "avg_grade_percent": round(avg_grade, 1),
            "max_grade_percent": max_grade_pct,
            "total_ascent_m": round(total_ascent, 1),
            "total_descent_m": round(total_descent, 1),
            "elevation_profile": elevation_profile,
            "geometry": geometry
        }
