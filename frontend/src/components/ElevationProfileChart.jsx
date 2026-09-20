import React, { useEffect, useRef } from 'react';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Filler, Legend } from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Filler, Legend);

export default function ElevationProfileChart({ activeVariant, onHoverPoint }) {
  const chartRef = useRef(null);

  if (!activeVariant || !activeVariant.elevation_profile || activeVariant.elevation_profile.length === 0) {
    return (
      <div className="glass-panel" style={{ padding: '16px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
        Wybierz trasę, aby zobaczyć profil wysokościowy terenu.
      </div>
    );
  }

  const profile = activeVariant.elevation_profile;
  const labels = profile.map(p => `${p.distance_m} km`);
  const dataPoints = profile.map(p => p.elevation_m);

  const data = {
    labels: labels,
    datasets: [
      {
        label: `Profil wysokości (${activeVariant.name})`,
        data: dataPoints,
        borderColor: activeVariant.color || '#10b981',
        backgroundColor: (context) => {
          const ctx = context.chart.ctx;
          const gradient = ctx.createLinearGradient(0, 0, 0, 150);
          gradient.addColorStop(0, `${activeVariant.color || '#10b981'}66`);
          gradient.addColorStop(1, `${activeVariant.color || '#10b981'}00`);
          return gradient;
        },
        borderWidth: 2,
        fill: true,
        tension: 0.3,
        pointRadius: 0,
        pointHoverRadius: 6,
        pointHoverBackgroundColor: '#ffffff',
        pointHoverBorderColor: activeVariant.color || '#10b981',
        pointHoverBorderWidth: 3,
      }
    ]
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      },
      tooltip: {
        mode: 'index',
        intersect: false,
        backgroundColor: 'rgba(15, 23, 42, 0.95)',
        titleColor: '#ffffff',
        bodyColor: '#94a3b8',
        borderColor: 'rgba(255, 255, 255, 0.1)',
        borderWidth: 1,
        padding: 10,
        callbacks: {
          label: (context) => {
            const index = context.dataIndex;
            const pt = profile[index];
            if (pt) {
              return ` Wysokość: ${pt.elevation_m} m | Nachylenie: ${pt.grade_percent}%`;
            }
            return ` Wysokość: ${context.parsed.y} m`;
          }
        }
      }
    },
    scales: {
      x: {
        grid: { color: 'rgba(255, 255, 255, 0.05)' },
        ticks: { color: '#94a3b8', font: { size: 10 }, maxTicksLimit: 10 }
      },
      y: {
        grid: { color: 'rgba(255, 255, 255, 0.05)' },
        ticks: { color: '#94a3b8', font: { size: 10 } },
        title: { display: true, text: 'Wysokość (m n.p.m.)', color: '#94a3b8', font: { size: 10 } }
      }
    },
    onHover: (event, chartElements) => {
      if (chartElements && chartElements.length > 0) {
        const index = chartElements[0].index;
        if (activeVariant.geometry && activeVariant.geometry[index]) {
          onHoverPoint(activeVariant.geometry[index]);
        }
      } else {
        onHoverPoint(null);
      }
    }
  };

  return (
    <div className="glass-panel" style={{
      padding: '12px 16px',
      height: '180px',
      margin: '0 16px 12px 16px',
      display: 'flex',
      flexDirection: 'column',
      zIndex: 1000
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
        <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-main)' }}>
          📊 Profil Wysokościowy: <strong style={{ color: activeVariant.color }}>{activeVariant.name}</strong>
        </span>
        <div style={{ display: 'flex', gap: '16px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          <span>Wysokość min/max: <strong>{Math.min(...dataPoints)}m / {Math.max(...dataPoints)}m</strong></span>
          <span>Przewyższenie: <strong style={{ color: '#10b981' }}>+{activeVariant.total_ascent_m}m</strong></span>
        </div>
      </div>

      <div style={{ flex: 1, position: 'relative' }}>
        {/* Renderowanie canvas przez dynamiczny import Chart.js lub standardową bibliotekę React */}
        <SimpleChartWrapper data={data} options={options} />
      </div>
    </div>
  );
}

function SimpleChartWrapper({ data, options }) {
  const { Line } = require('react-chartjs-2');
  return <Line data={data} options={options} />;
}
