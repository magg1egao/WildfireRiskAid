from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from geoalchemy2 import Geometry
from sqlalchemy.dialects.postgresql import JSONB
from werkzeug.utils import secure_filename
import numpy as np
import json
import os
import joblib
import pandas as pd

load_dotenv()

app = Flask(__name__)
CORS(app)

# GPT4All — optional, app still runs without the model file
try:
    from gpt4all import GPT4All
    _model_file = os.getenv('GPT4ALL_MODEL', 'Meta-Llama-3-8B-Instruct.Q4_0.gguf')
    llm = GPT4All(_model_file)
except Exception:
    llm = None

# XGBoost prediction model
_xgb_path = os.getenv(
    'XGB_MODEL_PATH',
    os.path.join(os.path.dirname(__file__), '..', 'predictive_model', 'XgBoost', 'xgboost_wildfire_model.joblib')
)
try:
    xgb_model = joblib.load(_xgb_path)
except Exception:
    xgb_model = None

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://localhost/wildfire_db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')

db = SQLAlchemy(app)


# ── AI helpers ────────────────────────────────────────────────────────────────

def generate_chat_response(query, context=None):
    if llm is None:
        return "AI model not available. Please ensure the GPT4All model file is present."

    system_prompt = (
        "You are FireSight AI Assistant, an expert in wildfire risk assessment and management. "
        "You help analyze satellite imagery, vegetation indices, weather patterns, and terrain factors. "
        "Provide concise, actionable information about wildfire risks and prevention strategies."
    )
    user_prompt = f"Context: {json.dumps(context)}\n\nUser query: {query}" if context else query
    return llm.generate(f"{system_prompt}\n\n{user_prompt}", max_tokens=1024).strip()


def analyze_with_gpt4all(data):
    if llm is None:
        return "AI analysis not available. Model file not loaded."

    def col(name):
        return f"{data[name].mean():.3f}" if name in data.columns else "N/A"

    prompt = (
        f"Analyze this wildfire risk data summary:\n"
        f"Dataset: {len(data)} locations\n"
        f"NDVI: {col('NDVI')}, NBR: {col('NBR')}, NDWI: {col('NDWI')}\n"
        f"Temp: {col('Temp')}°C, Humidity: {col('Humidity')}%, Wind: {col('Wind_Spd')} km/h\n"
        f"Elevation: {col('Elev')} m, Slope: {col('Slope')}°\n"
    )
    if 'Wildfire_Probability' in data.columns:
        probs = data['Wildfire_Probability']
        prompt += (
            f"Wildfire probability — avg: {probs.mean():.3f}, max: {probs.max():.3f}\n"
            f"High risk (>70%): {(probs > 0.7).sum()}, "
            f"Medium (40–70%): {((probs > 0.4) & (probs <= 0.7)).sum()}, "
            f"Low (<40%): {(probs <= 0.4).sum()}\n"
        )
    prompt += "\nProvide: overall risk assessment, key contributing factors, and monitoring recommendations."
    return llm.generate(prompt, max_tokens=1024).strip()


# ── Summary helpers ───────────────────────────────────────────────────────────

def summarize_risk_data(risk_assessments):
    if not risk_assessments:
        return "No risk assessment data available."

    levels = [a.risk_level for a in risk_assessments]
    scores = [a.risk_score for a in risk_assessments if a.risk_score]
    recent = max(risk_assessments, key=lambda x: x.assessment_date)

    summary = (
        f"Summary of {len(risk_assessments)} risk assessments:\n"
        f"- Critical: {levels.count('Critical')}, High: {levels.count('High')}, "
        f"Medium: {levels.count('Medium')}, Low: {levels.count('Low')}\n"
    )
    if scores:
        summary += f"- Average risk score: {np.mean(scores):.2f}\n"
    summary += (
        f"\nMost recent ({recent.assessment_date.strftime('%Y-%m-%d')}):\n"
        f"- Level: {recent.risk_level}, Score: {recent.risk_score:.2f}\n"
        f"- Area: {recent.analysis_zone.zone_name if recent.analysis_zone else 'Unknown'}\n"
    )
    return summary


