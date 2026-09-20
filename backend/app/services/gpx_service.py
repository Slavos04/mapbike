import gpxpy
import gpxpy.gpx
from typing import List
from app.schemas import RoutePoint

class GPXService:
    @staticmethod
    def generate_gpx(points: List[RoutePoint], route_name: str = "Trasa MapBike") -> str:
        """
        Tworzy ciąg znaków XML w formacie GPX 1.1 dla podanej listy punktów trasy.
        """
        gpx = gpxpy.gpx.GPX()
        gpx.creator = "MapBike - Minimal Gradient Route Planner"
        gpx.name = route_name
        gpx.description = "Wygenerowana trasa rowerowa z aplikacją MapBike"

        # Tworzenie śladu
        gpx_track = gpxpy.gpx.GPXTrack(name=route_name)
        gpx.tracks.append(gpx_track)

        # Tworzenie segmentu śladu
        gpx_segment = gpxpy.gpx.GPXTrackSegment()
        gpx_track.segments.append(gpx_segment)

        # Dodawanie punktów
        for pt in points:
            gpx_segment.points.append(
                gpxpy.gpx.GPXTrackPoint(
                    latitude=pt.lat,
                    longitude=pt.lon,
                    elevation=pt.elevation_m
                )
            )

        return gpx.to_xml()
