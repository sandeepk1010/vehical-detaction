"""
Simple SQLite Database for Vehicle Detection
Without ORM complexity - using direct SQL
"""
import sqlite3
import json
import os
from datetime import datetime
from contextlib import contextmanager

DB_FILE = "vehicle_detection.db"

class Database:
    def __init__(self, db_file=DB_FILE):
        self.db_file = db_file
        self.init_db()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def init_db(self):
        """Create tables if they don't exist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # WebhookEvents table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS webhook_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT UNIQUE NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    event_type TEXT,
                    data TEXT,
                    image_filename TEXT,
                    vehicle_data TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # VehicleDetections table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS vehicle_detections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL,
                    license_plate TEXT,
                    vehicle_type TEXT,
                    confidence REAL,
                    detection_data TEXT,
                    image_url TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # ServerLogs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS server_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    endpoint TEXT,
                    status_code INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            print(f"Database initialized: {self.db_file}")
    
    def add_webhook_event(self, event_id, event_type, data, vehicle_data=None, image_filename=None):
        """Add a webhook event"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO webhook_events (event_id, event_type, data, vehicle_data, image_filename)
                VALUES (?, ?, ?, ?, ?)
            ''', (event_id, event_type, json.dumps(data) if data else None, 
                  json.dumps(vehicle_data) if vehicle_data else None, image_filename))
            conn.commit()
    
    def add_vehicle_detection(self, event_id, license_plate, detection_data, image_url, vehicle_type=None, confidence=None):
        """Add a vehicle detection record"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO vehicle_detections (event_id, license_plate, vehicle_type, confidence, detection_data, image_url)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (event_id, license_plate, vehicle_type, confidence, 
                  json.dumps(detection_data) if detection_data else None, image_url))
            conn.commit()
    
    def get_webhook_events(self, limit=20):
        """Get recent webhook events"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM webhook_events
                ORDER BY created_at DESC
                LIMIT ?
            ''', (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_vehicle_detections(self, limit=50):
        """Get recent vehicle detections"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM vehicle_detections
                ORDER BY created_at DESC
                LIMIT ?
            ''', (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_vehicle_by_plate(self, plate):
        """Get all detections for a specific plate"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM vehicle_detections
                WHERE license_plate = ?
                ORDER BY created_at DESC
            ''', (plate,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def add_server_log(self, level, message, endpoint=None, status_code=None):
        """Add a server log"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO server_logs (level, message, endpoint, status_code)
                VALUES (?, ?, ?, ?)
            ''', (level, message, endpoint, status_code))
            conn.commit()

# Initialize global database instance
db = Database()