def summarize_vegetation_indices(indices_data):
    if not indices_data:
        return "No vegetation index data available."

    def get(name):
        return next((i for i in indices_data if i.index_name == name), None)

    ndvi, nbr, ndwi = get('NDVI'), get('NBR'), get('NDWI')
    summary = "Vegetation Index Summary:\n"

    if ndvi:
        status = "healthy" if ndvi.mean_value > 0.6 else "stressed" if ndvi.mean_value > 0.4 else "severely stressed"
        summary += f"NDVI: {ndvi.mean_value:.2f} ({status}), range {ndvi.min_value:.2f}–{ndvi.max_value:.2f}\n"
    if nbr:
        status = "no burn" if nbr.mean_value > 0.3 else "moderate burn" if nbr.mean_value > 0.1 else "severe burn"
        summary += f"NBR: {nbr.mean_value:.2f} ({status}), range {nbr.min_value:.2f}–{nbr.max_value:.2f}\n"
    if ndwi:
        status = "adequate" if ndwi.mean_value > 0.4 else "moderate" if ndwi.mean_value > 0.2 else "low"
        summary += f"NDWI: {ndwi.mean_value:.2f} ({status} moisture), range {ndwi.min_value:.2f}–{ndwi.max_value:.2f}\n"

    if ndvi and nbr and ndwi:
        risk_score = (1 - ndvi.mean_value) * 0.4 + (1 - nbr.mean_value) * 0.3 + (1 - ndwi.mean_value) * 0.3
        risk_level = "HIGH" if risk_score > 0.6 else "MODERATE" if risk_score > 0.4 else "LOW"
        summary += f"\nOverall vegetation risk: {risk_level}\n"

    return summary


# ── Database models ───────────────────────────────────────────────────────────

class SatelliteImageStats(db.Model):
    __tablename__ = 'satellite_image_stats'
    stats_id          = db.Column(db.Integer, primary_key=True)
    image_name        = db.Column(db.String(255), nullable=False)
    acquisition_date  = db.Column(db.DateTime, nullable=False)
    sensor_type       = db.Column(db.String(50), nullable=False)
    resolution        = db.Column(db.Float, nullable=False)
    cloud_cover_percentage = db.Column(db.Float)
    region_geometry   = db.Column(Geometry('POLYGON', srid=4326))
    image_metadata    = db.Column(JSONB)
    created_at        = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    spectral_statistics       = db.relationship('SpectralStatistics', backref='image', lazy=True, cascade='all, delete-orphan')
    spectral_index_statistics = db.relationship('SpectralIndexStatistics', backref='image', lazy=True, cascade='all, delete-orphan')
    risk_assessments          = db.relationship('RiskAssessment', backref='image', lazy=True)


class SpectralStatistics(db.Model):
    __tablename__ = 'spectral_statistics'
    stat_id       = db.Column(db.Integer, primary_key=True)
    stats_id      = db.Column(db.Integer, db.ForeignKey('satellite_image_stats.stats_id', ondelete='CASCADE'), nullable=False)
    band_name     = db.Column(db.String(50), nullable=False)
    band_number   = db.Column(db.Integer)
    wavelength_nm = db.Column(db.Float)
    min_value     = db.Column(db.Float)
    max_value     = db.Column(db.Float)
    mean_value    = db.Column(db.Float)
    median_value  = db.Column(db.Float)
    std_dev       = db.Column(db.Float)
    histogram_data = db.Column(JSONB)
    created_at    = db.Column(db.DateTime, default=datetime.now(timezone.utc))


