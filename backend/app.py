from flask import Flask, request, jsonify
from flask_cors import CORS
from transformers import pipeline
from dotenv import load_dotenv
from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from geoalchemy2 import Geometry
from sqlalchemy.dialects.postgresql import JSONB
from gpt4all import GPT4All
from werkzeug.utils import secure_filename
import numpy as np
import json
import os
import joblib
import pandas as pd

# load env variables
load_dotenv()

# initialize Flask
app = Flask(__name__)
CORS(app)

# Initialize GPT4ALL
model = GPT4All("Meta-Llama-3-8B-Instruct.Q4_0.gguf")

# load the XGBoost predictive model
xgb_model = joblib.load('/Users/hwey/Desktop/projects/WildfireRiskAid/predictive_model/XgBoost/xgboost_wildfire_model.joblib')

# load configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://hwey:1234@localhost:5432/wildfire_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# initialize database
db = SQLAlchemy(app)

################### FUNCTIONS ################
# Function to generate chat responses
def generate_chat_response(query, context=None):
    # Create a system prompt with FireSight-specific knowledge
    system_prompt = """You are FireSight AI Assistant, an expert in wildfire risk assessment and management.
    You help analyze satellite imagery, vegetation indices, weather patterns, and terrain factors to assess wildfire risks.
    Provide concise, actionable information about wildfire risks and prevention strategies."""
    
    # Include context in the prompt if available
    if context:
        context_str = json.dumps(context)
        user_prompt = f"Context: {context_str}\n\nUser query: {query}"
    else:
        user_prompt = query
    
    # Full prompt with system and user parts
    full_prompt = f"{system_prompt}\n\n{user_prompt}"
    
    # Generate response using GPT4ALL
    response = model.generate(full_prompt, max_tokens=1024)
    
    return response.strip()

# Function to summarize risk assessments
def summarize_risk_data(risk_assessments):
    if not risk_assessments:
        return "No risk assessment data available."
    
    # Extract key information
    risk_levels = [assessment.risk_level for assessment in risk_assessments]
    risk_scores = [assessment.risk_score for assessment in risk_assessments if assessment.risk_score]
    
    # Count risk levels
    level_counts = {
        'Critical': risk_levels.count('Critical'),
        'High': risk_levels.count('High'),
        'Medium': risk_levels.count('Medium'),
        'Low': risk_levels.count('Low')
    }
    
    # Calculate averages
    avg_score = np.mean(risk_scores) if risk_scores else None
    
    # Get the most recent assessment
    recent = max(risk_assessments, key=lambda x: x.assessment_date)
    
    # Create a summary
    summary = (
        f"Summary of {len(risk_assessments)} risk assessments:\n"
        f"- Critical alerts: {level_counts['Critical']}\n"
        f"- High alerts: {level_counts['High']}\n"
        f"- Medium alerts: {level_counts['Medium']}\n"
        f"- Low alerts: {level_counts['Low']}\n"
    )
    
    if avg_score:
        summary += f"- Average risk score: {avg_score:.2f}\n"
    
    summary += (
        f"\nMost recent assessment ({recent.assessment_date.strftime('%Y-%m-%d')}):\n"
        f"- Risk level: {recent.risk_level}\n"
        f"- Risk score: {recent.risk_score:.2f}\n"
        f"- Area: {recent.analysis_zone.zone_name}\n"
    )
    
    return summary

