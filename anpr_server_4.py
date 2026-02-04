from flask import Flask, request, jsonify, render_template_string
import base64, os, json
from datetime import datetime

app = Flask(__name__)
recent_events = []
vehicle_count = 0

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
webhook_log_file = os.path.join(
    os.path.abspath(LOG_DIR), f"webhook_events_{datetime.now().strftime('%Y%m%d')}.log"
)

# Direct file write at startup
try:
    with open(webhook_log_file, 'a', encoding='utf-8') as f:
        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - INFO - === SERVER 4 STARTED (Port 8082) ===\n")
        f.flush()
        os.fsync(f.fileno())
except Exception as e:
    print(f"[ERROR] Could not write to log: {e}")

# Simple logging function that writes directly to file
def log_event(message):
    try:
        with open(webhook_log_file, 'a', encoding='utf-8') as f:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"{timestamp} - INFO - {message}\n")
            f.flush()
            os.fsync(f.fileno())
    except Exception as e:
        print(f"Log error: {e}")

# Function to save JSON data
def save_json_data(data, prefix="vehicle"):
    try:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{ts}.json"
        filepath = os.path.join(JSON_DIR, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
            f.flush()
            os.fsync(f.fileno())
        log_event(f"JSON saved: {filename}")
        return filename
    except Exception as e:
        print(f"JSON save error: {e}")
        return None

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

    # Increment vehicle count and log
    global vehicle_count
    vehicle_count += 1
    log_event(f"POST /webhook - VEHICLE #{vehicle_count} - received payload")
    
    # Save JSON data (including images as base64)
    json_data = {
        "vehicle_number": vehicle_count,
        "timestamp": datetime.now().isoformat(),
        "data": event
    }
    save_json_data(json_data, f"webhook_{vehicle_count}")

    return jsonify({"status": "ok", "total_count": vehicle_count})

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
    log_event(f"POST/GET /health from {request.remote_addr}")
    return jsonify({"status": "healthy"})

# =========================
# Catch 404s and log
# =========================
@app.errorhandler(404)
def handle_404(e):
    log_event(f"404 Error: {request.path}")
    return jsonify(error="Resource not found", path=request.path), 404

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
    app.run(host="0.0.0.0", port=8082)