class SpectralIndexStatistics(db.Model):
    __tablename__  = 'spectral_index_statistics'
    index_stat_id  = db.Column(db.Integer, primary_key=True)
    stats_id       = db.Column(db.Integer, db.ForeignKey('satellite_image_stats.stats_id', ondelete='CASCADE'), nullable=False)
    index_name     = db.Column(db.String(50), nullable=False)
    formula        = db.Column(db.String(255))
    min_value      = db.Column(db.Float)
    max_value      = db.Column(db.Float)
    mean_value     = db.Column(db.Float)
    median_value   = db.Column(db.Float)
    std_dev        = db.Column(db.Float)
    percentile_data = db.Column(JSONB)
    created_at     = db.Column(db.DateTime, default=datetime.now(timezone.utc))


class AnalysisZone(db.Model):
    __tablename__ = 'analysis_zones'
    zone_id   = db.Column(db.Integer, primary_key=True)
    zone_name = db.Column(db.String(100), nullable=False)
    zone_type = db.Column(db.String(50))
    geometry  = db.Column(Geometry('POLYGON', srid=4326))
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    risk_assessments = db.relationship('RiskAssessment', backref='zone', lazy=True)


class RiskAssessment(db.Model):
    __tablename__     = 'risk_assessments'
    assessment_id     = db.Column(db.Integer, primary_key=True)
    stats_id          = db.Column(db.Integer, db.ForeignKey('satellite_image_stats.stats_id'))
    zone_id           = db.Column(db.Integer, db.ForeignKey('analysis_zones.zone_id'))
    assessment_date   = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    risk_level        = db.Column(db.String(20), nullable=False)
    risk_score        = db.Column(db.Float)
    confidence_level  = db.Column(db.Float)
    weather_conditions = db.Column(JSONB)
    model_version     = db.Column(db.String(50))
    summary           = db.Column(db.Text)
    created_at        = db.Column(db.DateTime, default=datetime.now(timezone.utc))


class PredictionResult(db.Model):
    __tablename__   = 'prediction_results'
    prediction_id   = db.Column(db.Integer, primary_key=True)
    filename        = db.Column(db.String(255), nullable=False)
    upload_date     = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    prediction_data = db.Column(JSONB)
    analysis_summary = db.Column(db.Text)
    created_at      = db.Column(db.DateTime, default=datetime.now(timezone.utc))


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route('/upload/csv', methods=['POST'])
def upload_csv():
    if 'csvFile' not in request.files:
        return jsonify({"error": "No file part"})
    file = request.files['csvFile']
    if not file.filename:
        return jsonify({"error": "No selected file"})

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
            missing = [c for c in required if c not in df.columns]
            if missing:
                return jsonify({"error": f"Missing columns: {', '.join(missing)}"})

            if run_model:
                if xgb_model is None:
                    return jsonify({"error": "Prediction model not available."})
                probs = xgb_model.predict_proba(df[required])[:, 1]
                df['Wildfire_Probability'] = probs
                gpt_analysis = analyze_with_gpt4all(df)

                result = PredictionResult(
                    filename=filename,
                    prediction_data={
                        'num_locations': len(df),
                        'avg_probability': float(np.mean(probs)),
                        'max_probability': float(np.max(probs)),
                        'high_risk_locations': int(np.sum(probs > 0.7)),
                    },
                    analysis_summary=gpt_analysis[:500],
                )
                db.session.add(result)
                db.session.commit()
                return jsonify({
                    "success": True,
                    "message": "File uploaded and processed successfully",
                    "wildfire_predictions": df.to_dict(orient='records'),
                    "gpt_analysis": gpt_analysis,
                    "prediction_id": result.prediction_id,
                })

            return jsonify({"success": True, "message": "File uploaded", "rows": len(df), "columns": list(df.columns)})

        elif data_type == 'coordinates':
            cols_lower = [c.lower() for c in df.columns]
            if 'latitude' not in cols_lower or 'longitude' not in cols_lower:
                return jsonify({"error": "Missing required columns: latitude, longitude"})
            return jsonify({"success": True, "message": "Coordinate data uploaded", "points": len(df)})

        elif data_type == 'weather':
            required = ['date', 'temperature', 'humidity', 'wind_speed']
            cols_lower = [c.lower() for c in df.columns]
            missing = [c for c in required if c not in cols_lower]
            if missing:
                return jsonify({"error": f"Missing columns: {', '.join(missing)}"})
            return jsonify({"success": True, "message": "Weather data uploaded", "days": len(df)})

        return jsonify({"success": True, "message": "File uploaded", "rows": len(df), "columns": list(df.columns)})

    except Exception as e:
        return jsonify({"error": f"Error processing file: {str(e)}"})


