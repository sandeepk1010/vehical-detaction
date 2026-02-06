# Combined Vehicle Detection Server

## ✨ **Single Server - All Features**

You now have **one unified server** that handles everything:

### **vehicle_ui.py** - All-in-One Server

```
✅ Receives ANPR camera webhooks
✅ Saves detection images & JSON
✅ Logs all events per camera
✅ Displays web dashboard
✅ Stores data in SQLite database
✅ Auto-syncs to database
✅ API endpoints for mobile/integrations
```

## 🚀 **Quick Start**

```bash
python vehicle_ui.py
```

That's it! One command starts everything.

## 📊 **Access Points**

| Feature | URL | Purpose |
|---------|-----|---------|
| **Dashboard** | http://localhost:5001 | View detections & analytics |
| **Camera Webhook** | http://localhost:5001/NotificationInfo/TollgateInfo | Receive ANPR camera data (POST) |
| **Health Check** | http://localhost:5001/health | Server status |
| **API Endpoints** | http://localhost:5001/api/* | Data & search API |

## 🎯 **How It Works**

```
┌─────────────────┐
│  ANPR Cameras   │
│  (camera1, 2)   │
└────────┬────────┘
         │
         │ POST JSON data
         │
         ▼
┌─────────────────────────────┐
│   vehicle_ui.py Server      │
│   (Port 5001)               │
├─────────────────────────────┤
│ 1. Receive webhook          │
│ 2. Parse ANPR data          │
│ 3. Extract images           │
│ 4. Save JSON files          │
│ 5. Save images to disk      │
│ 6. Log per camera           │
│ 7. Store in database        │
└────────┬────────────────────┘
         │
         ├─────────────────────┐
         │                     │
         ▼                     ▼
    📁 JSON Files        📊 Dashboard
    📷 Images            🔍 Search
    📝 Logs              📈 Analytics
    🗄️ Database          📱 API
```

## 📝 **Configuration**

### Camera IP Mapping

Edit `vehicle_ui.py` to match your camera IPs:

```python
CAMERA_IP_MAP = {
    "192.168.1.108": "camera1",
    "192.168.1.109": "camera2",
}
```

### Change Port

Default is **5001**. To change:

```python
app.run(debug=True, port=5002, host='0.0.0.0')  # Change 5001 to 5002
```

## 📦 **What Gets Saved**

### File System
```
downloads/
├── camera1_KA15K3343_20260206_134824/    # Plate folder
│   ├── cutout.jpg                         # Plate close-up
│   ├── vehicle.jpg                        # Full vehicle
│   └── normal.jpg                         # Alternative views
└── camera2_...
```

### JSON Data
```
json_data/
├── camera1_20260206_134824_998944.json
├── camera2_20260206_135708_977529.json
└── ...
```

### Logs
```
logs/
├── camera1.log                            # Camera 1 detections
├── camera2.log                            # Camera 2 detections
└── webhook_events_20260206.log
```

### Database
```
vehicle_detection.db                      # SQLite database with all records
```

## 🔨 **Key Features**

### 1. **Automatic Image Extraction**
- Decodes base64 images from camera payload
- Saves CutoutPic (plate zoom)
- Saves VehiclePic (full vehicle)
- Saves NormalPic (alternative views)

### 2. **Per-Camera Logging**
```
logs/camera1.log:
2026-02-06 13:48:24 - INFO - TOLLGATE | CAMERA1 | VEHICLE #42 | Plate: KA15K3343 | Images: 3 | IP: 192.168.1.108
```

### 3. **Vehicle Counter**
- Tracks total detections per camera
- Shown in log messages
- Stored in database

### 4. **Dashboard Features**
- Real-time detection stream
- Image galleries (JSON + file-based)
- Search by plate
- Analytics & statistics
- Database record count

### 5. **Database Integration**
- Auto-saves all detections
- Query historic data
- Generate reports
- Analytics capability

## 🌐 **API Endpoints**

### Dashboard Routes
```
GET  /                           # Dashboard HTML
GET  /api/stats                  # Statistics
GET  /api/events                 # Detection events
GET  /api/cameras                # Camera status
GET  /api/search?q=PLATE         # Search plates
```

### Database Routes
```
GET  /api/db-stats               # Database statistics
GET  /api/db/records             # Database records
POST /api/db/sync                # Force sync JSON to DB
```

