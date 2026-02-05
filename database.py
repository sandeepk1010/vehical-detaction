"""
PostgreSQL Database Configuration and Models
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import JSON
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize SQLAlchemy
db = SQLAlchemy()

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://username:password@localhost:5432/vehicle_detection')

class WebhookEvent(db.Model):
    """Model for storing webhook events"""
    __tablename__ = 'webhook_events'
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.String(255), unique=True, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    event_type = db.Column(db.String(100), nullable=True)
    data = db.Column(JSON, nullable=True)
    image_filename = db.Column(db.String(255), nullable=True)
    vehicle_data = db.Column(JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<WebhookEvent {self.event_id}>'

class VehicleDetection(db.Model):
    """Model for storing vehicle detection results"""
    __tablename__ = 'vehicle_detections'
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.String(255), nullable=False)
    license_plate = db.Column(db.String(50), nullable=True)
    vehicle_type = db.Column(db.String(100), nullable=True)
    confidence = db.Column(db.Float, nullable=True)
    detection_data = db.Column(JSON, nullable=True)
    image_url = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<VehicleDetection {self.license_plate}>'

class ServerLog(db.Model):
    """Model for storing server logs"""
    __tablename__ = 'server_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    level = db.Column(db.String(20), nullable=False)  # INFO, WARNING, ERROR, etc.
    message = db.Column(db.Text, nullable=False)
    endpoint = db.Column(db.String(255), nullable=True)
    status_code = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<ServerLog {self.level}>'

def init_db(app):
    """Initialize database with Flask app"""
    db.init_app(app)
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")
