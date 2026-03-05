from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import numpy as np
import json
import os
import joblib
import pandas as pd

load_dotenv()

app = Flask(__name__)
CORS(app)

# ── Ollama (local LLM) ─────────────────────────────────────────────────────────

import requests as _requests

OLLAMA_URL   = os.getenv('OLLAMA_URL',   'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'gemma2:2b')

def _ollama_available():
    try:
        _requests.get(f'{OLLAMA_URL}/api/tags', timeout=2)
        return True
    except Exception:
        return False

_xgb_path = os.getenv(
    'XGB_MODEL_PATH',
    os.path.join(os.path.dirname(__file__), '..', 'predictive_model', 'XgBoost', 'xgboost_wildfire_model.joblib')
)
try:
    xgb_model = joblib.load(_xgb_path)
except Exception:
    xgb_model = None

# ── Database — SQLite by default, PostgreSQL if DATABASE_URL is set ─────────────

_default_db = 'sqlite:///' + os.path.join(os.path.dirname(os.path.abspath(__file__)), 'wildfire.db')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', _default_db)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')

db = SQLAlchemy(app)


# ── Models ─────────────────────────────────────────────────────────────────────

class Zone(db.Model):
    __tablename__ = 'zones'
    zone_id     = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(100), nullable=False)
    zone_type   = db.Column(db.String(50))
    coordinates = db.Column(db.JSON)       # list of [lat, lon] pairs
    risk_level  = db.Column(db.String(20)) # critical | high | medium | low
    risk_score  = db.Column(db.Float)      # 0–100
    ndvi        = db.Column(db.Float)
    nbr         = db.Column(db.Float)
    ndwi        = db.Column(db.Float)
    terrain     = db.Column(db.String(50))
    vegetation  = db.Column(db.String(50))
    details     = db.Column(db.Text)
    updated_at  = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class VegetationTrend(db.Model):
    __tablename__ = 'vegetation_trends'
    id          = db.Column(db.Integer, primary_key=True)
    label       = db.Column(db.String(50), nullable=False)
    ndvi        = db.Column(db.Float)
    nbr         = db.Column(db.Float)
    ndwi        = db.Column(db.Float)
    period_days = db.Column(db.Integer)  # 7, 30, or 90
    sort_order  = db.Column(db.Integer)


class PredictionResult(db.Model):
    __tablename__    = 'prediction_results'
    prediction_id    = db.Column(db.Integer, primary_key=True)
    filename         = db.Column(db.String(255), nullable=False)
    upload_date      = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    prediction_data  = db.Column(db.JSON)
    analysis_summary = db.Column(db.Text)


# ── Seed data ──────────────────────────────────────────────────────────────────

_ZONES = [
    {
        'name': 'Northridge Canyon',
        'zone_type': 'Canyon',
        'coordinates': [[34.2, -118.5], [34.3, -118.5], [34.3, -118.4], [34.2, -118.4]],
        'risk_level': 'critical', 'risk_score': 89.0,
        'ndvi': 0.37, 'nbr': 0.25, 'ndwi': 0.21,
        'terrain': 'Canyon', 'vegetation': 'Dense',
        'details': 'Extreme dry conditions, increasing winds, and declining vegetation health (NDVI: 0.37)',
    },
    {
        'name': 'Eastern Foothills',
        'zone_type': 'Foothills',
        'coordinates': [[34.1, -118.2], [34.2, -118.2], [34.2, -118.1], [34.1, -118.1]],
        'risk_level': 'high', 'risk_score': 72.0,
        'ndvi': 0.52, 'nbr': 0.31, 'ndwi': 0.28,
        'terrain': 'Foothills', 'vegetation': 'Moderate',
        'details': 'Decreasing moisture levels, temperatures expected to rise to 92°F today',
    },
    {
        'name': 'Pine Ridge Forest',
        'zone_type': 'Ridge',
        'coordinates': [[34.0, -118.3], [34.1, -118.3], [34.1, -118.2], [34.0, -118.2]],
        'risk_level': 'high', 'risk_score': 68.0,
        'ndvi': 0.48, 'nbr': 0.29, 'ndwi': 0.25,
        'terrain': 'Ridge', 'vegetation': 'Dense',
        'details': 'Limited access routes, dense vegetation with declining moisture content',
    },
    {
        'name': 'Valley Grasslands',
        'zone_type': 'Valley',
        'coordinates': [[33.9, -118.4], [34.0, -118.4], [34.0, -118.3], [33.9, -118.3]],
        'risk_level': 'medium', 'risk_score': 45.0,
        'ndvi': 0.61, 'nbr': 0.42, 'ndwi': 0.38,
        'terrain': 'Valley', 'vegetation': 'Sparse',
        'details': 'Moderate conditions, monitoring recommended during dry months',
    },
]

