"""
Apply niceness scores to property images in the database.

This script:
1. Fetches all properties from the database
2. Downloads property images from URLs
3. Applies the niceness scoring model
4. Updates the database with the scores
"""

import os
import sys
import torch
import requests
from pathlib import Path
from PIL import Image
from io import BytesIO
from torchvision import transforms
from sqlmodel import Session, select

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import database and model modules
from database import get_engine, MockProperty
from niceness.scoring.modeltest import NicenessModel

# =====================
# Configuration
# =====================
CHECKPOINT_PATH = Path(__file__).parent / "niceness" / "checkpoints" / "property_model.pth"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
BATCH_SIZE = 1  # Process one image at a time for simplicity

# =====================
# Load Model
# =====================
print("Loading niceness model...")
model = NicenessModel(embed_dim=1024)
if CHECKPOINT_PATH.exists():
    state_dict = torch.load(CHECKPOINT_PATH, map_location=DEVICE)
    model.load_state_dict(state_dict)
    print(f"✅ Model loaded from {CHECKPOINT_PATH}")
else:
    print(f"⚠️  Warning: Model checkpoint not found at {CHECKPOINT_PATH}")
    print("Using untrained model (scores may not be meaningful)")

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

# =====================
# Image Scoring Function
# =====================
@torch.no_grad()
def score_image_from_url(image_url):
    """
    Download an image from a URL and score it using the niceness model.
    
    Args:
        image_url: URL of the image to score
        
    Returns:
        float: Niceness score (0-10 scale) or None if error
    """
    try:
        # Download image
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        
        # Open image
        image = Image.open(BytesIO(response.content)).convert('RGB')
        
        # Preprocess and score
        image_tensor = test_transform(image).unsqueeze(0).to(DEVICE)
        score = model.forward_ava(image_tensor)
        
        return score.item()
    except requests.RequestException as e:
        print(f"  ❌ Error downloading image from {image_url}: {e}")
        return None
    except Exception as e:
        print(f"  ❌ Error processing image: {e}")
        return None

# =====================
# Main Scoring Process
# =====================
def apply_niceness_scores():
    """Apply niceness scores to all properties in the database."""
    print("\n" + "="*60)
    print("Starting Niceness Score Application")
    print("="*60 + "\n")
    
    # Get database engine
    engine = get_engine()
    
    with Session(engine) as session:
        # Fetch all properties
        properties = session.exec(select(MockProperty)).all()
        total_properties = len(properties)
        
        print(f"Found {total_properties} properties in database\n")
        
        if total_properties == 0:
            print("No properties found. Please populate the database first.")
            return
        
        # Score each property
        scored_count = 0
        skipped_count = 0
        error_count = 0
        
        for i, property_obj in enumerate(properties, 1):
            print(f"[{i}/{total_properties}] Processing property ID {property_obj.id}")
            print(f"  Address: {property_obj.address}")
            
            # Skip if no image URL
            if not property_obj.image:
                print("  ⚠️  No image URL available - skipping")
                skipped_count += 1
                continue
            
            # Skip if already scored (optional - comment out to re-score)
            # if property_obj.niceness_score is not None:
            #     print(f"  ℹ️  Already scored ({property_obj.niceness_score:.2f}) - skipping")
            #     skipped_count += 1
            #     continue
            
            # Score the image
            print(f"  📥 Downloading and scoring image...")
            score = score_image_from_url(property_obj.image)
            
            if score is not None:
                # Update database
                property_obj.niceness_score = score
                session.add(property_obj)
                print(f"  ✅ Score: {score:.4f}")
                scored_count += 1
            else:
                print(f"  ❌ Failed to score image")
                error_count += 1
            
            print()  # Blank line for readability
        
        # Commit all changes
        session.commit()
        
        # Summary
        print("="*60)
        print("Summary")
        print("="*60)
        print(f"Total properties:     {total_properties}")
        print(f"Successfully scored:  {scored_count}")
        print(f"Skipped:              {skipped_count}")
        print(f"Errors:               {error_count}")
        print("="*60)
        
        if scored_count > 0:
            # Show statistics
            scored_properties = session.exec(
                select(MockProperty).where(MockProperty.niceness_score != None)
            ).all()
            
            scores = [p.niceness_score for p in scored_properties]
            avg_score = sum(scores) / len(scores)
            max_score = max(scores)
            min_score = min(scores)
            
            print(f"\nScore Statistics:")
            print(f"  Average:  {avg_score:.4f}")
            print(f"  Maximum:  {max_score:.4f}")
            print(f"  Minimum:  {min_score:.4f}")
            
            # Find best property
            best_property = max(scored_properties, key=lambda p: p.niceness_score)
            print(f"\n🏆 Highest scoring property:")
            print(f"  ID: {best_property.id}")
            print(f"  Address: {best_property.address}")
            print(f"  Score: {best_property.niceness_score:.4f}")
        
        print("\n✅ Niceness scores have been applied to the database!\n")

if __name__ == "__main__":
    try:
        apply_niceness_scores()
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
