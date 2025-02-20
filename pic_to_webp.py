import os
from PIL import Image

def convert_to_webp(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(('.jpg', '.jpeg', '.png')):
                img_path = os.path.join(root, file)
                img = Image.open(img_path)
                webp_path = os.path.splitext(img_path)[0] + '.webp'
                img.save(webp_path, 'webp')
                print(f"Converted: {img_path} to {webp_path}")

# Specify the base directory to start conversion
base_directory = 'app/static/berichte'
convert_to_webp(base_directory)