import { useState } from 'react'
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
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

const DATA_7 = {
  labels: ['Mar 16', 'Mar 17', 'Mar 18', 'Mar 19', 'Mar 20', 'Mar 21', 'Mar 22'],
  ndvi:  [0.65, 0.64, 0.62, 0.59, 0.57, 0.54, 0.52],
  nbr:   [0.32, 0.31, 0.30, 0.28, 0.25, 0.21, 0.18],
  ndwi:  [0.41, 0.40, 0.38, 0.35, 0.32, 0.30, 0.28],
}

const DATA_30 = {
  labels: ['Feb 21', 'Feb 28', 'Mar 7', 'Mar 14', 'Mar 22'],
  ndvi:  [0.72, 0.68, 0.64, 0.58, 0.52],
  nbr:   [0.41, 0.37, 0.31, 0.25, 0.18],
  ndwi:  [0.51, 0.46, 0.40, 0.34, 0.28],
}

const DATA_90 = {
  labels: ['Dec 22', 'Jan 5', 'Jan 19', 'Feb 2', 'Feb 16', 'Mar 1', 'Mar 22'],
  ndvi:  [0.81, 0.78, 0.74, 0.70, 0.65, 0.59, 0.52],
  nbr:   [0.55, 0.51, 0.46, 0.40, 0.35, 0.27, 0.18],
  ndwi:  [0.62, 0.59, 0.54, 0.48, 0.42, 0.35, 0.28],
}

const DATASET_MAP = { '7': DATA_7, '30': DATA_30, '90': DATA_90 }

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
  const d = DATASET_MAP[range]

  const lastNdvi = d.ndvi[d.ndvi.length - 1]
  const firstNdvi = d.ndvi[0]
  const lastNbr = d.nbr[d.nbr.length - 1]
  const firstNbr = d.nbr[0]
  const lastNdwi = d.ndwi[d.ndwi.length - 1]
  const firstNdwi = d.ndwi[0]

  const pct = (last, first) => (((last - first) / first) * 100).toFixed(1)

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
          <Line data={buildChartData(d)} options={options} />
        </div>
        <div className="index-summary">
          {[
            { label: 'NDVI', last: lastNdvi, first: firstNdvi },
            { label: 'NBR', last: lastNbr, first: firstNbr },
            { label: 'NDWI', last: lastNdwi, first: firstNdwi },
          ].map(({ label, last, first }) => {
            const change = pct(last, first)
            const isNeg = change < 0
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
      </div>
    </div>
  )
}
