# Vehicle Detection UI - Database Integration Guide

## 📦 Database Features

Your vehicle detection UI now **automatically saves all detected events to a SQLite database** for persistent storage and analytics.

### What Gets Saved

Every vehicle detection is automatically saved with:
- ✅ License plate number
- ✅ Camera source
- ✅ Detection timestamp
- ✅ Vehicle color
- ✅ Plate color
- ✅ Detection confidence
- ✅ Associated images/files

## 🗄️ Database Schema

### Tables Created

```sql
-- Vehicle Detection Records
vehicle_detections (
  id INTEGER PRIMARY KEY,
  event_id TEXT UNIQUE,
  license_plate TEXT,
  vehicle_type TEXT,
  confidence REAL,
  detection_data JSON,
  image_url TEXT,
  created_at DATETIME
)

-- Webhook Events (raw JSON data)
webhook_events (
  id INTEGER PRIMARY KEY,
  event_id TEXT UNIQUE,
  timestamp DATETIME,
  event_type TEXT,
  data JSON,
  image_filename TEXT,
  vehicle_data JSON,
  created_at DATETIME
)

-- Server Logs
server_logs (
  id INTEGER PRIMARY KEY,
  level TEXT,
  message TEXT,
  endpoint TEXT,
  status_code INTEGER,
  created_at DATETIME
)
```

## 🔄 Data Flow

```
JSON Files
   ↓
Automatic Parsing
   ↓
Extract Data & Images
   ↓
Save to SQLite Database ✓
   ↓
Dashboard Display + Analytics
```

### How Data Gets Saved

1. **On Event Load**: When events are loaded from JSON files, they're automatically saved to the database
2. **On Sync**: Manual sync button saves all JSON files to DB
3. **Real-time**: New detections are saved immediately

## 💾 Database File Location

```
c:\vehicle-detection\vehicle_detection.db
```

This is a SQLite database file that persists all detection data.

## 🎯 API Endpoints for Database

### Get Database Statistics
```
GET /api/db-stats
```
Returns total vehicles, camera breakdown, and top plates from database.

**Response:**
```json
{
  "total_vehicles": 150,
  "cameras": {
    "camera1": 75,
    "camera2": 75
  },
  "top_plates": {
    "KA15K3343": 5,
    "MH170K9099": 4
  }
}
```

### Get Database Records
```
GET /api/db/records?limit=50
```
Returns raw database records with full details.

### Sync JSON to Database
```
POST /api/db/sync
```
Force-syncs all JSON files to database.

**Response:**
```json
{
  "synced": 45,
  "message": "Synced 45 events from JSON to database"
}
```

## 🎨 Dashboard Database Features

### Database Stats Card
- Shows total records in database
- Updates every 10 seconds
- Can be used to verify sync is working

### Sync Button
- Located in stats section
- Click to manually sync JSON → Database
- Shows confirmation message with count
- Loaded and auto-synced dashboard stats

## 📊 Data Analysis Capability

With database storage, you can now:

### Query Recent Detections
```python
with db.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM vehicle_detections ORDER BY created_at DESC LIMIT 50')
    rows = cursor.fetchall()
```

### Get Report by Camera
```python
cursor.execute('''
    SELECT camera, COUNT(*) as count 
    FROM vehicle_detections 
    GROUP BY camera
''')
```

### Find Specific Plates
```python
cursor.execute('''
    SELECT * FROM vehicle_detections 
    WHERE license_plate = ? 
    ORDER BY created_at DESC
''', ('KA15K3343',))
```

### Get Statistics by Time
```python
cursor.execute('''
    SELECT DATE(created_at), COUNT(*) as count 
    FROM vehicle_detections 
    GROUP BY DATE(created_at)
''')
```

## 🔧 Configuration

### Change Database Type

If you want to use **PostgreSQL** instead of SQLite:

**Option 1: Update vehicle_ui.py**
```python
# Use PostgreSQL instead of SQLite
from postgres_db import PostgresDatabase

db = PostgresDatabase("postgresql://user:password@localhost:5432/vehicle_detection")
```

**Option 2: Keep SQLite but custom location**
```python
db = Database("/path/to/custom/location/detection.db")
```

### Auto-Sync on Startup

To automatically sync all JSON files when the server starts:

**Add to vehicle_ui.py (after app creation):**
```python
@app.before_first_request
def sync_on_startup():
    with app.app_context():
        # Manually trigger sync
        pass  # Sync happens automatically on event load
```

