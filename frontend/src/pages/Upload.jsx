import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import Footer from '../components/Footer'

const DATA_TYPE_INFO = {
  feature_data: {
    title: 'XGBoost Model Input Format',
    desc: 'Upload CSV containing the following columns:',
    cols: ['NDVI', 'NBR', 'NDWI', 'Temp', 'Wind_Dir', 'Wind_Spd', 'Humidity', 'Elev', 'Slope', 'Latitude', 'Longitude'],
  },
  coordinates: {
    title: 'Coordinate Boundary Format',
    desc: 'Upload CSV with coordinate points that define a region boundary:',
    cols: ['point_id', 'latitude', 'longitude', 'order (optional)'],
  },
  weather: {
    title: 'Weather Conditions Format',
    desc: 'Upload CSV with weather data for the region:',
    cols: ['date', 'temperature', 'humidity', 'wind_speed', 'wind_direction', 'precipitation'],
  },
}

function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

function RiskBar({ label, count, total, color }) {
  const pct = total > 0 ? Math.round((count / total) * 100) : 0
  return (
    <div style={{ marginBottom: 8 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: 3 }}>
        <span>{label}</span>
        <span style={{ color: 'var(--secondary)' }}>{count} ({pct}%)</span>
      </div>
      <div style={{ background: 'rgba(0,0,0,0.08)', borderRadius: 4, height: 8 }}>
        <div style={{ background: color, width: `${pct}%`, height: 8, borderRadius: 4, transition: 'width 0.4s' }} />
      </div>
    </div>
  )
}

