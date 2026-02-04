from flask import Flask, request, jsonify, render_template_string
import base64, os, uuid
from datetime import datetime
import logging

app = Flask(__name__)
recent_events = []

# Directories
SAVE_DIR = "./downloads"
LOG_DIR = "./logs"
os.makedirs(SAVE_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

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

# Add handler if not already added
if not webhook_logger.hasHandlers():
    webhook_logger.addHandler(file_handler)

# =========================
# Utility: detect image type
# =========================
def get_image_format(b64_data):
    try:
        img_bytes = base64.b64decode(b64_data)
        # Detect image format from magic bytes
        if img_bytes.startswith(b'\xff\xd8\xff'):
            return ".jpg"
        elif img_bytes.startswith(b'\x89PNG'):
            return ".png"
        elif img_bytes.startswith(b'GIF87a') or img_bytes.startswith(b'GIF89a'):
            return ".gif"
        elif img_bytes.startswith(b'RIFF') and b'WEBP' in img_bytes[:12]:
            return ".webp"
        else:
            return ".jpg"  # default to jpg
    except:
        return ".jpg"

# =========================
# Webhook POST
# =========================
@app.route("/webhook", methods=["POST"])
def webhook():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    event = {"ReceivedAt": datetime.now().isoformat()}

    # JSON payload
    if request.is_json:
        data = request.get_json(force=True)
        event["Payload"] = data

        # Save image if exists
        if isinstance(data, dict) and "Image" in data:
            img_b64 = data["Image"]
            img_ext = get_image_format(img_b64)
            img_file = f"{data.get('Plate','UNKNOWN')}_{ts}{img_ext}"
            with open(os.path.join(SAVE_DIR, img_file), "wb") as f:
                f.write(base64.b64decode(img_b64))
            event["ImageSavedAs"] = img_file

    # Non-JSON raw data
    else:
        event["RawData"] = request.data.decode(errors="ignore")

    # Multipart files
    if request.files:
        event["Files"] = []
        for name, file in request.files.items():
            img_file = f"{name}_{ts}.jpg"
            file.save(os.path.join(SAVE_DIR, img_file))
            event["Files"].append({"field": name, "filename": file.filename, "saved_as": img_file})

    # Store event in memory
    recent_events.insert(0, event)
    recent_events[:] = recent_events[:20]

    # Log to separate webhook file
    webhook_logger.info(event)

    return jsonify({"status": "ok"})


@app.route("/NotificationInfo/TollgateInfo", methods=["POST"])
def crossing():
    # 1. Generate Unique Request ID
    request_id = str(uuid.uuid4())
    data = request.get_json(force=True)
    
    # 2. Extract Metadata for folder naming/logging
    # Safely navigate the nested structure
    picture_data = data.get("Picture", {})
    plate_info = picture_data.get("Plate", {})
    snap_info = picture_data.get("SnapInfo", {})
    
    plate_number = plate_info.get("PlateNumber", "UNKNOWN")
    device_id = snap_info.get("DeviceID", "NO_ID")
    
    # Create directory: downloads/PLATE_DEVICEID_UUID
    folder_name = f"{plate_number}_{device_id}_{request_id[:8]}"
    request_dir = os.path.join(SAVE_DIR, folder_name)
    os.makedirs(request_dir, exist_ok=True)

    saved_files = []

    # 3. Helper to process specific picture objects
    def save_nested_image(pic_obj, prefix):
        if pic_obj and "Content" in pic_obj:
            content = pic_obj["Content"].replace('\\/', '/')
            # Use their filename or generate one
            filename = pic_obj.get("PicName") or f"{prefix}_{request_id[:8]}.jpg"
            full_path = os.path.join(request_dir, filename)
            
            with open(full_path, "wb") as f:
                f.write(base64.b64decode(content))
            return filename
        return None

    # 4. Save both Cutout and Normal pictures
    cutout = save_nested_image(picture_data.get("CutoutPic"), "cutout")
    normal = save_nested_image(picture_data.get("NormalPic"), "normal")

    if cutout: saved_files.append(cutout)
    if normal: saved_files.append(normal)

    # 5. Log and Respond
    response_data = {
        "status": "success",
        "request_id": request_id,
        "folder": folder_name,
        "saved_images": saved_files,
        "plate": plate_number
    }
    
    print(f"Processed Request {request_id}: Saved {len(saved_files)} images for {plate_number}")
    
    return jsonify(response_data), 200

# =========================
# GET Events
# =========================
@app.route("/webhook/events", methods=["GET"])
def get_events():
    return jsonify(recent_events)

# =========================
# Health check
# =========================
@app.route("/health", methods=["GET", "POST"])
def health_check():
    return jsonify({"status": "healthy"})

# =========================
# Catch 404s and log
# =========================
@app.errorhandler(404)
def handle_404(e):
    # Log the basics first so you have info even if the body read fails
    path = request.path
    method = request.method
    
    # Check content length to avoid loading massive images into the log
    content_length = request.content_length or 0
    if content_length > 1024 * 10:  # If body > 10KB, don't log the whole thing
        request_data = f"<Payload too large to log: {content_length} bytes>"
    else:
        request_data = request.get_data(as_text=True, errors="ignore")

    webhook_logger.error(f"404 Error: {method} {path} | Body: {request_data}")
    return jsonify(error="Resource not found", path=path), 404

# =========================
# Simple frontend to view events
# =========================
@app.route("/")
def index():
    return render_template_string("""
<!doctype html>
<html>
<head><title>Webhook Events</title></head>
<body>
<h2>Webhook Events (Latest 20)</h2>
<pre id="events"></pre>
<script>
async function load() {
  const res = await fetch("/webhook/events");
  const data = await res.json();
  document.getElementById("events").textContent = JSON.stringify(data, null, 2);
}
load();
</script>
</body>
</html>
""")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)