import uuid
from simple_db import Database

db = Database('vehicle_detection.db')

# Camera 1 event
event_id1 = str(uuid.uuid4())
data1 = {
    'plate': 'CAM1PLATE',
    'camera': 'camera1',
    'timestamp': '2026-02-06 10:00:00',
    'vehicle_color': 'Red',
    'plate_color': 'White'
}
vehicle_data1 = {'color': 'Red', 'type': 'Car'}

db.add_webhook_event(event_id1, 'vehicle_detection', data1, vehicle_data1, image_filename='camera1_20260206_100000_000001.json', camera='camera1')
db.add_camera_detection('camera1', event_id1, 'CAM1PLATE', {'camera':'camera1','timestamp':'2026-02-06 10:00:00'}, image_url='camera1_20260206_100000_000001.json')

# Camera 2 event
event_id2 = str(uuid.uuid4())
data2 = {
    'plate': 'CAM2PLATE',
    'camera': 'camera2',
    'timestamp': '2026-02-06 11:00:00',
    'vehicle_color': 'Blue',
    'plate_color': 'Yellow'
}
vehicle_data2 = {'color': 'Blue', 'type': 'Truck'}

db.add_webhook_event(event_id2, 'vehicle_detection', data2, vehicle_data2, image_filename='camera2_20260206_110000_000002.json', camera='camera2')
db.add_camera_detection('camera2', event_id2, 'CAM2PLATE', {'camera':'camera2','timestamp':'2026-02-06 11:00:00'}, image_url='camera2_20260206_110000_000002.json')

print('Inserted 2 sample events')