# Function to summarize vegetation indices
def summarize_vegetation_indices(indices_data):
    if not indices_data:
        return "No vegetation index data available."
    
    # Extract key data
    ndvi_data = [idx for idx in indices_data if idx.index_name == 'NDVI']
    nbr_data = [idx for idx in indices_data if idx.index_name == 'NBR']
    ndwi_data = [idx for idx in indices_data if idx.index_name == 'NDWI']
    
    summary = "Vegetation Index Summary:\n"
    
    # Add NDVI summary
    if ndvi_data:
        ndvi = ndvi_data[0]
        health_status = "healthy" if ndvi.mean_value > 0.6 else "stressed" if ndvi.mean_value > 0.4 else "severely stressed"
        summary += (
            f"NDVI (vegetation health):\n"
            f"- Average: {ndvi.mean_value:.2f} ({health_status})\n"
            f"- Range: {ndvi.min_value:.2f} to {ndvi.max_value:.2f}\n"
        )
    
    # Add NBR summary
    if nbr_data:
        nbr = nbr_data[0]
        burn_status = "no burn" if nbr.mean_value > 0.3 else "moderate burn" if nbr.mean_value > 0.1 else "severe burn"
        summary += (
            f"NBR (burn ratio):\n"
            f"- Average: {nbr.mean_value:.2f} ({burn_status})\n"
            f"- Range: {nbr.min_value:.2f} to {nbr.max_value:.2f}\n"
        )
    
    # Add NDWI summary
    if ndwi_data:
        ndwi = ndwi_data[0]
        moisture_status = "adequate" if ndwi.mean_value > 0.4 else "moderate" if ndwi.mean_value > 0.2 else "low"
        summary += (
            f"NDWI (moisture):\n"
            f"- Average: {ndwi.mean_value:.2f} ({moisture_status} moisture)\n"
            f"- Range: {ndwi.min_value:.2f} to {ndwi.max_value:.2f}\n"
        )
    
    # Add recommendation
    if ndvi_data and nbr_data and ndwi_data:
        combined_risk = (1 - ndvi.mean_value) * 0.4 + (1 - nbr.mean_value) * 0.3 + (1 - ndwi.mean_value) * 0.3
        risk_level = "high" if combined_risk > 0.6 else "moderate" if combined_risk > 0.4 else "low"
        summary += f"\nOverall vegetation risk level: {risk_level.upper()}\n"
        
        if risk_level == "high":
            summary += "Recommendation: Immediate monitoring and preventive measures advised."
        elif risk_level == "moderate":
            summary += "Recommendation: Regular monitoring and preparedness advised."
        else:
            summary += "Recommendation: Standard monitoring protocols sufficient."
    
    return summary

# Analyze the wildfire risk with gpt4all
def analyze_with_gpt4all(data):
    # Create a summary of the data instead of sending the entire dataset
    summary = {
        'num_rows': len(data),
        'columns': list(data.columns),
        'ndvi_avg': data['NDVI'].mean() if 'NDVI' in data.columns else None,
        'nbr_avg': data['NBR'].mean() if 'NBR' in data.columns else None,
        'ndwi_avg': data['NDWI'].mean() if 'NDWI' in data.columns else None,
        'temp_avg': data['Temp'].mean() if 'Temp' in data.columns else None,
        'humidity_avg': data['Humidity'].mean() if 'Humidity' in data.columns else None,
        'wind_spd_avg': data['Wind_Spd'].mean() if 'Wind_Spd' in data.columns else None,
        'elev_avg': data['Elev'].mean() if 'Elev' in data.columns else None,
        'slope_avg': data['Slope'].mean() if 'Slope' in data.columns else None
    }
    
    # Add high-risk information if wildfire probability has been calculated
    if 'Wildfire_Probability' in data.columns:
        summary['avg_probability'] = data['Wildfire_Probability'].mean()
        summary['max_probability'] = data['Wildfire_Probability'].max()
        summary['high_risk_count'] = (data['Wildfire_Probability'] > 0.7).sum()
        summary['medium_risk_count'] = ((data['Wildfire_Probability'] > 0.4) & (data['Wildfire_Probability'] <= 0.7)).sum()
        summary['low_risk_count'] = (data['Wildfire_Probability'] <= 0.4).sum()
    
    # Create a prompt with the summary instead of the entire dataset
    prompt = f"""Analyze the following wildfire risk data summary:
    
    Dataset size: {summary['num_rows']} locations
    
    Average metrics:
    - NDVI (vegetation health): {summary['ndvi_avg']:.3f} if applicable
    - NBR (burn ratio): {summary['nbr_avg']:.3f} if applicable
    - NDWI (moisture): {summary['ndwi_avg']:.3f} if applicable
    - Temperature: {summary['temp_avg']:.2f}°C if applicable
    - Humidity: {summary['humidity_avg']:.2f}% if applicable
    - Wind speed: {summary['wind_spd_avg']:.2f} km/h if applicable
    - Elevation: {summary['elev_avg']:.2f} m if applicable
    - Slope: {summary['slope_avg']:.2f}° if applicable
    
    """
    
    # Add risk analysis if available
    if 'Wildfire_Probability' in data.columns:
        prompt += f"""
    Wildfire risk assessment:
    - Average probability: {summary['avg_probability']:.3f}
    - Maximum probability: {summary['max_probability']:.3f}
    - High risk locations (>70%): {summary['high_risk_count']} ({summary['high_risk_count']/summary['num_rows']*100:.1f}%)
    - Medium risk locations (40-70%): {summary['medium_risk_count']} ({summary['medium_risk_count']/summary['num_rows']*100:.1f}%)
    - Low risk locations (<40%): {summary['low_risk_count']} ({summary['low_risk_count']/summary['num_rows']*100:.1f}%)
    """
    
    prompt += """
    Based on this data, provide:
    1. An assessment of the overall wildfire risk in the analyzed region
    2. Key factors contributing to the risk
    3. Recommendations for monitoring and prevention
    """
    
    # Generate response using GPT4ALL
    response = model.generate(prompt, max_tokens=1024)
    
    return response.strip()

