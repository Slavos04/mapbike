import React from 'react';
import { Play, Download, Sliders, Compass, CheckCircle2, AlertTriangle, Search } from 'lucide-react';

export default function Sidebar({
  startCoord,
  endCoord,
  setStartCoord,
  setEndCoord,
  startAddressInput,
  setStartAddressInput,
  endAddressInput,
  setEndAddressInput,
  onSearchAddress,
  numVariants,
  setNumVariants,
  maxDetourPercent,
  setMaxDetourPercent,
  elevationProvider,
  setElevationProvider,
  onCalculate,
  loading,
  routeData,
  activeVariantId,
  setActiveVariantId,
  onDownloadGpx
}) {
  return (
    <aside className="glass-panel" style={{
      width: '440px',
      height: 'calc(100vh - 90px)',
      margin: '12px 0 12px 16px',
      padding: '20px',
      display: 'flex',
      flexDirection: 'column',
      gap: '16px',
      overflowY: 'auto',
      zIndex: 1000
    }}>
      <div>
        <h2 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Compass size={18} color="var(--accent-emerald)" /> Punkty Trasy (Adres lub Mapa)
        </h2>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {/* Start */}
          <div>
            <label style={{ fontSize: '0.78rem', color: 'var(--text-main)', fontWeight: 600 }}>🟢 Punkt Startowy:</label>
            <div style={{ display: 'flex', gap: '4px', marginTop: '4px' }}>
              <input
                type="text"
                value={startAddressInput}
                onChange={(e) => setStartAddressInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && onSearchAddress('start')}
                placeholder="Wpisz adres startu (np. Rynek 1)"
                style={{ flex: 1, padding: '8px', borderRadius: '6px', background: 'rgba(15,23,42,0.8)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', fontSize: '0.85rem' }}
              />
              <button
                onClick={() => onSearchAddress('start')}
                style={{ padding: '6px 12px', background: 'var(--accent-blue)', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 600, fontSize: '0.8rem' }}
              >
                Szukaj
              </button>
            </div>

            <div style={{ display: 'flex', gap: '6px', marginTop: '4px' }}>
              <input
                type="number"
                step="0.0001"
                value={startCoord?.lat || ''}
                onChange={(e) => setStartCoord({ ...startCoord, lat: parseFloat(e.target.value) || 0 })}
                style={{ flex: 1, padding: '8px', borderRadius: '6px', background: 'rgba(15,23,42,0.6)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', fontSize: '0.85rem' }}
                placeholder="Szerokość (Lat)"
              />
              <input
                type="number"
                step="0.0001"
                value={startCoord?.lon || ''}
                onChange={(e) => setStartCoord({ ...startCoord, lon: parseFloat(e.target.value) || 0 })}
                style={{ flex: 1, padding: '8px', borderRadius: '6px', background: 'rgba(15,23,42,0.6)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', fontSize: '0.85rem' }}
                placeholder="Długość (Lon)"
              />
            </div>
          </div>

          {/* Meta */}
          <div>
            <label style={{ fontSize: '0.78rem', color: 'var(--text-main)', fontWeight: 600 }}>🔴 Punkt Końcowy (Meta):</label>
            <div style={{ display: 'flex', gap: '4px', marginTop: '4px' }}>
              <input
                type="text"
                value={endAddressInput}
                onChange={(e) => setEndAddressInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && onSearchAddress('end')}
                placeholder="Wpisz adres mety (np. Mogilska 20)"
                style={{ flex: 1, padding: '8px', borderRadius: '6px', background: 'rgba(15,23,42,0.8)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', fontSize: '0.85rem' }}
              />
              <button
                onClick={() => onSearchAddress('end')}
                style={{ padding: '6px 12px', background: 'var(--accent-blue)', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 600, fontSize: '0.8rem' }}
              >
                Szukaj
              </button>
            </div>

            <div style={{ display: 'flex', gap: '6px', marginTop: '4px' }}>
              <input
                type="number"
                step="0.0001"
                value={endCoord?.lat || ''}
                onChange={(e) => setEndCoord({ ...endCoord, lat: parseFloat(e.target.value) || 0 })}
                style={{ flex: 1, padding: '8px', borderRadius: '6px', background: 'rgba(15,23,42,0.6)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', fontSize: '0.85rem' }}
                placeholder="Szerokość (Lat)"
              />
              <input
                type="number"
                step="0.0001"
                value={endCoord?.lon || ''}
                onChange={(e) => setEndCoord({ ...endCoord, lon: parseFloat(e.target.value) || 0 })}
                style={{ flex: 1, padding: '8px', borderRadius: '6px', background: 'rgba(15,23,42,0.6)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', fontSize: '0.85rem' }}
                placeholder="Długość (Lon)"
              />
            </div>
          </div>
          
          <p style={{ fontSize: '0.73rem', color: 'var(--accent-emerald)', fontStyle: 'italic' }}>
            💡 Kliknij na mapie w 2 miejscach, aby kolejno ustawić Start i Metę!
          </p>
        </div>
      </div>

      <hr style={{ borderColor: 'rgba(255,255,255,0.08)' }} />

      <div>
        <h2 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Sliders size={18} color="var(--accent-blue)" /> Parametry & Algorytm
        </h2>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-main)' }}>Liczba wariantów tras:</label>
              <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--accent-emerald)' }}>{numVariants}</span>
            </div>
            <input
              type="range"
              min="1"
              max="10"
              value={numVariants}
              onChange={(e) => setNumVariants(parseInt(e.target.value))}
            />
          </div>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-main)' }}>Maksymalne wydłużenie (Max Detour):</label>
              <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--accent-blue)' }}>+{maxDetourPercent}%</span>
            </div>
            <input
              type="range"
              min="10"
              max="200"
              step="10"
              value={maxDetourPercent}
              onChange={(e) => setMaxDetourPercent(parseInt(e.target.value))}
            />
          </div>

          <div>
            <label style={{ fontSize: '0.8rem', color: 'var(--text-main)', display: 'block', marginBottom: '4px' }}>
              Źródło danych wysokościowych:
            </label>
            <select
              value={elevationProvider}
              onChange={(e) => setElevationProvider(e.target.value)}
              style={{ width: '100%', padding: '8px', borderRadius: '6px', background: 'rgba(15,23,42,0.8)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', fontSize: '0.85rem' }}
            >
              <option value="open-meteo">Open-Meteo API (Rekomendowane)</option>
              <option value="open-elevation">Open-Elevation API</option>
              <option value="synthetic">Offline Fallback (Symulacja SRTM)</option>
            </select>
          </div>
        </div>
      </div>

      <button
        onClick={onCalculate}
        disabled={loading}
        className="glass-button"
        style={{ width: '100%', justifyContent: 'center', padding: '12px', fontSize: '0.95rem' }}
      >
        {loading ? 'Obliczanie tras i profilu...' : (
          <>
            <Play size={18} /> Wyznacz Optymalne Trasy
          </>
        )}
      </button>

      {routeData && routeData.variants && (
        <div style={{ marginTop: '8px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-main)' }}>
              Wygenerowane Trasy ({routeData.variants.length})
            </h3>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Najkrótsza: {routeData.shortest_distance_km} km
            </span>
          </div>

          {routeData.variants.map((variant, idx) => {
            const isActive = activeVariantId === variant.id;
            return (
              <div
                key={variant.id}
                onClick={() => setActiveVariantId(variant.id)}
                className="glass-panel"
                style={{
                  padding: '12px',
                  cursor: 'pointer',
                  borderRadius: '10px',
                  borderLeft: `5px solid ${variant.color}`,
                  background: isActive ? 'rgba(30, 41, 59, 0.95)' : 'rgba(15, 23, 42, 0.6)',
                  boxShadow: isActive ? `0 0 12px ${variant.color}44` : 'none',
                  transition: 'all 0.2s ease'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '6px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span style={{
                      backgroundColor: variant.color,
                      color: '#000',
                      fontWeight: 700,
                      fontSize: '0.7rem',
                      padding: '2px 6px',
                      borderRadius: '4px'
                    }}>
                      #{variant.id}
                    </span>
                    <strong style={{ fontSize: '0.85rem', color: '#fff' }}>{variant.name}</strong>
                  </div>

                  {variant.is_within_limit ? (
                    <span style={{ fontSize: '0.7rem', color: '#10b981', display: 'flex', alignItems: 'center', gap: '2px' }}>
                      <CheckCircle2 size={12} /> Limit OK
                    </span>
                  ) : (
                    <span style={{ fontSize: '0.7rem', color: '#f59e0b', display: 'flex', alignItems: 'center', gap: '2px' }}>
                      <AlertTriangle size={12} /> Ponad limit
                    </span>
                  )}
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '8px' }}>
                  <div>📏 Dystans: <strong style={{ color: '#fff' }}>{variant.total_distance_km} km</strong></div>
                  <div>⛰️ Podjazdy: <strong style={{ color: '#10b981' }}>+{variant.total_ascent_m} m</strong></div>
                  <div>📈 Śr. nachylenie: <strong style={{ color: '#fff' }}>{variant.avg_grade_percent}%</strong></div>
                  <div>🚨 Max nachylenie: <strong style={{ color: variant.max_grade_percent > 8 ? '#ef4444' : '#fff' }}>{variant.max_grade_percent}%</strong></div>
                </div>

                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDownloadGpx(idx);
                  }}
                  className="glass-panel"
                  style={{
                    width: '100%',
                    padding: '6px',
                    fontSize: '0.75rem',
                    color: '#f8fafc',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '4px',
                    borderRadius: '6px',
                    background: 'rgba(255,255,255,0.05)'
                  }}
                >
                  <Download size={13} /> Pobierz plik GPX
                </button>
              </div>
            );
          })}
        </div>
      )}
    </aside>
  );
}