_TRENDS = {
    7: [
        ('Mar 16', 0.65, 0.32, 0.41, 1), ('Mar 17', 0.64, 0.31, 0.40, 2),
        ('Mar 18', 0.62, 0.30, 0.38, 3), ('Mar 19', 0.59, 0.28, 0.35, 4),
        ('Mar 20', 0.57, 0.25, 0.32, 5), ('Mar 21', 0.54, 0.21, 0.30, 6),
        ('Mar 22', 0.52, 0.18, 0.28, 7),
    ],
    30: [
        ('Feb 21', 0.72, 0.41, 0.51, 1), ('Feb 28', 0.68, 0.37, 0.46, 2),
        ('Mar 7',  0.64, 0.31, 0.40, 3), ('Mar 14', 0.58, 0.25, 0.34, 4),
        ('Mar 22', 0.52, 0.18, 0.28, 5),
    ],
    90: [
        ('Dec 22', 0.81, 0.55, 0.62, 1), ('Jan 5',  0.78, 0.51, 0.59, 2),
        ('Jan 19', 0.74, 0.46, 0.54, 3), ('Feb 2',  0.70, 0.40, 0.48, 4),
        ('Feb 16', 0.65, 0.35, 0.42, 5), ('Mar 1',  0.59, 0.27, 0.35, 6),
        ('Mar 22', 0.52, 0.18, 0.28, 7),
    ],
}


def seed_data():
    if Zone.query.count() == 0:
        for z in _ZONES:
            db.session.add(Zone(**z))
    if VegetationTrend.query.count() == 0:
        for days, rows in _TRENDS.items():
            for label, ndvi, nbr, ndwi, order in rows:
                db.session.add(VegetationTrend(
                    label=label, ndvi=ndvi, nbr=nbr, ndwi=ndwi,
                    period_days=days, sort_order=order,
                ))
    db.session.commit()


# ── AI helpers ─────────────────────────────────────────────────────────────────

def _ollama_generate(prompt):
    payload = {
        'model': OLLAMA_MODEL,
        'prompt': prompt,
        'stream': False,
        'options': {'num_predict': 1024},
    }
    resp = _requests.post(f'{OLLAMA_URL}/api/generate', json=payload, timeout=120)
    resp.raise_for_status()
    return resp.json().get('response', '').strip()


def generate_chat_response(query, context=None):
    if not _ollama_available():
        return (
            f"The AI assistant requires Ollama to be running locally with the {OLLAMA_MODEL} model. "
            "Install Ollama (https://ollama.com), then run: "
            f"ollama pull {OLLAMA_MODEL}. "
            "All other dashboard features are fully functional."
        )
    system_prompt = (
        "You are FireSight AI Assistant, an expert in wildfire risk assessment. "
        "Provide concise, actionable information about wildfire risks and prevention strategies."
    )
    user_prompt = f"Context: {json.dumps(context)}\n\nUser query: {query}" if context else query
    try:
        return _ollama_generate(f"{system_prompt}\n\n{user_prompt}")
    except Exception as e:
        return f"Error contacting Ollama: {str(e)}"


def analyze_with_llm(data):
    num = len(data)
    avg_ndvi = f"{data['NDVI'].mean():.3f}" if 'NDVI' in data.columns else 'N/A'

    if not _ollama_available():
        if 'Wildfire_Probability' in data.columns:
            probs = data['Wildfire_Probability']
            high = int((probs > 0.7).sum())
            med  = int(((probs > 0.4) & (probs <= 0.7)).sum())
            low  = int((probs <= 0.4).sum())
            return (
                f"Processed {num} locations. Average NDVI: {avg_ndvi}. "
                f"Risk breakdown — High (>70%): {high}, Medium (40–70%): {med}, Low (<40%): {low}. "
                "AI narrative analysis unavailable — Ollama not running."
            )
        return f"Processed {num} locations. Average NDVI: {avg_ndvi}. AI analysis unavailable."

    def col(name):
        return f"{data[name].mean():.3f}" if name in data.columns else 'N/A'

    prompt = (
        f"Analyze this wildfire risk data:\n"
        f"Dataset: {num} locations\n"
        f"NDVI: {col('NDVI')}, NBR: {col('NBR')}, NDWI: {col('NDWI')}\n"
        f"Temp: {col('Temp')}°C, Humidity: {col('Humidity')}%, Wind: {col('Wind_Spd')} km/h\n"
    )
    if 'Wildfire_Probability' in data.columns:
        probs = data['Wildfire_Probability']
        prompt += (
            f"Avg probability: {probs.mean():.3f}, max: {probs.max():.3f}\n"
            f"High risk (>70%): {(probs > 0.7).sum()}\n"
        )
    prompt += "\nProvide: risk assessment, key factors, and monitoring recommendations."
    try:
        return _ollama_generate(prompt)
    except Exception as e:
        return f"Error contacting Ollama: {str(e)}"


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route('/api/zones', methods=['GET'])
def get_zones():
    zones = Zone.query.all()
    return jsonify([{
        'zone_id':     z.zone_id,
        'name':        z.name,
        'zone_type':   z.zone_type,
        'coordinates': z.coordinates,
        'risk_level':  z.risk_level,
        'risk_score':  z.risk_score,
        'ndvi':        z.ndvi,
        'nbr':         z.nbr,
        'ndwi':        z.ndwi,
        'terrain':     z.terrain,
        'vegetation':  z.vegetation,
        'details':     z.details,
    } for z in zones])


