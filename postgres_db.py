"""
PostgreSQL Database Adapter for Vehicle Detection
Using psycopg2 for direct PostgreSQL connections
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import os
from datetime import datetime
from contextlib import contextmanager

# Get connection string from environment
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/vehicle_detection')

class PostgresDatabase:
    def __init__(self, database_url=DATABASE_URL):
        self.database_url = database_url
        self.init_db()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = None
        try:
            conn = psycopg2.connect(self.database_url)
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()
    
    def init_db(self):
        """Create tables if they don't exist"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Drop existing tables to ensure clean schema
                cursor.execute('DROP TABLE IF EXISTS webhook_events CASCADE')
                cursor.execute('DROP TABLE IF EXISTS vehicle_detections CASCADE')
                cursor.execute('DROP TABLE IF EXISTS system_logs CASCADE')
                
                # WebhookEvents table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS webhook_events (
                        id SERIAL PRIMARY KEY,
                        event_id VARCHAR(255) UNIQUE NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        event_type VARCHAR(100),
                        data JSONB,
                        image_filename VARCHAR(255),
                        vehicle_data JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # VehicleDetections table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS vehicle_detections (
                        id SERIAL PRIMARY KEY,
                        event_id VARCHAR(255) NOT NULL,
                        license_plate VARCHAR(50),
                        vehicle_type VARCHAR(100),
                        confidence FLOAT,
                        detection_data JSONB,
                        image_url VARCHAR(255),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # ServerLogs table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS system_logs (
                        id SERIAL PRIMARY KEY,
                        level VARCHAR(20) NOT NULL,
                        message TEXT NOT NULL,
                        endpoint VARCHAR(255),
                        status_code INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.commit()
                print("[OK] PostgreSQL database initialized successfully")
        except Exception as e:
            print(f"[ERROR] Database initialization error: {str(e)}")
    
    def add_webhook_event(self, event_id, event_type, data, vehicle_data=None, image_filename=None):
        """Add a webhook event"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO webhook_events (event_id, event_type, data, vehicle_data, image_filename)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (event_id) DO NOTHING
                ''', (event_id, event_type, json.dumps(data), 
                      json.dumps(vehicle_data) if vehicle_data else None, image_filename))
                conn.commit()
        except Exception as e:
            print(f"Error adding webhook event: {str(e)}")
    
    def add_vehicle_detection(self, event_id, license_plate, detection_data, image_url, vehicle_type=None, confidence=None):
        """Add a vehicle detection record"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO vehicle_detections (event_id, license_plate, vehicle_type, confidence, detection_data, image_url)
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', (event_id, license_plate, vehicle_type, confidence, 
                      json.dumps(detection_data) if detection_data else None, image_url))
                conn.commit()
        except Exception as e:
            print(f"Error adding vehicle detection: {str(e)}")
    
    def get_webhook_events(self, limit=20):
        """Get recent webhook events"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                cursor.execute('''
                    SELECT id, event_id, timestamp, event_type, data, image_filename, vehicle_data, created_at 
                    FROM webhook_events
                    ORDER BY created_at DESC
                    LIMIT %s
                ''', (limit,))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"Error fetching webhook events: {str(e)}")
            return []
    
    def get_vehicle_detections(self, limit=50):
        """Get recent vehicle detections"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                cursor.execute('''
                    SELECT id, event_id, license_plate, vehicle_type, confidence, detection_data, image_url, created_at 
                    FROM vehicle_detections
                    ORDER BY created_at DESC
                    LIMIT %s
                ''', (limit,))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"Error fetching vehicle detections: {str(e)}")
            return []
    
    def get_vehicle_by_plate(self, plate):
        """Get all detections for a specific plate"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                cursor.execute('''
                    SELECT id, event_id, license_plate, vehicle_type, confidence, detection_data, image_url, created_at 
                    FROM vehicle_detections
                    WHERE license_plate = %s
                    ORDER BY created_at DESC
                ''', (plate,))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"Error fetching vehicle by plate: {str(e)}")
            return []
    
    def add_server_log(self, level, message, endpoint=None, status_code=None):
        """Add a server log"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO system_logs (level, message, endpoint, status_code)
                    VALUES (%s, %s, %s, %s)
                ''', (level, message, endpoint, status_code))
                conn.commit()
        except Exception as e:
            print(f"Error adding server log: {str(e)}")

# Initialize global database instance
db = PostgresDatabase()
