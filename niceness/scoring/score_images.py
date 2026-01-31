import os
import pandas as pd
import base64
import glob
from pathlib import Path
import torch
from torchvision import transforms
from PIL import Image
from modeltest import NicenessModel

# =====================
# Configuration
# =====================
IMAGES_DIR = "images"
OUTPUT_HTML = "airbnb_viewer.html"
CHECKPOINT_PATH = "checkpoints/property_model.pth"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Load model
print("Loading model...")
model = NicenessModel(embed_dim=1024)
if os.path.exists(CHECKPOINT_PATH):
    state_dict = torch.load(CHECKPOINT_PATH, map_location=DEVICE)
    model.load_state_dict(state_dict)
model = model.to(DEVICE)
model.eval()

# Image preprocessing
test_transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                        std=[0.229, 0.224, 0.225])
])

# Score images
print("Scoring images...")
@torch.no_grad()
def score_image(image_path):
    try:
        image = Image.open(image_path).convert('RGB')
        image_tensor = test_transform(image).unsqueeze(0).to(DEVICE)
        score = model.forward_ava(image_tensor)
        return score.item()
    except Exception as e:
        print(f"Error processing {image_path}: {e}")
        return 0.0

# =====================
# Generate HTML
# =====================
html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Airbnb Listings - Aesthetic Scores</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .header {
            background: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 2.5em;
        }
        
        .header p {
            color: #666;
            font-size: 1.1em;
        }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }
        
        .stat-value {
            font-size: 2em;
            font-weight: bold;
        }
        
        .stat-label {
            font-size: 0.9em;
            opacity: 0.9;
        }
        
        .controls {
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .sort-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1em;
            margin-right: 10px;
            transition: background 0.3s;
        }
        
        .sort-btn:hover {
            background: #764ba2;
        }
        
        .sort-btn.active {
            background: #764ba2;
        }
        
        .gallery {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
        }
        
        .listing-card {
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            transition: transform 0.3s, box-shadow 0.3s;
            cursor: pointer;
        }
        
        .listing-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.3);
        }
        
        .image-container {
            position: relative;
            width: 100%;
            height: 250px;
            overflow: hidden;
            background: #f0f0f0;
        }
        
        .image-container img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        
        .score-badge {
            position: absolute;
            top: 10px;
            right: 10px;
            background: rgba(102, 126, 234, 0.95);
            color: white;
            padding: 8px 15px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 1.1em;
        }
        
        .score-badge.excellent {
            background: rgba(76, 175, 80, 0.95);
        }
        
        .score-badge.good {
            background: rgba(33, 150, 243, 0.95);
        }
        
        .score-badge.average {
            background: rgba(255, 152, 0, 0.95);
        }
        
        .score-badge.poor {
            background: rgba(244, 67, 54, 0.95);
        }
        
        .listing-info {
            padding: 15px;
        }
        
        .listing-name {
            font-weight: bold;
            color: #333;
            margin-bottom: 10px;
            font-size: 1.1em;
            line-height: 1.4;
        }
        
        .listing-id {
            font-size: 0.85em;
            color: #999;
            margin-bottom: 10px;
        }
        
        .score-details {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 8px;
            font-size: 0.9em;
        }
        
        .detail-row {
            display: flex;
            justify-content: space-between;
            padding: 5px 0;
            border-bottom: 1px solid #eee;
        }
        
        .detail-row:last-child {
            border-bottom: none;
        }
        
        .detail-label {
            color: #666;
            font-weight: 500;
        }
        
        .detail-value {
            color: #333;
            font-weight: bold;
        }
        
        .no-image {
            display: flex;
            align-items: center;
            justify-content: center;
            height: 250px;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            color: #999;
            font-size: 0.9em;
        }

        .ratings-panel {
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }

        .ratings-panel h2 {
            color: #333;
            margin-bottom: 10px;
            font-size: 1.5em;
        }

        .ratings-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 12px;
            margin: 15px 0 20px;
        }

        .ratings-stat {
            background: #f7f7fb;
            padding: 12px;
            border-radius: 8px;
            text-align: center;
        }

        .ratings-stat .value {
            font-size: 1.4em;
            font-weight: bold;
            color: #333;
        }

        .ratings-table {
            width: 100%;
            border-collapse: collapse;
        }

        .ratings-table th,
        .ratings-table td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }

        .ratings-table th {
            background: #f5f7fa;
            color: #555;
            font-weight: 600;
        }

        .ratings-table img {
            width: 80px;
            height: 60px;
            object-fit: cover;
            border-radius: 6px;
            border: 1px solid #eee;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Image Aesthetic Scores</h1>
            <p>Ranked by aesthetic quality using trained AVA model</p>
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-value" id="total-listings">0</div>
                    <div class="stat-label">Total Images</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="mean-score">0.00</div>
                    <div class="stat-label">Mean Score</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="highest-score">0.00</div>
                    <div class="stat-label">Highest Score</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="lowest-score">0.00</div>
                    <div class="stat-label">Lowest Score</div>
                </div>
            </div>
        </div>
        
        <div class="controls">
            <button class="sort-btn active" onclick="sortGallery('highest')">Highest Score</button>
            <button class="sort-btn" onclick="sortGallery('lowest')">Lowest Score</button>
            <button class="sort-btn" onclick="sortGallery('alphabetical')">Alphabetical</button>
        </div>

        <div class="ratings-panel">
            <h2>Property Ratings (final_model.pth)</h2>
            <div class="ratings-stats">
                <div class="ratings-stat">
                    <div class="value" id="ratings-total">0</div>
                    <div>Total Rated</div>
                </div>
                <div class="ratings-stat">
                    <div class="value" id="ratings-mean">0.00</div>
                    <div>Mean Rating</div>
                </div>
                <div class="ratings-stat">
                    <div class="value" id="ratings-min">0.00</div>
                    <div>Min Rating</div>
                </div>
                <div class="ratings-stat">
                    <div class="value" id="ratings-max">0.00</div>
                    <div>Max Rating</div>
                </div>
            </div>
            <table class="ratings-table" id="ratings-table">
                <thead>
                    <tr>
                        <th>Image</th>
                        <th>Filename</th>
                        <th>Rating</th>
                        <th>Path</th>
                    </tr>
                </thead>
                <tbody></tbody>
            </table>
        </div>
        
        <div class="gallery" id="gallery"></div>
    </div>
    
    <script>
        const propertyRatings = %PROPERTY_RATINGS_DATA%;
        const listings = %LISTINGS_DATA%;
        
        function getScoreBadgeClass(score) {
            if (score >= 3.5) return 'excellent';
            if (score >= 3.0) return 'good';
            if (score >= 2.5) return 'average';
            return 'poor';
        }
        
        function getScoreLabel(score) {
            if (score >= 3.5) return 'Excellent';
            if (score >= 3.0) return 'Good';
            if (score >= 2.5) return 'Average';
            return 'Poor';
        }
        
        function renderGallery(data) {
            const gallery = document.getElementById('gallery');
            gallery.innerHTML = '';
            
            data.forEach(listing => {
                const card = document.createElement('div');
                card.className = 'listing-card';
                
                const imageSrc = listing.image_src || '';
                const imageHTML = imageSrc 
                    ? `<img src="${imageSrc}" alt="${listing.listing_name}">`
                    : '<div class="no-image">No image available</div>';
                
                const badgeClass = getScoreBadgeClass(listing.avg_score);
                const scoreLabel = getScoreLabel(listing.avg_score);
                
                card.innerHTML = `
                    <div class="image-container">
                        ${imageHTML}
                        <div class="score-badge ${badgeClass}">${listing.avg_score.toFixed(2)}</div>
                    </div>
                    <div class="listing-info">
                        <div class="listing-name">${listing.listing_name}</div>
                        <div class="listing-id">ID: ${listing.listing_id}</div>
                        <div class="score-details">
                            <div class="detail-row">
                                <span class="detail-label">Avg Score</span>
                                <span class="detail-value">${listing.avg_score.toFixed(4)}</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Min</span>
                                <span class="detail-value">${listing.min_score.toFixed(4)}</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Max</span>
                                <span class="detail-value">${listing.max_score.toFixed(4)}</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Images</span>
                                <span class="detail-value">${listing.num_images}</span>
                            </div>
                        </div>
                    </div>
                `;
                
                gallery.appendChild(card);
            });
        }
        
        function sortGallery(method) {
            let sorted = [...listings];
            
            if (method === 'highest') {
                sorted.sort((a, b) => b.avg_score - a.avg_score);
            } else if (method === 'lowest') {
                sorted.sort((a, b) => a.avg_score - b.avg_score);
            } else if (method === 'alphabetical') {
                sorted.sort((a, b) => a.listing_name.localeCompare(b.listing_name));
            }
            
            renderGallery(sorted);
            
            // Update button states
            document.querySelectorAll('.sort-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
        }
        
        function updateStats() {
            const total = listings.length;
            const scores = listings.map(l => l.avg_score);
            const mean = (scores.reduce((a, b) => a + b, 0) / total).toFixed(2);
            const highest = Math.max(...scores).toFixed(2);
            const lowest = Math.min(...scores).toFixed(2);
            
            document.getElementById('total-listings').textContent = total;
            document.getElementById('mean-score').textContent = mean;
            document.getElementById('highest-score').textContent = highest;
            document.getElementById('lowest-score').textContent = lowest;
        }

        function updateRatingsStats() {
            if (!propertyRatings.length) return;
            const scores = propertyRatings.map(r => r.property_score);
            const mean = (scores.reduce((a, b) => a + b, 0) / scores.length).toFixed(2);
            const highest = Math.max(...scores).toFixed(2);
            const lowest = Math.min(...scores).toFixed(2);

            document.getElementById('ratings-total').textContent = propertyRatings.length;
            document.getElementById('ratings-mean').textContent = mean;
            document.getElementById('ratings-min').textContent = lowest;
            document.getElementById('ratings-max').textContent = highest;
        }

        function renderRatingsTable() {
            const tbody = document.querySelector('#ratings-table tbody');
            tbody.innerHTML = '';

            propertyRatings
                .slice()
                .sort((a, b) => b.property_score - a.property_score)
                .forEach(row => {
                    const tr = document.createElement('tr');
                    const imgPath = row.image_path.replace(/\\\\/g, '/');
                    tr.innerHTML = `
                        <td><img src="${imgPath}" alt="${row.filename}"></td>
                        <td>${row.filename}</td>
                        <td>${row.property_score.toFixed(4)}</td>
                        <td>${row.image_path}</td>
                    `;
                    tbody.appendChild(tr);
                });
        }
        
        // Initialize
        updateStats();
        renderGallery(listings);
        updateRatingsStats();
        renderRatingsTable();
    </script>
</body>
</html>
"""

# Find images and create listing data
print("Finding images...")
listings_data = []

# Get all images from imgs folder
image_files = []
for ext in ['*.jpg', '*.jpeg', '*.png', '*.webp', '*.avif']:
    image_files.extend(glob.glob(os.path.join(IMAGES_DIR, ext)))

for image_path in image_files:
    filename = os.path.basename(image_path)
    
    # Score the image
    score = score_image(image_path)
    
    # Convert image to base64
    with open(image_path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode()
        # Detect image type
        ext = os.path.splitext(filename)[1].lower()
        mime_types = {
            '.jpg': 'jpeg', '.jpeg': 'jpeg', 
            '.png': 'png', '.webp': 'webp', '.avif': 'avif'
        }
        mime = mime_types.get(ext, 'jpeg')
        image_src = f"data:image/{mime};base64,{image_data}"
    
    listings_data.append({
        'listing_id': filename,
        'listing_name': filename,
        'avg_score': float(score),
        'min_score': float(score),
        'max_score': float(score),
        'num_images': 1,
        'image_src': image_src
    })

# Sort by score
listings_data.sort(key=lambda x: x['avg_score'], reverse=True)

# Replace placeholder with actual data
import json
listings_json = json.dumps(listings_data)
html_content = html_content.replace('%LISTINGS_DATA%', listings_json)

# Property ratings (optional)
property_ratings_data = []
property_ratings_csv = "property_ratings.csv"
if os.path.exists(property_ratings_csv):
    try:
        ratings_df = pd.read_csv(property_ratings_csv)
        property_ratings_data = ratings_df[["image_path", "filename", "property_score"]].to_dict(orient="records")
    except Exception as exc:
        print(f"WARNING: Failed to load {property_ratings_csv}: {exc}")

property_ratings_json = json.dumps(property_ratings_data)
html_content = html_content.replace('%PROPERTY_RATINGS_DATA%', property_ratings_json)

# Write HTML file
with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"\nHTML viewer created: {OUTPUT_HTML}")
print(f"Open this file in your web browser to view the listings with their scores!")