@app.route('/api/predictions', methods=['GET'])
def get_predictions():
    predictions = PredictionResult.query.order_by(PredictionResult.upload_date.desc()).all()
    return jsonify([{
        'prediction_id': p.prediction_id,
        'filename': p.filename,
        'upload_date': p.upload_date.isoformat(),
        'avg_probability': p.prediction_data.get('avg_probability'),
        'high_risk_locations': p.prediction_data.get('high_risk_locations'),
    } for p in predictions])


@app.route('/api/stats', methods=['GET'])
def get_stats():
    stats = SatelliteImageStats.query.order_by(SatelliteImageStats.acquisition_date.desc()).all()
    return jsonify([{
        'stats_id': s.stats_id,
        'image_name': s.image_name,
        'acquisition_date': s.acquisition_date.isoformat(),
        'sensor_type': s.sensor_type,
        'risk_assessments': len(s.risk_assessments),
    } for s in stats])


@app.route('/api/stats/<int:stats_id>', methods=['GET'])
def get_stat_details(stats_id):
    stats   = SatelliteImageStats.query.get_or_404(stats_id)
    spectral = SpectralStatistics.query.filter_by(stats_id=stats_id).all()
    indices  = SpectralIndexStatistics.query.filter_by(stats_id=stats_id).all()
    return jsonify({
        'stats_id': stats.stats_id,
        'image_name': stats.image_name,
        'acquisition_date': stats.acquisition_date.isoformat(),
        'sensor_type': stats.sensor_type,
        'resolution': stats.resolution,
        'cloud_cover_percentage': stats.cloud_cover_percentage,
        'spectral_bands': [{'band_name': s.band_name, 'band_number': s.band_number, 'min_value': s.min_value, 'max_value': s.max_value, 'mean_value': s.mean_value} for s in spectral],
        'spectral_indices': [{'index_name': i.index_name, 'min_value': i.min_value, 'max_value': i.max_value, 'mean_value': i.mean_value} for i in indices],
    })


@app.route('/api/chat', methods=['POST'])
def chat():
    data         = request.json
    query        = data.get('query', '')
    context_type = data.get('context_type')
    context_id   = data.get('context_id')

    context = None
    if context_type == 'risk' and context_id:
        a = RiskAssessment.query.get(context_id)
        if a:
            context = {'risk_level': a.risk_level, 'risk_score': a.risk_score, 'assessment_date': a.assessment_date.isoformat(), 'zone_name': a.analysis_zone.zone_name if a.analysis_zone else 'Unknown', 'weather': a.weather_conditions}
    elif context_type == 'vegetation' and context_id:
        idxs = SpectralIndexStatistics.query.filter_by(stats_id=context_id).all()
        if idxs:
            context = {'indices': [{'name': i.index_name, 'mean': i.mean_value, 'min': i.min_value, 'max': i.max_value} for i in idxs]}
    elif context_type == 'prediction' and context_id:
        p = PredictionResult.query.get(context_id)
        if p:
            context = {'filename': p.filename, 'upload_date': p.upload_date.isoformat(), 'prediction_data': p.prediction_data, 'analysis_summary': p.analysis_summary}

    q = query.lower()
    if q.startswith('summarize'):
        if 'risk' in q or 'alerts' in q:
            assessments = RiskAssessment.query.order_by(RiskAssessment.assessment_date.desc()).limit(10).all()
            response = summarize_risk_data(assessments)
        elif 'vegetation' in q or 'ndvi' in q or 'indices' in q:
            recent = SatelliteImageStats.query.order_by(SatelliteImageStats.acquisition_date.desc()).first()
            indices = SpectralIndexStatistics.query.filter_by(stats_id=recent.stats_id).all() if recent else []
            response = summarize_vegetation_indices(indices)
        elif 'prediction' in q:
            recent = PredictionResult.query.order_by(PredictionResult.upload_date.desc()).limit(5).all()
            response = ("Recent Predictions:\n\n" + "".join(f"- {p.filename}: avg prob {p.prediction_data.get('avg_probability', 0):.2f}, high risk: {p.prediction_data.get('high_risk_locations', 0)}\n" for p in recent)) if recent else "No prediction results available."
        else:
            recent_p = PredictionResult.query.order_by(PredictionResult.upload_date.desc()).limit(3).all()
            recent_a = RiskAssessment.query.order_by(RiskAssessment.assessment_date.desc()).limit(5).all()
            pred_text = "".join(f"- {p.filename}: avg {p.prediction_data.get('avg_probability', 0):.2f}\n" for p in recent_p) if recent_p else "None available.\n"
            response = f"FireSight Summary\n\nRecent Predictions:\n{pred_text}\n{summarize_risk_data(recent_a)}"
    else:
        response = generate_chat_response(query, context)

    return jsonify({"answer": response})


