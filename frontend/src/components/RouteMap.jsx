import React, { useEffect } from 'react';
import { MapContainer, TileLayer, Polyline, Marker, Popup, useMapEvents, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Usunięcie domyślnych ikonek leaflet fix
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

const startIcon = new L.DivIcon({
  className: 'custom-div-icon',
  html: `<div class="marker-start-pin"></div>`,
  iconSize: [20, 20],
  iconAnchor: [10, 10]
});

const endIcon = new L.DivIcon({
  className: 'custom-div-icon',
  html: `<div class="marker-end-pin"></div>`,
  iconSize: [20, 20],
  iconAnchor: [10, 10]
});

const hoverIcon = new L.DivIcon({
  className: 'custom-div-icon',
  html: `<div style="width: 14px; height: 14px; background-color: #ffffff; border: 3px solid #3b82f6; border-radius: 50%; box-shadow: 0 0 10px #3b82f6;"></div>`,
  iconSize: [16, 16],
  iconAnchor: [8, 8]
});

function MapClickHandler({ onMapClick }) {
  useMapEvents({
    click(e) {
      onMapClick(e.latlng);
    },
  });
  return null;
}

function MapFitBounds({ variants, start, end }) {
  const map = useMap();
  useEffect(() => {
    if (variants && variants.length > 0) {
      const allCoords = [];
      variants.forEach(v => {
        if (v.geometry) {
          v.geometry.forEach(pt => allCoords.push([pt.lat, pt.lon]));
        }
      });
      if (allCoords.length > 0) {
        const bounds = L.latLngBounds(allCoords);
        map.fitBounds(bounds, { padding: [40, 40] });
      }
    } else if (start && end && start.lat && end.lat) {
      const bounds = L.latLngBounds([
        [start.lat, start.lon],
        [end.lat, end.lon]
      ]);
      map.fitBounds(bounds, { padding: [60, 60] });
    }
  }, [variants, start, end, map]);
  return null;
}

export default function RouteMap({
  startCoord,
  endCoord,
  onMapClick,
  variants,
  activeVariantId,
  setActiveVariantId,
  hoveredPoint
}) {
  const center = startCoord && startCoord.lat ? [startCoord.lat, startCoord.lon] : [52.0693, 19.4803];

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative' }}>
      <MapContainer center={center} zoom={startCoord ? 13 : 6} style={{ width: '100%', height: '100%' }}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
        />

        <MapClickHandler onMapClick={onMapClick} />
        <MapFitBounds variants={variants} start={startCoord} end={endCoord} />

        {startCoord && startCoord.lat && (
          <Marker position={[startCoord.lat, startCoord.lon]} icon={startIcon}>
            <Popup>
              <strong>🟢 Punkt Startowy</strong><br />
              {startCoord.lat.toFixed(4)}, {startCoord.lon.toFixed(4)}
            </Popup>
          </Marker>
        )}

        {endCoord && endCoord.lat && (
          <Marker position={[endCoord.lat, endCoord.lon]} icon={endIcon}>
            <Popup>
              <strong>🔴 Punkt Końcowy (Meta)</strong><br />
              {endCoord.lat.toFixed(4)}, {endCoord.lon.toFixed(4)}
            </Popup>
          </Marker>
        )}

        {hoveredPoint && (
          <Marker position={[hoveredPoint.lat, hoveredPoint.lon]} icon={hoverIcon} zIndexOffset={1000}>
            <Popup autoPan={false}>
              Wysokość: <strong>{hoveredPoint.elevation_m} m</strong><br />
              Dystans od startu: <strong>{(hoveredPoint.distance_m / 1000).toFixed(2)} km</strong>
            </Popup>
          </Marker>
        )}

        {variants && variants.map((variant) => {
          const isActive = variant.id === activeVariantId;
          const positions = variant.geometry ? variant.geometry.map(pt => [pt.lat, pt.lon]) : [];

          if (positions.length === 0) return null;

          return (
            <Polyline
              key={variant.id}
              positions={positions}
              pathOptions={{
                color: variant.color || '#3b82f6',
                weight: isActive ? 7 : 4,
                opacity: isActive ? 0.95 : 0.45,
                lineCap: 'round',
                lineJoin: 'round'
              }}
              eventHandlers={{
                click: () => setActiveVariantId(variant.id)
              }}
            >
              <Popup>
                <div>
                  <strong style={{ color: variant.color }}>#{variant.id} {variant.name}</strong><br />
                  📏 Dystans: <strong>{variant.total_distance_km} km</strong><br />
                  ⛰️ Podjazdy: <strong>+{variant.total_ascent_m} m</strong><br />
                  📈 Śr. nachylenie: <strong>{variant.avg_grade_percent}%</strong><br />
                  Kliknij, aby podświetlić trasę.
                </div>
              </Popup>
            </Polyline>
          );
        })}
      </MapContainer>
    </div>
  );
}