################### DATABASE #################

# Define models
class SatelliteImageStats(db.Model):
    __tablename__ = 'satellite_image_stats'
    
    stats_id = db.Column(db.Integer, primary_key=True)
    image_name = db.Column(db.String(255), nullable=False)
    acquisition_date = db.Column(db.DateTime, nullable=False)
    sensor_type = db.Column(db.String(50), nullable=False)
    resolution = db.Column(db.Float, nullable=False)
    cloud_cover_percentage = db.Column(db.Float)
    region_geometry = db.Column(Geometry('POLYGON', srid=4326))
    image_metadata = db.Column(JSONB)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    
    # Relationships
    spectral_statistics = db.relationship('SpectralStatistics', backref='satellite_image_stats', lazy=True, cascade="all, delete-orphan")
    spectral_index_statistics = db.relationship('SpectralIndexStatistics', backref='satellite_image_stats', lazy=True, cascade="all, delete-orphan")
    risk_assessments = db.relationship('RiskAssessment', backref='satellite_image_stats', lazy=True)

class SpectralStatistics(db.Model):
    __tablename__ = 'spectral_statistics'
    
    stat_id = db.Column(db.Integer, primary_key=True)
    stats_id = db.Column(db.Integer, db.ForeignKey('satellite_image_stats.stats_id', ondelete='CASCADE'), nullable=False)
    band_name = db.Column(db.String(50), nullable=False)
    band_number = db.Column(db.Integer)
    wavelength_nm = db.Column(db.Float)
    min_value = db.Column(db.Float)
    max_value = db.Column(db.Float)
    mean_value = db.Column(db.Float)
    median_value = db.Column(db.Float)
    std_dev = db.Column(db.Float)
    histogram_data = db.Column(JSONB)  # Store histogram as JSON
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))

class SpectralIndexStatistics(db.Model):
    __tablename__ = 'spectral_index_statistics'
    
    index_stat_id = db.Column(db.Integer, primary_key=True)
    stats_id = db.Column(db.Integer, db.ForeignKey('satellite_image_stats.stats_id', ondelete='CASCADE'), nullable=False)
    index_name = db.Column(db.String(50), nullable=False)
    formula = db.Column(db.String(255))
    min_value = db.Column(db.Float)
    max_value = db.Column(db.Float)
    mean_value = db.Column(db.Float)
    median_value = db.Column(db.Float)
    std_dev = db.Column(db.Float)
    percentile_data = db.Column(JSONB)  # Store percentiles as JSON
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))

class AnalysisZone(db.Model):
    __tablename__ = 'analysis_zones'
    
    zone_id = db.Column(db.Integer, primary_key=True)
    zone_name = db.Column(db.String(100), nullable=False)
    zone_type = db.Column(db.String(50))
    geometry = db.Column(Geometry('POLYGON', srid=4326))
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    
    # Relationships
    risk_assessments = db.relationship('RiskAssessment', backref='analysis_zone', lazy=True)

