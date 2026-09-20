import React from 'react';
import { Bike, Navigation, MapPin, Info } from 'lucide-react';

export default function Navbar({ onSelectPreset, onToggleInfo }) {
  return (
    <header className="glass-panel" style={{
      margin: '12px 16px 0 16px',
      padding: '12px 24px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      zIndex: 1000
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div style={{
          background: 'linear-gradient(135deg, #10b981 0%, #3b82f6 100%)',
          width: '40px',
          height: '40px',
          borderRadius: '10px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 4px 12px rgba(16, 185, 129, 0.4)'
        }}>
          <Bike size={24} color="#ffffff" />
        </div>
        <div>
          <h1 style={{ fontSize: '1.25rem', fontWeight: 700, letterSpacing: '-0.02em', background: 'linear-gradient(90deg, #ffffff, #94a3b8)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            MapBike
          </h1>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Planer Tras o Minimalnym Nachyleniu
          </p>
        </div>
      </div>

      {/* Szybkie presety tras testowych */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
          <MapPin size={14} /> Trasy testowe:
        </span>
        <button
          className="glass-panel"
          onClick={() => onSelectPreset({ start: { lat: 50.0614, lon: 19.9365 }, end: { lat: 50.0880, lon: 19.9950 } })}
          style={{ padding: '6px 12px', fontSize: '0.8rem', color: '#f8fafc', cursor: 'pointer', borderRadius: '6px' }}
        >
          Kraków (Wisła)
        </button>
        <button
          className="glass-panel"
          onClick={() => onSelectPreset({ start: { lat: 49.2990, lon: 19.9490 }, end: { lat: 49.2800, lon: 19.9800 } })}
          style={{ padding: '6px 12px', fontSize: '0.8rem', color: '#f8fafc', cursor: 'pointer', borderRadius: '6px' }}
        >
          Zakopane (Góry)
        </button>
        <button
          className="glass-panel"
          onClick={() => onSelectPreset({ start: { lat: 52.2297, lon: 21.0122 }, end: { lat: 52.2600, lon: 21.0500 } })}
          style={{ padding: '6px 12px', fontSize: '0.8rem', color: '#f8fafc', cursor: 'pointer', borderRadius: '6px' }}
        >
          Warszawa
        </button>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <button
          onClick={onToggleInfo}
          className="glass-panel"
          style={{ padding: '8px 14px', fontSize: '0.85rem', color: '#f8fafc', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px', borderRadius: '8px' }}
        >
          <Info size={16} /> Instrukcja API
        </button>
      </div>
    </header>
  );
}