@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    zones = (
        Zone.query
        .filter(Zone.risk_level.in_(['critical', 'high']))
        .order_by(Zone.risk_score.desc())
        .all()
    )
    return jsonify([{
        'name':     z.name,
        'severity': z.risk_level,
        'label':    f"{'Critical' if z.risk_level == 'critical' else 'High'} ({z.risk_score:.0f}%)",
        'details':  z.details,
        'action':   'Deploy Resources' if z.risk_level == 'critical' else 'Monitor',
    } for z in zones])


@app.route('/api/dashboard-stats', methods=['GET'])
def get_dashboard_stats():
    zones = Zone.query.all()
    if not zones:
        return jsonify({
            'risk_level': 'Unknown', 'active_alerts': 0,
            'avg_ndvi': 0, 'wind_speed': 'N/A', 'last_updated': 'N/A',
        })

    alert_count = sum(1 for z in zones if z.risk_level in ('critical', 'high'))
    ndvi_vals   = [z.ndvi for z in zones if z.ndvi is not None]
    avg_ndvi    = round(float(np.mean(ndvi_vals)), 2) if ndvi_vals else 0

    counts = {l: sum(1 for z in zones if z.risk_level == l)
              for l in ('critical', 'high', 'medium', 'low')}
    if counts['critical'] > 0:
        overall = 'Critical'
    elif counts['high'] > 0:
        overall = 'High'
    elif counts['medium'] > 0:
        overall = 'Medium'
    else:
        overall = 'Low'

    last_updated = max(
        (z.updated_at for z in zones if z.updated_at),
        default=datetime.now(timezone.utc),
    )
    return jsonify({
        'risk_level':    overall,
        'active_alerts': alert_count,
        'avg_ndvi':      avg_ndvi,
        'wind_speed':    '12 mph',
        'last_updated':  last_updated.strftime('%B %d, %I:%M %p'),
    })


@app.route('/api/indices-trend', methods=['GET'])
def get_indices_trend():
    days   = int(request.args.get('days', 7))
    trends = (
        VegetationTrend.query
        .filter_by(period_days=days)
        .order_by(VegetationTrend.sort_order)
        .all()
    )
    return jsonify({
        'labels': [t.label for t in trends],
        'ndvi':   [t.ndvi  for t in trends],
        'nbr':    [t.nbr   for t in trends],
        'ndwi':   [t.ndwi  for t in trends],
    })


