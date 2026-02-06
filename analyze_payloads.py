#!/usr/bin/env python3
"""
Analyze camera payloads to understand the actual data format being sent
"""
import json
import os
from pathlib import Path
from datetime import datetime

LOGS_DIR = "./logs"

def analyze_payload(filepath):
    """Analyze a single payload file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to load {filepath}: {e}")
        return None
    
    print(f"\n{'='*70}")
    print(f"[ANALYSIS] {os.path.basename(filepath)}")
    print(f"{'='*70}")
    
    # Show structure
    print("\n[STRUCTURE]")
    print(f"Root keys: {list(data.keys())}")
    
    # If Picture exists
    if "Picture" in data:
        picture = data["Picture"]
        print(f"\nPicture keys: {list(picture.keys())}")
        
        # Check for image data
        image_found = False
        missing_images = []
        
        for key in ["CutoutPic", "NormalPic", "VehiclePic"]:
            if key in picture:
                pic = picture[key]
                if isinstance(pic, dict):
                    pic_keys = list(pic.keys())
                    print(f"\n  {key}:")
                    print(f"    - Keys: {pic_keys}")
                    
                    # Check for actual image data
                    has_data = False
                    for data_key in ["Content", "PicData", "Data", "ContentBase64", "content", "data"]:
                        if data_key in pic:
                            val = pic[data_key]
                            if isinstance(val, str) and len(val) > 100:
                                print(f"    - [{data_key}] Found: {len(val)} characters (looks like base64)")
                                has_data = True
                                image_found = True
                            elif isinstance(val, bytes):
                                print(f"    - [{data_key}] Found: bytes ({len(val)} bytes)")
                                has_data = True
                                image_found = True
                    
                    if not has_data:
                        missing_images.append(key)
                        print(f"    - [WARNING] No image data found")
        
        # Check plate info
        if "Plate" in picture:
            plate = picture["Plate"]
            if isinstance(plate, dict):
                plate_num = plate.get("PlateNumber", "UNKNOWN")
                print(f"\nPlate Number: {plate_num}")
        
        # Summary
        print(f"\n[SUMMARY]")
        if image_found:
            print("[OK] Images ARE present in payload")
        else:
            print("[WARNING] No images found in payload")
            if missing_images:
                print(f"     Missing from: {missing_images}")
    
    # Show recommendations
    print(f"\n[RECOMMENDATIONS]")
    if image_found:
        print("[OK] Images are being sent - they should be saved to /downloads/")
    else:
        print("[ACTION] Camera might not be configured to send images")
        print("        1. Check camera error logs")
        print("        2. Verify webhook URL is correct")
        print("        3. Enable 'Include Images' in camera settings")
        print("        4. Check image encoding (base64 vs raw bytes)")
    
    return data

def main():
    """Main function"""
    print("[PAYLOAD ANALYZER]")
    print("This tool analyzes camera payloads saved by the server\n")
    
    logs_dir = Path(LOGS_DIR)
    
    # Find debug payload files
    debug_files = sorted(logs_dir.glob("payload_debug_*.json"), reverse=True)
    
    if not debug_files:
        print("[ERROR] No debug payload files found")
        print(f"        Check: {LOGS_DIR}/")
        return
    
    print(f"[INFO] Found {len(debug_files)} debug payload files")
    print("[INFO] Analyzing latest payloads...\n")
    
    # Analyze last 5 payloads
    for payload_file in debug_files[:5]:
        analyze_payload(str(payload_file))
    
    print(f"\n{'='*70}")
    print("[NEXT STEPS]")
    print("1. Check the analysis above for missing/present images")
    print("2. If images are missing:")
    print("   - Check camera webhook configuration")
    print("   - Verify 'Include Images' or 'Include Payload' is enabled")
    print("3. If images are present but not being saved:")
    print("   - Check that base64 decoding is working")
    print("   - Look at error messages in the server output")
    print("4. Send test data from camera and re-run this script")

if __name__ == "__main__":
    main()
