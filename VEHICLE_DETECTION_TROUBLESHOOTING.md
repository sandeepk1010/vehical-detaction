# Vehicle Detection Troubleshooting Guide

## Current Server Status

✓ **Server Running:** YES  
✓ **Server IP Address:** `192.168.1.120`  
✓ **Server Port:** `5000`  
✓ **Database:** PostgreSQL (initialized)  
✓ **Endpoints:** All operational

---

## Why Vehicles Aren't Being Detected

The most common reason is **camera not sending data to correct server IP**.

### Check 1: Verify Server IP Address

**Your server IP is:** `192.168.1.120:5000`

If your camera is configured to use `192.168.0.100:5000`, it will NOT reach this server.

**Camera MUST be configured with:**
```
IP: 192.168.1.120
Port: 5000
```

---

## Camera Configuration for Vehicle Detection

### Camera 1 Settings

**Webhook URL (for TollGate/Notification):**
```
POST http://192.168.1.120:5000/NotificationInfo/TollgateInfo
```

**Backup Webhook URL:**
```
POST http://192.168.1.120:5000/webhook
```

**Health Check URL:**
```
GET http://192.168.1.120:5000/health
```

### Camera 2 Settings (if using dual camera)

**Webhook URL:**
```
POST http://192.168.1.120:5000/NotificationInfo/TollgateInfo1
```

**Alternative:**
```
POST http://192.168.1.120:5000/webhook1
```

---

## Expected Data Format from Camera

The server expects JSON data in this format:

```json
{
  "Picture": {
    "Plate": {
      "PlateNumber": "MH15AB1234",
      "Color": "Yellow"
    },
    "SnapInfo": {
      "DeviceID": "CAMERA1",
      "Timestamp": "2026-02-04T19:00:00"
    },
    "NormalPic": {
      "Content": "base64_encoded_image_data_here...",
      "PicName": "normal.jpg"
    },
    "CutoutPic": {
      "Content": "base64_encoded_image_data_here...",
      "PicName": "cutout.jpg"
    }
  }
}
```

### Required Fields:
- `Picture.Plate.PlateNumber` - License plate number (e.g., "MH15AB1234")
- `Picture.SnapInfo.DeviceID` - Camera ID (e.g., "CAMERA1")
- `Picture.NormalPic.Content` - Base64 encoded image
- `Picture.CutoutPic.Content` - Base64 encoded plate crop image

### What Happens When Data is Received:

1. **Images are saved** to: `c:\vehicle-detection\downloads\`
2. **JSON backup** created in: `c:\vehicle-detection\json_data\`
3. **Log entry** created in: `c:\vehicle-detection\logs\webhook_events_20260204.log`
4. **Vehicle count** incremented in real-time
5. **Data persisted** to PostgreSQL database

---

## Step-by-Step: Configure Your Camera

### Step 1: Identify Camera IP Address
```powershell
# On the camera's network
ping 192.168.1.120
# Should show: Reply from 192.168.1.120
```

### Step 2: Access Camera Admin Panel
- Usually: `http://camera-ip:8000` or `http://camera-ip/admin`
- Look for: Webhook settings, Event notification, or Integration settings

### Step 3: Set Webhook URL
Find the setting for:
- "Webhook URL"
- "Callback URL"
- "Server URL"
- "Event Notification Address"

Enter:
```
http://192.168.1.120:5000/NotificationInfo/TollgateInfo
```

### Step 4: Enable Event Notifications
- Enable: "Vehicle Detection"
- Enable: "Send to Webhook"
- Enable: "Include Images in Payload"
- Enable: "Send Both Normal and Cutout Images"

### Step 5: Test the Connection
From camera settings, there's usually a "Test" or "Send Test Event" button. Click it.

---

## Verify Server is Receiving Data

### Check Logs in Real-Time

Open PowerShell and run:
```powershell
# Watch logs as they're updated
Get-Content c:\vehicle-detection\logs\webhook_events_20260204.log -Tail 20 -Wait
```

You should see entries like:
```
2026-02-04 19:05:32,123 - INFO - POST /NotificationInfo/TollgateInfo (Camera 1) - VEHICLE #1 - Plate: MH15AB1234
2026-02-04 19:05:32,234 - INFO - JSON saved: vehicle_cam1_1_20260204_190532.json
```

