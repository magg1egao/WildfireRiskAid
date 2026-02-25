# FireSight 🔥
## Wildfire Risk Assessment Dashboard

FireSight is a web-based wildfire risk assessment tool that combines satellite-derived vegetation data, machine learning predictions, and a local AI assistant to help analysts and emergency responders monitor and act on fire-prone areas in real time.

## The Problem 🌍

Wildfires are becoming more frequent and harder to predict. Early detection depends on monitoring vegetation health, moisture levels, and weather conditions across large geographic areas — data that is difficult to interpret quickly without specialized tools. FireSight aims to reduce the gap between raw satellite data and actionable risk decisions.

## Features 🌟

- **Interactive Risk Map**: Visualizes fire-risk zones color-coded by severity (Critical / High / Medium / Low) with per-zone popups showing NDVI, terrain, and vegetation details
- **Vegetation & Moisture Trends**: Tracks NDVI, NBR, and NDWI indices over 7, 30, and 90-day windows with live trend charts
- **ML-Based Predictions**: Uploads field or satellite CSV data and runs an XGBoost classifier to estimate wildfire probability per location
- **AI Assistant**: A locally-run LLM (Meta-Llama-3-8B via GPT4All) answers natural language questions about risk data, vegetation health, and uploaded predictions — no data leaves the machine
- **Active Alerts Panel**: Surfaces critical and high-risk zones with severity badges and recommended actions

## Technical Architecture 🔧

### Satellite Data Pipeline
- Imagery sourced from **Sentinel-2** and **Landsat 8** via **Google Earth Engine (GEE)**
- Spectral indices extracted per sampled location:

| Index | Measures |
|-------|----------|
| NDVI  | Vegetation health — low values indicate dry or stressed vegetation |
| NBR   | Burn ratio — low values suggest burn signatures or fuel accumulation |
| NDWI  | Moisture content — low values indicate dry, fire-prone conditions |

- Dataset covers Alberta wildfire seasons (May–September 2023/2024), ~5,000 sampled geographic points

### Predictive Model
- **XGBoost classifier** trained on satellite + weather features: NDVI, NBR, NDWI, temperature, wind speed/direction, humidity, elevation, slope
- Fire-risk labels generated via vegetation threshold rule (NDVI < 0.2 and NBR < 0.3 → high-risk) in the absence of ground-truth fire data
- ~99% accuracy on labeled dataset; **Random Forest** baseline also trained for comparison

### Backend
- **Flask** REST API with **PostgreSQL + PostGIS** database
- Stores satellite image stats, spectral index summaries, analysis zones, and prediction results
- Key endpoints:
  - `POST /upload/csv` — accepts field data CSV, runs XGBoost predictions, stores results
  - `POST /api/chat` — routes natural language queries to the local LLM
  - `GET /api/stats` / `GET /api/predictions` — retrieve stored analysis data

### Frontend
- **React** SPA (Vite) with three pages:
  - **Dashboard** — risk map (react-leaflet), alerts panel, NDVI/NBR/NDWI trend chart (Chart.js)
  - **Upload** — drag-and-drop CSV upload form with data type selection and model toggle
  - **AI Assistant** — full-page chat interface with context sidebar showing current risk conditions and grouped suggestion prompts

## System Requirements 💻

- **Python**: 3.9+
- **Node.js**: 18+
- **Database**: PostgreSQL 14+ with PostGIS extension
- **Storage**: ~1GB for XGBoost model; ~5GB for GPT4All model (Meta-Llama-3-8B)
- **RAM**: 8GB minimum; 16GB recommended when running the local LLM

## Project Structure 🗂️

```
WildfireRiskAid/
├── backend/                  # Flask API, database models, ML inference
│   ├── app.py
│   ├── requirements.txt
│   └── uploads/
├── frontend/                 # React SPA (Vite)
│   ├── src/
│   │   ├── pages/            # Dashboard, Upload, Chat
│   │   └── components/       # Navbar, RiskMap, AlertsPanel, IndicesChart, ChatPanel
│   └── vite.config.js
├── predictive_model/         # Model training, data extraction, preprocessing
│   ├── XgBoost/
│   ├── RandomForest/
│   ├── DataExtraction/       # Google Earth Engine scripts
│   └── Preprocessing/
└── legacy/                   # Original Jinja2 templates (pre-React)
```

## Running Locally 🚀

**1. Backend**
```bash
cd backend
pip install -r requirements.txt
python app.py          # Flask API → http://localhost:5000
```

**2. Frontend**
```bash
cd frontend
npm install
npm run dev            # React app → http://localhost:5173
```

**3. Environment**

Create a `.env` file in `backend/` with:
```
DATABASE_URL=postgresql://<user>:<password>@localhost:5432/wildfire_db
XGB_MODEL_PATH=../predictive_model/XgBoost/xgboost_wildfire_model.joblib
GPT4ALL_MODEL=Meta-Llama-3-8B-Instruct.Q4_0.gguf
```

PostgreSQL with the PostGIS extension must be running. The app starts without the GPT4All model present — AI features will return a fallback message until the model file is added.
