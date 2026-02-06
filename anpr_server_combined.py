"""
Combined ANPR Server - Multi-Camera Support with PostgreSQL Database
Camera 1: /webhook, /health, /NotificationInfo/TollgateInfo
Camera 2: /webhooks, /healths, /NotificationInfo/TollgateInfo1
Database: PostgreSQL ONLY with vehicle_detection
"""

from flask import Flask, request, jsonify, render_template_string
import base64, os, json, uuid, logging
from datetime import datetime
from dotenv import load_dotenv

# =========================
# ENV & DB INIT
# =========================
load_dotenv()

db = None
db_type = None

try:
    from postgres_db import db as pg_db
    db = pg_db
    db_type = "PostgreSQL"
except Exception as e:
    print(f"PostgreSQL failed: {e}")
    from simple_db import db as sqlite_db
    db = sqlite_db
    db_type = "SQLite"

app = Flask(__name__)

vehicle_count = 0
vehicle_count1 = 0
recent_events = []
recent_events1 = []

# =========================
# DIRECTORIES
# =========================
SAVE_DIR = "./downloads"
LOG_DIR = "./logs"
JSON_CAM1 = "./json_data/camera1"
JSON_CAM2 = "./json_data/camera2"

for d in [SAVE_DIR, LOG_DIR, JSON_CAM1, JSON_CAM2]:
    os.makedirs(d, exist_ok=True)

# =========================
# LOGGER SETUP
# =========================
def create_logger(name, filename):
    logger = logging.getLogger(name)

    # 🔥 CRITICAL FIXES
    logger.setLevel(logging.INFO)
    logger.propagate = False   # stop leaking to root logger

    # 🔥 REMOVE OLD HANDLERS (important!)
    if logger.handlers:
        for h in logger.handlers[:]:
            logger.removeHandler(h)
            h.close()

    file_path = os.path.join(LOG_DIR, filename)
    handler = logging.FileHandler(file_path)
    handler.setLevel(logging.INFO)
    handler.flush()  # Flush immediately after creation

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger

cam1_logger = create_logger(
    "camera1_logger",
    f"camera1_{datetime.now().strftime('%Y%m%d')}.log"
)

cam2_logger = create_logger(
    "camera2_logger",
    f"camera2_{datetime.now().strftime('%Y%m%d')}.log"
)

# Auto-flush wrapper
def log_info(logger, msg):
    logger.info(msg)
    for handler in logger.handlers:
        handler.flush()

def log_error(logger, msg):
    logger.error(msg)
    for handler in logger.handlers:
        handler.flush()


# =========================
# UTILITIES
# =========================
def get_image_format(b64_data):
    try:
        img = base64.b64decode(b64_data)
        if img.startswith(b'\xff\xd8'):
            return ".jpg"
        elif img.startswith(b'\x89PNG'):
            return ".png"
        return ".jpg"
    except:
        return ".jpg"


def save_json(data, prefix, camera):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_{ts}.json"
    base = JSON_CAM1 if camera == "camera1" else JSON_CAM2
    path = os.path.join(base, filename)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
        f.flush()
        os.fsync(f.fileno())

    return filename


def save_nested_image(pic_obj, folder, fallback):
    if not pic_obj or "Content" not in pic_obj:
        return None
    content = pic_obj["Content"].replace('\\/', '/')
    name = pic_obj.get("PicName") or fallback
    with open(os.path.join(folder, name), "wb") as f:
        f.write(base64.b64decode(content))
    return name

# =========================
# CAMERA 1
# =========================
@app.route("/webhook", methods=["POST"])
def cam1_webhook():
    global vehicle_count
    vehicle_count += 1

    data = request.get_json(force=True, silent=True)
    event_id = str(uuid.uuid4())

    log_info(cam1_logger, f"/webhook VEHICLE #{vehicle_count}")

    try:
        db.add_webhook_event(event_id, "webhook_camera1", data, data)
    except Exception as e:
        log_error(cam1_logger, f"DB error: {e}")

    save_json({"vehicle": vehicle_count, "data": data}, "webhook", "camera1")
    return jsonify(status="ok", camera="camera1", count=vehicle_count)

