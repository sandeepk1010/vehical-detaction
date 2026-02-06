# Vehicle Detection System UI - With Database Integration

A modern web-based dashboard for monitoring vehicle detection from ANPR (Automatic Number Plate Recognition) cameras with **live image galleries** and **automatic database storage**.

## 🚀 Features

### Dashboard with Real-time Analytics
- Statistics cards showing total vehicles, database records, active cameras
- Live image galleries from both JSON data and file system
- Vehicle and plate color information
- Most detected plates overview
- **Automatic sync** of detections to SQLite database

### Live Events Tab
- Stream of detection events with full images
- Camera information and license plate numbers
- Vehicle and plate colors
- Image thumbnails from JSON and file system
- Filter by camera or plate number
- Auto-refresh every 15 seconds

### Search Tab
- Search for specific vehicle plates across detection history
- View all detections of a plate
- Display plate-specific images
- Vehicle color and plate color information

### Database Features ✨
- **Auto-save**: All detections automatically saved to SQLite database
- **Persistent storage**: Long-term analytics and reporting
- **Manual sync**: Button to force-sync JSON files to database
- **Database stats**: View total records and camera breakdown
- **Query API**: Access raw database records via API

### Camera Status
- Monitor connected cameras and their operational status
- Camera IP addresses and locations

## 📋 Requirements

- Python 3.6+
- Flask 2.3.3
- Modern web browser (Chrome, Firefox, Safari, Edge)

## ⚙️ Installation

Ensure you have Flask installed:
```bash
pip install -r requirements.txt
```

## 🎯 Running the UI

```bash
python vehicle_ui.py
```

Then open in your browser: **http://localhost:5001**

The dashboard will:
- ✅ Automatically load images from JSON base64 data
- ✅ Display saved image files from downloads folder  
- ✅ Refresh data every 10-15 seconds
- ✅ Show image galleries in event list and search results
- ✅ **Automatically save all detections to SQLite database**

## 📁 Project Structure

```
vehicle-detection/
├── vehicle_ui.py          # Flask app with image serving
├── templates/
│   └── dashboard.html     # Main dashboard (responsive)
├── static/
│   ├── styles.css         # Dashboard styling with image gallery CSS
│   └── script.js          # Dashboard interactions & image display
├── downloads/             # Vehicle detection images
│   ├── camera1_KA15K3343_20260206_134824/
│   │   ├── cutout.jpg     # Plate zoom image
│   │   └── normal.jpg     # Vehicle image
│   └── camera2_...
├── json_data/             # Detection event JSON with base64 images
│   ├── camera1_*.json
│   └── camera2_*.json
└── logs/                  # Application logs
```

## 💾 **Database Storage** (NEW!)

All vehicle detections are **automatically saved to SQLite database** for permanent storage:

### Database Features
- ✅ Automatic saving of all detections
- ✅ Persistent storage across server restarts
- ✅ Analytics and reporting capability
- ✅ Manual sync button to force-update database
- ✅ Real-time record count display
- ✅ Database file: `vehicle_detection.db`

### How It Works
1. Events loaded from JSON files → Automatically saved to database
2. Click "Sync" button in dashboard to force-sync all JSON files
3. Database stats displayed in stats card (updates every 10 seconds)
4. Query via API endpoints: `/api/db-stats`, `/api/db/records`

### What's Stored in Database
- License plate number
- Camera source (camera1, camera2)
- Detection timestamp
- Vehicle color
- Plate color
- Associated image filenames
- Event ID and confidence

### Database Endpoints
```
GET /api/db-stats              → Database statistics (total, by camera, top plates)
GET /api/db/records?limit=50   → Recent database records
POST /api/db/sync              → Force sync JSON files to database
```

### Database Location
```
c:\vehicle-detection\vehicle_detection.db    (SQLite3)
```

**For detailed database integration guide, see [DATABASE_INTEGRATION.md](DATABASE_INTEGRATION.md)**

## 🎨 Dashboard Interface

### Stats Cards
- Total Vehicles Detected (from current session)
- **DB Records** - Total records in database (NEW!)
- Active Cameras
- Detections Today
- Last Detection Time
- **Sync Button** - Force-sync JSON files to database (NEW!)

### Charts
- Bar chart: Vehicle count by camera
- Pie chart: Camera distribution

### Event Cards with Images
Each event shows:
- **Header**: Timestamp, plate number, camera name
- **Details**: Vehicle color, plate color
- **Images**: Thumbnails of available images
  - Click to expand images
  - Labeled by type (cutout, vehicle, file)

### Search Results
- Full vehicle history by plate
- All associated images
- Detection timestamps

## 🖼️ Image Display

### Image Thumbnails
- **Size**: 120×100px (events), 150×120px (search)
- **Hover**: Scale up with enhanced shadow
- **Label**: Image type badge (cutout, vehicle, file)
- **Format**: JPEG
- **Error handling**: Placeholder on load failure