### Image Serving
```
GET  /image/<folder>/<filename>  # File images
GET  /api/json-image/<file>/<type>  # Decoded base64 images
GET  /api/images/<folder>        # List images in folder
```

### Webhook (from cameras)
```
POST /NotificationInfo/TollgateInfo  # ANPR camera webhook
GET  /health                        # Server health
```

## 🔄 **Webhook Format**

Cameras send JSON like this:

```json
{
  "Picture": {
    "Plate": {
      "PlateNumber": "KA15K3343",
      "PlateColor": "White"
    },
    "Vehicle": {
      "VehicleColor": "Black"
    },
    "SnapInfo": {
      "AccurateTime": "2026-02-06 13:48:24"
    },
    "CutoutPic": {
      "Content": "base64_image_data...",
      "PicName": "cutout.jpg"
    },
    "VehiclePic": {
      "Content": "base64_image_data...",
      "PicName": "vehicle.jpg"
    }
  }
}
```

The server automatically:
1. Extracts plate number & colors
2. Decodes base64 images
3. Saves to disk
4. Saves JSON file
5. Logs to per-camera log
6. Saves to database

## 📊 **Dashboard Features**

### Stats Cards
- **Total Vehicles**: Detected in session
- **DB Records**: Total in database
- **Active Cameras**: Online cameras
- **Detections**: Count today
- **Last Detection**: Most recent time
- **Sync Button**: Force-sync JSON → DB

### Tabs
- **Dashboard**: Statistics & charts
- **Cameras**: Camera status
- **Live Events**: Detection stream with images
- **Search**: Find vehicles by plate

## 🔐 **Production Notes**

### Security Improvements for Production
```python
# 1. Add authentication
from flask_httpauth import HTTPBasicAuth
auth = HTTPBasicAuth()

@auth.verify_password
def verify_password(username, password):
    return username == "admin" and password == "secret"

@app.route('/api/events')
@auth.login_required
def secure_events():
    ...

# 2. Use HTTPS
app.run(ssl_context='adhoc')  # or use proper certificates

# 3. Disable debug mode
app.run(debug=False)

# 4. Add rate limiting
from flask_limiter import Limiter
limiter = Limiter(app)

@app.route('/NotificationInfo/TollgateInfo', methods=['POST'])
@limiter.limit("100/minute")
def tollgate():
    ...
```

## 🐛 **Troubleshooting**

### Server won't start
```bash
# Check if port 5001 is in use
netstat -ano | findstr :5001

# Kill the process (if needed)
taskkill /PID <PID> /F

# Try different port
# Edit: app.run(debug=True, port=5002, ...)
```

### No images being saved
- Check camera IP matches `CAMERA_IP_MAP`
- Verify camera is sending correct JSON format
- Check file permissions in `./downloads/`
- See logs for errors: `logs/camera*.log`

### Database errors
- Verify `simple_db.py` is in same directory
- Check write permissions on `vehicle_detection.db`
- Ensure SQLite3 is installed (included with Python)

### Dashboard not loading
- Verify `templates/` folder exists
- Check `logs/` for Flask errors
- Browser console (F12) for JavaScript errors

## 📱 **Mobile/Desktop Integration**

### Use the API from any application

**Get all detections:**
```bash
curl http://localhost:5001/api/events
```

**Search for a plate:**
```bash
curl http://localhost:5001/api/search?q=KA15K3343
```

**Send detection from camera:**
```bash
curl -X POST http://localhost:5001/NotificationInfo/TollgateInfo \
  -H "Content-Type: application/json" \
  -d @detection.json
```

## 📖 **Documentation Files**

- `UI_README.md` - Dashboard & image features
- `DATABASE_INTEGRATION.md` - Database operations
- `COMBINED_SERVER.md` - This file

## ✅ **Summary**

| Aspect | Before | After |
|--------|--------|-------|
| Servers | 2 (anpr_server_2.py + vehicle_ui.py) | 1 (vehicle_ui.py) |
| Command | `python anpr_server_2.py` + `python vehicle_ui.py` | `python vehicle_ui.py` |
| Port | 5000 + 5001 | 5001 |
| Dashboard | Yes | Yes ✓ |
| Camera Webhooks | Yes | Yes ✓ |
| Image Saving | Yes | Yes ✓ |
| Database | Optional | Yes ✓ |
| Logging | Yes | Yes ✓ |

---

**Now run just ONE server and get everything!** 🎉

```bash
python vehicle_ui.py
```
