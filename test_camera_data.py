#!/usr/bin/env python3
"""
Test script to simulate camera sending data to ANPR server (without requests)
"""
import urllib.request
import json
import base64
from datetime import datetime

# Server URL
SERVER_URL = "http://127.0.0.1:5000"

# Create a test image (1x1 black JPEG)
test_jpeg = base64.b64encode(b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xfb\xd3\xff\xd9').decode('latin-1')

def test_tollgate_endpoint():
    """Test the /NotificationInfo/TollgateInfo endpoint"""
    print("[TEST] Testing /NotificationInfo/TollgateInfo endpoint...")
    
    # Create test payload matching the expected format
    payload = {
        "Picture": {
            "PlateNumber": "MH15AB1234",
            "Plate": {
                "PlateNumber": "MH15AB1234",
                "Color": "Yellow"
            },
            "SnapInfo": {
                "DeviceID": "CAMERA1",
                "Timestamp": datetime.now().isoformat()
            },
            "NormalPic": {
                "Content": test_jpeg,
                "PicName": "normal.jpg"
            },
            "CutoutPic": {
                "Content": test_jpeg,
                "PicName": "cutout.jpg"
            }
        }
    }
    
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            f"{SERVER_URL}/NotificationInfo/TollgateInfo",
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            result = json.loads(response.read())
            print(f"[OK] Status: {response.status}")
            print(f"[OK] Response: {result}")
            return True
    except Exception as e:
        print(f"[ERROR] Failed: {str(e)}")
        return False

def test_webhook_endpoint():
    """Test the /webhook endpoint"""
    print("\n[TEST] Testing /webhook endpoint...")
    
    payload = {
        "Plate": "MH15AB5678",
        "Image": test_jpeg,
        "Timestamp": datetime.now().isoformat()
    }
    
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            f"{SERVER_URL}/webhook",
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            result = json.loads(response.read())
            print(f"[OK] Status: {response.status}")
            print(f"[OK] Response: {result}")
            return True
    except Exception as e:
        print(f"[ERROR] Failed: {str(e)}")
        return False

def test_health_endpoint():
    """Test the /health endpoint"""
    print("\n[TEST] Testing /health endpoint...")
    
    try:
        with urllib.request.urlopen(f"{SERVER_URL}/health", timeout=5) as response:
            result = json.loads(response.read())
            print(f"[OK] Status: {response.status}")
            print(f"[OK] Response: {result}")
            return True
    except Exception as e:
        print(f"[ERROR] Failed: {str(e)}")
        return False

def test_vehicle_count():
    """Test the /vehicle/count endpoint"""
    print("\n[TEST] Testing /vehicle/count endpoint...")
    
    try:
        with urllib.request.urlopen(f"{SERVER_URL}/vehicle/count", timeout=5) as response:
            result = json.loads(response.read())
            print(f"[OK] Status: {response.status}")
            print(f"[OK] Response: {result}")
            return True
    except Exception as e:
        print(f"[ERROR] Failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("ANPR Server Test Suite")
    print("=" * 60)
    
    test_health_endpoint()
    test_vehicle_count()
    test_tollgate_endpoint()
    test_webhook_endpoint()
    
    print("\n" + "=" * 60)
    print("Test suite completed")
    print("=" * 60)