class RiskAssessment(db.Model):
    __tablename__ = 'risk_assessments'
    
    assessment_id = db.Column(db.Integer, primary_key=True)
    stats_id = db.Column(db.Integer, db.ForeignKey('satellite_image_stats.stats_id'))
    zone_id = db.Column(db.Integer, db.ForeignKey('analysis_zones.zone_id'))
    assessment_date = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    risk_level = db.Column(db.String(20), nullable=False)
    risk_score = db.Column(db.Float)
    confidence_level = db.Column(db.Float)
    weather_conditions = db.Column(JSONB)
    model_version = db.Column(db.String(50))
    summary = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    
    # Relationships
    simulations = db.relationship('FireSimulation', backref='risk_assessment', lazy=True, cascade="all, delete-orphan")

class FireSimulation(db.Model):
    __tablename__ = 'fire_simulations'
    
    simulation_id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey('risk_assessments.assessment_id'))
    simulation_parameters = db.Column(JSONB)
    simulation_results = db.Column(JSONB)  # Store simulation results directly as JSON
    time_horizon = db.Column(db.Integer)  # in hours
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))

class ModelConfiguration(db.Model):
    __tablename__ = 'model_configurations'
    
    config_id = db.Column(db.Integer, primary_key=True)
    model_name = db.Column(db.String(100), nullable=False)
    model_type = db.Column(db.String(50), nullable=False)
    model_version = db.Column(db.String(50), nullable=False)
    parameters = db.Column(JSONB)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))

class PredictionResult(db.Model):
    __tablename__ = 'prediction_results'
    
    prediction_id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    prediction_data = db.Column(JSONB)  # Store prediction results as JSON
    analysis_summary = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))

################### ROUTES ###################

@app.route('/upload/csv', methods=['POST'])
def upload_csv():
    if 'csvFile' not in request.files:  # Changed from 'file' to 'csvFile' to match the form input name
        return jsonify({"error": "No file part"})
    
    file = request.files['csvFile']
    if file.filename == '':
        return jsonify({"error": "No selected file"})
    
    if file:
        filename = secure_filename(file.filename)
        
        # Make sure UPLOAD_FOLDER is defined
        if 'UPLOAD_FOLDER' not in app.config:
            app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
            
        # Ensure the upload directory exists
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        try:
            # Load the CSV data
            df = pd.read_csv(filepath)

            # Get additional form data
            data_type = request.form.get('csvDataType', 'feature_data')
            region = request.form.get('csvRegion', 'from_csv')
            run_model = request.form.get('runModel', 'off') == 'on'
            
            # Check for required columns based on data type
            if data_type == 'feature_data':
                # For XGBoost prediction model
                required_columns = ['NDVI','NBR','NDWI','Temp','Wind_Dir','Wind_Spd','Humidity','Elev','Slope']
                if not all(col in df.columns for col in required_columns):
                    return jsonify({"error": f"Missing required columns in CSV. Required: {', '.join(required_columns)}"})
                
                if run_model:
                    # Predict wildfire probability
                    features = df[required_columns]
                    wildfire_probabilities = xgb_model.predict_proba(features)[:, 1]  # Get probability of wildfire
                    df['Wildfire_Probability'] = wildfire_probabilities

                    # Analyze data with GPT-4All
                    gpt_analysis = analyze_with_gpt4all(df)
                    
                    # Store prediction results in database
                    prediction_data = {
                        'num_locations': len(df),
                        'avg_probability': float(np.mean(wildfire_probabilities)),
                        'max_probability': float(np.max(wildfire_probabilities)),
                        'high_risk_locations': int(np.sum(wildfire_probabilities > 0.7))
                    }
                    
                    new_prediction = PredictionResult(
                        filename=filename,
                        prediction_data=prediction_data,
                        analysis_summary=gpt_analysis[:500]  # Store a truncated version of the analysis
                    )
                    db.session.add(new_prediction)
                    db.session.commit()

                    # Return results
                    return jsonify({
                        "success": True,
                        "message": "File uploaded and processed successfully",
                        "wildfire_predictions": df.to_dict(orient='records'),
                        "gpt_analysis": gpt_analysis,
                        "prediction_id": new_prediction.prediction_id
                    })
                else:
                    # Just save the file without running the model
                    return jsonify({
                        "success": True,
                        "message": "File uploaded successfully",
                        "rows": len(df),
                        "columns": list(df.columns)
                    })
            
            elif data_type == 'coordinates':
                # Handle coordinate boundary data
                required_columns = ['latitude', 'longitude']
                if not all(col.lower() in [c.lower() for c in df.columns] for col in required_columns):
                    return jsonify({"error": f"Missing required columns in CSV. Required: {', '.join(required_columns)}"})
                
                return jsonify({
                    "success": True,
                    "message": "Coordinate boundary data uploaded successfully",
                    "points": len(df)
                })
                
            elif data_type == 'weather':
                # Handle weather conditions data
                required_columns = ['date', 'temperature', 'humidity', 'wind_speed']
                if not all(col.lower() in [c.lower() for c in df.columns] for col in required_columns):
                    return jsonify({"error": f"Missing required columns in CSV. Required: {', '.join(required_columns)}"})
                
                return jsonify({
                    "success": True,
                    "message": "Weather condition data uploaded successfully",
                    "days": len(df)
                })
            
            # Default response if no specific handling
            return jsonify({
                "success": True,
                "message": "File uploaded successfully",
                "rows": len(df),
                "columns": list(df.columns)
            })
            
        except Exception as e:
            return jsonify({
                "error": f"Error processing CSV file: {str(e)}"
            })

    return jsonify({"error": "Failed to process file"})

