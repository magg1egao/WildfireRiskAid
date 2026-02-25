# FireSight — Wildfire Risk Assessment Dashboard

FireSight is a web-based wildfire risk assessment tool that combines satellite-derived vegetation data, machine learning predictions, and an AI assistant to help monitor and analyze fire-prone areas.

---

## The Problem

Wildfires are becoming more frequent and harder to predict. Early detection and risk assessment depend on monitoring vegetation health, moisture levels, and weather conditions across large geographic areas — data that is hard to interpret quickly without specialized tools.

---

## What FireSight Aims to Do

FireSight aims to centralize wildfire risk intelligence into a single dashboard that lets analysts and responders:

- **Monitor vegetation health** using satellite-derived indices (NDVI, NBR, NDWI) over time
- **Identify high-risk zones** before a fire starts, based on declining vegetation and moisture trends
- **Run ML-based predictions** on uploaded field or satellite data to get wildfire probability estimates per location
- **Get AI-generated analysis** of the data in plain language, without needing to interpret raw numbers manually

The goal is to reduce the gap between raw satellite data and actionable risk decisions.

---

## Current Solution

### Data

Satellite data is extracted from **Sentinel-2 and Landsat 8** imagery via **Google Earth Engine (GEE)**. Key spectral indices computed:

| Index | What it measures |
|-------|-----------------|
| NDVI  | Vegetation health — low values indicate dry or stressed vegetation |
| NBR   | Burn ratio — low values suggest burn signatures or fuel accumulation |
| NDWI  | Moisture content — low values indicate dry conditions |

Data covers Alberta wildfire seasons (May–September 2023/2024), sampled at ~5,000 geographic points.

### Predictive Model

An **XGBoost classifier** trained on the extracted satellite + weather features predicts wildfire probability per location. Input features include NDVI, NBR, NDWI, temperature, wind speed/direction, humidity, elevation, and slope.

Fire-risk labels were generated using a vegetation threshold rule (NDVI < 0.2 and NBR < 0.3 → high-risk) in the absence of ground-truth fire data. The model achieves ~99% accuracy on the labeled dataset.

A **Random Forest** model was also trained as a baseline.

### Backend

A **Flask API** serves prediction and analysis endpoints. It connects to a **PostgreSQL + PostGIS** database that stores satellite image statistics, spectral index summaries, analysis zones, and prediction results.

Key endpoints:
- `POST /upload/csv` — accepts a CSV of field data, runs XGBoost predictions, stores results
- `POST /api/chat` — routes a natural language query to the local AI model
- `GET /api/stats` / `GET /api/predictions` — retrieve stored analysis data

### AI Assistant

A locally-run **GPT4All** model (Meta-Llama-3-8B) answers natural language questions about the current risk data. It can summarize risk assessments, explain vegetation index trends, and interpret uploaded prediction results without sending data to an external API.

### Frontend

A **React** single-page app (Vite) with four main views:

- **Dashboard** — risk map (Leaflet), active alerts panel, NDVI/NBR/NDWI trend chart
- **Upload** — drag-and-drop CSV upload form to run the prediction model
- **AI Assistant** — full-page chat interface with context-aware suggestions

---

## Project Structure

```
WildfireRiskAid/
├── backend/              # Flask API, database models, ML inference
├── frontend/             # React SPA (Vite)
├── predictive_model/     # Model training scripts, data extraction, preprocessing
│   ├── XgBoost/
│   ├── RandomForest/
│   ├── DataExtraction/   # Google Earth Engine scripts
│   └── Preprocessing/
├── legacy/               # Original Jinja2 templates (pre-React)
└── summarizer/           # Standalone summarization experiments
```

---

## Running Locally

**Backend**
```bash
cd backend
pip install -r requirements.txt
python app.py          # Flask API on http://localhost:5000
```

**Frontend**
```bash
cd frontend
npm install
npm run dev            # React app on http://localhost:5173
```

PostgreSQL with PostGIS must be running. Set credentials in a `.env` file (see `.env.example`).
