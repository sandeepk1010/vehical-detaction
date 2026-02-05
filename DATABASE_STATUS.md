# Vehicle Detection Server - Database Setup Complete ✓

## Database Status: ACTIVE

Your Flask server is now running with **SQLite database** on `http://127.0.0.1:5000`

### Database Details:
- **File**: `vehicle_detection.db` (auto-created)
- **Type**: SQLite3 (no installation required)
- **Tables Created**:
  - `webhook_events` - Stores all webhook events
  - `vehicle_detections` - Stores vehicle detection records  
  - `server_logs` - Stores server logs

---

## API Endpoints

### GET Events
```bash
curl http://127.0.0.1:5000/webhook/events?limit=20
```
Returns the latest webhook events from the database

### GET Vehicle Detections
```bash
curl http://127.0.0.1:5000/vehicle-detections?limit=50
```
Returns the latest vehicle detections

### GET Detections by License Plate
```bash
curl http://127.0.0.1:5000/vehicle-detections/ABC123
```
Returns all detections for a specific plate

### POST Webhook Event
```bash
curl -X POST http://127.0.0.1:5000/webhook \
  -H "Content-Type: application/json" \
  -d '{"Image": "base64string", "Plate": "ABC123"}'
```

### POST Vehicle Detection
```bash
curl -X POST http://127.0.0.1:5000/NotificationInfo/TollgateInfo \
  -H "Content-Type: application/json" \
  -d '{
    "Picture": {
      "Plate": {"PlateNumber": "ABC123"},
      "SnapInfo": {"DeviceID": "CAMERA01"},
      "CutoutPic": {"Content": "base64string", "PicName": "cutout.jpg"},
      "NormalPic": {"Content": "base64string", "PicName": "normal.jpg"}
    }
  }'
```

---

## Switching to PostgreSQL

When ready to use PostgreSQL, see [POSTGRES_SETUP.md](POSTGRES_SETUP.md):

1. Install PostgreSQL from https://www.postgresql.org/download/windows/
2. Update `.env` with your connection string:
   ```
   DATABASE_URL=postgresql://username:password@localhost:5432/vehicle_detection
   ```
3. Install psycopg2: `pip install psycopg2-binary`
4. Restart the server - your data will persist!

---

## Database Files

- **simple_db.py** - SQLite database module (no ORM, simple SQL)
- **database.py** - SQLAlchemy models (for PostgreSQL when ready)
- **anpr_server.py** - Flask app with database integration
- **.env** - Configuration (update DATABASE_URL when switching)
- **vehicle_detection.db** - SQLite database file (auto-created)

---

## Testing

**Check database contents**:
```bash
# View all webhook events
sqlite3 vehicle_detection.db "SELECT * FROM webhook_events;"

# View all vehicle detections  
sqlite3 vehicle_detection.db "SELECT * FROM vehicle_detections;"

# Count records
sqlite3 vehicle_detection.db "SELECT COUNT(*) FROM vehicle_detections;"
```

---

**Status**: ✓ Running | ✓ Database Active | ✓ Ready for production use