@app.route('/api/predictions', methods=['GET'])
def get_predictions():
    predictions = PredictionResult.query.order_by(PredictionResult.upload_date.desc()).all()
    return jsonify([{
        'prediction_id': p.prediction_id,
        'filename': p.filename,
        'upload_date': p.upload_date.isoformat(),
        'avg_probability': p.prediction_data.get('avg_probability'),
        'high_risk_locations': p.prediction_data.get('high_risk_locations')
    } for p in predictions])

# API Routes
@app.route('/api/stats', methods=['GET'])
def get_stats():
    stats = SatelliteImageStats.query.order_by(SatelliteImageStats.acquisition_date.desc()).all()
    return jsonify([{
        'stats_id': s.stats_id,
        'image_name': s.image_name,
        'acquisition_date': s.acquisition_date.isoformat(),
        'sensor_type': s.sensor_type,
        'risk_assessments': len(s.risk_assessments)
    } for s in stats])

@app.route('/api/stats/<int:stats_id>', methods=['GET'])
def get_stat_details(stats_id):
    stats = SatelliteImageStats.query.get_or_404(stats_id)
    spectral_stats = SpectralStatistics.query.filter_by(stats_id=stats_id).all()
    index_stats = SpectralIndexStatistics.query.filter_by(stats_id=stats_id).all()
    
    return jsonify({
        'stats_id': stats.stats_id,
        'image_name': stats.image_name,
        'acquisition_date': stats.acquisition_date.isoformat(),
        'sensor_type': stats.sensor_type,
        'resolution': stats.resolution,
        'cloud_cover_percentage': stats.cloud_cover_percentage,
        'spectral_bands': [{
            'band_name': s.band_name,
            'band_number': s.band_number,
            'min_value': s.min_value,
            'max_value': s.max_value,
            'mean_value': s.mean_value
        } for s in spectral_stats],
        'spectral_indices': [{
            'index_name': i.index_name,
            'min_value': i.min_value,
            'max_value': i.max_value,
            'mean_value': i.mean_value
        } for i in index_stats]
    })

