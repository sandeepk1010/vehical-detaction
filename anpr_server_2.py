from flask import Flask, request, jsonify
import os, json, logging, base64, re
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
IMG_DIR = "./downloads"

os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(JSON_DIR, exist_ok=True)
os.makedirs(IMG_DIR, exist_ok=True)

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
vehicle_count = {"camera1": 0, "camera2": 0, "unknown": 0}

# =========================
# HELPERS
# =========================
def get_camera():
    return CAMERA_IP_MAP.get(request.remote_addr, "unknown")

def safe_name(text):
    return re.sub(r"[^A-Za-z0-9_-]", "_", str(text))

def decode_b64(b64):
    """
    Handles:
    - data:image/jpeg;base64,...
    - pure base64
    - escaped slashes
    """
    try:
        if not b64:
            return None
        if "," in b64:
            b64 = b64.split(",", 1)[1]
        b64 = b64.replace("\\/", "/")
        return base64.b64decode(b64)
    except Exception as e:
        print("❌ Base64 decode error:", e)
        return None

def save_json(camera, data):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    path = os.path.join(JSON_DIR, f"{camera}_{ts}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)

def save_images(camera, plate, picture):
    saved = []

    folder = f"{camera}_{safe_name(plate)}_{datetime.now():%Y%m%d_%H%M%S}"
    folder_path = os.path.join(IMG_DIR, folder)
    os.makedirs(folder_path, exist_ok=True)

    IMAGE_MAP = {
        "CutoutPic": "cutout.jpg",
        "NormalPic": "normal.jpg",
    }

    DATA_KEYS = ["Content", "PicData", "Data", "ContentBase64"]

    for pic_key, default_name in IMAGE_MAP.items():
        pic = picture.get(pic_key)
        if not isinstance(pic, dict):
            continue

        img_bytes = None
        for dk in DATA_KEYS:
            if dk in pic:
                img_bytes = decode_b64(pic.get(dk))
                if img_bytes:
                    break   # only break DATA_KEYS loop

        if not img_bytes:
            continue

        filename = pic.get("PicName") or default_name
        path = os.path.join(folder_path, filename)

        with open(path, "wb") as f:
            f.write(img_bytes)

        saved.append(filename)

    return folder, saved


# =========================
# TOLLGATE ENDPOINT
# =========================
@app.route("/NotificationInfo/TollgateInfo", methods=["POST"])
def tollgate():
    camera = get_camera()
    vehicle_count[camera] += 1

    data = request.get_json(silent=True) or {}
    picture = data.get("Picture", {})

    plate = (
        picture.get("Plate", {})
               .get("PlateNumber", "UNKNOWN")
    )

    folder, images = save_images(camera, plate, picture)
    save_json(camera, data)

    log_msg = (
        f"TOLLGATE | {camera.upper()} | "
        f"VEHICLE #{vehicle_count[camera]} | "
        f"Plate: {plate} | "
        f"Images: {len(images)} | "
        f"IP: {request.remote_addr}"
    )

    if camera == "camera2":
        cam2_logger.info(log_msg)
    else:
        cam1_logger.info(log_msg)

    if not images:
        print("⚠️ WARNING: No images saved. Check camera payload format.")

    return jsonify(
        status="success",
        camera=camera,
        plate=plate,
        count=vehicle_count[camera],
        image_folder=folder,
        images=images
    )

# =========================
# HEALTH
# =========================
@app.route("/health", methods=["GET", "POST"])
def health():
    return jsonify(status="ok")

# =========================
# RUN
# =========================
if __name__ == "__main__":
    print("🚀 ANPR Server Started (FULL image support enabled)")
    app.run(host="0.0.0.0", port=5000, debug=False)
