from flask import Flask, request, jsonify
import os, json, uuid, logging
from datetime import datetime

app = Flask(__name__)

# =========================
# CAMERA IP → NAME MAP
# =========================
CAMERA_IP_MAP = {
    "192.168.1.108": "camera1",
    "192.168.1.109": "camera2",
}

# =========================
# DIRECTORIES
# =========================
LOG_DIR = "./logs"
JSON_DIR = "./json_data"

os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(JSON_DIR, exist_ok=True)

# =========================
# LOGGER FACTORY
# =========================
def create_logger(name, filename):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if logger.handlers:
        for h in logger.handlers[:]:
            logger.removeHandler(h)
            h.close()

    handler = logging.FileHandler(os.path.join(LOG_DIR, filename))
    handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(handler)
    return logger

cam1_logger = create_logger("cam1", "camera1.log")
cam2_logger = create_logger("cam2", "camera2.log")

# =========================
# COUNTERS
# =========================
vehicle_count = {"camera1": 0, "camera2": 0}

# =========================
# HELPER
# =========================
def get_camera():
    ip = request.remote_addr
    return CAMERA_IP_MAP.get(ip, "unknown")

def save_json(camera, data):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(JSON_DIR, f"{camera}_{ts}.json")
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)

# =========================
# SINGLE TOLLGATE ENDPOINT
# =========================
@app.route("/NotificationInfo/TollgateInfo", methods=["POST"])
def tollgate():
    camera = get_camera()
    vehicle_count[camera] += 1

    data = request.get_json(force=True, silent=True) or {}
    plate = (
        data.get("Picture", {})
            .get("Plate", {})
            .get("PlateNumber", "UNKNOWN")
    )

    log_msg = (
        f"POST /NotificationInfo/TollgateInfo "
        f"- {camera.upper()} "
        f"- VEHICLE #{vehicle_count[camera]} "
        f"- Plate: {plate} "
        f"- IP: {request.remote_addr}"
    )

    if camera == "camera2":
        cam2_logger.info(log_msg)
    else:
        cam1_logger.info(log_msg)

    save_json(camera, data)

    return jsonify(
        status="success",
        camera=camera,
        plate=plate,
        count=vehicle_count[camera]
    )

# =========================
# HEALTH (POST SAFE)
# =========================
@app.route("/health", methods=["GET", "POST"])
def health():
    return jsonify(status="ok")

# =========================
# RUN
# =========================
if __name__ == "__main__":
    print("🚀 ANPR Server Started (IP-based camera detection)")
    app.run(host="0.0.0.0", port=5000, debug=False)
