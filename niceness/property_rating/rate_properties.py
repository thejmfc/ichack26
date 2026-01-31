import os
import glob
import argparse
from PIL import Image
import pandas as pd
import torch
from torchvision import transforms
from modeltest import NicenessModel

# =====================
# Configuration
# =====================
IMAGES_DIR = "images"
RATINGS_CSV = "property_ratings.csv"
MODEL_CHECKPOINT = "final_model.pth"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# =====================
# Model / Transform
# =====================
inference_transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                        std=[0.229, 0.224, 0.225])
])


def load_model(checkpoint_path: str) -> NicenessModel:
    model = NicenessModel(embed_dim=1024)
    if os.path.exists(checkpoint_path):
        state_dict = torch.load(checkpoint_path, map_location=DEVICE)
        model.load_state_dict(state_dict)
        print(f"Loaded weights from {checkpoint_path}")
    else:
        print(f"WARNING: Checkpoint not found at {checkpoint_path}. Using random initialization.")
    model = model.to(DEVICE)
    model.eval()
    return model


@torch.no_grad()
def score_image(model: NicenessModel, image_path: str) -> float | None:
    try:
        image = Image.open(image_path).convert("RGB")
        image_tensor = inference_transform(image).unsqueeze(0).to(DEVICE)
        score = model.forward_ava(image_tensor).item()
        return float(score)
    except Exception as exc:
        print(f"Error scoring {image_path}: {exc}")
        return None

# =====================
# Rating Script
# =====================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rate property images manually or with a model")
    parser.add_argument("--auto", action="store_true", help="Auto-rate using a model checkpoint")
    parser.add_argument("--images-dir", default=IMAGES_DIR, help="Directory with property images")
    parser.add_argument("--output", default=RATINGS_CSV, help="Output CSV path")
    parser.add_argument("--checkpoint", default=MODEL_CHECKPOINT, help="Model checkpoint path")
    args = parser.parse_args()

    print("\n" + "="*70)
    print("Property Photo Rating Tool")
    print("="*70)
    if args.auto:
        print("Auto-rating using model checkpoint")
    else:
        print("Rate each property from 1-10:")
        print("  1-3: Poor (unappealing, messy, bad lighting)")
        print("  4-5: Below Average (decent but not appealing)")
        print("  6-7: Good (nice, clean, good lighting)")
        print("  8-9: Excellent (very appealing, great layout/design)")
        print("  10: Perfect (ideal property interior/exterior)")
    print("="*70)
    
    # Get all images
    image_files = []
    for ext in ['*.jpg', '*.jpeg', '*.png', '*.webp', '*.avif']:
        image_files.extend(glob.glob(os.path.join(args.images_dir, ext)))
    
    if not image_files:
        print(f"No images found in {args.images_dir}")
        exit(1)
    
    image_files.sort()
    ratings = []
    
    print(f"\nFound {len(image_files)} images to rate\n")

    model = None
    if args.auto:
        print(f"Device: {DEVICE}")
        model = load_model(args.checkpoint)
    
    # Rate each image
    for idx, image_path in enumerate(image_files, 1):
        filename = os.path.basename(image_path)
        
        print(f"\n[{idx}/{len(image_files)}] {filename}")
        print(f"Path: {image_path}")
        
        # Display image info
        try:
            img = Image.open(image_path)
            print(f"Size: {img.size[0]}x{img.size[1]} pixels")
            print(f"Format: {img.format}")
        except:
            print("(Could not read image info)")
        
        # Get rating
        if args.auto:
            rating = score_image(model, image_path)
            if rating is None:
                continue
            rating = max(1.0, min(10.0, rating))
            print(f"Auto score: {rating:.4f}")
        else:
            while True:
                try:
                    rating = float(input("Rate this property (1-10): ").strip())
                    if 1 <= rating <= 10:
                        break
                    else:
                        print("Please enter a number between 1 and 10")
                except ValueError:
                    print("Invalid input. Please enter a number between 1 and 10")
        
        ratings.append({
            'image_path': image_path,
            'filename': filename,
            'property_score': rating
        })
        
        print(f"✓ Rated: {rating}/10")
    
    # Save ratings
    df = pd.DataFrame(ratings)
    df.to_csv(args.output, index=False)
    
    print("\n" + "="*70)
    print(f"Ratings saved to {args.output}")
    print(f"Total images rated: {len(ratings)}")
    print(f"Average rating: {df['property_score'].mean():.2f}")
    print(f"Min rating: {df['property_score'].min():.1f}")
    print(f"Max rating: {df['property_score'].max():.1f}")
    print("="*70)
    print("\nNext step: Run 'python finetune_property_model.py' to fine-tune the model")