@app.route('/api/chat', methods=["POST"])
def chat():
    query = request.json.get('query', '')
    context_type = request.json.get('context_type', None)
    context_id = request.json.get('context_id', None)
    
    # Get appropriate context based on request
    context = None
    if context_type == 'risk' and context_id:
        assessment = RiskAssessment.query.get(context_id)
        if assessment:
            context = {
                'risk_level': assessment.risk_level,
                'risk_score': assessment.risk_score,
                'assessment_date': assessment.assessment_date.isoformat(),
                'zone_name': assessment.analysis_zone.zone_name if assessment.analysis_zone else 'Unknown',
                'weather': assessment.weather_conditions
            }
    elif context_type == 'vegetation' and context_id:
        indices = SpectralIndexStatistics.query.filter_by(stats_id=context_id).all()
        if indices:
            context = {
                'indices': [
                    {
                        'name': idx.index_name,
                        'mean': idx.mean_value,
                        'min': idx.min_value,
                        'max': idx.max_value
                    } for idx in indices
                ]
            }
    elif context_type == 'prediction' and context_id:
        prediction = PredictionResult.query.get(context_id)
        if prediction:
            context = {
                'filename': prediction.filename,
                'upload_date': prediction.upload_date.isoformat(),
                'prediction_data': prediction.prediction_data,
                'analysis_summary': prediction.analysis_summary
            }
    
    # Handle special commands for summarization
    if query.lower().startswith('summarize'):
        if 'risk' in query.lower() or 'alerts' in query.lower():
            # Summarize risk assessments
            zone_id = context_id if context_type == 'zone' else None
            
            if zone_id:
                assessments = RiskAssessment.query.filter_by(zone_id=zone_id).all()
            else:
                assessments = RiskAssessment.query.order_by(RiskAssessment.assessment_date.desc()).limit(10).all()
            
            response = summarize_risk_data(assessments)
        
        elif 'vegetation' in query.lower() or 'indices' in query.lower() or 'ndvi' in query.lower():
            # Summarize vegetation indices
            stats_id = context_id if context_type == 'stats' else None
            
            if stats_id:
                indices = SpectralIndexStatistics.query.filter_by(stats_id=stats_id).all()
            else:
                # Get the most recent satellite image stats
                recent_stats = SatelliteImageStats.query.order_by(SatelliteImageStats.acquisition_date.desc()).first()
                indices = SpectralIndexStatistics.query.filter_by(stats_id=recent_stats.stats_id).all() if recent_stats else []
            
            response = summarize_vegetation_indices(indices)
        
        elif 'prediction' in query.lower() or 'predictions' in query.lower():
            # Summarize prediction results
            prediction_id = context_id if context_type == 'prediction' else None
            
            if prediction_id:
                prediction = PredictionResult.query.get(prediction_id)
                if prediction:
                    response = f"Prediction Summary for {prediction.filename}:\n"
                    response += f"- Upload Date: {prediction.upload_date.strftime('%Y-%m-%d %H:%M')}\n"
                    response += f"- Locations Analyzed: {prediction.prediction_data.get('num_locations')}\n"
                    response += f"- Average Wildfire Probability: {prediction.prediction_data.get('avg_probability', 0):.2f}\n"
                    response += f"- Maximum Wildfire Probability: {prediction.prediction_data.get('max_probability', 0):.2f}\n"
                    response += f"- High Risk Locations: {prediction.prediction_data.get('high_risk_locations', 0)}\n\n"
                    response += f"Analysis Summary:\n{prediction.analysis_summary}"
                else:
                    response = "Prediction not found."
            else:
                recent_predictions = PredictionResult.query.order_by(PredictionResult.upload_date.desc()).limit(5).all()
                if recent_predictions:
                    response = "Recent Prediction Summaries:\n\n"
                    for p in recent_predictions:
                        response += f"Prediction ID {p.prediction_id} - {p.filename}:\n"
                        response += f"- Upload Date: {p.upload_date.strftime('%Y-%m-%d %H:%M')}\n"
                        response += f"- Average Probability: {p.prediction_data.get('avg_probability', 0):.2f}\n"
                        response += f"- High Risk Locations: {p.prediction_data.get('high_risk_locations', 0)}\n\n"
                else:
                    response = "No prediction results available."
        
        else:
            # General summary - combine multiple summaries
            recent_predictions = PredictionResult.query.order_by(PredictionResult.upload_date.desc()).limit(3).all()
            recent_assessments = RiskAssessment.query.order_by(RiskAssessment.assessment_date.desc()).limit(5).all()
            
            prediction_summary = "Recent Predictions:\n"
            if recent_predictions:
                for p in recent_predictions:
                    prediction_summary += f"- {p.filename}: Avg Prob {p.prediction_data.get('avg_probability', 0):.2f}, High Risk: {p.prediction_data.get('high_risk_locations', 0)}\n"
            else:
                prediction_summary += "No recent predictions available.\n"
            
            risk_summary = summarize_risk_data(recent_assessments)
            
            response = f"FireSight Dashboard Summary\n\n{prediction_summary}\n\n{risk_summary}"
    
    else:
        # Regular chat response
        response = generate_chat_response(query, context)
    
    return jsonify({"answer": response})

