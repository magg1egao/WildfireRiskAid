import { useState, useEffect } from 'react'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js'
import { Line } from 'react-chartjs-2'

ChartJS.register(
  CategoryScale, LinearScale, PointElement, LineElement,
  Title, Tooltip, Legend, Filler
)

function buildChartData(d) {
  return {
    labels: d.labels,
    datasets: [
      {
        label: 'NDVI',
        borderColor: '#2D4739',
        backgroundColor: 'rgba(45,71,57,0.1)',
        data: d.ndvi,
        tension: 0.3,
        fill: true,
      },
      {
        label: 'NBR',
        borderColor: '#F44336',
        backgroundColor: 'rgba(244,67,54,0.1)',
        data: d.nbr,
        tension: 0.3,
        fill: true,
      },
      {
        label: 'NDWI',
        borderColor: '#0288D1',
        backgroundColor: 'rgba(2,136,209,0.1)',
        data: d.ndwi,
        tension: 0.3,
        fill: true,
      },
    ],
  }
}

const options = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'top',
      labels: { boxWidth: 12, usePointStyle: true, pointStyle: 'circle' },
    },
    tooltip: {
      mode: 'index',
      intersect: false,
      backgroundColor: 'rgba(38,50,56,0.9)',
      padding: 12,
      cornerRadius: 4,
    },
  },
  scales: {
    y: {
      beginAtZero: false,
      min: 0,
      max: 1,
      grid: { color: 'rgba(0,0,0,0.05)' },
    },
    x: { grid: { display: false } },
  },
  elements: { point: { radius: 3, hoverRadius: 5 } },
}

export default function IndicesChart() {
  const [range, setRange] = useState('7')
  const [data, setData] = useState(null)

  useEffect(() => {
    fetch(`/api/indices-trend?days=${range}`)
      .then((r) => r.json())
      .then(setData)
      .catch(() => {})
  }, [range])

  const lastNdvi  = data ? data.ndvi[data.ndvi.length - 1]   : 0
  const firstNdvi = data ? data.ndvi[0]                       : 0
  const lastNbr   = data ? data.nbr[data.nbr.length - 1]     : 0
  const firstNbr  = data ? data.nbr[0]                        : 0
  const lastNdwi  = data ? data.ndwi[data.ndwi.length - 1]   : 0
  const firstNdwi = data ? data.ndwi[0]                       : 0

  const pct = (last, first) =>
    first !== 0 ? (((last - first) / first) * 100).toFixed(1) : '0.0'

  return (
    <div className="panel">
      <div className="panel-header">
        <div className="panel-title">
          <i className="fas fa-chart-line"></i>
          Vegetation &amp; Moisture Trends
        </div>
        <div className="panel-actions">
          <select
            className="form-select compact"
            value={range}
            onChange={(e) => setRange(e.target.value)}
          >
            <option value="7">Last 7 Days</option>
            <option value="30">Last 30 Days</option>
            <option value="90">Last 90 Days</option>
          </select>
        </div>
      </div>
      <div className="panel-body">
        <div className="chart-container">
          {!data ? (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--secondary)' }}>
              Loading...
            </div>
          ) : data.labels.length < 2 ? (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', gap: '0.5rem', color: 'var(--secondary)', textAlign: 'center', padding: '1rem' }}>
              <i className="fas fa-chart-line" style={{ fontSize: '1.5rem', opacity: 0.3 }}></i>
              <span style={{ fontSize: '0.85rem' }}>No trend data yet</span>
              <span style={{ fontSize: '0.75rem', opacity: 0.7 }}>Upload datasets over time to see vegetation and moisture trends</span>
            </div>
          ) : (
            <Line data={buildChartData(data)} options={options} />
          )}
        </div>
        {data && (
          <div className="index-summary">
            {[
              { label: 'NDVI', last: lastNdvi, first: firstNdvi },
              { label: 'NBR',  last: lastNbr,  first: firstNbr  },
              { label: 'NDWI', last: lastNdwi, first: firstNdwi },
            ].map(({ label, last, first }) => {
              const change = pct(last, first)
              const isNeg  = parseFloat(change) < 0
              return (
                <div key={label} className="index-stat declining">
                  <div className="index-label">{label}</div>
                  <div className="index-value">{last.toFixed(2)}</div>
                  <div className={`index-change ${isNeg ? 'negative' : 'positive'}`}>
                    {change}% in {range} days
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
