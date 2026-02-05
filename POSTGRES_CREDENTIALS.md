## PostgreSQL Connection Setup

Your PostgreSQL database has been created with the following tables:
- webhook_events
- vehicle_detections  
- system_logs

### Update Your PostgreSQL Credentials

The `.env` file currently has:
```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/vehicle_detection
```

**To find your actual PostgreSQL password:**

1. Open PostgreSQL command line:
   ```bash
   psql -U postgres
   ```

2. If you forgot the password, reset it:
   ```sql
   ALTER USER postgres WITH PASSWORD 'your_new_password';
   ```

3. Update `.env` with your actual credentials:
   ```
   DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/vehicle_detection
   ```

### Verify Database Connection

Test the connection:
```bash
psql -U postgres -h localhost -d vehicle_detection
```

### Start the Server

Once credentials are configured:
```bash
python anpr_server_combined.py
```

The server will:
✓ Connect to PostgreSQL automatically
✓ Create tables if they don't exist
✓ Start listening on http://0.0.0.0:5000/
✓ Accept webhooks from both cameras
✓ Store all events in PostgreSQL

### API Endpoints

**Camera 1:**
- POST /webhook - Generic webhook
- POST /NotificationInfo/TollgateInfo - Tollgate data
- GET /webhook/events - View events
- GET /health - Health check

**Camera 2:**
- POST /webhook1 - Generic webhook
- POST /NotificationInfo/TollgateInfo1 - Tollgate data
- GET /webhook/events1 - View events
- GET /health1 - Health check

**Combined:**
- GET /vehicle-detections - All detections
- GET /vehicle-detections/<plate> - By plate
- GET /vehicle/count - Statistics
- GET / - Dashboard