@app.route('/api/summary', methods=["GET"])
def get_summary():
    summary_type = request.args.get('type', 'general')
    entity_id = request.args.get('id')
    
    if summary_type == 'risk':
        if entity_id:
            assessments = [RiskAssessment.query.get_or_404(entity_id)]
        else:
            assessments = RiskAssessment.query.order_by(RiskAssessment.assessment_date.desc()).limit(5).all()
        
        summary = summarize_risk_data(assessments)
    
    elif summary_type == 'vegetation':
        if entity_id:
            indices = SpectralIndexStatistics.query.filter_by(stats_id=entity_id).all()
        else:
            recent_stats = SatelliteImageStats.query.order_by(SatelliteImageStats.acquisition_date.desc()).first()
            indices = SpectralIndexStatistics.query.filter_by(stats_id=recent_stats.stats_id).all() if recent_stats else []
        
        summary = summarize_vegetation_indices(indices)
    
    elif summary_type == 'prediction':
        if entity_id:
            prediction = PredictionResult.query.get_or_404(entity_id)
            summary = f"Prediction Summary for {prediction.filename}:\n"
            summary += f"- Upload Date: {prediction.upload_date.strftime('%Y-%m-%d %H:%M')}\n"
            summary += f"- Locations Analyzed: {prediction.prediction_data.get('num_locations')}\n"
            summary += f"- Average Wildfire Probability: {prediction.prediction_data.get('avg_probability', 0):.2f}\n"
            summary += f"- Maximum Wildfire Probability: {prediction.prediction_data.get('max_probability', 0):.2f}\n"
            summary += f"- High Risk Locations: {prediction.prediction_data.get('high_risk_locations', 0)}\n\n"
            summary += f"Analysis Summary:\n{prediction.analysis_summary}"
        else:
            recent_predictions = PredictionResult.query.order_by(PredictionResult.upload_date.desc()).limit(5).all()
            if recent_predictions:
                summary = "Recent Prediction Summaries:\n\n"
                for p in recent_predictions:
                    summary += f"Prediction ID {p.prediction_id} - {p.filename}:\n"
                    summary += f"- Upload Date: {p.upload_date.strftime('%Y-%m-%d %H:%M')}\n"
                    summary += f"- Average Probability: {p.prediction_data.get('avg_probability', 0):.2f}\n"
                    summary += f"- High Risk Locations: {p.prediction_data.get('high_risk_locations', 0)}\n\n"
            else:
                summary = "No prediction results available."
    
    else:  # general summary
        recent_predictions = PredictionResult.query.order_by(PredictionResult.upload_date.desc()).limit(3).all()
        recent_assessments = RiskAssessment.query.order_by(RiskAssessment.assessment_date.desc()).limit(5).all()
        
        prediction_summary = "Recent Predictions:\n"
        if recent_predictions:
            for p in recent_predictions:
                prediction_summary += f"- {p.filename}: Avg Prob {p.prediction_data.get('avg_probability', 0):.2f}, High Risk: {p.prediction_data.get('high_risk_locations', 0)}\n"
        else:
            prediction_summary += "No recent predictions available.\n"
        
        risk_summary = summarize_risk_data(recent_assessments)
        
        summary = f"FireSight Dashboard Summary\n\n{prediction_summary}\n\n{risk_summary}"
    
    return jsonify({"summary": summary})

# initialize database
def init_db():
    # enable postGIS
    with db.engine.connect() as conn:
        conn.execute(db.text('CREATE EXTENSION IF NOT EXISTS postgis'))
        conn.commit()
    # create tables
    db.create_all()

if __name__ == "__main__":
    with app.app_context():
        init_db()
    app.run(debug=True)