@app.route('/api/summary', methods=['GET'])
def get_summary():
    summary_type = request.args.get('type', 'general')
    entity_id    = request.args.get('id')

    if summary_type == 'risk':
        assessments = [RiskAssessment.query.get_or_404(entity_id)] if entity_id else RiskAssessment.query.order_by(RiskAssessment.assessment_date.desc()).limit(5).all()
        return jsonify({"summary": summarize_risk_data(assessments)})

    if summary_type == 'vegetation':
        if entity_id:
            indices = SpectralIndexStatistics.query.filter_by(stats_id=entity_id).all()
        else:
            recent = SatelliteImageStats.query.order_by(SatelliteImageStats.acquisition_date.desc()).first()
            indices = SpectralIndexStatistics.query.filter_by(stats_id=recent.stats_id).all() if recent else []
        return jsonify({"summary": summarize_vegetation_indices(indices)})

    if summary_type == 'prediction':
        if entity_id:
            p = PredictionResult.query.get_or_404(entity_id)
            summary = (f"Prediction: {p.filename}\n- Uploaded: {p.upload_date.strftime('%Y-%m-%d %H:%M')}\n- Locations: {p.prediction_data.get('num_locations')}\n- Avg probability: {p.prediction_data.get('avg_probability', 0):.2f}\n- High risk: {p.prediction_data.get('high_risk_locations', 0)}\n\n{p.analysis_summary}")
        else:
            recent = PredictionResult.query.order_by(PredictionResult.upload_date.desc()).limit(5).all()
            summary = ("Recent Predictions:\n\n" + "".join(f"- {p.filename}: avg {p.prediction_data.get('avg_probability', 0):.2f}, high risk: {p.prediction_data.get('high_risk_locations', 0)}\n" for p in recent)) if recent else "No predictions available."
        return jsonify({"summary": summary})

    # general
    recent_p = PredictionResult.query.order_by(PredictionResult.upload_date.desc()).limit(3).all()
    recent_a = RiskAssessment.query.order_by(RiskAssessment.assessment_date.desc()).limit(5).all()
    pred_text = "".join(f"- {p.filename}: avg {p.prediction_data.get('avg_probability', 0):.2f}\n" for p in recent_p) if recent_p else "No recent predictions.\n"
    return jsonify({"summary": f"FireSight Summary\n\nRecent Predictions:\n{pred_text}\n{summarize_risk_data(recent_a)}"})


def init_db():
    with db.engine.connect() as conn:
        conn.execute(db.text('CREATE EXTENSION IF NOT EXISTS postgis'))
        conn.commit()
    db.create_all()


if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True)
