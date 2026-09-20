import React, { useState } from 'react';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import RouteMap from './components/RouteMap';
import ElevationProfileChart from './components/ElevationProfileChart';
import axios from 'axios';
import { X, HelpCircle, Server, Terminal } from 'lucide-react';

export default function App() {
  const [startCoord, setStartCoord] = useState(null);
  const [endCoord, setEndCoord] = useState(null);
  const [startAddressInput, setStartAddressInput] = useState('');
  const [endAddressInput, setEndAddressInput] = useState('');
  
  const [numVariants, setNumVariants] = useState(5);
  const [maxDetourPercent, setMaxDetourPercent] = useState(100);
  const [elevationProvider, setElevationProvider] = useState('open-meteo');

  const [routeData, setRouteData] = useState(null);
  const [activeVariantId, setActiveVariantId] = useState(1);
  const [hoveredPoint, setHoveredPoint] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const [clickTarget, setClickTarget] = useState('start');
  const [showInfoModal, setShowInfoModal] = useState(false);

  const handleCalculateRoute = async () => {
    if (!startCoord && !startAddressInput) {
      alert('Podaj punkt Start (wpisz adres lub kliknij na mapie)!');
      return;
    }
    if (!endCoord && !endAddressInput) {
      alert('Podaj punkt Meta (wpisz adres lub kliknij na mapie)!');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await axios.post('/api/route', {
        start: startCoord,
        end: endCoord,
        start_address: startAddressInput || null,
        end_address: endAddressInput || null,
        num_variants: numVariants,
        max_detour_percent: maxDetourPercent,
        elevation_provider: elevationProvider
      });

      setRouteData(response.data);
      if (response.data.variants && response.data.variants.length > 0) {
        setActiveVariantId(response.data.variants[0].id);
      }
      if (response.data.start) {
        setStartCoord(response.data.start);
      }
      if (response.data.end) {
        setEndCoord(response.data.end);
      }
    } catch (err) {
      console.error('Błąd pobierania tras:', err);
      setError(err.response?.data?.detail || 'Błąd połączenia z serwerem API MapBike.');
    } finally {
      setLoading(false);
    }
  };

  const handleSearchAddress = async (target) => {
    const query = target === 'start' ? startAddressInput : endAddressInput;
    if (!query) return;

    try {
      const res = await axios.get(`/api/geocode?query=${encodeURIComponent(query)}`);
      if (res.data) {
        const coord = { lat: res.data.lat, lon: res.data.lon };
        if (target === 'start') {
          setStartCoord(coord);
        } else {
          setEndCoord(coord);
        }
      }
    } catch (err) {
      alert('Nie znaleziono adresu: ' + query);
    }
  };

  const handleMapClick = async (latlng) => {
    const coord = { lat: latlng.lat, lon: latlng.lng };
    if (clickTarget === 'start') {
      setStartCoord(coord);
      setClickTarget('end');
    } else {
      setEndCoord(coord);
      setClickTarget('start');
    }
  };

  const handleDownloadGpx = (variantIndex) => {
    if (!routeData || !routeData.variants || !routeData.variants[variantIndex]) return;
    const variant = routeData.variants[variantIndex];
    const blob = new Blob([variant.gpx_data], { type: 'application/gpx+xml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `mapbike_trasa_${variant.id}_${variant.name.replace(/\s+/g, '_').toLowerCase()}.gpx`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handlePresetSelect = (preset) => {
    setStartCoord(preset.start);
    setEndCoord(preset.end);
  };

  const activeVariant = routeData?.variants?.find(v => v.id === activeVariantId) || routeData?.variants?.[0];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', width: '100vw', overflow: 'hidden' }}>
      <Navbar onSelectPreset={handlePresetSelect} onToggleInfo={() => setShowInfoModal(true)} />

      <div style={{ display: 'flex', flex: 1, position: 'relative', overflow: 'hidden' }}>
        <Sidebar
          startCoord={startCoord}
          endCoord={endCoord}
          setStartCoord={setStartCoord}
          setEndCoord={setEndCoord}
          startAddressInput={startAddressInput}
          setStartAddressInput={setStartAddressInput}
          endAddressInput={endAddressInput}
          setEndAddressInput={setEndAddressInput}
          onSearchAddress={handleSearchAddress}
          numVariants={numVariants}
          setNumVariants={setNumVariants}
          maxDetourPercent={maxDetourPercent}
          setMaxDetourPercent={setMaxDetourPercent}
          elevationProvider={elevationProvider}
          setElevationProvider={setElevationProvider}
          onCalculate={handleCalculateRoute}
          loading={loading}
          routeData={routeData}
          activeVariantId={activeVariantId}
          setActiveVariantId={setActiveVariantId}
          onDownloadGpx={handleDownloadGpx}
        />

        <main style={{ flex: 1, display: 'flex', flexDirection: 'column', position: 'relative' }}>
          {error && (
            <div className="glass-panel" style={{
              position: 'absolute',
              top: '16px',
              left: '50%',
              transform: 'translateX(-50%)',
              zIndex: 1100,
              padding: '12px 24px',
              backgroundColor: 'rgba(239, 68, 68, 0.9)',
              color: '#fff',
              fontWeight: 600,
              fontSize: '0.85rem'
            }}>
              ⚠️ {error}
            </div>
          )}

          <div style={{ flex: 1, margin: '12px 16px 12px 12px', borderRadius: '12px', overflow: 'hidden', border: '1px solid rgba(255,255,255,0.1)' }}>
            <RouteMap
              startCoord={startCoord}
              endCoord={endCoord}
              onMapClick={handleMapClick}
              variants={routeData?.variants}
              activeVariantId={activeVariantId}
              setActiveVariantId={setActiveVariantId}
              hoveredPoint={hoveredPoint}
            />
          </div>

          <ElevationProfileChart
            activeVariant={activeVariant}
            onHoverPoint={setHoveredPoint}
          />
        </main>
      </div>

      {showInfoModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100vw',
          height: '100vh',
          backgroundColor: 'rgba(15, 23, 42, 0.8)',
          backdropFilter: 'blur(8px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 2000
        }}>
          <div className="glass-panel" style={{ width: '650px', maxHeight: '85vh', padding: '24px', overflowY: 'auto', position: 'relative' }}>
            <button
              onClick={() => setShowInfoModal(false)}
              style={{ position: 'absolute', top: '16px', right: '16px', background: 'none', border: 'none', color: '#fff', cursor: 'pointer' }}
            >
              <X size={24} />
            </button>

            <h2 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <HelpCircle color="var(--accent-emerald)" /> Instrukcja Obsługi & API MapBike
            </h2>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              <div>
                <h3 style={{ color: '#fff', fontSize: '0.95rem', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Terminal size={16} color="var(--accent-blue)" /> Uruchomienie na Linux (Kubuntu) / Windows
                </h3>
                <pre style={{ background: 'rgba(0,0,0,0.4)', padding: '10px', borderRadius: '6px', overflowX: 'auto', color: '#10b981' }}>
                  {`# Windows (Gotowe pliki BAT):
install.bat
run.bat

# Linux / Terminal:
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000`}
                </pre>
              </div>

              <div>
                <h3 style={{ color: '#fff', fontSize: '0.95rem', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Server size={16} color="var(--accent-emerald)" /> Zapytanie REST API z adresem tekstowym
                </h3>
                <pre style={{ background: 'rgba(0,0,0,0.4)', padding: '10px', borderRadius: '6px', overflowX: 'auto', color: '#3b82f6' }}>
                  {`POST /api/route HTTP/1.1
Content-Type: application/json

{
  "start_address": "Kraków, Rynek Główny 1",
  "end_address": "Kraków, Mogilska 20",
  "num_variants": 5,
  "max_detour_percent": 100,
  "elevation_provider": "open-meteo"
}`}
                </pre>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