export default function Upload() {
  const navigate    = useNavigate()
  const fileInputRef = useRef(null)

  const [dataType,   setDataType]   = useState('feature_data')
  const [region,     setRegion]     = useState('from_csv')
  const [runModel,   setRunModel]   = useState(true)
  const [file,       setFile]       = useState(null)
  const [dragOver,   setDragOver]   = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error,      setError]      = useState('')
  const [result,     setResult]     = useState(null)

  const info = DATA_TYPE_INFO[dataType]

  function handleFile(files) {
    if (files && files.length > 0) {
      setFile(files[0])
      setResult(null)
    }
  }

  function handleDrop(e) {
    e.preventDefault()
    setDragOver(false)
    handleFile(e.dataTransfer.files)
  }

  async function handleSubmit(e) {
    e.preventDefault()
    if (!file) { setError('Please select a CSV file.'); return }
    setError('')
    setResult(null)
    setSubmitting(true)

    const formData = new FormData()
    formData.append('csvFile',     file)
    formData.append('csvDataType', dataType)
    formData.append('csvRegion',   region)
    if (runModel) formData.append('runModel', 'on')

    try {
      const res  = await fetch('/upload/csv', { method: 'POST', body: formData })
      const data = await res.json()
      if (data.success) {
        setResult(data)
        if (data.gpt_analysis) {
          localStorage.setItem('firesight_gpt_analysis', data.gpt_analysis)
        }
      } else {
        setError(data.error || 'Upload failed.')
      }
    } catch {
      setError('An error occurred during upload.')
    } finally {
      setSubmitting(false)
    }
  }

  function handleReset() {
    setFile(null)
    setResult(null)
    setError('')
  }

  // ── Results panel ─────────────────────────────────────────────────────────
  if (result) {
    const pd = result.prediction_data
    return (
      <div className="content">
        <header>
          <h2>Upload Results</h2>
        </header>
        <div className="upload-container">
          <div className="card upload-card">
            <div className="card-header" style={{ background: '#e8f5e9' }}>
              <h3 style={{ color: 'var(--primary-dark)' }}>
                <i className="fas fa-check-circle" style={{ marginRight: 8 }}></i>
                {result.message}
              </h3>
            </div>
            <div className="card-body">
              {pd ? (
                <>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginBottom: 20 }}>
                    {[
                      { label: 'Locations Analysed', value: pd.num_locations },
                      { label: 'Avg. Probability',   value: `${(pd.avg_probability * 100).toFixed(1)}%` },
                      { label: 'Max Probability',    value: `${(pd.max_probability * 100).toFixed(1)}%` },
                    ].map(({ label, value }) => (
                      <div key={label} style={{ background: '#f5f7f9', borderRadius: 6, padding: '12px 16px', textAlign: 'center' }}>
                        <div style={{ fontSize: '0.75rem', color: 'var(--secondary)', marginBottom: 4 }}>{label}</div>
                        <div style={{ fontSize: '1.3rem', fontWeight: 700 }}>{value}</div>
                      </div>
                    ))}
                  </div>

                  <div style={{ marginBottom: 20 }}>
                    <h4 style={{ marginBottom: 10, fontSize: '0.9rem', color: 'var(--secondary)' }}>RISK DISTRIBUTION</h4>
                    <RiskBar label="High Risk (>70%)"    count={pd.high_risk_locations}   total={pd.num_locations} color="var(--danger)" />
                    <RiskBar label="Medium Risk (40–70%)" count={pd.medium_risk_locations} total={pd.num_locations} color="var(--warning)" />
                    <RiskBar label="Low Risk (<40%)"     count={pd.low_risk_locations}    total={pd.num_locations} color="var(--success)" />
                  </div>

                  {result.gpt_analysis && (
                    <div style={{ background: '#f0f8ff', border: '1px solid #add8e6', borderRadius: 6, padding: '14px 16px', marginBottom: 20 }}>
                      <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--secondary)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                        Analysis
                      </div>
                      <p style={{ fontSize: '0.875rem', margin: 0, lineHeight: 1.6 }}>{result.gpt_analysis}</p>
                    </div>
                  )}
                </>
              ) : (
                <p style={{ color: 'var(--secondary)' }}>{result.message}</p>
              )}

              <div className="form-actions">
                <button className="btn btn-primary" onClick={() => navigate('/')}>
                  <i className="fas fa-chart-bar" style={{ marginRight: 6 }}></i>
                  View Dashboard
                </button>
                {result.gpt_analysis && (
                  <button className="btn btn-outline" onClick={() => navigate('/chat')}>
                    <i className="fas fa-robot" style={{ marginRight: 6 }}></i>
                    Discuss with AI
                  </button>
                )}
                <button className="btn btn-outline" onClick={handleReset}>
                  Upload Another
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // ── Upload form ───────────────────────────────────────────────────────────
  return (
    <div className="content">
      <div className="upload-container">
        <div className="card upload-card">
          <div className="card-header">
            <h3><i className="fas fa-cloud-upload-alt" style={{ marginRight: '0.5rem', color: 'var(--primary)' }}></i>Upload CSV Data</h3>
          </div>
          <div className="card-body">
            <form className="upload-form" onSubmit={handleSubmit}>

              <div className="form-group">
                <label htmlFor="csvDataType">Data Type</label>
                <select
                  id="csvDataType"
                  className="form-select"
                  value={dataType}
                  onChange={(e) => setDataType(e.target.value)}
                >
                  <option value="feature_data">Feature Data (for XGBoost Model)</option>
                  <option value="coordinates">Coordinate Boundary Data</option>
                  <option value="weather">Weather Conditions Data</option>
                </select>
              </div>

              <div className="form-group">
                <div className="info-box">
                  <i className="fas fa-info-circle"></i>
                  <div>
                    <h4>{info.title}</h4>
                    <p>{info.desc}</p>
                    <ul>
                      {info.cols.map((col) => <li key={col}>{col}</li>)}
                    </ul>
                  </div>
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="csvRegion">Region</label>
                <select
                  id="csvRegion"
                  className="form-select"
                  value={region}
                  onChange={(e) => setRegion(e.target.value)}
                >
                  <option value="northridge">Northridge Canyon</option>
                  <option value="eastern">Eastern Foothills</option>
                  <option value="pine">Pine Ridge Forest</option>
                  <option value="valley">Valley Grasslands</option>
                  <option value="from_csv">From CSV (Uses lat/long in CSV)</option>
                </select>
              </div>

              <div className="form-group">
                <label>Upload CSV File</label>
                <div
                  className={`upload-box${dragOver ? ' dragover' : ''}`}
                  onClick={() => fileInputRef.current?.click()}
                  onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
                  onDragLeave={() => setDragOver(false)}
                  onDrop={handleDrop}
                >
                  <i className="fas fa-file-csv"></i>
                  <p>Drag &amp; drop CSV file here or click to browse</p>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".csv"
                    style={{ display: 'none' }}
                    onChange={(e) => handleFile(e.target.files)}
                  />
                </div>

                {file && (
                  <div className="upload-preview">
                    <div className="file-item">
                      <i className="fas fa-file-csv"></i>
                      <div className="file-info">
                        <span className="file-name">{file.name}</span>
                        <span className="file-size">{formatFileSize(file.size)}</span>
                      </div>
                      <button
                        type="button"
                        className="btn btn-sm btn-outline"
                        onClick={(e) => { e.stopPropagation(); setFile(null) }}
                      >
                        <i className="fas fa-times"></i>
                      </button>
                    </div>
                  </div>
                )}
              </div>

              <div className="form-group">
                <div className="form-check">
                  <input
                    type="checkbox"
                    id="csvRunModel"
                    className="form-check-input"
                    checked={runModel}
                    onChange={(e) => setRunModel(e.target.checked)}
                  />
                  <label htmlFor="csvRunModel" className="form-check-label">
                    Run XGBoost wildfire prediction model
                  </label>
                </div>
              </div>

              {error && <p style={{ color: 'var(--danger)', marginBottom: 10 }}>{error}</p>}

              <div className="form-actions">
                <button type="submit" className="btn btn-primary" disabled={submitting}>
                  {submitting ? 'Uploading...' : 'Upload & Analyze'}
                </button>
                <button
                  type="button"
                  className="btn btn-outline"
                  onClick={() => navigate('/')}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>

        <div className="card help-card">
          <div className="card-header">
            <h3>CSV Data Requirements</h3>
          </div>
          <div className="card-body">
            <div className="accordion-item">
              <button className="accordion-button">CSV Data for XGBoost Model</button>
              <div className="accordion-body">
                <ul className="help-list">
                  <li><strong>Required Format:</strong> CSV with header row</li>
                  <li><strong>Required Columns:</strong> NDVI, NBR, NDWI, Temp, Wind_Dir, Wind_Spd, Humidity, Elev, Slope, Latitude, Longitude</li>
                  <li><strong>Note:</strong> All numeric fields must contain valid numbers with no missing values</li>
                </ul>
              </div>
            </div>
            <div className="accordion-item" style={{ marginTop: 8 }}>
              <button className="accordion-button">Coordinate Boundary Data</button>
              <div className="accordion-body">
                <ul className="help-list">
                  <li><strong>Required Columns:</strong> latitude, longitude</li>
                  <li><strong>Optional:</strong> point_id, order</li>
                </ul>
              </div>
            </div>
            <div className="accordion-item" style={{ marginTop: 8 }}>
              <button className="accordion-button">Weather Conditions Data</button>
              <div className="accordion-body">
                <ul className="help-list">
                  <li><strong>Required Columns:</strong> date, temperature, humidity, wind_speed</li>
                  <li><strong>Optional:</strong> wind_direction, precipitation</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
      <Footer />
    </div>
  )
}
