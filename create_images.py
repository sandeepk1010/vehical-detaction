import os, base64
os.makedirs('downloads/camera1_CAM1PLATE_20260206_100000', exist_ok=True)
os.makedirs('downloads/camera2_CAM2PLATE_20260206_110000', exist_ok=True)
img_b64='iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVQYV2NgYAAAAAMAAWgmWQ0AAAAASUVORK5CYII='
for folder, name in [('camera1_CAM1PLATE_20260206_100000','CAM1PLATE-20260206100000-plate.jpg'),
                     ('camera2_CAM2PLATE_20260206_110000','CAM2PLATE-20260206110000-plate.jpg')]:
    path = os.path.join('downloads', folder, name)
    with open(path, 'wb') as f:
        f.write(base64.b64decode(img_b64))
print('Image files created')
