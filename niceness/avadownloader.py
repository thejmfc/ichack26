import os
import requests
from tqdm import tqdm
import time

AVA_TXT = "AVA.txt"          # path to annotation file
OUT_DIR = "ava_images"       # output directory

os.makedirs(OUT_DIR, exist_ok=True)

def download_image(image_id):
    # Try multiple URL sources
    urls = [
        f"https://images.pexels.com/photos/{image_id}/pexels-photo-{image_id}.jpeg",
        f"https://www.dpchallenge.com/image/{image_id}",
    ]
    
    out_path = os.path.join(OUT_DIR, f"{image_id}.jpg")

    if os.path.exists(out_path):
        return True

    for url in urls:
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                with open(out_path, "wb") as f:
                    f.write(r.content)
                return True
        except Exception:
            continue
    
    return False


print(f"Reading {AVA_TXT}...")
with open(AVA_TXT, "r") as f:
    lines = f.readlines()

# Limit to first 1000 images for training
limit = 1000
lines = lines[:limit]

print(f"Downloading {len(lines)} sample images to {OUT_DIR}/")

for line in tqdm(lines, desc="Downloading images"):
    image_id = line.split()[1]  # Image ID is in column 2
    download_image(image_id)

print(f"Download complete!")