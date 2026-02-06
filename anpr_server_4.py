from flask import Flask, render_template, jsonify, request, send_file
import os, json, logging, base64, re, uuid
from datetime import datetime
from pathlib import Path

app = Flask(__name__, template_folder="templates")

# ==================== CONFIG ====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOADS_DIR = os.path.join(BASE_DIR, "downloads")
JSON_DIR = os.path.join(BASE_DIR, "json_data")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

os.makedirs(DOWNLOADS_DIR, exist_ok=True)
os.makedirs(JSON_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# ==================== CAMERA IP MAP ====================
CAMERA_IP_MAP = {
    "192.168.1.108": "camera1",
    "192.168.1.109": "camera2",
}

vehicle_count = {"camera1": 0, "camera2": 0, "unknown": 0}

# ==================== LOGGER ====================
log_file = os.path.join(LOGS_DIR, f"webhook_{datetime.now():%Y%m%d}.log")
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ==================== HELPERS ====================
def get_camera():
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    return CAMERA_IP_MAP.get(ip, "unknown")

def safe_name(text):
    return re.sub(r"[^A-Za-z0-9_-]", "_", str(text))

def decode_b64(data):
    if not data:
        return None
    if isinstance(data, bytes):
        return data
    if "," in data:
        data = data.split(",", 1)[1]
    data = data.replace("\\/", "/").strip()
    try:
        return base64.b64decode(data)
    except:
        return None

def save_json(camera, payload):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"{camera}_{ts}.json"
    path = os.path.join(JSON_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, default=str)
    return filename

def save_images(camera, plate, picture):
    folder = f"{camera}_{safe_name(plate)}_{datetime.now():%Y%m%d_%H%M%S}"
    folder_path = os.path.join(DOWNLOADS_DIR, folder)
    os.makedirs(folder_path, exist_ok=True)

    saved = []

    IMAGE_MAP = {
        "CutoutPic": "cutout.jpg",
        "NormalPic": "normal.jpg",
        "VehiclePic": "vehicle.jpg",
    }

    DATA_KEYS = ["Content", "PicData", "Data", "ContentBase64"]

    for key, default_name in IMAGE_MAP.items():
        pic = picture.get(key)
        if not isinstance(pic, dict):
            continue

        img_bytes = None
        for dk in DATA_KEYS:
            if dk in pic:
                img_bytes = decode_b64(pic.get(dk))
                if img_bytes:
                    break

        if not img_bytes:
            continue

        filename = f"{key.lower()}_{pic.get('PicName', default_name)}"
        path = os.path.join(folder_path, filename)

        with open(path, "wb") as f:
            f.write(img_bytes)

        saved.append(filename)

    return folder, saved

# ==================== CORE HANDLER ====================
def process_event():
    camera = get_camera()
    vehicle_count[camera] += 1

    payload = request.get_json(silent=True) or {}
    picture = payload.get("Picture", {})

    plate = picture.get("Plate", {}).get("PlateNumber", "UNKNOWN")

    folder, images = save_images(camera, plate, picture)
    json_file = save_json(camera, payload)

    logging.info(
        f"TOLLGATE | {camera} | Plate={plate} | Images={len(images)} | IP={request.remote_addr}"
    )

    print(f"[OK] {camera} | Plate={plate} | Images={len(images)}")

    return jsonify(
        status="success",
        camera=camera,
        plate=plate,
        count=vehicle_count[camera],
        folder=folder,
        images=images,
        json_file=json_file
    )

# ==================== CAMERA ENDPOINTS ====================
@app.route("/NotificationInfo/TollgateInfo", methods=["POST"])
def tollgate():
    return process_event()

# Backward compatibility (camera misconfig safe)
@app.route("/webhook", methods=["POST"])
@app.route("/webhooks", methods=["POST"])
def webhook_alias():
    return process_event()

# ==================== HEALTH ====================
@app.route("/health", methods=["GET", "POST"])
@app.route("/healths", methods=["GET", "POST"])
def health():
    return jsonify(status="ok")

# ==================== DASHBOARD ====================
@app.route("/")
def dashboard():
    return render_template("dashboard.html")

# ==================== APIs ====================
@app.route("/api/events")
def api_events():
    events = []
    for file in sorted(Path(JSON_DIR).glob("*.json"), reverse=True)[:50]:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
        picture = data.get("Picture", {})
        events.append({
            "plate": picture.get("Plate", {}).get("PlateNumber", "UNKNOWN"),
            "camera": file.name.split("_")[0],
            "time": picture.get("SnapInfo", {}).get("AccurateTime", ""),
            "images": []
        })
    return jsonify(events)

@app.route("/api/images/<folder>")
def api_images(folder):
    path = Path(DOWNLOADS_DIR) / folder
    images = []
    if path.exists():
        for img in path.glob("*.jpg"):
            images.append({
                "name": img.name,
                "url": f"/image/{folder}/{img.name}"
            })
    return jsonify(images)

@app.route("/image/<folder>/<filename>")
def serve_image(folder, filename):
    path = Path(DOWNLOADS_DIR) / folder / filename
    if path.exists():
        return send_file(path, mimetype="image/jpeg")
    return "Not Found", 404

# ==================== RUN ====================
if __name__ == "__main__":
    print("=" * 60)
    print("✅ CP PLUS ANPR SERVER – FINAL VERSION")
    print("Webhook      : /NotificationInfo/TollgateInfo")
    print("Compatibility: /webhook /webhooks")
    print("Health       : /health")
    print("Dashboard    : http://localhost:5001/")
    print("Images dir   :", DOWNLOADS_DIR)
    print("=" * 60)
    app.run(host="0.0.0.0", port=5001, debug=False)
