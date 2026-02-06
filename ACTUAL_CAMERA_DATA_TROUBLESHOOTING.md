# Actual Camera Data Not Saving - Troubleshooting Guide

## Problem
- Test data saves successfully ✓
- Actual vehicle data from camera doesn't save ✗

## Root Causes

### 1. Camera Not Sending Images
**Symptom:** Plate is saved, but no images in `/downloads/`

**Check:**
```powershell
# Look at logs for "No images saved" message
Get-Content "c:\vehicle-detection\logs\camera1.log" | Select-String "No images"

# Check payload debug files
dir "c:\vehicle-detection\logs\payload_debug_*" | Sort LastWriteTime -Desc | Select -First 5
```

**Solution:**
1. Access camera admin panel (usually http://camera-ip:8000)
2. Find webhook/event settings
3. Enable these options:
   - ✓ "Include Image In Payload" 
   - ✓ "Send NormalPic" 
   - ✓ "Send CutoutPic"
   - ✓ "Base64 Encoding"
4. Test: Send a test event from camera, check `/downloads/`

---

### 2. Wrong Payload Format
**Symptom:** Server receives JSON but images aren't in expected structure

**Check:**
Run the analyzer:
```powershell
cd c:\vehicle-detection
python analyze_payloads.py
```

**Common Issues:**

| Camera Brand | Format | Fix |
|---|---|---|
| Generic ANPR | `Picture.NormalPic.Content` | Enable base64 encoding |
| HikVision | `Picture.NormalPic.Data` | Use "Data" instead of "Content" |
| Dahua | `Picture.NormalPic.PicData` | Check alternate key names |
| Custom API | Different structure | Modify image extraction code |

---

### 3. Image Data Not Decoding
**Symptom:** Images exist in payload but not saved

**Check:**
```powershell
# Look at decode errors in server console
# Look for: "base64.b64decode failed" or "decode error"
```

**Solution:**
Run this to test base64 decoding:
```python
import json
import base64

# Load latest debug payload
with open("logs/payload_debug_XXXX.json") as f:
    data = json.load(f)

picture = data["Picture"]
if "NormalPic" in picture:
    normal = picture["NormalPic"]
    if "Content" in normal:
        try:
            img = base64.b64decode(normal["Content"])
            print(f"[OK] Decoded: {len(img)} bytes")
        except Exception as e:
            print(f"[ERROR] Decode failed: {e}")
```

---

## Step-by-Step Diagnosis

### Step 1: Verify Server is Running
```powershell
$response = Invoke-WebRequest -Uri "http://localhost:5001/health" -UseBasicParsing
Write-Host "Server status: $($response.StatusCode)"
```

### Step 2: Send Test Data
```powershell
$payload = @{
    Picture = @{
        Plate = @{
            PlateNumber = "TEST00001"
            PlateColor = "Yellow"
        }
        SnapInfo = @{
            DeviceID = "TEST_CAMERA"
        }
        NormalPic = @{
            PicName = "normal.jpg"
            # Use base64-encoded JPEG (minimal 1x1 pixel)
            Content = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        }
    }
} | ConvertTo-Json

$response = Invoke-WebRequest -Uri "http://localhost:5001/NotificationInfo/TollgateInfo" `
    -Method POST -Body $payload -ContentType "application/json" -UseBasicParsing

Write-Host "Response:"
$response.Content | ConvertFrom-Json | ConvertTo-Json
```

### Step 3: Check Saved Files
```powershell
# Check if images were saved
Get-ChildItem "c:\vehicle-detection\downloads\*TEST00001*" -Recurse

# Check JSON data was saved
Get-ChildItem "c:\vehicle-detection\json_data\*.json" -File | Sort CreationTime -Desc | Select -First 3

# Check logs
Get-Content "c:\vehicle-detection\logs\camera1.log" | Select -Last 5
```

### Step 4: Analyze Payloads
```powershell
cd c:\vehicle-detection
python analyze_payloads.py
```

---

## What Should Happen

When real camera sends data:

```
=================================================================
[OK] TOLLGATE ENDPOINT CALLED at 2026-02-06 18:30:45.123456
=================================================================
Camera: camera1 (Remote IP: 192.168.1.108)

[DEBUG] Picture keys: ['Plate', 'SnapInfo', 'NormalPic', 'CutoutPic', ...]

[DEBUG] Processing NormalPic: ['Content', 'PicName']
[DEBUG] Found NormalPic.Content, attempting decode...
[DEBUG] Successfully decoded NormalPic.Content: 85432 bytes

[OK] Image saved: C:\vehicle-detection\downloads\camera1_ABC1234_20260206_183045\normal.jpg (85432 bytes)
[OK] Image saved: C:\vehicle-detection\downloads\camera1_ABC1234_20260206_183045\cutout.jpg (12345 bytes)
[OK] Images folder: camera1_ABC1234_20260206_183045 (2 images)
[OK] JSON saved: camera1_20260206_183045_654321.json
[OK] Saved to database
=================================================================
```

If you see **"No images saved"** instead, the camera payload doesn't have the image data.

---

## Configuration Example for HikVision Cameras

1. Go to: **Event Settings → Notification**
2. Enable: **Upload to HTTP Server**
3. URL: `http://192.168.1.120:5001/NotificationInfo/TollgateInfo`
4. In the payload editor, ensure:
   - Picture data is included
   - Base64 encoding is enabled
   - Both NormalPic and CutoutPic are enabled
5. Save and test

---

## Getting Help

When asking for help, include:
1. Output from `analyze_payloads.py`
2. Last 10 lines from server console
3. Camera model and firmware version
4. Whether test data saves correctly (it should)