### Check Saved Images

```powershell
# View saved vehicle images
Get-ChildItem c:\vehicle-detection\downloads\ | Select-Object -Last 5
```

Should show files like:
```
MH15AB1234_CAMERA1_abcd1234/
  ├── normal.jpg
  └── cutout.jpg
```

### Check JSON Backups

```powershell
# View saved event data
Get-ChildItem c:\vehicle-detection\json_data\ | Select-Object -Last 5
```

---

## Common Issues & Solutions

### Issue 1: "Connection Refused" on Camera
**Cause:** Wrong IP address or port  
**Solution:** 
- Verify server IP: `192.168.1.120`
- Verify server port: `5000`
- Verify server is running: `tasklist | findstr python`

### Issue 2: "Request Timeout" on Camera
**Cause:** Camera cannot reach server network  
**Solution:**
- Ensure camera is on same network (192.168.1.x)
- Check router/firewall isn't blocking
- Ping server from camera network: `ping 192.168.1.120`

### Issue 3: Server Receives Data But No Vehicles Detected
**Cause:** Incorrect JSON format from camera  
**Solution:**
- Check camera's webhook payload format
- Verify it includes `Picture.Plate.PlateNumber`
- Enable detailed logging on camera
- Review server logs for error messages

### Issue 4: Vehicles Detected But Images Not Saved
**Cause:** Base64 encoding issue  
**Solution:**
- Verify image data is valid base64
- Check image format (JPEG/PNG)
- Review error logs: `Get-Content c:\vehicle-detection\logs\webhook_events_20260204.log -Tail 50 | Select-String ERROR`

---

## Test Camera Connection (Without Real Camera)

Run the test script to verify server is accepting vehicle data:

```powershell
cd c:\vehicle-detection
python test_camera_data.py
```

Should output:
```
[TEST] Testing /NotificationInfo/TollgateInfo endpoint...
[OK] Status: 200
[OK] Response: {'status': 'success', 'plate': 'MH15AB1234', ...}
```

---

## Real-Time Monitoring Dashboard

**Dashboard URL:** `http://192.168.1.120:5000/`

This shows:
- Camera 1 vehicle count (real-time)
- Camera 2 vehicle count (real-time)
- Total vehicles detected
- Last detection timestamp
- Auto-refreshes every 5 seconds

---

## Network Topology Verification

```
Camera (192.168.1.x)
    ↓
    └─→ Network → Router (192.168.1.1)
                      ↓
                      └─→ Server (192.168.1.120:5000)
                              ↓
                         PostgreSQL DB
                              ↓
                    Image Files + JSON Logs
```

Make sure:
- ✓ Camera and server are on same network (192.168.1.x)
- ✓ Server port 5000 is not blocked by firewall
- ✓ Camera has correct server IP (192.168.1.120)
- ✓ Server Flask app is running

---

## Server Log Locations

| Type | Location |
|------|----------|
| Webhook Events | `c:\vehicle-detection\logs\webhook_events_20260204.log` |
| Saved Images | `c:\vehicle-detection\downloads\` |
| JSON Backups | `c:\vehicle-detection\json_data\` |
| Database | PostgreSQL `vehicle_detection` |

---

## Quick Diagnostic Checklist

- [ ] Server is running: `tasklist | findstr python` shows python.exe
- [ ] Server is listening: Port 5000 is open and listening
- [ ] Camera IP configured: Using `192.168.1.120:5000`
- [ ] Network connectivity: Camera can ping server
- [ ] Webhook URL correct: `/NotificationInfo/TollgateInfo`
- [ ] JSON format matches: Includes all required fields
- [ ] Images are base64: Properly encoded images in payload
- [ ] Database connected: PostgreSQL initialized successfully

---

## Need Help?

1. Check logs: `Get-Content c:\vehicle-detection\logs\webhook_events_20260204.log -Tail 50`
2. Test server: Run `python test_camera_data.py`
3. Monitor real-time: `Get-Content c:\vehicle-detection\logs\webhook_events_20260204.log -Tail 20 -Wait`
4. Check IP: `ipconfig` - ensure camera uses same network
5. Restart server: Kill python and restart `python anpr_server_combined.py`
