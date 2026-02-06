from flask import Flask, render_template, jsonify, request, send_file
import os
import json
import logging
from datetime import datetime
from pathlib import Path
import sqlite3
import base64
import uuid
from postgres_db import db

app = Flask(__name__, template_folder='templates')

# ==================== CONFIG ====================
DOWNLOADS_DIR = "./downloads"
JSON_DIR = "./json_data"
LOGS_DIR = "./logs"

os.makedirs(DOWNLOADS_DIR, exist_ok=True)
os.makedirs(JSON_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# ==================== WEBHOOK LOGGER ====================
webhook_log_file = os.path.join(LOGS_DIR, f"webhook_events_{datetime.now().strftime('%Y%m%d')}.log")
webhook_logger = logging.getLogger("webhook_logger")
webhook_logger.setLevel(logging.INFO)
webhook_logger.propagate = False

# Ensure absolute path and encoding, remove any existing handlers, then add fresh FileHandler
webhook_log_file = os.path.abspath(webhook_log_file)
for h in webhook_logger.handlers[:]:
    try:
        webhook_logger.removeHandler(h)
    except Exception:
        pass

file_handler = logging.FileHandler(webhook_log_file, mode='a', encoding='utf-8')
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

webhook_logger.addHandler(file_handler)

# ==================== UTILITIES ====================
def get_image_format(b64_data):
    """Detect image format from base64 data"""
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

def extract_images_from_json(data):
    """Extract image data from JSON"""
    images = []
    try:
        if 'Picture' in data:
            picture = data['Picture']
            
            # Cutout image (plate zoom)
            if 'CutoutPic' in picture and 'Content' in picture['CutoutPic']:
                content = picture['CutoutPic']['Content']
                images.append({
                    'type': 'cutout',
                    'url': f"data:image/jpeg;base64,{content}",
                    'name': picture['CutoutPic'].get('PicName', 'cutout.jpg')
                })
            
            # Normal vehicle image
            if 'VehiclePic' in picture and 'Content' in picture['VehiclePic']:
                content = picture['VehiclePic']['Content']
                images.append({
                    'type': 'vehicle',
                    'url': f"data:image/jpeg;base64,{content}",
                    'name': picture['VehiclePic'].get('PicName', 'vehicle.jpg')
                })
            
            # NormalPic as fallback
            if 'NormalPic' in picture and 'Content' in picture['NormalPic']:
                content = picture['NormalPic']['Content']
                images.append({
                    'type': 'normal',
                    'url': f"data:image/jpeg;base64,{content}",
                    'name': picture['NormalPic'].get('PicName', 'normal.jpg')
                })
    except:
        pass
    
    return images

def get_folder_images(plate_str):
    """Get actual image files from downloads folder"""
    images = []
    downloads = Path(DOWNLOADS_DIR)
    
    for folder in downloads.glob(f"*{plate_str}*"):
        if folder.is_dir():
            for img_file in folder.glob("*.jpg"):
                images.append({
                    'path': f"/image/{folder.name}/{img_file.name}",
                    'name': img_file.name,
                    'folder': folder.name
                })
    
    return images

def get_recent_events(limit=50):
    """Get recent detection events from JSON files"""
    events = []
    json_path = Path(JSON_DIR)
    
    if json_path.exists():
        json_files = sorted(json_path.glob("*.json"), reverse=True)[:limit]
        for file in json_files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Extract key info from nested structure
                    picture_data = data.get('Picture', {})
                    plate_info = picture_data.get('Plate', {})
                    snap_info = picture_data.get('SnapInfo', {})
                    vehicle_info = picture_data.get('Vehicle', {})
                    
                    plate = plate_info.get('PlateNumber', 'UNKNOWN')
                    device_id = snap_info.get('DeviceID', '')
                    
                    event = {
                        'filename': file.name,
                        'plate': plate,
                        'camera': device_id if device_id else file.name.split('_')[0] if '_' in file.name else 'unknown',
                        'timestamp': snap_info.get('AccurateTime', ''),
                        'vehicle_color': vehicle_info.get('VehicleColor', 'Unknown'),
                        'plate_color': plate_info.get('PlateColor', 'Unknown'),
                    }
                    
                    # Extract images
                    images = extract_images_from_json(data)
                    event['json_images'] = images
                    
                    # Get actual image files
                    event['file_images'] = get_folder_images(plate)
                    
                    events.append(event)
            except Exception as e:
                print(f"Error processing {file}: {e}")
    
    return events

def get_vehicle_statistics():
    """Calculate vehicle statistics from recent events"""
    events = get_recent_events(100)
    stats = {
        'total_vehicles': len(events),
        'cameras': {},
        'top_plates': {},
        'hourly': {}
    }
    
    for event in events:
        camera = event.get('camera', 'unknown')
        plate = event.get('plate', 'UNKNOWN')
        
        # Camera stats
        if camera not in stats['cameras']:
            stats['cameras'][camera] = 0
        stats['cameras'][camera] += 1
        
        # Top plates
        if plate not in stats['top_plates']:
            stats['top_plates'][plate] = 0
        stats['top_plates'][plate] += 1
    
    # Sort top plates
    stats['top_plates'] = dict(sorted(stats['top_plates'].items(), 
                                      key=lambda x: x[1], reverse=True)[:10])
    
    return stats

def get_folder_images(folder_name):
    """Get images from a specific detection folder"""
    folder_path = Path(DOWNLOADS_DIR) / folder_name
    images = []
    
    if folder_path.exists():
        for img_file in folder_path.glob("*.jpg"):
            images.append({
                'name': img_file.name,
                'path': f"/image/{folder_name}/{img_file.name}"
            })
    
    return images

# ==================== WEBHOOK ENDPOINTS ====================

@app.route("/webhook", methods=["POST"])
def webhook():
    """General webhook endpoint for image/data submission"""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    event_id = str(uuid.uuid4())
    event = {"EventID": event_id, "ReceivedAt": datetime.now().isoformat()}

    # JSON payload
    if request.is_json:
        data = request.get_json(force=True)
        event["Payload"] = data

        # ALWAYS save the full incoming payload as JSON (for all camera types/structures)
        try:
            payload_filename = f"payload_{event_id}_{ts}.json"
            payload_path = os.path.join(JSON_DIR, payload_filename)
            with open(payload_path, 'w', encoding='utf-8') as pf:
                json.dump(data, pf, indent=2, ensure_ascii=False, default=str)
            event['RawPayloadSaved'] = payload_filename
        except Exception:
            pass

        # Save image if exists
        # If payload has top-level Image (older cameras)
        if isinstance(data, dict) and "Image" in data:
            img_b64 = data["Image"]
            img_ext = get_image_format(img_b64)
            img_file = f"{data.get('Plate','UNKNOWN')}_{ts}{img_ext}"
            with open(os.path.join(DOWNLOADS_DIR, img_file), "wb") as f:
                f.write(base64.b64decode(img_b64))
            event["ImageSavedAs"] = img_file

        # If payload follows nested Picture structure, save nested images and JSON
        if isinstance(data, dict) and "Picture" in data:
            picture_data = data.get('Picture', {})
            plate_info = picture_data.get('Plate', {})
            snap_info = picture_data.get('SnapInfo', {})

            plate_number = plate_info.get('PlateNumber', 'UNKNOWN')
            device_id = snap_info.get('DeviceID', '') or 'NOID'
            req_id = str(uuid.uuid4())
            folder_name = f"{plate_number}_{device_id}_{req_id[:8]}"
            request_dir = os.path.join(DOWNLOADS_DIR, folder_name)
            os.makedirs(request_dir, exist_ok=True)

            saved = []

            def _save_nested(pic_obj, default_prefix):
                if pic_obj and isinstance(pic_obj, dict) and 'Content' in pic_obj:
                    content = pic_obj['Content'].replace('\\/', '/')
                    fname = pic_obj.get('PicName') or f"{default_prefix}_{req_id[:8]}.jpg"
                    full = os.path.join(request_dir, fname)
                    try:
                        with open(full, 'wb') as out:
                            out.write(base64.b64decode(content))
                        return fname
                    except Exception:
                        return None
                return None

            for key, prefix in (('CutoutPic', 'cutout'), ('NormalPic', 'normal'), ('VehiclePic', 'vehicle')):
                n = _save_nested(picture_data.get(key), prefix)
                if n:
                    saved.append(n)

            # Save JSON copy for this event
            json_filename = f"{plate_number}_{ts}.json"
            json_path = os.path.join(JSON_DIR, json_filename)
            try:
                with open(json_path, 'w', encoding='utf-8') as jf:
                    json.dump(data, jf, indent=2, ensure_ascii=False)
            except Exception:
                pass

            event['SavedFolder'] = folder_name
            event['SavedImages'] = saved
            event['SavedJSON'] = json_filename

    # Non-JSON raw data
    else:
        event["RawData"] = request.data.decode(errors="ignore")

    # Multipart files
    if request.files:
        event["Files"] = []
        for name, file in request.files.items():
            img_file = f"{name}_{ts}.jpg"
            file.save(os.path.join(DOWNLOADS_DIR, img_file))
            event["Files"].append({"field": name, "filename": file.filename, "saved_as": img_file})

    # Persist to Postgres (best-effort)
    try:
        vehicle_data = None
        if isinstance(data, dict):
            # extract plate if available
            pic = data.get('Picture') if isinstance(data, dict) else None
            if pic and isinstance(pic, dict):
                plate = pic.get('Plate', {}).get('PlateNumber')
                vehicle_data = {'plate': plate} if plate else None

        image_fname = event.get('ImageSavedAs') or event.get('SavedImages', [None])[0] if event.get('SavedImages') else None
        db.add_webhook_event(event_id, 'webhook', data, vehicle_data=vehicle_data, image_filename=image_fname)
    except Exception:
        pass

    # Always save a JSON metadata file for the event (best-effort)
    try:
        meta_name = f"event_{event_id}_{ts}.json"
        meta_path = os.path.join(JSON_DIR, meta_name)
        with open(meta_path, 'w', encoding='utf-8') as mf:
            json.dump(event, mf, indent=2, ensure_ascii=False, default=str)
        event['SavedJSON'] = meta_name
    except Exception:
        pass

    # Log event (as JSON string for clarity)
    try:
        webhook_logger.info(json.dumps(event, ensure_ascii=False))
        # flush handlers to ensure immediate write
        for h in webhook_logger.handlers:
            try:
                h.flush()
            except Exception:
                pass
    except Exception:
        try:
            webhook_logger.info(str(event))
        except Exception:
            pass
    
    return jsonify({"status": "ok"})


@app.route("/NotificationInfo/TollgateInfo", methods=["POST"])
def crossing():
    """Main endpoint for vehicle detection - saves images and JSON data"""
    request_id = str(uuid.uuid4())
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    data = request.get_json(force=True)
    
    # ALWAYS save the full incoming payload as JSON (universal for all payloads)
    try:
        payload_filename = f"payload_{request_id}_{ts}.json"
        payload_path = os.path.join(JSON_DIR, payload_filename)
        with open(payload_path, 'w', encoding='utf-8') as pf:
            json.dump(data, pf, indent=2, ensure_ascii=False, default=str)
    except Exception:
        pass
    
    # Extract metadata
    picture_data = data.get("Picture", {})
    plate_info = picture_data.get("Plate", {})
    snap_info = picture_data.get("SnapInfo", {})
    
    plate_number = plate_info.get("PlateNumber", "UNKNOWN")
    device_id = snap_info.get("DeviceID", "NO_ID")
    
    # Create directory: downloads/PLATE_DEVICEID_UUID
    folder_name = f"{plate_number}_{device_id}_{request_id[:8]}"
    request_dir = os.path.join(DOWNLOADS_DIR, folder_name)
    os.makedirs(request_dir, exist_ok=True)

    saved_files = []

    # Helper to process nested picture objects
    def save_nested_image(pic_obj, prefix):
        if pic_obj and "Content" in pic_obj:
            content = pic_obj["Content"].replace('\\/', '/')
            filename = pic_obj.get("PicName") or f"{prefix}_{request_id[:8]}.jpg"
            full_path = os.path.join(request_dir, filename)
            
            with open(full_path, "wb") as f:
                f.write(base64.b64decode(content))
            return filename
        return None

    # Save Cutout and Normal pictures
    cutout = save_nested_image(picture_data.get("CutoutPic"), "cutout")
    normal = save_nested_image(picture_data.get("NormalPic"), "normal")
    vehicle = save_nested_image(picture_data.get("VehiclePic"), "vehicle")

    if cutout: saved_files.append(cutout)
    if normal: saved_files.append(normal)
    if vehicle: saved_files.append(vehicle)

    # Save JSON data
    json_filename = f"{plate_number}_{snap_info.get('AccurateTime', ts.replace(' ', '_'))}.json"
    json_path = os.path.join(JSON_DIR, json_filename)
    with open(json_path, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    # Log event
    response_data = {
        "status": "success",
        "request_id": request_id,
        "folder": folder_name,
        "saved_images": saved_files,
        "json_file": json_filename,
        "plate": plate_number
    }
    
    webhook_logger.info(f"Processed Request {request_id}: Saved {len(saved_files)} images and JSON for {plate_number}")
    print(f"[+] Processed {plate_number}: {len(saved_files)} images saved to {folder_name}")
    
    return jsonify(response_data), 200

# ==================== DASHBOARD & API ROUTES ====================

@app.route('/')
def dashboard():
    """Main dashboard"""
    return render_template('dashboard.html')

@app.route('/api/stats')
def api_stats():
    """Get vehicle statistics"""
    return jsonify(get_vehicle_statistics())


@app.route('/api/db-stats')
def api_db_stats():
    """Return simple DB statistics for UI"""
    try:
        # get recent webhook events (best-effort)
        rows = db.get_webhook_events(limit=1000)
        total = len(rows)
    except Exception:
        total = 0
    return jsonify({
        'total_vehicles': total
    })


@app.route('/api/db/sync', methods=['POST'])
def api_db_sync():
    """Scan JSON_DIR and insert JSON events into Postgres (idempotent)"""
    synced = 0
    json_path = Path(JSON_DIR)
    if not json_path.exists():
        return jsonify({'synced': synced})

    for jf in sorted(json_path.glob('*.json')):
        try:
            with open(jf, 'r', encoding='utf-8') as f:
                data = json.load(f)
            event_id = jf.name
            # extract plate if present
            pic = data.get('Picture') if isinstance(data, dict) else None
            vehicle_data = None
            if pic and isinstance(pic, dict):
                plate = pic.get('Plate', {}).get('PlateNumber')
                device = pic.get('SnapInfo', {}).get('DeviceID')
                vehicle_data = {'plate': plate, 'device': device}

            db.add_webhook_event(event_id, 'json_file', data, vehicle_data=vehicle_data, image_filename=None)
            synced += 1
        except Exception:
            continue

    return jsonify({'synced': synced})


@app.route('/api/db/date-wise')
def api_db_date_wise():
    """Return detections grouped by date from webhook_events"""
    try:
        rows = db.get_webhook_events(limit=5000)
    except Exception:
        rows = []

    buckets = {}
    for r in rows:
        created = r.get('created_at') or r.get('timestamp')
        if not created:
            continue
        date = str(created)[:10]
        if date not in buckets:
            buckets[date] = {'date': date, 'count': 0, 'plates': []}
        buckets[date]['count'] += 1
        plate = None
        try:
            plate = (r.get('vehicle_data') or {}).get('plate')
        except Exception:
            plate = None
        if plate:
            buckets[date]['plates'].append(plate)

    # convert to list, sort desc
    out = sorted(buckets.values(), key=lambda x: x['date'], reverse=True)
    return jsonify(out)


@app.route('/api/db/date/<date_str>')
def api_db_date_records(date_str):
    """Return records for a specific date (YYYY-MM-DD)"""
    try:
        rows = db.get_webhook_events(limit=5000)
    except Exception:
        rows = []

    records = []
    for r in rows:
        created = r.get('created_at') or r.get('timestamp')
        if not created:
            continue
        if str(created).startswith(date_str):
            plate = None
            try:
                plate = (r.get('vehicle_data') or {}).get('plate')
            except Exception:
                plate = None
            records.append({
                'created_at': r.get('created_at'),
                'plate': plate,
                'camera': (r.get('data') or {}).get('Picture', {}).get('SnapInfo', {}).get('DeviceID', 'unknown'),
                'plate_color': (r.get('data') or {}).get('Picture', {}).get('Plate', {}).get('PlateColor')
            })

    return jsonify({'total': len(records), 'records': records})


@app.route('/api/camera-stats')
def api_camera_stats():
    """Return stats per camera for UI"""
    try:
        rows = db.get_webhook_events(limit=5000)
    except Exception:
        rows = []

    stats = {}
    for r in rows:
        data = r.get('data') or {}
        pic = data.get('Picture') if isinstance(data, dict) else None
        camera = 'unknown'
        if pic:
            camera = pic.get('SnapInfo', {}).get('DeviceID', camera)
        if camera not in stats:
            stats[camera] = {'total_detections': 0, 'unique_plates': set(), 'top_plates': {}}
        stats[camera]['total_detections'] += 1
        plate = None
        try:
            plate = pic.get('Plate', {}).get('PlateNumber')
        except Exception:
            plate = None
        if plate:
            stats[camera]['unique_plates'].add(plate)
            stats[camera]['top_plates'][plate] = stats[camera]['top_plates'].get(plate, 0) + 1

    # convert sets and sort top plates
    out = {}
    for cam, v in stats.items():
        out[cam] = {
            'total_detections': v['total_detections'],
            'unique_plates': len(v['unique_plates']),
            'top_plates': dict(sorted(v['top_plates'].items(), key=lambda x: x[1], reverse=True)[:10])
        }

    return jsonify(out)

@app.route('/api/events')
def api_events():
    """Get recent events"""
    limit = request.args.get('limit', 50, type=int)
    events = get_recent_events(limit)
    return jsonify(events)

@app.route('/api/cameras')
def api_cameras():
    """Get camera list and status"""
    cameras = {
        'camera1': {
            'name': 'Camera 1',
            'ip': '192.168.1.108',
            'status': 'active',
            'location': 'Gate 1'
        },
        'camera2': {
            'name': 'Camera 2',
            'ip': '192.168.1.109',
            'status': 'active',
            'location': 'Gate 2'
        }
    }
    return jsonify(cameras)

@app.route('/api/images/<folder_name>')
def api_folder_images(folder_name):
    """Get images from a detection folder"""
    images = get_folder_images(folder_name)
    return jsonify(images)

@app.route('/image/<folder_name>/<filename>')
def serve_image(folder_name, filename):
    """Serve image from downloads folder"""
    from flask import send_file
    image_path = Path(DOWNLOADS_DIR) / folder_name / filename
    
    if image_path.exists():
        return send_file(image_path, mimetype='image/jpeg')
    else:
        return "Image not found", 404

@app.route('/api/search')
def search_plates():
    """Search for vehicles by plate"""
    query = request.args.get('q', '').upper()
    if not query:
        return jsonify([])
    
    events = get_recent_events(200)
    results = []
    
    for event in events:
        if query in event.get('plate', 'UNKNOWN'):
            results.append({
                'plate': event.get('plate', 'UNKNOWN'),
                'camera': event.get('camera', 'unknown'),
                'time': event.get('timestamp', ''),
                'file': event.get('filename', '')
            })
    
    return jsonify(results[:20])

@app.route('/health', methods=['GET', 'POST'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    print("=" * 50)
    print("[*] VEHICLE DETECTION SERVER STARTED")
    print("=" * 50)
    print("[+] Dashboard: http://localhost:5001/")
    print("[+] Webhook: POST http://localhost:5001/webhook")
    print("[+] Camera: POST http://localhost:5001/NotificationInfo/TollgateInfo")
    print("[+] Images saved to: ./downloads/")
    print("[+] JSON data saved to: ./json_data/")
    print("[+] Logs saved to: ./logs/")
    print("=" * 50)
    app.run(debug=False, port=5001, host='0.0.0.0')