@app.route("/NotificationInfo/TollgateInfo", methods=["POST"])
def cam1_tollgate():
    global vehicle_count
    vehicle_count += 1

    data = request.get_json(force=True)
    plate = data.get("Picture", {}).get("Plate", {}).get("PlateNumber", "UNKNOWN")
    req_id = str(uuid.uuid4())

    folder = os.path.join(SAVE_DIR, f"{plate}_CAM1_{req_id[:6]}")
    os.makedirs(folder, exist_ok=True)

    pic = data.get("Picture", {})
    files = []

    f1 = save_nested_image(pic.get("CutoutPic"), folder, "cutout.jpg")
    f2 = save_nested_image(pic.get("NormalPic"), folder, "normal.jpg")

    if f1: files.append(f1)
    if f2: files.append(f2)

    # ✅ CORRECT LOG (only once, before return)
    cam1_logger.info(
        f"POST /NotificationInfo/TollgateInfo (Camera 1) "
        f"- VEHICLE #{vehicle_count} - Plate: {plate}"
    )

    try:
        db.add_vehicle_detection(req_id, plate, data, folder)
    except Exception as e:
        cam1_logger.error(f"DB error: {e}")

    save_json({"plate": plate, "files": files}, "vehicle", "camera1")

    return jsonify(status="success", plate=plate, camera="camera1")



@app.route("/health")
def cam1_health():
    log_info(cam1_logger, "Health check")
    return jsonify(camera="camera1", status="healthy", count=vehicle_count)


# =========================
# CAMERA 2
# =========================
@app.route("/webhooks", methods=["POST"])
def cam2_webhook():
    global vehicle_count1
    vehicle_count1 += 1

    data = request.get_json(force=True, silent=True)
    event_id = str(uuid.uuid4())

    log_info(cam2_logger, f"/webhooks VEHICLE #{vehicle_count1}")

    try:
        db.add_webhook_event(event_id, "webhook_camera2", data, data)
    except Exception as e:
        log_error(cam2_logger, f"DB error: {e}")

    save_json({"vehicle": vehicle_count1, "data": data}, "webhook", "camera2")
    return jsonify(status="ok", camera="camera2", count=vehicle_count1)

@app.route("/NotificationInfo/TollgateInfo1", methods=["POST"])
def cam2_tollgate():
    global vehicle_count1
    vehicle_count1 += 1

    data = request.get_json(force=True)
    plate = data.get("Picture", {}).get("Plate", {}).get("PlateNumber", "UNKNOWN")
    req_id = str(uuid.uuid4())

    folder = os.path.join(SAVE_DIR, f"{plate}_CAM2_{req_id[:6]}")
    os.makedirs(folder, exist_ok=True)

    pic = data.get("Picture", {})
    files = []

    f1 = save_nested_image(pic.get("CutoutPic"), folder, "cutout.jpg")
    f2 = save_nested_image(pic.get("NormalPic"), folder, "normal.jpg")

    if f1: files.append(f1)
    if f2: files.append(f2)

    # ✅ CORRECT, EXPLICIT LOG
    cam2_logger.info(
        f"POST /NotificationInfo/TollgateInfo1 (Camera 2) "
        f"- VEHICLE #{vehicle_count1} - Plate: {plate}"
    )

    try:
        db.add_vehicle_detection(req_id, plate, data, folder)
    except Exception as e:
        cam2_logger.error(f"DB error: {e}")

    save_json({"plate": plate, "files": files}, "vehicle", "camera2")
    
    return jsonify(status="success", plate=plate, camera="camera2")


@app.route("/healths")
def cam2_health():
    log_info(cam2_logger, "Health check")
    return jsonify(camera="camera2", status="healthy", count=vehicle_count1)


# =========================
# COMMON
# =========================
@app.route("/vehicle/count")
def count():
    return jsonify(
        cam1=vehicle_count,
        cam2=vehicle_count1,
        total=vehicle_count + vehicle_count1,
        db=db_type
    )


@app.route("/")
def index():
    return "<h2>Multi-Camera ANPR Server Running</h2>"


if __name__ == "__main__":
    print("🚀 ANPR Server Started")
    app.run(host="0.0.0.0", port=5001, debug=False)
