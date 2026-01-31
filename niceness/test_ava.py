import os
import torch
import torch.nn as nn
from torchvision import transforms
from PIL import Image
import numpy as np
from modeltest import NicenessModel
import glob

# =====================
# Configuration
# =====================
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
CHECKPOINT_PATH = "checkpoints/best_model.pth"
IMAGE_DIR = "ava_images"

print(f"Device: {DEVICE}")


# =====================
# Image Preprocessing
# =====================
test_transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                        std=[0.229, 0.224, 0.225])
])


# =====================
# Model Loading
# =====================
def load_model(checkpoint_path, device):
    """Load trained model from checkpoint"""
    model = NicenessModel(embed_dim=1024)
    
    if os.path.exists(checkpoint_path):
        print(f"Loading checkpoint: {checkpoint_path}")
        state_dict = torch.load(checkpoint_path, map_location=device)
        model.load_state_dict(state_dict)
        print("✓ Model loaded successfully")
    else:
        print(f"WARNING: Checkpoint not found at {checkpoint_path}")
        print("Using untrained model")
    
    model = model.to(device)
    model.eval()
    return model


# =====================
# Single Image Testing
# =====================
@torch.no_grad()
def score_image(model, image_path, transform, device):
    """Score a single image"""
    try:
        # Load and preprocess image
        image = Image.open(image_path).convert('RGB')
        image_tensor = transform(image).unsqueeze(0).to(device)
        
        # Get aesthetic score
        score = model.forward_ava(image_tensor)
        score = score.item()
        
        return score, True
    except Exception as e:
        print(f"Error processing {image_path}: {e}")
        return None, False


# =====================
# Batch Testing
# =====================
@torch.no_grad()
def test_multiple_images(model, image_paths, transform, device, top_k=10):
    """Test multiple images and show top/bottom scores"""
    results = []
    
    print(f"\nTesting {len(image_paths)} images...")
    
    for img_path in image_paths:
        score, success = score_image(model, img_path, transform, device)
        if success:
            results.append((img_path, score))
    
    if not results:
        print("No images were successfully scored")
        return
    
    # Sort by score
    results.sort(key=lambda x: x[1], reverse=True)
    
    print(f"\n{'='*70}")
    print(f"Top {top_k} Highest Aesthetic Scores:")
    print(f"{'='*70}")
    for i, (path, score) in enumerate(results[:top_k], 1):
        filename = os.path.basename(path)
        print(f"{i:2d}. Score: {score:.4f} - {filename}")
    
    print(f"\n{'='*70}")
    print(f"Top {top_k} Lowest Aesthetic Scores:")
    print(f"{'='*70}")
    for i, (path, score) in enumerate(results[-top_k:][::-1], 1):
        filename = os.path.basename(path)
        print(f"{i:2d}. Score: {score:.4f} - {filename}")
    
    # Statistics
    scores = [s for _, s in results]
    print(f"\n{'='*70}")
    print("Score Statistics:")
    print(f"{'='*70}")
    print(f"Mean:   {np.mean(scores):.4f}")
    print(f"Median: {np.median(scores):.4f}")
    print(f"Std:    {np.std(scores):.4f}")
    print(f"Min:    {np.min(scores):.4f}")
    print(f"Max:    {np.max(scores):.4f}")
    
    return results


# =====================
# Interactive Testing
# =====================
def interactive_test(model, transform, device):
    """Test individual images interactively"""
    print("\n" + "="*70)
    print("Interactive Image Testing")
    print("="*70)
    print("Enter image path (or 'q' to quit)")
    
    while True:
        image_path = input("\nImage path: ").strip().strip('"\'')
        
        if image_path.lower() in ['q', 'quit', 'exit']:
            break
        
        if not os.path.exists(image_path):
            print(f"File not found: {image_path}")
            continue
        
        score, success = score_image(model, image_path, transform, device)
        if success:
            print(f"\n{'='*50}")
            print(f"Aesthetic Score: {score:.4f}")
            print(f"{'='*50}")
            
            # Interpretation
            if score > 6.5:
                quality = "Excellent"
            elif score > 5.5:
                quality = "Good"
            elif score > 4.5:
                quality = "Average"
            elif score > 3.5:
                quality = "Below Average"
            else:
                quality = "Poor"
            print(f"Quality Rating: {quality}")


# =====================
# Main
# =====================
if __name__ == "__main__":
    print("\n" + "="*70)
    print("AVA Aesthetic Model Testing")
    print("="*70)
    
    # Load model
    model = load_model(CHECKPOINT_PATH, DEVICE)
    
    # Menu
    print("\nTest Options:")
    print("1. Test all images in ava_images folder")
    print("2. Test specific image (interactive)")
    print("3. Test images from custom directory")
    print("4. Quick test on 50 random images")
    
    choice = input("\nSelect option (1-4): ").strip()
    
    if choice == "1":
        # Test all images
        image_paths = glob.glob(os.path.join(IMAGE_DIR, "*.jpg"))
        if not image_paths:
            print(f"No images found in {IMAGE_DIR}")
        else:
            test_multiple_images(model, image_paths, test_transform, DEVICE, top_k=10)
    
    elif choice == "2":
        # Interactive testing
        interactive_test(model, test_transform, DEVICE)
    
    elif choice == "3":
        # Custom directory
        custom_dir = input("Enter directory path: ").strip().strip('"\'')
        if os.path.exists(custom_dir):
            image_paths = []
            for ext in ['*.jpg', '*.jpeg', '*.png']:
                image_paths.extend(glob.glob(os.path.join(custom_dir, ext)))
            
            if image_paths:
                test_multiple_images(model, image_paths, test_transform, DEVICE, top_k=10)
            else:
                print(f"No images found in {custom_dir}")
        else:
            print(f"Directory not found: {custom_dir}")
    
    elif choice == "4":
        # Quick test on random subset
        image_paths = glob.glob(os.path.join(IMAGE_DIR, "*.jpg"))
        if image_paths:
            np.random.seed(42)
            sample_paths = np.random.choice(image_paths, min(50, len(image_paths)), replace=False)
            test_multiple_images(model, sample_paths, test_transform, DEVICE, top_k=10)
        else:
            print(f"No images found in {IMAGE_DIR}")
    
    else:
        print("Invalid option")
    
    print("\n" + "="*70)
    print("Testing complete!")
    print("="*70)