### Image Types

| Type | Source | Description |
|------|--------|-------------|
| `cutout` | JSON base64 | Zoomed plate detection |
| `vehicle` | JSON base64 | Full vehicle photo |
| `file` | File system | Saved detection images |

## 📡 API Endpoints

```
GET /                    → Dashboard HTML
GET /api/stats           → Vehicle statistics
GET /api/events          → Recent detection events with image URLs
GET /api/cameras         → Camera list and status
GET /api/search?q=PLATE  → Search for plates
GET /image/*             → Serve file system images
GET /api/json-image/*    → Serve JSON base64 images
```

## 📊 JSON Data Format

Expected structure in `json_data/` files:

```json
{
  "Picture": {
    "Plate": {
      "PlateNumber": "AB12CD1234",
      "PlateColor": "White"
    },
    "Vehicle": {
      "VehicleColor": "Black"
    },
    "SnapInfo": {
      "AccurateTime": "2026-02-06T13:48:24"
    },
    "CutoutPic": {
      "Content": "base64_encoded_image_data...",
      "PicName": "cutout.jpg"
    },
    "VehiclePic": {
      "Content": "base64_encoded_image_data...",
      "PicName": "vehicle.jpg"
    }
  }
}
```

## 🚀 Features in Detail

### Auto-Image Extraction
The system automatically:
1. Reads JSON files from `json_data/`
2. Extracts plate number and colors
3. Decodes base64 images
4. Finds matching image files in `downloads/`
5. Presents everything in unified gallery

### Image Serving
- Base64 images are decoded on-demand and cached in memory
- File system images are directly served
- Error handling if images are missing
- Supports multiple images per detection

### Responsive Design
- Desktop: Full view with detailed event cards
- Tablet: 2-column grid layout
- Mobile: Single column with collapsible sections

## ⚡ Performance

- **Loads**: Last 50 events by default (configurable)
- **Refresh**: 10 seconds for statistics, 15 seconds for events
- **Images**: Lazy loaded on display
- **Database**: File-based (can be upgraded to SQL)

## 🔧 Configuration

### Change Port
Edit `vehicle_ui.py` line ~270:
```python
app.run(debug=True, port=5002, host='0.0.0.0')  # Change 5001 to 5002
```

### Change Refresh Intervals
Edit `static/script.js`:
```javascript
setInterval(loadStatistics, 10000);    // Change to 5000 for 5 seconds
setInterval(() => loadEvents(), 15000); // Change to 30000 for 30 seconds
```

### Change Dashboard Colors
Edit `static/styles.css`:
```css
:root {
    --primary-color: #2c3e50;    /* Main color */
    --secondary-color: #3498db;  /* Accent color */
    /* ... other colors ... */
}
```

## 🐛 Troubleshooting

### Images Not Showing
1. Check `downloads/` folder has images
2. Verify JSON files in `json_data/` have base64 data
3. Check browser console (F12) for JavaScript errors
4. Verify file permissions

### Base64 Images Not Decoding
- Some JSON encoders escape slashes: `\/` → Fix automatically handled
- File might be corrupted: Validate JSON with `python -m json.tool`

### Slow Performance
- Archive old JSON files: Keep < 500 files
- Increase event limit: Change `limit=50` to `limit=100` in API calls
- Clear browser cache: Ctrl+Shift+Delete

### Port Already in Use
```bash
netstat -ano | findstr :5001  # Find process using port
taskkill /PID <PID> /F        # Kill the process
```

## 📈 Database Integration (Optional)

To use a real database instead of JSON files:

1. Update `get_recent_events()` in `vehicle_ui.py`
2. Query PostgreSQL instead of reading files
3. Keep same data structure
4. No UI changes needed

## 🔐 Security

For production:
- [ ] Add authentication/login
- [ ] Use HTTPS instead of HTTP
- [ ] Set `debug=False`
- [ ] Implement rate limiting
- [ ] Add CORS headers
- [ ] Sanitize file paths

## 📱 Supported Browsers

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

## 🎯 Upcoming Features

- [ ] Real-time video stream integration
- [ ] Event recording to database
- [ ] Advanced filtering (date, color, speed)
- [ ] Export events to CSV/PDF
- [ ] Alerts on specific plates
- [ ] Admin panel for configuration
- [ ] Multi-camera live view

## 📞 Support

Check these for issues:
- `logs/webhook_events_*.log` - Detection events
- `logs/camera*.log` - Camera-specific logs
- Browser console (F12) - Frontend errors

---

**Your Vehicle Detection Dashboard is ready!** 🚗📹

### Quick Commands
```bash
# Start UI
python vehicle_ui.py

# Open in browser
http://localhost:5001

# Stop server (Ctrl+C)
```

### Access the Dashboard
- **Dashboard**: Statistics & charts
- **Cameras**: Monitor camera status
- **Events**: Live detection stream with images
- **Search**: Find vehicles by plate

