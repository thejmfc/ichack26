import os
import glob
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from modeltest import NicenessModel
import pandas as pd
from tqdm import tqdm
from PIL import Image

# =====================
# Configuration
# =====================
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
BATCH_SIZE = 16
LEARNING_RATE = 2e-4
EPOCHS = 30
IMAGES_DIR = "images"
PROPERTY_RATINGS_CSV = "property_ratings.csv"
CHECKPOINT_DIR = "checkpoints"
EARLY_STOP_PATIENCE = 5
os.makedirs(CHECKPOINT_DIR, exist_ok=True)
PRETRAINED_PATH = "final_model.pth"

print(f"Device: {DEVICE}")


# =====================
# Dataset
# =====================
class PropertyRatingsDataset(Dataset):
    def __init__(self, ratings_csv, transform=None, max_samples=None):
        self.transform = transform
        self.samples = []

        if not os.path.exists(ratings_csv):
            raise FileNotFoundError(f"{ratings_csv} not found")

        ratings_df = pd.read_csv(ratings_csv)
        rows = ratings_df.to_dict(orient="records")
        if max_samples:
            rows = rows[:max_samples]

        for row in rows:
            image_path = row.get("image_path")
            score = float(row.get("property_score"))

            if not os.path.exists(image_path):
                continue

            self.samples.append((image_path, score))

        print(f"Loaded {len(self.samples)} images from {ratings_csv}")
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        image_path, score = self.samples[idx]
        
        try:
            image = Image.open(image_path).convert('RGB')
            if self.transform:
                image = self.transform(image)
            return image, torch.tensor(score, dtype=torch.float32)
        except Exception as e:
            print(f"Error loading {image_path}: {e}")
            return None, None


# =====================
# Data Augmentation
# =====================
train_transform = transforms.Compose([
    transforms.RandomResizedCrop(224, scale=(0.7, 1.0)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(15),
    transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.3, hue=0.1),
    transforms.RandomGrayscale(p=0.1),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                        std=[0.229, 0.224, 0.225])
])

val_transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                        std=[0.229, 0.224, 0.225])
])


# =====================
# Training Functions
# =====================
def train_epoch(model, dataloader, optimizer, criterion, device):
    model.train()
    total_loss = 0.0
    num_batches = 0
    
    pbar = tqdm(dataloader, desc="Training")
    for images, scores in pbar:
        # Handle None values from failed image loads
        if images is None:
            continue
        
        images = images.to(device)
        scores = scores.to(device)
        
        # Forward pass
        preds = model.forward_ava(images)
        loss = criterion(preds, scores)
        
        # Backward pass
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
        num_batches += 1
        pbar.set_postfix({"loss": f"{loss.item():.4f}"})
    
    return total_loss / max(num_batches, 1)


def validate(model, dataloader, criterion, device):
    model.eval()
    total_loss = 0.0
    num_batches = 0
    
    with torch.no_grad():
        for images, scores in tqdm(dataloader, desc="Validating"):
            if images is None:
                continue
            
            images = images.to(device)
            scores = scores.to(device)
            
            preds = model.forward_ava(images)
            loss = criterion(preds, scores)
            
            total_loss += loss.item()
            num_batches += 1
    
    return total_loss / max(num_batches, 1)


# =====================
# Main Training Loop
# =====================
if __name__ == "__main__":
    print("\n" + "="*60)
    print("Property Ratings Model Training")
    print("="*60)
    
    # Load dataset
    print("\nLoading dataset...")
    dataset = PropertyRatingsDataset(
        ratings_csv=PROPERTY_RATINGS_CSV,
        transform=train_transform,
        max_samples=None  # Use all available data
    )
    
    if len(dataset) == 0:
        print(f"ERROR: No images found! Make sure {IMAGES_DIR} and {PROPERTY_RATINGS_CSV} exist.")
        exit(1)
    
    # Split into train/val
    train_size = int(0.8 * len(dataset))
    val_size = len(dataset) - train_size
    train_dataset, val_dataset = torch.utils.data.random_split(
        dataset, [train_size, val_size]
    )
    
    # Use same transform for val but apply val_transform
    val_dataset.dataset.transform = val_transform
    
    # Create dataloaders
    train_loader = DataLoader(
        train_dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=0
    )
    val_loader = DataLoader(
        val_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=0
    )
    
    print(f"Train samples: {len(train_dataset)}")
    print(f"Val samples: {len(val_dataset)}")
    
    # Initialize model
    print("\nInitializing model...")
    model = NicenessModel(embed_dim=1024).to(DEVICE)

    # Load pretrained weights if available
    if os.path.exists(PRETRAINED_PATH):
        state_dict = torch.load(PRETRAINED_PATH, map_location=DEVICE)
        model.load_state_dict(state_dict)
        print(f"Loaded pretrained weights from {PRETRAINED_PATH}")
    
    # Optimizer and loss
    optimizer = optim.AdamW(model.parameters(), lr=LEARNING_RATE, weight_decay=0.01)
    criterion = nn.MSELoss()  # Changed to MSE for better score prediction
    scheduler = optim.lr_scheduler.CosineAnnealingWarmRestarts(optimizer, T_0=5, T_mult=2)
    
    # Training loop
    print("\nStarting training...\n")
    best_val_loss = float('inf')
    patience_counter = 0
    
    for epoch in range(1, EPOCHS + 1):
        print(f"\nEpoch {epoch}/{EPOCHS}")
        
        train_loss = train_epoch(model, train_loader, optimizer, criterion, DEVICE)
        val_loss = validate(model, val_loader, criterion, DEVICE)
        scheduler.step()
        
        print(f"Train Loss: {train_loss:.4f}")
        print(f"Val Loss: {val_loss:.4f}")
        print(f"LR: {optimizer.param_groups[0]['lr']:.6f}")
        
        # Save checkpoint
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            checkpoint_path = os.path.join(CHECKPOINT_DIR, "best_model.pth")
            torch.save(model.state_dict(), checkpoint_path)
            print(f"✓ Saved best model to {checkpoint_path} (val_loss: {val_loss:.4f})")
        else:
            patience_counter += 1
            print(f"No improvement for {patience_counter} epoch(s)")
            
        # Early stopping
        if patience_counter >= EARLY_STOP_PATIENCE:
            print(f"\nEarly stopping triggered after {epoch} epochs")
            break
    
    # Save final model
    final_path = os.path.join(CHECKPOINT_DIR, "final_model.pth")
    torch.save(model.state_dict(), final_path)
    print(f"\n✓ Training complete! Final model saved to {final_path}")
    print("="*60)
