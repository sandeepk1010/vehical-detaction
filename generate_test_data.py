"""
Generate sample test data for vehicle detection system
"""
import json
import os
from datetime import datetime
from pathlib import Path

# Create simple 1x1 white JPG (minimal valid JPEG)
# This is a valid JPEG file (minimal)
def create_sample_jpg():
    """Return bytes of a minimal valid JPEG"""
    return bytes.fromhex(
        'ffd8ffe000104a46494600010100000100010000ffdb004300080606070605080707'
        '070909080a0c140d0c0b0b0c1912130f141d1a1f1e1d1a1c1c20242e2720222c231c'
        '1c285037333432341f27393d38323c2e333432ffc0000b080001000101011100ffc4'
        '001f000001050101010101010000000000000000010203040506070809ffda00080101'
        '00003f007f1fff00ffd9'
    )

def generate_test_events():
    """Generate sample vehicle detection events"""
    
    # Create directories
    json_dir = Path("./json_data")
    downloads_dir = Path("./downloads")
    json_dir.mkdir(exist_ok=True)
    downloads_dir.mkdir(exist_ok=True)
    
    # Sample JPG bytes
    sample_jpg = create_sample_jpg()
    
    # Sample detection events
    test_events = [
        {
            "plate": "KA51AB1234",
            "device_id": "CAM_001",
            "vehicle_color": "Black",
            "plate_color": "White",
            "timestamp": "2026-02-06 18:45:30"
        },
        {
            "plate": "KA51CD5678",
            "device_id": "CAM_002",
            "vehicle_color": "White",
            "plate_color": "Yellow",
            "timestamp": "2026-02-06 18:44:15"
        },
        {
            "plate": "KA51EF9999",
            "device_id": "CAM_001",
            "vehicle_color": "Silver",
            "plate_color": "White",
            "timestamp": "2026-02-06 18:43:00"
        },
        {
            "plate": "KA51GH2222",
            "device_id": "CAM_002",
            "vehicle_color": "Red",
            "plate_color": "White",
            "timestamp": "2026-02-06 18:42:00"
        },
        {
            "plate": "KA51IJ3333",
            "device_id": "CAM_001",
            "vehicle_color": "Blue",
            "plate_color": "White",
            "timestamp": "2026-02-06 18:41:00"
        },
    ]
    
    # Create JSON files with proper structure
    for idx, event in enumerate(test_events):
        json_filename = f"{event['plate']}_{event['timestamp'].replace(' ', '_').replace(':', '')}.json"
        json_path = json_dir / json_filename
        
        # Create dummy base64 string for images
        dummy_b64 = "Qk1KAAAAAAAAAAA0AAAA="  # Minimal valid base64 (BMP header)
        
        # Create nested JSON structure that matches the API parser
        json_data = {
            "Picture": {
                "Plate": {
                    "PlateNumber": event["plate"],
                    "PlateColor": event["plate_color"]
                },
                "Vehicle": {
                    "VehicleColor": event["vehicle_color"]
                },
                "SnapInfo": {
                    "DeviceID": event["device_id"],
                    "AccurateTime": event["timestamp"]
                },
                "CutoutPic": {
                    "Content": dummy_b64,
                    "PicName": "cutout.jpg"
                },
                "VehiclePic": {
                    "Content": dummy_b64,
                    "PicName": "vehicle.jpg"
                },
                "NormalPic": {
                    "Content": dummy_b64,
                    "PicName": "normal.jpg"
                }
            }
        }
        
        # Save JSON file
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Created {json_filename}")
        
        # Create image folder and files
        folder_name = f"{event['plate']}_{event['device_id'][4:]}_{idx:04d}"
        image_folder = downloads_dir / folder_name
        image_folder.mkdir(exist_ok=True)
        
        # Save sample images
        for img_name in ['cutout.jpg', 'vehicle.jpg', 'normal.jpg']:
            img_path = image_folder / img_name
            with open(img_path, 'wb') as f:
                f.write(sample_jpg)
        
        print(f"  └─ Created image folder: {folder_name}/")
    
    print(f"\n✓ Generated {len(test_events)} test events")
    print(f"  - JSON files: {json_dir}/")
    print(f"  - Images: {downloads_dir}/")

if __name__ == '__main__':
    print("=" * 50)
    print("Generating Test Data...")
    print("=" * 50)
    generate_test_events()
    print("=" * 50)
    print("Test data ready! Run: python vehicle_ui.py")
    print("Then visit: http://localhost:5001/")
    print("=" * 50)
