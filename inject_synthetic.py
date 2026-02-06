import os
import json
from datetime import datetime
from pathlib import Path
import base64

# Create JSON entries and placeholder images for camera1 and camera2
BASE_DIR = Path(__file__).parent
JSON_DIR = BASE_DIR / 'json_data'
DOWNLOADS_DIR = BASE_DIR / 'downloads'

os.makedirs(JSON_DIR, exist_ok=True)
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

# Tiny 1x1 PNG base64
PNG_B64 = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII='
PNG_BYTES = base64.b64decode(PNG_B64)

now = datetime.now()

def write_for_camera(camera, plate):
    ts = now.strftime('%Y%m%d_%H%M%S')
    json_name = f"{camera}_{ts}.json"
    folder_name = f"{camera}_{plate}_{ts}"
    folder_path = DOWNLOADS_DIR / folder_name
    os.makedirs(folder_path, exist_ok=True)
    # write placeholder image
    img_path = folder_path / 'vehicle.jpg'
    with open(img_path, 'wb') as f:
        f.write(PNG_BYTES)

    # build JSON
    data = {
        'Picture': {
            'Plate': {
                'PlateNumber': plate,
                'PlateColor': 'White'
            },
            'SnapInfo': {
                'AccurateTime': now.isoformat()
            },
            'Vehicle': {
                'VehicleColor': 'Blue'
            },
            'VehiclePic': {
                'Content': PNG_B64,
                'PicName': 'vehicle.jpg'
            },
            'CutoutPic': {
                'Content': PNG_B64,
                'PicName': 'cutout.jpg'
            }
        }
    }

    with open(JSON_DIR / json_name, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

    print(f'Wrote: {JSON_DIR / json_name} and {img_path}')

# Try to log via vehicle_ui loggers if available
try:
    import vehicle_ui
    vehicle_ui.cam1_logger.info('SYNTHETIC | camera1 synthetic detection')
    vehicle_ui.cam2_logger.info('SYNTHETIC | camera2 synthetic detection')
    print('Logged via vehicle_ui loggers')
except Exception as e:
    print('Could not import vehicle_ui loggers:', e)

# Create entries for both cameras
write_for_camera('camera1', 'SYNTH1')
write_for_camera('camera2', 'SYNTH2')
print('Done')
