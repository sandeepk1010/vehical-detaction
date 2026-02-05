"""
Combined ANPR Server - Multi-Camera Support with PostgreSQL Database
Camera 1: /webhook, /health, /NotificationInfo/TollgateInfo
Camera 2: /webhooks, /healths, /NotificationInfo/TollgateInfo1
Database: PostgreSQL ONLY with vehicle_detection
"""
from flask import Flask, request, jsonify, render_template_string
import base64, os, json, uuid
from datetime import datetime
import logging
from dotenv import load_dotenv

load_dotenv()

# Try PostgreSQL first, fallback to SQLite
db = None
db_type = "UNKNOWN"
try:
    from postgres_db import db as pg_db
    db = pg_db
    db_type = "PostgreSQL"
except Exception as e:
    print(f"PostgreSQL connection failed: {e}")
    print("Falling back to SQLite...")
    from simple_db import db as sqlite_db
    db = sqlite_db
    db_type = "SQLite"

app = Flask(__name__)
recent_events = []
recent_events1 = []
vehicle_count = 0
vehicle_count1 = 0

# Directories
SAVE_DIR = "./downloads"
LOG_DIR = "./logs"
JSON_DIR = "./json_data"
os.makedirs(SAVE_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(JSON_DIR, exist_ok=True)

# =========================
# Webhook Logger (Separate File)
# =========================
webhook_log_file = os.path.join(LOG_DIR, f"webhook_events_{datetime.now().strftime('%Y%m%d')}.log")
webhook_logger = logging.getLogger("webhook_logger")
webhook_logger.setLevel(logging.INFO)

file_handler = logging.FileHandler(webhook_log_file)
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

if not webhook_logger.hasHandlers():
    webhook_logger.addHandler(file_handler)

# Print startup info
print(f"\n{'=' * 60}")
print(f"Multi-Camera ANPR Server - {db_type} Database")
print(f"{'=' * 60}")
print("✓ Camera 1 endpoints: /webhook, /health, /NotificationInfo/TollgateInfo")
print("✓ Camera 2 endpoints: /webhooks, /healths, /NotificationInfo/TollgateInfo1")
print("✓ Dashboard: http://0.0.0.0:5000/")
print(f"✓ Database: {db_type}")
print(f"{'=' * 60}\n")

# =========================
# Utility: detect image type
# =========================
def get_image_format(b64_data):
    try:
        img_bytes = base64.b64decode(b64_data)
        if img_bytes.startswith(b'\xff\xd8\xff'):
            return ".jpg"
        elif img_bytes.startswith(b'\x89PNG'):
            return ".png"
        elif img_bytes.startswith(b'GIF87a') or img_bytes.startswith(b'GIF89a'):
            return ".gif"
        elif img_bytes.startswith(b'RIFF') and b'WEBP' in img_bytes[:12]:
            return ".webp"
        else:
            return ".jpg"
    except:
        return ".jpg"

# =========================
# Function to save JSON data
# =========================
def save_json_data(data, prefix="vehicle"):
    try:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{ts}.json"
        filepath = os.path.join(JSON_DIR, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
            f.flush()
            os.fsync(f.fileno())
        webhook_logger.info(f"JSON saved: {filename}")
        return filename
    except Exception as e:
        webhook_logger.error(f"JSON save error: {e}")
        return None

# =======================================
# CAMERA 1 ENDPOINTS
# =======================================

@app.route("/webhook", methods=["POST"])
def webhook():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    event = {"ReceivedAt": datetime.now().isoformat(), "camera": "camera1"}
    data = None

    if request.is_json:
        data = request.get_json(force=True)
        event["Payload"] = data
        if isinstance(data, dict) and "Image" in data:
            img_b64 = data["Image"]
            img_ext = get_image_format(img_b64)
            img_file = f"{data.get('Plate','UNKNOWN')}_{ts}{img_ext}"
            with open(os.path.join(SAVE_DIR, img_file), "wb") as f:
                f.write(base64.b64decode(img_b64))
            event["ImageSavedAs"] = img_file
    else:
        event["RawData"] = request.data.decode(errors="ignore")

    if request.files:
        event["Files"] = []
        for name, file in request.files.items():
            img_file = f"{name}_{ts}.jpg"
            file.save(os.path.join(SAVE_DIR, img_file))
            event["Files"].append({"field": name, "filename": file.filename, "saved_as": img_file})

    recent_events.insert(0, event)
    recent_events[:] = recent_events[:20]

    global vehicle_count
    vehicle_count += 1
    webhook_logger.info(f"POST /webhook (Camera 1) - VEHICLE #{vehicle_count}")
    
    try:
        event_id = str(uuid.uuid4())
        db.add_webhook_event(event_id=event_id, event_type='webhook_camera1', data=event, vehicle_data=data if request.is_json else None)
        save_json_data({"vehicle_number": vehicle_count, "camera": "camera1", "timestamp": datetime.now().isoformat(), "event_id": event_id, "data": event}, f"webhook_cam1_{vehicle_count}")
    except Exception as e:
        webhook_logger.error(f"Database error (Camera 1): {str(e)}")

    return jsonify({"status": "ok", "total_count": vehicle_count, "camera": "camera1"})

@app.route("/NotificationInfo/TollgateInfo", methods=["POST"])
def crossing():
    request_id = str(uuid.uuid4())
    try:
        data = request.get_json(force=True)
        picture_data = data.get("Picture", {})
        plate_info = picture_data.get("Plate", {})
        snap_info = picture_data.get("SnapInfo", {})
        
        plate_number = plate_info.get("PlateNumber", "UNKNOWN")
        device_id = snap_info.get("DeviceID", "CAMERA1")
        
        folder_name = f"{plate_number}_{device_id}_{request_id[:8]}"
        request_dir = os.path.join(SAVE_DIR, folder_name)
        os.makedirs(request_dir, exist_ok=True)

        saved_files = []

        def save_nested_image(pic_obj, prefix):
            if pic_obj and "Content" in pic_obj:
                content = pic_obj["Content"].replace('\\/', '/')
                filename = pic_obj.get("PicName") or f"{prefix}_{request_id[:8]}.jpg"
                full_path = os.path.join(request_dir, filename)
                with open(full_path, "wb") as f:
                    f.write(base64.b64decode(content))
                return filename
            return None

        cutout = save_nested_image(picture_data.get("CutoutPic"), "cutout")
        normal = save_nested_image(picture_data.get("NormalPic"), "normal")

        if cutout: saved_files.append(cutout)
        if normal: saved_files.append(normal)

        global vehicle_count
        vehicle_count += 1
        webhook_logger.info(f"POST /NotificationInfo/TollgateInfo (Camera 1) - VEHICLE #{vehicle_count} - Plate: {plate_number}")

        try:
            db.add_vehicle_detection(event_id=request_id, license_plate=plate_number, detection_data=data, image_url=folder_name)
            db.add_webhook_event(event_id=request_id, event_type='tollgate_camera1', data=data, image_filename=folder_name)
        except Exception as e:
            webhook_logger.error(f"Database error (Camera 1 Tollgate): {str(e)}")
        
        save_json_data({"vehicle_number": vehicle_count, "camera": "camera1", "plate": plate_number, "device_id": device_id, "timestamp": datetime.now().isoformat(), "saved_images": saved_files, "request_id": request_id}, f"vehicle_cam1_{vehicle_count}")
        
        return jsonify({"status": "success", "request_id": request_id, "folder": folder_name, "saved_images": saved_files, "plate": plate_number, "camera": "camera1", "total_count": vehicle_count}), 200
    except Exception as e:
        webhook_logger.error(f"Error processing Camera 1 tollgate: {str(e)}")
        return jsonify({"status": "error", "message": str(e), "camera": "camera1"}), 400

@app.route("/webhook/events", methods=["GET"])
def get_events():
    limit = request.args.get('limit', default=20, type=int)
    try:
        events = db.get_webhook_events(limit=limit)
        camera1_events = [e for e in events if 'camera1' in str(e.get('event_type', ''))]
        return jsonify(camera1_events if camera1_events else events)
    except Exception as e:
        webhook_logger.error(f"Database error: {str(e)}")
        return jsonify(recent_events)

@app.route("/health", methods=["GET", "POST"])
def health_check():
    webhook_logger.info(f"Health check from {request.remote_addr} - Camera 1")
    return jsonify({"status": "healthy", "camera": "camera1", "vehicle_count": vehicle_count, "database": db_type})

# =======================================
# CAMERA 2 ENDPOINTS
# =======================================

@app.route("/webhooks", methods=["POST"])
def webhooks():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    event = {"ReceivedAt": datetime.now().isoformat(), "camera": "camera2"}
    data = None

    if request.is_json:
        data = request.get_json(force=True)
        event["Payload"] = data
        if isinstance(data, dict) and "Image" in data:
            img_b64 = data["Image"]
            img_ext = get_image_format(img_b64)
            img_file = f"CAM2_{data.get('Plate','UNKNOWN')}_{ts}{img_ext}"
            with open(os.path.join(SAVE_DIR, img_file), "wb") as f:
                f.write(base64.b64decode(img_b64))
            event["ImageSavedAs"] = img_file
    else:
        event["RawData"] = request.data.decode(errors="ignore")

    if request.files:
        event["Files"] = []
        for name, file in request.files.items():
            img_file = f"CAM2_{name}_{ts}.jpg"
            file.save(os.path.join(SAVE_DIR, img_file))
            event["Files"].append({"field": name, "filename": file.filename, "saved_as": img_file})

    recent_events1.insert(0, event)
    recent_events1[:] = recent_events1[:20]

    global vehicle_count1
    vehicle_count1 += 1
    webhook_logger.info(f"POST /webhooks (Camera 2) - VEHICLE #{vehicle_count1}")
    
    try:
        event_id = str(uuid.uuid4())
        db.add_webhook_event(event_id=event_id, event_type='webhook_camera2', data=event, vehicle_data=data if request.is_json else None)
        save_json_data({"vehicle_number": vehicle_count1, "camera": "camera2", "timestamp": datetime.now().isoformat(), "event_id": event_id, "data": event}, f"webhook_cam2_{vehicle_count1}")
    except Exception as e:
        webhook_logger.error(f"Database error (Camera 2): {str(e)}")

    return jsonify({"status": "ok", "total_count": vehicle_count1, "camera": "camera2"})

@app.route("/NotificationInfo/TollgateInfo1", methods=["POST"])
def crossing1():
    request_id = str(uuid.uuid4())
    try:
        data = request.get_json(force=True)
        picture_data = data.get("Picture", {})
        plate_info = picture_data.get("Plate", {})
        snap_info = picture_data.get("SnapInfo", {})
        
        plate_number = plate_info.get("PlateNumber", "UNKNOWN")
        device_id = snap_info.get("DeviceID", "CAMERA2")
        
        folder_name = f"CAM2_{plate_number}_{device_id}_{request_id[:8]}"
        request_dir = os.path.join(SAVE_DIR, folder_name)
        os.makedirs(request_dir, exist_ok=True)

        saved_files = []

        def save_nested_image(pic_obj, prefix):
            if pic_obj and "Content" in pic_obj:
                content = pic_obj["Content"].replace('\\/', '/')
                filename = pic_obj.get("PicName") or f"{prefix}_{request_id[:8]}.jpg"
                full_path = os.path.join(request_dir, filename)
                with open(full_path, "wb") as f:
                    f.write(base64.b64decode(content))
                return filename
            return None

        cutout = save_nested_image(picture_data.get("CutoutPic"), "cutout")
        normal = save_nested_image(picture_data.get("NormalPic"), "normal")

        if cutout: saved_files.append(cutout)
        if normal: saved_files.append(normal)

        global vehicle_count1
        vehicle_count1 += 1
        webhook_logger.info(f"POST /NotificationInfo/TollgateInfo1 (Camera 2) - VEHICLE #{vehicle_count1} - Plate: {plate_number}")

        try:
            db.add_vehicle_detection(event_id=request_id, license_plate=plate_number, detection_data=data, image_url=folder_name)
            db.add_webhook_event(event_id=request_id, event_type='tollgate_camera2', data=data, image_filename=folder_name)
        except Exception as e:
            webhook_logger.error(f"Database error (Camera 2 Tollgate): {str(e)}")
        
        save_json_data({"vehicle_number": vehicle_count1, "camera": "camera2", "plate": plate_number, "device_id": device_id, "timestamp": datetime.now().isoformat(), "saved_images": saved_files, "request_id": request_id}, f"vehicle_cam2_{vehicle_count1}")
        
        return jsonify({"status": "success", "request_id": request_id, "folder": folder_name, "saved_images": saved_files, "plate": plate_number, "camera": "camera2", "total_count": vehicle_count1}), 200
    except Exception as e:
        webhook_logger.error(f"Error processing Camera 2 tollgate: {str(e)}")
        return jsonify({"status": "error", "message": str(e), "camera": "camera2"}), 400

@app.route("/webhook/events1", methods=["GET"])
def get_events1():
    limit = request.args.get('limit', default=20, type=int)
    try:
        events = db.get_webhook_events(limit=limit)
        camera2_events = [e for e in events if 'camera2' in str(e.get('event_type', ''))]
        return jsonify(camera2_events if camera2_events else events)
    except Exception as e:
        webhook_logger.error(f"Database error: {str(e)}")
        return jsonify(recent_events1)

@app.route("/healths", methods=["GET", "POST"])
def health_checks():
    webhook_logger.info(f"Health check from {request.remote_addr} - Camera 2")
    return jsonify({"status": "healthy", "camera": "camera2", "vehicle_count": vehicle_count1, "database": db_type})

# =======================================
# COMBINED ENDPOINTS
# =======================================

@app.route("/vehicle-detections", methods=["GET"])
def get_vehicle_detections():
    limit = request.args.get('limit', default=50, type=int)
    try:
        detections = db.get_vehicle_detections(limit=limit)
        return jsonify(detections)
    except Exception as e:
        webhook_logger.error(f"Database error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/vehicle-detections/<plate>", methods=["GET"])
def get_vehicle_by_plate(plate):
    try:
        detections = db.get_vehicle_by_plate(plate)
        return jsonify(detections)
    except Exception as e:
        webhook_logger.error(f"Database error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/vehicle/count", methods=["GET"])
def get_vehicle_count():
    return jsonify({"camera1_count": vehicle_count, "camera2_count": vehicle_count1, "total_vehicles": vehicle_count + vehicle_count1, "database": db_type, "timestamp": datetime.now().isoformat()})

@app.errorhandler(404)
def handle_404(e):
    path = request.path
    method = request.method
    webhook_logger.error(f"404 Error: {method} {path}")
    return jsonify(error="Resource not found", path=path), 404

@app.route("/")
def index():
    return render_template_string("""
<!doctype html>
<html>
<head>
    <title>Multi-Camera ANPR System - PostgreSQL</title>
    <style>
        body { font-family: Arial; margin: 20px; background: #f5f5f5; }
        .container { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .camera { border: 1px solid #ddd; padding: 15px; border-radius: 5px; background: white; box-shadow: 0 2px 4px; }
        h2 { margin-top: 0; color: #333; }
        pre { background: #f4f4f4; padding: 10px; max-height: 400px; font-size: 11px; overflow: auto; }
        .stats { background: #e8f4f8; padding: 15px; border-radius: 5px; margin-bottom: 20px; border-left: 4px solid #0077cc; }
        button { padding: 8px 15px; margin: 5px 5px 5px 0; cursor: pointer; background: #0077cc; color: white; border: none; border-radius: 3px; }
        button:hover { background: #005fa3; }
        .db-status { color: #00a650; font-weight: bold; }
    </style>
</head>
<body>
<h1>Multi-Camera ANPR System</h1>
<div class="stats">
    <h3>System Status</h3>
    <p><strong>Database:</strong> <span class="db-status">PostgreSQL ✓</span></p>
    <p><strong>Vehicles:</strong> Camera 1: <span id="cam1">-</span> | Camera 2: <span id="cam2">-</span> | Total: <span id="total">-</span></p>
</div>
<div class="container">
    <div class="camera">
        <h2>📷 Camera 1</h2>
        <button onclick="load1()">Refresh</button>
        <pre id="e1">Loading...</pre>
    </div>
    <div class="camera">
        <h2>📷 Camera 2</h2>
        <button onclick="load2()">Refresh</button>
        <pre id="e2">Loading...</pre>
    </div>
</div>
<script>
async function load1(){const r=await fetch("/webhook/events?limit=5");document.getElementById("e1").textContent=JSON.stringify(await r.json(),null,2)}
async function load2(){const r=await fetch("/webhook/events1?limit=5");document.getElementById("e2").textContent=JSON.stringify(await r.json(),null,2)}
async function loadCounts(){const r=await fetch("/vehicle/count"),d=await r.json();document.getElementById("cam1").textContent=d.camera1_count;document.getElementById("cam2").textContent=d.camera2_count;document.getElementById("total").textContent=d.total_vehicles}
load1();load2();loadCounts();setInterval(loadCounts,5000);
</script>
</body>
</html>
""")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
