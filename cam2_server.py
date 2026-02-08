from flask import Flask, request, jsonify
import logging, os, json
from datetime import datetime

app = Flask(__name__)

count = 0
os.makedirs("logs", exist_ok=True)

# =========================
# LOGGER SETUP (STRONG)
# =========================
log_file = f"logs/camera2_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"

logger = logging.getLogger("cam2_logger")
logger.setLevel(logging.INFO)
logger.propagate = False

# remove old handlers
if logger.handlers:
    for h in logger.handlers[:]:
        logger.removeHandler(h)

file_handler = logging.FileHandler(log_file, encoding="utf-8")
formatter = logging.Formatter("%(asctime)s - %(message)s")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

print("Log file:", log_file)

# =========================
# MAIN ROUTE
# =========================
@app.route("/NotificationInfo/TollgateInfo", methods=["POST"])
def cam2():
    global count
    count += 1

    # handle ANY camera payload
    try:
        data = request.get_json(force=True, silent=True)
        if not data:
            data = json.loads(request.data.decode("utf-8"))
    except:
        data = {}

    plate = data.get("Picture", {}).get("Plate", {}).get("PlateNumber", "UNKNOWN")

    logger.info(f"cam2 VEHICLE #{count} Plate:{plate}")
    print(f"CAM2 COUNT {count} PLATE {plate}")

    return jsonify(status="ok", count=count)

# =========================
# HEALTH
# =========================
@app.route("/health")
def health():
    return jsonify(cam2_count=count)

# =========================
if __name__ == "__main__":
    print("🚀 CAM2 running on 5001")
    app.run(host="0.0.0.0", port=5001, debug=False)
