from flask import Flask, request, jsonify
import os, json, uuid, base64
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
from postgres_db import db

app = Flask(__name__)

BASE = os.getcwd()
LOG_DIR = os.path.join(BASE, "logs")
JSON_DIR = os.path.join(BASE, "json_cam1")
IMG_DIR = os.path.join(BASE, "images_cam1")

for d in [LOG_DIR, JSON_DIR, IMG_DIR]:
    os.makedirs(d, exist_ok=True)

# =====================
# LOG FILE (ONE PER START)
# =====================
log_file = os.path.join(
    LOG_DIR,
    f"camera1_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
)

print("CAM1 log file:", log_file)

# =====================
vehicle_count = 0

# =====================
def write_log(text):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
    line = f"{ts} - {text}\n"

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(line)
        f.flush()
        os.fsync(f.fileno())

# =====================
def save_json(data):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(os.path.join(JSON_DIR, f"{ts}.json"), "w") as f:
        json.dump(data, f, indent=2)

def save_image(pic, folder, name):
    if not pic or "Content" not in pic:
        return
    img = base64.b64decode(pic["Content"])
    with open(os.path.join(folder, name), "wb") as f:
        f.write(img)

# =====================
@app.route("/NotificationInfo/TollgateInfo", methods=["POST"])
def vehicle():
    global vehicle_count
    vehicle_count += 1

    # handle ANY camera payload
    try:
        data = request.get_json(force=True, silent=True)
        if not data:
            data = json.loads(request.data.decode("utf-8"))
    except:
        data = {}

    plate = data.get("Picture", {}).get("Plate", {}).get("PlateNumber", "UNKNOWN")
    event_id = str(uuid.uuid4())

    folder = os.path.join(IMG_DIR, f"{plate}_{event_id[:6]}")
    os.makedirs(folder, exist_ok=True)

    pic = data.get("Picture", {})
    save_image(pic.get("CutoutPic"), folder, "cutout.jpg")
    save_image(pic.get("NormalPic"), folder, "normal.jpg")

    write_log(f"cam1 VEHICLE #{vehicle_count} Plate:{plate}")
    print(f"CAM1 COUNT {vehicle_count} PLATE {plate}")

    try:
        db.add_vehicle_detection(event_id, plate, data, folder)
    except Exception as e:
        print("DB error:", e)

    save_json(data)
    return jsonify(status="ok", count=vehicle_count)

# =====================
@app.route("/health", methods=["GET","POST"])
def health():
    return jsonify(cam1_count=vehicle_count)

# =====================
if __name__ == "__main__":
    print("🚀 CAM1 running 5000")
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