@app.route('/upload/csv', methods=['POST'])
def upload_csv():
    if 'csvFile' not in request.files:
        return jsonify({'error': 'No file part'})
    file = request.files['csvFile']
    if not file.filename:
        return jsonify({'error': 'No selected file'})

    filename = secure_filename(file.filename)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    try:
        df = pd.read_csv(filepath)
        data_type = request.form.get('csvDataType', 'feature_data')
        run_model = request.form.get('runModel', 'off') == 'on'

        if data_type == 'feature_data':
            required = ['NDVI', 'NBR', 'NDWI', 'Temp', 'Wind_Dir', 'Wind_Spd', 'Humidity', 'Elev', 'Slope']
            missing  = [c for c in required if c not in df.columns]
            if missing:
                return jsonify({'error': f"Missing columns: {', '.join(missing)}"})

            if run_model:
                if xgb_model is None:
                    return jsonify({'error': 'XGBoost model file not found. Set XGB_MODEL_PATH in .env.'})

                probs = xgb_model.predict_proba(df[required])[:, 1]
                df['Wildfire_Probability'] = probs
                gpt_analysis = analyze_with_llm(df)

                pred_data = {
                    'num_locations':        len(df),
                    'avg_probability':      round(float(np.mean(probs)), 3),
                    'max_probability':      round(float(np.max(probs)), 3),
                    'high_risk_locations':  int(np.sum(probs > 0.7)),
                    'medium_risk_locations': int(np.sum((probs > 0.4) & (probs <= 0.7))),
                    'low_risk_locations':   int(np.sum(probs <= 0.4)),
                }
                result = PredictionResult(
                    filename=filename,
                    prediction_data=pred_data,
                    analysis_summary=gpt_analysis[:1000],
                )
                db.session.add(result)
                db.session.commit()
                return jsonify({
                    'success':          True,
                    'message':          'File processed successfully',
                    'prediction_data':  pred_data,
                    'gpt_analysis':     gpt_analysis,
                    'prediction_id':    result.prediction_id,
                    'wildfire_predictions': df.head(100).to_dict(orient='records'),
                })

            return jsonify({'success': True, 'message': 'File uploaded', 'rows': len(df), 'columns': list(df.columns)})

        elif data_type == 'coordinates':
            cols_lower = [c.lower() for c in df.columns]
            if 'latitude' not in cols_lower or 'longitude' not in cols_lower:
                return jsonify({'error': 'Missing required columns: latitude, longitude'})
            return jsonify({'success': True, 'message': 'Coordinate data uploaded', 'points': len(df)})

        elif data_type == 'weather':
            required  = ['date', 'temperature', 'humidity', 'wind_speed']
            cols_lower = [c.lower() for c in df.columns]
            missing   = [c for c in required if c not in cols_lower]
            if missing:
                return jsonify({'error': f"Missing columns: {', '.join(missing)}"})
            return jsonify({'success': True, 'message': 'Weather data uploaded', 'days': len(df)})

        return jsonify({'success': True, 'message': 'File uploaded', 'rows': len(df)})

    except Exception as e:
        return jsonify({'error': f'Error processing file: {str(e)}'})


@app.route('/api/predictions', methods=['GET'])
def get_predictions():
    predictions = PredictionResult.query.order_by(PredictionResult.upload_date.desc()).all()
    return jsonify([{
        'prediction_id':  p.prediction_id,
        'filename':       p.filename,
        'upload_date':    p.upload_date.isoformat(),
        'prediction_data': p.prediction_data,
    } for p in predictions])


@app.route('/api/chat', methods=['POST'])
def chat():
    data  = request.json
    query = data.get('query', '').strip()
    if not query:
        return jsonify({'answer': 'Please enter a question.'})

    q = query.lower()

    # Built-in summarize shortcuts (no LLM needed)
    if 'summarize' in q or 'summary' in q or 'current risk' in q:
        zones = Zone.query.all()
        if zones:
            counts  = {l: sum(1 for z in zones if z.risk_level == l)
                       for l in ('critical', 'high', 'medium', 'low')}
            ndvi_vals = [z.ndvi for z in zones if z.ndvi]
            avg_ndvi  = np.mean(ndvi_vals) if ndvi_vals else 0
            response  = (
                f"FireSight Risk Summary\n\n"
                f"Monitoring {len(zones)} zones:\n"
                f"- Critical: {counts['critical']}\n"
                f"- High: {counts['high']}\n"
                f"- Medium: {counts['medium']}\n"
                f"- Low: {counts['low']}\n\n"
                f"Average NDVI: {avg_ndvi:.2f}\n"
            )
            critical = [z for z in zones if z.risk_level == 'critical']
            if critical:
                response += f"\nMost critical zone: {critical[0].name} (score: {critical[0].risk_score:.0f}%)"
            return jsonify({'answer': response})

    # Pass zone context to LLM if query is zone/risk related
    context = None
    if any(kw in q for kw in ('zone', 'area', 'risk', 'ndvi', 'vegetation', 'alert')):
        zones   = Zone.query.filter(Zone.risk_level.in_(['critical', 'high'])).all()
        context = [{'name': z.name, 'risk_level': z.risk_level,
                    'risk_score': z.risk_score, 'ndvi': z.ndvi,
                    'details': z.details} for z in zones]

    return jsonify({'answer': generate_chat_response(query, context)})


# ── Startup ────────────────────────────────────────────────────────────────────

def init_db():
    db.create_all()
    seed_data()


if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True)
