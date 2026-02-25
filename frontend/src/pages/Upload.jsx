import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'

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

export default function Upload() {
  const navigate = useNavigate()
  const fileInputRef = useRef(null)

  const [dataType, setDataType] = useState('feature_data')
  const [region, setRegion] = useState('from_csv')
  const [runModel, setRunModel] = useState(true)
  const [file, setFile] = useState(null)
  const [dragOver, setDragOver] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  const info = DATA_TYPE_INFO[dataType]

  function handleFile(files) {
    if (files && files.length > 0) setFile(files[0])
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
    setSubmitting(true)

    const formData = new FormData()
    formData.append('csvFile', file)
    formData.append('csvDataType', dataType)
    formData.append('csvRegion', region)
    if (runModel) formData.append('runModel', 'on')

    try {
      const res = await fetch('/upload/csv', { method: 'POST', body: formData })
      const data = await res.json()
      if (data.success) {
        if (data.gpt_analysis) {
          localStorage.setItem('firesight_gpt_analysis', data.gpt_analysis)
        }
        navigate('/')
      } else {
        setError(data.error || 'Upload failed.')
      }
    } catch {
      setError('An error occurred during upload.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="content">
      <header>
        <h2>Upload CSV Data</h2>
      </header>

      <div className="upload-container">
        <div className="card upload-card">
          <div className="card-header">
            <h3>Upload CSV Data</h3>
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
                  <li><strong>Note:</strong> Make sure all numeric fields contain valid numbers and there are no missing values</li>
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
    </div>
  )
}