## 📈 Advanced Usage

### Export Data to CSV
```python
import csv
with db.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM vehicle_detections')
    
    with open('export.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'Plate', 'Camera', 'Time'])
        for row in cursor.fetchall():
            writer.writerow([row['id'], row['license_plate'], ...])
```

### Create Reports
```python
def get_hourly_report(date):
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                strftime('%Y-%m-%d %H:00:00', created_at) as hour,
                COUNT(*) as detections
            FROM vehicle_detections
            WHERE DATE(created_at) = ?
            GROUP BY hour
        ''', (date,))
        return cursor.fetchall()
```

### Archive Old Data
```python
def archive_old_detections(days=30):
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM vehicle_detections 
            WHERE created_at < datetime('now', ? || ' days')
        ''', (f'-{days}',))
        conn.commit()
```

## 🔍 Database Monitoring

### Check Database Size
```bash
# PowerShell
(Get-Item "c:\vehicle-detection\vehicle_detection.db").Length / 1MB
```

### View Total Records
```bash
# Using Python
from simple_db import Database
db = Database()
with db.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) as total FROM vehicle_detections')
    print(cursor.fetchone()['total'])
```

## ⚡ Performance Tips

### Dashboard loads slowly?
- **Archive old records**: Delete records older than 90 days
- **Add indexes**: Add indexes on frequently queried columns
  ```sql
  CREATE INDEX idx_plate ON vehicle_detections(license_plate);
  CREATE INDEX idx_camera ON vehicle_detections((detection_data->>'camera'));
  CREATE INDEX idx_timestamp ON vehicle_detections(created_at);
  ```

### Database getting too large?
- Implement automated cleanup of records older than 180 days
- Archive to separate backup database
- Use PostgreSQL for better performance with large datasets

## 🔒 Database Backup

### Automatic Backup
```python
import shutil
from datetime import datetime

def backup_database():
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    shutil.copy(
        'vehicle_detection.db', 
        f'backups/vehicle_detection_backup_{timestamp}.db'
    )
```

### Restore from Backup
```python
shutil.copy('backups/vehicle_detection_backup_20260206_120000.db', 'vehicle_detection.db')
```

## 🐛 Troubleshooting

### Database Locked Error
**Issue**: "database is locked"
**Solution**: 
- Reduce concurrent connections
- Increase timeout in `simple_db.py`
- Use PostgreSQL in production

### Missing Records
**Issue**: Events not being saved to DB
**Solution**:
- Click "Sync" button to force-sync JSON files
- Check `vehicle_detection.db` file permissions
- Verify JSON files are valid

### Slow Queries
**Issue**: Dashboard loading slowly
**Solution**:
- Add database indexes
- Limit event load to fewer records: `limit=20`
- Archive old records

## 📋 Database Query Examples

```python
from simple_db import Database

db = Database()

# Get all detections for a plate
with db.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute(
        'SELECT * FROM vehicle_detections WHERE license_plate = ?',
        ('KA15K3343',)
    )
    print(cursor.fetchall())

# Get detections by camera today
with db.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute('''
        SELECT detection_data->>'camera' as camera, COUNT(*) as count
        FROM vehicle_detections
        WHERE DATE(created_at) = DATE('now')
        GROUP BY camera
    ''')
    print(cursor.fetchall())

# Get peak detection hours
with db.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 
            strftime('%H', created_at) as hour,
            COUNT(*) as count
        FROM vehicle_detections
        GROUP BY hour
        ORDER BY count DESC
    ''')
    print(cursor.fetchall())
```

## 🎯 Integration with ANPR Server

To save detections from your ANPR server to the database:

```python
from simple_db import Database
import uuid

db = Database()

# In your webhook handler
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    
    # Extract detection info
    plate = data.get('Plate', {}).get('PlateNumber', 'UNKNOWN')
    
    event_id = str(uuid.uuid4())
    
    # Save to database
    db.add_vehicle_detection(
        event_id=event_id,
        license_plate=plate,
        detection_data={...},
        image_url='...',
        confidence=data.get('Confidence')
    )
    
    return jsonify({'status': 'saved'})
```

## 📞 Support

For database-related questions:
- Check `logs/` folder for detailed logs
- Verify `vehicle_detection.db` exists and is readable
- Review `/api/db-stats` endpoint response
- Use the Sync button to validate data flow

---

Your vehicle detection events are now **permanently stored in the database**! All detections from JSON files are automatically saved for long-term analytics and reporting. 🎉
